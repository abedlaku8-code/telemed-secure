
from Api.database import get_connection
from Api.chiffrement import chiffrer_dossier, dechiffrer_dossier


def creer_dossier(patient_id: int, contenu: str) -> dict:
    """Chiffre puis enregistre un dossier médical dans PostgreSQL."""

    contenu_chiffre = chiffrer_dossier(contenu)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dossiers_medicaux (patient_id, contenu_chiffre)
                VALUES (%s, %s)
                RETURNING id
                """,
                (patient_id, contenu_chiffre)
            )

            dossier_id = cur.fetchone()[0]

    return {
        "id": dossier_id,
        "patient_id": patient_id,
        "message": "Dossier médical chiffré et enregistré"
    }


def lire_dossier(
    patient_id: int,
    dossier_id: int,
    utilisateur_id: int = None,
    adresse_ip: str = None
) -> str:
    """Récupère, déchiffre et journalise la consultation d'un dossier médical."""

    if utilisateur_id is None:
        raise ValueError("Utilisateur non identifié")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT contenu_chiffre
                FROM dossiers_medicaux
                WHERE id = %s AND patient_id = %s
                """,
                (dossier_id, patient_id)
            )

            resultat = cur.fetchone()

    if not resultat:
        raise ValueError("Dossier médical introuvable")

    contenu = dechiffrer_dossier(resultat[0])

    # Journalisation de la consultation
    from Api.audit import enregistrer_action

    enregistrer_action(
        utilisateur_id=utilisateur_id,
        action="CONSULTATION_DOSSIER",
        ressource=f"dossier_{dossier_id}",
        adresse_ip=adresse_ip
    )

    return contenu

