<?php
// The "manager bot". The container hits this on a loop with the manager token.
// It stands in for a human opening the review screen in a browser: for each
// un-reviewed booking, if the note contains a script or event handler, the
// script "runs" in the manager's session and the manager's flag is written
// back onto that booking. No real browser (regex only).
require __DIR__ . '/../lib/db.php';

if (($_GET['token'] ?? '') !== (getenv('BARBER_MGR_TOKEN') ?: 'nope')) {
    http_response_code(403);
    exit("no\n");
}

$flag = pr_flag();
$db = pr_db();
$pending = $db->query('SELECT id, note FROM bookings WHERE bot_note IS NULL')->fetchAll();
$fired = 0;
foreach ($pending as $b) {
    $xss = preg_match('/<script\b|on\w+\s*=|<img\b[^>]*\bon|javascript:/i', (string) $b['note']);
    $note = $xss ? $flag : 'reviewed - looks fine';
    $st = $db->prepare('UPDATE bookings SET bot_note = ? WHERE id = ?');
    $st->execute([$note, $b['id']]);
    $fired += $xss ? 1 : 0;
}
header('Content-Type: text/plain');
echo "reviewed " . count($pending) . " booking(s), $fired triggered\n";
