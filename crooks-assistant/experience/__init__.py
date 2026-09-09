"""The experience layer: what a turn looks like from the tablet's side, and how that is tested.

Nothing in here is imported by the running assistant. It holds the golden fixture world, the
harness that drives real turns through the real runtime, and the reports that come out. The
seam it uses — `shopify_tools.bind(store)`, `gmail_tools.bind(client)` — is the same one the
unit tests use and the same one the runtime uses in production: a fixture run swaps the client
at the boundary and every line of application code above it is the code that ships.
"""
