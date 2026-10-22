"""
agents/orchestrateur.py — Orchestrateur du SMA
Coordonne la communication inter-agents et le flux de données.
Élément central de l'architecture multi-agents (Chapitre 3).
"""

import json
from profileur import AgentProfileur
from chercheur import AgentChercheur
from matcher import AgentMatcher
from conseiller import AgentConseiller
from coach import AgentCoach
from profil_store import ProfilStore
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint
import config


console = Console()


class Orchestrateur:
    """
    Orchestre la collaboration entre tous les agents du SMA.

    Flux d'exécution :
    1. Profileur  → entretien conversationnel → profil structuré
    2. Chercheur  → tool calling → offres candidates
    3. Matcher    → embeddings + scoring → top offres
    4. Conseiller → LLM → recommandations argumentées
    5. Coach      → persistance + suivi → rapport d'évolution
    """

    def __init__(self):
        console.print("\n[bold purple]🤖 Initialisation du SMA...[/bold purple]")

        self.profileur = AgentProfileur()
        self.chercheur = AgentChercheur()
        self.matcher = AgentMatcher()
        self.conseiller = AgentConseiller()
        self.coach = AgentCoach()
        self.store = ProfilStore(config.DB_PATH)

        # Pré-indexation des offres au démarrage
        console.print("[dim]Indexation des offres...[/dim]")
        self.matcher.indexer_offres()

        console.print("[bold green]✅ SMA prêt ![/bold green]\n")

    def demarrer_session(self, charger_profil_email: str = None):
        """
        Lance une session complète de conseil en orientation.

        Args:
            charger_profil_email: Si fourni, charge un profil existant (skip entretien)
        """
        console.rule("[bold purple]Système de Recommandation — Orientation & Stages[/bold purple]")

        # --- ÉTAPE 1 : Profilage ---
        if charger_profil_email:
            profil = self._charger_profil_existant(charger_profil_email)
        else:
            profil = self._mener_entretien()

        if not profil:
            console.print("[red]❌ Impossible d'obtenir le profil. Session annulée.[/red]")
            return

        self._afficher_profil(profil)

        # --- ÉTAPE 2 : Recherche d'offres ---
        console.print("\n[bold blue]🔍 Étape 2 — Recherche d'offres...[/bold blue]")
        offres_candidates = self.chercheur.rechercher(profil)
        console.print(f"[green]{len(offres_candidates)} offres candidates trouvées[/green]")

        if not offres_candidates:
            console.print("[yellow]⚠ Aucune offre trouvée. Vérifiez la base de données.[/yellow]")
            return

        # --- ÉTAPE 3 : Matching ---
        console.print("\n[bold blue]⚡ Étape 3 — Matching sémantique...[/bold blue]")
        # Re-indexer uniquement les offres candidates pour le matching
        self.matcher.vector_store.indexer_offres(offres_candidates)
        top_offres = self.matcher.matcher(profil, offres_candidates)

        # --- ÉTAPE 4 : Génération des recommandations ---
        console.print("\n[bold blue]💡 Étape 4 — Génération des recommandations...[/bold blue]")
        recommandations = self.conseiller.generer_recommandations(profil, top_offres)

        # --- ÉTAPE 5 : Affichage et persistance ---
        self._afficher_recommandations(recommandations)

        console.print("\n[bold blue]💾 Étape 5 — Sauvegarde et coaching...[/bold blue]")
        message_coach = self.coach.analyser_evolution(
            profil,
            recommandations.get("recommandations", [])
        )
        console.print(Panel(message_coach, title="🏋️ Message du Coach", border_style="purple"))

        console.rule("[bold green]Session terminée[/bold green]")
        return recommandations

    def _mener_entretien(self) -> dict:
        """Gère l'entretien conversationnel avec l'étudiant."""
        console.print("[bold blue]🎤 Étape 1 — Entretien de profilage[/bold blue]")
        console.print("[dim](L'agent Profileur va vous poser quelques questions)[/dim]\n")

        # Message d'ouverture
        msg = self.profileur.demarrer_entretien()
        console.print(Panel(msg, title="Amal (Conseillère)", border_style="teal4"))

        profil_complet = False
        while not profil_complet:
            # Input étudiant
            console.print("\n[bold cyan]Vous :[/bold cyan] ", end="")
            try:
                reponse_etudiant = input()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Session interrompue.[/yellow]")
                return {}

            if reponse_etudiant.strip().lower() in ["quit", "exit", "q"]:
                return {}

            # Traitement par le Profileur
            msg_agent, profil_complet = self.profileur.traiter_reponse(reponse_etudiant)

            # Affichage (masquer le JSON brut dans la conversation)
            if "<<<PROFIL_JSON>>>" in msg_agent:
                msg_affiche = msg_agent.split("<<<PROFIL_JSON>>>")[0].strip()
                if not msg_affiche:
                    msg_affiche = "Parfait ! J'ai maintenant toutes les informations pour analyser ton profil. Laisse-moi trouver les meilleures opportunités pour toi ! 🎯"
            else:
                msg_affiche = msg_agent

            console.print(Panel(msg_affiche, title="Amal (Conseillère)", border_style="teal4"))

        profil = self.profileur.obtenir_profil()
        console.print("[bold green]✅ Profil construit avec succès ![/bold green]")
        return profil

    def _charger_profil_existant(self, email: str) -> dict:
        """Charge un profil existant depuis la base de données."""
        profil = self.store.charger_profil(email)
        if profil:
            console.print(f"[green]✅ Profil chargé : {profil.get('nom', email)}[/green]")
        else:
            console.print(f"[yellow]⚠ Profil introuvable pour {email}[/yellow]")
        return profil or {}

    def _afficher_profil(self, profil: dict):
        """Affiche le profil de manière lisible."""
        table = Table(title="📋 Profil Étudiant", show_header=False, border_style="blue")
        table.add_column("Champ", style="cyan")
        table.add_column("Valeur", style="white")

        champs = [
            ("Nom", profil.get("nom", "")),
            ("Formation", profil.get("formation", "")),
            ("Niveau", profil.get("niveau", "")),
            ("Domaine d'intérêt", profil.get("domaine_interet", "")),
            ("Compétences tech", ", ".join(profil.get("competences_techniques", []))),
            ("Soft skills", ", ".join(profil.get("soft_skills", []))),
            ("Langues", ", ".join(profil.get("langues", []))),
            ("Localisation", profil.get("localisation_preferee", "")),
            ("Durée souhaitée", f"{profil.get('duree_min_mois', 3)}-{profil.get('duree_max_mois', 6)} mois"),
        ]
        for champ, valeur in champs:
            if valeur:
                table.add_row(champ, valeur)

        console.print(table)

    def _afficher_recommandations(self, recommandations: dict):
        """Affiche les recommandations de manière structurée et lisible."""
        console.print("\n")
        console.print(Panel(
            recommandations.get("message_intro", "Voici tes recommandations !"),
            title="🎯 Recommandations Personnalisées",
            border_style="green"
        ))

        for rec in recommandations.get("recommandations", []):
            score_pct = int(rec.get("score_match", 0) * 100)
            couleur = "green" if score_pct >= 70 else "yellow" if score_pct >= 50 else "red"

            # En-tête offre
            titre_offre = Text()
            titre_offre.append(f"#{rec.get('rang', '?')} ", style="bold white")
            titre_offre.append(rec.get("titre", ""), style="bold cyan")
            titre_offre.append(f" @ {rec.get('entreprise', '')}", style="white")
            titre_offre.append(f" [{score_pct}% de correspondance]", style=f"bold {couleur}")

            contenu = []
            contenu.append(f"[italic]{rec.get('pourquoi_correspond', '')}[/italic]")

            if rec.get("points_forts"):
                contenu.append("\n[bold green]✅ Points forts :[/bold green]")
                for pf in rec.get("points_forts", []):
                    contenu.append(f"  • {pf}")

            if rec.get("gaps"):
                contenu.append("\n[bold yellow]📚 À développer :[/bold yellow]")
                for gap in rec.get("gaps", []):
                    contenu.append(f"  • {gap}")

            if rec.get("plan_action"):
                contenu.append("\n[bold blue]🛠 Plan d'action :[/bold blue]")
                for action in rec.get("plan_action", []):
                    contenu.append(
                        f"  → {action.get('gap', '')}: {action.get('action', '')} "
                        f"({action.get('ressource', '')}, ~{action.get('duree', '')})"
                    )

            console.print(Panel(
                "\n".join(contenu),
                title=titre_offre,
                border_style=couleur,
                padding=(1, 2)
            ))

        # Conseil global et prochaines étapes
        if recommandations.get("conseil_global"):
            console.print(Panel(
                recommandations["conseil_global"],
                title="💬 Conseil global",
                border_style="purple"
            ))

        if recommandations.get("prochaines_etapes"):
            etapes = "\n".join(
                f"{i+1}. {e}"
                for i, e in enumerate(recommandations["prochaines_etapes"])
            )
            console.print(Panel(etapes, title="📌 Prochaines étapes", border_style="cyan"))
