import os
import pyotp

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel


# Chargement du fichier .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DEMO_EMAIL = os.getenv("DEMO_EMAIL")
DEMO_PASSWORD_HASH = os.getenv("DEMO_PASSWORD_HASH")
TOTP_SECRET = os.getenv("TOTP_SECRET")

ALGORITHM = "HS256"


if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY absente du fichier .env")

if not DEMO_EMAIL:
    raise RuntimeError("DEMO_EMAIL absente du fichier .env")

if not DEMO_PASSWORD_HASH:
    raise RuntimeError("DEMO_PASSWORD_HASH absent du fichier .env")

if not TOTP_SECRET:
    raise RuntimeError("TOTP_SECRET absente du fichier .env")


application = FastAPI(title="Telemed Secure API")


# Gestion sécurisée des mots de passe
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class LoginRequest(BaseModel):
    username: str
    password: str
    otp: str


@application.get("/")
def accueil():
    return {
        "message": "API Telemed Secure",
        "statut": "API opérationnelle"
    }


@application.post("/login")
def login(data: LoginRequest):

    # Vérification de l'adresse email
    if data.username != DEMO_EMAIL:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    # Vérification du mot de passe avec le hash
    if not pwd_context.verify(data.password, DEMO_PASSWORD_HASH):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )
    # Vérification du code OTP
    totp = pyotp.TOTP(TOTP_SECRET)

    if not totp.verify(data.otp):
        raise HTTPException(
            status_code=401,
            detail="Code OTP incorrect ou expiré"
        )
    # Création du JWT
    token = jwt.encode(
        {
            "sub": DEMO_EMAIL,
            "role": "admin"
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "message": "Authentification réussie",
        "acces": "autorisé",
        "access_token": token,
        "token_type": "bearer"
    }