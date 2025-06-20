import os
from openai import OpenAI
from fastapi import HTTPException, Depends
from jose import jwt, JWTError

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET", "insecure_dev_secret")

client = OpenAI(api_key=OPENAI_API_KEY)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, NEXTAUTH_SECRET, algorithms=["HS256"])
        return payload
    except JWTError as e:
        print("JWT validation error:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token") 