<?php
// Internal inventory service. "Only reachable from localhost" - which is
// exactly what makes it an SSRF payoff: reach it through fetch.php.
$ip = $_SERVER['REMOTE_ADDR'] ?? '';
if (!in_array($ip, ['127.0.0.1', '::1'], true)) {
    http_response_code(403);
    exit("internal service - localhost only\n");
}
require __DIR__ . '/../../lib/db.php';
header('Content-Type: text/plain');
echo "PACKET RIVER BAIT & TACKLE - internal inventory API\n";
echo "warehouse token: " . pr_flag('baittackle_ssrf') . "\n";
