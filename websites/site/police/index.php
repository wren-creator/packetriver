<?php
require __DIR__ . '/../lib/portal.php';
// Static-ish public page. The bug is not in the app: the dispatch team left
// their config where the web server serves it.
//   /police/dispatch/config.json
pr_head('Daily blotter');
?>
<h1>Packet River PD &mdash; Daily Blotter</h1>
<p class="lede">Non-emergency dispatch. For emergencies dial 911.</p>
<table class="list"><tbody>
  <tr><td>06:12</td><td>Noise complaint, Packet River Rd. Advised.</td></tr>
  <tr><td>09:40</td><td>Lost dog returned to owner, Main St.</td></tr>
  <tr><td>14:05</td><td>Fender-bender at the X2 light. No injuries.</td></tr>
  <tr><td>19:30</td><td>Welfare check, requested by family. All well.</td></tr>
</tbody></table>
<?php
pr_foot();
