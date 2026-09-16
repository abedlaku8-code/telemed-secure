# ==============================
# GESTION DES RÔLES ET PERMISSIONS
# ==============================

ROLES = {
    "admin": {
        "gerer_utilisateurs",
        "gerer_roles",
        "voir_dossiers",
        "gerer_consentements",
    },

    "medecin": {
        "voir_dossiers",
        "gerer_consentements",
    },

    "patient": {
        "voir_ses_donnees",
        "gerer_son_consentement",
    },
}


def role_existe(role: str) -> bool:
    """Vérifie si le rôle existe."""
    return role in ROLES


def a_permission(role: str, permission: str) -> bool:
    """Vérifie si un rôle possède une permission."""
    return permission in ROLES.get(role, set())