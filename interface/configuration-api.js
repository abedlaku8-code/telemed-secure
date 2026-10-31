/**
 * Configuration centralisée de l'API Telemed Secure.
 * Détection automatique de l'environnement.
 */

(function () {
    const hote = window.location.hostname;

    if (hote === "localhost" || hote === "127.0.0.1") {
        window.API_URL = "http://127.0.0.1:8000";
        console.log("Telemed Secure : environnement local");
    } else {
        window.API_URL = "https://telemed-secure-api-v2.onrender.com";
        console.log("Telemed Secure : environnement en ligne");
    }
})();