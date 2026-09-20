import streamlit as st, yaml, pandas as pd
from pathlib import Path
from database.db import init_db, upsert, all_items, price_history, auction_history, verification_checks, save_verification, verification_status, get_mark, save_mark
from collectors.eldeber import collect as collect_eldeber
from collectors.bcp import collect as collect_bcp
from collectors.ganadero import collect as collect_ganadero
from collectors.sin import collect as collect_sin
from collectors.economico import collect as collect_economico
from analysis.filters import classify
from analysis.events import events_for
from analysis.ranking import opportunity_score

ROOT=Path(__file__).parent
cfg=yaml.safe_load((ROOT/"config.yaml").read_text(encoding="utf-8"))
init_db()
st.set_page_config(page_title="Radar SCZ",page_icon="🏠",layout="wide")

def money(x):
    if x.get("currency")=="USD" and x.get("price") is not None: return f"$us {x['price']:,.2f}"
    if x.get("currency")=="BOB" and x.get("price") is not None: return f"Bs {x['price']:,.2f}"
    return "Precio no detectado"

def area(x):
    return f"{x['land_m2']:,.2f} m²" if x.get("land_m2") else "Superficie no detectada"

def card(x, auction=False):
    cat=x.get("categoria","fuera")
    labels={"principal":"🔥 CUMPLE","excepcion":"⚡ EXCEPCIÓN 400–499 m²","negociable":"👀 NEGOCIABLE","fuera":"📌 FUERA DE CRITERIO"}
    with st.container(border=True):
        score=opportunity_score(x,cfg,rows)
        st.markdown(f"### 🎯 Opportunity Score: {score['total']}/100")
        with st.expander("¿Cómo se calculó?"):
            st.write("Este puntaje mide ajuste económico a tus criterios; no mide seguridad jurídica.")
            st.json(score["parts"])
            if score["median_ppm"]:
                st.write(f"Mediana comparable: $us {score['median_ppm']:.2f}/m² · {score['comparables']} comparables")
                st.write(f"Diferencia frente a mediana: {score['discount_pct']:+.1f}%")
            else:
                st.write(f"Referencia de zona: datos insuficientes ({score['comparables']} comparables; se requieren {cfg['analisis_mercado']['comparables_minimos']}).")
        for event in events_for(x,cfg):
            st.markdown(f"**{event['text']}**")
        a,b,c=st.columns([5,2,2])
        with a:
            st.subheader(x.get("title") or ("Remate BCP" if auction else "Propiedad"))
            st.caption(f"{labels.get(cat,cat)} · Fuente: {x.get('source','').upper()}")
        with b:
            st.metric("Precio",money(x))
        with c:
            st.metric("Terreno",area(x))
        cols=st.columns(4)
        cols[0].metric("USD/m²",f"{x['price_per_m2_usd']:.2f}" if x.get("price_per_m2_usd") else "—")
        cols[1].metric("Zona",x.get("zone") or "Por revisar")
        if auction:
            cols[2].metric("N.º remate",x.get("auction_number") or "—")
            cols[3].metric("Matrícula",x.get("registry") or "—")
            if x.get("court"): st.caption(f"⚖️ Juzgado: {x['court']}")
            if x.get("auction_date"): st.caption(f"📅 {x['auction_date']}")
            history=auction_history(x.get("registry"))
            if len(history)>1:
                st.markdown("#### 🔨 Historial conocido de esta matrícula")
                first_usd=next((h.get("price_usd") for h in history if h.get("price_usd")),None)
                for h in history:
                    n=f"Remate {h['auction_number']}" if h.get("auction_number") else "Evento"
                    p=(f"$us {h['price_usd']:,.2f}" if h.get("price_usd") else
                       f"Bs {h['price_bob']:,.2f}" if h.get("price_bob") else "precio no detectado")
                    delta=""
                    if first_usd and h.get("price_usd") and h["price_usd"]!=first_usd:
                        delta=f" · {(h['price_usd']-first_usd)/first_usd*100:+.1f}% vs. primer evento conocido"
                    st.write(f"**{n}** · {p}{delta} · {h.get('auction_date') or 'fecha por revisar'}")
                st.caption("Sólo se muestran eventos encontrados. Radar no supone que exista un remate intermedio ni predice futuras rebajas.")
        else:
            cols[2].metric("Categoría",cat.title())
            cols[3].metric("Detectado",str(x.get("first_seen",""))[:10] or "—")
        hist=price_history(x["id"])
        if len(hist)>1:
            first=hist[0].get("price_usd"); last=hist[-1].get("price_usd")
            if first and last and first!=last:
                pct=(last-first)/first*100
                st.markdown(f"📉 **Historial:** $us {first:,.2f} → $us {last:,.2f} ({pct:+.1f}%)")
                with st.expander("Ver historial de precios"):
                    hd=pd.DataFrame(hist)
                    st.dataframe(hd[[c for c in ["observed_at","price","currency","price_usd","price_bob"] if c in hd.columns]],hide_index=True,use_container_width=True)
        if auction:
            status=verification_status(x["id"])
            icons={"desconocido":"⚪","parcial":"🟡","verificado":"🟢","alerta":"🔴"}
            st.markdown(f"**Verificación jurídica:** {icons.get(status,'⚪')} {status.title()}")
            names={"folio_real":"Folio Real actual","gravamenes":"Gravámenes / hipotecas / embargos","impuestos_municipales":"Impuestos municipales","ocupacion":"Ocupación / posesión","litigios_adicionales":"Litigios adicionales","propiedad_100":"Se vende 100% del derecho","plano_catastro":"Plano / catastro","visita_fisica":"Visita física"}
            with st.expander("📑 Checklist de verificación"):
                for check in verification_checks(x["id"]):
                    key=check["check_type"]; current=check["status"]
                    options=["desconocido","pendiente","verificado","alerta"]
                    choice=st.selectbox(names[key],options,index=options.index(current),key=f"v_{x['id']}_{key}")
                    note=st.text_input("Nota",value=check.get("notes") or "",key=f"n_{x['id']}_{key}",label_visibility="collapsed",placeholder=f"Nota sobre {names[key]}")
                    if choice!=current or note!=(check.get("notes") or ""):
                        if st.button(f"Guardar {names[key]}",key=f"s_{x['id']}_{key}"):
                            save_verification(x["id"],key,choice,note); st.rerun()
            st.caption("Este checklist registra comprobaciones; no certifica por sí mismo la situación jurídica del inmueble.")
        mark=get_mark(x["id"])
        with st.expander("❤️ Guardar / 👀 Vigilar"):
            fav=st.checkbox("❤️ Guardado",value=bool(mark["favorite"]),key=f"fav_{x['id']}")
            watch=st.checkbox("👀 Vigilar cambios de precio",value=bool(mark["watching"]),key=f"watch_{x['id']}")
            note=st.text_input("Nota personal",value=mark.get("notes") or "",key=f"marknote_{x['id']}")
            if st.button("Guardar selección",key=f"marksave_{x['id']}"):
                save_mark(x["id"],fav,watch,note); st.success("Guardado.")
        if x.get("url"): st.link_button("Abrir fuente original ↗",x["url"])

