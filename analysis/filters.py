def classify(item,cfg):
    b=cfg["busqueda"]; area=item.get("land_m2") or 0
    usd=item.get("price_usd"); bob=item.get("price_bob")
    principal=area>=b["superficie_objetivo_min_m2"] and ((usd is not None and usd<=b["precio_max_usd"]) or (bob is not None and bob<=b["precio_max_bob"]))
    exception=area>=b["superficie_excepcion_min_m2"] and ((usd is not None and usd<=b["precio_max_usd"]) or (bob is not None and bob<=b["precio_max_bob"]))
    negotiable=area>=b["superficie_excepcion_min_m2"] and ((usd is not None and usd<=b["precio_negociable_usd"]) or (bob is not None and bob<=b["precio_negociable_bob"]))
    return "principal" if principal else "excepcion" if exception else "negociable" if negotiable else "fuera"
