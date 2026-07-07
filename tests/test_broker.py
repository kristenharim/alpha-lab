"""FakeBroker contract tests. Two must-pass (green = the brick is done):
moves-toward-targets and skips-non-tradable. The third pins the exit contract."""
from core.broker.base import FakeBroker


def test_fakebroker_moves_toward_targets():
    b = FakeBroker(prices={"AAPL": 100.0})
    b.submit_targets({"AAPL": 5000.0})          # want $5k of AAPL
    assert b.positions()["AAPL"]["qty"] == 50    # 5000 / 100
    assert b.positions()["AAPL"]["side"] == "long"
    assert b.fills()[-1]["ticker"] == "AAPL"


def test_fakebroker_skips_nontradable():
    # the decision-relevant test: a delisted name must NOT fill
    b = FakeBroker(prices={"XYZ": 20.0})
    b.set_status("XYZ", "delisted")
    b.submit_targets({"XYZ": 2000.0})
    assert "XYZ" not in b.positions()
    assert b.fills() == []


def test_fakebroker_exits_held_name_absent_from_targets():
    # held name dropped from the target book -> treated as target 0 -> closed
    b = FakeBroker(prices={"AAPL": 100.0})
    b.submit_targets({"AAPL": 5000.0})
    b.fills()                                    # drain
    b.submit_targets({})                         # empty book = flatten everything
    assert "AAPL" not in b.positions()
    assert b.fills()[-1]["side"] == "sell"
