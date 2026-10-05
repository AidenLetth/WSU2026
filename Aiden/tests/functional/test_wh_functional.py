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


class FakeResponse:
    def __init__(self, data=b"Hello"):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# 1. Handler returns complete website information
def test_handler_returns_complete_result(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"hello")
    )

    times = [10, 10.5]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )

    result = webhealth.lambda_handler({}, None)

    assert result[0]["website"] == "https://example.com"
    assert result[0]["availability"] == 1
    assert result[0]["latency"] == 0.5
    assert result[0]["response_size"] == 5


# 2. Handler processes multiple websites
def test_handler_processes_multiple_websites(monkeypatch):
    webhealth.constants.WEBSITES = [
        "https://site1.com",
        "https://site2.com"
    ]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"hello")
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )

    result = webhealth.lambda_handler({}, None)

    assert len(result) == 2
    assert result[0]["website"] == "https://site1.com"
    assert result[1]["website"] == "https://site2.com"


# 3. One failed website does not stop the next website
def test_failure_does_not_stop_crawler(monkeypatch):
    webhealth.constants.WEBSITES = [
        "https://bad.com",
        "https://good.com"
    ]

    def fake_urlopen(request, timeout):
        if request.full_url == "https://bad.com":
            raise Exception("Connection failed")

        return FakeResponse(b"good")

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        fake_urlopen
    )

    times = [1, 1.1, 2, 2.2]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )

    result = webhealth.lambda_handler({}, None)

    assert len(result) == 2
    assert result[0]["availability"] == 0
    assert result[1]["availability"] == 1


# 4. HTTP 403 is handled correctly
def test_http_403_is_handled(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    error = urllib.error.HTTPError(
        "https://example.com",
        403,
        "Forbidden",
        None,
        io.BytesIO(b"Forbidden")
    )

    def fake_urlopen(request, timeout):
        raise error

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        fake_urlopen
    )

    times = [1, 1.2]

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: times.pop(0)
    )

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )

    result = webhealth.lambda_handler({}, None)

    assert result[0]["availability"] == 0
    assert result[0]["response_size"] == len(b"Forbidden")


# 5. Three metrics are sent for every website
def test_three_metrics_per_website(monkeypatch):
    webhealth.constants.WEBSITES = [
        "https://site1.com",
        "https://site2.com"
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

    calls = []

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: calls.append(args)
    )

    webhealth.lambda_handler({}, None)

    # 2 websites x 3 metrics
    assert len(calls) == 6


# 6. Correct metric names are sent to CloudWatch
def test_correct_metrics_are_sent(monkeypatch):
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
        lambda namespace, metric, website, value:
            calls.append(metric)
    )

    webhealth.lambda_handler({}, None)

    assert webhealth.constants.metricAvailability in calls
    assert webhealth.constants.metricLatency in calls
    assert webhealth.constants.metricResponseSize in calls


# 7. HTTP request uses WebHealth User-Agent
def test_user_agent_is_used(monkeypatch):
    webhealth.constants.WEBSITES = ["https://example.com"]

    saved_request = []

    def fake_urlopen(request, timeout):
        saved_request.append(request)
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

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )

    webhealth.lambda_handler({}, None)

    assert (
        saved_request[0].get_header("User-agent")
        == "Mozilla/5.0 WebHealthMonitor"
    )


# 8. Returned website order matches configured website order
def test_websites_returned_in_correct_order(monkeypatch):
    websites = [
        "https://first.com",
        "https://second.com",
        "https://third.com"
    ]

    webhealth.constants.WEBSITES = websites

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

    monkeypatch.setattr(
        webhealth.cw,
        "putdatafunction",
        lambda *args: None
    )

    result = webhealth.lambda_handler({}, None)

    returned_websites = [
        item["website"]
        for item in result
    ]

    assert returned_websites == websites