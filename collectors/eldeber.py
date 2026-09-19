"""MVP conservador: descubre anuncios públicos de inmuebles en EL DEBER.
No evade CAPTCHA, 403/429 ni otras restricciones técnicas.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency
BASE="https://clasificados.eldeber.com.bo"
URL=BASE+"/category/inmuebles"

def _parse_text(text):
    low=text.lower(); item={}
    m=re.search(r"(\d[\d.,]*)\s*m(?:2|²)",text,re.I)
    if m: item["land_m2"]=number(m.group(1))
    money=re.search(r"(?:usd|us\$|\$)\s*([\d.,]+)|([\d.,]+)\s*(?:usd|d[oó]lares)",text,re.I)
    bs=re.search(r"(?:bs\.?|bob)\s*([\d.,]+)|([\d.,]+)\s*(?:bs\.?|bob)",text,re.I)
    if money:
        item["price"]=number(next(x for x in money.groups() if x)); item["currency"]="USD"
    elif bs:
        item["price"]=number(next(x for x in bs.groups() if x)); item["currency"]="BOB"
    item["kind"]="casa" if "casa" in low else "terreno"
    return item

def collect(rate=7.0):
    r=requests.get(URL,timeout=20,headers={"User-Agent":"RadarSCZ-personal/0.1"})
    r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser"); out=[]; seen=set()
    for a in soup.select("a[href]"):
        href=a.get("href","")
        if not re.search(r"/(?:node/)?\d+",href): continue
        url=urljoin(BASE,href)
        if url in seen: continue
        seen.add(url); text=" ".join(a.parent.stripped_strings) if a.parent else a.get_text(" ",strip=True)
        if not text: continue
        item={"source":"eldeber","source_id":re.findall(r"\d+",href)[-1],"title":a.get_text(" ",strip=True)[:250],"url":url,"raw_text":text}
        item.update(_parse_text(text)); out.append(enrich_currency(item,rate))
    return out
