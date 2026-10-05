import sys
from pathlib import Path
import io
import urllib.error

# Allow Python to find resources/webhealth.py
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "resources")
)

import webhealth  # type: ignore


# Fake website response
class FakeResponse:
    def __init__(self, data=b"Hello"):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# Helper: stop tests from sending real data to CloudWatch
def mock_cloudwatch(monkeypatch):
    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )


# 1. Website success -> availability = 1
def test_availability_success(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse()
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["availability"] == 1


# 2. Response size is correct
def test_response_size(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"12345")
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["response_size"] == 5


# 3. Latency is calculated
def test_latency(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    times = [10, 10.5]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse()
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["latency"] == 0.5


# 4. Correct website is returned
def test_website_name(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse()
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["website"] == "https://example.com"


# 5. CloudWatch receives 3 metrics
def test_three_metrics_sent(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse()
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    calls = []

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: calls.append(args)
    )

    webhealth.lambda_handler({}, None)

    assert len(calls) == 3


# 6. All websites are checked
def test_all_websites(monkeypatch):
    webhealth.constants.WEBSITES = [
        "https://site1.com",
        "https://site2.com",
        "https://site3.com"
    ]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse()
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert len(result) == 3


# 7. HTTP error -> availability = 0
def test_http_error(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    error = urllib.error.HTTPError(
        "https://example.com",
        403,
        "Forbidden",
        None,
        io.BytesIO(b"error")
    )

    def raise_error(request, timeout):
        raise error

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        raise_error
    )

    times = [10, 10.2]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["availability"] == 0


# 8. HTTP error response size is recorded
def test_http_error_size(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    error = urllib.error.HTTPError(
        "https://example.com",
        403,
        "Forbidden",
        None,
        io.BytesIO(b"error")
    )

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(error)
    )

    times = [10, 10.2]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["response_size"] == 5


# 9. General error -> response size = 0
def test_general_error(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    def raise_error(request, timeout):
        raise Exception("Connection error")

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        raise_error
    )

    times = [10, 10.1]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    mock_cloudwatch(monkeypatch)

    result = webhealth.lambda_handler({}, None)

    assert result[0]["response_size"] == 0


# 10. Request uses timeout = 10
def test_timeout(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    saved_timeout = []

    def fake_urlopen(request, timeout):
        saved_timeout.append(timeout)
        return FakeResponse()

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        fake_urlopen
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    mock_cloudwatch(monkeypatch)

    webhealth.lambda_handler({}, None)

    assert saved_timeout[0] == 10