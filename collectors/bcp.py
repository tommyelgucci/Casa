"""Recolector de Remates BCP Santa Cruz.
Procesa listado y fichas públicas; no evade controles técnicos.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency
BASE="https://www.bcp.com.bo"; URL=BASE+"/BienesAdjudicados/Remates?dep=santa+cruz"

def _grab(text,pattern):
    m=re.search(pattern,text,re.I); return m.group(1).strip() if m else None

def collect(rate=7.0):
    s=requests.Session(); s.headers.update({"User-Agent":"RadarSCZ-personal/0.1"})
    r=s.get(URL,timeout=20); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
    links=[]
    for a in soup.select("a[href]"):
        href=a.get("href","")
        if "/BienesAdjudicados/Remates/detalle/" in href:
            u=urljoin(BASE,href)
            if u not in links: links.append(u)
    out=[]
    for url in links:
        d=s.get(url,timeout=20); d.raise_for_status(); page=BeautifulSoup(d.text,"html.parser")
        text=" ".join(page.stripped_strings)
        surface=_grab(text,r"(?:superficie(?:\s+de)?|sup\.)\s*[:\-]?\s*([\d.,]+)\s*(?:m²|mts?\.?\s*2|m2)")
        auction=_grab(text,r"(?:n[uú]mero\s+de\s+remate)\s*[:\-]?\s*0*(\d+)")
        registry=_grab(text,r"(?:matr[ií]cula|folio\s+con\s+matr[ií]cula)(?:\s+n[°ºo.]*)?\s*[:\-]?\s*([\d.]+)")
        # En BCP el precio puede preceder a Bs. o $us.
        bob=_grab(text,r"([\d.]+,[\d]{2})\s*Bs\.?")
        usd=_grab(text,r"([\d.]+,[\d]{2})\s*\$us\.?")
        court=_grab(text,r"(?:juzgado)\s*[:\-]?\s*([^|]{3,100}?)(?=\s+(?:fecha|lugar|n[uú]mero|matr[ií]cula|$))")
        date=_grab(text,r"Fecha\s+de\s+remate\s*[:\-]?\s*([^|]{5,80}?)(?=\s+(?:lugar|juzgado|n[uú]mero|$))")
        item={"source":"bcp","source_id":url.rstrip("/").split("/")[-1],"kind":"remate",
              "title":"Remate BCP Santa Cruz","url":url,"land_m2":number(surface),
              "registry":registry,"auction_number":int(auction) if auction else None,
              "court":court,"auction_date":date,"raw_text":text}
        if usd: item.update(price=number(usd),currency="USD")
        elif bob: item.update(price=number(bob),currency="BOB")
        out.append(enrich_currency(item,rate))
    return out
