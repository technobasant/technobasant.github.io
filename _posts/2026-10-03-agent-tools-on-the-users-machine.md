---
title: "The user's laptop is not a server. Make it a queue consumer."
seo_title: "Running agent tools on a user's machine from a multi-pod backend"
description: "A cloud agent that drives a browser on a user's Mac kept reporting it offline. The fix was not sticky routing: model the laptop as a queue consumer."
date: 2026-10-03 09:10:00 +0545
last_modified_at: 2026-10-03
type: essay
tags:
  - ai-agents
  - kubernetes
toc: true
featured: false
work: clickhomes
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - AI agent tool execution
  - Redis Streams
  - at-least-once delivery
  - WebSocket backpressure
mentions:
  - LangGraph
  - Redis
  - Playwright
  - websockets
  - Kubernetes
cover:
  base: "/assets/images/editorial-agent-remote-tools-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: an agent on any pod adds a job to a per-user Redis stream, the pod holding the socket relays it to the user's laptop, and a TTL presence key answers for every pod"
  caption: "No pod owns the user. Work goes onto a stream, presence is a key every pod reads, and the laptop is whoever happens to be consuming."
faq:
  - q: "How does a cloud agent call a tool that only runs on a user's own machine?"
    a: "The machine dials out; nothing dials in. Put each job on a per-user queue that any backend replica can write to, let whichever process holds the user's outbound connection consume it, and keep presence in a shared TTL key rather than in one process's memory."
  - q: "Why not use sticky sessions to route requests to the pod that holds the WebSocket?"
    a: "Affinity fixes routing, not state. ClientIP affinity breaks behind NAT, which is where every end user sits, and a rolling deploy terminates the pod that held the socket whatever the load balancer remembers. It is a transition aid while adding a second replica, not an architecture."
  - q: "Should a desktop agent deduplicate on the job id or on an idempotency key?"
    a: "On an idempotency key that stays stable across redeliveries. In this design the hub regenerates the job id on every delivery, so a cache keyed on id can never match a duplicate. The reply still has to carry the incoming frame's id, or the caller drops it as unknown."
  - q: "Why did a long-running job make the WebSocket drop?"
    a: "Because the receive loop awaited the job inline. Once more than websockets' default of 16 frames queued up unread, the library stopped reading the transport, the keepalive pong sat behind them, and ping_timeout closed a healthy connection. Reading, writing and executing have to be separate tasks."
key_takeaways:
  - "A process-local socket registry is correct on one worker and wrong on two; with gunicorn -w 2, any request that reached the other worker reported a live desktop as offline."
  - "Session affinity was rejected because it fixes routing rather than state: ClientIP affinity breaks behind NAT and rolling deploys drop the socket regardless."
  - "At-least-once delivery bit the recovery path first: without an in-flight guard, draining the pending list executed one form fill twelve times during development."
  - "Deduplicate on a stable idempotency key, never on a delivery id the hub regenerates, and answer the cached outcome under the incoming frame's id."
  - "Keepalive is part of the protocol: a receive loop that runs jobs inline stops reading, starves the pong, and turns a slow job into a dropped connection."
---

The agent in a product I am building runs in the cloud. Some of its tools cannot: they drive a real Chrome on the user's Mac, signed into MLS and brokerage portals the user will not hand over credentials for. A small desktop sidecar opens a WebSocket out to the backend, the backend sends it jobs, and the sidecar runs them in that browser.

It worked on my machine and failed in production in the most confusing way available. The connectors page, polling, showed the desktop **live**. The agent, asking once, was told it was **offline** and fell back to a web search that could not see the data it needed. Both answers came from the same backend, a few seconds apart.

**Operating rule.** A user's machine is not a server you can route to. It is a consumer that comes and goes. Put the work somewhere every replica can write, let whoever holds the connection right now consume it, and make presence a fact every replica reads the same way. Then accept that delivery is at-least-once and make the machine safe to call twice.

## The bug was a dictionary

The socket registry was a process-local `dict` keyed by user id. That is not a mistake in itself — a WebSocket object cannot be serialised or shared — but production ran `gunicorn -w 2`. The socket lived in exactly one worker. A request handled by the other worker looked in an empty dict and answered honestly: not connected.

The connectors page polled repeatedly, so some of its requests landed on the right worker and it showed green. The agent made one call per tool and lost whenever it hit the wrong process. With two workers that is a coin flip; on Kubernetes with several pods, node spread and rolling deploys, the same design degrades from "intermittent" to "usually wrong".

