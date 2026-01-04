from typing import Annotated

from fastapi import Depends

from app.auth.service import oauth2_scheme, verify_token


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return verify_token(token)


CheckAuth = Depends(get_current_user)
