import jwt

from rest_framework.exceptions import AuthenticationFailed

import os

PUBLIC_KEY = os.getenv("TOROB_PUBLIC_KEY")


def validate_token(token: str, expected_aud: str):
    if not token:
        raise AuthenticationFailed("Torob token is missing")

    try:
        payload = jwt.decode(
            token,
            key=PUBLIC_KEY,
            algorithms=["EdDSA"],
            audience=expected_aud,
            options={
                "require": ["exp", "nbf", "aud"],
            },
        )
        return payload

    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid or expired Torob token")