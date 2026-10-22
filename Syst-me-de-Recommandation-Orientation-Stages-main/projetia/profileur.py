"""
agents/profileur.py — Agent Profileur
Mène un entretien semi-structuré adaptatif pour construire le profil étudiant.
Utilise Few-shot prompting, Chain-of-Thought et mémoire conversationnelle.
"""

from base_agent import BaseAgent
import json


SYSTEM_PROMPT_PROFILEUR = """
Tu es Amal, une conseillère en orientation bienveillante et expérimentée qui travaille avec des étudiants marocains en informatique et IA.

Ton rôle est de mener un entretien naturel et chaleureux (pas un interrogatoire) pour comprendre :
1. La formation et le niveau de l'étudiant
2. Ses compétences techniques (langages, frameworks, outils)
3. Ses soft skills et qualités personnelles
4. Ses intérêts et passions (domaines, secteurs)
5. Ses contraintes pratiques (localisation, durée, remote, rémunération)
6. Son projet professionnel à moyen terme

RÈGLES D'ENTRETIEN (MODE DÉMO RAPIDE) :
- Pose TOUTES les questions essentielles en une seule fois pour aller vite.
- Si l'étudiant donne ses informations, génère DIRECTEMENT le résumé JSON.
- Ne fais PAS durer la conversation. Termine par le résumé JSON dès la première réponse de l'étudiant.

EXEMPLES (Few-shot) :
Étudiant : "Je suis en Master IA"
Mauvaise réponse : "Quelles sont vos compétences ?"
Bonne réponse : "Super ! Le Master IA c'est passionnant. Qu'est-ce qui t'a le plus accroché dans ta formation jusqu'ici — plutôt la partie algorithmique, le traitement de données, ou peut-être les applications concrètes ?"

Quand tu as collecté suffisamment d'informations, génère un résumé JSON STRICTEMENT au format suivant, précédé de la balise <<<PROFIL_JSON>>>:

<<<PROFIL_JSON>>>
{
  "nom": "",
  "email": "",
  "formation": "",
  "niveau": "",
  "competences_techniques": [],
  "soft_skills": [],
  "langues": [],
  "localisation_preferee": "",
  "accepte_remote": false,
  "duree_min_mois": 3,
  "duree_max_mois": 6,
  "domaine_interet": "",
  "secteur_prefere": "",
  "projet_professionnel": "",
  "contraintes": []
}
"""


class AgentProfileur(BaseAgent):
    """
    Agent qui construit progressivement le profil de l'étudiant
    via une conversation naturelle et adaptative.
    """

    def __init__(self):
        super().__init__("Profileur", SYSTEM_PROMPT_PROFILEUR)
        self.profil_collecte = {}
        self.nb_tours = 0
        self.profil_complet = False

    def demarrer_entretien(self) -> str:
        """Message d'ouverture de l'entretien."""
        self.reset_historique()
        msg_ouverture = (
            "Bonjour ! Je suis Amal, ta conseillère en orientation. "
            "dis-moi tout en une phrase : "
            "ton nom, ta formation, tes compétences clés (ex: Python, ML), "
            "et tes critères de stage (ville, durée) ?"
        )
        self.ajouter_message("assistant", msg_ouverture)
        return msg_ouverture

    def traiter_reponse(self, reponse_etudiant: str) -> tuple[str, bool]:
        """
        Traite une réponse de l'étudiant et génère la prochaine question.

        Returns:
            (message_agent, profil_complet)
        """
        self.ajouter_message("user", reponse_etudiant)
        self.nb_tours += 1

        # Instruction contextuelle selon l'avancement
        instruction_contexte = ""
        if self.nb_tours >= 1:
            instruction_contexte = (
                " [Note interne MODE DÉMO : Génère IMMÉDIATEMENT le profil JSON "
                "avec les informations fournies. S'il manque des informations, "
                "mets des valeurs par défaut raisonnables (ex: 3 mois, Casablanca, etc.) "
                "pour terminer l'entretien tout de suite.]"
            )

        messages = self.historique.copy()
        if instruction_contexte:
            messages[-1]["content"] += instruction_contexte

        reponse = self.appeler_llm(messages, temperature=0.7, max_tokens=800)
        contenu = reponse["content"]

        self.ajouter_message("assistant", contenu)

        # Détecter si le profil JSON est présent
        if "<<<PROFIL_JSON>>>" in contenu:
            self.profil_complet = True
            self.profil_collecte = self._extraire_json_profil(contenu)
            return contenu, True

        return contenu, False

    def _extraire_json_profil(self, texte: str) -> dict:
        """Extrait et parse le profil JSON depuis le message de l'agent."""
        try:
            debut = texte.find("<<<PROFIL_JSON>>>") + len("<<<PROFIL_JSON>>>")
            json_brut = texte[debut:].strip()
            # Trouver le bloc JSON
            debut_accolade = json_brut.find("{")
            fin_accolade = json_brut.rfind("}") + 1
            json_str = json_brut[debut_accolade:fin_accolade]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ⚠ Erreur parsing profil JSON : {e}")
            return {}

    def obtenir_profil(self) -> dict:
        """Retourne le profil collecté."""
        return self.profil_collecte
