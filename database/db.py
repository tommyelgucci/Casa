import sqlite3
from pathlib import Path
from datetime import datetime, timezone
DB_PATH=Path(__file__).resolve().parents[1]/"data"/"radar.db"
def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True); con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row; return con
def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS items (
          id INTEGER PRIMARY KEY, source TEXT NOT NULL, source_id TEXT, kind TEXT NOT NULL,
          title TEXT, url TEXT NOT NULL, zone TEXT, municipality TEXT, land_m2 REAL, built_m2 REAL,
          price REAL, currency TEXT, price_usd REAL, price_bob REAL, price_per_m2_usd REAL,
          registry TEXT, cadastral_code TEXT, auction_number INTEGER, ownership_percent REAL,
          court TEXT, auction_date TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
          raw_text TEXT, UNIQUE(source,url));
        CREATE TABLE IF NOT EXISTS user_marks (
          item_id INTEGER PRIMARY KEY, favorite INTEGER NOT NULL DEFAULT 0,
          watching INTEGER NOT NULL DEFAULT 0, notes TEXT,
          updated_at TEXT NOT NULL, FOREIGN KEY(item_id) REFERENCES items(id));
        CREATE TABLE IF NOT EXISTS verification_checks (
          id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, check_type TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'desconocido', notes TEXT, checked_at TEXT,
          UNIQUE(item_id,check_type), FOREIGN KEY(item_id) REFERENCES items(id));
        CREATE TABLE IF NOT EXISTS price_history (
          id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, observed_at TEXT NOT NULL,
          price REAL, currency TEXT, price_usd REAL, price_bob REAL,
          FOREIGN KEY(item_id) REFERENCES items(id));
        """)
        # Migración suave para bases creadas con v0.1 inicial.
        existing={r["name"] for r in con.execute("PRAGMA table_info(price_history)")}
        for name in ("price_usd","price_bob"):
            if name not in existing: con.execute(f"ALTER TABLE price_history ADD COLUMN {name} REAL")
def _history(con,item_id,now,item):
    con.execute("INSERT INTO price_history(item_id,observed_at,price,currency,price_usd,price_bob) VALUES(?,?,?,?,?,?)",
                (item_id,now,item.get("price"),item.get("currency"),item.get("price_usd"),item.get("price_bob")))
def upsert(item):
    now=datetime.now(timezone.utc).isoformat()
    with connect() as con:
        old=con.execute("SELECT id,price,currency FROM items WHERE source=? AND url=?",(item["source"],item["url"])).fetchone()
        cols=["source","source_id","kind","title","url","zone","municipality","land_m2","built_m2","price","currency","price_usd","price_bob","price_per_m2_usd","registry","cadastral_code","auction_number","ownership_percent","court","auction_date","raw_text"]
        vals=[item.get(c) for c in cols]
        changed=False; created=False
        if old:
            sets=",".join(f"{c}=?" for c in cols[1:])
            con.execute(f"UPDATE items SET {sets},last_seen=? WHERE id=?",vals[1:]+[now,old["id"]]); item_id=old["id"]
            changed=old["price"]!=item.get("price") or old["currency"]!=item.get("currency")
            if changed: _history(con,item_id,now,item)
        else:
            qs=",".join("?" for _ in cols)
            cur=con.execute(f"INSERT INTO items({','.join(cols)},first_seen,last_seen) VALUES({qs},?,?)",vals+[now,now])
            item_id=cur.lastrowid; created=True; _history(con,item_id,now,item)
        return {"id":item_id,"created":created,"price_changed":changed}
def all_items():
    with connect() as con: return [dict(r) for r in con.execute("SELECT * FROM items ORDER BY last_seen DESC")]
def price_history(item_id):
    with connect() as con: return [dict(r) for r in con.execute("SELECT * FROM price_history WHERE item_id=? ORDER BY observed_at",(item_id,))]
def first_price(item_id):
    h=price_history(item_id); return h[0] if h else None

def auction_history(registry):
    """Eventos conocidos de una misma matrícula, sin asumir etapas faltantes."""
    if not registry: return []
    with connect() as con:
        rows=con.execute("""SELECT id,source,source_id,title,url,registry,auction_number,
          price,currency,price_usd,price_bob,auction_date,court,ownership_percent,first_seen
          FROM items WHERE kind IN ('remate','adjudicacion') AND registry=?
          ORDER BY COALESCE(auction_number,0), COALESCE(auction_date,first_seen)""",(registry,)).fetchall()
        return [dict(r) for r in rows]


VERIFICATION_TYPES=["folio_real","gravamenes","impuestos_municipales","ocupacion","litigios_adicionales","propiedad_100","plano_catastro","visita_fisica"]

def verification_checks(item_id):
    with connect() as con:
        existing={r["check_type"]:dict(r) for r in con.execute("SELECT * FROM verification_checks WHERE item_id=?",(item_id,))}
    return [{"check_type":t,"status":existing.get(t,{}).get("status","desconocido"),"notes":existing.get(t,{}).get("notes")} for t in VERIFICATION_TYPES]

def save_verification(item_id,check_type,status,notes=""):
    if check_type not in VERIFICATION_TYPES: raise ValueError("Tipo de verificación desconocido")
    if status not in ("desconocido","pendiente","verificado","alerta"): raise ValueError("Estado inválido")
    now=datetime.now(timezone.utc).isoformat()
    with connect() as con:
        con.execute("""INSERT INTO verification_checks(item_id,check_type,status,notes,checked_at)
        VALUES(?,?,?,?,?) ON CONFLICT(item_id,check_type) DO UPDATE SET
        status=excluded.status,notes=excluded.notes,checked_at=excluded.checked_at""",(item_id,check_type,status,notes,now))

def verification_status(item_id):
    states=[x["status"] for x in verification_checks(item_id)]
    if "alerta" in states: return "alerta"
    verified=sum(s=="verificado" for s in states)
    return "verificado" if verified==len(states) else "parcial" if verified else "desconocido"


def get_mark(item_id):
    with connect() as con:
        r=con.execute("SELECT * FROM user_marks WHERE item_id=?",(item_id,)).fetchone()
    return dict(r) if r else {"item_id":item_id,"favorite":0,"watching":0,"notes":""}

def save_mark(item_id,favorite=False,watching=False,notes=""):
    now=datetime.now(timezone.utc).isoformat()
    with connect() as con:
        con.execute("""INSERT INTO user_marks(item_id,favorite,watching,notes,updated_at)
        VALUES(?,?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET
        favorite=excluded.favorite,watching=excluded.watching,notes=excluded.notes,updated_at=excluded.updated_at""",
        (item_id,int(bool(favorite)),int(bool(watching)),notes,now))

def marked_items(mode="favorite"):
    column="favorite" if mode=="favorite" else "watching"
    with connect() as con:
        return [dict(r) for r in con.execute(f"""SELECT i.*,m.favorite,m.watching,m.notes
        FROM items i JOIN user_marks m ON i.id=m.item_id WHERE m.{column}=1 ORDER BY m.updated_at DESC""")]
