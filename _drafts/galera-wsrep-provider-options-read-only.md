---
title: "Galera recovery when wsrep_provider_options is read-only"
description: "The canonical pc.bootstrap recovery fails on MariaDB 11.8 because the variable is read-only at runtime. What to do instead, and why quorum is not symmetric."
type: tutorial
tags: [distributed-databases]
series: failover-lab
series_order: 4
toc: true
level: advanced
---

Every Galera recovery guide tells you to bootstrap the most advanced survivor with `SET GLOBAL wsrep_provider_options='pc.bootstrap=YES'`. On the MariaDB 11.8 build in this lab that variable is read-only at runtime, so recovery goes through restarting that node as a new cluster with `galera_new_cluster` or `--wsrep-new-cluster` instead.

Evidence from the rig: 150 concurrent cross-master UPDATEs of one row produced 3 certification failures on node2 and 5 certification failures plus 2 brute-force aborts on node3, and the counter still converged to 300 on all three nodes — optimistic concurrency caught every conflict at commit time and the arithmetic came out right.

The other half is that quorum is not symmetric. Stopping galera3 and then galera2 gracefully left the survivor at `wsrep_cluster_size 1` and still `Primary`, because a graceful leave shrinks the Primary Component cleanly. Killing the same two nodes ungracefully left the survivor `non-Primary`, rejecting writes with `ERROR 1047 "WSREP has not yet prepared node for application use"`. Same node count, opposite behavior, and only one of the two is a split-brain risk. Rejoin after a short absence used IST rather than a full mariabackup SST.
