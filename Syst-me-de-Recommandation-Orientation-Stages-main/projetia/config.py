"""
config.py — Configuration centrale du SMA
Mettez vos clés API dans un fichier .env à la racine
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Clés API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Choisissez votre provider : "openai", "anthropic" ou "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# Modèles

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")     # rapide et gratuit (tier gratuit disponible)

# --- Embeddings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # modèle local sentence-transformers

# --- Persistance ---
DB_PATH = "memory/profiles.db"
CHROMA_PATH = "memory/chroma_db"
OFFRES_PATH = "data/offres_simule.json"

# --- Paramètres de matching ---
TOP_K_OFFRES = 5          # nombre de recommandations finales
SEUIL_SIMILARITE = 0.3    # score minimum pour considérer une offre
POIDS_SEMANTIQUE = 0.6    # 60% sémantique, 40% filtres durs
POIDS_FILTRES = 0.4
