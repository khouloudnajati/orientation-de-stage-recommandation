"""
vector_store.py — Indexation des offres avec embeddings et matching sémantique
Utilise sentence-transformers en local (gratuit, pas d'API key nécessaire).
"""

import json
import numpy as np
from typing import Optional


class VectorStore:
    """
    Gère l'indexation et la recherche sémantique des offres de stages
    via des embeddings sentence-transformers.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialise le vector store.
        Le modèle est téléchargé automatiquement au premier lancement (~90MB).
        """
        print("  Chargement du modèle d'embeddings...")
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers non installé. "
                "Lancez : pip install sentence-transformers"
            )

        self.offres: list[dict] = []
        self.embeddings: Optional[np.ndarray] = None
        print("  Modèle chargé.")

    def _texte_offre(self, offre: dict) -> str:
        """Construit la représentation textuelle d'une offre pour l'embedding."""
        parties = [
            offre.get("titre", ""),
            offre.get("domaine", ""),
            offre.get("secteur", ""),
            offre.get("description", ""),
            "Compétences: " + ", ".join(offre.get("competences_requises", [])),
            "Soft skills: " + ", ".join(offre.get("soft_skills", [])),
        ]
        return " | ".join(p for p in parties if p.strip())

    def _texte_profil(self, profil: dict) -> str:
        """Construit la représentation textuelle d'un profil pour l'embedding."""
        parties = [
            f"Formation: {profil.get('formation', '')}",
            f"Domaine d'intérêt: {profil.get('domaine_interet', '')}",
            "Compétences techniques: " + ", ".join(profil.get("competences_techniques", [])),
            "Soft skills: " + ", ".join(profil.get("soft_skills", [])),
            f"Projet professionnel: {profil.get('projet_professionnel', '')}",
            f"Secteur préféré: {profil.get('secteur_prefere', '')}",
        ]
        return " | ".join(p for p in parties if p.strip() and p.split(": ", 1)[-1].strip())

    def indexer_offres(self, offres: list[dict]):
        """Embed et indexe toutes les offres en mémoire."""
        self.offres = offres
        textes = [self._texte_offre(o) for o in offres]
        print(f"  Indexation de {len(textes)} offres...")
        self.embeddings = self.model.encode(textes, normalize_embeddings=True)
        print("  Indexation terminée.")

    def rechercher_similaires(
        self,
        profil: dict,
        top_k: int = 10,
        seuil: float = 0.2
    ) -> list[tuple[dict, float]]:
        """
        Cherche les offres les plus similaires au profil via cosine similarity.

        Returns:
            Liste de (offre, score) triée par score décroissant
        """
        if self.embeddings is None or len(self.offres) == 0:
            return []

        # Embedding du profil
        texte_p = self._texte_profil(profil)
        embed_profil = self.model.encode([texte_p], normalize_embeddings=True)[0]

        # Cosine similarity (les embeddings sont normalisés → produit scalaire suffit)
        scores = np.dot(self.embeddings, embed_profil)

        # Tri et filtrage
        indices_tries = np.argsort(scores)[::-1]
        resultats = []
        for idx in indices_tries[:top_k * 2]:  # prendre 2x pour filtrer après
            score = float(scores[idx])
            if score >= seuil:
                resultats.append((self.offres[idx], round(score, 4)))
            if len(resultats) >= top_k:
                break

        return resultats

    def charger_depuis_json(self, chemin: str):
        """Charge et indexe les offres depuis un fichier JSON."""
        with open(chemin, "r", encoding="utf-8") as f:
            offres = json.load(f)
        self.indexer_offres(offres)
        return len(offres)


def calculer_score_global(
    offre: dict,
    profil: dict,
    score_semantique: float,
    poids_sem: float = 0.6,
    poids_filtres: float = 0.4
) -> dict:
    """
    Calcule un score composite combinant:
    - Similarité sémantique (embeddings)
    - Score de filtres durs (localisation, langues, durée)
    - Overlap de compétences

    Returns:
        Dictionnaire avec scores détaillés et score global
    """
    scores = {}

    # 1. Score sémantique
    scores["semantique"] = score_semantique

    # 2. Score langues (% de langues requises maîtrisées)
    langues_requises = set(l.lower() for l in offre.get("langues", []))
    langues_profil = set(l.lower() for l in profil.get("langues", []))
    if langues_requises:
        scores["langues"] = len(langues_requises & langues_profil) / len(langues_requises)
    else:
        scores["langues"] = 1.0

    # 3. Score compétences (overlap)
    comps_requises = set(c.lower() for c in offre.get("competences_requises", []))
    comps_profil = set(c.lower() for c in profil.get("competences_techniques", []))
    if comps_requises:
        scores["competences"] = len(comps_requises & comps_profil) / len(comps_requises)
    else:
        scores["competences"] = 0.5

    # 4. Score localisation
    localisation_pref = profil.get("localisation_preferee", "").lower()
    offre_loc = offre.get("localisation", "").lower()
    offre_remote = offre.get("remote", False)
    profil_remote = profil.get("accepte_remote", False)

    if not localisation_pref or localisation_pref in ["toutes", "flexible"]:
        scores["localisation"] = 1.0
    elif localisation_pref in offre_loc:
        scores["localisation"] = 1.0
    elif offre_remote and profil_remote:
        scores["localisation"] = 0.9
    else:
        scores["localisation"] = 0.3

    # 5. Score durée
    duree_min = profil.get("duree_min_mois", 1)
    duree_max = profil.get("duree_max_mois", 12)
    offre_duree = offre.get("duree_mois", 6)
    if duree_min <= offre_duree <= duree_max:
        scores["duree"] = 1.0
    elif abs(offre_duree - duree_min) <= 1 or abs(offre_duree - duree_max) <= 1:
        scores["duree"] = 0.7
    else:
        scores["duree"] = 0.3

    # Score composite filtres (moyenne pondérée)
    score_filtres = (
        scores["langues"] * 0.2 +
        scores["competences"] * 0.4 +
        scores["localisation"] * 0.2 +
        scores["duree"] * 0.2
    )

    # Score global
    scores["filtres"] = round(score_filtres, 4)
    scores["global"] = round(
        poids_sem * scores["semantique"] + poids_filtres * score_filtres, 4
    )

    # Compétences manquantes (pour le plan d'action)
    scores["competences_manquantes"] = list(comps_requises - comps_profil)
    scores["competences_communes"] = list(comps_requises & comps_profil)

    return scores
