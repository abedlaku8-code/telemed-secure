
import os
import secrets
import time
import hashlib
import hmac
import smtplib
import ssl

from email.message import EmailMessage
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from Api.database import get_connection
from Api.rbac import a_permission
from Api.consentement import consentement_valide
from Api.dossiers import (
    creer_dossier,
    lire_dossier,
    lire_dossier_specialiste
)
from Api.audit import enregistrer_action


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
DEMO_EMAIL = os.getenv("DEMO_EMAIL")
DEMO_PASSWORD_HASH = os.getenv("DEMO_PASSWORD_HASH")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

ALGORITHM = "HS256"
DUREE_CHALLENGE = 300
MAX_TENTATIVES_MFA = 5

defis_mfa = {}

def envoyer_code_mfa(email_destinataire: str, code: str) -> None:
    """Envoie le code MFA temporaire par e-mail."""

    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM]):
        raise RuntimeError("Configuration SMTP incomplÃ¨te.")

    message = EmailMessage()
    message["Subject"] = "Votre code de vÃ©rification Telemed Secure"
    message["From"] = EMAIL_FROM
    message["To"] = email_destinataire
    message.set_content(
        f"""Bonjour,

Votre code de vÃ©rification Telemed Secure est : {code}

Ce code expire dans 5 minutes et ne peut Ãªtre utilisÃ© qu'une seule fois.

Si vous n'Ãªtes pas Ã  l'origine de cette demande, ignorez ce message.

L'Ã©quipe Telemed Secure"""
    )

    contexte_ssl = ssl.create_default_context()

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=15
    ) as serveur:
        serveur.ehlo()
        serveur.starttls(context=contexte_ssl)
        serveur.ehlo()
        serveur.login(SMTP_USERNAME, SMTP_PASSWORD)
        serveur.send_message(message)



if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY absente du fichier .env"
    )

if not DEMO_EMAIL:
    raise RuntimeError(
        "DEMO_EMAIL absente du fichier .env"
    )

if not DEMO_PASSWORD_HASH:
    raise RuntimeError(
        "DEMO_PASSWORD_HASH absent du fichier .env"
    )



# ============================================================
# APPLICATION FASTAPI
# ============================================================

application = FastAPI(
    title="Telemed Secure API"
)


application.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://telemed-secure-frontend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


securite = HTTPBearer()


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# VERIFICATION DES PERMISSIONS
# ============================================================

def verifier_role(
    role: str,
    permission: str
):
    """VÃ©rifie qu'un rÃ´le possÃ¨de une permission."""

    if not a_permission(
        role,
        permission
    ):
        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s interdit : permission insuffisante"
        )


# ============================================================
# AUTHENTIFICATION JWT
# ============================================================

def obtenir_utilisateur_token(
    credentials: HTTPAuthorizationCredentials = Depends(
        securite
    )
):
    """
    VÃ©rifie le JWT et rÃ©cupÃ¨re l'identitÃ©
    et le rÃ´le depuis PostgreSQL.
    """

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if not email:
            raise HTTPException(
                status_code=401,
                detail="Token invalide"
            )

        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        email,
                        role,
                        actif
                    FROM utilisateurs
                    WHERE email = %s
                    """,
                    (email,)
                )

                utilisateur = cur.fetchone()

        if not utilisateur:
            raise HTTPException(
                status_code=401,
                detail="Utilisateur non autorisÃ©"
            )

        (
            utilisateur_id,
            email_db,
            role,
            actif
        ) = utilisateur

        if not actif:
            raise HTTPException(
                status_code=403,
                detail="Compte dÃ©sactivÃ©"
            )

        return {
            "id": utilisateur_id,
            "email": email_db,
            "role": role
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token invalide ou expirÃ©"
        )


# ============================================================
# MODELES
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class DemandeReinitialisationRequest(BaseModel):
    identifiant: str


class NouveauMotDePasseRequest(BaseModel):
    jeton: str
    nouveau_mot_de_passe: str


class InscriptionRequest(BaseModel):
    nom: str
    prenom: str
    email: str
    telephone: str
    password: str
    role: str


class InscriptionResponse(BaseModel):
    message: str
    utilisateur_id: int
    nom: str
    prenom: str
    email: str
    telephone: str
    role: str


class UtilisateurRequest(BaseModel):
    email: str
    password: str
    role: str


class MFARequest(BaseModel):
    mfa_challenge: str
    code: str


class DossierRequest(BaseModel):
    patient_id: int
    contenu: str
    motif: str | None = None
    antecedents: str | None = None
    allergies: str | None = None
    traitements: str | None = None
    observations: str | None = None


class DemandeMedecinRequest(BaseModel):
    medecin_id: int
    message: str | None = None


class ReponseDemandeMedecinRequest(BaseModel):
    demande_id: int
    decision: str
    date_rendez_vous: str | None = None
    heure_rendez_vous: str | None = None


class ReponseRecommandationSpecialisteRequest(BaseModel):
    recommandation_id: int
    decision: str


class RecommandationSpecialisteRequest(BaseModel):
    patient_id: int
    specialiste_id: int
    message: str | None = None


# ============================================================
# ACCUEIL
# ============================================================

@application.get("/")
def accueil():

    return {
        "message": "API Telemed Secure",
        "statut": "API opÃ©rationnelle"
    }


# ============================================================
# CREATION UTILISATEUR
# ============================================================

@application.post(
    "/utilisateurs",
    response_model=InscriptionResponse
)
def creer_utilisateur(
    data: InscriptionRequest
):

    nom = data.nom.strip()
    prenom = data.prenom.strip()
    email = data.email.strip().lower()
    telephone = data.telephone.strip()
    role = data.role.strip().lower()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not nom or len(nom) < 2:
        raise HTTPException(
            status_code=400,
            detail="Le nom est obligatoire."
        )

    if not prenom or len(prenom) < 2:
        raise HTTPException(
            status_code=400,
            detail="Le prÃ©nom est obligatoire."
        )

    if (
        "@" not in email
        or "." not in email.split("@")[-1]
    ):
        raise HTTPException(
            status_code=400,
            detail="Adresse email invalide."
        )

    if not telephone or len(telephone) < 8:
        raise HTTPException(
            status_code=400,
            detail="NumÃ©ro de tÃ©lÃ©phone invalide."
        )

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail=(
                "Le mot de passe doit contenir "
                "au moins 8 caractÃ¨res."
            )
        )

    # --------------------------------------------------------
    # LE COMPTE ADMIN NE PEUT PAS ÃŠTRE CREE PUBLIQUEMENT
    # --------------------------------------------------------

    if role not in {
        "patient",
        "medecin"
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Le rÃ´le doit Ãªtre patient ou medecin."
            )
        )

    # --------------------------------------------------------
    # VERIFICATION EMAIL
    # --------------------------------------------------------

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM utilisateurs
                WHERE email = %s
                   OR telephone = %s
                """,
                (
                    email,
                    telephone
                )
            )

            utilisateur_existant = cur.fetchone()

            if utilisateur_existant:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Cette adresse email "
                        "ou ce numÃ©ro de tÃ©lÃ©phone "
                        "est dÃ©jÃ  utilisÃ©."
                    )
                )

            # ------------------------------------------------
            # HASHAGE DU MOT DE PASSE
            # ------------------------------------------------

            password_hash = pwd_context.hash(
                data.password
            )

            # ------------------------------------------------
            # CREATION DU COMPTE
            # ------------------------------------------------

            cur.execute(
                """
                INSERT INTO utilisateurs
                (
                    nom,
                    prenom,
                    email,
                    telephone,
                    password_hash,
                    role,
                    actif
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
                RETURNING
                    id,
                    nom,
                    prenom,
                    email,
                    telephone,
                    role
                """,
                (
                    nom,
                    prenom,
                    email,
                    telephone,
                    password_hash,
                    role
                )
            )

            utilisateur = cur.fetchone()

            utilisateur_id = utilisateur[0]

    # --------------------------------------------------------
    # JOURNALISATION
    # --------------------------------------------------------

    enregistrer_action(
        utilisateur_id=utilisateur_id,
        action="CREATION_COMPTE",
        ressource=(
            f"utilisateur:{utilisateur_id}"
        ),
        adresse_ip="127.0.0.1"
    )

    return {
        "message": "Compte crÃ©Ã© avec succÃ¨s.",
        "utilisateur_id": utilisateur[0],
        "nom": utilisateur[1],
        "prenom": utilisateur[2],
        "email": utilisateur[3],
        "telephone": utilisateur[4],
        "role": utilisateur[5]
    }

