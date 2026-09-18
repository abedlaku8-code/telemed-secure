const API_URL = "http://127.0.0.1:8000";

const token =
    sessionStorage.getItem("access_token");

const listeNotifications =
    document.getElementById("liste-notifications");

const messageNotifications =
    document.getElementById("message-notifications");


function afficherMessage(message, erreur = false) {

    if (!messageNotifications) {
        return;
    }

    messageNotifications.textContent = message;

    messageNotifications.style.color =
        erreur ? "#b91c1c" : "";
}


async function chargerNotifications() {

    if (!token) {
        afficherMessage(
            "Votre session a expiré. Veuillez vous reconnecter.",
            true
        );
        return;
    }

    try {

        const reponse =
            await fetch(`${API_URL}/notifications`, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

        const resultat =
            await reponse.json();

        if (!reponse.ok) {
            throw new Error(
                resultat.detail ||
                "Impossible de charger les notifications."
            );
        }

        const notifications =
            resultat.notifications || [];

        if (notifications.length === 0) {

            afficherMessage(
                "Aucune notification pour le moment."
            );

            return;
        }

        afficherMessage("");

        listeNotifications.innerHTML = "";

        notifications.forEach(function (notification) {

            const carte =
                document.createElement("article");

            carte.className =
                "carte-notification";

            const titre =
                document.createElement("h3");

            titre.textContent =
                notification.type ||
                "Notification";

            const contenu =
                document.createElement("p");

            contenu.textContent =
                notification.message ||
                "Aucun détail disponible.";

            const date =
                document.createElement("small");

            date.textContent =
                notification.date_creation
                    ? new Date(
                        notification.date_creation
                    ).toLocaleString("fr-FR")
                    : "Date non disponible";

            carte.appendChild(titre);
            carte.appendChild(contenu);
            carte.appendChild(date);

            listeNotifications.appendChild(carte);

        });

    } catch (erreur) {

        console.error(
            "Erreur de chargement des notifications :",
            erreur
        );

        afficherMessage(
            erreur.message ||
            "Une erreur est survenue.",
            true
        );
    }
}


chargerNotifications();