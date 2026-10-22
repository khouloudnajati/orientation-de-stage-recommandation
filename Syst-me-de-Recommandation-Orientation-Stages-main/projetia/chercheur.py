"""
agents/chercheur.py — Agent Chercheur d'Offres
Utilise le tool calling pour interroger la base d'offres de manière intelligente.
Traduit le profil en requête de recherche optimisée.
"""

import json
from base_agent import BaseAgent
from jobs_api import rechercher_offres, TOOLS_DEFINITION


SYSTEM_PROMPT_CHERCHEUR = """
Tu es un expert en recherche d'emploi et de stages spécialisé dans les domaines tech et IA.

Ton rôle : à partir du profil d'un étudiant, formuler la meilleure requête de recherche
pour trouver des offres de stages pertinentes.

Tu dois appeler l'outil rechercher_offres avec des paramètres bien choisis :
- Extraire les mots-clés les plus pertinents du profil (compétences, domaines)
- Respecter les contraintes pratiques (localisation, durée, remote)
- Élargir intelligemment si nécessaire (ex: "ML" → aussi "Machine Learning", "IA")

Retourne uniquement le résultat de l'appel outil, sans commentaire supplémentaire.
"""


class AgentChercheur(BaseAgent):
    """
    Agent qui recherche les offres pertinentes via tool calling.
    Traduit le profil étudiant en requête de recherche optimisée.
    """

    def __init__(self):
        super().__init__("Chercheur", SYSTEM_PROMPT_CHERCHEUR)

    def rechercher(self, profil: dict) -> list[dict]:
        """
        Lance la recherche d'offres basée sur le profil.

        Returns:
            Liste d'offres candidates
        """
        # Construction du message pour le LLM
        prompt = f"""
Voici le profil de l'étudiant :
{json.dumps(profil, ensure_ascii=False, indent=2)}

Appelle l'outil rechercher_offres avec les paramètres les plus adaptés à ce profil.
Pense à inclure des synonymes et variantes des compétences pour élargir la recherche.
"""
        self.ajouter_message("user", prompt)

        # Premier appel LLM (Tools désactivés temporairement pour éviter MALFORMED_FUNCTION_CALL)
        reponse = self.appeler_llm(
            self.historique,
            temperature=0.3,
            max_tokens=500
        )

        # Si le LLM a généré un tool call
        if reponse.get("tool_calls"):
            tool_call = reponse["tool_calls"][0]
            args = tool_call["arguments"]

            print(f"\n  [Chercheur] Tool call: rechercher_offres({args})")

            # Exécution du tool
            offres = rechercher_offres(
                mots_cles=args.get("mots_cles", []),
                localisation=args.get("localisation"),
                duree_min=args.get("duree_min"),
                duree_max=args.get("duree_max"),
                type_offre=args.get("type_offre"),
                remote=args.get("remote")
            )

            print(f"  [Chercheur] {len(offres)} offres trouvées via tool call")
            return offres

        else:
            # Fallback : recherche directe avec les compétences du profil
            print("  [Chercheur] Fallback : recherche directe par compétences")
            mots_cles = (
                profil.get("competences_techniques", [])[:5] +
                [profil.get("domaine_interet", "")]
            )
            return rechercher_offres(
                mots_cles=[mc for mc in mots_cles if mc],
                localisation=profil.get("localisation_preferee"),
                remote=profil.get("accepte_remote")
            )
