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
