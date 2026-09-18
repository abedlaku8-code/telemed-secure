const token = sessionStorage.getItem("access_token");

const message =
    document.getElementById("message-utilisateurs");

const resultat =
    document.getElementById("resultat-utilisateurs");

const bouton =
    document.getElementById(
        "bouton-verifier-administration"
    );


/*
 * Vérification de la session.
 */
if (!token) {
    window.location.href = "index.html";
}


/*
 * Affichage du résultat de la vérification RBAC.
 */
function afficherResultat(autorise, donnees) {

    resultat.innerHTML = "";

    const carte =
        document.createElement("div");

    carte.className =
        autorise
            ? "resultat-autorise"
            : "resultat-refuse";


    const icone =
        document.createElement("div");

    icone.className =
        "icone-resultat";

    icone.textContent =
        autorise ? "✓" : "×";


    const contenu =
        document.createElement("div");


    const titre =
        document.createElement("h3");

    titre.textContent =
        autorise
            ? "Accès administratif autorisé"
            : "Accès administratif refusé";


    const description =
        document.createElement("p");

    description.textContent =
        autorise
            ? (
                donnees.message ||
                "Votre compte possède les permissions nécessaires."
            )
            : (
                donnees.detail ||
                "Votre compte ne possède pas les permissions nécessaires."
            );


    contenu.appendChild(titre);
    contenu.appendChild(description);

    carte.appendChild(icone);
    carte.appendChild(contenu);

    resultat.appendChild(carte);
}


/*
 * Vérification des permissions administratives.
 */
async function verifierAdministration() {

    message.textContent =
        "Vérification des autorisations...";

    message.className =
        "message chargement";

    resultat.innerHTML = "";

    bouton.disabled = true;


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


        const donnees =
            await reponse.json();


        /*
         * Le backend reste l'autorité RBAC.
         */
        if (!reponse.ok) {

            afficherResultat(
                false,
                donnees
            );

            message.textContent =
                donnees.detail ||
                "Accès administratif refusé.";

            message.className =
                "message erreur";

            return;
        }


        afficherResultat(
            true,
            donnees
        );


        message.textContent =
            "Autorisation administrative validée.";

        message.className =
            "message succes";


    } catch (erreur) {

        console.error(
            "Erreur lors de la vérification RBAC :",
            erreur
        );


        message.textContent =
            "Impossible de vérifier les autorisations pour le moment.";

        message.className =
            "message erreur";


    } finally {

        bouton.disabled = false;

    }

}