<?php
require __DIR__ . '/../lib/shopkit.php';
pr_start();

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (pr_try_login($_POST['username'] ?? '', $_POST['password'] ?? '')) {
        header('Location: .');
        exit;
    }
    $error = 'Wrong username or password.';
}
if (!pr_current_user()) {
    pr_render_portal($error);
    return;
}

$u = pr_current_user();
$rows = pr_query('SELECT id, name, price, stock FROM products ORDER BY name')->fetchAll();
$mine = pr_prepare('SELECT id FROM receipts WHERE customer = ? ORDER BY id DESC LIMIT 1');
$mine->execute([$u['username']]);
$last = $mine->fetchColumn();

pr_head('Hardware & Supply');
echo '<h1>Hardware &amp; Supply</h1><p class="lede">tools, wire, and know-how</p>';
if ($last) {
    echo '<p><a href="receipt.php?id=' . (int) $last . '">View your last receipt (#' . (int) $last . ')</a></p>';
}
echo '<table class="list"><thead><tr><th>Item</th><th>Price</th><th>Stock</th></tr></thead><tbody>';
foreach ($rows as $r) {
    printf('<tr><td>%s</td><td>$%s</td><td>%d</td></tr>',
        htmlspecialchars($r['name']), number_format((float) $r['price'], 2), (int) $r['stock']);
}
echo '</tbody></table>';
pr_foot();
