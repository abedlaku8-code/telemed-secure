const formulaire = document.getElementById("inscription-form");
const message = document.getElementById("message-inscription");

formulaire.addEventListener("submit", async function (event) {
    event.preventDefault();

    const nom = document.getElementById("nom").value.trim();
    const prenom = document.getElementById("prenom").value.trim();
    const email = document.getElementById("email").value.trim();
    const telephone = document.getElementById("telephone").value.trim();
    const motDePasse = document.getElementById("mot_de_passe").value;
    const confirmation = document.getElementById(
        "confirmation_mot_de_passe"
    ).value;
    const role = document.getElementById("role").value;

    // --------------------------------------------------------
    // VALIDATION COTE FRONTEND
    // --------------------------------------------------------

    if (
        !nom ||
        !prenom ||
        !email ||
        !telephone ||
        !motDePasse ||
        !confirmation ||
        !role
    ) {
        message.textContent =
            "Veuillez remplir tous les champs.";
        message.className = "message erreur";
        return;
    }

    if (motDePasse.length < 8) {
        message.textContent =
            "Le mot de passe doit contenir au moins 8 caractères.";
        message.className = "message erreur";
        return;
    }

    if (motDePasse !== confirmation) {
        message.textContent =
            "Les deux mots de passe ne correspondent pas.";
        message.className = "message erreur";
        return;
    }

    if (!["patient", "medecin"].includes(role)) {
        message.textContent =
            "Veuillez sélectionner un type de compte valide.";
        message.className = "message erreur";
        return;
    }

    message.textContent =
        "Création de votre compte en cours...";
    message.className = "message chargement";

    try {
        const reponse = await fetch(
            "http://127.0.0.1:8000/utilisateurs",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    nom: nom,
                    prenom: prenom,
                    email: email,
                    telephone: telephone,
                    password: motDePasse,
                    role: role
                })
            }
        );

        const resultat = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail ||
                "Impossible de créer le compte."
            );
        }

        message.textContent =
            "Compte créé avec succès. Redirection vers la connexion...";
        message.className = "message succes";

        formulaire.reset();

        setTimeout(function () {
            window.location.href = "index.html";
        }, 1500);

    } catch (erreur) {

        console.error(
            "Erreur lors de la création du compte :",
            erreur
        );

        message.textContent = erreur.message;
        message.className = "message erreur";
    }
});