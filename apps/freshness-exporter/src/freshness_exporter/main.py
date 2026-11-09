import logging
import os
import signal
import threading

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY

from .collector import StatusCollector


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    url = os.environ["MONITOR_URL"]
    port = int(os.environ.get("PORT", "9108"))
    timeout = float(os.environ.get("FETCH_TIMEOUT_SECONDS", "5"))
    REGISTRY.register(StatusCollector(url, timeout_s=timeout))
    start_http_server(port, addr="0.0.0.0")
    logging.info("serving metrics on :%d for %s", port, url)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    stop.wait()


if __name__ == "__main__":
    main()
