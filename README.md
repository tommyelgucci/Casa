# 🏠 Radar SCZ

Aplicación personal para detectar terrenos, casas y remates potencialmente interesantes en Santa Cruz de la Sierra, Urubó, Porongo y Warnes.

## MVP v0.1
- Clasificados EL DEBER
- Remates BCP Santa Cruz
- SQLite local e historial de precios
- Filtros en `config.yaml`
- Presupuesto principal, banda negociable y excepciones desde 400 m²
- Interfaz Streamlit

> Radar SCZ no determina que una propiedad sea jurídicamente segura. Un precio atractivo debe verificarse con Folio Real/DDRR, gravámenes, impuestos, ocupación, porcentaje del derecho rematado y demás documentación.

## Ejecutar
Necesitas Python 3.11 o superior.

~~~bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
~~~

La base `data/radar.db` se crea automáticamente.

## Configuración
Edita `config.yaml`. El tipo de cambio es configurable y sólo se usa para conversión/comparación; se conserva la moneda original.

## Recolectores
Los recolectores consultan páginas públicas y no incluyen técnicas para evadir CAPTCHA, bloqueos, autenticación, límites o controles de acceso. Si una fuente falla, las demás continúan.

## Fuentes actuales
Radar incluye colectores para Clasificados EL DEBER, BCP Remates, Banco Ganadero, SIN, Banco Económico e InfoCasas (experimental). La pestaña 📡 Cobertura indica cuáles están aportando registros.

## Arranque fácil
- macOS/Linux: `bash run_radar.sh`
- Windows: doble clic en `run_radar.bat` o ejecútalo desde Terminal.

Los lanzadores crean `.venv`, instalan dependencias y abren Streamlit. Los scrapers se ejecutan desde Radar al pulsar **Actualizar fuentes**, no mediante GitHub Actions.

## Prioridad actual
Validar cobertura real de cada fuente y ampliar el mercado normal. Las alertas quedan pospuestas.
