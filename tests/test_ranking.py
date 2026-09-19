import yaml
from pathlib import Path
from analysis.ranking import comparable_median, opportunity_score
CFG=yaml.safe_load((Path(__file__).parents[1]/"config.yaml").read_text(encoding="utf-8"))

def test_requires_five_comparables():
    target={"id":1,"kind":"terreno","zone":"porongo","land_m2":500,"price_usd":15000,"price_per_m2_usd":30}
    others=[{"id":i+2,"kind":"terreno","zone":"porongo","land_m2":500,"price_per_m2_usd":40} for i in range(4)]
    med,n=comparable_median(target,others,5)
    assert med is None and n==4

def test_median_with_five_comparables():
    target={"id":1,"kind":"terreno","zone":"porongo","land_m2":500,"price_usd":15000,"price_per_m2_usd":30}
    vals=[35,40,45,50,100]
    others=[{"id":i+2,"kind":"terreno","zone":"porongo","land_m2":500,"price_per_m2_usd":v} for i,v in enumerate(vals)]
    med,n=comparable_median(target,others,5)
    assert med==45 and n==5
    score=opportunity_score(target,CFG,others)
    assert 0<=score["total"]<=100
