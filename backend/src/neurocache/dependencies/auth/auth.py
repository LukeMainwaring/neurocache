"""Auth0 JWT authentication dependency."""

import logging
from typing import Annotated, Any, cast

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from neurocache.core.config import get_settings

logger = logging.getLogger(__name__)

config = get_settings()

_bearer_scheme = HTTPBearer(auto_error=False)


class VerifyToken:
    """Token verification and user info retrieval using PyJWT and Auth0."""

    def __init__(self) -> None:
        self.jwks_client = jwt.PyJWKClient(config.auth0_jwks_url)
        self.user_info_url = f"https://{config.AUTH0_DOMAIN}/userinfo"

    async def verify(
        self,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> dict[str, Any]:
        """Decode and validate a JWT against Auth0's JWKS."""
        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(credentials.credentials).key
        except jwt.exceptions.PyJWKClientError as e:
            raise HTTPException(status_code=401, detail=str(e))

        try:
            payload: dict[str, Any] = jwt.decode(
                credentials.credentials,
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

    async def get_user_info(
        self,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    ) -> dict[str, Any]:
        """Fetch user info from Auth0's /userinfo endpoint."""
        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.user_info_url,
                    headers={"Authorization": f"Bearer {credentials.credentials}"},
                )
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise HTTPException(status_code=401, detail="Invalid response from Auth0")
                return cast(dict[str, Any], result)
        except httpx.HTTPStatusError as e:
            logger.warning(f"Auth0 /userinfo failed: {e.response.status_code}")
            raise HTTPException(status_code=401, detail="Failed to fetch user info from Auth0")
        except httpx.RequestError as e:
            logger.error(f"Auth0 /userinfo request error: {e}")
            raise HTTPException(status_code=502, detail="Unable to reach Auth0")


_verify_token = VerifyToken()


def _extract_user_id(sub: str) -> str:
    """Strip provider prefix from Auth0 sub claim (e.g. 'google-oauth2|12345' -> '12345')."""
    return sub.split("|")[1] if "|" in sub else sub


async def get_current_user_id(
    payload: dict[str, Any] = Depends(_verify_token.verify),
) -> str:
    """Extract user ID from verified JWT payload."""
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
    return _extract_user_id(str(sub))


async def get_current_user_email(
    user_info: dict[str, Any] = Depends(_verify_token.get_user_info),
) -> str:
    """Extract email from Auth0 /userinfo endpoint."""
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Unable to get email from user info")
    return str(email)


# Convenience alias used across all routes
authenticated_user = get_current_user_id

AuthenticatedUser = Annotated[str, Depends(authenticated_user)]