# ============================================================
# RÃ‰INITIALISATION DU MOT DE PASSE â€” DEMANDE
# ============================================================

@application.post("/mot-de-passe-oublie")
def demander_reinitialisation(
    data: DemandeReinitialisationRequest
):
    identifiant = data.identifiant.strip().lower()

    if not identifiant:
        raise HTTPException(
            status_code=400,
            detail="Identifiant requis"
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id, email, telephone, actif
                FROM utilisateurs
                WHERE email = %s
                   OR telephone = %s
                """,
                (
                    identifiant,
                    identifiant
                )
            )

            utilisateur = cur.fetchone()

            # RÃ©ponse volontairement identique si le compte
            # n'existe pas afin d'Ã©viter l'Ã©numÃ©ration des comptes.
            if not utilisateur:

                return {
                    "message": (
                        "Si un compte correspondant existe, "
                        "une procÃ©dure de rÃ©initialisation sera disponible."
                    )
                }

            utilisateur_id = utilisateur[0]
            email_db = utilisateur[1]
            telephone_db = utilisateur[2]
            actif = utilisateur[3]

            if not actif:

                return {
                    "message": (
                        "Si un compte correspondant existe, "
                        "une procÃ©dure de rÃ©initialisation sera disponible."
                    )
                }

            # ------------------------------------------------
            # INVALIDATION DES ANCIENS JETONS
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE jetons_reinitialisation
                SET utilise = TRUE
                WHERE utilisateur_id = %s
                  AND utilise = FALSE
                """,
                (utilisateur_id,)
            )

            # ------------------------------------------------
            # CRÃ‰ATION DU NOUVEAU JETON
            # ------------------------------------------------

            jeton = secrets.token_urlsafe(32)

            jeton_hash = pwd_context.hash(jeton)

            date_expiration = (
                datetime.now()
                + timedelta(minutes=15)
            )

            cur.execute(
                """
                INSERT INTO jetons_reinitialisation
                    (
                        utilisateur_id,
                        jeton_hash,
                        date_expiration,
                        utilise
                    )
                VALUES
                    (%s, %s, %s, FALSE)
                """,
                (
                    utilisateur_id,
                    jeton_hash,
                    date_expiration
                )
            )

            # ------------------------------------------------
            # JOURNAL D'AUDIT
            # ------------------------------------------------

            enregistrer_action(
                utilisateur_id=utilisateur_id,
                action="DEMANDE_REINITIALISATION_MOT_DE_PASSE",
                ressource="compte",
                adresse_ip="127.0.0.1"
            )

    # --------------------------------------------------------
    # MODE DÃ‰MONSTRATION
    # --------------------------------------------------------
    #
    # Pour l'instant, aucun e-mail rÃ©el n'est envoyÃ©.
    # Le jeton est retournÃ© uniquement pour permettre
    # les tests de la fonctionnalitÃ© en environnement
    # acadÃ©mique de dÃ©monstration.
    #

    return {
        "message": (
            "Si un compte correspondant existe, "
            "une procÃ©dure de rÃ©initialisation sera disponible."
        ),
        "jeton_demo": jeton
    }


# ============================================================
# RÃ‰INITIALISATION DU MOT DE PASSE â€” VALIDATION
# ============================================================

