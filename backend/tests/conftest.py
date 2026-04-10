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

# OpenAIResponsesModel constructs its provider client eagerly at module import
# time. Any test that imports chat_agent — directly or transitively — would
# otherwise fail at collection. Tests that actually invoke the model should use
# agent.override with TestModel; this dummy value never reaches a real API call.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-deterministic-no-real-calls")
