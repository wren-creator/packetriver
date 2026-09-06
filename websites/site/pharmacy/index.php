<?php
require __DIR__ . '/../lib/shopkit.php';
pr_start();

// THE BUG (auth bypass): the portal login builds the query by concatenation.
//   username:  ' OR role='staff' LIMIT 1 -- -   password: anything
// lands you on a staff account, which unlocks the patient records page.
$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = $_POST['username'] ?? '';
    $p = $_POST['password'] ?? '';
    $sql = "SELECT * FROM users WHERE username = '$u' AND password_hash = '" . md5($p) . "' LIMIT 1";
    $row = pr_query($sql)->fetch();
    if ($row) {
        pr_login_user($row);
        header('Location: .');
        exit;
    }
    $error = 'Wrong username or password.';
}
if (!pr_current_user()) {
    pr_render_portal($error, 'Sign in to refill prescriptions. Staff use the same form.');
    return;
}

$u = pr_current_user();
pr_head('Riverside Pharmacy');
echo '<h1>Riverside Pharmacy</h1><p class="lede">prescriptions &amp; sundries</p>';
if (($u['role'] ?? '') === 'staff' || ($u['role'] ?? '') === 'admin') {
    echo '<p><a href="records.php">Patient records</a> (staff)</p>';
} else {
    echo '<p>Your refills are up to date.</p>';
}
pr_foot();