@application.post("/reinitialiser-mot-de-passe")
def reinitialiser_mot_de_passe(
    data: NouveauMotDePasseRequest
):
    jeton = data.jeton.strip()
    nouveau_mot_de_passe = data.nouveau_mot_de_passe

    if not jeton:
        raise HTTPException(
            status_code=400,
            detail="Jeton requis"
        )

    if len(nouveau_mot_de_passe) < 8:
        raise HTTPException(
            status_code=400,
            detail="Le nouveau mot de passe doit contenir au moins 8 caractÃ¨res"
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # RECHERCHE DES JETONS ACTIFS
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    utilisateur_id,
                    jeton_hash,
                    date_expiration,
                    utilise
                FROM jetons_reinitialisation
                WHERE utilise = FALSE
                  AND date_expiration > CURRENT_TIMESTAMP
                ORDER BY date_creation DESC
                """
            )

            jetons = cur.fetchall()

            jeton_trouve = None

            for ligne in jetons:

                jeton_id = ligne[0]
                utilisateur_id = ligne[1]
                jeton_hash = ligne[2]
                date_expiration = ligne[3]

                if pwd_context.verify(
                    jeton,
                    jeton_hash
                ):
                    jeton_trouve = (
                        jeton_id,
                        utilisateur_id,
                        date_expiration
                    )
                    break

            # ------------------------------------------------
            # JETON INVALIDE
            # ------------------------------------------------

            if not jeton_trouve:

                raise HTTPException(
                    status_code=400,
                    detail="Jeton invalide ou expirÃ©"
                )

            jeton_id = jeton_trouve[0]
            utilisateur_id = jeton_trouve[1]

            # ------------------------------------------------
            # HACHAGE DU NOUVEAU MOT DE PASSE
            # ------------------------------------------------

            nouveau_hash = pwd_context.hash(
                nouveau_mot_de_passe
            )

            # ------------------------------------------------
            # MISE Ã€ JOUR DU MOT DE PASSE
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE utilisateurs
                SET password_hash = %s
                WHERE id = %s
                """,
                (
                    nouveau_hash,
                    utilisateur_id
                )
            )

            # ------------------------------------------------
            # INVALIDATION DU JETON
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE jetons_reinitialisation
                SET utilise = TRUE
                WHERE id = %s
                """,
                (jeton_id,)
            )

            # ------------------------------------------------
            # JOURNAL D'AUDIT
            # ------------------------------------------------

            enregistrer_action(
                utilisateur_id=utilisateur_id,
                action="REINITIALISATION_MOT_DE_PASSE",
                ressource="compte",
                adresse_ip="127.0.0.1"
            )

    return {
        "message": "Mot de passe rÃ©initialisÃ© avec succÃ¨s."
    }



# ============================================================
# CONNEXION
# ============================================================

@application.post("/login")
def login(
    data: LoginRequest
):

    identifiant = (
        data.username.strip().lower()
    )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    email,
                    password_hash,
                    role,
                    actif
                FROM utilisateurs
                WHERE email = %s
                   OR telephone = %s
                """,
                (
                    identifiant,
                    identifiant
                )
            )

            utilisateur = cur.fetchone()

    if not utilisateur:

        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    (
        utilisateur_id,
        email_db,
        password_hash,
        role,
        actif
    ) = utilisateur

    if not actif:

        raise HTTPException(
            status_code=403,
            detail="Compte dÃ©sactivÃ©"
        )

    if not pwd_context.verify(
        data.password,
        password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    # --------------------------------------------------------
    # CREATION DU DEFI MFA
    # --------------------------------------------------------


    mfa_challenge = secrets.token_urlsafe(32)
    code_mfa = f"{secrets.randbelow(1_000_000):06d}"

    defis_mfa[mfa_challenge] = {
        "utilisateur_id": utilisateur_id,
        "email": email_db,
        "role": role,
        "date_creation": time.time(),
        "code_hash": hashlib.sha256(code_mfa.encode()).hexdigest(),
        "tentatives": 0
    }


    try:
        debut_envoi = time.perf_counter()
        envoyer_code_mfa(email_db, code_mfa)
        print(
            f"Temps d'envoi Gmail : "
            f"{time.perf_counter() - debut_envoi:.2f} secondes"
        )

    except Exception as erreur:
        defis_mfa.pop(mfa_challenge, None)

        print(f"Erreur d'envoi MFA : {type(erreur).__name__}")

        raise HTTPException(
            status_code=503,
            detail="Impossible d'envoyer le code de vÃ©rification. RÃ©essayez plus tard."
        )

    return {
        "message": "PremiÃ¨re Ã©tape rÃ©ussie",
        "mfa_requis": True,
        "mfa_challenge": mfa_challenge
    }



# ============================================================
# MFA AUTHENTICATOR
# ============================================================

@application.post("/mfa/authenticator")

def verifier_authenticator(data: MFARequest):
    defi = defis_mfa.get(data.mfa_challenge)

    if not defi:
        raise HTTPException(
            status_code=401,
            detail="Session MFA invalide ou expirÃ©e"
        )

    if time.time() - defi["date_creation"] > DUREE_CHALLENGE:
        defis_mfa.pop(data.mfa_challenge, None)
        raise HTTPException(
            status_code=401,
            detail="Code MFA expirÃ©. Recommencez la connexion."
        )

    if not data.code.isdigit() or len(data.code) != 6:
        raise HTTPException(
            status_code=400,
            detail="Le code doit contenir exactement 6 chiffres."
        )

    defi["tentatives"] += 1

    if defi["tentatives"] > MAX_TENTATIVES_MFA:
        defis_mfa.pop(data.mfa_challenge, None)
        raise HTTPException(
            status_code=429,
            detail="Nombre maximal de tentatives atteint. Recommencez la connexion."
        )

    code_hash_recu = hashlib.sha256(data.code.encode()).hexdigest()

    if not hmac.compare_digest(code_hash_recu, defi["code_hash"]):
        if defi["tentatives"] >= MAX_TENTATIVES_MFA:
            defis_mfa.pop(data.mfa_challenge, None)
            raise HTTPException(
                status_code=429,
                detail="Nombre maximal de tentatives atteint. Recommencez la connexion."
            )

        raise HTTPException(
            status_code=401,
            detail="Code de vÃ©rification incorrect."
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, role, actif
                FROM utilisateurs
                WHERE email = %s
                """,
                (defi["email"],)
            )
            utilisateur = cur.fetchone()

    if not utilisateur:
        defis_mfa.pop(data.mfa_challenge, None)
        raise HTTPException(
            status_code=401,
            detail="Utilisateur non autorisÃ©."
        )

    utilisateur_id, email, role, actif = utilisateur

    if not actif:
        defis_mfa.pop(data.mfa_challenge, None)
        raise HTTPException(
            status_code=403,
            detail="Compte dÃ©sactivÃ©."
        )

    date_expiration = datetime.now(timezone.utc) + timedelta(hours=1)

    token = jwt.encode(
        {
            "sub": email,
            "role": role,
            "exp": date_expiration
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    # Suppression du dÃ©fi : le code ne peut plus Ãªtre rÃ©utilisÃ©.
    defis_mfa.pop(data.mfa_challenge, None)

    return {
        "message": "Authentification MFA rÃ©ussie",
        "acces": "autorisÃ©",
        "access_token": token,
        "token_type": "bearer"
    }



# ============================================================
# ADMIN
# ============================================================

@application.get("/admin")
def espace_admin(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    role = utilisateur["role"]

    verifier_role(
        role,
        "gerer_utilisateurs"
    )

    return {

        "message": "AccÃ¨s autorisÃ©",

        "role": role,

        "permission": (
            "gerer_utilisateurs"
        )
    }


# ============================================================
# ADMIN MEDECIN
# ============================================================

@application.get("/medecin/admin")
def acces_medecin_admin(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    role = utilisateur["role"]

    verifier_role(
        role,
        "gerer_utilisateurs"
    )

    return {
        "message": "AccÃ¨s autorisÃ©",
        "role": role
    }

# ============================================================
# LISTE DES MEDECINS
# ============================================================

@application.get("/profil")
def obtenir_profil(
    utilisateur=Depends(obtenir_utilisateur_token)
):
    return {
        "id": utilisateur["id"],
        "email": utilisateur["email"],
        "role": utilisateur["role"]
    }

@application.get("/medecins")
def obtenir_medecins(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    nom,
                    prenom,
                    email
                FROM utilisateurs
                WHERE role = 'medecin'
                  AND actif = TRUE
                ORDER BY
                    nom,
                    prenom
                """
            )

            medecins = cur.fetchall()

    return {
        "medecins": [
            {
                "id": medecin[0],
                "nom": medecin[1],
                "prenom": medecin[2],
                "email": medecin[3]
            }
            for medecin in medecins
        ]
    }

# ============================================================
# DEMANDE DE MEDECIN PRINCIPAL
# ============================================================

@application.post("/demandes-medecin")
def creer_demande_medecin(
    data: DemandeMedecinRequest,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    verifier_role(
        utilisateur["role"],
        "voir_ses_donnees"
    )

    patient_id = utilisateur["id"]

    medecin_id = data.medecin_id

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM utilisateurs
                WHERE id = %s
                  AND role = 'medecin'
                  AND actif = TRUE
                """,
                (medecin_id,)
            )

            medecin = cur.fetchone()

            if not medecin:

                raise HTTPException(
                    status_code=404,
                    detail="MÃ©decin introuvable"
                )

            cur.execute(
                """
                SELECT id
                FROM demandes_medecin
                WHERE patient_id = %s
                  AND medecin_id = %s
                  AND statut = 'EN_ATTENTE'
                """,
                (
                    patient_id,
                    medecin_id
                )
            )

            demande_existante = (
                cur.fetchone()
            )

            if demande_existante:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Une demande est dÃ©jÃ  "
                        "en attente pour ce mÃ©decin"
                    )
                )

            cur.execute(
                """
                INSERT INTO demandes_medecin
                (
                    patient_id,
                    medecin_id,
                    type_demande,
                    origine,
                    statut,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    'principal',
                    'patient',
                    'EN_ATTENTE',
                    %s
                )
                RETURNING id, date_demande
                """,
                (
                    patient_id,
                    medecin_id,
                    data.message
                )
            )

            demande = cur.fetchone()

            cur.execute(
                """
                INSERT INTO notifications
                (
                    utilisateur_id,
                    type,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    medecin_id,
                    "DEMANDE_MEDECIN",
                    (
                        "Un patient souhaite vous "
                        "choisir comme mÃ©decin principal."
                    )
                )
            )

    enregistrer_action(
        utilisateur_id=patient_id,
        action="DEMANDE_MEDECIN_CREEE",
        ressource=(
            f"demande_medecin_{demande[0]}"
        ),
        adresse_ip="127.0.0.1"
    )

    return {

        "message": (
            "Demande envoyÃ©e au mÃ©decin"
        ),

        "demande_id": demande[0],

        "patient_id": patient_id,

        "medecin_id": medecin_id,

        "statut": "EN_ATTENTE",

        "date_demande": demande[1]
    }


# ============================================================
# REPONSE DEMANDE MEDECIN
# ============================================================

@application.post(
    "/demandes-medecin/repondre"
)
def repondre_demande_medecin(
    demande: ReponseDemandeMedecinRequest,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "medecin":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux mÃ©decins"
        )

    if demande.decision not in {
        "ACCEPTEE",
        "REFUSEE"
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "La dÃ©cision doit Ãªtre "
                "ACCEPTEE ou REFUSEE"
            )
        )

    if demande.decision == "ACCEPTEE":

        if (
            not demande.date_rendez_vous
            or not demande.heure_rendez_vous
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "La date et l'heure "
                    "du rendez-vous sont obligatoires"
                )
            )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    patient_id,
                    medecin_id,
                    statut
                FROM demandes_medecin
                WHERE id = %s
                """,
                (demande.demande_id,)
            )

            demande_existante = (
                cur.fetchone()
            )

            if not demande_existante:

                raise HTTPException(
                    status_code=404,
                    detail="Demande introuvable"
                )

            (
                patient_id,
                medecin_id,
                statut
            ) = demande_existante

            if medecin_id != utilisateur["id"]:

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Cette demande ne vous est pas destinÃ©e"
                    )
                )

            if statut != "EN_ATTENTE":

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Cette demande a dÃ©jÃ  Ã©tÃ© traitÃ©e"
                    )
                )

            # ------------------------------------------------
            # REFUS
            # ------------------------------------------------

            if demande.decision == "REFUSEE":

                cur.execute(
                    """
                    UPDATE demandes_medecin
                    SET statut = 'REFUSEE',
                        date_reponse = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (demande.demande_id,)
                )

                cur.execute(
                    """
                    INSERT INTO notifications
                    (
                        utilisateur_id,
                        type,
                        message
                    )
                    VALUES
                    (
                        %s,
                        'REPONSE_MEDECIN',
                        %s
                    )
                    """,
                    (
                        patient_id,
                        (
                            "Votre demande de mÃ©decin "
                            "principal a Ã©tÃ© refusÃ©e."
                        )
                    )
                )

                enregistrer_action(
                    utilisateur["id"],
                    "DEMANDE_MEDECIN_REFUSEE",
                    f"demande:{demande.demande_id}"
                )

                conn.commit()

                return {

                    "message": "Demande refusÃ©e",

                    "demande_id": (
                        demande.demande_id
                    ),

                    "statut": "REFUSEE"
                }

            # ------------------------------------------------
            # ACCEPTATION
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    id,
                    medecin_id
                FROM relations_patient_medecin
                WHERE patient_id = %s
                  AND type_relation = 'principal'
                  AND actif = TRUE
                """,
                (patient_id,)
            )

            relation_existante = (
                cur.fetchone()
            )

            if relation_existante:

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Le patient possÃ¨de dÃ©jÃ  "
                        "un mÃ©decin principal actif"
                    )
                )

            cur.execute(
                """
                UPDATE demandes_medecin
                SET statut = 'ACCEPTEE',
                    date_reponse = CURRENT_TIMESTAMP,
                    date_rendez_vous = %s,
                    heure_rendez_vous = %s
                WHERE id = %s
                """,
                (
                    demande.date_rendez_vous,
                    demande.heure_rendez_vous,
                    demande.demande_id
                )
            )

            cur.execute(
                """
                INSERT INTO relations_patient_medecin
                (
                    patient_id,
                    medecin_id,
                    type_relation,
                    actif
                )
                VALUES
                (
                    %s,
                    %s,
                    'principal',
                    TRUE
                )
                """,
                (
                    patient_id,
                    utilisateur["id"]
                )
            )

            cur.execute(
                """
                INSERT INTO notifications
                (
                    utilisateur_id,
                    type,
                    message
                )
                VALUES
                (
                    %s,
                    'RENDEZ_VOUS_MEDECIN',
                    %s
                )
                """,
                (
                    patient_id,
                    (
                        "Votre demande de mÃ©decin "
                        "principal a Ã©tÃ© acceptÃ©e. "
                        f"Rendez-vous prÃ©vu le "
                        f"{demande.date_rendez_vous} "
                        f"Ã  {demande.heure_rendez_vous}."
                    )
                )
            )

            enregistrer_action(
                utilisateur["id"],
                "DEMANDE_MEDECIN_ACCEPTEE",
                f"demande:{demande.demande_id}"
            )

            conn.commit()

    return {

        "message": (
            "Demande acceptÃ©e et "
            "rendez-vous enregistrÃ©"
        ),

        "demande_id": demande.demande_id,

        "statut": "ACCEPTEE",

        "date_rendez_vous": (
            demande.date_rendez_vous
        ),

        "heure_rendez_vous": (
            demande.heure_rendez_vous
        )
    }


# ============================================================
# RECOMMANDATION SPECIALISTE
# ============================================================

@application.post(
    "/recommandations-specialiste"
)
def recommander_specialiste(
    demande: RecommandationSpecialisteRequest,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "medecin":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux mÃ©decins"
        )

    medecin_principal_id = utilisateur["id"]

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT patient_id
                FROM relations_patient_medecin
                WHERE patient_id = %s
                  AND medecin_id = %s
                  AND type_relation = 'principal'
                  AND actif = TRUE
                """,
                (
                    demande.patient_id,
                    medecin_principal_id
                )
            )

            relation = cur.fetchone()

            if not relation:

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Ce mÃ©decin n'est pas "
                        "le mÃ©decin principal de ce patient"
                    )
                )

            patient_id = demande.patient_id

            cur.execute(
                """
                SELECT
                    id,
                    email,
                    role,
                    actif
                FROM utilisateurs
                WHERE id = %s
                """,
                (demande.specialiste_id,)
            )

            specialiste = cur.fetchone()

            if not specialiste:

                raise HTTPException(
                    status_code=404,
                    detail="SpÃ©cialiste introuvable"
                )

            if (
                specialiste[2] != "medecin"
                or not specialiste[3]
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "L'utilisateur sÃ©lectionnÃ© "
                        "n'est pas un mÃ©decin actif"
                    )
                )

            if (
                specialiste[0]
                == medecin_principal_id
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Le mÃ©decin principal "
                        "ne peut pas se recommander lui-mÃªme"
                    )
                )

            cur.execute(
                """
                SELECT id
                FROM recommandations_specialiste
                WHERE patient_id = %s
                  AND medecin_principal_id = %s
                  AND specialiste_id = %s
                  AND statut = 'EN_ATTENTE'
                """,
                (
                    patient_id,
                    medecin_principal_id,
                    demande.specialiste_id
                )
            )

            if cur.fetchone():

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Une recommandation est "
                        "dÃ©jÃ  en attente"
                    )
                )

            cur.execute(
                """
                INSERT INTO recommandations_specialiste
                (
                    patient_id,
                    medecin_principal_id,
                    specialiste_id,
                    message,
                    statut
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    'EN_ATTENTE'
                )
                RETURNING
                    id,
                    date_recommandation
                """,
                (
                    patient_id,
                    medecin_principal_id,
                    demande.specialiste_id,
                    demande.message
                )
            )

            recommandation = (
                cur.fetchone()
            )

            cur.execute(
                """
                INSERT INTO notifications
                (
                    utilisateur_id,
                    type,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    patient_id,
                    "RECOMMANDATION_SPECIALISTE",
                    (
                        "Votre mÃ©decin principal "
                        "vous recommande le spÃ©cialiste "
                        f"{specialiste[1]}."
                    )
                )
            )

            enregistrer_action(
                medecin_principal_id,
                "RECOMMANDATION_SPECIALISTE_CREEE",
                (
                    f"recommandation:"
                    f"{recommandation[0]}"
                )
            )

        conn.commit()

    return {

        "message": (
            "Recommandation du spÃ©cialiste crÃ©Ã©e"
        ),

        "recommandation_id": (
            recommandation[0]
        ),

        "patient_id": patient_id,

        "medecin_principal_id": (
            medecin_principal_id
        ),

        "specialiste_id": (
            demande.specialiste_id
        ),

        "statut": "EN_ATTENTE",

        "date_recommandation": (
            recommandation[1]
        )
    }


# ============================================================
# REPONSE RECOMMANDATION SPECIALISTE
# ============================================================

@application.post(
    "/recommandations-specialiste/repondre"
)
def repondre_recommandation_specialiste(
    demande: ReponseRecommandationSpecialisteRequest,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "patient":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux patients"
        )

    decision = demande.decision.upper()

    if decision not in {
        "ACCEPTEE",
        "REFUSEE"
    }:

        raise HTTPException(
            status_code=400,
            detail="DÃ©cision invalide"
        )

    patient_id = utilisateur["id"]

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    patient_id,
                    medecin_principal_id,
                    specialiste_id,
                    statut
                FROM recommandations_specialiste
                WHERE id = %s
                """,
                (demande.recommandation_id,)
            )

            recommandation = cur.fetchone()

            if not recommandation:

                raise HTTPException(
                    status_code=404,
                    detail="Recommandation introuvable"
                )

            (
                recommandation_id,
                patient_recommandation_id,
                medecin_principal_id,
                specialiste_id,
                statut
            ) = recommandation

            if (
                patient_recommandation_id
                != patient_id
            ):

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Cette recommandation "
                        "ne vous appartient pas"
                    )
                )

            if statut != "EN_ATTENTE":

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Cette recommandation "
                        "a dÃ©jÃ  reÃ§u une rÃ©ponse"
                    )
                )

            # ------------------------------------------------
            # ACCEPTATION
            # ------------------------------------------------

            if decision == "ACCEPTEE":

                cur.execute(
                    """
                    SELECT id
                    FROM relations_patient_medecin
                    WHERE patient_id = %s
                      AND medecin_id = %s
                      AND type_relation = 'specialiste'
                      AND actif = TRUE
                    """,
                    (
                        patient_id,
                        specialiste_id
                    )
                )

                relation_existante = (
                    cur.fetchone()
                )

                if not relation_existante:

                    cur.execute(
                        """
                        INSERT INTO relations_patient_medecin
                        (
                            patient_id,
                            medecin_id,
                            type_relation,
                            actif
                        )
                        VALUES
                        (
                            %s,
                            %s,
                            'specialiste',
                            TRUE
                        )
                        """,
                        (
                            patient_id,
                            specialiste_id
                        )
                    )

                cur.execute(
                    """
                    UPDATE recommandations_specialiste
                    SET statut = 'ACCEPTEE',
                        date_reponse = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (recommandation_id,)
                )

                cur.execute(
                    """
                    INSERT INTO notifications
                    (
                        utilisateur_id,
                        type,
                        message
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        specialiste_id,
                        "RECOMMANDATION_SPECIALISTE_ACCEPTEE",
                        (
                            "Le patient a acceptÃ© "
                            "la recommandation du spÃ©cialiste."
                        )
                    )
                )

                enregistrer_action(
                    patient_id,
                    "RECOMMANDATION_SPECIALISTE_ACCEPTEE",
                    (
                        f"recommandation:"
                        f"{recommandation_id}"
                    )
                )

                message = (
                    "Recommandation du spÃ©cialiste "
                    "acceptÃ©e"
                )

            # ------------------------------------------------
            # REFUS
            # ------------------------------------------------

            else:

                cur.execute(
                    """
                    UPDATE recommandations_specialiste
                    SET statut = 'REFUSEE',
                        date_reponse = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (recommandation_id,)
                )

                cur.execute(
                    """
                    INSERT INTO notifications
                    (
                        utilisateur_id,
                        type,
                        message
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        medecin_principal_id,
                        "RECOMMANDATION_SPECIALISTE_REFUSEE",
                        (
                            "Le patient a refusÃ© "
                            "la recommandation du spÃ©cialiste."
                        )
                    )
                )

                enregistrer_action(
                    patient_id,
                    "RECOMMANDATION_SPECIALISTE_REFUSEE",
                    (
                        f"recommandation:"
                        f"{recommandation_id}"
                    )
                )

                message = (
                    "Recommandation du spÃ©cialiste "
                    "refusÃ©e"
                )

            conn.commit()

    return {

        "message": message,

        "recommandation_id": (
            recommandation_id
        ),

        "patient_id": patient_id,

        "specialiste_id": specialiste_id,

        "statut": decision
    }