The constraints I set before choosing a fix were deliberately narrow:

- Use only what was already deployed: Redis and PostgreSQL. No NATS, Kafka, Temporal, MQTT or managed tunnels.
- The desktop client may change, but a fix that ships server-side only is better.
- The target is multi-pod, multi-node, with rolling deploys — not "works on two gunicorn workers".

## Four ways to reach a laptop, and why three failed

| Option | What it fixes | Failure mode that ruled it out |
| --- | --- | --- |
| `gunicorn -w 1` | The symptom, on one host | Throws away the second worker and does nothing for a second pod. A stopgap, and in the end not even needed. |
| Sticky sessions (header or `ClientIP` affinity) | Routing to the pod that holds the socket | Fixes routing, not state. `ClientIP` affinity breaks behind NAT — where every end user sits — and a rolling deploy kills the pod holding the socket regardless of what the balancer remembers. |
| Redis Pub/Sub request/reply | Cross-pod messaging with no topology | At-most-once. A reply published while the requester is not subscribed is gone; `PUBLISH` returning `0` means it was dropped. A lost reply is a hung tool call. |
| **Per-user stream + TTL presence** | **State and routing, together** | Delivery becomes at-least-once, so every side effect needs an idempotency key. That cost is real and is what the rest of this essay is about. |
{: aria-label="Options considered for reaching a user's machine from a multi-replica backend" }

The sticky-session row deserves its own sentence, because it was the previous recommendation in my own repository and it was wrong. Practitioners who scale WebSockets on Kubernetes converge on affinity as a transition tool while you add a second replica. It is not where you end up. When the pod dies, its in-memory sockets die with it; affinity cheerfully routes the client to a pod that never had the socket.

The pull model is also not a workaround. It is how self-hosted CI runners solve the identical problem: the runner opens the connection outbound and asks for work, so no inbound rule is ever needed. A laptop behind a home router is the same shape as a runner behind a corporate firewall.

## What shipped: a stream, a key, and no owner

Two pieces, both keyed by user id, both in the Redis that was already there:

```python
_PRESENCE_KEY = "bridge:presence:{user_id}"
_JOBS_STREAM = "bridge:jobs:{user_id}"
_RESULT_KEY = "bridge:result:{job_id}"
_CONSUMER_GROUP = "bridge-workers"

# A multiple of the heartbeat, not the idle timeout: a network blip
# shorter than two heartbeats must not read as a disconnect.
PRESENCE_HEARTBEAT_SECONDS = 10
PRESENCE_TTL_SECONDS = PRESENCE_HEARTBEAT_SECONDS * 3

# Redis does not trim acknowledged entries; an offline desktop must not
# accumulate work forever.
_JOBS_MAXLEN = 500

# Longer than the longest legitimate job (browser automations run 60–120 s),
# or a job still running would be reclaimed and executed twice.
_RECLAIM_IDLE_MS = 180_000
```
{: data-file="desktop_bridge_substrate.py" }

**Presence** is a key the socket-holding process refreshes every 10 seconds with a 30-second TTL. "Is this user's desktop connected?" now has one answer cluster-wide instead of one answer per process. It is still corroborated by a real round-trip before the product claims a healthy bridge: a key that exists proves a heartbeat, not that the desktop is answering.

**Dispatch** is a per-user stream with a consumer group. Any replica can add a job with zero knowledge of topology. The replica that holds that user's socket consumes the stream and forwards each job down the WebSocket it already has. The reply comes back on a per-job list the requester waits on with `BLPOP`, with a 300-second TTL so a reply nobody collected cannot be handed to a later call.

```text
# any replica
XADD   bridge:jobs:{user}  MAXLEN ~ 500  *  id <uuid> name browser_click args {...} idempotency_key <k>
BLPOP  bridge:result:{job_id}  90

# the replica holding the socket
XREADGROUP GROUP bridge-workers <consumer> STREAMS bridge:jobs:{user} 0     # drain own pending first
XREADGROUP GROUP bridge-workers <consumer> BLOCK 2000 STREAMS bridge:jobs:{user} >
XAUTOCLAIM bridge:jobs:{user} bridge-workers <consumer> 180000 0-0          # when idle
RPUSH  bridge:result:{job_id} {...} ; EXPIRE bridge:result:{job_id} 300
XACK   bridge:jobs:{user} bridge-workers <entry-id>                         # only after the reply
```

