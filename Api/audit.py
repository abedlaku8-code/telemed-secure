# ==============================
# JOURNAL D'AUDIT ET TRAÇABILITÉ
# ==============================

from Api.database import get_connection


def enregistrer_action(
    utilisateur_id: int,
    action: str,
    ressource: str = None,
    adresse_ip: str = None
) -> dict:
    """Enregistre une action dans le journal d'audit PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO journal_audit
                    (utilisateur_id, action, ressource, adresse_ip)
                VALUES
                    (%s, %s, %s, %s)
                RETURNING id, date_action
                """,
                (
                    utilisateur_id,
                    action,
                    ressource,
                    adresse_ip
                )
            )

            resultat = cur.fetchone()

    return {
        "id": resultat[0],
        "utilisateur_id": utilisateur_id,
        "action": action,
        "ressource": ressource,
        "adresse_ip": adresse_ip,
        "date_action": resultat[1]
    }