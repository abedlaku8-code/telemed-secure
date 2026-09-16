# ==============================
# GESTION DU CONSENTEMENT PATIENT
# ==============================

consentements = {}


def donner_consentement(patient_id: str, medecin_id: str) -> dict:
    """Enregistre le consentement d'un patient pour un médecin."""
    consentements[(patient_id, medecin_id)] = True

    return {
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "consentement": True
    }


def retirer_consentement(patient_id: str, medecin_id: str) -> dict:
    """Retire le consentement d'un patient pour un médecin."""
    consentements[(patient_id, medecin_id)] = False

    return {
        "patient_id": patient_id,
        "medecin_id": medecin_id,
        "consentement": False
    }


def consentement_valide(patient_id: str, medecin_id: str) -> bool:
    """Vérifie si le patient a donné son consentement."""
    return consentements.get((patient_id, medecin_id), False)