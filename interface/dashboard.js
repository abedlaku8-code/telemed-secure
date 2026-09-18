const token = sessionStorage.getItem("access_token");

const roleElement = document.getElementById("role-utilisateur");
const titreDashboard = document.getElementById("titre-dashboard");
const descriptionDashboard = document.getElementById(
    "description-dashboard"
);

const messageDashboard = document.getElementById(
    "message-dashboard"
);


/*
 * Vérification de la session.
 *
 * Sans token JWT, l'utilisateur ne peut pas accéder
 * au tableau de bord.
 */
if (!token) {
    window.location.href = "index.html";
}


/*
 * Récupération du rôle enregistré après authentification.
 *
 * Le rôle n'est jamais choisi par l'utilisateur.
 * Les permissions réelles restent contrôlées par le backend.
 */
const role = sessionStorage.getItem("role");


function afficherRole(roleUtilisateur) {

    if (!roleUtilisateur) {

        roleElement.textContent = "Utilisateur";
        roleElement.className = "badge-role";

        return;
    }


    const roles = {

        patient: {
            nom: "Patient",
            description:
                "Consultez vos informations et les services médicaux autorisés."
        },

        medecin: {
            nom: "Médecin",
            description:
                "Gérez les consultations et consultez les dossiers autorisés."
        },

        admin: {
            nom: "Administrateur",
            description:
                "Gérez la plateforme et les fonctions d'administration autorisées."
        }

    };


    const informations = roles[roleUtilisateur];


    if (informations) {

        roleElement.textContent = informations.nom;

        roleElement.className =
            "badge-role role-" + roleUtilisateur;

        descriptionDashboard.textContent =
            informations.description;

    } else {

        roleElement.textContent = "Utilisateur";

        roleElement.className =
            "badge-role";

    }

}


/*
 * Affichage du rôle connu côté interface.
 */
afficherRole(role);


/*
 * Affichage d'un message de bienvenue.
 */
if (role) {

    messageDashboard.textContent =
        "Votre session est active et protégée par authentification MFA.";

    messageDashboard.className =
        "message succes";

}