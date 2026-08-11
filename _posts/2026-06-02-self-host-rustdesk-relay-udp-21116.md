---
title: "A free private remote desktop with RustDesk"
seo_title: "Self-host RustDesk: open UDP 21116 or the client never stays up"
description: "Want a free private remote desktop? Self-host RustDesk on Docker, open UDP 21116, pin the key, and keep sessions past the public cutoff."
date: 2026-06-02 09:00:00 +0545
last_modified_at: 2026-08-11 11:30:00 +0545
type: tutorial
tags: [self-hosted]
series: self-hosted-ops
series_order: 1
featured: true
toc: true
level: intermediate
time_estimate: "~30 min hands-on"
what_youll_build: "Your own RustDesk server on a VPS, so two machines can connect without the public 30-second cutoff or a paid plan."
prerequisites:
  - "A Linux VPS with a public IPv4 address and Docker Compose v2"
  - "A DNS A record you can point at that VPS, for example relay.example.com"
  - "Two machines with the RustDesk client (laptop plus the machine you want to control)"
tested_on: "rustdesk/rustdesk-server · Docker Compose v2 · Debian/Ubuntu VPS with UFW"
key_takeaways:
  - "Public RustDesk cuts sessions around 30 seconds; your own hbbs/hbbr does not, if UDP 21116 and TCP 21117 actually reach the host."
  - "hbbs advertises the relay with -r hostname:21117; ALWAYS_USE_RELAY=Y is how you prove traffic hits hbbr instead of silent P2P."
  - "The only durable secret is data/id_ed25519; lose it and every client must be re-keyed, even if the containers look healthy."
work: clickhomes
---

## Why bother

Want a TeamViewer-style remote desktop without a subscription, and without handing connection metadata to someone else's relay? RustDesk is fully open source. The clients are free. The public servers will connect you — and then drop the session at about thirty seconds unless you pay.

You can skip that tax. Run the official `hbbs` (rendezvous) and `hbbr` (relay) containers on any small Linux VPS, point `relay.example.com` at it, and paste one public key into each client. Idle cost is tens of megabytes of RAM. Bandwidth is whatever your VPS already has.

Two things usually waste the first hour, so we will treat them as part of the setup rather than surprises:

1. **UDP 21116.** People open TCP 21116 and forget UDP. The app sits on “Connecting…” while Docker looks healthy.
2. **Silent P2P.** RustDesk prefers a direct path. On the same LAN a session can succeed without ever touching `hbbr`. You have not tested the relay until `ALWAYS_USE_RELAY=Y` and you see traffic on 21117.

Substitute your domain below. Do not publish the private key.

<div class="callout callout--note" markdown="1">
**What “done” means.** Not `docker compose ps` saying healthy. Done is: UDP 21116 answers from outside, the client shows `Ready (relay.example.com)`, and a session through your relay lasts past sixty seconds.
</div>

## Step 1 — DNS, firewall, and the compose file

Create a directory and an A record for the relay hostname, pointing at the VPS. IPv6 is optional; if you add AAAA, keep using the hostname as the client setting so you are not locked to one stack.

```bash
mkdir -p rustdesk-server/data
cd rustdesk-server
```

Open the ports. UDP 21116 is the one people skip. 21118/21119 are only for the web client; leave them closed if you are not using it.

```bash
sudo ufw allow 21115/tcp
sudo ufw allow 21116/tcp
sudo ufw allow 21116/udp
sudo ufw allow 21117/tcp
sudo ufw reload
sudo ss -lntu | grep -E '21115|21116|21117' || true
```

Write `.env` and the compose file. `RUSTDESK_PUBLIC_HOST` must be the name you put in DNS. `hbbs -r` tells clients which host:port is the relay.

```bash
cat > .env <<'EOF'
RUSTDESK_PUBLIC_HOST=relay.example.com
RUSTDESK_ALWAYS_USE_RELAY=Y
EOF
```
{: data-file="rustdesk-server/.env"}

```yaml
services:
  hbbs:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk_hbbs
    restart: unless-stopped
    environment:
      - ALWAYS_USE_RELAY=${RUSTDESK_ALWAYS_USE_RELAY:-Y}
    command: hbbs -r ${RUSTDESK_PUBLIC_HOST}:21117
    ports:
      - "21115:21115"
      - "21116:21116"
      - "21116:21116/udp"
    volumes:
      - ./data:/root
    depends_on:
      - hbbr
    networks: [rustdesk_net]
    mem_limit: 256m
    cpus: "0.25"

  hbbr:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk_hbbr
    restart: unless-stopped
    command: hbbr
    ports:
      - "21117:21117"
    volumes:
      - ./data:/root
    networks: [rustdesk_net]
    mem_limit: 256m
    cpus: "0.50"

networks:
  rustdesk_net:
    driver: bridge
```
{: data-file="rustdesk-server/docker-compose.yml"}

Explicit port maps beat host networking here. The relay then sits beside an existing app stack without claiming the host network namespace. Idle cost is small: tens of megabytes of RAM and almost no CPU until a session is relayed.

```bash
docker compose up -d
docker compose ps
docker compose logs hbbs --tail=30
docker compose logs hbbr --tail=20
```

