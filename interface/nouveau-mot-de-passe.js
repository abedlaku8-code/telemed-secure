document.addEventListener("DOMContentLoaded", function () {
    const formulaire = document.getElementById("formulaire-nouveau-mot-de-passe");
    const motDePasseChamp = document.getElementById("nouveau-mot-de-passe");
    const confirmationChamp = document.getElementById("confirmation-mot-de-passe");
    const message = document.getElementById("message-reinitialisation");
    const bouton = document.getElementById("bouton-reinitialisation");

    if (!formulaire || !motDePasseChamp || !confirmationChamp || !message || !bouton) {
        console.error("Erreur : un ou plusieurs éléments du formulaire sont introuvables.");
        return;
    }

    formulaire.addEventListener("submit", async function (event) {
        event.preventDefault();

        message.textContent = "";
        message.style.color = "";

        const parametres = new URLSearchParams(window.location.search);
        const jeton = parametres.get("jeton");
        const nouveauMotDePasse = motDePasseChamp.value;
        const confirmation = confirmationChamp.value;

        if (!jeton) {
            message.textContent = "Le lien de réinitialisation est incomplet. Demandez un nouveau lien.";
            message.style.color = "red";
            return;
        }

        if (nouveauMotDePasse.length < 8) {
            message.textContent = "Le mot de passe doit contenir au moins 8 caractères.";
            message.style.color = "red";
            return;
        }

        if (nouveauMotDePasse !== confirmation) {
            message.textContent = "Les deux mots de passe ne correspondent pas.";
            message.style.color = "red";
            return;
        }

        bouton.disabled = true;
        bouton.textContent = "Réinitialisation en cours...";

        try {
            const reponse = await fetch(`${window.API_URL}/reinitialiser-mot-de-passe`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({
                    jeton: jeton,
                    nouveau_mot_de_passe: nouveauMotDePasse
                })
            });

            const resultat = await reponse.json();

            if (!reponse.ok) {
                throw new Error(resultat.detail || "La réinitialisation a échoué.");
            }

            message.textContent = resultat.message || "Votre mot de passe a été réinitialisé avec succès.";
            message.style.color = "green";
            formulaire.reset();
        } catch (erreur) {
            console.error("Erreur de réinitialisation :", erreur);
            message.textContent = erreur.message || "Impossible de contacter le serveur. Réessayez plus tard.";
            message.style.color = "red";
        } finally {
            bouton.disabled = false;
            bouton.textContent = "Réinitialiser le mot de passe";
        }
    });
});