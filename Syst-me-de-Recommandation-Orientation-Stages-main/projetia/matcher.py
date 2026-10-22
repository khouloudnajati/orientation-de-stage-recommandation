"""
agents/matcher.py — Agent Matcher
Calcule la similarité profil-offre via embeddings et scoring composite.
Classe et filtre les opportunités pour présenter les meilleures.
"""

from vector_store import VectorStore, calculer_score_global
import config


class AgentMatcher:
    """
    Agent de matching sémantique entre profil étudiant et offres de stages.
    Combine embeddings (sémantique) et filtres durs (contraintes pratiques).
    """

    def __init__(self, offres_path: str = None):
        self.vector_store = VectorStore(model_name=config.EMBEDDING_MODEL)
        self.offres_indexees = False
        self.offres_path = offres_path or config.OFFRES_PATH

    def indexer_offres(self, offres: list[dict] = None):
        """Indexe les offres (depuis liste ou fichier JSON)."""
        if offres:
            self.vector_store.indexer_offres(offres)
        else:
            nb = self.vector_store.charger_depuis_json(self.offres_path)
            print(f"  [Matcher] {nb} offres indexées depuis {self.offres_path}")
        self.offres_indexees = True

    def matcher(
        self,
        profil: dict,
        offres_candidates: list[dict],
        top_k: int = None
    ) -> list[dict]:
        """
        Effectue le matching complet profil-offres.

        Pipeline :
        1. Embedding du profil
        2. Similarité cosinus avec toutes les offres
        3. Score composite (sémantique + filtres)
        4. Classement final

        Returns:
            Top K offres avec scores détaillés
        """
        top_k = top_k or config.TOP_K_OFFRES

        if not self.offres_indexees:
            print("  [Matcher] Indexation des offres candidates...")
            self.vector_store.indexer_offres(offres_candidates)
            self.offres_indexees = True

        # Recherche sémantique
        resultats_sem = self.vector_store.rechercher_similaires(
            profil=profil,
            top_k=top_k * 3,  # large pool pour le re-ranking
            seuil=config.SEUIL_SIMILARITE
        )

        print(f"  [Matcher] {len(resultats_sem)} offres avec score sémantique > {config.SEUIL_SIMILARITE}")

        # Calcul du score composite et tri final
        offres_scorees = []
        for offre, score_sem in resultats_sem:
            scores = calculer_score_global(
                offre=offre,
                profil=profil,
                score_semantique=score_sem,
                poids_sem=config.POIDS_SEMANTIQUE,
                poids_filtres=config.POIDS_FILTRES
            )

            offres_scorees.append({
                "offre": offre,
                "scores": scores,
                "score_global": scores["global"],
                "competences_manquantes": scores["competences_manquantes"],
                "competences_communes": scores["competences_communes"]
            })

        # Tri par score global décroissant
        offres_scorees.sort(key=lambda x: x["score_global"], reverse=True)

        top_offres = offres_scorees[:top_k]
        print(f"  [Matcher] Top {len(top_offres)} offres sélectionnées")

        # Affichage debug des scores
        for i, item in enumerate(top_offres, 1):
            o = item["offre"]
            s = item["score_global"]
            print(f"    {i}. [{s:.2f}] {o['titre']} @ {o['entreprise']}")

        return top_offres
