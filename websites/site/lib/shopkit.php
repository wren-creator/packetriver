<?php
// Storefront helpers so each shop's index.php stays tiny.
require_once __DIR__ . '/portal.php';

/** The generic "portal, then catalogue" flow used by the plain storefronts. */
function pr_storefront(): void
{
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
        pr_render_portal($error);
        return;
    }
    $rows = pr_query('SELECT id, name, price, stock FROM products ORDER BY name')->fetchAll();
    $m = pr_meta();
    pr_head('Catalogue');
    echo '<h1>' . htmlspecialchars($m['name']) . '</h1>';
    echo '<p class="lede">' . htmlspecialchars($m['tag']) . '</p>';
    echo '<table class="list"><thead><tr><th>Item</th><th>Price</th><th>Stock</th></tr></thead><tbody>';
    foreach ($rows as $r) {
        printf(
            '<tr><td>%s</td><td>$%s</td><td>%d</td></tr>',
            htmlspecialchars($r['name']),
            number_format((float) $r['price'], 2),
            (int) $r['stock']
        );
    }
    echo '</tbody></table>';
    pr_foot();
}

/** The vulnerable concatenated-LIKE search (General Store, and any shop that
 *  wants a search box). Three selected columns for a clean UNION. */
function pr_vuln_search(): void
{
    pr_require_login();
    $q = $_GET['q'] ?? '';
    $results = [];
    if ($q !== '') {
        $sql = "SELECT id, name, price FROM products WHERE name LIKE '%$q%' ORDER BY name";
        $results = pr_query($sql)->fetchAll();
    }
    pr_head('Search');
    echo '<h1>Search results</h1>';
    if ($q !== '') {
        echo '<p class="lede">You searched for: ' . $q . '</p>';   // reflected, unencoded
    }
    if ($q === '') {
        echo '<p>Type something in the search box.</p>';
    } elseif (!$results) {
        echo '<p>Nothing matched &ldquo;' . $q . '&rdquo;.</p>';
    } else {
        echo '<table class="list"><thead><tr><th>Item</th><th>Price</th></tr></thead><tbody>';
        foreach ($results as $r) {
            printf(
                '<tr><td>%s</td><td>$%s</td></tr>',
                htmlspecialchars((string) $r['name']),
                htmlspecialchars((string) $r['price'])
            );
        }
        echo '</tbody></table>';
    }
    pr_foot();
}
