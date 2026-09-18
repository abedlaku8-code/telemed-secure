const bouton = document.getElementById("bouton-consulter-dossier");
const message = document.getElementById("message-dossiers");
const resultat = document.getElementById("grille-informations-dossier");

async function consulterDossier() {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
        window.location.href = "index.html";
        return;
    }

    bouton.disabled = true;
    bouton.textContent = "Consultation en cours...";

    message.textContent = "";
    message.className = "message";

    try {
        const reponse = await fetch(
            "http://127.0.0.1:8000/dossiers/1/2/8",
            {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        const donnees = await reponse.json();

        console.log("Réponse du serveur :", donnees);

        if (!reponse.ok) {
            throw new Error(
                donnees.detail || "Consultation du dossier refusée."
            );
        }

        // Le backend renvoie le contenu médical sous forme de texte JSON.
        let contenu = {};

        try {
            contenu = JSON.parse(donnees.contenu);
        } catch (erreur) {
            console.error("Erreur lors de la lecture du contenu :", erreur);
            throw new Error("Impossible de lire les informations du dossier.");
        }

        afficherDossier(contenu);

        message.textContent =
            "Dossier consulté avec succès. L'accès a été journalisé.";
        message.className = "message succes";

    } catch (erreur) {
        console.error("Erreur de consultation :", erreur);

        message.textContent = erreur.message;
        message.className = "message erreur";

    } finally {
        bouton.disabled = false;
        bouton.textContent = "Consulter le dossier";
    }
}

function afficherDossier(donnees) {

    resultat.innerHTML = "";

    const informations = [
        {
            titre: "Motif",
            valeur: donnees.motif
        },
        {
            titre: "Allergies",
            valeur: donnees.allergies
        },
        {
            titre: "Traitements",
            valeur: donnees.traitements
        }
    ];

    informations.forEach(function (information) {

        const bloc = document.createElement("div");
        bloc.className = "information-dossier";

        const titre = document.createElement("strong");
        titre.textContent = information.titre;

        const valeur = document.createElement("span");
        valeur.textContent =
            information.valeur || "Non renseigné";

        bloc.appendChild(titre);
        bloc.appendChild(valeur);

        resultat.appendChild(bloc);
    });
}

window.consulterDossier = consulterDossier;