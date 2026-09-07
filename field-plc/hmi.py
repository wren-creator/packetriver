"""Operator HMIs for the Packet River field plants.

Four plants, four separate front doors - each with its own login page and its
own mimic-diagram operational display (pumps, tanks, breakers, valves, AUTO/HAND
faceplates, setpoints), in the style of a vendor SCADA panel. `/` is a plain
index; the map opens the relevant plant per building.

The HMI reads and writes the same Modbus datastores the field bus exposes. It
is the recognisable front door; the scored bug is the *unauthenticated* Modbus
write that skips the login entirely.
"""
import json
import os
import pathlib
import time

from flask import Flask, jsonify, redirect, request, session

from maps import FACTORY, POWER, SEWAGE, WATER
from store import FCTX, FLOCK, PCTX, PLOCK, SGCTX, SGLOCK, WCTX, WLOCK, rd, wr

app = Flask(__name__)
app.secret_key = os.environ.get("HMI_SECRET", "field-plc-dev")

# Short-lived operator sessions: open the HMI after a real gap and it asks to
# sign in again. Active use keeps it alive. Tunable with PKT_PORTAL_TTL.
_PORTAL_TTL = int(os.environ.get("PKT_PORTAL_TTL", "180") or 180)


@app.before_request
def _portal_idle_timeout():
    seen = session.get("_seen")
    if seen and (time.time() - seen) > _PORTAL_TTL:
        for k in [k for k in list(session.keys()) if k.startswith("op_")]:
            session.pop(k, None)
    session["_seen"] = time.time()

# Per-plant operator logins are minted by `scoring` into /run/secret/creds/ and
# rotate on policy (blue team rolls them at Alert L2). Read live per request so
# a rotation needs no restart; fall back to the shipped default if the vault
# isn't mounted. The login is NOT the scored bug - the Modbus bus is.
CRED_DIR = pathlib.Path("/run/secret/creds")


def plant_creds(plant):
    try:
        c = json.loads((CRED_DIR / f"hmi-{plant}.json").read_text())
        return c.get("user", "operator"), c.get("pass", "operator")
    except (OSError, ValueError):
        return os.environ.get("HMI_USER", "operator"), os.environ.get("HMI_PASS", "operator")

CTX = {"water": (WCTX, WLOCK), "power": (PCTX, PLOCK),
       "factory": (FCTX, FLOCK), "sewage": (SGCTX, SGLOCK)}
HAND_BASE = 20   # HR HAND_BASE+coil = 1 -> that device is in HAND (segmented build honours it)

THEMES = {
    "water": dict(brand="AQUAVIEW", model="4 TREATMENT SCADA",
                  bg="#0d2530", screen="#c6d8de", ink="#123", accent="#0e77b7",
                  bar="#0e77b7", lbl="#12324a", vendor="Aquaview Systems Inc."),
    "power": dict(brand="GRIDMASTER", model="RTU // BUS CONTROL // HV",
                  bg="#161617", screen="#22252a", ink="#eee", accent="#f4c020",
                  bar="#8a1f14", lbl="#c9cdd2", vendor="GridMaster Controls"),
    "factory": dict(brand="PLANTLINK", model="HMI r3.1  LINE / LOADING",
                    bg="#20201d", screen="#2e2e2a", ink="#e8e4d8", accent="#e07b2c",
                    bar="#4a463c", lbl="#cfc9b8", vendor="PlantLink OT"),
    "sewage": dict(brand="CLARUS", model="EFFLUENT & RETURN",
                   bg="#182016", screen="#eef1e8", ink="#28321f", accent="#5c7d3a",
                   bar="#3f5626", lbl="#28321f", vendor="Clarus Environmental"),
}
TITLES = {"water": "Packet River Municipal Water Authority",
          "power": "Packet River Power & Light - Substation 1",
          "factory": "Packet River Widget Works - Line & Loading",
          "sewage": "Packet River Water Reclamation Facility"}

