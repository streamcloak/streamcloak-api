from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.security import check_refresh_eligibility, create_access_token, oauth2_scheme

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

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(token: Annotated[str, Depends(oauth2_scheme)]):
    new_token = check_refresh_eligibility(token)

    if new_token:
        return {"access_token": new_token, "token_type": "bearer", "status": "refreshed"}

    return {"message": "Token is still valid", "status": "valid"}
