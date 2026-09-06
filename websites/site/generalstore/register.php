<?php
require __DIR__ . '/../lib/portal.php';
pr_start();

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = trim($_POST['username'] ?? '');
    $p = $_POST['password'] ?? '';
    if (!preg_match('/^[A-Za-z0-9_.-]{3,32}$/', $u)) {
        $error = 'Username: 3-32 chars, letters/digits/._-';
    } elseif (strlen($p) < 4) {
        $error = 'Password must be at least 4 characters.';
    } else {
        try {
            $st = pr_prepare('INSERT INTO users (username, password_hash, role) VALUES (?, ?, "customer")');
            $st->execute([$u, md5($p)]);
            $st2 = pr_prepare('SELECT * FROM users WHERE username = ?');
            $st2->execute([$u]);
            pr_login_user($st2->fetch());
            header('Location: .');
            exit;
        } catch (PDOException $e) {
            $error = 'That username is taken.';
        }
    }
}

pr_head('Register');
?>
<section class="portal">
  <h1>Create an account</h1>
  <?php if ($error): ?><p class="portal-err"><?= htmlspecialchars($error) ?></p><?php endif; ?>
  <form method="post" action="register.php">
    <label>Username <input type="text" name="username" autofocus required></label>
    <label>Password <input type="password" name="password" required></label>
    <button type="submit">Register</button>
  </form>
  <p class="portal-alt"><a href=".">Back to login</a></p>
</section>
<?php
pr_foot();
