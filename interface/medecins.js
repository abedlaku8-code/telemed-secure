const API_URL = "http://127.0.0.1:8000";

const listeMedecins =
    document.getElementById("liste-medecins");

const listeDemandes =
    document.getElementById("liste-demandes");

const zoneDemande =
    document.getElementById("zone-demande-medecin");

const medecinSelectionne =
    document.getElementById("medecin-selectionne");

const texteDemande =
    document.getElementById("texte-demande");

const resultatDemande =
    document.getElementById("resultat-demande");
const boutonEnvoyer =
    document.getElementById("bouton-envoyer-demande");

const zoneChoixMedecin =
    document.getElementById("zone-choix-medecin");

let medecinChoisi = null;


function obtenirToken() {

    const token =
        sessionStorage.getItem("access_token");

    if (!token) {
        window.location.href = "index.html";
        return null;
    }

    return token;
}


async function chargerMedecins() {

    const token = obtenirToken();

    if (!token) {
        return;
    }

    try {

        const reponse = await fetch(
            `${API_URL}/medecins`,
            {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        const donnees = await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail ||
                "Impossible de charger les médecins."
            );
        }

        listeMedecins.innerHTML = "";

        if (
            !donnees.medecins ||
            donnees.medecins.length === 0
        ) {

            listeMedecins.innerHTML = `
                <div class="information-dossier">
                    Aucun médecin disponible actuellement.
                </div>
            `;

            return;
        }

        donnees.medecins.forEach(function (medecin) {

            const bloc =
                document.createElement("div");

            bloc.className =
                "information-dossier";

            bloc.innerHTML = `
                <strong>MÉDECIN</strong>

                <span>
                    Dr ${medecin.prenom}
                    ${medecin.nom}
                </span>

                <span>
                    ${medecin.email}
                </span>

                <button
                    type="button"
                    class="bouton-principal"
                    data-medecin-id="${medecin.id}"
                >
                    Choisir ce médecin
                </button>
            `;

            const bouton =
                bloc.querySelector("button");

            bouton.addEventListener(
                "click",
                function () {

                    selectionnerMedecin(medecin);
                }
            );

            listeMedecins.appendChild(bloc);
        });

    } catch (erreur) {

        console.error(erreur);

        listeMedecins.innerHTML = `
            <div class="message erreur">
                ${erreur.message}
            </div>
        `;
    }
}


function selectionnerMedecin(medecin) {

    medecinChoisi = medecin;

    medecinSelectionne.textContent =
        `Médecin sélectionné : Dr ${medecin.prenom} ${medecin.nom}`;

    zoneDemande.style.display = "block";

    zoneDemande.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


async function envoyerDemande() {

    const token = obtenirToken();

    if (!token || !medecinChoisi) {
        return;
    }

    boutonEnvoyer.disabled = true;

    boutonEnvoyer.textContent =
        "Envoi en cours...";

    resultatDemande.textContent = "";

    try {

        const message =
            exteDemande.value.trim();

        const reponse = await fetch(
            `${API_URL}/demandes-medecin`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Authorization":
                        "Bearer " + token
                },

                body: JSON.stringify({
                    medecin_id: medecinChoisi.id,
                    message: message || null
                })
            }
        );

        const donnees =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail ||
                "Impossible d'envoyer la demande."
            );
        }

        resultatDemande.textContent =
             donnees.message ||
            "Demande envoyée avec succès.";

        resultatDemande.className =
            "message succes";

        texteDemande.value = "";
        await chargerDemandes();

        } catch (erreur) {

        console.error(erreur);

        resultatDemande.textContent =
            erreur.message;

        resultatDemande.className =
            "message erreur";

    } finally {

        boutonEnvoyer.disabled = false;

        boutonEnvoyer.textContent =
            "Envoyer la demande";
    }
}


async function chargerDemandes() {

    const token = obtenirToken();

    if (!token) {
        return;
    }

    try {

        const reponse = await fetch(
            `${API_URL}/mes-demandes-medecin`,
            {
                method: "GET",

                headers: {
                    "Authorization":
                        "Bearer " + token
                }
            }
        );

        const donnees =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail ||
                "Impossible de charger les demandes."
            );
        }

        listeDemandes.innerHTML = "";

        if (
            !donnees.demandes ||
            donnees.demandes.length === 0
        ) {

            listeDemandes.innerHTML = `
                <div class="information-dossier">
                    Aucune demande envoyée.
                </div>
            `;

            return;
        }

        donnees.demandes.forEach(
            function (demande) {

                const bloc =
                    document.createElement("div");

                bloc.className =
                    "information-dossier";

                const statut =
                    demande.statut || "en_attente";

                let texteStatut =
                    "En attente";

                if (statut === "acceptee") {
                    texteStatut = "Acceptée";
                }

                if (statut === "refusee") {
                    texteStatut = "Refusée";
                }

                bloc.innerHTML = `
                    <strong>MÉDECIN</strong>

                    <span>
                        Dr ${demande.medecin_prenom}
                        ${demande.medecin_nom}
                    </span>

                    <strong>STATUT</strong>

                    <span>
                        ${texteStatut}
                    </span>

                    ${
                        demande.message
                        ? `
                            <strong>MESSAGE</strong>
                            <span>
                                ${demande.message}
                            </span>
                        `
                        : ""
                    }

                    ${
                        demande.date_rendez_vous
                        ? `
                            <strong>RENDEZ-VOUS</strong>
                            <span>
                                ${demande.date_rendez_vous}
                                ${
                                    demande.heure_rendez_vous
                                    ? " à " +
                                      demande.heure_rendez_vous
                                    : ""
                                }
                            </span>
                        `
                        : ""
                    }
                `;

                listeDemandes.appendChild(bloc);
            }
        );

    } catch (erreur) {

        console.error(erreur);

        listeDemandes.innerHTML = `
            <div class="message erreur">
                ${erreur.message}
            </div>
        `;
    }
}


