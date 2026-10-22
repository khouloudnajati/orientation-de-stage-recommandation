"""
agents/coach.py — Agent Coach Évolution
Suit l'évolution du profil dans le temps et signale les nouvelles opportunités.
Utilise la mémoire long-terme (SQLite) pour comparer les profils successifs.
"""

import json
from base_agent import BaseAgent
from profil_store import ProfilStore


SYSTEM_PROMPT_COACH = """
Tu es un coach de carrière spécialisé dans l'accompagnement à long terme des étudiants en tech.

Ton rôle : analyser l'évolution d'un étudiant entre deux sessions et :
1. Identifier les nouvelles compétences acquises
2. Signaler si de nouvelles opportunités correspondent maintenant à son profil
3. Féliciter les progrès et encourager à continuer
4. Suggérer le prochain axe de développement prioritaire

Ton ton est motivant, précis et orienté croissance.
"""


class AgentCoach(BaseAgent):
    """
    Agent de suivi long-terme. Compare les profils entre sessions
    et notifie les nouvelles opportunités.
    """

    def __init__(self, db_path: str = None):
        super().__init__("Coach", SYSTEM_PROMPT_COACH)
        from config import DB_PATH
        self.store = ProfilStore(db_path or DB_PATH)

    def analyser_evolution(
        self,
        profil_actuel: dict,
        recommandations_actuelles: list[dict]
    ) -> str:
        """
        Compare le profil actuel avec l'historique et génère un rapport d'évolution.

        Returns:
            Message d'analyse de l'évolution
        """
        email = profil_actuel.get("email", "")

        # Sauvegarder le profil et la session
        self.store.sauvegarder_profil(profil_actuel)
        self.store.sauvegarder_session(email, recommandations_actuelles)

        # Charger l'ancien profil pour comparaison
        profil_precedent = self.store.charger_profil(email)

        if not profil_precedent or profil_precedent == profil_actuel:
            return self._message_premiere_session(profil_actuel, recommandations_actuelles)

        return self._analyser_progression(
            profil_actuel, profil_precedent, recommandations_actuelles
        )

    def _message_premiere_session(
        self,
        profil: dict,
        recommandations: list[dict]
    ) -> str:
        """Message pour la première session d'un étudiant."""
        nom = profil.get("nom", "")
        nb_offres = len(recommandations)
        titres = [r.get("titre", "") for r in recommandations[:3]]

        return (
            f"Bienvenue {nom} ! Ton profil a été enregistré avec succès. "
            f"J'ai trouvé {nb_offres} opportunités correspondant à ton profil, "
            f"notamment : {', '.join(titres)}.\n\n"
            f"Reviens régulièrement — je te notifierai dès que de nouvelles opportunités "
            f"corresponderont à ton évolution ! 🚀"
        )

    def _analyser_progression(
        self,
        profil_actuel: dict,
        profil_precedent: dict,
        recommandations: list[dict]
    ) -> str:
        """Analyse la progression entre deux sessions."""
        comps_avant = set(profil_precedent.get("competences_techniques", []))
        comps_apres = set(profil_actuel.get("competences_techniques", []))
        nouvelles_comps = comps_apres - comps_avant

        prompt = f"""
Profil précédent :
{json.dumps(profil_precedent, ensure_ascii=False, indent=2)}

Profil actuel :
{json.dumps(profil_actuel, ensure_ascii=False, indent=2)}

Nouvelles compétences acquises : {list(nouvelles_comps)}

Nouvelles recommandations :
{json.dumps([{"titre": r.get("titre"), "score": r.get("score_match")} for r in recommandations], ensure_ascii=False)}

Génère un message de coaching motivant (3-4 paragraphes) qui :
1. Félicite les progrès concrets
2. Explique quelles nouvelles portes s'ouvrent
3. Suggère le prochain objectif prioritaire
"""
        self.ajouter_message("user", prompt)
        reponse = self.appeler_llm(self.historique, temperature=0.8, max_tokens=600)
        return reponse["content"]

    def notifier_nouvelles_opportunites(
        self,
        email: str,
        nouvelles_offres: list[dict]
    ) -> str:
        """Génère une notification pour de nouvelles opportunités correspondantes."""
        if not nouvelles_offres:
            return ""

        profil = self.store.charger_profil(email)
        nom = profil.get("nom", "étudiant") if profil else "étudiant"

        titres = [o.get("titre", "") for o in nouvelles_offres[:3]]
        return (
            f"🔔 {nom}, de nouvelles opportunités correspondent à ton profil : "
            f"{', '.join(titres)}. "
            f"Connecte-toi pour voir les détails !"
        )