# ---------------------------------------------------------------------------
# Per-plant mimic definitions. Coordinates are in a 0..960 x 0..420 viewBox.
#   pipes    : SVG path `d` strings (drawn grey-blue, behind devices)
#   devices  : {id, coil, kind: pump|breaker|valve, x, y, label,
#               on/off: display words for the faceplate}
#   tank     : optional {x,y,w,h, src ("hr:N"), scale, label}
#   tags     : {x,y, label, src, unit, scale, fmt (decimals), hi (>value -> red)}
#   sp       : {reg, label, unit, scale, step, lo, hi}
# ---------------------------------------------------------------------------
PLANTS = {
  "water": dict(
    pipes=["M40 330 H250", "M250 330 V150 H360", "M250 240 H150 V300",
           "M600 150 H860", "M760 150 V330 H900"],
    devices=[
      dict(id="INTAKE", coil=0, kind="pump", x=120, y=330, label="Intake P-101"),
      dict(id="HIGHLIFT", coil=1, kind="pump", x=470, y=150, label="High-lift P-201"),
      dict(id="CHLORINE", coil=2, kind="pump", x=175, y=270, label="Cl2 dosing P-301"),
      dict(id="MAIN_VALVE", coil=3, kind="valve", x=340, y=150, label="Main isol. valve",
           on="OPEN", off="CLOSED"),
    ],
    tank=dict(x=560, y=95, w=120, h=150, src="hr:10", scale=0.1, label="Clearwell / Tower"),
    tags=[
      dict(x=110, y=330, label="1FT101", src="hr:13", unit="gpm", scale=1, fmt=0),
      dict(x=470, y=150, label="2PT201", src="hr:11", unit="psi", scale=0.1, fmt=1, hi=None),
      dict(x=175, y=270, label="3AIT301", src="hr:12", unit="ppm", scale=0.01, fmt=2),
      dict(x=780, y=330, label="Dist. pressure", src="hr:11", unit="psi", scale=0.1, fmt=1),
    ],
    sp=[dict(reg=0, label="High-lift setpoint", unit="psi", scale=0.1, step=1, lo=400, hi=700)],
  ),
  "power": dict(
    pipes=["M40 60 H150", "M150 60 V360", "M150 120 H900", "M150 200 H900",
           "M150 280 H900", "M150 350 H900", "M40 350 H150"],
    devices=[
      dict(id="BRK_MAIN", coil=0, kind="breaker", x=150, y=60, label="52-M incomer",
           on="CLOSED", off="OPEN"),
      dict(id="BRK_RES", coil=1, kind="breaker", x=760, y=120, label="52-1 residential",
           on="CLOSED", off="OPEN"),
      dict(id="BRK_BIZ", coil=2, kind="breaker", x=760, y=200, label="52-2 business",
           on="CLOSED", off="OPEN"),
      dict(id="BRK_IND", coil=3, kind="breaker", x=760, y=280, label="52-3 plants",
           on="CLOSED", off="OPEN"),
      dict(id="BRK_ST", coil=4, kind="breaker", x=760, y=350, label="52-4 streetlights",
           on="CLOSED", off="OPEN"),
      dict(id="GEN_ENABLE", coil=5, kind="pump", x=90, y=350, label="Local generation",
           on="ONLINE", off="OFFLINE"),
    ],
    tags=[
      dict(x=290, y=120, label="Bus freq", src="hr:10", unit="Hz", scale=0.01, fmt=2),
      dict(x=470, y=120, label="Bus volt", src="hr:11", unit="kV", scale=0.1, fmt=1),
      dict(x=650, y=120, label="Load", src="hr:12", unit="MW", scale=0.1, fmt=1),
    ],
    sp=[dict(reg=0, label="Generation setpoint", unit="MW", scale=0.1, step=1, lo=40, hi=120)],
  ),
  "factory": dict(
    pipes=["M60 210 H560", "M560 210 V120 H720", "M300 210 V330 H520"],
    devices=[
      dict(id="LINE_RUN", coil=0, kind="pump", x=180, y=210, label="Assembly line M-1",
           on="RUNNING", off="STOPPED"),
      dict(id="ESTOP_BYPASS", coil=1, kind="valve", x=380, y=210, label="E-stop interlock",
           on="BYPASSED", off="ARMED"),
      dict(id="GANTRY", coil=2, kind="pump", x=640, y=120, label="Loading gantry",
           on="RUNNING", off="STOPPED"),
      dict(id="HOPPER_GATE", coil=3, kind="valve", x=420, y=330, label="Hopper gate",
           on="OPEN", off="SHUT"),
    ],
    tags=[
      dict(x=180, y=210, label="Line speed", src="hr:0", unit="%", scale=1, fmt=0),
      dict(x=560, y=210, label="Throughput", src="hr:11", unit="%", scale=1, fmt=0),
      dict(x=640, y=120, label="Car in pos.", src="di:0", unit="", scale=1, fmt=0),
    ],
    sp=[dict(reg=0, label="Line speed setpoint", unit="%", scale=1, step=1, lo=20, hi=90)],
  ),
  "sewage": dict(
    pipes=["M40 210 H220", "M220 210 H420", "M420 210 H620", "M620 210 H900",
           "M300 210 V330 H900"],
    devices=[
      dict(id="AERATION", coil=0, kind="pump", x=300, y=210, label="Aeration blower B-1",
           on="RUNNING", off="STOPPED"),
      dict(id="CHEM_DOSE", coil=1, kind="pump", x=500, y=210, label="Disinfection P-2",
           on="DOSING", off="OFF"),
      dict(id="RETURN_PUMP", coil=2, kind="pump", x=700, y=210, label="Treated-return P-3",
           on="RUNNING", off="STOPPED"),
      dict(id="BYPASS_GATE", coil=3, kind="valve", x=500, y=330, label="Storm bypass gate",
           on="OPEN", off="SHUT"),
    ],
    tank=dict(x=180, y=150, w=90, h=120, src="hr:10", scale=1, label="Aeration basin DO"),
    tags=[
      dict(x=300, y=210, label="DO", src="hr:10", unit="mg/L", scale=0.1, fmt=1),
      dict(x=500, y=210, label="Turbidity", src="hr:11", unit="NTU", scale=0.1, fmt=1, hi=300),
      dict(x=700, y=210, label="Effluent qual.", src="hr:12", unit="%", scale=0.1, fmt=0),
    ],
    sp=[dict(reg=0, label="Disinfection dose", unit="mg/L", scale=0.01, step=5, lo=80, hi=260)],
  ),
}


