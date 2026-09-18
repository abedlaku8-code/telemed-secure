const formulaire = document.getElementById("connexion-form");
const message = document.getElementById("message-connexion");

// Vider les champs à chaque ouverture de la page
window.addEventListener("pageshow", function () {
    document.getElementById("identifiant").value = "";
    document.getElementById("mot_de_passe").value = "";
    message.textContent = "";
    message.className = "message";
});

formulaire.addEventListener("submit", async function (event) {
    event.preventDefault();

    const identifiant = document.getElementById("identifiant").value.trim();
    const motDePasse = document.getElementById("mot_de_passe").value;

    if (!identifiant || !motDePasse) {
        message.textContent = "Veuillez remplir tous les champs.";
        message.className = "message erreur";
        return;
    }

    message.textContent = "Authentification en cours...";
    message.className = "message chargement";

    try {
        const reponse = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: identifiant,
                password: motDePasse
            })
        });

        const resultat = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail || "Identifiant ou mot de passe incorrect."
            );
        }

        sessionStorage.setItem(
            "mfa_challenge",
            resultat.mfa_challenge
        );

        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("role");
        sessionStorage.removeItem("mfa_method");

        message.textContent =
            "Première vérification réussie. Passage à la vérification MFA...";
        message.className = "message succes";

        window.location.href = "verification-mfa.html";

    } catch (erreur) {
        console.error("Erreur de connexion :", erreur);

        message.textContent = erreur.message;
        message.className = "message erreur";
    }
});