const formulaire = document.getElementById("connexion-form");
const message = document.getElementById("message-connexion");

formulaire.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const motDePasse = document.getElementById("mot_de_passe").value;

    message.textContent = "Connexion en cours...";

    try {
        const reponse = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: email,
                password: motDePasse
            })
        });

        const resultat = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail || "Échec de la connexion"
            );
        }

        sessionStorage.setItem(
            "mfa_challenge",
            resultat.mfa_challenge
        );

        window.location.href = "verification-mfa.html";

    } catch (erreur) {
        message.textContent = erreur.message;
    }
});