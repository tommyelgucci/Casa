import streamlit as st, yaml, pandas as pd
from pathlib import Path
from database.db import init_db, upsert, all_items
from collectors.eldeber import collect as collect_eldeber
from collectors.bcp import collect as collect_bcp
from analysis.filters import classify

ROOT=Path(__file__).parent
cfg=yaml.safe_load((ROOT/"config.yaml").read_text(encoding="utf-8"))
init_db(); st.set_page_config(page_title="Radar SCZ",page_icon="🏠",layout="wide")
st.title("🏠 Radar SCZ")
st.caption("Buscador personal de oportunidades y remates en Santa Cruz, Bolivia")
if st.button("🔄 Actualizar fuentes",type="primary"):
    rate=float(cfg["moneda"]["usd_bob"]); total=0
    with st.status("Consultando fuentes públicas…"):
        for name,collector in [("EL DEBER",collect_eldeber),("BCP Remates",collect_bcp)]:
            try:
                rows=collector(rate); [upsert(x) for x in rows]; total+=len(rows); st.write(f"✓ {name}: {len(rows)} registros")
            except Exception as e: st.warning(f"{name}: no se pudo actualizar ({e})")
    st.success(f"Actualización terminada: {total} registros procesados.")
rows=all_items()
for x in rows: x["categoria"]=classify(x,cfg)
tabs=st.tabs(["🔥 Oportunidades","🔨 Remates","📋 Todo","⚙️ Configuración"])
with tabs[0]:
    data=[x for x in rows if x["categoria"] in ("principal","excepcion","negociable")]
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True) if data else st.info("Aún no hay oportunidades almacenadas. Pulsa Actualizar fuentes.")
with tabs[1]:
    data=[x for x in rows if x["kind"]=="remate"]
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True) if data else st.info("Aún no hay remates almacenados.")
with tabs[2]:
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True) if rows else st.info("Base vacía.")
with tabs[3]:
    st.code((ROOT/"config.yaml").read_text(encoding="utf-8"),language="yaml")
    st.caption("En v0.1 la configuración se edita en config.yaml.")
