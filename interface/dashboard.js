const token = sessionStorage.getItem("access_token");

if (!token) {
    window.location.href = "connexion.html";
}