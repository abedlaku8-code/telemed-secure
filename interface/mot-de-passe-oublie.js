const formulaire =
    document.getElementById(
        "formulaire-recuperation"
    );

const identifiant =
    document.getElementById(
        "identifiant-recuperation"
    );

const bouton =
    document.getElementById(
        "bouton-recuperation"
    );

const message =
    document.getElementById(
        "message-recuperation"
    );


formulaire.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        const valeur =
            identifiant.value.trim();

        if (!valeur) {

            message.textContent =
                "Veuillez saisir votre adresse e-mail ou votre numéro de téléphone.";

            message.className =
                "message erreur";

            return;
        }


        bouton.disabled = true;

        message.textContent =
            "Préparation de la demande...";

        message.className =
            "message chargement";


        /*
         * La réinitialisation réelle sera connectée
         * au backend sécurisé ultérieurement.
         *
         * Aucun code de récupération, mot de passe
         * ou secret n'est généré côté navigateur.
         */

        setTimeout(function () {

            message.textContent =
                "La fonctionnalité de réinitialisation sécurisée sera disponible après l'intégration du service d'envoi.";

            message.className =
                "message information";

            bouton.disabled = false;

        }, 700);

    }
);