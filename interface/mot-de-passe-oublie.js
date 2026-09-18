const formulaire = document.getElementById("formulaire-recuperation");
const identifiant = document.getElementById("identifiant-recuperation");
const bouton = document.getElementById("bouton-recuperation");
const message = document.getElementById("message-recuperation");

formulaire.addEventListener("submit", async function (event) {

    event.preventDefault();

    const valeur = identifiant.value.trim();

    if (!valeur) {
        message.textContent =
            "Veuillez saisir votre adresse e-mail ou votre numéro de téléphone.";

        message.className = "message erreur";
        return;
    }

    bouton.disabled = true;

    message.textContent =
        "Traitement de votre demande...";

    message.className = "message chargement";

    try {

        const reponse = await fetch(
            "http://127.0.0.1:8000/mot-de-passe-oublie",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    identifiant: valeur
                })
            }
        );

        const donnees = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail ||
                "Une erreur est survenue."
            );
        }

        if (donnees.jeton_demo) {

            sessionStorage.setItem(
                "jeton_reinitialisation",
                donnees.jeton_demo
            );

            window.location.href =
                "nouveau-mot-de-passe.html";

            return;
        }

        message.textContent =
            donnees.message;

        message.className =
            "message information";

    } catch (erreur) {

        message.textContent =
            erreur.message ||
            "Impossible de traiter la demande.";

        message.className =
            "message erreur";

    } finally {

        bouton.disabled = false;
    }

});