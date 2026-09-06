<?php
require __DIR__ . '/../lib/shopkit.php';
// Plain storefront. The bug is a working copy of the site's git repo left in
// the web root: /drycleaner/.git/ is browsable. Dump it and read the history
// of config.php.
//   git-dumper http://<host>/drycleaner/.git/ loot && cd loot && git log -p
pr_storefront();
