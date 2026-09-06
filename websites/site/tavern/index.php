<?php
require __DIR__ . '/../lib/shopkit.php';
pr_start();

// THE BUG (default creds): the jukebox / POS admin account ships as
// admin / admin. Log in as admin and the back-office panel shows the flag.
//   hydra -l admin -P rockyou.txt <host> http-post-form ...
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (pr_try_login($_POST['username'] ?? '', $_POST['password'] ?? '')) {
        header('Location: .');
        exit;
    }
    $error = 'Wrong username or password.';
}
if (!pr_current_user()) {
    pr_render_portal($error, 'Staff / POS login.');
    return;
}

$u = pr_current_user();
pr_head('The Watering Hole');
echo '<h1>The Watering Hole</h1><p class="lede">cold beer, warm jukebox</p>';
if (($u['role'] ?? '') === 'admin') {
    echo '<div class="portal"><h2>Back office</h2>';
    echo '<p>Nightly cash drawer, jukebox playlist, supplier logins.</p>';
    echo '<p><b>POS terminal key:</b> <code>' . htmlspecialchars(pr_flag()) . '</code></p></div>';
} else {
    echo '<p>Ask a manager for the back office.</p>';
}
pr_foot();
