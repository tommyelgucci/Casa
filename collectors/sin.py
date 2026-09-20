"""SIN Bolivia - portal público de subastas/adjudicaciones de inmuebles.
Conserva resultados de Santa Cruz incluso si están fuera del presupuesto,
para permitir análisis posterior. No evade controles técnicos.
"""
import re, requests
from bs4 import BeautifulSoup
from .common import number, enrich_currency
URL="https://subastas.impuestos.gob.bo/"

def _surface(block):
    m=re.search(r"(?:SUPERFICIE\s*[:.]?\s*)?([\d.,]+)\s*(?:MTS?\.?\s*2|MTRS?2|M2|Metros²)",block,re.I)
    return number(m.group(1)) if m else None

def _ownership(text):
    m=re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:de\s+las\s+)?(?:acciones\s+y\s+derechos|sobre)",text,re.I)
    return number(m.group(1)) if m else 100.0 if re.search(r"100%|100 %",text) else None

def collect(rate=7.0):
    r=requests.get(URL,timeout=25,headers={"User-Agent":"RadarSCZ-personal/0.1"})
    r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser"); text="\n".join(soup.stripped_strings)
    # Las fichas del índice empiezan por expediente BI-xx-...
    starts=list(re.finditer(r"BI-\d{2}-\d{4}-\d+(?:-PRSP)?",text,re.I)); out=[]; seen=set()
    for i,m in enumerate(starts):
        sid=m.group(0).upper()
        if sid in seen: continue
        end=starts[i+1].start() if i+1<len(starts) else min(len(text),m.start()+2500)
        block=text[m.start():end]
        if "Santa Cruz" not in block: continue
        seen.add(sid)
        surf=_surface(block)
        pm=re.search(r"(?:Bs\.?\s*)?([\d.]+,[\d]{2})",block,re.I)
        price=number(pm.group(1)) if pm else None
        own=_ownership(block)
        upper=block.upper()\n        mode="adjudicacion" if "ADJUDICACIÓN DIRECTA" in upper else "remate"
        zone=None; low=block.lower()
        for k,words in {"cotoca":["cotoca"],"warnes":["warnes"],"porongo":["porongo"],"urubo":["urubó","urubo"],"zona_norte":["zona norte","nor este","noreste"]}.items():
            if any(w in low for w in words): zone=k; break
        out.append(enrich_currency({"source":"sin","source_id":sid,"kind":mode,"title":f"SIN {sid}",
          "url":URL,"zone":zone,"municipality":"Santa Cruz","land_m2":surf,"price":price,"currency":"BOB",
          "ownership_percent":own,"raw_text":block},rate))
    return out
