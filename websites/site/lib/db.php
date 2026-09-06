<?php
// Shared database access for the Main Street sites.
//
// Each shop lives in its own directory (/hardware/, /pharmacy/, ...) and gets
// its own MariaDB schema of the same name. On a query failure the handler
// prints the failing SQL, the driver message, and a backtrace when
// VERBOSE_ERRORS=1 - which is what leaks table and column names.

function pr_shop(): string
{
    // the shop key is the directory the running script lives in
    return basename(dirname($_SERVER['SCRIPT_FILENAME']));
}

function pr_config(): array
{
    static $c = null;
    if ($c === null) {
        $c = [
            'db' => [
                'host' => getenv('DB_HOST') ?: 'db',
                'name' => pr_shop(),
                'user' => getenv('DB_USER') ?: 'shop',
                'pass' => getenv('DB_PASS') ?: 'shop',
            ],
            'verbose_errors' => (getenv('VERBOSE_ERRORS') ?: '1') === '1',
        ];
    }
    return $c;
}

function pr_db(): PDO
{
    static $pool = [];
    $name = pr_config()['db']['name'];
    if (isset($pool[$name])) {
        return $pool[$name];
    }
    $c = pr_config()['db'];
    $dsn = "mysql:host={$c['host']};dbname={$c['name']};charset=utf8mb4";
    $last = null;
    for ($i = 0; $i < 30; $i++) {
        try {
            $pool[$name] = new PDO($dsn, $c['user'], $c['pass'], [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => true,
            ]);
            return $pool[$name];
        } catch (PDOException $e) {
            $last = $e;
            sleep(1);
        }
    }
    http_response_code(500);
    echo "database unavailable: " . htmlspecialchars($last ? $last->getMessage() : 'unknown');
    exit;
}

/** Run a raw SQL string. Intentionally does no escaping. */
function pr_query(string $sql): PDOStatement
{
    try {
        return pr_db()->query($sql);
    } catch (PDOException $e) {
        pr_sql_error($sql, $e);
    }
}

/** Parameterised statement - the safe path (register, some portals). */
function pr_prepare(string $sql): PDOStatement
{
    return pr_db()->prepare($sql);
}

function pr_sql_error(string $sql, PDOException $e): void
{
    http_response_code(500);
    if (pr_config()['verbose_errors']) {
        echo "<pre style=\"background:#fdecea;border:1px solid #d9584f;padding:12px;white-space:pre-wrap;color:#5a1a15\">";
        echo "SQL ERROR\n";
        echo "  query : " . htmlspecialchars($sql) . "\n";
        echo "  driver: " . htmlspecialchars($e->getMessage()) . "\n\n";
        echo htmlspecialchars((new Exception())->getTraceAsString());
        echo "</pre>";
    } else {
        echo "<p>Sorry, something went wrong.</p>";
    }
    exit;
}

const SHOP_TECHNIQUE = [
    'generalstore' => 'generalstore_sqli', 'hardware' => 'hardware_idor',
    'pharmacy' => 'pharmacy_authbypass', 'diner' => 'diner_backup',
    'barber' => 'barber_xss', 'tavern' => 'tavern_defaultcreds',
    'drycleaner' => 'drycleaner_gitleak', 'baittackle' => 'baittackle_ssrf',
];

/** Read this session's flag for a technique (defaults to the current shop's
 *  primary technique). scoring/flags.py writes /run/secret/<technique_id>/flag.txt */
function pr_flag(?string $technique = null): string
{
    $technique = $technique ?? (SHOP_TECHNIQUE[pr_shop()] ?? pr_shop());
    $f = '/run/secret/' . $technique . '/flag.txt';
    return is_readable($f) ? trim((string) file_get_contents($f)) : 'flag-not-planted';
}
