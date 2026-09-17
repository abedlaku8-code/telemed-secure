const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

const message = document.getElementById(
    "message-securite"
);

const liste = document.getElementById(
    "liste-audit"
);

function seDeconnecter() {
    sessionStorage.clear();
    window.location.href = "connexion.html";
}

async function chargerJournalAudit() {

    message.textContent =
        "Chargement du journal d'audit...";

    message.className = "";

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

            liste.innerHTML = `
                <section class="carte">
                    <h3>Aucun événement</h3>
                    <p>
                        Aucun événement d'audit n'est actuellement enregistré.
                    </p>
                </section>
            `;

        } else {

            donnees.evenements.forEach(
                function (evenement) {

                    const carte =
                        document.createElement("article");

                    carte.className =
                        "audit-evenement";

                    carte.innerHTML = `

                        <div class="audit-icone">
                            🔐
                        </div>

                        <div class="audit-contenu">

                            <h3>
                                ${evenement.action}
                            </h3>

                            <p>
                                <strong>Utilisateur :</strong>
                                ${evenement.email}
                            </p>

                            <p>
                                <strong>Rôle :</strong>
                                ${evenement.role}
                            </p>

                            <p>
                                <strong>Ressource :</strong>
                                ${evenement.ressource || "Non précisée"}
                            </p>

                            <p>
                                <strong>Adresse IP :</strong>
                                ${evenement.adresse_ip || "Non précisée"}
                            </p>

                        </div>

                        <div class="audit-date">
                            ${evenement.date_action}
                        </div>
                    `;

                    liste.appendChild(carte);
                }
            );
        }

        message.textContent =
            `${donnees.nombre} événement(s) d'audit chargé(s).`;

        message.className =
            "message-succes";

    } catch (erreur) {

        message.textContent =
            erreur.message;

        message.className =
            "message-erreur";
    }
}