st.title("🏠 Radar SCZ")
st.caption("Terrenos, casas y remates · Santa Cruz · Urubó · Porongo · Warnes")
top1,top2,top3,top4=st.columns(4)
rows=all_items()
for x in rows: x["categoria"]=classify(x,cfg)
top1.metric("🔥 Cumplen",sum(x["categoria"]=="principal" for x in rows))
top2.metric("⚡ Excepciones",sum(x["categoria"]=="excepcion" for x in rows))
top3.metric("👀 Negociables",sum(x["categoria"]=="negociable" for x in rows))
top4.metric("🔨 Remates",sum(x["kind"] in ("remate","adjudicacion") for x in rows))

if st.button("🔄 Actualizar fuentes",type="primary",use_container_width=True):
    rate=float(cfg["moneda"]["usd_bob"]); total=0; new_count=0; changed_count=0
    with st.status("Consultando fuentes públicas…",expanded=True):
        for name,collector in [("EL DEBER",collect_eldeber),("BCP Remates",collect_bcp),("Banco Ganadero",collect_ganadero),("SIN",collect_sin),("Banco Económico",collect_economico)]:
            try:
                found=collector(rate)
                for item in found:\n                    event=upsert(item); new_count+=int(event["created"]); changed_count+=int(event["price_changed"])
                total+=len(found); st.write(f"✓ {name}: {len(found)} registros procesados")
            except Exception as e:
                st.warning(f"{name}: no se pudo actualizar. Las demás fuentes continúan. ({e})")
    st.success(f"Actualización terminada: {total} procesados · {new_count} nuevos · {changed_count} cambios de precio.")
    st.rerun()

