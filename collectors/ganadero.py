"""Banco Ganadero - avisos públicos de remates.
Extrae sólo inmuebles de Santa Cruz; ignora vehículos y otros bienes muebles.
No evade controles técnicos.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency
BASE="https://www.bg.com.bo"; URL=BASE+"/aviso-de-remates/"

def _first(text,pat):
    m=re.search(pat,text,re.I); return m.group(1).strip() if m else None

def collect(rate=7.0):
    s=requests.Session(); s.headers.update({"User-Agent":"RadarSCZ-personal/0.1"})
    r=s.get(URL,timeout=20); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
    links=[]
    for a in soup.select("a[href]"):
        href=a.get("href","")
        if re.search(r"/aviso-de-remates/\d+/?$",href):
            u=urljoin(BASE,href)
            if u not in links: links.append(u)
    out=[]
    for url in links:
        d=s.get(url,timeout=20); d.raise_for_status(); p=BeautifulSoup(d.text,"html.parser")
        text=" ".join(p.stripped_strings); low=text.lower()
        if "ciudad:santa cruz" not in low and "ciudad: santa cruz" not in low: continue
        # Evita remates de automotores/bienes muebles.
        if "bien mueble" in low or "vehículo" in low or "vehiculo" in low: continue
        surface=_first(text,r"(?:superficie|sup\.)\s*(?:de)?\s*([\d.,]+)\s*(?:m2|mts2|m²)")
        registry=_first(text,r"matr[ií]cula(?:\s+n[°ºo.]*)?\s*([\d.]+)")
        audience=_first(text,r"Audiencia\s*:\s*(\d+)")
        court=_first(text,r"Juzgado\s*:\s*([^:]{1,50}?)(?=\s+(?:Audiencia|Lugar|Descripción|Descripcion))")
        date=_first(text,r"Fecha\s*:\s*(\d{1,2}/\d{1,2}/\d{4})")
        price=_first(text,r"Precio\s*:\s*([\d.,]+)\s*(?:Bs|\$us)")
        cur="USD" if re.search(r"Precio\s*:\s*[\d.,]+\s*\$us",text,re.I) else "BOB"
        zone=None
        for k,words in {"warnes":["warnes"],"porongo":["porongo"],"urubo":["urubo","urubó"],"zona_norte":["zona norte","palmas del norte"],"equipetrol":["equipetrol"]}.items():
            if any(w in low for w in words): zone=k; break
        item={"source":"banco_ganadero","source_id":url.rstrip("/").split("/")[-1],"kind":"remate",
              "title":"Remate Banco Ganadero","url":url,"zone":zone,"municipality":"Santa Cruz",
              "land_m2":number(surface),"price":number(price),"currency":cur,"registry":registry,
              "auction_number":int(audience) if audience else None,"court":court,"auction_date":date,"raw_text":text}
        out.append(enrich_currency(item,rate))
    return out
