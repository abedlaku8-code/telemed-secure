const boutonDeconnexion =
    document.getElementById("bouton-deconnexion");

const role = sessionStorage.getItem("role");

const lienAdministration =
    document.getElementById("lien-administration");

const lienAudit =
    document.getElementById("lien-audit");

const lienMesMedecins =
    document.getElementById("lien-mes-medecins");

const lienConsentements =
    document.getElementById("lien-consentements");

const lienMesDemandes =
    document.getElementById("lien-mes-demandes");

const accesAdministration =
    document.getElementById("acces-administration");

const accesHistorique =
    document.getElementById("acces-historique");


/*
|--------------------------------------------------------------------------
| Navigation selon le rôle
|--------------------------------------------------------------------------
*/

if (role === "patient") {

    /*
     * Patient :
     * - Dashboard
     * - Dossiers
     * - Mes demandes
     * - Mes médecins
     * - Consentements
     * - Notifications
     * - Journal / Historique
     * - Paramètres
     */

    if (lienMesDemandes) {
        lienMesDemandes.href = "medecins.html";
    }

    if (lienMesMedecins) {
        lienMesMedecins.style.display = "flex";
    }

    if (lienConsentements) {
        lienConsentements.style.display = "flex";
    }

    if (lienAdministration) {
        lienAdministration.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

    if (accesAdministration) {
        accesAdministration.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

}


else if (role === "medecin") {

    /*
     * Médecin :
     * - Dashboard
     * - Dossiers
     * - Mes demandes
     * - Notifications
     * - Journal / Historique
     * - Paramètres
     */

    if (lienMesDemandes) {
        lienMesDemandes.href = "medecins.html";
    }

    if (lienMesMedecins) {
        lienMesMedecins.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

    if (lienConsentements) {
        lienConsentements.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

    if (lienAdministration) {
        lienAdministration.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

    if (accesAdministration) {
        accesAdministration.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

}


else if (role === "admin") {

    /*
     * Administrateur :
     * - Dashboard
     * - Dossiers
     * - Mes demandes
     * - Notifications
     * - Journal / Historique
     * - Paramètres
     * - Administration
     */

    if (lienMesDemandes) {
        lienMesDemandes.href = "medecins.html";
    }

    if (lienMesMedecins) {
        lienMesMedecins.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

    if (lienConsentements) {
        lienConsentements.style.setProperty(
            "display",
            "none",
            "important"
        );
    }

    if (lienAdministration) {
        lienAdministration.style.display = "flex";
    }

    if (accesAdministration) {
        accesAdministration.style.display = "flex";
    }

}

/*
|--------------------------------------------------------------------------
| Navigation selon le rôle
|--------------------------------------------------------------------------
*/

function masquerElement(element) {

    if (element) {
        element.style.setProperty(
            "display",
            "none",
            "important"
        );
    }
}

function afficherElement(element) {

    if (element) {
        element.style.setProperty(
            "display",
            "flex",
            "important"
        );
    }
}


/*
|--------------------------------------------------------------------------
| Liens communs
|--------------------------------------------------------------------------
*/

if (lienMesDemandes) {
    lienMesDemandes.href = "medecins.html";
}
if (lienAudit) {
    lienAudit.href = "historique.html";
}

/*
|--------------------------------------------------------------------------
| Patient
|--------------------------------------------------------------------------
*/

if (role === "patient") {

    afficherElement(lienMesMedecins);
    afficherElement(lienConsentements);

    masquerElement(lienAdministration);
    masquerElement(accesAdministration);

}


/*
|--------------------------------------------------------------------------
| Médecin
|--------------------------------------------------------------------------
*/

else if (role === "medecin") {

    masquerElement(lienMesMedecins);
    masquerElement(lienConsentements);

    masquerElement(lienAdministration);
    masquerElement(accesAdministration);

}


/*
|--------------------------------------------------------------------------
| Administrateur
|--------------------------------------------------------------------------
*/

else if (role === "admin") {

    masquerElement(lienMesMedecins);
    masquerElement(lienConsentements);

    afficherElement(lienAdministration);
    afficherElement(accesAdministration);

}


/*
|--------------------------------------------------------------------------
| Aucun rôle valide
|--------------------------------------------------------------------------
*/

else {

    masquerElement(lienMesMedecins);
    masquerElement(lienConsentements);
    masquerElement(lienAdministration);
    masquerElement(accesAdministration);

}

/*
|--------------------------------------------------------------------------
| Profil utilisateur
|--------------------------------------------------------------------------
*/

function afficherProfilUtilisateur() {

    const nomUtilisateur =
        document.getElementById("nom-utilisateur");

    const roleUtilisateur =
        document.getElementById("role-utilisateur");

    const initialesUtilisateur =
        document.getElementById("initiales-utilisateur");

    const token =
        sessionStorage.getItem("access_token");

    if (!token) {
        return;
    }

    try {

        const parties = token.split(".");

        const donnees =
            JSON.parse(
                atob(
                    parties[1]
                        .replace(/-/g, "+")
                        .replace(/_/g, "/")
                )
            );

        const email =
            donnees.sub || "Utilisateur";

        const roles = {
            admin: "Administrateur",
            medecin: "Médecin",
            patient: "Patient"
        };

        if (nomUtilisateur) {
            nomUtilisateur.textContent = email;
        }

        if (roleUtilisateur) {
            roleUtilisateur.textContent =
                roles[donnees.role] || "Utilisateur";
        }

        if (initialesUtilisateur) {
            initialesUtilisateur.textContent =
                email.substring(0, 2).toUpperCase();
        }

    } catch (erreur) {

        console.error(
            "Erreur lors de la lecture du profil :",
            erreur
        );
    }
}

afficherProfilUtilisateur();


/*
|--------------------------------------------------------------------------
| Déconnexion
|--------------------------------------------------------------------------
*/

if (boutonDeconnexion) {

    boutonDeconnexion.addEventListener(
        "click",
        function () {

            sessionStorage.removeItem("access_token");
            sessionStorage.removeItem("mfa_challenge");
            sessionStorage.removeItem("mfa_method");
            sessionStorage.removeItem("role");

            window.location.href = "index.html";
        }
    );
}