The original ADR assumed the sidecar would become a Redis consumer itself. What shipped is simpler: the process holding the socket consumes on the user's behalf. The desktop client's contract — a `job` frame in, a `job_result` frame out — did not move, and the fix deployed server-side. The model is the same either way. **No replica owns the user.** There is no registry to look up, so the class of bug disappears instead of being routed around.

## At-least-once bites the recovery path first

The happy path was correct on the first try. The recovery path was not, and it failed in the direction that matters most for a tool that clicks buttons in someone's browser.

A browser job runs for a minute or more, so the consuming loop cannot await it; it spawns a task per job, and that task sends the `XACK` once the reply is published. On startup the loop drains its own pending entries by reading from id `0`. Those two facts combine badly: a pending read repeated before the spawned task's `XACK` lands returns the same entry again. The drain loop re-dispatched one entry as fast as it could spin.

During development that was **twelve executions of a single form-fill job**. Every "was it delivered?" test passed.

The fix is a set of in-flight entry ids, released only after the acknowledgement is durable:

```python
fresh = [(entry_id, job) for entry_id, job in jobs if entry_id not in inflight]
if drain_pending and not fresh:
    # Nothing pending left that we are not already serving: switch to new
    # messages, which also stops this phase from spinning.
    drain_pending = False
for entry_id, job in fresh:
    inflight.add(entry_id)
    asyncio.create_task(self._serve_relayed_job(user_id, entry_id, job, semaphore, inflight))
```
{: data-file="desktop_bridge_hub.py" }

Two more recovery-path facts the ADR did not anticipate:

- **`XAUTOCLAIM` is not optional.** Consumer names are per process. When a pod is evicted mid-job, its pending entries belong to a name nobody will ever read again — invisible to a `>` read and to every survivor's own drain. Without reclaim those jobs hang until the requester times out, every time. The reclaim threshold, 180 seconds, sits above the longest legitimate job on purpose.
- **An asyncio Redis client is bound to the event loop that created it.** The substrate is a process-wide singleton, so a cached client can outlive its loop and fail with `Event loop is closed` — intermittently, because a pooled connection sometimes still works. Every substrate failure degrades to "desktop offline", so this would have resurrected the exact bug being fixed. The client now tracks its loop and rebuilds when it changes.

<div class="callout callout--gotcha" markdown="1">
**Test the second delivery, not the first.** A delivery test passes while work is duplicated. Every recovery path here — startup drain, reclaim after eviction, redelivery after a dropped socket — needs an explicit *executed exactly once* assertion. The hub's multi-pod suite carries one for the startup drain; the sidecar's carries one for redelivery under a new id.
</div>

## Deduplicate on the key, answer on the id

At-least-once delivery plus browser side effects means a duplicate is a second click. In this product that is a safety issue, not a reliability one: the approval model forbids an agent submitting anything the user did not approve, and a redelivered `browser_click` is exactly that.

The sidecar originally read only `id`, `name` and `args`. Deduplicating on `id` looks natural and can never work, because the hub mints a fresh `id` per delivery so it can correlate replies. The stable value is `idempotency_key`, which the requester sets once and every redelivery carries unchanged.

```python
cached = deduper.cached(key)
if cached is not None:
    return cached

# Shielded: if the socket drops mid-action the work still finishes and records
# its outcome, so the redelivery that follows is answered from cache.
return await asyncio.shield(
    deduper.run(key, lambda: _invoke_job(chat, name, args, timeout_s))
)
```
{: data-file="bridge/__init__.py" }

Three details carry the weight:

- The cache lives **across reconnects**. A reclaimed job is redelivered on a new socket, often through a different pod, so a per-session cache would never see the duplicate. It holds 256 outcomes for 300 seconds, mirroring the hub's own result TTL.
- A redelivery that arrives **while the original is still running** awaits the original task instead of starting a second one.
- The replayed outcome is sent under the **incoming** frame's id. The hub correlates on `id`; replaying the stored one would be logged as a result for an unknown job and leave the caller hanging.

## The socket has to keep reading

The last failure looked like a network problem and was a scheduling one. The receive loop awaited each job inline. While a long browser action ran, nothing read the socket. The `websockets` library buffers incoming frames up to `max_queue`, which defaults to 16; past that it stops reading the transport — and the keepalive pong is one of the frames it is not reading. `ping_timeout` then closed a perfectly healthy connection, the hub saw the desktop vanish mid-job, and the job was eventually redelivered.

