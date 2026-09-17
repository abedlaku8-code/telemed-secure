import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import pyotp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from Api.database import get_connection
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

securite = HTTPBearer()

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


def obtenir_utilisateur_token(
    credentials: HTTPAuthorizationCredentials = Depends(securite)
):
    """Vérifie le JWT et récupère l'identité et le rôle depuis PostgreSQL."""
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
                    SELECT id, email, role, actif
                    FROM utilisateurs
                    WHERE email = %s
                    """,
                    (email,)
                )
                utilisateur = cur.fetchone()

        if not utilisateur:
            raise HTTPException(
                status_code=401,
                detail="Utilisateur non autorisé"
            )

        utilisateur_id, email_db, role, actif = utilisateur

        if not actif:
            raise HTTPException(
                status_code=403,
                detail="Compte désactivé"
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
            detail="Token invalide ou expiré"
        )


class LoginRequest(BaseModel):
    username: str
    password: str

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

class DemandeMedecinRequest(BaseModel):
    medecin_id: int
    message: str | None = None

class ReponseDemandeMedecinRequest(BaseModel):
    demande_id: int
    decision: str
    date_rendez_vous: str | None = None
    heure_rendez_vous: str | None = None

@application.get("/")
def accueil():
    return {
        "message": "API Telemed Secure",
        "statut": "API opérationnelle"
    }

@application.post("/utilisateurs")
def creer_utilisateur(data: UtilisateurRequest):

    email = data.email.strip().lower()
    role = data.role.strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="Adresse email invalide"
        )

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Le mot de passe doit contenir au moins 8 caractères"
        )

    if role not in {"patient", "medecin"}:
        raise HTTPException(
            status_code=400,
            detail="Le rôle doit être patient ou medecin"
        )

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM utilisateurs
                WHERE email = %s
                """,
                (email,)
            )

            utilisateur_existant = cur.fetchone()

            if utilisateur_existant:
                raise HTTPException(
                    status_code=409,
                    detail="Cette adresse email est déjà utilisée"
                )

            password_hash = pwd_context.hash(data.password)

            cur.execute(
                """
                INSERT INTO utilisateurs
                    (email, password_hash, role, actif)
                VALUES
                    (%s, %s, %s, TRUE)
                RETURNING id, email, role, actif
                """,
                (email, password_hash, role)
            )

            utilisateur = cur.fetchone()

    return {
        "message": "Utilisateur créé avec succès",
        "id": utilisateur[0],
        "email": utilisateur[1],
        "role": utilisateur[2],
        "actif": utilisateur[3]
    }

