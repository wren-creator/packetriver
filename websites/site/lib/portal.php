<?php
// Login portal + page chrome, shared by every Main Street site. Links are
// relative so the same code works under /generalstore/, /hardware/, etc.

require_once __DIR__ . '/db.php';

const SHOP_META = [
    'generalstore' => ['name' => 'General Store', 'tag' => 'daily goods since 1961'],
    'hardware'     => ['name' => 'Hardware & Supply', 'tag' => 'tools, wire, and know-how'],
    'pharmacy'     => ['name' => 'Riverside Pharmacy', 'tag' => 'prescriptions & sundries'],
    'diner'        => ['name' => 'The Daily Grind', 'tag' => 'coffee, pie, open wi-fi'],
    'barber'       => ['name' => 'Two Chairs Barbershop', 'tag' => 'walk-ins welcome'],
    'tavern'       => ['name' => 'The Watering Hole', 'tag' => 'cold beer, warm jukebox'],
    'drycleaner'   => ['name' => 'Packet River Cleaners', 'tag' => 'in by 9, out by 5'],
    'baittackle'   => ['name' => 'Bait & Tackle', 'tag' => 'gear for the swimming hole'],
    'townhall'     => ['name' => 'Packet River Town Hall', 'tag' => 'pop. 646'],
    'police'       => ['name' => 'Packet River PD', 'tag' => 'non-emergency: dispatch'],
    'fire'         => ['name' => 'Packet River Fire Dept', 'tag' => 'station 1'],
];

function pr_meta(): array
{
    return SHOP_META[pr_shop()] ?? ['name' => ucfirst(pr_shop()), 'tag' => ''];
}

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
    $_SESSION['user'] = [
        'id' => (int) $row['id'],
        'username' => $row['username'],
        'role' => $row['role'] ?? 'customer',
    ];
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
        header('Location: .');
        exit;
    }
}

function pr_head(string $title): void
{
    $u = pr_current_user();
    $m = pr_meta();
    ?><!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($title) ?> &middot; <?= htmlspecialchars($m['name']) ?></title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="shop-top">
  <a class="brand" href="."><?= strtoupper(htmlspecialchars($m['name'])) ?></a>
  <?php if ($u): ?>
    <form class="search" action="search.php" method="get">
      <input type="text" name="q" placeholder="Search&hellip;"
             value="<?= isset($_GET['q']) ? htmlspecialchars($_GET['q']) : '' ?>">
      <button type="submit">Search</button>
    </form>
    <nav><span><?= htmlspecialchars($u['username']) ?><?= $u['role'] === 'staff' || $u['role'] === 'admin' ? ' (' . $u['role'] . ')' : '' ?></span>
      <a href="logout.php">Log out</a></nav>
  <?php endif; ?>
</header>
<main>
<?php
}

function pr_foot(): void
{
    ?>
</main>
<footer class="shop-foot"><a href="/">&larr; Main Street</a> &nbsp;&middot;&nbsp;
  <?= htmlspecialchars(pr_meta()['name']) ?> &mdash; a training target, do not deploy on a routable network</footer>
</body>
</html>
<?php
}

// Parameterised customer login - the safe default. Individual portals that
// teach an auth-bypass override this with a concatenated query.
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

function pr_render_portal(?string $error = null, string $note = 'Sign in to browse and order. Staff use the same form.'): void
{
    pr_head('Login');
    ?>
<section class="portal">
  <h1>Login</h1>
  <p class="portal-note"><?= htmlspecialchars($note) ?></p>
  <?php if ($error): ?><p class="portal-err"><?= htmlspecialchars($error) ?></p><?php endif; ?>
  <form method="post" action=".">
    <label>Username <input type="text" name="username" autofocus required></label>
    <label>Password <input type="password" name="password" required></label>
    <button type="submit">Sign in</button>
  </form>
  <?php if (is_readable(__DIR__ . '/../' . pr_shop() . '/register.php')): ?>
    <p class="portal-alt">No account? <a href="register.php">Register</a>.</p>
  <?php endif; ?>
</section>
<?php
    pr_foot();
}
