const API_URL = "http://127.0.0.1:8000";

const token =
    sessionStorage.getItem("access_token");

const listeConsentements =
    document.getElementById("liste-consentements");

let utilisateurConnecte = null;


/*
|--------------------------------------------------------------------------
| Récupération du profil connecté
|--------------------------------------------------------------------------
*/

async function chargerProfil() {

    const reponse =
        await fetch(`${API_URL}/profil`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

    const resultat =
        await reponse.json();

    if (!reponse.ok) {
        throw new Error(
            resultat.detail ||
            "Impossible de récupérer le profil."
        );
    }

    utilisateurConnecte = resultat;

    return resultat;
}


/*
|--------------------------------------------------------------------------
| Médecins disponibles
|--------------------------------------------------------------------------
*/

async function chargerConsentements() {

    if (!token) {

        listeConsentements.textContent =
            "Votre session a expiré. Veuillez vous reconnecter.";

        return;
    }

    try {

        const profil =
            await chargerProfil();

        if (profil.role !== "patient") {

            listeConsentements.innerHTML =
                "<p>Cette page est réservée aux patients.</p>";

            return;
        }


        const reponseMedecins =
            await fetch(
                `${API_URL}/medecins`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        const resultatMedecins =
            await reponseMedecins.json();

        if (!reponseMedecins.ok) {
            throw new Error(
                resultatMedecins.detail ||
                "Impossible de charger les médecins."
            );
        }

        const medecins =
            resultatMedecins.medecins || [];


        if (medecins.length === 0) {

            listeConsentements.innerHTML =
                "<p>Aucun médecin disponible.</p>";

            return;
        }


        listeConsentements.innerHTML = "";


        for (const medecin of medecins) {

            const carte =
                document.createElement("article");

            carte.className =
                "carte-notification";


            const nom =
                document.createElement("h3");

            nom.textContent =
                `Dr ${medecin.prenom || ""} ${medecin.nom || ""}`;


            const email =
                document.createElement("p");

            email.textContent =
                medecin.email || "";


            const statut =
                document.createElement("p");

            statut.textContent =
                "Vérification du consentement...";


            const bouton =
                document.createElement("button");

            bouton.type = "button";


            carte.appendChild(nom);
            carte.appendChild(email);
            carte.appendChild(statut);
            carte.appendChild(bouton);

            listeConsentements.appendChild(carte);


            await chargerStatutConsentement(
                medecin.id,
                statut,
                bouton
            );
        }

    } catch (erreur) {

        console.error(
            "Erreur consentements :",
            erreur
        );

        listeConsentements.innerHTML =
            `<p>${erreur.message}</p>`;
    }
}


/*
|--------------------------------------------------------------------------
| Vérification du consentement
|--------------------------------------------------------------------------
*/

async function chargerStatutConsentement(
    medecinId,
    elementStatut,
    bouton
) {

    try {

        const patientId =
            utilisateurConnecte.id;

        const reponse =
            await fetch(
                `${API_URL}/consentement/${patientId}/${medecinId}`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        const resultat =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail ||
                "Impossible de vérifier le consentement."
            );
        }


        if (resultat.consentement_valide === true) {

            elementStatut.textContent =
                "Consentement accordé";

            bouton.textContent =
                "Retirer le consentement";

            bouton.addEventListener(
                "click",
                function () {
                    retirerConsentement(
                        medecinId,
                        elementStatut,
                        bouton
                    );
                }
            );

        } else {

            elementStatut.textContent =
                "Consentement non accordé";

            bouton.textContent =
                "Donner le consentement";

            bouton.addEventListener(
                "click",
                function () {
                    donnerConsentement(
                        medecinId,
                        elementStatut,
                        bouton
                    );
                }
            );
        }

    } catch (erreur) {

        console.error(erreur);

        elementStatut.textContent =
            "Impossible de vérifier le consentement.";

        bouton.textContent =
            "Réessayer";
    }
}


/*
|--------------------------------------------------------------------------
| Donner le consentement
|--------------------------------------------------------------------------
*/

async function donnerConsentement(
    medecinId,
    elementStatut,
    bouton
) {

    try {

        const patientId =
            utilisateurConnecte.id;

        const reponse =
            await fetch(
                `${API_URL}/consentement/${patientId}/${medecinId}`,
                {
                    method: "POST",
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        const resultat =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail ||
                "Impossible de donner le consentement."
            );
        }

        elementStatut.textContent =
            "Consentement accordé";

        bouton.textContent =
            "Retirer le consentement";

        bouton.onclick = function () {

            retirerConsentement(
                medecinId,
                elementStatut,
                bouton
            );

        };

    } catch (erreur) {

        alert(erreur.message);
    }
}


/*
|--------------------------------------------------------------------------
| Retirer le consentement
|--------------------------------------------------------------------------
*/

async function retirerConsentement(
    medecinId,
    elementStatut,
    bouton
) {

    if (
        !confirm(
            "Voulez-vous réellement retirer ce consentement ?"
        )
    ) {
        return;
    }

    try {

        const patientId =
            utilisateurConnecte.id;

        const reponse =
            await fetch(
                `${API_URL}/consentement/${patientId}/${medecinId}`,
                {
                    method: "DELETE",
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        const resultat =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail ||
                "Impossible de retirer le consentement."
            );
        }

        elementStatut.textContent =
            "Consentement non accordé";

        bouton.textContent =
            "Donner le consentement";

        bouton.onclick = function () {

            donnerConsentement(
                medecinId,
                elementStatut,
                bouton
            );

        };

    } catch (erreur) {

        alert(erreur.message);
    }
}


chargerConsentements();