# -- shared chrome ---------------------------------------------------------
def shell(plant, heading, body_html):
    t = THEMES[plant]
    return f"""<!doctype html><meta charset=utf-8><title>{TITLES[plant]} - {heading}</title>
<style>
 :root{{--bg:{t['bg']};--screen:{t['screen']};--ink:{t['ink']};--acc:{t['accent']};--bar:{t['bar']}}}
 *{{box-sizing:border-box}}
 body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 'Segoe UI',system-ui,sans-serif;
   min-height:100vh;display:flex;justify-content:center;padding:14px}}
 .panel{{background:#0000;max-width:1000px;width:100%}}
 .bar{{background:var(--bar);color:#fff;padding:9px 16px;font-weight:800;letter-spacing:.08em;
   border-radius:6px 6px 0 0;display:flex;justify-content:space-between;align-items:baseline}}
 .bar small{{font-weight:600;letter-spacing:.14em;opacity:.85}}
 .screen{{background:var(--screen);color:#123;border:2px solid #0006;border-radius:0 0 6px 6px;padding:0}}
 nav{{background:#00000010;border-bottom:1px solid #0002;padding:5px 12px;font-size:12px;
   display:flex;justify-content:space-between;align-items:center}}
 nav a{{color:#1b5e8a;text-decoration:none}}
 .alarmbar{{min-height:22px;background:#f5e9e9;color:#a11;padding:3px 12px;font-size:12px;
   font-weight:700;border-bottom:1px solid #0002}}
 .mimic{{position:relative}} svg{{display:block;width:100%;height:auto;background:var(--screen)}}
 .dev{{cursor:pointer}}
 .tag{{position:absolute;transform:translate(-50%,calc(-100% - 12px));font:10px/1.2 'Courier New',monospace;text-align:center}}
 .tag::after{{content:'';position:absolute;left:50%;top:100%;width:1px;height:12px;background:#2b5c86}}
 .tag .h{{background:#2b5c86;color:#fff;padding:1px 4px;white-space:nowrap}}
 .tag .v{{background:#eef4f6;color:#12324a;padding:1px 4px;border:1px solid #2b5c86;border-top:0}}
 .tag .v.hi{{background:#f4c9c9;color:#7a1414;font-weight:700}}
 .foot{{padding:8px 12px;font-size:11px;color:#0007}}
 /* login */
 form.portal{{max-width:320px;margin:44px auto;color:#123}}
 form.portal input{{display:block;width:100%;margin:6px 0;padding:8px 10px;border:1px solid #0003;border-radius:4px;font:inherit}}
 form.portal button,button.act{{padding:7px 16px;border:0;border-radius:4px;background:var(--acc);color:#fff;
   font:inherit;font-weight:700;cursor:pointer}}
 .err{{color:#a11;font-size:13px}}
 /* faceplate */
 .pop{{position:fixed;inset:0;background:#0007;display:flex;align-items:center;justify-content:center;z-index:20}}
 .pop .box{{background:#eef1f2;color:#123;border:2px solid #0006;border-radius:6px;min-width:280px}}
 .pop h3{{margin:0;background:#2b5c86;color:#fff;padding:7px 12px;display:flex;justify-content:space-between}}
 .pop h3 button{{background:0;border:0;color:#fff;font-size:1.1em;cursor:pointer}}
 .pop .body{{padding:12px}} .pop .row{{display:flex;justify-content:space-between;gap:8px;margin:8px 0;align-items:center}}
 .pop input{{width:90px;padding:3px 5px;border:1px solid #0003;font:inherit}}
 [hidden]{{display:none!important}}
 #toast{{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:#123c4d;color:#cfe;
   padding:6px 14px;border-radius:4px;font-size:12px;z-index:30}}
</style>
<div class=panel>
 <div class=bar><span>{t['brand']} &nbsp; <small>{TITLES[plant]}</small></span><small>{t['model']}</small></div>
 <div class=screen>{body_html}</div>
 <div class=foot>{t['vendor']} &bull; operator terminal</div>
</div>
<div id=toast hidden></div>"""


