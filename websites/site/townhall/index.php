<?php
require __DIR__ . '/../lib/portal.php';

// Public announcements board. The body is rendered raw - a defaced notice
// posted through /townhall/admin.php shows up here for the whole town.
$rows = pr_query('SELECT title, body, created FROM announce ORDER BY id DESC')->fetchAll();
pr_head('Announcements');
?>
<h1>Town Hall &mdash; Announcements</h1>
<p class="lede">Notices from the Clerk's office. Also here:
  <a href="admin.php">clerk login</a> &middot; <a href="payroll.php">payroll</a>.</p>
<?php foreach ($rows as $r): ?>
  <article class="notice">
    <h2><?= htmlspecialchars($r['title']) ?></h2>
    <div><?= $r['body'] ?></div>
    <small><?= htmlspecialchars($r['created']) ?></small>
  </article>
<?php endforeach; ?>
<?php
pr_foot();