# ============================================================
# MEDECIN PRINCIPAL
# ============================================================

@application.get("/medecin-principal")
def obtenir_medecin_principal(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "patient":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux patients"
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    r.id,
                    r.medecin_id,
                    u.email,
                    r.type_relation,
                    r.actif,
                    r.date_debut,
                    r.date_fin,
                    d.date_rendez_vous,
                    d.heure_rendez_vous
                FROM relations_patient_medecin r
                JOIN utilisateurs u
                    ON u.id = r.medecin_id
                LEFT JOIN demandes_medecin d
                    ON d.patient_id = r.patient_id
                   AND d.medecin_id = r.medecin_id
                   AND d.type_demande = 'principal'
                   AND d.statut = 'ACCEPTEE'
                WHERE r.patient_id = %s
                  AND r.type_relation = 'principal'
                  AND r.actif = TRUE
                ORDER BY
                    d.date_reponse DESC NULLS LAST
                LIMIT 1
                """,
                (utilisateur["id"],)
            )

            relation = cur.fetchone()

    if not relation:

        return {

            "patient_id": utilisateur["id"],

            "medecin_principal": None,

            "rendez_vous": None
        }

    return {

        "patient_id": utilisateur["id"],

        "medecin_principal": {

            "relation_id": relation[0],

            "medecin_id": relation[1],

            "medecin_email": relation[2],

            "type_relation": relation[3],

            "actif": relation[4],

            "date_debut": relation[5],

            "date_fin": relation[6]
        },

        "rendez_vous": {

            "date": relation[7],

            "heure": relation[8]

        }
        if relation[7] and relation[8]
        else None
    }


# ============================================================
# JOURNAL D'AUDIT
# ============================================================

@application.get("/historique")
def obtenir_historique(
    utilisateur=Depends(obtenir_utilisateur_token)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    action,
                    ressource,
                    adresse_ip,
                    date_action
                FROM journal_audit
                WHERE utilisateur_id = %s
                ORDER BY date_action DESC
                LIMIT 50
                """,
                (utilisateur["id"],)
            )

            historique = cur.fetchall()

    return [
        {
            "id": ligne[0],
            "action": ligne[1],
            "ressource": ligne[2],
            "adresse_ip": ligne[3],
            "date_action": ligne[4]
        }
        for ligne in historique
    ]

