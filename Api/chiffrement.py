# ==============================
# CHIFFREMENT DES DOSSIERS MÉDICAUX
# AES-256-GCM
# ==============================

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv


load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY absente du fichier .env")


try:
    KEY = base64.urlsafe_b64decode(ENCRYPTION_KEY)
except Exception as erreur:
    raise RuntimeError("ENCRYPTION_KEY invalide") from erreur


if len(KEY) != 32:
    raise RuntimeError("ENCRYPTION_KEY doit contenir 32 octets")


def chiffrer_dossier(contenu: str) -> str:
    """Chiffre le contenu d'un dossier médical avec AES-256-GCM."""

    nonce = os.urandom(12)
    aesgcm = AESGCM(KEY)

    donnees_chiffrees = aesgcm.encrypt(
        nonce,
        contenu.encode("utf-8"),
        None
    )

    resultat = nonce + donnees_chiffrees

    return base64.urlsafe_b64encode(resultat).decode("utf-8")


def dechiffrer_dossier(contenu_chiffre: str) -> str:
    """Déchiffre un dossier médical avec AES-256-GCM."""

    donnees = base64.urlsafe_b64decode(contenu_chiffre)

    nonce = donnees[:12]
    texte_chiffre = donnees[12:]

    aesgcm = AESGCM(KEY)

    contenu = aesgcm.decrypt(
        nonce,
        texte_chiffre,
        None
    )

    return contenu.decode("utf-8")