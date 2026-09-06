<?php
require __DIR__ . '/../lib/portal.php';
pr_start();

// THE BUG (default creds): the station alarm panel takes admin / fire.
$err = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (($_POST['username'] ?? '') === 'admin' && ($_POST['password'] ?? '') === 'fire') {
        $_SESSION['fire'] = true;
    } else {
        $err = 'Wrong username or password.';
    }
}

pr_head('Station 1 alarm panel');
if (empty($_SESSION['fire'])) {
    ?>
<section class="portal">
  <h1>Alarm panel login</h1>
  <?php if ($err): ?><p class="portal-err"><?= htmlspecialchars($err) ?></p><?php endif; ?>
  <form method="post" action=".">
    <label>Username <input name="username" autofocus></label>
    <label>Password <input name="password" type="password"></label>
    <button type="submit">Sign in</button>
  </form>
</section>
<?php
} else {
    echo '<h1>Packet River Fire Dept &mdash; Station 1</h1>';
    echo '<div class="portal"><h2>Panel</h2>';
    echo '<p>Zones: 4 &nbsp; Trouble: 0 &nbsp; Battery: OK</p>';
    echo '<p><b>Panel programming key:</b> <code>' . htmlspecialchars(pr_flag('fire_defaultcreds')) . '</code></p>';
    echo '</div>';
}
pr_foot();