@application.get("/audit")
def consulter_audit(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    role = utilisateur["role"]

    if role != "admin":

        raise HTTPException(
            status_code=403,
            detail=(
                "AccÃ¨s au journal d'audit "
                "rÃ©servÃ© aux administrateurs"
            )
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    ja.id,
                    ja.utilisateur_id,
                    u.email,
                    u.role,
                    ja.action,
                    ja.ressource,
                    ja.adresse_ip,
                    ja.date_action
                FROM journal_audit ja
                JOIN utilisateurs u
                    ON u.id = ja.utilisateur_id
                ORDER BY
                    ja.date_action DESC
                LIMIT 50
                """
            )

            lignes = cur.fetchall()

    return {

        "nombre": len(lignes),

        "evenements": [

            {
                "id": ligne[0],
                "utilisateur_id": ligne[1],
                "email": ligne[2],
                "role": ligne[3],
                "action": ligne[4],
                "ressource": ligne[5],
                "adresse_ip": ligne[6],
                "date_action": ligne[7]
            }

            for ligne in lignes
        ]
    }


# ============================================================
# NOTIFICATIONS
# ============================================================

@application.get("/notifications")
def obtenir_notifications(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    type,
                    message,
                    lue,
                    date_creation
                FROM notifications
                WHERE utilisateur_id = %s
                ORDER BY date_creation DESC
                """,
                (utilisateur["id"],)
            )

            notifications = cur.fetchall()

    return {

        "utilisateur_id": utilisateur["id"],

        "notifications": [

            {
                "id": notification[0],
                "type": notification[1],
                "message": notification[2],
                "lue": notification[3],
                "date_creation": notification[4]
            }

            for notification in notifications
        ]
    }

# ============================================================
# MES DEMANDES DE MEDECIN
# ============================================================

@application.get("/mes-demandes-medecin")
def obtenir_mes_demandes_medecin(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "patient":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux patients"
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    d.id,
                    d.medecin_id,
                    u.nom,
                    u.prenom,
                    u.email,
                    d.type_demande,
                    d.statut,
                    d.message,
                    d.date_demande,
                    d.date_reponse,
                    d.date_rendez_vous,
                    d.heure_rendez_vous
                FROM demandes_medecin d
                JOIN utilisateurs u
                    ON u.id = d.medecin_id
                WHERE d.patient_id = %s
                ORDER BY
                    d.date_demande DESC
                """,
                (utilisateur["id"],)
            )

            demandes = cur.fetchall()

    return {
        "patient_id": utilisateur["id"],
        "demandes": [
            {
                "id": demande[0],
                "medecin_id": demande[1],
                "medecin_nom": demande[2],
                "medecin_prenom": demande[3],
                "medecin_email": demande[4],
                "type_demande": demande[5],
                "statut": demande[6],
                "message": demande[7],
                "date_demande": demande[8],
                "date_reponse": demande[9],
                "date_rendez_vous": demande[10],
                "heure_rendez_vous": demande[11]
            }
            for demande in demandes
        ]
    }

# ============================================================
# DEMANDES MEDECIN
# ============================================================

@application.get("/demandes-medecin")
def obtenir_demandes_medecin(
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "medecin":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux mÃ©decins"
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    d.id,
                    d.patient_id,
                    u.email,
                    d.type_demande,
                    d.origine,
                    d.statut,
                    d.message,
                    d.date_demande,
                    d.date_reponse
                FROM demandes_medecin d
                JOIN utilisateurs u
                    ON u.id = d.patient_id
                WHERE d.medecin_id = %s
                ORDER BY d.date_demande DESC
                """,
                (utilisateur["id"],)
            )

            demandes = cur.fetchall()

    return {

        "medecin_id": utilisateur["id"],

        "demandes": [

            {
                "id": demande[0],
                "patient_id": demande[1],
                "patient_email": demande[2],
                "type_demande": demande[3],
                "origine": demande[4],
                "statut": demande[5],
                "message": demande[6],
                "date_demande": demande[7],
                "date_reponse": demande[8]
            }

            for demande in demandes
        ]
    }


# ============================================================
# CONSENTEMENT
# ============================================================
@application.post(
    "/consentement/{patient_id}/{medecin_id}"
)
def donner_consentement_route(
    patient_id: int,
    medecin_id: int,
    utilisateur=Depends(obtenir_utilisateur_token)
):

    if utilisateur["role"] != "patient":
        raise HTTPException(
            status_code=403,
            detail="Seul le patient peut gÃ©rer son consentement"
        )

    if utilisateur["id"] != patient_id:
        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s non autorisÃ©"
        )

    from Api.consentement import (
        donner_consentement
    )

    return donner_consentement(
        patient_id,
        medecin_id
    )