tabs=st.tabs(["🔥 Cumple","⚡ Excepciones","👀 Negociables","🔨 Remates","❤️ Guardados","👀 Vigilar","📋 Todo","⚙️ Configuración"])
with tabs[0]:
    data=[x for x in rows if x["categoria"]=="principal" and x["kind"]!="remate"]
    if data:
        for x in sorted(data,key=lambda z:z.get("price_per_m2_usd") or 1e18): card(x)
    else: st.info("Todavía no hay anuncios normales que cumplan superficie y presupuesto.")
with tabs[1]:
    data=[x for x in rows if x["categoria"]=="excepcion" and x["kind"]!="remate"]
    if data:
        for x in sorted(data,key=lambda z:z.get("price_per_m2_usd") or 1e18): card(x)
    else: st.info("Aquí aparecerán propiedades de 400–499 m² que entren en el presupuesto.")
with tabs[2]:
    data=[x for x in rows if x["categoria"]=="negociable" and x["kind"]!="remate"]
    if data:
        for x in sorted(data,key=lambda z:z.get("price_per_m2_usd") or 1e18): card(x)
    else: st.info("Aquí aparecerán propiedades cercanas al presupuesto para vigilar o negociar.")
with tabs[3]:
    data=[x for x in rows if x["kind"] in ("remate","adjudicacion")]
    if data:
        for x in sorted(data,key=lambda z:(-(z.get("auction_number") or 0),z.get("price_usd") or 1e18)): card(x,True)
    else: st.info("Pulsa Actualizar fuentes para consultar BCP Remates.")
with tabs[4]:
    data=[x for x in rows if get_mark(x["id"])["favorite"]]
    if data:
        for x in data: card(x,x["kind"]=="remate")
    else: st.info("Marca ❤️ Guardado en cualquier tarjeta para verla aquí.")
with tabs[5]:
    data=[x for x in rows if get_mark(x["id"])["watching"]]
    if data:
        for x in data: card(x,x["kind"]=="remate")
    else: st.info("Marca 👀 Vigilar para seguir futuras bajadas de precio.")
with tabs[6]:
    if rows:
        cols=["source","kind","title","land_m2","built_m2","price","currency","price_usd","price_per_m2_usd","zone","registry","auction_number","categoria","url"]
        df=pd.DataFrame(rows)
        st.dataframe(df[[c for c in cols if c in df.columns]],use_container_width=True,hide_index=True,
                     column_config={"url":st.column_config.LinkColumn("Fuente")})
    else: st.info("La base está vacía. Pulsa Actualizar fuentes.")
with tabs[7]:
    st.markdown("### Tus reglas actuales")
    b=cfg["busqueda"]
    st.write(f"**Objetivo:** ≥ {b['superficie_objetivo_min_m2']} m² · hasta $us {b['precio_max_usd']:,} o Bs {b['precio_max_bob']:,}")
    st.write(f"**Excepción:** desde {b['superficie_excepcion_min_m2']} m²")
    st.write(f"**Negociable:** hasta $us {b['precio_negociable_usd']:,} o Bs {b['precio_negociable_bob']:,}")
    st.write(f"**Cambio configurable:** 1 USD = {cfg['moneda']['usd_bob']} Bs")
    with st.expander("Ver config.yaml"):
        st.code((ROOT/"config.yaml").read_text(encoding="utf-8"),language="yaml")
    st.caption("El tipo de cambio es una preferencia configurable, no una cotización automática.")
