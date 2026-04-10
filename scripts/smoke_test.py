from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple health endpoint smoke test.")
    parser.add_argument("--url", required=True, help="Health URL to test, e.g. http://127.0.0.1:8010/health")
    parser.add_argument("--timeout-seconds", type=int, default=90, help="Total wait time before failing")
    parser.add_argument("--interval-seconds", type=int, default=3, help="Delay between retry attempts")
    return parser.parse_args()


def run_smoke_test(url: str, timeout_seconds: int, interval_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error = "unknown"

    while time.time() < deadline:
        try:
            request = urllib.request.Request(url=url, method="GET")
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = response.read().decode("utf-8", errors="replace")
                if response.status != 200:
                    last_error = f"Unexpected status code: {response.status}"
                else:
                    try:
                        body = json.loads(payload)
                    except json.JSONDecodeError:
                        body = {}

                    if body.get("status") == "ok":
                        print(f"Smoke test passed: {url}")
                        return
                    last_error = f"Health payload did not report ok status: {payload}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)

        print(f"Smoke test retry: {last_error}")
        time.sleep(interval_seconds)

    raise SystemExit(f"Smoke test failed after {timeout_seconds}s. Last error: {last_error}")


def main() -> None:
    args = parse_args()
    run_smoke_test(
        url=args.url,
        timeout_seconds=args.timeout_seconds,
        interval_seconds=args.interval_seconds,
    )


if __name__ == "__main__":
    main()
