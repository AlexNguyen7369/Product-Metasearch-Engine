#!/usr/bin/env python3
"""
Local end-to-end smoke test for the Docker Compose stack — not a unit
test, not part of any test suite.

Every other e2e script in this folder (test_search_e2e.py, test_mcp_e2e.py)
runs the app's own Python code directly, against a Redis reached however
the caller has one set up. This script instead runs `docker-compose.yml`
itself: builds the `api` image from the Dockerfile, brings up `api` +
`redis` together, and hits the real HTTP API through the container
network — the same `docker-compose up` a fresh clone of this repo is
documented (stack.md, app_structure.md) to be run with, which as of
writing has never actually been executed and verified.

Specifically this proves container-to-container networking works, not
just the application logic: REDIS_URL=redis://redis:6379/0 (from
.env.example) only resolves inside the Compose network's DNS — a Redis
reached at redis://localhost:6379/0 during local testing doesn't exercise
that at all.

Tears the stack down (`docker compose down`) afterward, including on
failure, so it doesn't leave containers running.

This makes one real, billable SerpAPI call. Run manually, not in CI.

Usage:
    python scripts/test_docker_compose_e2e.py ["search query"]

Requires:
  - Docker running, with either the `docker compose` v2 plugin or the
    standalone `docker-compose` v1 binary on PATH.
  - SERPAPI_API_KEY set in .env at the repo root — docker-compose.yml
    loads it into the api container via `env_file: .env`.
  - Ports 8000 and 6379 free on the host (docker-compose.yml publishes
    both).
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "http://localhost:8000"
DEFAULT_QUERY = "wireless mouse"


def compose_command() -> list[str] | None:
    """Prefer the `docker compose` v2 plugin; fall back to v1's standalone binary."""
    try:
        if subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0:
            return ["docker", "compose"]
    except FileNotFoundError:
        pass
    try:
        if subprocess.run(["docker-compose", "version"], capture_output=True).returncode == 0:
            return ["docker-compose"]
    except FileNotFoundError:
        pass
    return None


def has_serpapi_key() -> bool:
    """Presence check only — never reads/prints the key's value."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return False
    for line in env_path.read_text().splitlines():
        if line.strip().startswith("SERPAPI_API_KEY="):
            return bool(line.split("=", 1)[1].strip())
    return False


def run(compose: list[str], *args: str, **kwargs) -> subprocess.CompletedProcess:
    cmd = [*compose, *args]
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT, **kwargs)


def wait_for_api(timeout: float = 90.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{BASE_URL}/", timeout=2.0).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(1.0)
    return False


def main(query: str) -> int:
    print("== Product Metasearch Engine — Docker Compose e2e test ==\n")

    compose = compose_command()
    if compose is None:
        print("FAIL: neither `docker compose` (v2) nor `docker-compose` (v1) found on PATH.")
        return 1
    print(f"Using: {' '.join(compose)}")

    if not has_serpapi_key():
        print("FAIL: SERPAPI_API_KEY is missing or empty in .env — the api container will "
              "start but every search will fail.")
        return 1

    print("\nBuilding and starting the stack (up --build -d)...")
    result = run(compose, "up", "--build", "-d")
    if result.returncode != 0:
        print("FAIL: `compose up` exited non-zero.")
        return 1

    try:
        print("\nWaiting for the api container to become reachable...")
        if not wait_for_api():
            print(f"FAIL: {BASE_URL}/ did not respond within the timeout.")
            print("--- api logs ---")
            run(compose, "logs", "api")
            return 1
        print("OK: api container is up.\n")

        print("Checking the frontend is served from the container...")
        r = httpx.get(f"{BASE_URL}/", timeout=5.0)
        if r.status_code != 200 or "Product Metasearch Engine" not in r.text:
            print(f"FAIL: unexpected response serving the frontend: {r.status_code}")
            return 1
        print("OK: frontend served correctly.\n")

        print(f"Calling /api/search?q={query!r} (expect a real SerpAPI call, cache miss)...")
        r = httpx.get(f"{BASE_URL}/api/search", params={"q": query}, timeout=20.0)
        if r.status_code != 200:
            print(f"FAIL: /api/search returned {r.status_code}: {r.text}")
            return 1
        first = r.json()
        if first["cached"]:
            print("FAIL: first call reported cached=True unexpectedly.")
            return 1
        if not first["results"]:
            print(f"FAIL: live search returned zero results: {first}")
            return 1
        sample = first["results"][0]
        print(f"OK: {first['total']} result(s), cached=False")
        print(f"    sample: {sample['title']!r} — {sample['currency']} {sample['price']} from {sample['source']}\n")

        print("Calling the same search again (expect a cache hit via the redis container)...")
        r = httpx.get(f"{BASE_URL}/api/search", params={"q": query}, timeout=10.0)
        if r.status_code != 200:
            print(f"FAIL: /api/search returned {r.status_code}: {r.text}")
            return 1
        second = r.json()
        if not second["cached"]:
            print("FAIL: second call reported cached=False — container-to-container Redis "
                  "(REDIS_URL=redis://redis:6379/0) isn't resolving/connecting.")
            return 1
        print("OK: cached=True — api container reached the redis container by its service "
              "name, confirming Compose's container-to-container DNS actually works.\n")

        print("All checks passed: docker-compose builds and runs the full stack correctly.")
        return 0
    finally:
        print("\nTearing down (compose down)...")
        run(compose, "down", "--remove-orphans")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    sys.exit(main(q))
