const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

const message = document.getElementById("message-securite");
const liste = document.getElementById("liste-audit");

async function chargerJournalAudit() {
    message.textContent = "Chargement du journal d'audit...";
    liste.innerHTML = "";

    try {
        const reponse = await fetch(
            "http://127.0.0.1:8000/audit",
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
                donnees.detail ||
                "Impossible de consulter le journal d'audit."
            );
        }

        if (donnees.evenements.length === 0) {
            liste.innerHTML =
                "<p>Aucun événement enregistré.</p>";
        } else {
            donnees.evenements.forEach(function (evenement) {

                const carte = document.createElement("section");

                carte.className = "carte";

                carte.innerHTML = `
                    <h3>${evenement.action}</h3>
                    <p><strong>Utilisateur :</strong> ${evenement.email}</p>
                    <p><strong>Rôle :</strong> ${evenement.role}</p>
                    <p><strong>Ressource :</strong> ${evenement.ressource || "Non précisée"}</p>
                    <p><strong>Adresse IP :</strong> ${evenement.adresse_ip || "Non précisée"}</p>
                    <p><strong>Date :</strong> ${evenement.date_action}</p>
                `;

                liste.appendChild(carte);
            });
        }

        message.textContent =
            `${donnees.nombre} événement(s) d'audit chargé(s).`;

    } catch (erreur) {
        message.textContent = erreur.message;
    }
}