# SMA — Système de Recommandation Orientation & Stages

Projet 6 — 4AISDR Module SMA Agentic AI  
REALISER PAR : Yasemine Aayat
---

## Architecture

```
5 agents spécialisés collaborent sous la supervision d'un Orchestrateur :

Étudiant → [Profileur] → profil structuré
                              ↓
                         [Chercheur] ──(tool calling)──→ offres candidates
                              ↓
                         [Matcher] ──(embeddings)──→ top offres scorées
                              ↓
                         [Conseiller] ──(LLM)──→ recommandations argumentées
                              ↓
                         [Coach] ──(SQLite)──→ suivi long-terme
```

## Installation

```bash
# 1. Cloner / télécharger le projet
cd sma_orientation

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les clés API
cp .env.example .env
# Éditez .env et ajoutez votre OPENAI_API_KEY ou ANTHROPIC_API_KEY
# 5. Lancer
python main.py
```

## Utilisation

```
Menu principal :
  1 — Nouvelle session (entretien + recommandations)
  2 — Charger un profil existant
  3 — Afficher les profils enregistrés
  4 — Mode démo (3 profils types prédéfinis)
```

## Technologies mobilisées

| Concept cours | Implémentation |
|---|---|
| Profilage conversationnel adaptatif | `agents/profileur.py` — Few-shot + CoT + mémoire |
| Tool calling | `agents/chercheur.py` — TOOLS_DEFINITION + exécution |
| Matching par embeddings | `tools/vector_store.py` — sentence-transformers + cosine |
| Argumentation des recommandations | `agents/conseiller.py` — génération structurée JSON |
| Mémoire long-terme | `memory/profil_store.py` — SQLite persistant |
| Orchestration inter-agents | `agents/orchestrateur.py` — flux de données coordonné |

## Structure des fichiers

```
sma_orientation/
├── main.py                  # Point d'entrée + menu
├── config.py                # Configuration centralisée
├── requirements.txt
├── .env.example
├── agents/
│   ├── base_agent.py        # Classe parente (abstraction LLM)
│   ├── orchestrateur.py     # Chef d'orchestre
│   ├── profileur.py         # Entretien conversationnel
│   ├── chercheur.py         # Recherche d'offres (tool calling)
│   ├── matcher.py           # Matching sémantique
│   ├── conseiller.py        # Recommandations argumentées
│   └── coach.py             # Suivi long-terme
├── tools/
│   ├── jobs_api.py          # Simulation API offres
│   └── vector_store.py      # Embeddings + scoring composite
├── memory/
│   └── profil_store.py      # Persistance SQLite
└── data/
    └── offres_simule.json   # Base de 10 offres simulées
```

## Algorithme de matching

Score composite = 0.6 × score_sémantique + 0.4 × score_filtres

Score filtres = 0.4 × overlap_compétences + 0.2 × score_langues + 0.2 × score_localisation + 0.2 × score_durée

## Discussion éthique

- **Biais de sélection** : la base d'offres simulée peut surreprésenter certains secteurs
- **Biais d'embeddings** : les modèles pré-entraînés peuvent favoriser certains profils linguistiques
- **Équité** : le système ne prend pas en compte le genre, l'âge ou l'origine — intentionnel
- **Transparence** : chaque recommandation est justifiée et les gaps sont explicités
- **Données personnelles** : les profils sont stockés localement, pas envoyés à des tiers (sauf LLM)

## Démo — 3 profils types

| Profil | Formation | Domaine |
|---|---|---|
| Yasmine El Fassi | Master IA | Data Science → Casablanca |
| Omar Benali | Licence Informatique | Développement Web → Remote |
| Sara Idrissi | Master NLP | NLP / Recherche → Flexible |

Lancez avec `python main.py` → option 4.
