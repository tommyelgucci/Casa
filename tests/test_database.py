from database import db

def test_price_history_and_marks(tmp_path,monkeypatch):
    monkeypatch.setattr(db,"DB_PATH",tmp_path/"test.db")
    db.init_db()
    x={"source":"test","source_id":"1","kind":"terreno","title":"Prueba","url":"https://example.test/1",
       "land_m2":500,"price":24000,"currency":"USD","price_usd":24000,"price_bob":168000}
    first=db.upsert(x)
    assert first["created"] is True
    x["price"]=19000; x["price_usd"]=19000; x["price_bob"]=133000
    second=db.upsert(x)
    assert second["price_changed"] is True
    assert len(db.price_history(first["id"]))==2
    db.save_mark(first["id"],True,True,"vigilar")
    mark=db.get_mark(first["id"])
    assert mark["favorite"]==1 and mark["watching"]==1

def test_verification_and_auction_history(tmp_path,monkeypatch):
    monkeypatch.setattr(db,"DB_PATH",tmp_path/"test2.db")
    db.init_db()
    base={"source":"test","kind":"remate","title":"R","land_m2":600,"registry":"7.01.1.99.TEST",
          "price":200000,"currency":"BOB","price_bob":200000,"price_usd":28571}
    for n in (1,2,3):
        x=dict(base,url=f"https://example.test/r{n}",source_id=str(n),auction_number=n,price=200000-(n-1)*30000)
        db.upsert(x)
    hist=db.auction_history("7.01.1.99.TEST")
    assert [x["auction_number"] for x in hist]==[1,2,3]
    db.save_verification(hist[-1]["id"],"folio_real","verificado","prueba")
    assert db.verification_status(hist[-1]["id"])=="parcial"
