<?php
// The login portal + page chrome for the General Store. Every Packet River
// target shows a portal like this first (styled after the Cross Creek HMI
// logons and widgetorium's login.php). Getting a session is the first move;
// the scored bug is the SQL injection in the authenticated search.

require_once __DIR__ . '/db.php';

function pr_start(): void
{
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
}

function pr_current_user(): ?array
{
    pr_start();
    return $_SESSION['user'] ?? null;
}

function pr_login_user(array $row): void
{
    pr_start();
    $_SESSION['user'] = ['id' => (int) $row['id'], 'username' => $row['username']];
}

function pr_logout(): void
{
    pr_start();
    $_SESSION = [];
    session_destroy();
}

function pr_require_login(): void
{
    if (!pr_current_user()) {
        header('Location: /');
        exit;
    }
}

// Parameterised on purpose: the portal is the recognisable front door, not the
// Phase 1 target. Seeded account: shopper / shopper.
function pr_try_login(string $u, string $p): bool
{
    $st = pr_prepare('SELECT * FROM users WHERE username = ? AND password_hash = ? LIMIT 1');
    $st->execute([$u, md5($p)]);
    $row = $st->fetch();
    if ($row) {
        pr_login_user($row);
        return true;
    }
    return false;
}

function pr_head(string $title): void
{
    $u = pr_current_user();
    ?><!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($title) ?> &middot; Packet River General Store</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="shop-top">
  <a class="brand" href="/">PACKET RIVER GENERAL STORE</a>
  <?php if ($u): ?>
    <form class="search" action="/search.php" method="get">
      <input type="text" name="q" placeholder="Search the shelves&hellip;"
             value="<?= isset($_GET['q']) ? htmlspecialchars($_GET['q']) : '' ?>">
      <button type="submit">Search</button>
    </form>
    <nav><span><?= htmlspecialchars($u['username']) ?></span>
      <a href="/logout.php">Log out</a></nav>
  <?php endif; ?>
</header>
<main>
<?php
}

function pr_foot(): void
{
    ?>
</main>
<footer class="shop-foot">Packet River General Store &middot; est. 1961 &middot; a training target, do not deploy on a routable network</footer>
</body>
</html>
<?php
}

function pr_render_portal(?string $error = null): void
{
    pr_head('Staff & account login');
    ?>
<section class="portal">
  <h1>Login</h1>
  <p class="portal-note">Sign in to browse the catalogue and place orders.
     Staff use the same form.</p>
  <?php if ($error): ?><p class="portal-err"><?= htmlspecialchars($error) ?></p><?php endif; ?>
  <form method="post" action="/">
    <label>Username <input type="text" name="username" autofocus required></label>
    <label>Password <input type="password" name="password" required></label>
    <button type="submit">Sign in</button>
  </form>
  <p class="portal-alt">No account? <a href="/register.php">Register</a>.</p>
</section>
<?php
    pr_foot();
}
