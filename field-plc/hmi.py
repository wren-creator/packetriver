"""Operator HMIs for the Packet River field plants.

Four plants, four separate front doors: each has its own login page and its own
operational display style (they were bought from different vendors in different
decades - that is why they look nothing alike). `/` is a plain index that
links to each; the map opens the relevant plant per building.

This is the recognisable front door. The scored bug is the unauthenticated
Modbus write that bypasses it entirely.
"""
import os

from flask import Flask, redirect, request, session

from maps import FACTORY, POWER, SEWAGE, WATER
from store import FCTX, FLOCK, PCTX, PLOCK, SGCTX, SGLOCK, WCTX, WLOCK, rd

app = Flask(__name__)
app.secret_key = os.environ.get("HMI_SECRET", "field-plc-dev")
USER = os.environ.get("HMI_USER", "operator")
PASS = os.environ.get("HMI_PASS", "operator")

# -- per-plant look & feel ---------------------------------------------
# vendor, palette, typeface, header voice - all deliberately different.
THEMES = {
    "water": dict(
        title="Packet River Water Company",
        sys="AQUAVIEW 4 &mdash; Treatment &amp; Distribution SCADA",
        font="'Segoe UI',system-ui,sans-serif",
        bg="#eef6fb", panel="#ffffff", ink="#173b52", muted="#5b7f96",
        accent="#0e77b7", line="#cfe6f2", radius="14px", banner_bg="#0e77b7",
        vendor="Aquaview Systems Inc.",
    ),
    "power": dict(
        title="Municipal Power - Substation 1",
        sys="GRIDMASTER RTU // BUS CONTROL // DANGER - HIGH VOLTAGE",
        font="'Arial Narrow',Arial,sans-serif",
        bg="#1c1c1e", panel="#26262a", ink="#f2f2f2", muted="#9a9a9e",
        accent="#f4c020", line="#3a3a40", radius="2px", banner_bg="#8a1f14",
        vendor="GridMaster Controls",
    ),
    "factory": dict(
        title="WIDGET FACTORY - LINE & LOADING",
        sys="PLANTLINK HMI  r3.1  [ ASSEMBLY / GANTRY / HOPPER ]",
        font="'DejaVu Sans Mono','Courier New',monospace",
        bg="#2b2b28", panel="#343430", ink="#e8e4d8", muted="#a49a80",
        accent="#e07b2c", line="#4a463c", radius="0px", banner_bg="#4a463c",
        vendor="PlantLink OT",
    ),
    "sewage": dict(
        title="Packet River Water Reclamation",
        sys="CLARUS &mdash; Effluent & Return Control",
        font="Georgia,'Times New Roman',serif",
        bg="#eef1e8", panel="#fbfcf7", ink="#28321f", muted="#5f6b4c",
        accent="#5c7d3a", line="#dbe2cd", radius="10px", banner_bg="#3f5626",
        vendor="Clarus Environmental",
    ),
}
TITLES = {"water": "Water Treatment", "power": "Power Substation",
          "factory": "Widget Factory", "sewage": "Sewage Treatment"}


def page(plant, heading, body):
    t = THEMES[plant]
    return f"""<!doctype html><meta charset=utf-8><title>{t['title']} - {heading}</title>
<style>
 body{{margin:0;background:{t['bg']};color:{t['ink']};font:15px/1.5 {t['font']}}}
 .bar{{background:{t['banner_bg']};color:#fff;padding:12px 20px;font-weight:800;letter-spacing:.06em}}
 .sub{{background:{t['panel']};border-bottom:2px solid {t['line']};padding:6px 20px;color:{t['muted']};font-size:12px}}
 main{{max-width:700px;margin:22px auto;padding:0 20px}}
 nav{{margin-bottom:14px}} nav a{{color:{t['accent']};margin-right:14px;text-decoration:none;font-size:13px}}
 .card{{background:{t['panel']};border:1px solid {t['line']};border-radius:{t['radius']};padding:16px;margin-bottom:14px}}
 h2{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:{t['muted']};margin:0 0 12px}}
 table{{width:100%;border-collapse:collapse}} td{{padding:5px 8px;border-bottom:1px solid {t['line']}}}
 td.k{{color:{t['muted']};width:55%}} .alarm{{color:#d9584f;font-weight:700}}
 form.portal{{max-width:340px;margin:46px auto}}
 label{{display:block;font-size:12px;color:{t['muted']};margin-top:10px}}
 input{{display:block;width:100%;margin:4px 0;padding:8px 10px;border:1px solid {t['line']};border-radius:{t['radius']};font:inherit;background:{t['bg']};color:{t['ink']}}}
 button{{margin-top:14px;padding:8px 18px;border:0;border-radius:{t['radius']};background:{t['accent']};color:#fff;font:inherit;font-weight:700;cursor:pointer}}
 .err{{color:#d9584f;font-size:13px}} .foot{{color:{t['muted']};font-size:11px;margin-top:24px}}
</style>
<div class=bar>{t['title']}</div><div class=sub>{t['sys']}</div>
<main>{body}<p class=foot>{t['vendor']} &nbsp;&bull;&nbsp; operator terminal</p></main>"""


