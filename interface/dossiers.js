const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

const message = document.getElementById("message-dossier");
const resultat = document.getElementById("resultat-dossier");

function seDeconnecter() {
    sessionStorage.clear();
    window.location.href = "connexion.html";
}

async function consulterDossier() {

    message.textContent = "Chargement du dossier...";
    message.className = "";

    resultat.innerHTML = "";
    resultat.style.display = "none";

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
                donnees.detail ||
                "Accès au dossier refusé."
            );
        }

        let contenu = donnees.contenu;

        try {
            contenu = JSON.parse(contenu);
        } catch (erreur) {
            contenu = {
                contenu: contenu
            };
        }

        afficherDossier(contenu);

        message.textContent =
            "Dossier médical chargé avec succès.";

        message.className = "message-succes";

    } catch (erreur) {

        message.textContent = erreur.message;

        message.className = "message-erreur";

        resultat.style.display = "none";
    }
}

function afficherDossier(dossier) {

    const noms = {
        motif: "Motif",
        antecedents: "Antécédents",
        allergies: "Allergies",
        traitements: "Traitements",
        observations: "Observations",
        contenu: "Contenu"
    };

    let lignes = "";

    Object.entries(dossier).forEach(
        ([cle, valeur]) => {

            lignes += `
                <tr>
                    <td>${noms[cle] || cle}</td>
                    <td>${valeur ?? "Non renseigné"}</td>
                </tr>
            `;
        }
    );

    resultat.innerHTML = `
        <h3>Informations médicales</h3>

        <div class="tableau-conteneur">

            <table class="tableau-dossier">

                <thead>
                    <tr>
                        <th>Information</th>
                        <th>Donnée</th>
                    </tr>
                </thead>

                <tbody>
                    ${lignes}
                </tbody>

            </table>

        </div>
    `;

    resultat.style.display = "block";
}