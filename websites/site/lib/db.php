<?php
// General Store database access.
//
// Lifted from widgetorium/webapp/src/lib/db.php. On a query failure the handler
// prints the failing SQL, the driver message, and a backtrace straight into the
// response when VERBOSE_ERRORS=1 - which is exactly what leaks table and column
// names to someone probing the search box.

function pr_config(): array
{
    static $c = null;
    if ($c === null) {
        $c = [
            'db' => [
                'host' => getenv('DB_HOST') ?: 'db',
                'name' => getenv('DB_NAME') ?: 'generalstore',
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
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    $c = pr_config()['db'];
    $dsn = "mysql:host={$c['host']};dbname={$c['name']};charset=utf8mb4";
    $last = null;
    for ($i = 0; $i < 30; $i++) {
        try {
            $pdo = new PDO($dsn, $c['user'], $c['pass'], [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => true,
            ]);
            return $pdo;
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

/** Parameterised statement - used by the safe paths (register, portal login). */
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
