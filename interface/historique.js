const API_URL = "http://127.0.0.1:8000";

const token = sessionStorage.getItem("access_token");

const listeHistorique =
    document.getElementById("liste-historique");

const messageHistorique =
    document.getElementById("message-historique");


if (!token) {

    window.location.href = "connexion.html";

} else {

    chargerHistorique();

}


async function chargerHistorique() {

    try {

        const reponse = await fetch(
            `${API_URL}/historique`,
            {
                method: "GET",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );


        if (!reponse.ok) {

            if (reponse.status === 401) {

                sessionStorage.clear();

                window.location.href =
                    "connexion.html";

                return;
            }

            throw new Error(
                "Impossible de charger l'historique"
            );
        }


        const historique =
            await reponse.json();


        listeHistorique.innerHTML = "";


        if (!historique.length) {

            messageHistorique.textContent =
                "Aucune activité enregistrée.";

            return;
        }


        messageHistorique.textContent =
            `${historique.length} activité(s) récente(s).`;


        historique.forEach(
            evenement => {

                const ligne =
                    document.createElement("tr");


                const date =
                    document.createElement("td");

                date.textContent =
                    formaterDate(
                        evenement.date_action
                    );


                const action =
                    document.createElement("td");

                action.textContent =
                    traduireAction(
                        evenement.action
                    );


                const ressource =
                    document.createElement("td");

                ressource.textContent =
                    evenement.ressource || "—";


                const adresseIp =
                    document.createElement("td");

                adresseIp.textContent =
                    evenement.adresse_ip || "—";


                ligne.appendChild(date);

                ligne.appendChild(action);

                ligne.appendChild(ressource);

                ligne.appendChild(adresseIp);


                listeHistorique.appendChild(
                    ligne
                );

            }
        );

    } catch (erreur) {

        console.error(
            "Erreur historique :",
            erreur
        );

        messageHistorique.textContent =
            "Impossible de charger l'historique.";
    }

}


function formaterDate(date) {

    if (!date) {
        return "—";
    }

    return new Date(date).toLocaleString(
        "fr-FR"
    );
}


function traduireAction(action) {

    const traductions = {

        "CREATION_COMPTE":
            "Création du compte",

        "CONNEXION":
            "Connexion",

        "DECONNEXION":
            "Déconnexion",

        "CONSENTEMENT_DONNE":
            "Consentement accordé",

        "CONSENTEMENT_RETIRE":
            "Consentement retiré",

        "DEMANDE_MEDECIN_CREEE":
            "Demande de médecin créée",

        "DEMANDE_MEDECIN_ACCEPTEE":
            "Demande de médecin acceptée",

        "DEMANDE_MEDECIN_REFUSEE":
            "Demande de médecin refusée",

        "CONSULTATION_DOSSIER":
            "Consultation d'un dossier médical",

        "CONSULTATION_DOSSIER_SPECIALISTE":
            "Consultation d'un dossier médical",

        "CREATION_DOSSIER":
            "Création d'un dossier médical",

        "RECOMMANDATION_SPECIALISTE":
            "Recommandation d'un spécialiste",

        "RECOMMANDATION_SPECIALISTE_ACCEPTEE":
            "Recommandation de spécialiste acceptée",

        "RECOMMANDATION_SPECIALISTE_REFUSEE":
            "Recommandation de spécialiste refusée",

        "MODIFICATION_DOSSIER":
            "Modification d'un dossier médical",

        "SUPPRESSION_DOSSIER":
            "Suppression d'un dossier médical",

        "ACCES_REFUSE":
            "Accès refusé",

        "MFA_REUSSIE":
            "Authentification MFA réussie",

        "MFA_ECHEC":
            "Échec de l'authentification MFA"

    };


    return traductions[action] || action;
}