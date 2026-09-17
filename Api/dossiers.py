import json
from Api.database import get_connection
from Api.chiffrement import chiffrer_dossier, dechiffrer_dossier


def creer_dossier(
    patient_id: int,
    contenu: str = "",
    motif: str = None,
    antecedents: str = None,
    allergies: str = None,
    traitements: str = None,
    observations: str = None
) -> dict:
    """Chiffre puis enregistre un dossier médical dans PostgreSQL."""

    # Si des informations structurées sont fournies,
    # elles sont regroupées dans un objet JSON.
    if any([
        motif,
        antecedents,
        allergies,
        traitements,
        observations
    ]):
        dossier = {
            "motif": motif,
            "antecedents": antecedents,
            "allergies": allergies,
            "traitements": traitements,
            "observations": observations
        }

        contenu = json.dumps(
            dossier,
            ensure_ascii=False
        )

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
def lire_dossier_specialiste(
    patient_id: int,
    dossier_id: int,
    utilisateur_id: int = None,
    adresse_ip: str = None
) -> str:
    """Retourne uniquement les informations nécessaires au spécialiste."""

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

    try:
        dossier = json.loads(contenu)

        dossier_minimise = {
            "motif": dossier.get("motif"),
            "allergies": dossier.get("allergies"),
            "traitements": dossier.get("traitements")
        }

        contenu = json.dumps(
            dossier_minimise,
            ensure_ascii=False
        )

    except (json.JSONDecodeError, TypeError):
        # Les anciens dossiers non structurés restent accessibles.
        pass

    # Journalisation spécifique de l'accès du spécialiste.
    from Api.audit import enregistrer_action

    enregistrer_action(
        utilisateur_id=utilisateur_id,
        action="CONSULTATION_DOSSIER_SPECIALISTE",
        ressource=f"dossier_{dossier_id}",
        adresse_ip=adresse_ip
    )

    return contenu
