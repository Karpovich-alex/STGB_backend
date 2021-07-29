from datetime import timedelta
from typing import Optional

import uvicorn
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

import utils.validator as v
from STGB_backend.auth import get_password_hash, authenticate_user, create_access_token, get_current_active_user, Token, \
    credentials_exception, ACCESS_TOKEN_EXPIRE_MINUTES
from database import WebUser


class User(BaseModel):
    id: Optional[int]
    username: str
    full_name: Optional[str] = None


class RegistryUser(User):
    password: str


class UserInDB(User):
    hashed_password: str

    @classmethod
    def create(cls, user: RegistryUser):
        user_dict = user.dict(include={'username', 'full_name'})
        user_dict["hashed_password"] = get_password_hash(user.password)
        new_user = cls(**user_dict)
        return new_user


router = APIRouter()


def login_user(username, password):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    token = login_user(form_data.username, form_data.password)
    return token


@router.get("/me", response_model=v.WebUser)
async def read_user_info(current_user: WebUser = Depends(get_current_active_user)):
    return current_user.to_base()


# @router.get("/users/me/items/", response_model=v.WebUser)
# async def read_own_items(current_user: v.WebUser = Depends(get_current_active_user)):
#     return [{"item_id": "Foo", "owner": current_user.username}]


@router.post("/register", response_model=Token)
async def register(new_user: RegistryUser):
    user = WebUser.create_user(new_user)
    if not user:
        raise credentials_exception

    # return login_user(user.username, new_user.password)
    return status.HTTP_200_OK


if __name__ == '__main__':
    from fastapi import FastAPI

    app = FastAPI()
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8000)
