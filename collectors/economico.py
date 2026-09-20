"""Banco Económico Bolivia - archivo público de avisos de remate.

La página pública conserva avisos históricos. Radar guarda Santa Cruz sin
confundir "segundo aviso" con "segundo remate/audiencia".
Los PDFs quedan enlazados para revisión; no se eluden controles técnicos.
"""
import re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .common import number, enrich_currency

BASE="https://www.baneco.com.bo"
URL=BASE+"/avisos_de_remate"

def _event(title):
    t=title.upper()
    notice=None; auction=None
    if re.search(r"SEGUND[OA]\s+AVISO|2DO\.?\s+AVISO",t): notice=2
    elif re.search(r"PRIMER\s+AVISO|1ER\s+AVISO",t): notice=1
    # Audiencia/remate sí representa etapa; aviso no.
    if re.search(r"TERCER\s+REMATE|TERCERA\s+AUDIENCIA|3ER\.?\s+REMATE",t): auction=3
    elif re.search(r"SEGUND[OA]\s+(?:AUDIENCIA|AUD)|SEGUNDO\s+REMATE|2DO\.?\s+REMATE",t): auction=2
    elif re.search(r"PRIMER[AO]?\s+(?:AUDIENCIA|REMATE)|1ER\.?\s+(?:AUDIENCIA|REMATE)",t): auction=1
    return notice,auction

def collect(rate=7.0):
    r=requests.get(URL,timeout=25,headers={"User-Agent":"RadarSCZ-personal/0.1"})
    r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser"); out=[]; seen=set()
    # Filas de tabla: Dpto | aviso | archivo | galería | publicación.
    for tr in soup.select("tr"):
        cells=tr.find_all(["td","th"])
        txt=[" ".join(c.stripped_strings) for c in cells]
        if not txt or txt[0].strip().lower()!="santa cruz": continue
        title=txt[1] if len(txt)>1 else "Aviso de remate Banco Económico"
        links=[urljoin(BASE,a.get("href")) for a in tr.select("a[href]")]
        file_url=next((u for u in links if ".pdf" in u.lower()),links[0] if links else URL)
        published=next((x for x in reversed(txt) if re.fullmatch(r"\d{4}-\d{2}-\d{2}",x)),None)
        sid=file_url.rstrip("/").split("/")[-1] if file_url!=URL else f"{published}-{title}"
        if sid in seen: continue
        seen.add(sid); notice,auction=_event(title)
        out.append(enrich_currency({
            "source":"banco_economico","source_id":sid,"kind":"remate","title":title,
            "url":file_url,"municipality":"Santa Cruz","auction_number":auction,
            "auction_date":published,"raw_text":f"numero_aviso={notice or ''}; publicación={published or ''}; {title}"
        },rate))
    return out
