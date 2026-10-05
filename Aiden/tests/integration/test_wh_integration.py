import sys
from pathlib import Path

# Allow Python to find files in resources/
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "resources")
)

import webhealth  # type: ignore
import CWdata  # type: ignore


class FakeResponse:
    def __init__(self, data=b"Hello"):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class FakeCloudWatch:
    def __init__(self):
        self.calls = []

    def put_metric_data(self, **kwargs):
        self.calls.append(kwargs)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


# 1. WebHealth sends 3 metrics through CWdata
def test_webhealth_sends_metrics_to_cloudwatch(monkeypatch):
    webhealth.constants.WEBSITES = [
        "https://example.com"
    ]

    # Fake website response
    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"Hello")
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    # Fake AWS CloudWatch
    fake_cloudwatch = FakeCloudWatch()

    monkeypatch.setattr(
        CWdata.boto3,
        "client",
        lambda service: fake_cloudwatch
    )

    result = webhealth.lambda_handler({}, None)

    # 1 website should send:
    # Availability + Latency + ResponseSize
    assert len(fake_cloudwatch.calls) == 3

    assert result[0]["availability"] == 1
    assert result[0]["response_size"] == 5


# 2. Multiple websites send metrics through CWdata
def test_multiple_websites_send_all_metrics(monkeypatch):
    webhealth.constants.WEBSITES = [
        "https://site1.com",
        "https://site2.com"
    ]

    monkeypatch.setattr(
        webhealth.urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse(b"Hello")
    )

    monkeypatch.setattr(
        webhealth.time,
        "perf_counter",
        lambda: 1
    )

    fake_cloudwatch = FakeCloudWatch()

    monkeypatch.setattr(
        CWdata.boto3,
        "client",
        lambda service: fake_cloudwatch
    )

    result = webhealth.lambda_handler({}, None)

    # 2 websites x 3 metrics = 6 CloudWatch calls
    assert len(fake_cloudwatch.calls) == 6

    assert len(result) == 2
    assert result[0]["website"] == "https://site1.com"
    assert result[1]["website"] == "https://site2.com"