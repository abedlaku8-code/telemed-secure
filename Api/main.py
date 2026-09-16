import os
import secrets
import time
import pyotp

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from Api.rbac import a_permission
from Api.consentement import consentement_valide


# Chargement du fichier .env
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
DEMO_EMAIL = os.getenv("DEMO_EMAIL")
DEMO_PASSWORD_HASH = os.getenv("DEMO_PASSWORD_HASH")
TOTP_SECRET = os.getenv("TOTP_SECRET")

ALGORITHM = "HS256"

# Durée maximale d'un défi MFA : 5 minutes
DUREE_CHALLENGE = 300

# Stockage temporaire des défis MFA
defis_mfa = {}


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


def verifier_role(role: str, permission: str):
    """Vérifie qu'un rôle possède une permission."""
    if not a_permission(role, permission):
        raise HTTPException(
            status_code=403,
            detail="Accès interdit : permission insuffisante"
        )


class LoginRequest(BaseModel):
    username: str
    password: str


class MFARequest(BaseModel):
    mfa_challenge: str
    code: str


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

    # Vérification du mot de passe
    if not pwd_context.verify(
        data.password,
        DEMO_PASSWORD_HASH
    ):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    # Création d'un défi temporaire MFA
    mfa_challenge = secrets.token_urlsafe(32)

    defis_mfa[mfa_challenge] = {
        "email": DEMO_EMAIL,
        "date_creation": time.time()
    }

    return {
        "message": "Première étape réussie",
        "mfa_requis": True,
        "mfa_challenge": mfa_challenge
    }


@application.post("/mfa/authenticator")
def verifier_authenticator(data: MFARequest):

    # Vérification du défi MFA
    defi = defis_mfa.get(data.mfa_challenge)

    if not defi:
        raise HTTPException(
            status_code=401,
            detail="Session MFA invalide ou expirée"
        )

    # Vérification de l'expiration
    if time.time() - defi["date_creation"] > DUREE_CHALLENGE:
        del defis_mfa[data.mfa_challenge]

        raise HTTPException(
            status_code=401,
            detail="Session MFA expirée"
        )

    # Vérification du code Authenticator
    totp = pyotp.TOTP(TOTP_SECRET)

    if not totp.verify(data.code):
        raise HTTPException(
            status_code=401,
            detail="Code Authenticator incorrect ou expiré"
        )

    # Création du JWT uniquement après la deuxième étape
    token = jwt.encode(
        {
            "sub": DEMO_EMAIL,
            "role": "admin"
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    # Suppression du défi MFA après utilisation
    del defis_mfa[data.mfa_challenge]

    return {
        "message": "Authentification MFA réussie",
        "acces": "autorisé",
        "access_token": token,
        "token_type": "bearer"
    }


@application.get("/admin")
def espace_admin():

    role = "admin"

    verifier_role(
        role,
        "gerer_utilisateurs"
    )

    return {
        "message": "Accès autorisé",
        "role": role,
        "permission": "gerer_utilisateurs"
    }


@application.get("/medecin/admin")
def acces_medecin_admin():

    role = "medecin"

    verifier_role(
        role,
        "gerer_utilisateurs"
    )

    return {
        "message": "Accès autorisé",
        "role": role
    }


@application.post("/consentement/{patient_id}/{medecin_id}")
def donner_consentement_route(
    patient_id: str,
    medecin_id: str
):

    from Api.consentement import donner_consentement

    return donner_consentement(
        patient_id,
        medecin_id
    )


@application.get("/consentement/{patient_id}/{medecin_id}")
def verifier_consentement_route(
    patient_id: str,
    medecin_id: str
):

    consentement = consentement_valide(
        patient_id,
        medecin_id
    )

    return {
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "consentement_valide": consentement
    }


@application.delete("/consentement/{patient_id}/{medecin_id}")
def retirer_consentement_route(
    patient_id: str,
    medecin_id: str
):

    from Api.consentement import retirer_consentement

    return retirer_consentement(
        patient_id,
        medecin_id
    )


@application.get("/dossiers/{patient_id}/{medecin_id}")
def acces_dossier(
    patient_id: str,
    medecin_id: str
):

    role = "medecin"

    # Vérification du rôle
    verifier_role(
        role,
        "voir_dossiers"
    )

    # Vérification du consentement
    if not consentement_valide(
        patient_id,
        medecin_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Accès refusé : consentement du patient absent"
        )

    return {
        "message": "Accès au dossier autorisé",
        "patient_id": patient_id,
        "medecin_id": medecin_id
    }