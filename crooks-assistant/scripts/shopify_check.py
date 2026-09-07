#!/usr/bin/env python3
"""M6's success test: mint a token, read the shop, and prove the second call reuses the cache."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.shopify import ShopifyAuthError, ShopifyClient, ShopifyError  # noqa: E402
from config.settings import get_settings  # noqa: E402


async def main() -> int:
    settings = get_settings()
    client = ShopifyClient(
        settings.shopify_shop_domain,
        settings.shopify_api_version,
        auth_mode=settings.shopify_auth_mode,
    )
    print(f"shop domain : {settings.shopify_shop_domain}")
    print(f"api version : {settings.shopify_api_version}")
    print(f"auth mode   : {settings.shopify_auth_mode}\n")

    try:
        shop = await client.shop()
    except ShopifyAuthError as exc:
        print(f"AUTH FAILED\n\n{exc}\n")
        return 1
    except ShopifyError as exc:
        print(f"QUERY FAILED: {exc}")
        return 1

    print(f"name        : {shop['name']}")
    print(f"timezone    : {shop['ianaTimezone']}   (expect Europe/London)")
    print(f"currency    : {shop['currencyCode']}")
    print(f"plan        : {(shop.get('plan') or {}).get('publicDisplayName')}")
    print(f"expires_in  : {client.token_expires_in}   (expect 86399)")
    print(f"token calls : {client.token_requests}")

    from app.tools import shopify_tools

    shopify_tools.bind(client)
    recent = await shopify_tools.shopify_list_orders(days=7, limit=1)
    print(f"\nlocal day starts (UTC): {recent['since']}")
    if recent["orders"]:
        order = recent["orders"][0]
        print(f"most recent order     : {order['order_number']} · {order['placed_at']} · {order['total']}")
    else:
        print("most recent order     : none in the last 7 days")

    print("\n— second run, ten seconds later —")
    await asyncio.sleep(10)
    before = client.token_requests
    await client.shop(refresh=True)
    after = client.token_requests
    if after == before:
        print(f"token calls : {after} (unchanged) — the cache is working. M6 PASSES.")
        return 0
    print(f"token calls : {after} (was {before}) — a token was re-requested. The cache is not wired.")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
