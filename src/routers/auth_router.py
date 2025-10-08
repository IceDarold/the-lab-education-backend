from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user_service import UserService
from src.schemas import UserCreate, UserResponse, Token
from src.dependencies import get_db, get_current_user
from src.core.security import create_access_token
from src.db.session import get_supabase_client

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    supabase = get_supabase_client()
    try:
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        if auth_response.user:
            user = await UserService.create_user_with_id(str(auth_response.user.id), user_data, db)
            access_token = create_access_token(data={"sub": user.email})
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Registration failed due to an internal error")

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user