def login_form(plant, err=""):
    t = THEMES[plant]
    return page(plant, "Sign in", f"""
      <form class=portal method=post action="/{plant}/login">
        <h2>Operator sign-in</h2>
        {'<p class=err>' + err + '</p>' if err else ''}
        <label>Operator ID</label><input name=user autofocus autocomplete=off>
        <label>Password</label><input name=password type=password>
        <button type=submit>Sign in to {t['title']}</button>
      </form>""")


def _onoff(v):
    return "RUNNING" if v else "<span class=alarm>STOPPED</span>"


def _brk(v):
    return "CLOSED" if v else "<span class=alarm>OPEN</span>"


def _tbl(rows):
    return "<table>" + "".join(
        f"<tr><td class=k>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</table>"


def _card(title, rows, alarms):
    a = f"<p class=alarm>&#9888; {' &nbsp; '.join(alarms)}</p>" if alarms else ""
    return f"<div class=card><h2>{title}</h2>{_tbl(rows)}{a}</div>"


# -- per-plant operational displays -----------------------------------
def water_card():
    co = rd(WCTX, WLOCK, 1, 0, 12)
    hr = rd(WCTX, WLOCK, 3, 0, 20)
    di = rd(WCTX, WLOCK, 2, 0, 4)
    rows = [
        ("Intake pump", _onoff(co[WATER["coil"]["INTAKE"]])),
        ("High-lift pump", _onoff(co[WATER["coil"]["HIGHLIFT"]])),
        ("Chlorine dosing", _onoff(co[WATER["coil"]["CHLORINE"]])),
        ("Main isolation valve", "OPEN" if co[WATER["coil"]["MAIN_VALVE"]]
         else "<span class=alarm>CLOSED</span>"),
        ("High-lift setpoint", f"{hr[WATER['hr']['HIGHLIFT_SP']] / 10:.1f} psi"),
        ("Tower level", f"{hr[WATER['hr']['TANK_LEVEL']] / 10:.1f} %"),
        ("Distribution pressure", f"{hr[WATER['hr']['MAIN_PRESSURE']] / 10:.1f} psi"),
        ("Chlorine residual", f"{hr[WATER['hr']['CHLORINE_RESIDUAL']] / 100:.2f} ppm"),
        ("Flow", f"{hr[WATER['hr']['FLOW']]} gpm"),
    ]
    alarms = [n for n, x in (
        ("LOW DISTRIBUTION PRESSURE", di[WATER["di"]["LOW_PRESSURE"]]),
        ("LOW TOWER LEVEL", di[WATER["di"]["LOW_TANK"]]),
        ("LOW CHLORINE RESIDUAL", di[WATER["di"]["LOW_CHLORINE"]]),
    ) if x]
    return _card("Treatment &amp; Distribution", rows, alarms)


def power_card():
    co = rd(PCTX, PLOCK, 1, 0, 12)
    hr = rd(PCTX, PLOCK, 3, 0, 20)
    rows = [
        ("Main incomer breaker", _brk(co[POWER["coil"]["BRK_MAIN"]])),
        ("Residential feeder", _brk(co[POWER["coil"]["BRK_RES"]])),
        ("Business feeder (Main St)", _brk(co[POWER["coil"]["BRK_BIZ"]])),
        ("Plants feeder (factory / water / sewage)", _brk(co[POWER["coil"]["BRK_IND"]])),
        ("Streetlights feeder", _brk(co[POWER["coil"]["BRK_ST"]])),
        ("Local generation", _onoff(co[POWER["coil"]["GEN_ENABLE"]])),
        ("Bus frequency", f"{hr[POWER['hr']['BUS_FREQ']] / 100:.2f} Hz"),
        ("Bus voltage", f"{hr[POWER['hr']['BUS_VOLT']] / 10:.1f} kV"),
        ("Total load", f"{hr[POWER['hr']['LOAD']] / 10:.1f} MW"),
    ]
    return _card("Bus &amp; Feeder Status", rows, [])


def factory_card():
    co = rd(FCTX, FLOCK, 1, 0, 10)
    hr = rd(FCTX, FLOCK, 3, 0, 12)
    di = rd(FCTX, FLOCK, 2, 0, 4)
    rows = [
        ("Assembly line", _onoff(co[FACTORY["coil"]["LINE_RUN"]])),
        ("E-stop interlock", "<span class=alarm>BYPASSED</span>"
         if co[FACTORY["coil"]["ESTOP_BYPASS"]] else "armed"),
        ("Line speed", f"{hr[FACTORY['hr']['LINE_SPEED']]} %"),
        ("Loading gantry", _onoff(co[FACTORY["coil"]["GANTRY"]])),
        ("Hopper gate", "<span class=alarm>OPEN</span>"
         if co[FACTORY["coil"]["HOPPER_GATE"]] else "closed"),
        ("Rail car in position", "yes" if di[FACTORY["di"]["CAR_IN_POSITION"]] else "no"),
    ]
    alarms = ["LINE JAM / UNSAFE STATE"] if di[FACTORY["di"]["LINE_JAM"]] else []
    return _card("Line &amp; Loading", rows, alarms)


def sewage_card():
    co = rd(SGCTX, SGLOCK, 1, 0, 10)
    hr = rd(SGCTX, SGLOCK, 3, 0, 16)
    di = rd(SGCTX, SGLOCK, 2, 0, 4)
    rows = [
        ("Aeration basin", _onoff(co[SEWAGE["coil"]["AERATION"]])),
        ("Disinfection dosing", _onoff(co[SEWAGE["coil"]["CHEM_DOSE"]])),
        ("Treated-return pump", _onoff(co[SEWAGE["coil"]["RETURN_PUMP"]])),
        ("Storm bypass gate", "<span class=alarm>OPEN</span>"
         if co[SEWAGE["coil"]["BYPASS_GATE"]] else "closed"),
        ("Dose setpoint", f"{hr[SEWAGE['hr']['DOSE_SP']] / 100:.2f} mg/L"),
        ("Dissolved oxygen", f"{hr[SEWAGE['hr']['DO_LEVEL']] / 10:.1f} mg/L"),
        ("Effluent turbidity", f"{hr[SEWAGE['hr']['TURBIDITY']] / 10:.1f} NTU"),
        ("Effluent quality", f"{hr[SEWAGE['hr']['EFFLUENT_QUALITY']] / 10:.1f} %"),
    ]
    alarms = [n for n, x in (
        ("HIGH EFFLUENT TURBIDITY", di[SEWAGE["di"]["HIGH_TURBIDITY"]]),
        ("STORM BYPASS OPEN - DISCHARGING UNTREATED", di[SEWAGE["di"]["BYPASS_OPEN"]]),
    ) if x]
    return _card("Effluent &amp; Return", rows, alarms)


CARDS = {"water": water_card, "power": power_card,
         "factory": factory_card, "sewage": sewage_card}


@app.get("/")
def index():
    links = "".join(f'<li><a href="/{p}">{TITLES[p]}</a></li>' for p in CARDS)
    return (f"<!doctype html><meta charset=utf-8><title>Packet River Field Operations</title>"
            f"<style>body{{font:15px/1.7 system-ui;background:#f3ecdd;color:#3b3226;margin:0}}"
            f".bar{{background:#fffdf7;border-bottom:2px solid #e4d8bf;padding:12px 20px;font-weight:800}}"
            f"main{{max-width:520px;margin:24px auto;padding:0 20px}}a{{color:#2f8fbf}}</style>"
            f"<div class=bar>PACKET RIVER FIELD OPERATIONS</div><main>"
            f"<p>Operator terminals:</p><ul>{links}</ul></main>")


@app.get("/<plant>")
def plant_page(plant):
    if plant not in CARDS:
        return redirect("/")
    if not session.get(f"op_{plant}"):
        return login_form(plant)
    nav = "".join(f'<a href="/{p}">{TITLES[p]}</a>' for p in CARDS)
    body = f'<nav>{nav}<a href="/{plant}/logout">Log out</a></nav>' + CARDS[plant]()
    return page(plant, TITLES[plant], body)


@app.post("/<plant>/login")
def plant_login(plant):
    if plant not in CARDS:
        return redirect("/")
    if request.form.get("user") == USER and request.form.get("password") == PASS:
        session[f"op_{plant}"] = request.form["user"]
        return redirect(f"/{plant}")
    return login_form(plant, "Wrong operator ID or password."), 401


@app.get("/<plant>/logout")
def plant_logout(plant):
    session.pop(f"op_{plant}", None)
    return redirect(f"/{plant}" if plant in CARDS else "/")


@app.get("/health")
def health():
    return "ok"
