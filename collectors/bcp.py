"""Recolector de fichas públicas de Remates BCP Santa Cruz.
Se detiene ante errores HTTP; no evade controles técnicos.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency
BASE="https://www.bcp.com.bo"
URL=BASE+"/BienesAdjudicados/Remates?dep=santa+cruz"

def collect(rate=7.0):
    s=requests.Session(); s.headers.update({"User-Agent":"RadarSCZ-personal/0.1"})
    r=s.get(URL,timeout=20); r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
    links=[]
    for a in soup.select("a[href*='/BienesAdjudicados/Remates/detalle/']"):
        u=urljoin(BASE,a["href"])
        if u not in links: links.append(u)
    out=[]
    for url in links:
        d=s.get(url,timeout=20); d.raise_for_status(); page=BeautifulSoup(d.text,"html.parser")
        text=" ".join(page.stripped_strings)
        def grab(pattern):
            m=re.search(pattern,text,re.I); return m.group(1).strip() if m else None
        surface=grab(r"(?:superficie|sup\.)\s*[:\-]?\s*([\d.,]+)\s*m")
        auction=grab(r"(?:n[uú]mero de remate|remate)\s*[:\-]?\s*(\d+)")
        registry=grab(r"(?:matr[ií]cula)\s*[:\-]?\s*([\d.]+)")
        usd=grab(r"(?:USD|US\$)\s*([\d.,]+)"); bob=grab(r"(?:Bs\.?|BOB)\s*([\d.,]+)")
        item={"source":"bcp","source_id":url.rstrip("/").split("/")[-1],"kind":"remate","title":page.title.get_text(strip=True) if page.title else "Remate BCP","url":url,"land_m2":number(surface),"registry":registry,"auction_number":int(auction) if auction else None,"raw_text":text}
        if usd: item.update(price=number(usd),currency="USD")
        elif bob: item.update(price=number(bob),currency="BOB")
        out.append(enrich_currency(item,rate))
    return out
