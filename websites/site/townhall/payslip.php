<?php
require __DIR__ . '/../lib/portal.php';
pr_start();
if (empty($_SESSION['payroll'])) {
    header('Location: payroll.php');
    exit;
}

// THE BUG (LFI): `doc` is concatenated onto the payslips path with no
// sanitisation. Traverse out to any file www-data can read:
//   payslip.php?doc=../../../../etc/passwd
//   payslip.php?doc=../../../../run/secret/townhall_lfi/flag.txt   <- the flag
$doc = $_GET['doc'] ?? '';
$path = __DIR__ . '/payslips/' . $doc;
header('Content-Type: text/plain');
if (is_file($path)) {
    readfile($path);
} else {
    echo "no such payslip: $doc";
}