@application.post("/login")
def login(data: LoginRequest):

    email = data.username.strip().lower()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, role, actif
                FROM utilisateurs
                WHERE email = %s
                """,
                (email,)
            )
            utilisateur = cur.fetchone()

    if not utilisateur:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    utilisateur_id, email_db, password_hash, role, actif = utilisateur

    if not actif:
        raise HTTPException(
            status_code=403,
            detail="Compte désactivé"
        )

    if not pwd_context.verify(
        data.password,
        password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects"
        )

    mfa_challenge = secrets.token_urlsafe(32)

    defis_mfa[mfa_challenge] = {
        "utilisateur_id": utilisateur_id,
        "email": email_db,
        "role": role,
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
        raise HTTPException(
            status_code=401,
            detail="Utilisateur non autorisé"
        )

    utilisateur_id, email, role, actif = utilisateur

    if not actif:
        raise HTTPException(
            status_code=403,
            detail="Compte désactivé"
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

    del defis_mfa[data.mfa_challenge]

    return {
        "message": "Authentification MFA réussie",
        "acces": "autorisé",
        "access_token": token,
        "token_type": "bearer"
    }


@application.get("/admin")
def espace_admin(
    utilisateur=Depends(obtenir_utilisateur_token)
):

    role = utilisateur["role"]

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
def acces_medecin_admin(
    utilisateur=Depends(obtenir_utilisateur_token)
):

    role = utilisateur["role"]

    verifier_role(
        role,
        "gerer_utilisateurs"
    )

    return {
        "message": "Accès autorisé",
        "role": role
    }

@application.post("/demandes-medecin")
def creer_demande_medecin(
    data: DemandeMedecinRequest,
    utilisateur=Depends(obtenir_utilisateur_token)
):
    verifier_role(utilisateur["role"], "voir_ses_donnees")

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
                    detail="Médecin introuvable"
                )

            cur.execute(
                """
                SELECT id
                FROM demandes_medecin
                WHERE patient_id = %s
                  AND medecin_id = %s
                  AND statut = 'EN_ATTENTE'
                """,
                (patient_id, medecin_id)
            )

            demande_existante = cur.fetchone()

            if demande_existante:
                raise HTTPException(
                    status_code=409,
                    detail="Une demande est déjà en attente pour ce médecin"
                )

            cur.execute(
                """
                INSERT INTO demandes_medecin
                    (patient_id, medecin_id, type_demande, origine, statut, message)
                VALUES
                    (%s, %s, 'principal', 'patient', 'EN_ATTENTE', %s)
                RETURNING id, date_demande
                """,
                (patient_id, medecin_id, data.message)
            )

            demande = cur.fetchone()

            cur.execute(
    """
    INSERT INTO notifications
        (utilisateur_id, type, message)
    VALUES
        (%s, %s, %s)
    """,
    (
        medecin_id,
        "DEMANDE_MEDECIN",
        "Un patient souhaite vous choisir comme médecin principal."
    )
)

    enregistrer_action(
        utilisateur_id=patient_id,
        action="DEMANDE_MEDECIN_CREEE",
        ressource=f"demande_medecin_{demande[0]}",
        adresse_ip="127.0.0.1"
    )

    return {
        "message": "Demande envoyée au médecin",
        "demande_id": demande[0],
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "statut": "EN_ATTENTE",
        "date_demande": demande[1]
    }

@application.post("/demandes-medecin/repondre")
def repondre_demande_medecin(
    demande: ReponseDemandeMedecinRequest,
    utilisateur=Depends(obtenir_utilisateur_token)
):
    # Seul un médecin peut répondre à une demande
    if utilisateur["role"] != "medecin":
        raise HTTPException(
            status_code=403,
            detail="Accès réservé aux médecins"
        )

    # Vérification de la décision
    if demande.decision not in {"ACCEPTEE", "REFUSEE"}:
        raise HTTPException(
            status_code=400,
            detail="La décision doit être ACCEPTEE ou REFUSEE"
        )

    # Si le médecin accepte, la date et l'heure du rendez-vous sont obligatoires
    if demande.decision == "ACCEPTEE":
        if not demande.date_rendez_vous or not demande.heure_rendez_vous:
            raise HTTPException(
                status_code=400,
                detail="La date et l'heure du rendez-vous sont obligatoires"
            )

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Vérifier que la demande appartient bien à ce médecin
            cur.execute(
                """
                SELECT patient_id, medecin_id, statut
                FROM demandes_medecin
                WHERE id = %s
                """,
                (demande.demande_id,)
            )

            demande_existante = cur.fetchone()

            if not demande_existante:
                raise HTTPException(
                    status_code=404,
                    detail="Demande introuvable"
                )

            patient_id, medecin_id, statut = demande_existante

            if medecin_id != utilisateur["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="Cette demande ne vous est pas destinée"
                )

            if statut != "EN_ATTENTE":
                raise HTTPException(
                    status_code=409,
                    detail="Cette demande a déjà été traitée"
                )

            # Refus
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
                        (utilisateur_id, type, message)
                    VALUES
                        (%s, 'REPONSE_MEDECIN',
                         'Votre demande de médecin principal a été refusée.')
                    """,
                    (patient_id,)
                )

                enregistrer_action(
                    utilisateur["id"],
                    "DEMANDE_MEDECIN_REFUSEE",
                    f"demande:{demande.demande_id}"
                )

                conn.commit()

                return {
                    "message": "Demande refusée",
                    "demande_id": demande.demande_id,
                    "statut": "REFUSEE"
                }

            # Acceptation : vérifier qu'il n'existe pas déjà
            # un médecin principal actif pour ce patient
            cur.execute(
                """
                SELECT id, medecin_id
                FROM relations_patient_medecin
                WHERE patient_id = %s
                  AND type_relation = 'principal'
                  AND actif = TRUE
                """,
                (patient_id,)
            )

            relation_existante = cur.fetchone()

            if relation_existante:
                raise HTTPException(
                    status_code=409,
                    detail="Le patient possède déjà un médecin principal actif"
                )

            # Enregistrer la date et l'heure du rendez-vous
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

            # Créer la relation patient-médecin principale
            cur.execute(
                """
                INSERT INTO relations_patient_medecin
                    (patient_id, medecin_id, type_relation, actif)
                VALUES
                    (%s, %s, 'principal', TRUE)
                """,
                (patient_id, utilisateur["id"])
            )

            # Notification du patient avec le rendez-vous
            cur.execute(
                """
                INSERT INTO notifications
                    (utilisateur_id, type, message)
                VALUES
                    (
                        %s,
                        'RENDEZ_VOUS_MEDECIN',
                        %s
                    )
                """,
                (
                    patient_id,
                    f"Votre demande de médecin principal a été acceptée. "
                    f"Rendez-vous prévu le {demande.date_rendez_vous} "
                    f"à {demande.heure_rendez_vous}."
                )
            )

            enregistrer_action(
                utilisateur["id"],
                "DEMANDE_MEDECIN_ACCEPTEE",
                f"demande:{demande.demande_id}"
            )

            conn.commit()

    return {
        "message": "Demande acceptée et rendez-vous enregistré",
        "demande_id": demande.demande_id,
        "statut": "ACCEPTEE",
        "date_rendez_vous": demande.date_rendez_vous,
        "heure_rendez_vous": demande.heure_rendez_vous
    }

@application.get("/notifications")
def obtenir_notifications(
    utilisateur=Depends(obtenir_utilisateur_token)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, type, message, lue, date_creation
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

@application.get("/demandes-medecin")
def obtenir_demandes_medecin(
    utilisateur=Depends(obtenir_utilisateur_token)
):
    # Seul un médecin peut consulter les demandes qui lui sont adressées
    if utilisateur["role"] != "medecin":
        raise HTTPException(
            status_code=403,
            detail="Accès réservé aux médecins"
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
                JOIN utilisateurs u ON u.id = d.patient_id
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


@application.get("/dossiers/{patient_id}/{medecin_id}/{dossier_id}")
def acces_dossier(
    patient_id: int,
    medecin_id: int,
    dossier_id: int,
    utilisateur=Depends(obtenir_utilisateur_token)
):

    role = utilisateur["role"]

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
            dossier_id=dossier_id,
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
        "dossier_id": dossier_id,
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