"""Compatibilidad de despliegue.

La interfaz activa de Radar SCZ vive en webapp.py.
Este archivo conserva el nombre app.py para plataformas que autodetectan Flask.
"""
from webapp import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)
