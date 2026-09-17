const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

const message = document.getElementById(
    "message-utilisateurs"
);

const resultat = document.getElementById(
    "resultat-utilisateurs"
);

function seDeconnecter() {
    sessionStorage.clear();
    window.location.href = "connexion.html";
}

async function verifierAdministration() {

    message.textContent =
        "Vérification des autorisations...";

    message.className = "";

    resultat.innerHTML = "";
    resultat.style.display = "none";

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
                donnees.detail ||
                "Accès administratif refusé."
            );
        }

        resultat.innerHTML = `
            <div class="statut-rbac">

                <div class="statut-icone statut-autorise">
                    ✓
                </div>

                <div>
                    <strong>Accès administratif autorisé</strong>
                    <br>
                    <span class="badge badge-protege">
                        Autorisation valide
                    </span>
                </div>

            </div>

            <div class="details-rbac">

                <div class="detail-rbac">
                    <small>Rôle</small>
                    <strong>${donnees.role}</strong>
                </div>

                <div class="detail-rbac">
                    <small>Permission</small>
                    <strong>${donnees.permission}</strong>
                </div>

            </div>
        `;

        resultat.style.display = "block";

        message.textContent =
            "Vos autorisations ont été vérifiées.";

        message.className = "message-succes";

    } catch (erreur) {

        resultat.innerHTML = `
            <div class="statut-rbac">

                <div class="statut-icone statut-refuse">
                    !
                </div>

                <div>
                    <strong>Accès administratif refusé</strong>
                    <br>
                    <span class="badge badge-refuse">
                        Permission insuffisante
                    </span>
                </div>

            </div>
        `;

        resultat.style.display = "block";

        message.textContent =
            erreur.message;

        message.className =
            "message-erreur";
    }
}