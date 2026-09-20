from flask import Flask, render_template_string, redirect, url_for, request
import yaml
from pathlib import Path
from database.db import init_db, all_items, upsert, get_mark, save_mark, marked_items, price_history, auction_history, verification_status, verification_checks, save_verification
from analysis.filters import classify
from analysis.ranking import opportunity_score
from analysis.sources import coverage\nfrom collectors.eldeber import collect as collect_eldeber\nfrom collectors.bcp import collect as collect_bcp\nfrom collectors.ganadero import collect as collect_ganadero\nfrom collectors.sin import collect as collect_sin\nfrom collectors.economico import collect as collect_economico\nfrom collectors.infocasas import collect as collect_infocasas

ROOT=Path(__file__).parent
cfg=yaml.safe_load((ROOT/"config.yaml").read_text(encoding="utf-8"))
init_db()
app=Flask(__name__)\nLAST_REPORT=[]

HTML=r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar SCZ</title><style>
body{font-family:system-ui;margin:0;background:#0e1117;color:#fafafa}.wrap{max-width:1100px;margin:auto;padding:18px}
h1{margin-bottom:4px}.muted{color:#9aa4b2}.tabs{display:flex;gap:8px;overflow:auto;padding:12px 0}.tabs a{color:#fff;text-decoration:none;background:#262b36;padding:9px 12px;border-radius:10px;white-space:nowrap}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}.card{background:#171b24;border:1px solid #303746;border-radius:14px;padding:15px}.score{font-size:22px;font-weight:700}
.price{font-size:20px;font-weight:700}.pill{display:inline-block;padding:4px 8px;background:#292f3d;border-radius:20px;font-size:12px}.card a{color:#9ecbff}.stats{display:flex;gap:18px;flex-wrap:wrap;margin:8px 0}
</style></head><body><div class="wrap"><h1>🏠 Radar SCZ</h1><div class="muted">Terrenos, casas y remates · Santa Cruz, Bolivia</div>
<form method="post" action="/actualizar" style="margin:14px 0"><button style="background:#7c3aed;color:white;border:0;border-radius:10px;padding:11px 16px;font-weight:700">🔄 Actualizar fuentes</button></form>
{% if report %}<div class="card"><b>Última actualización</b>{% for r in report %}<p>{{r}}</p>{% endfor %}</div>{% endif %}
<div class="tabs">{% for key,label in tabs %}<a href="/?view={{key}}">{{label}}</a>{% endfor %}</div>
{% if view=="cobertura" %}<h2>📡 Cobertura</h2><div class="grid">{% for s in cov %}<div class="card"><b>{{s.name}}</b><p>{{s.mode}}</p><span class="pill">{{s.registros}} registros</span></div>{% endfor %}</div>
{% else %}<p class="muted">{{items|length}} resultados almacenados. Un cero también puede significar que una fuente todavía necesita ajuste técnico.</p><div class="grid">
{% for x in items %}<div class="card"><div class="score">🎯 {{x.score}}/100</div><h3>{{x.title or "Propiedad"}}</h3>
<div class="price">{{x.money}}</div><div class="stats"><span>📐 {{x.area}}</span><span>📍 {{x.zone or "Por revisar"}}</span></div>
<p><span class="pill">{{x.category}}</span> <span class="pill">{{x.source}}</span></p>
{% if x.registry %}<p>🔖 Matrícula: {{x.registry}}</p>{% endif %}{% if x.auction_date %}<p>📅 {{x.auction_date}}</p>{% endif %}
{% if x.price_hist|length > 1 %}<details><summary>📈 Historial de precios ({{x.price_hist|length}})</summary>{% for h in x.price_hist %}<p>{{h.observed_at[:10]}} · {{h.currency or ""}} {{h.price or "—"}}</p>{% endfor %}</details>{% endif %}
{% if x.auction_hist|length > 1 %}<details><summary>🔨 Historial conocido de matrícula</summary>{% for h in x.auction_hist %}<p>Remate {{h.auction_number or "—"}} · {{h.currency or ""}} {{h.price or "—"}} · {{h.auction_date or "fecha por revisar"}}</p>{% endfor %}<small class="muted">Sólo eventos encontrados; no se infieren etapas faltantes.</small></details>{% endif %}
{% if x.kind in ["remate","adjudicacion"] %}<p>⚖️ Verificación jurídica: <b>{{x.verification}}</b> · <a href="/verificar/{{x.id}}">abrir checklist</a></p>{% endif %}
<a href="{{x.url}}" target="_blank" rel="noopener">Abrir fuente ↗</a>
<form method="post" action="/marca/{{x.id}}" style="margin-top:12px;display:flex;gap:8px">
<input type="hidden" name="back" value="{{view}}">
<button name="action" value="favorite" style="padding:7px;border-radius:8px">❤️ Guardar</button>
<button name="action" value="watching" style="padding:7px;border-radius:8px">👀 Vigilar</button>
</form></div>{% else %}<div class="card"><h3>Aún no hay resultados</h3><p>La web ya funciona. El siguiente paso es ejecutar y validar los colectores reales.</p></div>{% endfor %}</div>{% endif %}
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
        x["price_hist"]=price_history(x["id"])
        x["auction_hist"]=auction_history(x.get("registry")) if x.get("registry") else []
        x["verification"]=verification_status(x["id"]) if x.get("kind") in ("remate","adjudicacion") else ""
    shown.sort(key=lambda x:x.get("score",0),reverse=True)
    tabs=[("principal","🔥 Cumple"),("excepciones","⚡ Excepciones"),("negociables","👀 Negociables"),("remates","🔨 Remates"),("favoritos","❤️ Guardados"),("vigilar","👀 Vigilar"),("todo","📋 Todo"),("cobertura","📡 Cobertura")]
    return render_template_string(HTML,items=shown,view=view,tabs=tabs,cov=coverage(rows),report=LAST_REPORT)


@app.post("/actualizar")
def actualizar():
    global LAST_REPORT
    rate=float(cfg.get("moneda",{}).get("usd_bob",7.0))
    collectors=[
      ("El Deber",collect_eldeber),("BCP",collect_bcp),("Banco Ganadero",collect_ganadero),
      ("SIN",collect_sin),("Banco Económico",collect_economico),("InfoCasas",collect_infocasas)
    ]
    report=[]
    for name,collector in collectors:
        try:
            found=collector(rate)
            new=0; changed=0
            for item in found:
                result=upsert(item); new+=int(result["created"]); changed+=int(result["price_changed"])
            report.append(f"✅ {name}: {len(found)} encontrados · {new} nuevos · {changed} cambios de precio")
        except Exception as exc:
            report.append(f"⚠️ {name}: {type(exc).__name__}: {str(exc)[:160]}")
    LAST_REPORT=report
    return redirect(url_for("home",view="todo"))


@app.post("/marca/<int:item_id>")
def marca(item_id):
    mark=get_mark(item_id); action=request.form.get("action")
    fav=bool(mark.get("favorite")); watch=bool(mark.get("watching"))
    if action=="favorite": fav=not fav
    if action=="watching": watch=not watch
    save_mark(item_id,fav,watch,mark.get("notes") or "")
    return redirect(url_for("home",view=request.form.get("back","todo")))


VERIFY_HTML=r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Verificación · Radar SCZ</title>
<style>body{font-family:system-ui;background:#0e1117;color:#fff;max-width:760px;margin:auto;padding:20px}.row{background:#171b24;padding:12px;margin:8px 0;border-radius:10px}select,input{padding:8px;width:100%;box-sizing:border-box;margin:5px 0}button{padding:10px 15px}</style></head><body>
<a href="/?view=remates" style="color:#9ecbff">← Remates</a><h1>⚖️ Checklist jurídico</h1><p>Esto organiza comprobaciones; no sustituye revisión legal, registral ni una visita física.</p>
<form method="post">{% for x in checks %}<div class="row"><b>{{labels.get(x.check_type,x.check_type)}}</b><select name="status_{{x.check_type}}">{% for s in states %}<option value="{{s}}" {% if s==x.status %}selected{% endif %}>{{s}}</option>{% endfor %}</select><input name="notes_{{x.check_type}}" value="{{x.notes or ''}}" placeholder="Notas / documento comprobado"></div>{% endfor %}<button>Guardar</button></form></body></html>"""

@app.route("/verificar/<int:item_id>",methods=["GET","POST"])
def verificar(item_id):
    states=["desconocido","pendiente","verificado","alerta"]
    labels={"folio_real":"Folio Real vigente","gravamenes":"Gravámenes","impuestos_municipales":"Impuestos municipales","ocupacion":"Ocupación","litigios_adicionales":"Litigios adicionales","propiedad_100":"100% de propiedad","plano_catastro":"Plano / catastro","visita_fisica":"Visita física"}
    checks=verification_checks(item_id)
    if request.method=="POST":
        for x in checks:
            t=x["check_type"]
            save_verification(item_id,t,request.form.get("status_"+t,"desconocido"),request.form.get("notes_"+t,""))
        return redirect(url_for("verificar",item_id=item_id))
    return render_template_string(VERIFY_HTML,checks=checks,states=states,labels=labels)
