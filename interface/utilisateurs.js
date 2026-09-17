const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

const message = document.getElementById("message-utilisateurs");
const resultat = document.getElementById("resultat-utilisateurs");

async function verifierAdministration() {
    message.textContent = "Vérification des autorisations...";
    resultat.textContent = "";

    try {
        const reponse = await fetch(
            "http://127.0.0.1:8000/admin",
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
                donnees.detail || "Accès administratif refusé."
            );
        }

        resultat.textContent =
            JSON.stringify(donnees, null, 2);

        message.textContent =
            "Accès administratif autorisé.";

    } catch (erreur) {
        message.textContent = erreur.message;
    }
}