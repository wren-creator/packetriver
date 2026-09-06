<?php
require __DIR__ . '/../lib/portal.php';
pr_require_login();
$u = pr_current_user();
if (($u['role'] ?? '') !== 'staff' && ($u['role'] ?? '') !== 'admin') {
    http_response_code(403);
    pr_head('Records');
    echo '<p>Staff only.</p>';
    pr_foot();
    exit;
}

// once you're past the auth bypass, the records (incl. the flag row) are here
$rows = pr_query('SELECT * FROM patient_records ORDER BY id')->fetchAll();
pr_head('Patient records');
echo '<h1>Patient records</h1>';
echo '<table class="list"><thead><tr><th>Patient</th><th>Rx</th><th>Note</th></tr></thead><tbody>';
foreach ($rows as $r) {
    printf('<tr><td>%s</td><td>%s</td><td>%s</td></tr>',
        htmlspecialchars($r['patient']), htmlspecialchars($r['rx']), htmlspecialchars($r['note']));
}
echo '</tbody></table>';
pr_foot();
