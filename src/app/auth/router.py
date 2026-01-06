from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import Token
from app.auth.service import check_refresh_eligibility, create_access_token, oauth2_scheme, verify_token
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if form_data.password != settings.DEVICE_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": "user"})

    context = {"access_token": access_token, "token_type": "bearer", "status": "valid"}
    return Token.model_validate(context)


@router.post("/refresh", response_model=Token)
async def refresh_token(token: Annotated[str, Depends(oauth2_scheme)]):
    new_token = check_refresh_eligibility(token)

    if new_token:
        context = {"access_token": new_token, "token_type": "bearer", "status": "refreshed"}
    else:
        valid_token = verify_token(token)
        context = {"access_token": valid_token, "token_type": "bearer", "status": "valid"}

    return Token.model_validate(context)
