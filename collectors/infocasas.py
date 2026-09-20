"""InfoCasas Bolivia - búsqueda pública de terrenos en Santa Cruz.

Uso conservador: una sola página pública por actualización, sin paginación
agresiva, login, CAPTCHA ni evasión de 403/429. Guarda el enlace original.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency

BASE="https://www.infocasas.com.bo"
URL=BASE+"/venta/lotes-o-terrenos/santa-cruz/m2-desde-400/totales"

def _zone(text):
    t=text.lower()
    for key,words in {
      "equipetrol":["equipetrol"],"urubo":["urubó","urubo"],"porongo":["porongo"],
      "warnes":["warnes"],"beni":["av. beni","avenida beni","prolongación beni"],
      "banzer":["banzer"],"zona_norte":["norte","zona norte"]
    }.items():
        if any(w in t for w in words): return key
    return None

def collect(rate=7.0):
    r=requests.get(URL,timeout=25,headers={"User-Agent":"RadarSCZ-personal/0.1"})
    if r.status_code in (403,429): return []
    r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser"); out=[]; seen=set()
    # InfoCasas puede cambiar su HTML; tomamos contenedores con precio + m² y
    # sólo aceptamos los que tienen un enlace interno identificable.
    for a in soup.select("a[href]"):
        box=a
        for _ in range(4):
            if box.parent: box=box.parent
        text=" ".join(box.stripped_strings)
        if not re.search(r"(?:U\$S|US\$|\$us|Bs\.?)\s*[\d.,]+",text,re.I): continue
        sm=re.search(r"([\d.,]+)\s*m²",text,re.I)
        if not sm: continue
        href=urljoin(BASE,a.get("href",""))
        if href in seen or "infocasas.com.bo" not in href: continue
        # Evita navegación/categorías: una ficha debe tener texto descriptivo suficiente.
        if len(text)<45: continue
        seen.add(href)
        pm=re.search(r"(U\$S|US\$|\$us|Bs\.?)\s*([\d.,]+)",text,re.I)
        if not pm: continue
        cur="BOB" if pm.group(1).lower().startswith("bs") else "USD"
        title=a.get_text(" ",strip=True) or re.sub(r"\s+"," ",text)[:110]
        out.append(enrich_currency({"source":"infocasas","source_id":href,"kind":"terreno",
          "title":title[:160],"url":href,"zone":_zone(text),"municipality":"Santa Cruz",
          "land_m2":number(sm.group(1)),"price":number(pm.group(2)),"currency":cur,
          "raw_text":text[:4000]},rate))
    return out
