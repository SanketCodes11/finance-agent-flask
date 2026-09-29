import pytest
from app.services.finance_service import get_stock_history

def test_stock_history_ohlcv_format():
    # Fetch AAPL 1mo history
    data = get_stock_history("AAPL", "1mo")
    
    assert "labels" in data
    assert "timestamps" in data
    assert "open" in data
    assert "high" in data
    assert "low" in data
    assert "close" in data
    assert "volume" in data
    assert "prices" in data
    
    # Assert data aligns in length
    length = len(data["labels"])
    assert length > 0
    assert len(data["timestamps"]) == length
    assert len(data["open"]) == length
    assert len(data["high"]) == length
    assert len(data["low"]) == length
    assert len(data["close"]) == length
    assert len(data["volume"]) == length

def test_stock_history_invalid_period():
    # Should fallback to 1mo
    data = get_stock_history("AAPL", "invalid_period_string")
    assert len(data["labels"]) > 0

def test_stock_history_indian_symbol():
    # Test NSE symbol as requested
    data = get_stock_history("TCS.NS", "1mo")
    assert "timestamps" in data
    assert len(data["labels"]) > 0


def test_stock_history_timestamps_ascending_and_unique():
    data = get_stock_history("AAPL", "1mo")
    timestamps = data["timestamps"]
    
    # Check for strictly ascending
    is_ascending = all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1))
    assert is_ascending, "Timestamps are not strictly ascending"
    
    # Check for unique
    assert len(timestamps) == len(set(timestamps)), "Duplicate timestamps found"

def test_stock_history_no_nans():
    data = get_stock_history("AAPL", "1mo")
    
    import math
    for key in ["open", "high", "low", "close", "volume"]:
        has_nan = any(math.isnan(val) for val in data[key])
        assert not has_nan, f"NaN value found in {key}"

def test_stock_history_api_failure_invalid_symbol():
    with pytest.raises(ValueError):
        get_stock_history("INVALID_SYMBOL_THAT_DOES_NOT_EXIST", "1mo")
