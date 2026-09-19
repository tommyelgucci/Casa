import yaml
from pathlib import Path
from database import db
from analysis.events import events_for
CFG=yaml.safe_load((Path(__file__).parents[1]/"config.yaml").read_text(encoding="utf-8"))

def test_price_drop_enters_budget(tmp_path,monkeypatch):
    monkeypatch.setattr(db,"DB_PATH",tmp_path/"events.db")
    import analysis.events as ev
    monkeypatch.setattr(ev,"price_history",db.price_history)
    monkeypatch.setattr(ev,"all_items",db.all_items)
    db.init_db()
    x={"source":"test","source_id":"x","kind":"terreno","title":"T","url":"https://example.test/x",
       "land_m2":550,"price":24000,"currency":"USD","price_usd":24000,"price_bob":168000}
    r=db.upsert(x); x["price"]=19000; x["price_usd"]=19000; x["price_bob"]=133000; db.upsert(x)
    item=[i for i in db.all_items() if i["id"]==r["id"]][0]
    texts=[e["text"] for e in events_for(item,CFG)]
    assert any("Bajó" in t for t in texts)
    assert any("entrar en tu presupuesto" in t for t in texts)