EGGS = os.environ.get("PKT_EGGS", "off")
_EGG_LOGIN = {
    "subtle": "<!-- op logins get rotated. last shift's are on the historian handover. -->",
    "obvious": "<!-- operator passwords rotate on a schedule now. the current set is on the "
               "shift-handover sheet the historian serves at /ops/handover.txt (no login). -->",
}
_EGG_NOTES = {
    "subtle": "field bus notes\n--------------\n- writes are open on the bus. no auth on the protocol.\n"
              "- the session flag block sits in the input registers; it only reads back\n"
              "  while the PLC is in maintenance mode (a coil).\n",
    "obvious": "field bus engineering notes\n---------------------------\n"
               "- Modbus/TCP takes writes from anything that can reach the port. there is no\n"
               "  authentication in the protocol. segment it; we haven't.\n"
               "- this run's flag is packed into an input-register block. it stays zeroed\n"
               "  until the maintenance-mode coil is set, then it reads back as ASCII.\n"
               "- pymodbus, or the bundled modbus_attack.py, does both.\n",
}


def login_form(plant, err=""):
    ports = {"water": 502, "power": 503, "factory": 504, "sewage": 505}
    egg = _EGG_LOGIN.get(EGGS, "")
    return shell(plant, "Sign in", f"""{egg}
      <form class=portal method=post action="/{plant}/login">
        <h2 style="font-size:13px;letter-spacing:.08em;color:#2b5c86">OPERATOR SIGN-IN</h2>
        {'<p class=err>' + err + '</p>' if err else ''}
        <label>Operator ID</label><input name=user autofocus autocomplete=off>
        <label>Password</label><input name=password type=password>
        <button type=submit>Sign in</button>
        <p style="font-size:11px;color:#666;margin-top:14px">Field bus in service &mdash;
           engineering writes accepted on Modbus/TCP {ports.get(plant, 502)}.</p>
      </form>""")


