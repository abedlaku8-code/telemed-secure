const token = sessionStorage.getItem("access_token");

const message = document.getElementById("message-securite");
const liste = document.getElementById("liste-audit");
const resume = document.getElementById("resume-audit");
const bouton = document.getElementById("bouton-charger-audit");


/*
 * Vérification de la session.
 */
if (!token) {
    window.location.href = "index.html";
}


/*
 * Protection contre l'injection HTML.
 *
 * Les données du journal proviennent du serveur.
 * Elles sont donc affichées avec textContent.
 */
function creerCellule(valeur) {

    const cellule = document.createElement("td");

    cellule.textContent =
        valeur === null ||
        valeur === undefined ||
        valeur === ""
            ? "—"
            : String(valeur);

    return cellule;
}


/*
 * Chargement du journal d'audit.
 */
async function chargerJournalAudit() {

    message.textContent =
        "Chargement du journal d'audit...";

    message.className =
        "message chargement";

    liste.innerHTML = "";

    resume.textContent =
        "Chargement en cours...";

    bouton.disabled = true;


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


        const evenements =
            Array.isArray(donnees.evenements)
                ? donnees.evenements
                : [];


        /*
         * Aucun événement.
         */
        if (evenements.length === 0) {

            resume.textContent =
                "Aucun événement enregistré.";

            message.textContent =
                "Le journal d'audit ne contient aucun événement.";

            message.className =
                "message information";

            return;
        }


        /*
         * Création des lignes du tableau.
         */
        evenements.forEach(function (evenement) {

            const ligne =
                document.createElement("tr");


            ligne.appendChild(
                creerCellule(evenement.action)
            );


            ligne.appendChild(
                creerCellule(evenement.email)
            );


            ligne.appendChild(
                creerCellule(evenement.role)
            );


            ligne.appendChild(
                creerCellule(evenement.ressource)
            );


            ligne.appendChild(
                creerCellule(evenement.adresse_ip)
            );


            ligne.appendChild(
                creerCellule(evenement.date_action)
            );


            liste.appendChild(ligne);

        });


        /*
         * Résumé du nombre d'événements.
         */
        resume.textContent =
            `${donnees.nombre || evenements.length} événement(s) d'audit chargé(s).`;


        message.textContent =
            "Journal d'audit chargé avec succès.";

        message.className =
            "message succes";


    } catch (erreur) {

        console.error(
            "Erreur lors du chargement du journal d'audit :",
            erreur
        );


        message.textContent =
            erreur.message;

        message.className =
            "message erreur";


        resume.textContent =
            "Journal indisponible.";

    } finally {

        bouton.disabled = false;

    }

}