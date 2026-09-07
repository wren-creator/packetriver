# Easter-egg hints — instructor registry

Help hidden as in-world artifacts. Toggled by `PKT_EGGS` in `.env`:

- `off` (default) — no eggs anywhere.
- `subtle` — terse, cryptic fragments. You have to already half-know the bug.
- `obvious` — clearer fragments: the bug class and the tool, plainly. Still
  never a working command, a credential, a parameter value, or a flag
  location. That tier is `instructor/answer-key.md`.

Eggs are **free** — they cost only the looking. The opt-in scored hint is a
separate thing (`scoring` / the map HUD).

Each egg's text lives inline in the service that renders it (an entrypoint, an
app route) because it has to fit that surface. This file is the index.

| id | where to find it | points at |
|---|---|---|
| `robots` | `GET /robots.txt` on the shops host (`:8090`) | one `Disallow:` line per shop, each nudging at that shop's bug class |
| `drycleaner_readme` | `GET /drycleaner/README.old` | the deployed tree still has its version control; read the history |
| `hmi_login_comment` | HTML comment in the field-plc HMI login page source (`:8093`) | the operator logins rotate; last shift left the current set on the historian (`/ops/handover.txt`) |
| `hmi_eng_notes` | `GET /eng/notes.txt` on the field-plc HMI | the field bus takes writes from anyone; the flag block opens in maintenance mode |
| `dns_hint` | a `_hint` TXT record in `packetriver.range` (only in the AXFR, or `dig _hint.packetriver.range TXT`) | try transferring the whole zone |
| `town_gossip` | `GET /hints` on the map server (`:8080`) | rotating townsfolk chatter: the open Wi-Fi at the Diner, the house on the edge of town whose router "never got changed", the traffic box that "listens to anyone" |

## Adding an egg

1. Add a row here.
2. Render it in the owning service, gated on `os.environ["PKT_EGGS"]` /
   `$PKT_EGGS` being `subtle` or `obvious`, with both tiers written.
3. Keep it a fragment. If it reads like a walkthrough step, it belongs in the
   answer key instead.
