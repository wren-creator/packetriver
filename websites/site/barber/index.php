<?php
require __DIR__ . '/../lib/shopkit.php';
pr_start();
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (pr_try_login($_POST['username'] ?? '', $_POST['password'] ?? '')) {
        header('Location: .');
        exit;
    }
    $error = 'Wrong username or password.';
}
if (!pr_current_user()) {
    pr_render_portal($error, 'Sign in to request an appointment.');
    return;
}
pr_head('Two Chairs Barbershop');
echo '<h1>Two Chairs Barbershop</h1><p class="lede">walk-ins welcome</p>';
echo '<p><a href="book.php">Request an appointment</a></p>';
pr_foot();
