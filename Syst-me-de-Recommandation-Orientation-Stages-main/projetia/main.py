"""
config.py — Configuration centrale du SMA
Projet 6 — 4AISDR Module SMA Agentic AI
Compatible : Gemini
"""
print("MAIN DEMARRE")
import os
from dotenv import load_dotenv
from orchestrateur import Orchestrateur
# Charger les variables du fichier .env
load_dotenv()

# =========================================================
# PROVIDER LLM
# =========================================================
# Valeurs possibles :
#   - "openai"
#   - "anthropic"
#   - "gemini"
# =========================================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")



# =========================================================
# GEMINI
# =========================================================

GEMINI_API_KEY = os.getenv("AIzaSyAhIo61LG1_noQJLfYVnC18ZZS8ndWmIBw", "")

# Modèles Gemini possibles :
# - gemini-2.0-flash
# - gemini-1.5-flash
# - gemini-1.5-pro

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.0-flash"
)

# =========================================================
# EMBEDDINGS
# =========================================================

# Modèle local sentence-transformers
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# =========================================================
# PERSISTANCE
# =========================================================

# Base SQLite des profils
DB_PATH = "memory/profiles.db"

# Base vectorielle ChromaDB
CHROMA_PATH = "memory/chroma_db"

# Base des offres simulées
OFFRES_PATH = "data/offres_simule.json"

# =========================================================
# PARAMÈTRES DE MATCHING
# =========================================================

# Nombre final de recommandations
TOP_K_OFFRES = 5

# Score minimum pour accepter une offre
SEUIL_SIMILARITE = 0.3

# Pondérations
POIDS_SEMANTIQUE = 0.6
POIDS_FILTRES = 0.4

# =========================================================
# PARAMÈTRES APPLICATION
# =========================================================

DEBUG = True

MAX_TOKENS = 2048
TEMPERATURE = 0.7

# =========================================================
# LOGS / AFFICHAGE
# =========================================================

ENABLE_LOGS = True
LOG_LEVEL = "INFO"

# =========================================================
# VALIDATION CONFIG
# =========================================================

def afficher_config():
    """Affiche la configuration active."""

    print("======================================")
    print(" CONFIGURATION SMA")
    print("======================================")
    print(f"Provider LLM      : {LLM_PROVIDER}")

    if  LLM_PROVIDER == "gemini":
        print(f"Modèle Gemini     : {GEMINI_MODEL}")

    print(f"Embedding Model   : {EMBEDDING_MODEL}")
    print(f"DB SQLite         : {DB_PATH}")
    print(f"ChromaDB          : {CHROMA_PATH}")
    print(f"Base Offres       : {OFFRES_PATH}")
    print("======================================")


def main():
    print("IMPORT ORCHESTRATEUR")
    print("ORCHESTRATEUR IMPORTE")
    afficher_config()
    
    orch = Orchestrateur()
    orch.demarrer_session()

if __name__ == "__main__":
    main()