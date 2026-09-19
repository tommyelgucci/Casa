import re

def number(text):
    if text is None: return None
    s=re.sub(r"[^0-9,.-]","",str(text)).strip()
    if not s: return None
    if "," in s and "." in s:
        s=s.replace(".","").replace(",",".")
    elif "," in s: s=s.replace(",",".")
    try: return float(s)
    except ValueError: return None

def enrich_currency(item, rate):
    p=item.get("price"); cur=(item.get("currency") or "").upper()
    if p is None: return item
    if cur=="USD": item["price_usd"]=p; item["price_bob"]=p*rate
    elif cur in ("BOB","BS"): item["price_bob"]=p; item["price_usd"]=p/rate
    if item.get("land_m2") and item.get("price_usd"):
        item["price_per_m2_usd"]=item["price_usd"]/item["land_m2"]
    return item
