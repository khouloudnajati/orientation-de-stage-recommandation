# 🎓 Explication Détaillée du Projet : Système Multi-Agents d'Orientation (SMA)

Ce document est un guide complet pour vous aider à comprendre chaque partie de votre projet. Il vous sera très utile pour préparer votre soutenance et répondre aux questions du jury.

---

## 1. L'Architecture Globale

Votre projet est basé sur une architecture de **Système Multi-Agents (SMA)**. Au lieu d'avoir un seul gros programme qui fait tout, la tâche est divisée entre plusieurs petits "robots" (les agents), chacun ayant une spécialité précise.

*   **`app.py` (L'Interface Utilisateur)** : C'est le point d'entrée. Il utilise **Streamlit** pour créer l'interface web. C'est ici que l'on gère l'affichage (le chat, les onglets, les boutons).
*   **`orchestrateur.py` (Le Chef d'Orchestre)** : C'est le cerveau central. Il s'occupe de faire travailler les agents dans le bon ordre. Il s'assure que le profil récolté par le *Profileur* est bien envoyé au *Chercheur*, dont les résultats sont envoyés au *Matcher*, etc.
*   **`base_agent.py` (Le Cœur IA)** : C'est la classe parente de tous vos agents. Elle gère la communication directe avec l'API **Google Gemini**. Elle s'occupe d'envoyer les prompts, de conserver l'historique des conversations et de gérer les erreurs techniques.

---

## 2. Les 5 Agents Spécialisés

Ce sont les véritables acteurs de votre projet. Chacun hérite de la classe `BaseAgent`.

### 🗣️ 1. L'Agent Profileur (`profileur.py`)
*   **Son Rôle** : Mener un entretien avec l'étudiant de manière naturelle pour récolter ses informations (compétences, ville, durée de stage).
*   **Technique IA utilisée** : Le **Few-Shot Prompting**. Dans son prompt système, on lui donne des exemples de "bonnes" et "mauvaises" réponses pour lui apprendre à être conversationnel et à ne pas ressembler à un formulaire administratif.
*   **Résultat** : Quand il a fini, il génère un objet **JSON** structuré contenant toutes les données de l'étudiant.

### 🕵️‍♂️ 2. L'Agent Chercheur (`chercheur.py`)
*   **Son Rôle** : Trouver les offres de stage qui correspondent grossièrement aux compétences de l'étudiant.
*   **Technique IA utilisée** : Le **Tool Calling** (Appel d'outil). Cet agent a la capacité d'exécuter du vrai code Python (la fonction `rechercher_offres` de `jobs_api.py`) pour interroger votre base d'offres `offres_simule.json`. Il fait le pont entre le monde du texte (LLM) et la base de données brute.
*   *Note pour la démo : Nous avons mis un système de Fallback pour interroger la BDD directement si Gemini plante, ce qui rend le système ultra-fiable.*

### ⚡ 3. L'Agent Matcher (`matcher.py` & `vector_store.py`)
*   **Son Rôle** : Trier et noter les offres trouvées par le chercheur pour ne garder que le top 5.
*   **Technique IA utilisée** : La **Recherche Sémantique (Embeddings)**. Le Matcher utilise la bibliothèque `sentence-transformers` (`all-MiniLM-L6-v2`) pour transformer le texte du profil et le texte des offres en vecteurs mathématiques. 
*   **Le Score** : Il calcule un score global composé à 60% de similarité sémantique (Cosinus) et à 40% de filtres durs (si la ville ou la durée correspondent).

### 💡 4. L'Agent Conseiller (`conseiller.py`)
*   **Son Rôle** : Expliquer *pourquoi* une offre a été choisie et comment combler les lacunes (gaps).
*   **Technique IA utilisée** : La **Génération Structurée**. On force le modèle LLM à répondre sous format JSON strict pour pouvoir extraire et afficher proprement les "Points forts", les "Compétences manquantes" et un "Plan d'action" (ex: un cours Coursera à suivre) dans de jolies boîtes sur Streamlit.

### 🏋️ 5. L'Agent Coach Évolution (`coach.py`)
*   **Son Rôle** : Suivre l'étudiant dans le temps.
*   **Technique IA utilisée** : La **Mémoire à long terme**. Le Coach utilise une base de données SQLite (`profil_store.py`) pour sauvegarder le profil de l'étudiant. S'il revient plusieurs mois plus tard, le Coach compare les anciennes compétences avec les nouvelles, le félicite pour ses progrès et propose de nouvelles opportunités.

---

## 3. Gestion des Données

*   **`jobs_api.py`** : Simule une vraie API d'offres d'emploi (comme Indeed ou LinkedIn). Elle filtre le fichier `data/offres_simule.json` en fonction des critères de recherche.
*   **`profil_store.py` (Base de données locale)** : Utilise **SQLite3** pour sauvegarder l'historique des sessions et le profil de l'utilisateur. C'est grâce à cela que le système "se souvient" de vous.

---

## 💡 Conseils de présentation pour la Soutenance

Si le jury vous pose des questions, voici les 3 arguments forts de votre projet à mettre en avant :
1. **L'adaptabilité** : Ce n'est pas un simple script "if/else". Grâce aux "Agents", le comportement et les questions s'adaptent en direct à l'étudiant.
2. **L'hybridation (Le point fort du Matcher)** : Vous n'utilisez pas *que* l'IA générative. Le Matching combine des mathématiques vectorielles (Embeddings via un petit modèle open-source) avec des règles métiers classiques (localisation). C'est très robuste et professionnel.
3. **L'explicabilité (Éthique de l'IA)** : Dans le domaine de l'IA, il est crucial de pouvoir expliquer une décision (pour éviter les boîtes noires). Votre Agent Conseiller justifie *chaque* recommandation, ce qui rend votre système éthique et digne de confiance.
