document.addEventListener("DOMContentLoaded", function () {


const formulaire = document.getElementById("connexion-form");
const message = document.getElementById("message-connexion");
const identifiantChamp =
    document.getElementById("email") ||
    document.getElementById("identifiant");
const motDePasseChamp = document.getElementById("mot_de_passe");

// Vérification des éléments HTML
if (!formulaire) {
    console.error("Erreur : formulaire connexion-form introuvable.");
    return;
}

if (!message) {
    console.error("Erreur : élément message-connexion introuvable.");
    return;
}

if (!identifiantChamp) {
    console.error("Erreur : champ identifiant introuvable.");
    return;
}

if (!motDePasseChamp) {
    console.error("Erreur : champ mot_de_passe introuvable.");
    return;
}

// Vider les champs à l'ouverture de la page
identifiantChamp.value = "";
motDePasseChamp.value = "";
message.textContent = "";
message.className = "message";

formulaire.addEventListener("submit", async function (event) {
    event.preventDefault();

    const identifiant = identifiantChamp.value.trim();
    const motDePasse = motDePasseChamp.value;

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
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                username: identifiant,
                password: motDePasse
            })
        });

        const resultat = await reponse.json();

        console.log("Réponse API :", resultat);

        if (!reponse.ok) {
            throw new Error(
                resultat.detail || "Identifiant ou mot de passe incorrect."
            );
        }

        if (resultat.mfa_requis && resultat.mfa_challenge) {

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

            setTimeout(function () {
                window.location.href = "verification-mfa.html";
            }, 500);

        } else {
            throw new Error(
                "La réponse du serveur ne contient pas les informations MFA attendues."
            );
        }

    } catch (erreur) {

        console.error("Erreur de connexion :", erreur);

        message.textContent =
            erreur.message || "Une erreur est survenue.";

        message.className = "message erreur";
    }
});


});
