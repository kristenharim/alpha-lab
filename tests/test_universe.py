import pandas as pd
import pytest
from core.data.universe import clean_ticker, extract_symbols


def test_clean_ticker():
    assert clean_ticker("BRK.B") == "BRK-B"
    assert clean_ticker(" aapl ") == "AAPL"
    assert clean_ticker("BF.B") == "BF-B"


def test_extract_symbols_finds_symbol_and_sector():
    tables = [
        pd.DataFrame({"Foo": [1, 2]}),  # decoy table, no symbol column
        pd.DataFrame({"Symbol": ["AAPL", "BRK.B"],
                      "Security": ["Apple", "Berkshire"],
                      "GICS Sector": ["Tech", "Financials"]}),
    ]
    out = extract_symbols(tables)
    assert list(out["ticker"]) == ["AAPL", "BRK-B"]
    assert list(out["sector"]) == ["Tech", "Financials"]


def test_extract_symbols_handles_ticker_column_name():
    tables = [pd.DataFrame({"Ticker symbol": ["MSFT"], "Company": ["Microsoft"]})]
    out = extract_symbols(tables)
    assert list(out["ticker"]) == ["MSFT"]
    assert list(out["sector"]) == ["Unknown"]


def test_extract_symbols_raises_when_no_symbol():
    with pytest.raises(ValueError):
        extract_symbols([pd.DataFrame({"Foo": [1], "Bar": [2]})])
