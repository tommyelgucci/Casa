"""Detecta señales interesantes sin convertirlas en recomendaciones de compra."""
from analysis.filters import classify
from database.db import price_history, all_items

def events_for(item,cfg):
    events=[]; hist=price_history(item["id"])
    if len(hist)>=2:
        prev,last=hist[-2],hist[-1]
        p0,p1=prev.get("price_usd"),last.get("price_usd")
        if p0 and p1 and p1<p0:
            drop=(p0-p1)/p0*100
            events.append({"level":"price_drop","text":f"📉 Bajó {drop:.1f}%: $us {p0:,.0f} → $us {p1:,.0f}"})
        old=dict(item); old["price_usd"]=prev.get("price_usd"); old["price_bob"]=prev.get("price_bob")
        if classify(old,cfg) not in ("principal","excepcion") and classify(item,cfg) in ("principal","excepcion"):
            events.append({"level":"entered_budget","text":"🚨 Acaba de entrar en tu presupuesto"})
    if item.get("kind")=="remate" and item.get("registry"):
        same=[x for x in all_items() if x["id"]!=item["id"] and x.get("registry")==item["registry"]]
        nums=[x.get("auction_number") for x in same if x.get("auction_number")]
        if nums and item.get("auction_number") and item["auction_number"]>max(nums):
            events.append({"level":"advanced_auction","text":f"🔨 Nueva etapa: remate N.º {item['auction_number']} para la misma matrícula"})
        if same:
            events.append({"level":"same_registry","text":f"🔗 Matrícula vista en {len(same)+1} registros: revisar historial del inmueble"})
    share=item.get("ownership_percent")
    if share is not None and share<100:
        events.append({"level":"share_warning","text":f"🚨 Se ofrece sólo {share:g}% de acciones/derechos"})
    return events
