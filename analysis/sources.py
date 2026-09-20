"""Registro de cobertura de Radar SCZ.

Distingue fuentes automáticas de fuentes que, por condiciones/acceso técnico,
se mantienen manuales. El objetivo es que una fuente no desaparezca
silenciosamente del radar.
"""
SOURCES=[
 {"id":"eldeber","name":"Clasificados EL DEBER","group":"mercado","mode":"automatico","enabled":True},
 {"id":"bcp","name":"BCP Remates","group":"remates","mode":"automatico","enabled":True},
 {"id":"banco_ganadero","name":"Banco Ganadero","group":"remates","mode":"automatico","enabled":True},
 {"id":"sin","name":"SIN Subastas","group":"remates","mode":"automatico","enabled":True},
 {"id":"banco_economico","name":"Banco Económico","group":"remates","mode":"automatico","enabled":True},
 {"id":"infocasas","name":"InfoCasas Bolivia","group":"mercado","mode":"automático conservador/experimental","enabled":True},
 {"id":"ultracasas","name":"UltraCasas","group":"mercado","mode":"manual/pendiente","enabled":False},
 {"id":"remax","name":"RE/MAX Bolivia","group":"mercado","mode":"manual/pendiente","enabled":False},
 {"id":"facebook","name":"Facebook Marketplace","group":"mercado","mode":"manual","enabled":False},
 {"id":"thor","name":"THOR / Órgano Judicial","group":"remates","mode":"pendiente integración","enabled":False},
]

def coverage(rows):
    result=[]
    for s in SOURCES:
        found=sum(1 for x in rows if x.get("source")==s["id"])
        result.append({**s,"registros":found})
    return result
