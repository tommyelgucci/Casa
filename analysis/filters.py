from datetime import datetime, timezone

AUCTION_KINDS={"remate","adjudicacion"}

def _iso_age_days(value):
    if not value:
        return None
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        if dt.tzinfo is None:
            dt=dt.replace(tzinfo=timezone.utc)
        return max(0,(datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).days)
    except (ValueError,TypeError):
        return None

def is_current(item,cfg):
    """Anuncios normales: máximo 90 días desde publicación fiable o primera detección.
    Remates/adjudicaciones conservan historial y no caducan por esta regla.
    """
    if item.get("kind") in AUCTION_KINDS:
        return True
    max_days=cfg["busqueda"].get("antiguedad_max_dias",90)
    # publication_date sólo se usa cuando el colector realmente la obtuvo.
    age=_iso_age_days(item.get("publication_date") or item.get("first_seen"))
    return age is None or age<=max_days

def classify(item,cfg):
    if not is_current(item,cfg):
        return "antiguo"
    b=cfg["busqueda"]; area=item.get("land_m2") or 0
    usd=item.get("price_usd"); bob=item.get("price_bob")
    principal=area>=b["superficie_objetivo_min_m2"] and ((usd is not None and usd<=b["precio_max_usd"]) or (bob is not None and bob<=b["precio_max_bob"]))
    exception=area>=b["superficie_excepcion_min_m2"] and ((usd is not None and usd<=b["precio_max_usd"]) or (bob is not None and bob<=b["precio_max_bob"]))
    negotiable=area>=b["superficie_excepcion_min_m2"] and ((usd is not None and usd<=b["precio_negociable_usd"]) or (bob is not None and bob<=b["precio_negociable_bob"]))
    return "principal" if principal else "excepcion" if exception else "negociable" if negotiable else "fuera"
