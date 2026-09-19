"""Recolector conservador de Clasificados EL DEBER.
Sólo procesa enlaces de anuncios públicos; no evade controles técnicos.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency
BASE="https://clasificados.eldeber.com.bo"; URL=BASE+"/category/inmuebles"

def _parse_text(text):
    low=text.lower(); item={}
    # El listado mezcla m² construidos y terreno. Preferimos menciones explícitas de terreno/lote.
    land=re.search(r"(?:terreno|terr(?:eno)?\.?|lote)[^0-9]{0,20}(\d[\d.,]*)\s*m(?:2|²|ts?2?)?",text,re.I)
    generic=re.search(r"(\d[\d.,]*)\s*m(?:2|²)",text,re.I)
    if land: item["land_m2"]=number(land.group(1))
    elif generic and ("lote" in low or "terreno" in low): item["land_m2"]=number(generic.group(1))
    built=re.search(r"(?:const(?:ruidos?|rucci[oó]n)?\.?)[^0-9]{0,15}(\d[\d.,]*)\s*m(?:2|²)",text,re.I)
    if built: item["built_m2"]=number(built.group(1))
    # Formatos observados: 55.000 $us, $us 85.000, 520.000 bs, 15000 $us.
    usd=re.search(r"(?:\$us|us\$|usd)\.?\s*([\d.,]+)|([\d.,]+)\s*(?:\$us|us\$|usd|d[oó]lares)",text,re.I)
    bob=re.search(r"(?:bs\.?|bob)\s*([\d.,]+)|([\d.,]+)\s*(?:bs\.?|bob)",text,re.I)
    if usd:
        item["price"]=number(next(x for x in usd.groups() if x)); item["currency"]="USD"
    elif bob:
        item["price"]=number(next(x for x in bob.groups() if x)); item["currency"]="BOB"
    item["kind"]="casa" if "casa" in low else "terreno" if ("lote" in low or "terreno" in low) else "otro"
    for key,words in {"warnes":["warnes"],"porongo":["porongo"],"urubo":["urubó","urubo"],"av_beni":["av. beni","av beni"],"av_banzer":["av. banzer","av banzer"],"equipetrol":["equipetrol"],"zona_norte":["zona norte"]}.items():
        if any(w in low for w in words): item["zone"]=key; break
    return item

def collect(rate=7.0):
    r=requests.get(URL,timeout=20,headers={"User-Agent":"RadarSCZ-personal/0.1"})
    r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser"); out=[]; seen=set()
    # Los anuncios actuales llevan IDs como INMUEBLESB000447675 / INMUEBLESW007004819.
    for a in soup.select("a[href]"):
        text=" ".join(a.stripped_strings)
        parent=" ".join(a.parent.stripped_strings) if a.parent else text
        blob=(text+" "+parent).strip()
        m=re.search(r"(INMUEBLES[A-Z]\d+)",blob,re.I)
        if not m: continue
        source_id=m.group(1).upper()
        href=a.get("href",""); url=urljoin(BASE,href)
        if source_id in seen: continue
        seen.add(source_id)
        item={"source":"eldeber","source_id":source_id,"title":text[:250] or source_id,"url":url,"raw_text":blob}
        item.update(_parse_text(blob))
        if item["kind"] in ("casa","terreno"): out.append(enrich_currency(item,rate))
    return out
