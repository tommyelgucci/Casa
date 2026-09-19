"""Puntuación económica transparente. No mide seguridad jurídica."""
from statistics import median

def comparable_median(item, items, minimum=5):
    area=item.get("land_m2"); zone=item.get("zone"); kind=item.get("kind")
    if not area or not zone or kind=="remate": return None,0
    vals=[]
    for x in items:
        if x.get("id")==item.get("id") or x.get("kind")!=kind or x.get("zone")!=zone: continue
        a=x.get("land_m2"); ppm=x.get("price_per_m2_usd")
        if a and ppm and area*.70<=a<=area*1.30: vals.append(ppm)
    return (median(vals),len(vals)) if len(vals)>=minimum else (None,len(vals))

def opportunity_score(item,cfg,items):
    parts={}; ppm=item.get("price_per_m2_usd")
    med,n=comparable_median(item,items,cfg.get("analisis_mercado",{}).get("comparables_minimos",5))
    discount=None
    if ppm and med:
        ratio=ppm/med; parts["precio_m2"]=40 if ratio<=.70 else max(0,40*(1.30-ratio)/.60)
        discount=(med-ppm)/med*100
    else:
        usd=item.get("price_usd"); cap=cfg["busqueda"]["precio_max_usd"]
        parts["precio_m2"]=max(0,min(40,40*(1-(usd/cap-1)*.5))) if usd else 0
    priority=cfg.get("zonas",{}).get("prioridad",{}).get((item.get("zone") or "").lower(),0)
    parts["ubicacion"]=min(25,priority/10*25)
    area=item.get("land_m2") or 0; target=cfg["busqueda"]["superficie_objetivo_min_m2"]
    parts["superficie"]=min(10,10*area/target) if area else 0
    parts["descuento_zona"]=min(15,max(0,(discount or 0)/30*15)) if med else 0
    parts["antiguedad"]=0
    nrem=item.get("auction_number") or 0
    parts["remate_avanzado"]=min(5,max(0,nrem-1)*2.5) if item.get("kind")=="remate" else 0
    return {"total":round(sum(parts.values()),1),"parts":{k:round(v,1) for k,v in parts.items()},
            "median_ppm":med,"comparables":n,"discount_pct":round(discount,1) if discount is not None else None}
