---
title: "pgBackRest against a Patroni cluster: archive, rebuild, and restore"
description: "Wire pgBackRest into a running Patroni cluster over mutual TLS with Ansible, then prove it: full backup, replica rebuilt from the repo, and a point-in-time restore."
date: 2026-08-14 16:30:00 +0545
type: tutorial
tags: [postgres, distributed-databases]
series: rhel8-pg-ansible
series_order: 3
toc: true
cover:
  base: "/assets/images/editorial-pgbackrest-patroni-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Topology diagram: a pgBackRest repository declaring both cluster members, with archive_mode living in the DCS and create_replica_methods in the local Patroni config"
  caption: "The repo declares every member, not the primary. Which node is writable is a question pgBackRest asks at run time."
featured: true
level: intermediate
time_estimate: "~90 min on an existing cluster; the restore drill itself is ~15 min"
what_youll_build: "pgBackRest wired into a two-node Patroni cluster by Ansible over mutual TLS: archiving through the DCS, a full backup, a replica rebuilt from the repo, and a point-in-time restore of a dropped table."
prerequisites:
  - "The Patroni cluster from part 2 of this series, running PostgreSQL 18 with etcd"
  - "Ansible on the control node (ansible-core 2.15.x against RHEL-family guests)"
  - "Enough repo disk for one full backup plus WAL — 3 GB is plenty for a lab"
tested_on: "Rocky Linux 8 · amd64 under QEMU on Apple Silicon · PostgreSQL 18.6 (PGDG) · Patroni 4.1.5 · pgBackRest 2.59.0 over mutual TLS on 8432 · etcd 3.7.0 · ansible-core 2.15.13 · 192.168.105.140–142"
key_takeaways:
  - "Cluster-wide settings go in the DCS via edit-config; create_replica_methods names a local command so it stays in patroni.yml."
  - "archive_mode is postmaster-level: edit-config is not enough, Patroni raises a Pending restart flag and you must do a rolling restart."
  - "patronictl pause plus systemctl stop patroni does not stop PostgreSQL, and pgBackRest refuses to restore over a running server."
  - "After a point-in-time restore, take a fresh full backup before rebuilding replicas or they will ask for a timeline history that no longer exists."
  - "TLS is time-sensitive and TCG guests drift: 76 minutes of skew surfaced as `sslv3 alert bad certificate`, not as anything about clocks."
---

## The thing that makes this different from single-node backup

Backing up one PostgreSQL server is a solved problem with a well-worn runbook. Backing up a Patroni cluster is the same tool pointed at a target that moves: the primary is whichever node currently holds the leader key, and that can change between two backups without anyone touching a config file.

So the repository is not configured against "the primary". It is configured against *every member*, and pgBackRest works out which one is writable when it runs. That single decision is what makes the setup survive a failover, and it is visible in the very first command's output.

Everything here is Ansible. Part 1 of this series established the rule and it holds: Vagrant boots the box and wires the lab NIC; packages, configuration, services and certificates belong to Ansible, because a lab you fixed by hand is a lab you cannot rebuild.

The cluster is the one from [part 2](/writing/patroni-postgresql-18-rocky8-etcd-failover/) — `pgn1` and `pgn2` on PostgreSQL 18.6 with etcd on `etcd1`. The repository lives on `etcd1` as well, which is a lab economy and not a recommendation: in production the DCS and the backup repository are separate failure domains, and the repo does not sit on a database host at all.

## Step 1 — One repo, every member declared

The Ansible play installs pgBackRest on all three nodes, then writes a repository config that lists both cluster members:

```jinja
[global]
repo1-path={{ pgbackrest_repo_path }}
repo1-retention-full=2
start-fast=y

[{{ pgbackrest_stanza }}]
{% for m in patroni_members %}
pg{{ loop.index }}-host={{ m.ip }}
pg{{ loop.index }}-host-user={{ pgbackrest_user }}
pg{{ loop.index }}-path={{ pg_data_dir }}
pg{{ loop.index }}-port={{ pg_port }}
{% endfor %}
```
{: data-file="roles — repo host /etc/pgbackrest.conf"}

Transport is mutual TLS, the same as part 1, and it is the better answer for a cluster: no shell account on the peers, and authorisation is an explicit CN allow-list rather than "whatever the postgres unix user can reach over ssh". Each side names the other:

