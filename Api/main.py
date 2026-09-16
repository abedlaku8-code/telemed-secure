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
from Api.dossiers import creer_dossier, lire_dossier
from Api.audit import enregistrer_action


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DEMO_EMAIL = os.getenv("DEMO_EMAIL")
DEMO_PASSWORD_HASH = os.getenv("DEMO_PASSWORD_HASH")
TOTP_SECRET = os.getenv("TOTP_SECRET")

ALGORITHM = "HS256"
DUREE_CHALLENGE = 300

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


class DossierRequest(BaseModel):
    patient_id: int
    contenu: str


@application.get("/")
def accueil():
    return {
        "message": "API Telemed Secure",
        "statut": "API opérationnelle"
    }


@application.post("/login")
def login(data: LoginRequest):

    if data.username != DEMO_EMAIL:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    if not pwd_context.verify(
        data.password,
        DEMO_PASSWORD_HASH
    ):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

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

    defi = defis_mfa.get(data.mfa_challenge)

    if not defi:
        raise HTTPException(
            status_code=401,
            detail="Session MFA invalide ou expirée"
        )

    if time.time() - defi["date_creation"] > DUREE_CHALLENGE:
        del defis_mfa[data.mfa_challenge]

        raise HTTPException(
            status_code=401,
            detail="Session MFA expirée"
        )

    totp = pyotp.TOTP(TOTP_SECRET)

    if not totp.verify(data.code):
        raise HTTPException(
            status_code=401,
            detail="Code Authenticator incorrect ou expiré"
        )

    token = jwt.encode(
        {
            "sub": DEMO_EMAIL,
            "role": "admin"
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

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
    patient_id: int,
    medecin_id: int
):

    from Api.consentement import donner_consentement

    return donner_consentement(
        patient_id,
        medecin_id
    )


@application.get("/consentement/{patient_id}/{medecin_id}")
def verifier_consentement_route(
    patient_id: int,
    medecin_id: int
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
    patient_id: int,
    medecin_id: int
):

    from Api.consentement import retirer_consentement

    return retirer_consentement(
        patient_id,
        medecin_id
    )


@application.get("/dossiers/{patient_id}/{medecin_id}")
def acces_dossier(
    patient_id: int,
    medecin_id: int
):

    role = "medecin"

    verifier_role(
        role,
        "voir_dossiers"
    )

    if not consentement_valide(
        patient_id,
        medecin_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Accès refusé : consentement du patient absent"
        )

    try:
        contenu = lire_dossier(
            patient_id=patient_id,
            dossier_id=3,
            utilisateur_id=medecin_id,
            adresse_ip="127.0.0.1"
        )
    except ValueError as erreur:
        raise HTTPException(
            status_code=404,
            detail=str(erreur)
        )

    return {
        "message": "Accès au dossier autorisé",
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "contenu": contenu
    }


@application.post("/dossiers")
def creer_dossier_route(data: DossierRequest):

    utilisateur_id = 2

    resultat = creer_dossier(
        patient_id=data.patient_id,
        contenu=data.contenu
    )

    enregistrer_action(
        utilisateur_id=utilisateur_id,
        action="CREATION_DOSSIER",
        ressource=f"dossier_{resultat['id']}",
        adresse_ip="127.0.0.1"
    )

    return resultat