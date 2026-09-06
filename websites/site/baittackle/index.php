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
$rows = pr_query('SELECT id, name, price, stock FROM products ORDER BY name')->fetchAll();
pr_head('Bait & Tackle');
echo '<h1>Bait &amp; Tackle</h1><p class="lede">gear for the swimming hole</p>';
echo '<p>Product photos are pulled live from the supplier: '
    . '<a href="fetch.php?url=http://supplier.local/img/lure.png">preview a lure</a></p>';
echo '<table class="list"><thead><tr><th>Item</th><th>Price</th><th>Stock</th></tr></thead><tbody>';
foreach ($rows as $r) {
    printf('<tr><td>%s</td><td>$%s</td><td>%d</td></tr>',
        htmlspecialchars($r['name']), number_format((float) $r['price'], 2), (int) $r['stock']);
}
echo '</tbody></table>';
pr_foot();
