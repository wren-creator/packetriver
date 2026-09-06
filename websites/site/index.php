<?php
require_once __DIR__ . '/lib/portal.php';
pr_start();

// POST to "/" = a portal login attempt.
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = $_POST['username'] ?? '';
    $p = $_POST['password'] ?? '';
    if (pr_try_login($u, $p)) {
        header('Location: /');
        exit;
    }
    $error = 'Wrong username or password.';
}

if (!pr_current_user()) {
    pr_render_portal($error);
    exit;
}

// --- logged in: the storefront ------------------------------------------
$rows = pr_query('SELECT id, name, price, stock FROM products ORDER BY name')->fetchAll();
pr_head('Catalogue');
?>
<h1>Today at the General Store</h1>
<p class="lede">Use the search box up top to find something. It searches product
   names.</p>
<table class="list">
  <thead><tr><th>Item</th><th>Price</th><th>In stock</th></tr></thead>
  <tbody>
  <?php foreach ($rows as $r): ?>
    <tr>
      <td><?= htmlspecialchars($r['name']) ?></td>
      <td>$<?= number_format((float) $r['price'], 2) ?></td>
      <td><?= (int) $r['stock'] ?></td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
<?php
pr_foot();