```ini
tls-server-address=*
tls-server-port=8432
tls-server-cert-file=/etc/pgbackrest/certs/etcd1.crt
tls-server-key-file=/etc/pgbackrest/certs/etcd1.key
tls-server-ca-file=/etc/pgbackrest/certs/ca.crt
tls-server-auth=pgn1=pg18lab
tls-server-auth=pgn2=pg18lab
```
{: data-file="repo host — the allow-list"}

The database hosts get the mirror image, plus asynchronous archiving so `archive_command` never becomes the cluster's write ceiling. They run a TLS server too, because the repo reaches *back* to them when it takes a backup:

```ini
[global]
repo1-host=192.168.105.140
repo1-host-type=tls
repo1-host-port=8432
repo1-host-ca-file=/etc/pgbackrest/certs/ca.crt
repo1-host-cert-file=/etc/pgbackrest/certs/pgn1.crt
repo1-host-key-file=/etc/pgbackrest/certs/pgn1.key
archive-async=y
spool-path=/var/spool/pgbackrest

tls-server-auth=etcd1=pg18lab
```
{: data-file="database hosts /etc/pgbackrest.conf"}

A certificate signed by the CA but missing from `tls-server-auth` authenticates fine and is then refused. That is the behaviour you want, and it is worth knowing before you meet the error.

Name the stanza after the Patroni scope. pgBackRest thinks in stanzas and Patroni thinks in scopes; keeping them identical saves a future reader wondering whether they are the same thing.

**Verify.** The playbook is clean across all three hosts:

```text
etcd1  : ok=9  changed=4  unreachable=0  failed=0
pgn1   : ok=7  changed=3  unreachable=0  failed=0
pgn2   : ok=7  changed=3  unreachable=0  failed=0
```
{: .verify }

## Step 1b — Clocks, before certificates

This cost the most time of anything in the build, and the error points nowhere near the cause:

```text
WARN: unable to check pg1: [ServiceError] TLS error [1:336151570] sslv3 alert bad certificate
ERROR: [027]: no database found
```

The certificates were fine. The CA fingerprint matched on every host. What did not match was the time:

```text
control node (Mac):  2026-08-14 16:24:33 UTC
  etcd1              2026-08-14 16:24:34 UTC
  pgn1               2026-08-14 15:07:59 UTC
  pgn2               2026-08-14 15:08:00 UTC
CA notBefore:        Aug 14 16:16:14 2026 GMT
```

Both database nodes were **76 minutes behind**. The CA was issued on the Mac at 16:16, so from their point of view it was not yet valid, and `openssl verify` says so plainly once you ask it directly:

```text
error 9 at 1 depth lookup: certificate is not yet valid
```

TCG guests drift badly, and chronyd *slews* rather than steps, so it corrects a large offset far too slowly to help. Step the clock, and do it before anything issues a certificate:

```yaml
- name: Force an immediate step
  ansible.builtin.command: chronyc -a makestep

- name: Fail if still skewed from the control node
  ansible.builtin.assert:
    that: "(guest_epoch.stdout | int - control_epoch | int) | abs < 120"
    fail_msg: "{{ inventory_hostname }} is too far from the control node; certificates will not validate."
```
{: data-file="playbooks/05_pgbackrest_tls.yml"}

The assertion matters more than the `makestep`. A silent 76-minute skew turns into a TLS error an hour later; a failed assertion names the problem at the point it exists.

**Verify.** With clocks stepped, the handshake works and `check` proves the whole path:

```text
INFO: check repo1 (standby)
INFO: switch wal not performed because this is a standby
INFO: check repo1 configuration (primary)
INFO: WAL segment 00000004000000000000000F successfully archived ... on repo1
INFO: check command end: completed successfully (2560ms)
```
{: .verify }

## Step 2 — Two settings, two different homes

This is where most integrations quietly break, and the split is not arbitrary.

`archive_mode` and `archive_command` describe the whole cluster, so they belong in the **DCS**. Patroni regenerates `postgresql.conf` from the DCS every time it starts a node — so an `archive_command` typed straight into that file works perfectly until the first failover, then vanishes at exactly the moment you need it.

```yaml
- name: Push archive settings into the DCS
  ansible.builtin.shell: |
    cat <<'YML' | patronictl -c {{ patroni_config }} edit-config --force --apply -
    postgresql:
      parameters:
        archive_mode: "on"
        archive_command: "pgbackrest --stanza={{ pgbackrest_stanza }} archive-push %p"
        archive_timeout: 60
    YML
  become_user: postgres
  run_once: true
```
{: data-file="playbooks/04_patroni_archive.yml"}

