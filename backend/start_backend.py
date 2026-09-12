import json
import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from main import app


HOST = "127.0.0.1"
PREFERRED_PORT = 8000
FALLBACK_PORTS = range(8001, 8011)


def privacyguard_url(port):
    return f"http://{HOST}:{port}"


def is_privacyguard_running(port):
    """Return True only when an existing PrivacyGuard instance answers on this port."""
    try:
        with urllib.request.urlopen(
            f"{privacyguard_url(port)}/api/health",
            timeout=0.8,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return (
                payload.get("status") == "online"
                and "PrivacyGuard" in payload.get("message", "")
            )
    except Exception:
        return False


def port_is_available(port):
    """Check whether the loopback port can be bound locally."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((HOST, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def choose_port():
    # If PrivacyGuard is already running, reuse it instead of starting a duplicate.
    if is_privacyguard_running(PREFERRED_PORT):
        return PREFERRED_PORT, True

    if port_is_available(PREFERRED_PORT):
        return PREFERRED_PORT, False

    for port in FALLBACK_PORTS:
        if is_privacyguard_running(port):
            return port, True
        if port_is_available(port):
            return port, False

    raise RuntimeError(
        "PrivacyGuard could not find an available local port between 8000 and 8010."
    )


def open_privacyguard(port):
    # Give Uvicorn a moment to start before opening the browser.
    time.sleep(1.5)
    webbrowser.open(privacyguard_url(port))


if __name__ == "__main__":
    port, already_running = choose_port()
    url = privacyguard_url(port)

    if already_running:
        print("PrivacyGuard is already running.")
        print(f"Opening {url}")
        webbrowser.open(url)
    else:
        print("=" * 50)
        print(" PrivacyGuard")
        print(" Local Security Engine")
        print(f" {url}")
        print("=" * 50)

        browser_thread = threading.Thread(
            target=open_privacyguard,
            args=(port,),
            daemon=True,
        )
        browser_thread.start()

        uvicorn.run(
            app,
            host=HOST,
            port=port,
            log_level="info",
        )
