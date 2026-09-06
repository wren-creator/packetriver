"""Shared operator HMI for the water and power plants.

A login portal (default creds operator / operator) then a read-only status
screen pulled live off the two Modbus datastores. This is the recognisable
front door; the scored bug is the unauthenticated Modbus write that bypasses
it entirely.
"""
import os

from flask import Flask, redirect, request, session

from maps import POWER, WATER
from store import PCTX, PLOCK, WCTX, WLOCK, rd

app = Flask(__name__)
app.secret_key = os.environ.get("HMI_SECRET", "field-plc-dev")
USER = os.environ.get("HMI_USER", "operator")
PASS = os.environ.get("HMI_PASS", "operator")

PAGE = """<!doctype html><meta charset=utf-8><title>{title}</title>
<style>
body{{margin:0;background:#f3ecdd;color:#3b3226;font:15px/1.5 ui-rounded,system-ui,sans-serif}}
.bar{{background:#fffdf7;border-bottom:2px solid #e4d8bf;padding:12px 20px;font-weight:800;letter-spacing:.08em}}
main{{max-width:720px;margin:24px auto;padding:0 20px}}
.card{{background:#fffdf7;border:1px solid #e4d8bf;border-radius:12px;padding:16px;margin-bottom:14px}}
h2{{font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:#8c7d64;margin:0 0 10px}}
table{{width:100%;border-collapse:collapse}} td{{padding:4px 8px;border-bottom:1px solid #efe6d0}}
td.k{{color:#8c7d64}} .alarm{{color:#d9584f;font-weight:700}}
form.portal{{max-width:340px;margin:50px auto}} input{{display:block;width:100%;margin:6px 0;padding:7px 10px;border:1px solid #e4d8bf;border-radius:8px;font:inherit}}
button{{padding:7px 16px;border:0;border-radius:8px;background:#2f8fbf;color:#fff;font:inherit;font-weight:600;cursor:pointer}}
.err{{color:#d9584f}}
</style>
<div class=bar>PACKET RIVER FIELD OPERATIONS &mdash; {title}</div><main>{body}</main>"""


def _login_form(err=""):
    body = f"""<form class=portal method=post action=/login>
      <h2>Operator login</h2>
      {'<p class=err>' + err + '</p>' if err else ''}
      <input name=user placeholder=username autofocus>
      <input name=password type=password placeholder=password>
      <button type=submit>Sign in</button>
    </form>"""
    return PAGE.format(title="Login", body=body)


@app.get("/")
def index():
    if not session.get("op"):
        return _login_form()

    wco = rd(WCTX, WLOCK, 1, 0, 12)
    whr = rd(WCTX, WLOCK, 3, 0, 20)
    wdi = rd(WCTX, WLOCK, 2, 0, 4)
    pco = rd(PCTX, PLOCK, 1, 0, 12)
    phr = rd(PCTX, PLOCK, 3, 0, 20)

    def onoff(v):
        return "RUNNING" if v else "<span class=alarm>STOPPED</span>"

    def brk(v):
        return "CLOSED" if v else "<span class=alarm>OPEN</span>"

    water_rows = [
        ("Intake pump", onoff(wco[WATER["coil"]["INTAKE"]])),
        ("High-lift pump", onoff(wco[WATER["coil"]["HIGHLIFT"]])),
        ("Chlorine dosing", onoff(wco[WATER["coil"]["CHLORINE"]])),
        ("Main isolation valve", "OPEN" if wco[WATER["coil"]["MAIN_VALVE"]] else "<span class=alarm>CLOSED</span>"),
        ("High-lift setpoint", f"{whr[WATER['hr']['HIGHLIFT_SP']] / 10:.1f} psi"),
        ("Tower level", f"{whr[WATER['hr']['TANK_LEVEL']] / 10:.1f} %"),
        ("Distribution pressure", f"{whr[WATER['hr']['MAIN_PRESSURE']] / 10:.1f} psi"),
        ("Chlorine residual", f"{whr[WATER['hr']['CHLORINE_RESIDUAL']] / 100:.2f} ppm"),
        ("Flow", f"{whr[WATER['hr']['FLOW']]} gpm"),
    ]
    water_alarms = [n for n, a in (
        ("LOW DISTRIBUTION PRESSURE", wdi[WATER["di"]["LOW_PRESSURE"]]),
        ("LOW TOWER LEVEL", wdi[WATER["di"]["LOW_TANK"]]),
        ("LOW CHLORINE RESIDUAL", wdi[WATER["di"]["LOW_CHLORINE"]]),
    ) if a]

    power_rows = [
        ("Main incomer breaker", brk(pco[POWER["coil"]["BRK_MAIN"]])),
        ("Residential feeder", brk(pco[POWER["coil"]["BRK_RES"]])),
        ("Downtown feeder", brk(pco[POWER["coil"]["BRK_DT"]])),
        ("Industrial feeder", brk(pco[POWER["coil"]["BRK_IND"]])),
        ("Streetlights feeder", brk(pco[POWER["coil"]["BRK_ST"]])),
        ("Local generation", onoff(pco[POWER["coil"]["GEN_ENABLE"]])),
        ("Bus frequency", f"{phr[POWER['hr']['BUS_FREQ']] / 100:.2f} Hz"),
        ("Bus voltage", f"{phr[POWER['hr']['BUS_VOLT']] / 10:.1f} kV"),
        ("Total load", f"{phr[POWER['hr']['LOAD']] / 10:.1f} MW"),
    ]

    def tbl(rows):
        return "<table>" + "".join(
            f"<tr><td class=k>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</table>"

    body = (
        f"<div class=card><h2>Water Treatment &amp; Distribution</h2>{tbl(water_rows)}"
        + (f"<p class=alarm>&#9888; {' &nbsp; '.join(water_alarms)}</p>" if water_alarms else "")
        + "</div>"
        f"<div class=card><h2>Power Substation</h2>{tbl(power_rows)}</div>"
        "<p><a href=/logout>Log out</a></p>"
    )
    return PAGE.format(title="Plant Overview", body=body)


@app.post("/login")
def login():
    if request.form.get("user") == USER and request.form.get("password") == PASS:
        session["op"] = request.form["user"]
        return redirect("/")
    return _login_form("Wrong username or password."), 401


@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.get("/health")
def health():
    return "ok"
