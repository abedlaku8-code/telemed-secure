const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}

function seDeconnecter() {
    sessionStorage.clear();
    window.location.href = "connexion.html";
}