@application.get(
    "/consentement/{patient_id}/{medecin_id}"
)
def verifier_consentement_route(
    patient_id: int,
    medecin_id: int,
    utilisateur=Depends(obtenir_utilisateur_token)
):

    if utilisateur["role"] != "patient":
        raise HTTPException(
            status_code=403,
            detail="Seul le patient peut consulter son consentement"
        )

    if utilisateur["id"] != patient_id:
        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s non autorisÃ©"
        )

    consentement = consentement_valide(
        patient_id,
        medecin_id
    )

    return {

        "patient_id": patient_id,

        "medecin_id": medecin_id,

        "consentement_valide": consentement
    }


@application.delete(
    "/consentement/{patient_id}/{medecin_id}"
)
def retirer_consentement_route(
    patient_id: int,
    medecin_id: int,
    utilisateur=Depends(obtenir_utilisateur_token)
):

    if utilisateur["role"] != "patient":
        raise HTTPException(
            status_code=403,
            detail="Seul le patient peut retirer son consentement"
        )

    if utilisateur["id"] != patient_id:
        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s non autorisÃ©"
        )

    from Api.consentement import (
        retirer_consentement
    )

    return retirer_consentement(
        patient_id,
        medecin_id
    )


# ============================================================
# LISTE DES DOSSIERS DU PATIENT CONNECTE
# ============================================================

