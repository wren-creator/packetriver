<?php
require __DIR__ . '/../lib/portal.php';
pr_require_login();

// THE BUG (IDOR): any logged-in customer can pull ANY receipt by id. There is
// no check that the receipt belongs to the caller. Receipts are numbered from
// 1001; walk them. One of them carries the flag in its notes.
//   for i in $(seq 1001 1040); do curl -s -b cookie "receipt.php?id=$i"; done
$id = (int) ($_GET['id'] ?? 0);
$r = pr_query("SELECT * FROM receipts WHERE id = $id")->fetch();

pr_head('Receipt');
if (!$r) {
    echo '<p>No such receipt.</p>';
} else {
    echo '<h1>Receipt #' . (int) $r['id'] . '</h1>';
    echo '<table class="list"><tbody>';
    echo '<tr><td>Customer</td><td>' . htmlspecialchars($r['customer']) . '</td></tr>';
    echo '<tr><td>Total</td><td>$' . htmlspecialchars($r['total']) . '</td></tr>';
    echo '<tr><td>Notes</td><td>' . htmlspecialchars($r['notes']) . '</td></tr>';
    echo '</tbody></table>';
}
echo '<p><a href=".">Back</a></p>';
pr_foot();
