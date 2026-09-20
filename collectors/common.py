import re

def number(text):
    """Convierte formatos habituales de Bolivia/LatAm sin confundir miles con decimales."""
    if text is None:
        return None
    s=re.sub(r"[^0-9,.-]","",str(text)).strip()
    if not s:
        return None
    neg=s.startswith("-")
    s=s.lstrip("-")
    if "," in s and "." in s:
        # El separador que aparece más a la derecha se considera decimal.
        if s.rfind(",") > s.rfind("."):
            s=s.replace(".","").replace(",",".")
        else:
            s=s.replace(",","")
    elif "," in s:
        tail=s.rsplit(",",1)[1]
        s=s.replace(",",".") if len(tail) in (1,2) else s.replace(",","")
    elif "." in s:
        tail=s.rsplit(".",1)[1]
        # 55.000 / 200.000 son miles; 6.50 puede ser decimal.
        if len(tail)==3:
            s=s.replace(".","")
    try:
        value=float(s)
        return -value if neg else value
    except ValueError:
        return None

def enrich_currency(item, rate):
    p=item.get("price"); cur=(item.get("currency") or "").upper()
    if p is None: return item
    if not rate or rate<=0: return item
    if cur=="USD": item["price_usd"]=p; item["price_bob"]=p*rate
    elif cur in ("BOB","BS"): item["price_bob"]=p; item["price_usd"]=p/rate
    if item.get("land_m2") and item.get("price_usd"):
        item["price_per_m2_usd"]=item["price_usd"]/item["land_m2"]
    return item
