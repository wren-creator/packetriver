<?php
require __DIR__ . '/../lib/portal.php';
pr_require_login();

// Card checkout. Posts server-side to the town payment gateway
// (http://paygw:8500/charge). The gateway's GET /receipt/<txn_id> has no auth
// or ownership check - walk the ids from 5001.
$result = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $ch = curl_init('http://paygw:8500/charge');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 5,
        CURLOPT_POSTFIELDS => http_build_query([
            'pan' => $_POST['pan'] ?? '', 'exp' => $_POST['exp'] ?? '',
            'cvv' => $_POST['cvv'] ?? '', 'amount' => $_POST['amount'] ?? '0',
            'merchant' => 'General Store',
        ]),
    ]);
    $result = curl_exec($ch);
    curl_close($ch);
}

pr_head('Checkout');
?>
<h1>Checkout</h1>
<p class="lede">Card payments run through the town gateway. Test cards only.</p>
<form method="post" action="checkout.php" class="portal">
  <label>Card number <input name="pan" value="4111111111111111"></label>
  <label>Expiry <input name="exp" value="03/28"></label>
  <label>CVV <input name="cvv" value="123"></label>
  <label>Amount <input name="amount" value="21.39"></label>
  <button type="submit">Pay</button>
</form>
<?php if ($result !== null): ?>
  <h2>Gateway response</h2>
  <pre><?= htmlspecialchars($result) ?></pre>
  <p>Receipts: <code>GET http://paygw:8500/receipt/&lt;txn_id&gt;</code></p>
<?php endif; ?>
<?php
pr_foot();