@application.get("/dossiers/patient/{patient_id}")
def lister_dossiers_patient(
    patient_id: int,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "patient":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© au patient"
        )

    if utilisateur["id"] != patient_id:

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s refusÃ©"
        )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    patient_id
                FROM dossiers_medicaux
                WHERE patient_id = %s
                ORDER BY id DESC
                """,
                (patient_id,)
            )

            dossiers = cur.fetchall()

    return [
        {
            "id": ligne[0],
            "patient_id": ligne[1]
        }
        for ligne in dossiers
    ]

# ============================================================
# LISTE DES DOSSIERS ACCESSIBLES AU MEDECIN
# ============================================================

@application.get("/dossiers/medecin/{medecin_id}")
def lister_dossiers_medecin(
    medecin_id: int,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    if utilisateur["role"] != "medecin":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux mÃ©decins"
        )

    if utilisateur["id"] != medecin_id:

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s refusÃ©"
        )

    verifier_role(
        utilisateur["role"],
        "voir_dossiers"
    )

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT DISTINCT
                    d.id,
                    d.patient_id,
                    r.type_relation
                FROM dossiers_medicaux d
                INNER JOIN relations_patient_medecin r
                    ON r.patient_id = d.patient_id
                WHERE r.medecin_id = %s
                  AND r.actif = TRUE
                ORDER BY d.id DESC
                """,
                (medecin_id,)
            )

            dossiers = cur.fetchall()

    return [
        {
            "id": ligne[0],
            "patient_id": ligne[1],
            "type_relation": ligne[2]
        }
        for ligne in dossiers
    ]

