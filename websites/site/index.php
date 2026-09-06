<?php
// Main Street directory.
$shops = [
  'generalstore' => 'General Store', 'hardware' => 'Hardware & Supply',
  'pharmacy' => 'Riverside Pharmacy', 'diner' => 'The Daily Grind',
  'barber' => 'Two Chairs Barbershop', 'tavern' => 'The Watering Hole',
  'drycleaner' => 'Packet River Cleaners', 'baittackle' => 'Bait & Tackle',
  'townhall' => 'Town Hall', 'police' => 'Police Dept', 'fire' => 'Fire Dept',
];
?><!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Main Street &middot; Packet River</title><link rel=stylesheet href="/style.css"></head>
<body><header class="shop-top"><span class="brand">PACKET RIVER &mdash; MAIN STREET</span></header>
<main><h1>Main Street</h1><p class=lede>Pick a storefront.</p>
<table class="list"><tbody>
<?php foreach ($shops as $k => $name):
  $dir = __DIR__ . '/' . $k;
  if (!is_file("$dir/index.php")) continue; ?>
  <tr><td><a href="<?= htmlspecialchars($k) ?>/"><?= htmlspecialchars($name) ?></a></td></tr>
<?php endforeach; ?>
</tbody></table></main>
<footer class="shop-foot">a training range, do not deploy on a routable network</footer>
</body></html>
