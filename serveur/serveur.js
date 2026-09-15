const express = require("express");

const application = express();
const routeTest = require("./routes/test.routes");
const PORT = 3000;

// Autorise le serveur à recevoir des données au format JSON.
application.use(express.json());
application.use("/api/test", routeTest);

// Route d'accueil pour vérifier que le serveur fonctionne.
application.get("/", (requete, reponse) => {
    reponse.json({
        message: "Plateforme de télémédecine simulée et sécurisée",
        statut: "Serveur opérationnel"
    });
});

// Démarrage du serveur.
application.listen(PORT, () => {
    console.log(`Serveur démarré sur http://localhost:${PORT}`);
});