<?php
require __DIR__ . '/../lib/portal.php';
pr_require_login();
$id = (int) ($_GET['id'] ?? 0);
$b = pr_query("SELECT * FROM bookings WHERE id = $id")->fetch();
pr_head('Booking');
if (!$b) {
    echo '<p>No such booking.</p>';
} else {
    echo '<h1>Booking #' . (int) $b['id'] . '</h1>';
    echo '<table class="list"><tbody>';
    echo '<tr><td>Name</td><td>' . htmlspecialchars($b['name']) . '</td></tr>';
    // rendered raw, same as the manager's review screen
    echo '<tr><td>Note</td><td>' . $b['note'] . '</td></tr>';
    echo '<tr><td>Manager</td><td>' . htmlspecialchars((string) $b['bot_note']) . '</td></tr>';
    echo '</tbody></table>';
}
pr_foot();
