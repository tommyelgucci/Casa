import yaml
from pathlib import Path
from analysis.filters import classify

CFG=yaml.safe_load((Path(__file__).parents[1]/"config.yaml").read_text(encoding="utf-8"))

def item(area,usd=None,bob=None):
    return {"land_m2":area,"price_usd":usd,"price_bob":bob}

def test_principal_500m2_under_usd_cap():
    assert classify(item(500,19999),CFG)=="principal"

def test_exception_400_to_499():
    assert classify(item(450,18000),CFG)=="excepcion"

def test_negotiable_band():
    assert classify(item(600,24000),CFG)=="negociable"

def test_below_exception_is_out():
    assert classify(item(399,10000),CFG)=="fuera"

def test_bob_cap_is_independent():
    assert classify(item(500,None,199999),CFG)=="principal"
