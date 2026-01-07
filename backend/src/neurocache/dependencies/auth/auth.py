"""Simple authentication for demo purposes."""

from typing import Annotated

from fastapi import Depends

# Hardcoded demo user ID
DEMO_USER_ID = "110771214372945994893"


async def authenticated_user() -> str:
    """Return the demo user ID. Replace with real auth when needed."""
    return DEMO_USER_ID


AuthenticatedUser = Annotated[str, Depends(authenticated_user)]
