"""
agents/conseiller.py — Agent Conseiller
Génère des recommandations personnalisées et argumentées.
Présente les top offres avec justifications et plan d'action concret.
"""

import json
from base_agent import BaseAgent


SYSTEM_PROMPT_CONSEILLER = """
Tu es un conseiller en orientation expert, bienveillant et pragmatique.

Ton rôle : présenter les meilleures opportunités de stage à un étudiant
de manière personnalisée, motivante et actionnable.

Pour CHAQUE offre recommandée, tu dois :
1. Expliquer POURQUOI cette offre correspond au profil (lien compétences/intérêts)
2. Mettre en valeur les points forts de la correspondance
3. Identifier honnêtement les gaps (compétences manquantes)
4. Proposer des actions concrètes pour combler ces gaps

STYLE :
- Ton chaleureux et encourageant, mais réaliste
- Utilise le prénom de l'étudiant
- Commence par les points positifs, puis les gaps
- Actions concrètes : cours en ligne, projets, certifications (avec exemples)

FORMAT DE RÉPONSE JSON STRICT :
{
  "message_intro": "Message d'introduction personnalisé",
  "recommandations": [
    {
      "rang": 1,
      "offre_id": "OFF001",
      "titre": "...",
      "entreprise": "...",
      "score_match": 0.85,
      "pourquoi_correspond": "Explication personnalisée en 2-3 phrases",
      "points_forts": ["Point 1", "Point 2"],
      "gaps": ["Gap 1", "Gap 2"],
      "plan_action": [
        {"gap": "Gap 1", "action": "Action concrète", "ressource": "Lien ou plateforme", "duree": "2 semaines"}
      ]
    }
  ],
  "conseil_global": "Conseil final personnalisé",
  "prochaines_etapes": ["Étape 1", "Étape 2", "Étape 3"]
}
"""


class AgentConseiller(BaseAgent):
    """
    Agent qui génère les recommandations finales avec argumentation complète.
    """

    def __init__(self):
        super().__init__("Conseiller", SYSTEM_PROMPT_CONSEILLER)

    def generer_recommandations(
        self,
        profil: dict,
        top_offres: list[dict]
    ) -> dict:
        """
        Génère les recommandations argumentées pour le top des offres.

        Returns:
            Dictionnaire structuré avec recommandations + plan d'action
        """
        # Prépare le contexte pour le LLM
        offres_ctx = []
        for item in top_offres:
            offres_ctx.append({
                "offre": {k: v for k, v in item["offre"].items() if not k.startswith("_")},
                "score_global": item["score_global"],
                "scores_detail": item["scores"],
                "competences_communes": item["competences_communes"],
                "competences_manquantes": item["competences_manquantes"]
            })

        prompt = f"""
Profil de l'étudiant :
{json.dumps(profil, ensure_ascii=False, indent=2)}

Top {len(top_offres)} offres sélectionnées par le système de matching :
{json.dumps(offres_ctx, ensure_ascii=False, indent=2)}

Génère les recommandations personnalisées en JSON selon le format demandé.
Sois précis sur les justifications et propose des ressources RÉELLES (Coursera, edX, YouTube, documentation officielle).
"""
        self.ajouter_message("user", prompt)

        reponse = self.appeler_llm(
            self.historique,
            temperature=0.6,
            max_tokens=2500,
            json_mode=True  # Force output JSON (OpenAI)
        )

        contenu = reponse["content"]

        try:
            # Nettoyage si nécessaire (Anthropic ne supporte pas json_mode)
            if "```json" in contenu:
                contenu = contenu.split("```json")[1].split("```")[0].strip()
            elif "```" in contenu:
                contenu = contenu.split("```")[1].split("```")[0].strip()

            result = json.loads(contenu)
            return result

        except json.JSONDecodeError as e:
            print(f"  ⚠ Erreur JSON conseiller : {e}")
            return {
                "message_intro": f"Voici tes recommandations de stages, {profil.get('nom', '')} !",
                "recommandations": [
                    {
                        "rang": i + 1,
                        "offre_id": item["offre"]["id"],
                        "titre": item["offre"]["titre"],
                        "entreprise": item["offre"]["entreprise"],
                        "score_match": item["score_global"],
                        "pourquoi_correspond": "Offre correspondant à ton profil.",
                        "points_forts": item["competences_communes"],
                        "gaps": item["competences_manquantes"],
                        "plan_action": []
                    }
                    for i, item in enumerate(top_offres)
                ],
                "conseil_global": "Bonne chance dans tes démarches !",
                "prochaines_etapes": ["Postule aux offres", "Prépare ton CV", "Entraîne-toi aux entretiens"]
            }
