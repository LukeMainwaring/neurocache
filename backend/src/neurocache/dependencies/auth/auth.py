"""Auth0 JWT authentication dependency."""

import logging
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from neurocache.core.config import get_settings

logger = logging.getLogger(__name__)

config = get_settings()

_jwks_client = jwt.PyJWKClient(config.auth0_jwks_url)

_bearer_scheme = HTTPBearer(auto_error=False)


def _verify_jwt(token: str) -> dict[str, Any]:
    """Decode and validate a JWT against Auth0's JWKS."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token).key
    except jwt.exceptions.PyJWKClientError as e:
        raise HTTPException(status_code=401, detail=str(e))

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            signing_key,
            algorithms=[config.AUTH0_ALGORITHMS],
            audience=config.AUTH0_API_AUDIENCE,
            issuer=config.auth0_issuer,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload


def _extract_user_id(sub: str) -> str:
    """Strip provider prefix from Auth0 sub claim (e.g. 'google-oauth2|12345' -> '12345')."""
    return sub.split("|")[1] if "|" in sub else sub


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Extract and verify Auth0 JWT, returning the user ID from the 'sub' claim."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    payload = _verify_jwt(credentials.credentials)

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

    return _extract_user_id(str(sub))


async def get_current_user_email(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Extract email from Auth0 JWT claims."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    payload = _verify_jwt(credentials.credentials)

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Token missing 'email' claim")

    return str(email)


# Convenience alias used across all routes
authenticated_user = get_current_user_id

AuthenticatedUser = Annotated[str, Depends(authenticated_user)]