`create_replica_methods` is the opposite. It names a *command on that host*, so it cannot live in shared cluster state and goes into the local `patroni.yml`:

```yaml
create_replica_methods:
  - pgbackrest
  - basebackup
pgbackrest:
  command: "/usr/bin/pgbackrest --stanza=pg18lab --delta restore"
  keep_data: true
  no_params: true
```
{: data-file="/etc/patroni/patroni.yml"}

Order matters. With `pgbackrest` first, a new replica clones from the repository; `basebackup` stays as the fallback. Without it, every rebuild drags a full copy off the primary while that primary is serving traffic.

## Step 3 — The restart nobody mentions

Apply the config and check whether PostgreSQL actually took it:

```bash
psql -tAc "SELECT name||' = '||setting FROM pg_settings
           WHERE name IN ('archive_mode','archive_command','archive_timeout');"
```

```text
archive_command = (disabled)
archive_mode = off
archive_timeout = 60
```

The DCS has the right values and the server does not. `archive_timeout` is reloadable so it applied; `archive_mode` is a postmaster-level parameter and needs a full restart. Patroni knows, and says so:

```text
| Member | Role    | State     | TL | Pending restart | Pending restart reason |
| pgn1   | Replica | streaming |  3 | *               | archive_mode: off->on  |
| pgn2   | Leader  | running   |  3 | *               | archive_mode: off->on  |
```

A rolling restart through `patronictl` handles the replica first and the leader last, so the write outage is one brief switchover rather than the whole cluster:

```bash
patronictl -c /etc/patroni/patroni.yml restart pg18lab --force
```

**Verify.** The flag clears and archiving is live:

```text
archive_command = pgbackrest --stanza=pg18lab archive-push %p
archive_mode = on
```
{: .verify }

## Step 4 — Stanza, check, and the first backup

Run these from the repository host. `stanza-create` initialises the repo layout; `check` proves a WAL segment can actually make the trip.

```bash
sudo -u postgres pgbackrest --stanza=pg18lab stanza-create
sudo -u postgres pgbackrest --stanza=pg18lab check
```

**Verify.** Read the `check` output closely, because it contains the proof that the multi-host config works:

```text
INFO: switch wal not performed because this is a standby
INFO: check repo1 configuration (primary)
INFO: WAL segment 000000030000000000000004 successfully archived to
      '/var/lib/pgbackrest/archive/pg18lab/18-1/...' on repo1
INFO: check command end: completed successfully (6795ms)
```
{: .verify }

pgBackRest probed both declared hosts, found one in recovery, skipped it, and did the WAL switch on the primary. Nothing told it which node was the leader.

```bash
sudo -u postgres pgbackrest --stanza=pg18lab --type=full backup
```

```text
INFO: backup start archive = 000000030000000000000006, lsn = 0/6000060
INFO: new backup label = 20260814-141156F
INFO: full backup size = 22.7MB, file total = 981
INFO: backup command end: completed successfully (23910ms)
```

The repo stored 2.9 MB for a 22.7 MB database — compression is on by default and worth knowing before you size the volume.

## Step 5 — Rebuild a replica from the repository

The first restore drill is the cheap one, and it is the one you will actually use: throw a replica away and let Patroni rebuild it.

```bash
patronictl -c /etc/patroni/patroni.yml reinit pg18lab pgn1 --force
```

**Verify.** The Patroni journal on the rebuilt node names the method, which is the only way to know it did not silently fall back to `pg_basebackup`:

```text
INFO: restore command begin 2.59.0: --delta --repo1-host=192.168.105.140 ... --stanza=pg18lab
INFO: restore command end: completed successfully (5020ms)
INFO: replica has been created using pgbackrest
```
{: .verify }

Five seconds, and the primary was never touched. On a database where a full copy would take hours across a busy link, that difference is the entire reason to wire the two tools together.

## Step 6 — Point-in-time restore of a dropped table

Now the drill people actually rehearse for. Note a timestamp, then break something:

```sql
SELECT now();                     -- 2026-08-14 14:15:20.119249+00
DROP TABLE failover_probe;        -- the accident
SELECT pg_switch_wal();           -- make sure the damage is archived
```

Patroni must be told to stand down first, or it will fight the restore by restarting PostgreSQL underneath you:

```bash
patronictl -c /etc/patroni/patroni.yml pause --wait
```

