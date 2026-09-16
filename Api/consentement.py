# ==============================
# GESTION DU CONSENTEMENT PATIENT
# PostgreSQL
# ==============================

from Api.database import get_connection


def donner_consentement(patient_id: int, medecin_id: int) -> dict:
    """Enregistre ou met à jour le consentement du patient."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO consentements (patient_id, medecin_id, accord)
                VALUES (%s, %s, TRUE)
                ON CONFLICT (patient_id, medecin_id)
                DO UPDATE SET
                    accord = TRUE,
                    date_consentement = CURRENT_TIMESTAMP
                """,
                (patient_id, medecin_id)
            )

    from Api.audit import enregistrer_action

    enregistrer_action(
        utilisateur_id=patient_id,
        action="CONSENTEMENT_DONNE",
        ressource=f"patient_{patient_id}_medecin_{medecin_id}",
        adresse_ip="127.0.0.1"
    )
    return {
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "consentement": True
    }


def retirer_consentement(patient_id: int, medecin_id: int) -> dict:
    """Retire le consentement du patient."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE consentements
                SET accord = FALSE,
                    date_consentement = CURRENT_TIMESTAMP
                WHERE patient_id = %s
                  AND medecin_id = %s
                """,
                (patient_id, medecin_id)
            )
    from Api.audit import enregistrer_action

    enregistrer_action(
        utilisateur_id=patient_id,
        action="CONSENTEMENT_RETIRE",
        ressource=f"patient_{patient_id}_medecin_{medecin_id}",
        adresse_ip="127.0.0.1"
    )

    return {
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "consentement": False
    }


def consentement_valide(patient_id: int, medecin_id: int) -> bool:
    """Vérifie dans PostgreSQL si le consentement est valide."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT accord
                FROM consentements
                WHERE patient_id = %s
                  AND medecin_id = %s
                """,
                (patient_id, medecin_id)
            )

            resultat = cur.fetchone()

    return bool(resultat and resultat[0])