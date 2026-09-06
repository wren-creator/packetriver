<?php
require __DIR__ . '/../lib/shopkit.php';
// Plain storefront. The bug here is not in the app: a database backup got
// left in the web root. Try /diner/db_backup.sql  (Phase 5 also opens the
// Diner's open Wi-Fi as a separate lane.)
pr_storefront();
