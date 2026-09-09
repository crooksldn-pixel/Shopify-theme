"""A small shop that always says the same thing.

The dataset is in `data.py` and is deliberately readable: five customers, seven orders, a
catalogue of three garments and an inbox that correlates with them. `shopify.py` and `gmail.py`
answer the real clients' real requests from it, so a fixture turn runs the production query
shaping, the production presenters and the production tablet renderer.
"""

from experience.fixtures.data import World, world
from experience.fixtures.gmail import fixture_gmail
from experience.fixtures.shopify import FixtureShopify

__all__ = ["World", "world", "fixture_gmail", "FixtureShopify"]
