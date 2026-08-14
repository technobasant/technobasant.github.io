---
title: "Orchestrated failover and a restore I actually performed"
hook: "A production-shaped Postgres cluster on one laptop: killed the primary, rebuilt the replica, recovered a dropped table"
description: "A Rocky 8 VM cluster running Patroni, etcd and pgBackRest over mutual TLS, built entirely by Ansible, where every failure and recovery claim was measured rather than assumed."
kind: lab
order: 5
featured: true
role: "Personal lab"
org: "Personal"
period: "2026"
team: "One person"
scale: "Three amd64 Rocky 8 guests under QEMU on Apple Silicon; PostgreSQL 18.6, Patroni 4.1.5, etcd 3.7.0, pgBackRest 2.59 on a shared socket_vmnet fabric"
problem: "A cluster that has never failed is a cluster whose recovery path is a hypothesis. I wanted a rig where the primary dies badly, the replica is thrown away, and a table is dropped on purpose — with the timings recorded rather than described."
decision: "Build it on VMs rather than containers so the failure modes are the ones production has, drive every byte of configuration from Ansible so the lab is rebuildable, and refuse to publish a number that did not come off a run."
flow: lab
stack: [PostgreSQL, Patroni, etcd, pgBackRest, Ansible, Rocky Linux, QEMU, Vagrant, TLS]
metrics: [lab_patroni_promotion, lab_replica_rebuild, lab_pitr_recovery]
tags: [postgres, distributed-databases, self-hosted]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

The multi-engine lab answered a comparison question: what do six different databases do when a node disappears. This one answers a narrower and more operational question about a single stack — what happens to a PostgreSQL cluster that is *managed*, when the managing layer has to make a decision under pressure.

Containers were the wrong shape for it. A Docker network cannot produce the failure modes an operator actually meets — clock drift, systemd ordering, firewalld, a package manager refusing a key import. So the rig is three amd64 virtual machines on a shared L2 fabric, running the same RHEL-family distribution and the same PostgreSQL packages as the servers this pattern is deployed on.

## Constraints

One laptop, so the whole cluster fits in about 4 GB of RAM. amd64 guests under emulation on an Apple Silicon host, which is slow on purpose: a lab that lies about the instruction set makes every later packaging story suspect.

The honest limit is etcd. It runs on one node, so this rig proves *PostgreSQL* failover, not *cluster* availability — and rather than caveat that, I measured what a DCS outage costs and published the answer.

## Architecture

Three nodes: one carrying etcd and the pgBackRest repository, two running PostgreSQL 18.6 under Patroni. Vagrant boots the boxes and wires the lab NIC; everything above that — packages, configuration, certificates, systemd units, firewall rules — belongs to Ansible. A lab fixed by hand is a lab that cannot be rebuilt, and rebuildability is the only thing that makes a measurement repeatable.

The repository declares *every* cluster member rather than a primary, because the primary moves. Transport between the repo and the database hosts is mutual TLS with an explicit certificate CN allow-list, not SSH: no shell account on the peers, and authorisation that can be read out of a config file.

## Decisions and rejected alternatives

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| VMs under emulation | Containers on the host | Systemd, firewalld, chrony and package managers are where the real failures live | Slow: hours for a first bring-up |
| Rocky 8 | Unregistered RHEL 8 | An unregistered RHEL box has no AppStream, so no python3.12, so no current Patroni at all | One paragraph of explanation in every post |
| Ansible for all configuration | Shell over SSH | The lab has been rebuilt several times; each rebuild is a command, not an afternoon | Slower to write the first time |
| Mutual TLS between repo and nodes | SSH keys | No shell accounts, and authorisation is an explicit allow-list | Certificate lifecycle, and a clock-skew failure that cost real time |
| Single etcd node | Three-node quorum | Fits the RAM budget, and the resulting limitation is measurable rather than hypothetical | The rig cannot claim cluster availability |

## Results

Three claims, each with a number that came off a run.

**Promotion.** A `SIGKILL` of the leader — not a graceful stop, which is the easy case — produced a promoted replica in {{ site.data.metrics.lab_patroni_promotion.value }}, with the timeline advancing 1 to 2. The old primary rejoined afterwards via `pg_rewind` from the last common checkpoint rather than a full re-clone.

**Replica rebuild.** Discarding a replica and letting Patroni rebuild it from the backup repository took {{ site.data.metrics.lab_replica_rebuild.value }}, and the Patroni journal names the method rather than leaving it to inference. The primary was never read during the rebuild, which is the entire reason to wire the two tools together.

**Restore.** A deliberately dropped table was recovered by point-in-time restore with {{ site.data.metrics.lab_pitr_recovery.value }} rows intact, ending on a new timeline.

The most useful result was not a success. Stopping the single etcd node did not merely remove protection — the healthy leader demoted itself and the cluster went read-only within about 45 seconds, because Patroni could not renew the leader key and correctly refused to accept writes. That is the argument for a three-node DCS, and it is stronger as a measurement than as advice.

## Operating consequence

Two settings decided whether recovery was cheap or expensive, and neither can be added usefully during an incident: `use_pg_rewind` with data checksums, which is the difference between a rejoin and a rebuild; and `create_replica_methods` ordering pgBackRest ahead of `basebackup`, which is the difference between restoring from a repository and dragging a full copy off a primary that is serving traffic.

A third is an ordering rule rather than a setting: after a point-in-time restore, take a fresh full backup *before* rebuilding any replica, or it will ask the restored leader for a timeline history file that no longer exists.

## What I would do differently

**Three etcd nodes.** The single-node DCS is the one place this rig cannot speak to production, and the read-only demotion showed exactly why.

**Load during failover.** Every measurement here happened on an idle cluster. A background writer during the kill would make the promotion and rewind numbers mean considerably more.

**Automate the restore drill.** The point-in-time recovery was performed by hand, which means it is a thing I have done rather than a thing that is tested. A scheduled restore into a scratch instance, with the row count asserted, would turn it into a capability.

The full build is written up as a three-part series: [the lab fabric](/writing/amd64-vagrant-labs-apple-silicon-socket-vmnet/), [Patroni HA and the failover measurements](/writing/patroni-postgresql-18-rocky8-etcd-failover/), and [pgBackRest, backup and the restore](/writing/pgbackrest-patroni-cluster-backup-pitr/).