# ============================================================
# ACCES DOSSIER MEDICAL
# ============================================================

@application.get(
    "/dossiers/{patient_id}/{medecin_id}/{dossier_id}"
)
def acces_dossier(
    patient_id: int,
    medecin_id: int,
    dossier_id: int,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    role = utilisateur["role"]

    utilisateur_id = utilisateur["id"]

    # --------------------------------------------------------
    # PATIENT
    # --------------------------------------------------------

    if role == "patient":

        if utilisateur_id != patient_id:

            raise HTTPException(
                status_code=403,
                detail="AccÃ¨s refusÃ©"
            )

        try:

            contenu = lire_dossier(
                patient_id=patient_id,
                dossier_id=dossier_id,
                utilisateur_id=utilisateur_id,
                adresse_ip="127.0.0.1"
            )

        except ValueError as erreur:

            raise HTTPException(
                status_code=404,
                detail=str(erreur)
            )

        return {

            "message": (
                "AccÃ¨s au dossier autorisÃ©"
            ),

            "patient_id": patient_id,

            "medecin_id": medecin_id,

            "dossier_id": dossier_id,

            "contenu": contenu
        }

    # --------------------------------------------------------
    # MEDECIN
    # --------------------------------------------------------

    elif role == "medecin":

        if utilisateur_id != medecin_id:

            raise HTTPException(
                status_code=403,
                detail="AccÃ¨s refusÃ©"
            )

        verifier_role(
            role,
            "voir_dossiers"
        )

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT type_relation
                    FROM relations_patient_medecin
                    WHERE patient_id = %s
                      AND medecin_id = %s
                      AND actif = TRUE
                    """,
                    (
                        patient_id,
                        utilisateur_id
                    )
                )

                relation_detail = (
                    cur.fetchone()
                )

        if not relation_detail:

            raise HTTPException(
                status_code=403,
                detail=(
                    "AccÃ¨s refusÃ© : aucune "
                    "relation mÃ©dicale active"
                )
            )

        type_relation = relation_detail[0]

        # ----------------------------------------------------
        # CONSENTEMENT OBLIGATOIRE
        # ----------------------------------------------------

        if not consentement_valide(
            patient_id,
            utilisateur_id
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "AccÃ¨s refusÃ© : consentement "
                    "du patient absent"
                )
            )

        try:

            # ------------------------------------------------
            # SPECIALISTE
            # ------------------------------------------------

            if type_relation == "specialiste":

                contenu = lire_dossier_specialiste(
                    patient_id=patient_id,
                    dossier_id=dossier_id,
                    utilisateur_id=utilisateur_id,
                    adresse_ip="127.0.0.1"
                )

            # ------------------------------------------------
            # MEDECIN PRINCIPAL
            # ------------------------------------------------

            else:

                contenu = lire_dossier(
                    patient_id=patient_id,
                    dossier_id=dossier_id,
                    utilisateur_id=utilisateur_id,
                    adresse_ip="127.0.0.1"
                )

        except ValueError as erreur:

            raise HTTPException(
                status_code=404,
                detail=str(erreur)
            )

        return {

            "message": (
                "AccÃ¨s au dossier autorisÃ©"
            ),

            "patient_id": patient_id,

            "medecin_id": medecin_id,

            "dossier_id": dossier_id,

            "type_relation": type_relation,

            "contenu": contenu
        }

    # --------------------------------------------------------
    # AUTRE ROLE
    # --------------------------------------------------------

    else:

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s refusÃ©"
        )


# ============================================================
# CREATION DOSSIER MEDICAL
# ============================================================

@application.post("/dossiers")
def creer_dossier_route(
    data: DossierRequest,
    utilisateur=Depends(
        obtenir_utilisateur_token
    )
):

    role = utilisateur["role"]

    utilisateur_id = utilisateur["id"]

    # --------------------------------------------------------
    # MEDECIN UNIQUEMENT
    # --------------------------------------------------------

    if role != "medecin":

        raise HTTPException(
            status_code=403,
            detail="AccÃ¨s rÃ©servÃ© aux mÃ©decins"
        )

    verifier_role(
        role,
        "voir_dossiers"
    )

    # --------------------------------------------------------
    # RELATION MEDICALE
    # --------------------------------------------------------

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM relations_patient_medecin
                WHERE patient_id = %s
                  AND medecin_id = %s
                  AND actif = TRUE
                """,
                (
                    data.patient_id,
                    utilisateur_id
                )
            )

            relation = cur.fetchone()

    if not relation:

        raise HTTPException(
            status_code=403,
            detail=(
                "AccÃ¨s refusÃ© : aucune "
                "relation mÃ©dicale active"
            )
        )

    # --------------------------------------------------------
    # CREATION ET CHIFFREMENT DU DOSSIER
    # --------------------------------------------------------

    resultat = creer_dossier(
        patient_id=data.patient_id,
        contenu=data.contenu,
        motif=data.motif,
        antecedents=data.antecedents,
        allergies=data.allergies,
        traitements=data.traitements,
        observations=data.observations
    )

    # --------------------------------------------------------
    # JOURNALISATION
    # --------------------------------------------------------

    enregistrer_action(
        utilisateur_id=utilisateur_id,
        action="CREATION_DOSSIER",
        ressource=(
            f"dossier_{resultat['id']}"
        ),
        adresse_ip="127.0.0.1"
    )

    return resultat

