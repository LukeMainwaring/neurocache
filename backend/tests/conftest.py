"""Shared test fixtures for neurocache tests.

Sets dummy environment variables so that modules requiring database config
(e.g., DocumentChunk → get_settings()) can be imported without a running database.
"""

import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
