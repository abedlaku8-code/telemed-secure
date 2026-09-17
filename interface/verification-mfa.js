const challenge =
    sessionStorage.getItem("mfa_challenge");

const message =
    document.getElementById("message-mfa");

const boutonAuthenticator =
    document.getElementById(
        "bouton-authenticator"
    );

if (!challenge) {
    window.location.href = "connexion.html";
}

boutonAuthenticator.addEventListener(
    "click",
    async function () {

        const code =
            document
                .getElementById("code-authenticator")
                .value
                .trim();

        if (!/^\d{6}$/.test(code)) {

            message.textContent =
                "Veuillez saisir un code à 6 chiffres.";

            message.className =
                "message-erreur";

            return;
        }

        message.textContent =
            "Vérification MFA en cours...";

        message.className = "";

        boutonAuthenticator.disabled = true;

        try {

            const reponse =
                await fetch(
                    "http://127.0.0.1:8000/mfa/authenticator",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            mfa_challenge:
                                challenge,

                            code: code
                        })
                    }
                );

            const resultat =
                await reponse.json();

            if (!reponse.ok) {

                throw new Error(
                    resultat.detail ||
                    "Échec de la vérification MFA."
                );
            }

            sessionStorage.setItem(
                "access_token",
                resultat.access_token
            );

            sessionStorage.removeItem(
                "mfa_challenge"
            );

            message.textContent =
                "Authentification réussie. Redirection...";

            message.className =
                "message-succes";

            window.location.href =
                "dashboard.html";

        } catch (erreur) {

            message.textContent =
                erreur.message;

            message.className =
                "message-erreur";

            boutonAuthenticator.disabled =
                false;
        }
    }
);