The session is now four kinds of task: a reader that never awaits job work, a writer that is the sole owner of `send`, a strictly serial browser worker (there is one Chrome and one automation session, and ordering matters), and a separate queue for `status`. `status` is what the backend calls to decide whether the desktop is online, so it must never sit behind a minute-long action. The keepalive settings are spelled out rather than inherited, and an application-level ping has a deadline that actually raises.

The sidecar also compares wall-clock and monotonic time every second. On macOS the monotonic clock pauses across sleep while the wall clock does not, so a gap of more than five seconds in either means the lid closed or the loop wedged. Either way the socket is presumed dead and the client reconnects, instead of waiting for the operating system to admit it.

Against a local hub, after these changes:

| Check | Result |
| --- | --- |
| Two deliveries of one `idempotency_key` | Browser tool executed once |
| `status` while a 12 s browser job was in flight | Answered in 0.02 s |
| Backend restart | Sidecar reconnected in about 22 s |
{: aria-label="Verification results against a local hub" }

<div class="callout callout--note" markdown="1">
**Boundary.** The twelve-fold execution was observed during development of the startup drain, before the in-flight guard existed. The three results above were verified against a backend hub running locally, not under production load or across real pod evictions; reclaim after eviction is covered by tests with a fake hub, not by a measured incident. That two workers made roughly half the agent's calls fail is an inference from how requests spread across processes, not a counted rate. The design claims — affinity breaking behind NAT, Pub/Sub being at-most-once — rest on Redis documentation and practitioner write-ups, which the decision record links.
</div>

## What this does not solve

A queue does not make a laptop reliable. It makes the backend honest about one that is not.

- **A closed lid mid-run.** Reclaim re-queues the job, but the user has to be told truthfully that it did not complete. No substrate fixes a sleeping machine.
- **Consent for side effects.** Approval for anything that submits or signs stays at the action layer, regardless of transport.
- **Egress blocked entirely.** A network with no outbound path defeats the pull model too, exactly as it does for CI runners.
- **Exactly-once.** It does not exist here. Idempotency keys are mandatory, not an optimisation.

Exposing the sidecar as an MCP server would not have fixed reachability either. A laptop behind NAT cannot be dialled by a pod, whatever the protocol. Direction is the invariant; MCP is a good interface for the tool catalogue that sits on top of this substrate, not a substitute for it.

## Frequently asked questions

### How does a cloud agent call a tool that only runs on a user's own machine?

The machine dials out; nothing dials in. Put each job on a per-user queue that any backend replica can write to, let whichever process holds the user's outbound connection consume it, and keep presence in a shared TTL key rather than in one process's memory.

### Why not use sticky sessions to route requests to the pod that holds the WebSocket?

Affinity fixes routing, not state. `ClientIP` affinity breaks behind NAT, which is where every end user sits, and a rolling deploy terminates the pod that held the socket whatever the load balancer remembers. It is a transition aid while adding a second replica, not an architecture.

### Should a desktop agent deduplicate on the job id or on an idempotency key?

On an idempotency key that stays stable across redeliveries. In this design the hub regenerates the job id on every delivery, so a cache keyed on id can never match a duplicate. The reply still has to carry the incoming frame's id, or the caller drops it as unknown.

### Why did a long-running job make the WebSocket drop?

Because the receive loop awaited the job inline. Once more than websockets' default of 16 frames queued up unread, the library stopped reading the transport, the keepalive pong sat behind them, and `ping_timeout` closed a healthy connection. Reading, writing and executing have to be separate tasks.

The references worth keeping open are the Redis documentation on [streams and consumer groups](https://redis.io/docs/latest/develop/data-types/streams/) and [`XAUTOCLAIM`](https://redis.io/docs/latest/commands/xautoclaim/), and the `websockets` notes on [keepalive](https://websockets.readthedocs.io/en/stable/topics/keepalive.html) and [memory and buffering](https://websockets.readthedocs.io/en/stable/topics/memory.html). The product this comes from is described in [the ClickHomes case study](/work/clickhomes/); the same rule — agent output is a candidate until something durable accepts it — runs through [governed AI delivery](/work/governed-ai-delivery/). More on [AI agents in production](/writing/tags/ai-agents/).
