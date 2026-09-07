"""Secret storage.

Deliberately NOT a top-level `secrets/` package, which the build plan specified: a top-level
package of that name shadows the standard library's `secrets` module, and FastAPI imports
`token_hex` from it at startup. The result is an ImportError before a single line of our code
runs. `app.secrets` reads the same and cannot shadow anything.
"""