if (boutonEnvoyer) {

    boutonEnvoyer.addEventListener(
        "click",
        envoyerDemande
    );
}

async function chargerDemandesMedecin() {

    const token = obtenirToken();

    if (!token) {
        return;
    }

    try {

        const reponse = await fetch(
            `${API_URL}/demandes-medecin`,
            {
                method: "GET",

                headers: {
                    "Authorization":
                        "Bearer " + token
                }
            }
        );

        const donnees =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail ||
                "Impossible de charger les demandes."
            );
        }

        listeDemandes.innerHTML = "";

        if (
            !donnees.demandes ||
            donnees.demandes.length === 0
        ) {

            listeDemandes.innerHTML = `
                <div class="information-dossier">
                    Aucune demande reçue.
                </div>
            `;

            return;
        }

        donnees.demandes.forEach(
            function (demande) {

                const bloc =
                    document.createElement("div");

                bloc.className =
                    "information-dossier";

                bloc.innerHTML = `
                    <strong>PATIENT</strong>

                    <span>
                        Patient #${demande.patient_id}
                    </span>

                    <strong>MESSAGE</strong>

                    <span>
                        ${
                            demande.message ||
                            "Aucun message"
                        }
                    </span>

                    <strong>STATUT</strong>

                    <span>
                        ${demande.statut}
                    </span>

                    ${
                        demande.statut === "EN_ATTENTE"
                        ? `
                            <button
                                type="button"
                                class="bouton-principal"
                                onclick="repondreDemande(
                                    ${demande.id},
                                    'ACCEPTEE'
                                )"
                            >
                                Accepter
                            </button>

                            <button
                                type="button"
                                class="bouton-deconnexion"
                                onclick="repondreDemande(
                                    ${demande.id},
                                    'REFUSEE'
                                )"
                            >
                                Refuser
                            </button>
                        `
                        : ""
                    }
                `;

                listeDemandes.appendChild(bloc);
            }
        );

    } catch (erreur) {

        console.error(erreur);

        listeDemandes.innerHTML = `
            <div class="message erreur">
                ${erreur.message}
            </div>
        `;
    }
}

async function repondreDemande(
    demandeId,
    decision
) {

    const token = obtenirToken();

    if (!token) {
        return;
    }

    let dateRendezVous = null;
    let heureRendezVous = null;

    if (decision === "ACCEPTEE") {

        dateRendezVous =
            prompt(
                "Date du rendez-vous (AAAA-MM-JJ) :"
            );

        if (!dateRendezVous) {
            return;
        }

        heureRendezVous =
            prompt(
                "Heure du rendez-vous (HH:MM) :"
            );

        if (!heureRendezVous) {
            return;
        }
    }

    try {

        const reponse = await fetch(
            `${API_URL}/demandes-medecin/repondre`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Authorization":
                        "Bearer " + token
                },

                body: JSON.stringify({
                    demande_id: demandeId,
                    decision: decision,
                    date_rendez_vous:
                        dateRendezVous,
                    heure_rendez_vous:
                        heureRendezVous
                })
            }
        );

        const donnees =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                donnees.detail ||
                "Impossible de répondre à la demande."
            );
        }

        alert(
            donnees.message ||
            "Réponse enregistrée."
        );

        await chargerDemandesMedecin();

    } catch (erreur) {

        console.error(erreur);

        alert(erreur.message);
    }
}

const titrePage =
    document.getElementById("titre-page-medecins");

const sousTitrePage =
    document.getElementById("sous-titre-page-medecins");

const roleUtilisateur =
    sessionStorage.getItem("role");

if (roleUtilisateur === "patient") {

    if (titrePage) {
        titrePage.textContent = "Mes médecins";
    }

    if (sousTitrePage) {
        sousTitrePage.textContent =
            "Choisissez un médecin et envoyez une demande de prise en charge.";
    }

} else if (roleUtilisateur === "medecin") {

    if (titrePage) {
        titrePage.textContent = "Mes demandes";
    }

    if (sousTitrePage) {
        sousTitrePage.textContent =
            "Consultez et traitez les demandes reçues des patients.";
    }

} else if (roleUtilisateur === "admin") {

    if (titrePage) {
        titrePage.textContent = "Mes demandes";
    }

    if (sousTitrePage) {
        sousTitrePage.textContent =
            "Suivi des demandes de prise en charge.";
    }
}

if (roleUtilisateur === "patient") {

    if (zoneChoixMedecin) {
        zoneChoixMedecin.style.display = "block";
    }

    chargerMedecins();
    chargerDemandes();

} else if (roleUtilisateur === "medecin") {

    if (zoneChoixMedecin) {
        zoneChoixMedecin.style.display = "none";
    }

    chargerDemandesMedecin();
}