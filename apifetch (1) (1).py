"""
apifetch.py — Async CLI tool: multiple public APIs se concurrently data fetch
Usage:
    python apifetch.py
    python apifetch.py --concurrency 2
Install:
    pip install httpx
"""

import argparse
import asyncio
import time
from typing import TypedDict

import httpx


# ---------- Type Hints: har API ka response shape define kiya ----------
class CatFact(TypedDict):
    fact: str
    length: int


class Joke(TypedDict):
    setup: str
    punchline: str
    id: int


# ---------- Config ----------
URLS: dict[str, str] = {
    "catfact_1": "https://catfact.ninja/fact",
    "joke_1": "https://official-joke-api.appspot.com/random_joke",
    "catfact_2": "https://catfact.ninja/fact",
    "joke_2": "https://official-joke-api.appspot.com/random_joke",
    "catfact_3": "https://catfact.ninja/fact",
}

API_TIMEOUT: float = 10.0


# ---------- Core logic ----------
async def fetch_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    name: str,
    url: str,
) -> dict:
    """Ek URL fetch karo. Semaphore limit lagaata hai, fail hone pe graceful result."""
    async with sem:  # max N concurrent requests — rate limiting!
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data: dict = resp.json()
            print(f"  ✅ {name}: fetched")
            return {"name": name, "ok": True, "data": data}
        except httpx.HTTPError as e:
            print(f"  ❌ {name}: failed -> {e}")
            return {"name": name, "ok": False, "data": None}


async def run(concurrency: int) -> None:
    sem = asyncio.Semaphore(concurrency)  # 🔥 concurrency limit — sirf N saath mein
    t = time.perf_counter()

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        tasks = [fetch_one(client, sem, name, url) for name, url in URLS.items()]
        results: list[dict] = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - t
    ok = sum(1 for r in results if r["ok"])
    print(f"\n{'='*50}")
    print(f"📊 {ok}/{len(results)} succeeded in {elapsed:.2f}s")
    for r in results:
        if r["ok"]:
            print(f"  • {r['name']}: {r['data']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async multi-API fetcher")
    parser.add_argument("--concurrency", type=int, default=3,
                        help="Max simultaneous requests (default: 3)")
    args = parser.parse_args()
    asyncio.run(run(args.concurrency))
