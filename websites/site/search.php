<?php
require_once __DIR__ . '/lib/portal.php';
pr_require_login();

// THE BUG: the search term is concatenated straight into a LIKE clause.
//   - three columns are selected, so `UNION SELECT a,b,c` lines up cleanly
//   - a broken quote drops the raw SQL into the page (verbose errors)
//   - the term is echoed back without encoding (reflected XSS)
// The General Store's flag lives in a row of `staff_notes`, which has no page:
//   ...&q=x' UNION SELECT note,1,1 FROM staff_notes -- -
$q = $_GET['q'] ?? '';

$results = [];
if ($q !== '') {
    $sql = "SELECT id, name, price FROM products WHERE name LIKE '%$q%' ORDER BY name";
    $results = pr_query($sql)->fetchAll();
}

pr_head('Search');
?>
<h1>Search results</h1>
<?php if ($q !== ''): ?>
  <p class="lede">You searched for: <?= $q ?></p>
<?php endif; ?>

<?php if ($q === ''): ?>
  <p>Type something in the search box.</p>
<?php elseif (!$results): ?>
  <p>Nothing matched &ldquo;<?= $q ?>&rdquo;.</p>
<?php else: ?>
  <table class="list">
    <thead><tr><th>Item</th><th>Price</th></tr></thead>
    <tbody>
    <?php foreach ($results as $r): ?>
      <tr>
        <td><?= htmlspecialchars((string) $r['name']) ?></td>
        <td>$<?= htmlspecialchars((string) $r['price']) ?></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
<?php endif; ?>
<?php
pr_foot();
