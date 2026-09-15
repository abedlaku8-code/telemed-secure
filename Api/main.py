from fastapi import FastAPI

application = FastAPI(title="Telemed Secure API")


@application.get("/")
def accueil():
    return {
        "message": "API Telemed Secure",
        "statut": "API opérationnelle"
    }