import logging
import uuid
from enum import Enum
from typing import Annotated, Any, Literal, cast

import httpx
import jwt
import tenacity
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser, UnauthenticatedUser

from neurocache.core.config import get_settings
from neurocache.dependencies.db import AsyncPostgresSessionDep, get_async_sqlalchemy_session
from neurocache.models.user import NoUserFound
from neurocache.models.user import User as UserModel

from .custom_exceptions import (
    UnauthenticatedException,
    UnauthorizedException,
)

CONFIG = get_settings()
logger = logging.getLogger(__name__)


class AuthCredentialScopes(Enum):
    AUTHENTICATED = "authenticated"


class VerifyToken:
    """Token verification using PyJWT"""

    def __init__(self, auto_error: bool = True) -> None:
        self._auto_error = auto_error

        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f"https://{CONFIG.AUTH_DOMAIN}/.well-known/jwks.json"
        self.jwks_client = jwt.PyJWKClient(jwks_url)
        self.user_info_url = f"https://{CONFIG.AUTH_DOMAIN}/userinfo"

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=0.5, min=0.1, max=1),
        retry=tenacity.retry_if_exception_type(jwt.exceptions.DecodeError),
    )
    async def verify(
        self,
        token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    ) -> dict[str, Any]:
        if token is None:
            if self._auto_error:
                raise UnauthenticatedException()
            return {}

        # This gets the 'kid' from the passed token
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token.credentials).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            payload: dict[str, Any] = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=[CONFIG.AUTH_ALGORITHMS],
                audience=CONFIG.AUTH_API_AUDIENCE,
                issuer=CONFIG.AUTH_ISSUER,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))

        return payload

    async def get_user_info(
        self,
        token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    ) -> dict[str, Any]:
        if token is None:
            return {}
        response_json = await _get_auth0_user_info(token.credentials, self.user_info_url)
        if not isinstance(response_json, dict):
            raise UnauthorizedException("Invalid response from Auth0")
        return response_json


class Auth0RateLimitException(Exception):
    """Exception raised when the Auth0 rate limit is exceeded."""


class Auth0BadGatewayException(Exception):
    """Exception raised when Auth0 returns a 502 Bad Gateway error."""


@tenacity.retry(
    stop=tenacity.stop_after_attempt(8),
    wait=tenacity.wait_exponential(multiplier=2, min=1, max=60),
    retry=tenacity.retry_if_exception_type((Auth0RateLimitException, Auth0BadGatewayException)),
)
async def _get_auth0_user_info(
    token_credentials: str,
    user_info_url: str,
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                user_info_url,
                headers={"authorization": f"Bearer {token_credentials}"},
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise Auth0RateLimitException() from e
        if e.response.status_code == 502:
            raise Auth0BadGatewayException() from e
        raise


verify_token = VerifyToken(auto_error=False)


async def get_current_user_id(payload: dict[str, Any] = Depends(verify_token.verify)) -> str:
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Unable to get user ID from token")
    return str(user_id.split("|")[1] if "|" in user_id else user_id)


async def get_current_user_email(
    user_info: dict[str, Any] = Depends(verify_token.get_user_info),
    payload: dict[str, Any] = Depends(verify_token.verify),
) -> str:
    if not user_info or not payload:
        raise UnauthorizedException("Unable to get user email from token")
    return str(user_info["email"])


async def get_user_id_from_token(
    db: AsyncPostgresSessionDep,
    payload: dict[str, Any] = Depends(verify_token.verify),
) -> str | None:
    """Gets the user ID from the token payload."""
    sub = payload.get("sub")
    if sub is None:
        return None
    user_id = str(sub.split("|")[1] if "|" in sub else sub)
    if not await UserModel.exists(db, id=user_id):
        raise UnauthenticatedException()
    return user_id


class CurrentAccessor(BaseUser, BaseModel):
    user_id: str | None = None
    access_key_project_id: uuid.UUID | None = None
    accessor_type: Literal["user"]

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_user(self) -> bool:
        return self.accessor_type == "user"


class AuthBackend(AuthenticationBackend):
    async def authenticate(self, request: Request) -> tuple[AuthCredentials, CurrentAccessor] | None:  # type: ignore[override]
        # get auth header values
        auth = await HTTPBearer(auto_error=False)(request)
        token = await verify_token.verify(auth)

        user_id_from_token: str | None = None

        # get user ID/access key ID values from tokens
        async with get_async_sqlalchemy_session() as db:
            try:
                user_id_from_token = await get_user_id_from_token(db, token)
            except (NoUserFound, UnauthenticatedException):
                pass

        # return the current accessor
        if user_id_from_token:
            return AuthCredentials([AuthCredentialScopes.AUTHENTICATED.value]), CurrentAccessor(
                user_id=user_id_from_token, accessor_type="user"
            )

        # fallback to unauthenticated user
        return None


class AuthenticatedRequest(Request):
    user: CurrentAccessor | UnauthenticatedUser
    auth: AuthCredentials


# async def authenticated_user(
#     request: AuthenticatedRequest,
#     auth_token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
# ) -> str:
#     """
#     Checks that the user is authenticated with a token or API key. Raises an exception otherwise.
#     """
#     if not request.user.is_authenticated:
#         raise UnauthenticatedException()

#     assert isinstance(request.user, CurrentAccessor), "user should be a CurrentAccessor if authenticated"

#     if request.user.is_user:
#         assert request.user.user_id is not None, "user_id should not be None if authenticated as a user"
#         return request.user.user_id

#     raise UnauthenticatedException()


# TODO: add back in proper authentication
async def authenticated_user() -> str:
    return "110771214372945994893"  # luke@cleanlab.ai


AuthenticatedUser = Annotated[str, Depends(authenticated_user)]
