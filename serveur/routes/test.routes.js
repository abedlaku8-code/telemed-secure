const express = require("express");

const routeur = express.Router();
console.log("Fichier test.routes.js chargé");

routeur.get("/test", (requete, reponse) => {
    reponse.json({
        message: "Route de test opérationnelle"
    });
});

module.exports = routeur;