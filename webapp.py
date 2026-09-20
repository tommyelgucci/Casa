from flask import Flask, render_template_string, redirect, url_for
import yaml
from pathlib import Path
from database.db import init_db, all_items
from analysis.filters import classify
from analysis.ranking import opportunity_score
from analysis.sources import coverage

ROOT=Path(__file__).parent
cfg=yaml.safe_load((ROOT/"config.yaml").read_text(encoding="utf-8"))
init_db()
app=Flask(__name__)

HTML=r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar SCZ</title><style>
body{font-family:system-ui;margin:0;background:#0e1117;color:#fafafa}.wrap{max-width:1100px;margin:auto;padding:18px}
h1{margin-bottom:4px}.muted{color:#9aa4b2}.tabs{display:flex;gap:8px;overflow:auto;padding:12px 0}.tabs a{color:#fff;text-decoration:none;background:#262b36;padding:9px 12px;border-radius:10px;white-space:nowrap}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}.card{background:#171b24;border:1px solid #303746;border-radius:14px;padding:15px}.score{font-size:22px;font-weight:700}
.price{font-size:20px;font-weight:700}.pill{display:inline-block;padding:4px 8px;background:#292f3d;border-radius:20px;font-size:12px}.card a{color:#9ecbff}.stats{display:flex;gap:18px;flex-wrap:wrap;margin:8px 0}
</style></head><body><div class="wrap"><h1>🏠 Radar SCZ</h1><div class="muted">Terrenos, casas y remates · Santa Cruz, Bolivia</div>
<div class="tabs">{% for key,label in tabs %}<a href="/?view={{key}}">{{label}}</a>{% endfor %}</div>
{% if view=="cobertura" %}<h2>📡 Cobertura</h2><div class="grid">{% for s in cov %}<div class="card"><b>{{s.name}}</b><p>{{s.mode}}</p><span class="pill">{{s.registros}} registros</span></div>{% endfor %}</div>
{% else %}<p class="muted">{{items|length}} resultados almacenados. Un cero también puede significar que una fuente todavía necesita ajuste técnico.</p><div class="grid">
{% for x in items %}<div class="card"><div class="score">🎯 {{x.score}}/100</div><h3>{{x.title or "Propiedad"}}</h3>
<div class="price">{{x.money}}</div><div class="stats"><span>📐 {{x.area}}</span><span>📍 {{x.zone or "Por revisar"}}</span></div>
<p><span class="pill">{{x.category}}</span> <span class="pill">{{x.source}}</span></p>
{% if x.registry %}<p>🔖 Matrícula: {{x.registry}}</p>{% endif %}{% if x.auction_date %}<p>📅 {{x.auction_date}}</p>{% endif %}
<a href="{{x.url}}" target="_blank" rel="noopener">Abrir fuente ↗</a></div>{% else %}<div class="card"><h3>Aún no hay resultados</h3><p>La web ya funciona. El siguiente paso es ejecutar y validar los colectores reales.</p></div>{% endfor %}</div>{% endif %}
</div></body></html>"""

def money(x):
    p=x.get("price")
    if p is None:return "Precio no detectado"
    return ("$us " if x.get("currency")=="USD" else "Bs " if x.get("currency")=="BOB" else "")+f"{p:,.2f}"

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/")
def home():
    from flask import request
    rows=all_items()
    for x in rows:x["categoria"]=classify(x,cfg)
    view=request.args.get("view","principal")
    if view=="principal": shown=[x for x in rows if x["categoria"]=="principal" and x.get("kind") not in ("remate","adjudicacion")]
    elif view=="excepciones": shown=[x for x in rows if x["categoria"]=="excepcion"]
    elif view=="negociables": shown=[x for x in rows if x["categoria"]=="negociable"]
    elif view=="remates": shown=[x for x in rows if x.get("kind") in ("remate","adjudicacion")]
    elif view=="todo": shown=rows
    else: shown=[]
    for x in shown:
        x["score"]=opportunity_score(x,cfg,rows)["total"]; x["money"]=money(x)
        x["area"]=f'{x["land_m2"]:,.0f} m²' if x.get("land_m2") else "Superficie no detectada"; x["category"]=x["categoria"].upper()
    shown.sort(key=lambda x:x.get("score",0),reverse=True)
    tabs=[("principal","🔥 Cumple"),("excepciones","⚡ Excepciones"),("negociables","👀 Negociables"),("remates","🔨 Remates"),("todo","📋 Todo"),("cobertura","📡 Cobertura")]
    return render_template_string(HTML,items=shown,view=view,tabs=tabs,cov=coverage(rows))
