import re

file_path = 'tests/test_charting_pytest.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''
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
'''

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content + new_tests)
