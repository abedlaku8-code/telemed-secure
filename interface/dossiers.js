const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

const message = document.getElementById("message-dossier");
const resultat = document.getElementById("resultat-dossier");

async function consulterDossier() {
    message.textContent = "Chargement du dossier...";
    resultat.textContent = "";

    try {
        const reponse = await fetch(
            "http://127.0.0.1:8000/dossiers/1/4/8",
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const donnees = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail || "Accès au dossier refusé."
            );
        }

        let contenu = donnees.contenu;

        try {
            contenu = JSON.parse(contenu);
        } catch (erreur) {
            // Le contenu reste affiché tel quel
        }

        resultat.textContent =
            typeof contenu === "object"
                ? JSON.stringify(contenu, null, 2)
                : contenu;

        message.textContent =
            "Dossier médical chargé avec succès.";

    } catch (erreur) {
        message.textContent = erreur.message;
    }
}