# -- SVG mimic rendering -------------------------------------------------
def _svg(plant):
    d = PLANTS[plant]
    lbl = THEMES[plant].get("lbl", "#12324a")
    parts = ['<svg viewBox="0 0 960 420" preserveAspectRatio="xMidYMid meet">']
    for p in d["pipes"]:
        parts.append(f'<path d="{p}" stroke="#2f6fb0" stroke-width="4" fill="none"/>')
    tk = d.get("tank")
    if tk:
        parts.append(f'<rect x="{tk["x"]}" y="{tk["y"]}" width="{tk["w"]}" height="{tk["h"]}" '
                     f'fill="#eef4f6" stroke="#1b4b7a" stroke-width="2"/>')
        parts.append(f'<rect id="tankfill" x="{tk["x"]+2}" y="{tk["y"]+tk["h"]-2}" '
                     f'width="{tk["w"]-4}" height="0" fill="#2f6fb0"/>')
        parts.append(f'<text x="{tk["x"]+tk["w"]/2}" y="{tk["y"]-10}" font-size="15" font-weight="600" '
                     f'fill="{lbl}" text-anchor="middle">{tk["label"]}</text>')
    for dev in d["devices"]:
        x, y, k = dev["x"], dev["y"], dev["kind"]
        gid = f'dev-{dev["id"]}'
        if k == "pump":
            parts.append(f'<g class=dev id="{gid}" data-dev="{dev["id"]}" data-coil="{dev["coil"]}">'
                         f'<circle cx="{x}" cy="{y}" r="15" fill="#3a3f45" stroke="#1b4b7a" stroke-width="2"/>'
                         f'<path d="M{x-7} {y} L{x+6} {y-7} L{x+6} {y+7} Z" fill="#c6d8de"/></g>')
        elif k == "breaker":
            parts.append(f'<g class=dev id="{gid}" data-dev="{dev["id"]}" data-coil="{dev["coil"]}">'
                         f'<rect x="{x-13}" y="{y-13}" width="26" height="26" fill="#3a3f45" '
                         f'stroke="#1b4b7a" stroke-width="2"/>'
                         f'<line class=brkbar x1="{x}" y1="{y-9}" x2="{x}" y2="{y+9}" '
                         f'stroke="#c6d8de" stroke-width="3"/></g>')
        else:  # valve
            parts.append(f'<g class=dev id="{gid}" data-dev="{dev["id"]}" data-coil="{dev["coil"]}">'
                         f'<path d="M{x-13} {y-11} L{x} {y} L{x-13} {y+11} Z" fill="#3a3f45" stroke="#1b4b7a"/>'
                         f'<path d="M{x+13} {y-11} L{x} {y} L{x+13} {y+11} Z" fill="#3a3f45" stroke="#1b4b7a"/></g>')
        parts.append(f'<text x="{x}" y="{y+36}" font-size="17" font-weight="600" '
                     f'text-anchor="middle" fill="{lbl}">{dev["label"]}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _tags_html(plant):
    d = PLANTS[plant]
    out = []
    for i, tg in enumerate(d["tags"]):
        out.append(f'<div class=tag style="left:{tg["x"]/9.6:.1f}%;top:{tg["y"]/4.2:.1f}%">'
                   f'<div class=h>{tg["label"]}</div><div class=v id="tag-{i}">--</div></div>')
    return "".join(out)


def dashboard(plant):
    import json
    d = PLANTS[plant]
    meta = dict(
        devices=[{k: dev[k] for k in dev} for dev in d["devices"]],
        tags=d["tags"], sp=d["sp"], tank=d.get("tank"), plant=plant,
    )
    body = f"""
      <nav><span>Operator: {plant}</span><a href="/{plant}/logout">Log out</a></nav>
      <div class=alarmbar id=alarmbar></div>
      <div class=mimic>{_svg(plant)}{_tags_html(plant)}</div>
      <div class=pop id=fp hidden><div class=box>
        <h3><span id=fp-tag>Faceplate</span><button onclick="hide('fp')">&times;</button></h3>
        <div class=body>
          <div class=row>State <b id=fp-state>--</b></div>
          <div class=row>Mode <b id=fp-mode>--</b></div>
          <div class=row><span>
            <button class=act onclick="mode(1)">HAND</button>
            <button class=act onclick="mode(0)">AUTO</button></span><span>
            <button class=act onclick="op(1)" id=fp-on>ON</button>
            <button class=act onclick="op(0)" id=fp-off>OFF</button></span></div>
          <p style="font-size:12px;color:#456;margin:6px 0 0">In AUTO the controller owns
             this output; ON/OFF holds only in HAND (segmented build).</p>
        </div></div></div>
      <div class=pop id=sp hidden><div class=box>
        <h3><span>Setpoints</span><button onclick="hide('sp')">&times;</button></h3>
        <div class=body id=sp-body></div></div></div>
      <p style="text-align:center;margin:6px"><button class=act onclick="show('sp')">Setpoints</button></p>
      <script>
      const META = {json.dumps(meta)};
      const $ = s => document.querySelector(s);
      function show(i){{$('#'+i).hidden=false}} function hide(i){{$('#'+i).hidden=true}}
      function toast(m){{const t=$('#toast');t.textContent=m;t.hidden=false;
        clearTimeout(toast.t);toast.t=setTimeout(()=>t.hidden=true,2400)}}
      let ST=null, FP=null;
      document.querySelectorAll('.dev').forEach(g=>g.addEventListener('click',()=>{{
        FP=META.devices.find(d=>d.id===g.dataset.dev); renderFP(); show('fp');
      }}));
      function renderFP(){{
        if(!ST||!FP)return;
        const on = ST.coils[FP.coil], hand = ST.hand[FP.coil];
        $('#fp-tag').textContent=FP.label;
        $('#fp-state').textContent = on ? (FP.on||'ON') : (FP.off||'OFF');
        $('#fp-mode').textContent = hand ? 'HAND' : 'AUTO';
        $('#fp-on').textContent = FP.on||'ON'; $('#fp-off').textContent = FP.off||'OFF';
      }}
      async function cmd(b,label){{
        try{{const r=await fetch('/{plant}/api/cmd',{{method:'POST',
          headers:{{'Content-Type':'application/json'}},body:JSON.stringify(b)}});
          const j=await r.json(); toast((r.ok&&j.ok?'→ ':'✗ ')+(label||''));}}
        catch(e){{toast('✗ '+e)}} tick();
      }}
      const mode = h => cmd({{action:'mode',coil:FP.coil,hand:!!h}}, FP.label+(h?' → HAND':' → AUTO'));
      const op   = o => cmd({{action:'set', coil:FP.coil,on:!!o}}, FP.label+(o?' ON':' OFF'));
      function renderSP(){{
        $('#sp-body').innerHTML = META.sp.map(s=>`
          <div class=row><span>${{s.label}}</span><span>
          <input id="sp-${{s.reg}}" type=number step="${{s.step}}" value="${{
            ST ? (ST.hr[s.reg]*s.scale).toFixed(s.scale<1?2:0) : ''}}">
          <button class=act onclick="setSp(${{s.reg}},${{s.scale}},${{s.lo}},${{s.hi}})">Set</button>
          ${{s.unit}}</span></div>`).join('');
      }}
      function setSp(reg,scale,lo,hi){{
        let v = Math.round(parseFloat($('#sp-'+reg).value)/scale);
        v = Math.max(lo, Math.min(hi, v));
        cmd({{action:'sp',reg,value:v}}, 'setpoint '+reg+' = '+v);
      }}
      async function tick(){{
        let r; try{{r=await(await fetch('/{plant}/api/state')).json()}}catch(e){{return}}
        if(r.error)return; ST=r;
        META.devices.forEach(d=>{{
          const g=$('#dev-'+d.id); if(!g)return;
          const on=ST.coils[d.coil], hand=ST.hand[d.coil];
          const shape=g.querySelector('circle,rect');
          if(shape) shape.setAttribute('fill', on?'#2f8f2f':'#3a3f45');
          const bar=g.querySelector('.brkbar');
          if(bar) bar.setAttribute('transform', on?'':`rotate(42 ${{d.x}} ${{d.y}})`);
          g.style.outline = hand ? '2px dashed #c98a2a' : 'none';
        }});
        META.tags.forEach((tg,i)=>{{
          let raw = tg.src.startsWith('hr:') ? ST.hr[+tg.src.slice(3)]
                  : tg.src.startsWith('di:') ? ST.di[+tg.src.slice(3)] : 0;
          const val = raw*tg.scale;
          const e=$('#tag-'+i); e.textContent = val.toFixed(tg.fmt)+(tg.unit?' '+tg.unit:'');
          e.classList.toggle('hi', tg.hi!=null && val>tg.hi);
        }});
        if(META.tank){{
          const pct = Math.max(0,Math.min(100, ST.hr[+META.tank.src.slice(3)]*META.tank.scale));
          const f=$('#tankfill'), h=META.tank.h-4, fh=h*pct/100;
          f.setAttribute('height', fh); f.setAttribute('y', META.tank.y+2+(h-fh));
        }}
        const al=[];
        ST.di.forEach((v,i)=>{{}});
        $('#alarmbar').textContent = ST.alarms.length ? '⚠ '+ST.alarms.join('   |   ') : '';
        if(!$('#fp').hidden) renderFP();
        if(!$('#sp').hidden && !$('#sp-body').innerHTML) renderSP();
      }}
      renderSP(); tick(); setInterval(tick,1500);
      </script>"""
    return shell(plant, "Overview", body)


# -- state + command APIs ----------------------------------------------
ALARM_SRC = {
    "water": lambda di: (["LOW DIST. PRESSURE"] if di[0] else []) + (["LOW TOWER"] if di[1] else [])
             + (["LOW CHLORINE"] if di[2] else []),
    "power": lambda di: [],
    "factory": lambda di: ["LINE JAM / UNSAFE"] if di[1] else [],
    "sewage": lambda di: (["HIGH TURBIDITY"] if di[0] else [])
              + (["STORM BYPASS OPEN"] if di[1] else []),
}


def _state(plant):
    ctx, lock = CTX[plant]
    coils = [int(x) for x in rd(ctx, lock, 1, 0, 8)]
    hr = [int(x) for x in rd(ctx, lock, 3, 0, 32)]
    di = [int(x) for x in rd(ctx, lock, 2, 0, 4)]
    hand = [hr[HAND_BASE + c] for c in range(8)]
    return dict(coils=coils, hr=hr, di=di, hand=hand, alarms=ALARM_SRC[plant](di))


@app.get("/<plant>/api/state")
def api_state(plant):
    if plant not in CTX:
        return jsonify(error="unknown plant"), 404
    if not session.get(f"op_{plant}"):
        return jsonify(error="auth"), 401
    return jsonify(_state(plant))


@app.post("/<plant>/api/cmd")
def api_cmd(plant):
    if plant not in CTX:
        return jsonify(error="unknown plant"), 404
    if not session.get(f"op_{plant}"):
        return jsonify(error="auth"), 401
    ctx, lock = CTX[plant]
    b = request.get_json(force=True, silent=True) or {}
    a = b.get("action")
    try:
        if a == "set":
            wr(ctx, lock, 1, int(b["coil"]), [1 if b.get("on") else 0])
        elif a == "mode":
            wr(ctx, lock, 3, HAND_BASE + int(b["coil"]), [1 if b.get("hand") else 0])
        elif a == "sp":
            wr(ctx, lock, 3, int(b["reg"]), [int(b["value"])])
        else:
            return jsonify(ok=False, error="bad action"), 400
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    return jsonify(ok=True)


# -- routes -----------------------------------------------------------
# No index of portals: each operator terminal stands alone. You reach a plant
# because you already knew its name (recon), not by following a link from here.
@app.get("/")
def index():
    # host-based routing for recon-by-name
    host = request.host.split(":")[0].split(".")[0]
    mapping = {"water": "water", "reclamation": "sewage", "power": "power", "widgetworks": "factory"}
    if host in mapping:
        return redirect(f"/{mapping[host]}")

    return ("<!doctype html><meta charset=utf-8><title>Field Operations</title>"
            "<p style=\"font:15px system-ui;margin:40px\">Packet River Field Operations. "
            "Operator terminals are not listed here.</p>"), 404


@app.get("/<plant>")
def plant_page(plant):
    if plant not in PLANTS:
        return "not found", 404
    if not session.get(f"op_{plant}"):
        return login_form(plant)
    return dashboard(plant)


@app.post("/<plant>/login")
def plant_login(plant):
    if plant not in PLANTS:
        return "not found", 404
    u, p = plant_creds(plant)
    if request.form.get("user") == u and request.form.get("password") == p:
        session[f"op_{plant}"] = u
        return redirect(f"/{plant}")
    return login_form(plant, "Wrong operator ID or password."), 401


@app.get("/<plant>/logout")
def plant_logout(plant):
    session.pop(f"op_{plant}", None)
    return redirect(f"/{plant}" if plant in PLANTS else "/")


@app.get("/ops/handover.txt")
def ops_handover():
    # the shift-handover sheet an ops team leaves on the historian. No auth -
    # a real, small finding, and it always shows the current (rotated) set.
    try:
        return (CRED_DIR / "handover.txt").read_text(), 200, {"Content-Type": "text/plain"}
    except OSError:
        return "no handover sheet on file\n", 200, {"Content-Type": "text/plain"}


@app.get("/eng/notes.txt")
def eng_notes():
    if EGGS == "off":
        return "not found\n", 404, {"Content-Type": "text/plain"}
    return _EGG_NOTES.get(EGGS, _EGG_NOTES["subtle"]), 200, {"Content-Type": "text/plain"}


@app.get("/health")
def health():
    return "ok"
