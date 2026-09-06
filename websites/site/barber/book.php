<?php
require __DIR__ . '/../lib/portal.php';
pr_require_login();

// THE BUG (stored XSS): the appointment note is stored raw and later rendered
// raw when the shop manager reviews pending bookings. A regex "manager bot"
// (review.php, hit on a loop by the container) stands in for the browser: if
// your note contains a script/handler, the bot treats it as executed in the
// manager's session and writes the manager's flag back onto your booking.
//   note:  <script>steal()</script>   ->  then read booking.php?id=<yours>
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = $_POST['name'] ?? '';
    $note = $_POST['note'] ?? '';
    $st = pr_prepare('INSERT INTO bookings (name, note, created) VALUES (?, ?, NOW())');
    $st->execute([$name, $note]);   // params, but `note` is rendered raw later
    header('Location: booking.php?id=' . pr_db()->lastInsertId());
    exit;
}

pr_head('Request an appointment');
?>
<section class="portal">
  <h1>Appointment request</h1>
  <form method="post" action="book.php">
    <label>Your name <input type="text" name="name" required></label>
    <label>Anything we should know?
      <input type="text" name="note" placeholder="e.g. same as last time"></label>
    <button type="submit">Send request</button>
  </form>
</section>
<?php
pr_foot();
