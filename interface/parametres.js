const token = sessionStorage.getItem("access_token");

if (!token) {

    window.location.href = "connexion.html";

} else {

    try {

        const parties = token.split(".");

        const donnees =
            JSON.parse(
                atob(
                    parties[1]
                        .replace(/-/g, "+")
                        .replace(/_/g, "/")
                )
            );


        const email =
            donnees.sub || "Utilisateur";

        const role =
            donnees.role || "Utilisateur";


        const roles = {

            admin: "Administrateur",

            medecin: "Médecin",

            patient: "Patient"

        };


        const emailCompte =
            document.getElementById(
                "email-compte"
            );

        const roleCompte =
            document.getElementById(
                "role-compte"
            );


        if (emailCompte) {

            emailCompte.textContent =
                email;

        }


        if (roleCompte) {

            roleCompte.textContent =
                roles[role] || role;

        }

    } catch (erreur) {

        console.error(
            "Erreur lors de la lecture du profil :",
            erreur
        );

    }

}