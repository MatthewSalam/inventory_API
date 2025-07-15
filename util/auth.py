from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Annotated
from passlib.context import CryptContext
from model_folder import model
from model_folder.model import Staff

SECRET_KEY = "956d7c6e06bb27e9268b7a1e9e42db8bccc89b04f4738b98cae66778f1a36844"#to generate secretkey, do "./openssl.exe rand -hex 32" after putting the files in your folder
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = APIRouter()
model.Base.metadata.create_all(bind=engine)
bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

dbDepend = Annotated[Session, Depends(get_db)]


# def create_access_token(data: dict, expires_delta: timedelta):
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)

#     data.update({"exp": expire})
#     encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

def create_token(username:str, user_id:int, expires:timedelta) -> str:
    """
    Return a JWT with `sub`, `id`, and `exp` (Unix timestamp, UTC).

    Args:
        email   : User's email → goes in `sub` claim
        user_id : DB id → goes in custom `id` claim
        expires : How long the token should stay valid (timedelta)

    Example:
        token = create_token(
            email="john@example.com",
            user_id=42,
            expires=timedelta(minutes=60)
        )
    """
    now_utc   = datetime.now(timezone.utc)
    exp_utc   = now_utc + expires

    payload = {
        "sub": username,
        "id" : user_id,
        "exp": int(exp_utc.timestamp())   # numeric date per JWT spec
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(db: dbDepend ,token: str = Depends(oauth_bearer)):
    credential_exception = HTTPException(status_code=401, detail="UNAUTHORIZED, credentials could not be validated", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("DEBUG: Token payload did not contain sub")
            raise credential_exception
        user = db.query(Staff).filter(Staff.username == username).first()
        if user is None:
            print ("DEBUG: No user found")
            raise credential_exception
        return user
    
    except JWTError as e:
        print(f"JWT error: {e}")
        raise credential_exception
       
def authenticate_user(username: str, passwordd: str, db: dbDepend):
    sta = db.query(Staff).filter(Staff.username == username).first()
    if not sta:
        return False
    if not bcrypt_context.verify(passwordd, sta.password):
        return False
    

@app.post("/login")
async def login(loginrqst: Annotated[OAuth2PasswordRequestForm, Depends()], db: dbDepend):
    user = loginrqst.username
    user_pas = loginrqst.password
    sta = db.query(Staff).filter(Staff.username == user).first()
    if not sta:
        return "User not found"
    if not bcrypt_context.verify(user_pas, sta.password):
        return "Wrong credentials"
    # staffc = authenticate_user(user, user_pas, db)
    # if not staffc:
    #     raise HTTPException(status_code=401, detail="Validation Error")
    token = create_token(sta.username, sta.id,timedelta(minutes=30))
    return {'access_token':token,'token_type':'bearer'}
