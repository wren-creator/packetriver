<?php
require __DIR__ . '/../lib/portal.php';
pr_start();

// Default creds clerk / clerk. Once in, the notice you post is stored raw and
// shown on the public board (stored XSS / defacement). The "published"
// confirmation code is the flag.
$err = null;
$posted = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['username'])) {
    if ($_POST['username'] === 'clerk' && $_POST['password'] === 'clerk') {
        $_SESSION['clerk'] = true;
    } else {
        $err = 'Wrong username or password.';
    }
}
if (!empty($_SESSION['clerk']) && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['body'])) {
    $st = pr_prepare('INSERT INTO announce (title, body, created) VALUES (?, ?, NOW())');
    $st->execute([$_POST['title'] ?? 'Notice', $_POST['body'] ?? '']);   // body stored raw, rendered raw
    $code = pr_query('SELECT confirm_code FROM announce_admin LIMIT 1')->fetchColumn();
    $posted = $code;
}

pr_head("Clerk's office");
if (empty($_SESSION['clerk'])) {
    ?>
<section class="portal">
  <h1>Clerk login</h1>
  <?php if ($err): ?><p class="portal-err"><?= htmlspecialchars($err) ?></p><?php endif; ?>
  <form method="post" action="admin.php">
    <label>Username <input name="username" autofocus></label>
    <label>Password <input name="password" type="password"></label>
    <button type="submit">Sign in</button>
  </form>
</section>
<?php
} else {
    echo '<h1>Post an announcement</h1>';
    if ($posted !== null) {
        echo '<p class="lede">Published. Confirmation code: <code>' . htmlspecialchars($posted) . '</code></p>';
    }
    ?>
  <form method="post" action="admin.php" class="portal">
    <label>Title <input name="title" value="Notice"></label>
    <label>Body <input name="body" size="60" placeholder="text or HTML"></label>
    <button type="submit">Publish</button>
  </form>
<?php
}
pr_foot();
