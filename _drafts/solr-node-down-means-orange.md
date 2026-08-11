---
title: "In SolrCloud, a node down means ORANGE, not down"
description: "Degraded and unavailable are different states, and SolrCloud tells you which one you are in. Plus the two-part fix for a collection BACKUP returning 500."
type: tutorial
tags: [distributed-databases]
series: failover-lab
series_order: 6
toc: true
level: intermediate
---

A two-shard, two-replica collection spread across two SolrCloud nodes reports GREEN when everything is up. Stop one node and it goes ORANGE with 4 replicas active and 2 down — and keeps answering `*:*` with `numFound 6` the entire time, because every shard still has a live replica on the surviving node. Start the node again and it recovers to GREEN on its own. Degraded is a state worth having a name for; most engines only offer working and broken.

The second half is the backup, which failed with a 500 and an access-denied message. The fix is two things and it only works if you do both: start Solr with `-Dsolr.allowPaths=/backup` in `SOLR_OPTS`, **and** make the location writable by the `solr` user with `chown solr:solr /backup`. Doing only the first gets you a permissions error that looks like the allow-list is still wrong.

The location also has to be visible to every node, which is why the lab mounts a shared volume into both containers — in production that means HDFS or S3 through a backup repository, not a local path that happens to exist on the node that answered the API call.
