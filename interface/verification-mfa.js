const challenge = sessionStorage.getItem("mfa_challenge");

const message = document.getElementById("message-mfa");

const boutonAuthenticator = document.getElementById(
    "bouton-authenticator"
);

const boutonEmail = document.getElementById(
    "bouton-email"
);

const boutonVerifierEmail = document.getElementById(
    "bouton-verifier-email"
);

const zoneCodeEmail = document.getElementById(
    "zone-code-email"
);


// Vérifier que le challenge MFA existe
if (!challenge) {
    window.location.href = "connexion.html";
}


// Vérification avec Authenticator
boutonAuthenticator.addEventListener("click", async function () {

    const code = document.getElementById(
        "code-authenticator"
    ).value;

    if (!code) {
        message.textContent = "Veuillez entrer le code Authenticator.";
        return;
    }

    message.textContent = "Vérification en cours...";

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
                resultat.detail || "Code Authenticator incorrect."
            );
        }

        localStorage.setItem(
            "access_token",
            resultat.access_token
        );

        sessionStorage.removeItem("mfa_challenge");

        window.location.href = "dashboard.html";

    } catch (erreur) {

        message.textContent = erreur.message;

    }
});


// Demander un code par e-mail
boutonEmail.addEventListener("click", async function () {

    message.textContent = "Envoi du code en cours...";

    try {

        const reponse = await fetch(
            "http://127.0.0.1:8000/mfa/email/send",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    mfa_challenge: challenge
                })
            }
        );

        const resultat = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail || "Impossible d'envoyer le code."
            );
        }

        zoneCodeEmail.style.display = "block";

        message.textContent =
            "Le code de vérification a été envoyé par e-mail.";

    } catch (erreur) {

        message.textContent = erreur.message;

    }
});


// Vérifier le code reçu par e-mail
boutonVerifierEmail.addEventListener(
    "click",
    async function () {

        const code = document.getElementById(
            "code-email"
        ).value;

        if (!code) {
            message.textContent =
                "Veuillez entrer le code reçu par e-mail.";
            return;
        }

        message.textContent =
            "Vérification du code en cours...";

        try {

            const reponse = await fetch(
                "http://127.0.0.1:8000/mfa/email/verify",
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
                    "Code e-mail incorrect ou expiré."
                );
            }

            localStorage.setItem(
                "access_token",
                resultat.access_token
            );

            sessionStorage.removeItem("mfa_challenge");

            window.location.href = "dashboard.html";

        } catch (erreur) {

            message.textContent = erreur.message;

        }
    }
);