Then stop PostgreSQL — and this is the step that catches people. Pausing Patroni and stopping the *service* does **not** stop the database. That is what pause means: Patroni stops managing, PostgreSQL keeps serving.

```text
ERROR: [038]: unable to restore while PostgreSQL is running
```

Stop it properly on both nodes, then restore the leader to the moment before the drop:

```bash
sudo -u postgres /usr/pgsql-18/bin/pg_ctl -D /var/lib/pgsql/18/data -m fast stop

sudo -u postgres pgbackrest --stanza=pg18lab --delta --type=time \
  --target='2026-08-14 14:15:20' --target-action=promote restore
```

```text
INFO: repo1: restore backup set 20260814-141156F, recovery will start at 2026-08-14 14:11:56
INFO: restore command end: completed successfully (4198ms)
```

Start the server and let it replay forward to the target:

```bash
sudo -u postgres /usr/pgsql-18/bin/pg_ctl -D /var/lib/pgsql/18/data -w -t 300 start
```

**Verify.** The table is back, on a new timeline, and out of recovery:

```text
in recovery: f
timeline:    4
table back:  t
row count:   5

 id |              note
----+---------------------------------
  1 | written on pgn1 before kill
 34 | written on pgn2 after promotion
 35 | after etcd recovery
 36 | before replica reinit
 37 | the row we must not lose
```
{: .verify }

## Step 7 — The gotcha after a PITR

Resume Patroni, start the other node, and rebuild it — and it hangs in `starting` forever:

```text
LOG:  fetching timeline history file for timeline 3 from primary server
FATAL: could not receive timeline history file from the primary server:
       ERROR: could not open file "pg_wal/00000003.history": No such file or directory
```

The replica restored from a backup whose base is on **timeline 3** and is asking the leader for that timeline's history. After the point-in-time restore the leader is on timeline 4 and never had the file. `archive-get` cannot supply it either, because archiving was switched on *after* the cluster had already reached timeline 3 — so that history file was never archived at all.

The fix is not a flag. It is an ordering rule: **after a point-in-time restore, take a fresh full backup before rebuilding any replica.** The new backup's base is on the current timeline, so nothing has to reach backwards.

```bash
sudo -u postgres pgbackrest --stanza=pg18lab --type=full backup
patronictl -c /etc/patroni/patroni.yml reinit pg18lab pgn1 --force
```

**Verify.** Both members on timeline 4, streaming, and both holding the recovered rows:

```text
| Member | Host            | Role    | State     | TL | Replay LSN | Lag |
| pgn1   | 192.168.105.141 | Replica | streaming |  4 | 0/E000060  |   0 |
| pgn2   | 192.168.105.142 | Leader  | running   |  4 |            |     |

  .141: 5 rows
  .142: 5 rows
```
{: .verify }

## Failure modes worth knowing

| Symptom | Cause | Repair |
|---|---|---|
| `archive_command` disabled after edit-config | `archive_mode` is postmaster-level | Rolling `patronictl restart`; watch the Pending restart column |
| archive settings vanish after a failover | Written into `postgresql.conf` by hand | Put them in the DCS with `edit-config` |
| `unable to restore while PostgreSQL is running` | pause and stop-service do not stop the database | `pg_ctl -m fast stop` on every node first |
| Replica stuck `starting`, wants `0000000N.history` | Backup base predates the current timeline | Fresh full backup after the PITR, then reinit |
| Replica rebuild is slow and loads the primary | `create_replica_methods` missing or wrong order | List `pgbackrest` before `basebackup` in the local yml |
| `check` reports the wrong host as primary | Only one `pgN-host` declared | Declare every member; the primary moves |
| `sslv3 alert bad certificate`, certs look correct | Guest clock behind the CA's notBefore | `chronyc -a makestep`, then assert the offset |
| Peer authenticates then is refused | CN missing from `tls-server-auth` | Add `tls-server-auth=<CN>=<stanza>` on the receiving side |

## What this buys you

The cluster now survives three separate things, and they are worth naming separately because they fail separately. A node dying is handled by Patroni, in about twenty seconds, from part 2. A replica needing to come back is handled by pgBackRest in five seconds without touching the primary. And an operator error — the dropped table — is handled by a point-in-time restore that recovered every row.

Only the first of those is automatic. The other two are drills, and a drill you have not run is a plan, not a capability. The useful outcome of this post is not the config; it is that the restore was performed once, on purpose, while nothing was actually on fire.