Look for `ALWAYS_USE_RELAY=Y` in the `hbbs` log and a listen line on 21117 in `hbbr`. Treat a healthcheck of `unhealthy` as untrusted if the image has no shell for `CMD-SHELL`. Ports listening plus an external `nc` are the real signals.

**Verify.** From a machine that is not the VPS, all four of these should report open. If TCP works and UDP fails, the firewall or provider security group is incomplete.
{: .verify}

```bash
nc -vz relay.example.com 21115
nc -vz relay.example.com 21116
nc -vz relay.example.com 21117
nc -vzu relay.example.com 21116
```

## Step 2 — Pin the key, then configure the clients

The first start writes an Ed25519 pair into `./data`. Clients pin the **public** key. Without that pin they will not talk to your server, which is the whole anti-MITM design.

```bash
cat ./data/id_ed25519.pub
# example only: 5fGu2T8aQrXkPnMwZ...kP9vNw=
```

Treat `./data/id_ed25519` as a secret. Back it up off the VPS. If that file is lost, the next start mints a new key and every existing client refuses to connect until you paste the new public key.

On each RustDesk client:

1. Install the app (`brew install --cask rustdesk` on a Mac).
2. Settings → Network → unlock network settings.
3. **ID Server** = `relay.example.com`.
4. **Relay Server** = leave empty. `hbbs -r` advertises the relay; the official docs discourage setting this on every client.
5. **API Server** = leave empty (Pro).
6. **Key** = the exact contents of `id_ed25519.pub`, no quotes, no trailing space.
7. Apply, then restart the app.

The status line should read `Ready (relay.example.com)`, not the public-server message.

<div class="callout callout--gotcha" markdown="1">
**Relay is server-side.** `ALWAYS_USE_RELAY=Y` is an `hbbs` environment variable. Putting a relay hostname in the client does not force relay. Two clients on the same LAN may still take a direct path on some RustDesk builds; test across two networks if you need to prove `hbbr`.
</div>

On the machine you want to control unattended: Settings → Security → enable a permanent password (16+ random characters, password manager), optionally 2FA, and grant the OS permissions RustDesk asks for (Accessibility and Screen Recording on macOS). That first permission grant needs a local screen. It cannot be done over SSH.

**Verify.** The controlled client shows `Ready (relay.example.com)` and `docker compose logs hbbs --tail=50` shows the client ID registering, with no `permission denied` or key errors.
{: .verify}

## Step 3 — Connect and prove you beat the public cutoff

From the controlling laptop, enter the nine-digit ID of the remote machine, use the permanent password, and wait for the desktop. Then do the only check that matters for this post: leave the session up for more than sixty seconds while moving the mouse.

While it is connected:

```bash
docker compose logs -f hbbr
sudo ss -tunap | grep 21117
```

With `ALWAYS_USE_RELAY=Y` you should see `hbbr` activity and established sockets on 21117. If the session is up and `hbbr` is silent, you are on P2P and have not tested the relay.

That is also why I default to relay-on. It costs server bandwidth. It makes the failure mode visible. Set `RUSTDESK_ALWAYS_USE_RELAY=N` later if you want hole-punched P2P and only fall back to `hbbr`.

**Verify.** The session is still connected at 60 seconds, `hbbr` logged traffic, and `ss` shows ESTABLISHED on 21117. That is the proof you are not on the public 30-second relay.
{: .verify}

## Failure modes

| Symptom | Cause | Repair |
| --- | --- | --- |
| Client stays on the public server message | Key has spaces/quotes, or ID Server is wrong | Paste `id_ed25519.pub` exactly; restart the app |
| TCP `nc` works, UDP 21116 fails | UFW or cloud SG missing UDP | `ufw allow 21116/udp` and the matching provider rule |
| Session starts, `hbbr` stays quiet | P2P / same LAN, or `ALWAYS_USE_RELAY` not `Y` | Confirm the env in `hbbs` logs; test from a different network |
| Containers “unhealthy” but ports listen | Image healthcheck needs a shell the image may lack | Ignore the health label; trust `ss` and `nc` |
| Every client dies after a recreate | `./data/id_ed25519` was deleted | Restore the backup, or distribute the new public key |
| IPv4 hangs after you add AAAA | Client tries A first and never falls back | Keep the hostname in the client; do not switch `RUSTDESK_PUBLIC_HOST` to a raw address unless you want one stack |

## Clean up and operating consequence

Quarterly:

```bash
docker compose pull
docker compose up -d
```

Backup recipe — the keys are under a kilobyte:

```bash
tar czf rustdesk-keys-$(date +%F).tgz -C rustdesk-server data/id_ed25519 data/id_ed25519.pub
```

To walk away from the private server, `docker compose down` and clear ID Server / Key on each client. They return to the public infrastructure in about thirty seconds per device.

If you can keep a session up for a minute through `hbbr`, you have a free private remote desktop. Add more devices the same way: same hostname, same public key, no server change.

Next, the other thing people usually want on the same VPS: [a free VPN with WireGuard](/writing/wg-easy-v15-latest-is-still-v14/).
