<?php
require __DIR__ . '/../lib/portal.php';
pr_require_login();

// THE BUG (SSRF): whatever URL you pass is fetched server-side and echoed
// back, with no scheme or host restriction. The supplier host does not exist,
// but there is an internal-only inventory endpoint on this very server:
//   fetch.php?url=http://127.0.0.1/baittackle/_internal/inv.php
$url = $_GET['url'] ?? '';
header('Content-Type: text/plain');
if ($url === '') {
    echo "usage: fetch.php?url=...";
    exit;
}
$ctx = stream_context_create(['http' => ['timeout' => 4]]);
$body = @file_get_contents($url, false, $ctx);
echo $body === false ? "fetch failed: $url" : $body;
