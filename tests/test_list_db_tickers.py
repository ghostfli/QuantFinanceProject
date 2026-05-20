from list_db_tickers import format_table


class DummyRow:
    def __init__(self, data):
        self._data = data

    def keys(self):
        return list(self._data.keys())

    def __getitem__(self, item):
        return self._data[item]


def test_format_table_outputs_headers_and_rows(capsys):
    rows = [
        DummyRow({"ticker": "AAPL", "status": "ok"}),
        DummyRow({"ticker": "MSFT", "status": "failed"}),
    ]

    format_table(rows)
    captured = capsys.readouterr()

    assert "ticker" in captured.out
    assert "status" in captured.out
    assert "AAPL" in captured.out
    assert "MSFT" in captured.out
