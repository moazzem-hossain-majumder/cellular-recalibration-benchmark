from scripts.select_positive_offers import upper


def test_positive_offer_evidence_floor():
    assert upper(0,0,.05)==1
    assert upper(5,5,.05)==1
    assert upper(0,28,.05)>.1>=upper(0,29,.05)
    assert upper(0,45,.05/6)>.1>=upper(0,46,.05/6)
