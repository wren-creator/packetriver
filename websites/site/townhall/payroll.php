<?php
require __DIR__ . '/../lib/portal.php';
pr_start();

// THE BUG: the payroll login builds its query by concatenation.
//   username:  ' OR '1'='1' LIMIT 1 -- -    password: anything
$err = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = $_POST['username'] ?? '';
    $p = $_POST['password'] ?? '';
    $sql = "SELECT * FROM payroll_users WHERE username = '$u' AND password_hash = '" . md5($p) . "' LIMIT 1";
    if (pr_query($sql)->fetch()) {
        $_SESSION['payroll'] = true;
        header('Location: payroll.php');
        exit;
    }
    $err = 'Login failed.';
}

pr_head('Payroll');
if (empty($_SESSION['payroll'])) {
    ?>
<section class="portal">
  <h1>Payroll login</h1>
  <?php if ($err): ?><p class="portal-err"><?= htmlspecialchars($err) ?></p><?php endif; ?>
  <form method="post" action="payroll.php">
    <label>Username <input name="username" autofocus></label>
    <label>Password <input name="password" type="password"></label>
    <button type="submit">Sign in</button>
  </form>
</section>
<?php
} else {
    echo '<h1>Payroll</h1><p class="lede">Payslip archive.</p><ul>';
    foreach (glob(__DIR__ . '/payslips/*.txt') as $f) {
        $b = basename($f);
        echo '<li><a href="payslip.php?doc=' . urlencode($b) . '">' . htmlspecialchars($b) . '</a></li>';
    }
    echo '</ul>';
}
pr_foot();
