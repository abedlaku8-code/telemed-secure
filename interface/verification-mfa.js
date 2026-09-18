const challenge = sessionStorage.getItem("mfa_challenge");

const formulaire = document.getElementById("mfa-form");
const codeMfa = document.getElementById("code-mfa");
const message = document.getElementById("message-mfa");

if (!formulaire || !codeMfa || !message) {
    console.error(
        "Erreur : un élément de la page MFA est introuvable."
    );
} else {

    formulaire.addEventListener("submit", async function (event) {

        event.preventDefault();

        const code = codeMfa.value.trim();

        if (!/^\d{6}$/.test(code)) {

            message.textContent =
                "Veuillez saisir un code à 6 chiffres.";

            message.className =
                "message erreur";

            return;
        }

        if (!challenge) {

            message.textContent =
                "Session MFA introuvable. Veuillez recommencer la connexion.";

            message.className =
                "message erreur";

            return;
        }

        message.textContent =
            "Vérification du code en cours...";

        message.className =
            "message chargement";

        const bouton =
            formulaire.querySelector("button[type='submit']");

        if (bouton) {
            bouton.disabled = true;
        }

        try {

            const reponse = await fetch(
                "http://127.0.0.1:8000/mfa/authenticator",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        mfa_challenge: challenge,
                        code: code
                    })
                }
            );

            const resultat = await reponse.json();

            if (!reponse.ok) {

                throw new Error(
                    resultat.detail ||
                    "Le code MFA est incorrect."
                );
            }

            if (!resultat.access_token) {

                throw new Error(
                    "Le serveur n'a pas retourné de jeton d'accès."
                );
            }

            sessionStorage.setItem(
                "access_token",
                resultat.access_token
            );

            /*
             * Récupération du rôle contenu
             * dans le JWT.
             */
            function obtenirRoleDepuisToken(token) {

                try {

                    const parties = token.split(".");

                    if (parties.length !== 3) {
                        return null;
                    }

                    const payloadBase64 = parties[1]
                        .replace(/-/g, "+")
                        .replace(/_/g, "/");

                    const payload = JSON.parse(
                        decodeURIComponent(
                            atob(payloadBase64)
                                .split("")
                                .map(function (caractere) {
                                    return (
                                        "%" +
                                        (
                                            "00" +
                                            caractere
                                                .charCodeAt(0)
                                                .toString(16)
                                        ).slice(-2)
                                    );
                                })
                                .join("")
                        )
                    );

                    return payload.role || null;

                } catch (erreur) {

                    console.error(
                        "Erreur de lecture du rôle :",
                        erreur
                    );

                    return null;
                }
            }

            const role =
                obtenirRoleDepuisToken(
                    resultat.access_token
                );

            if (!role) {

                sessionStorage.removeItem(
                    "access_token"
                );

                throw new Error(
                    "Le rôle du compte n'a pas pu être vérifié."
                );
            }

            const rolesAutorises = [
                "patient",
                "medecin",
                "admin"
            ];

            if (!rolesAutorises.includes(role)) {

                sessionStorage.removeItem(
                    "access_token"
                );

                throw new Error(
                    "Le rôle du compte n'est pas autorisé."
                );
            }

            sessionStorage.setItem(
                "role",
                role
            );

            sessionStorage.setItem(
                "mfa_method",
                "authenticator"
            );

            sessionStorage.removeItem(
                "mfa_challenge"
            );

            message.textContent =
                "Authentification réussie. Ouverture de votre espace...";

            message.className =
                "message succes";

            setTimeout(function () {

                window.location.href =
                    "dashboard.html";

            }, 500);

        } catch (erreur) {

            console.error(
                "Erreur de vérification MFA :",
                erreur
            );

            message.textContent =
                erreur.message ||
                "Une erreur est survenue.";

            message.className =
                "message erreur";

            if (bouton) {
                bouton.disabled = false;
            }
        }
    });
}