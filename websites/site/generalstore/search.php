<?php
require __DIR__ . '/../lib/shopkit.php';

// THE BUG: `q` is concatenated into `... WHERE name LIKE '%$q%'` (3 columns
// for a clean UNION), a broken quote drops the SQL into the page, and the
// term is reflected unencoded. The flag is a row of `staff_notes`, which has
// no page of its own:
//   q=x%' UNION SELECT 1,note,1 FROM staff_notes-- -
pr_vuln_search();
