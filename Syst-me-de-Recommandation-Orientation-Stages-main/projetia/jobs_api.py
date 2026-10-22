"""
jobs_api.py — Tool calling vers sources d'offres de stages
Simule les appels à Indeed / LinkedIn API avec possibilité d'extension vers de vraies APIs.
"""

import json
import os
from typing import Optional


def rechercher_offres(
    mots_cles: list[str],
    localisation: Optional[str] = None,
    duree_min: Optional[int] = None,
    duree_max: Optional[int] = None,
    type_offre: Optional[str] = None,
    remote: Optional[bool] = None,
    offres_path: str = "data/offres_simule.json"
) -> list[dict]:
    """
    Recherche des offres de stages selon des critères.

    Args:
        mots_cles: Liste de compétences ou domaines recherchés
        localisation: Ville ou "remote"
        duree_min: Durée minimale en mois
        duree_max: Durée maximale en mois
        type_offre: "stage", "alternance", ou None (tous)
        remote: True = télétravail uniquement
        offres_path: Chemin vers la base d'offres JSON

    Returns:
        Liste d'offres filtrées
    """
    # Chargement de la base d'offres
    if not os.path.exists(offres_path):
        return []

    with open(offres_path, "r", encoding="utf-8") as f:
        toutes_offres = json.load(f)

    resultats = []
    mots_cles_lower = [mc.lower() for mc in mots_cles]

    for offre in toutes_offres:
        # --- Filtres durs ---
        if type_offre and offre.get("type") != type_offre:
            continue
        if remote is True and not offre.get("remote", False):
            continue
        if localisation and localisation.lower() not in ["remote", "toutes"]:
            if localisation.lower() not in offre.get("localisation", "").lower():
                continue
        if duree_min and offre.get("duree_mois", 0) < duree_min:
            continue
        if duree_max and offre.get("duree_mois", 99) > duree_max:
            continue

        # --- Filtre souple sur mots-clés ---
        # On cherche dans titre, description, compétences, domaine
        texte_offre = " ".join([
            offre.get("titre", ""),
            offre.get("description", ""),
            offre.get("domaine", ""),
            offre.get("secteur", ""),
            " ".join(offre.get("competences_requises", []))
        ]).lower()

        # Score de pertinence mot-clé
        nb_correspondances = sum(
            1 for mc in mots_cles_lower
            if mc in texte_offre
        )

        # On inclut l'offre si au moins 1 mot-clé correspond (ou aucun filtre)
        if not mots_cles or nb_correspondances > 0:
            offre_avec_score = offre.copy()
            offre_avec_score["_score_keywords"] = nb_correspondances / max(len(mots_cles_lower), 1)
            resultats.append(offre_avec_score)

    # Tri par pertinence mot-clé décroissante
    resultats.sort(key=lambda x: x.get("_score_keywords", 0), reverse=True)

    return resultats


def obtenir_offre_par_id(offre_id: str, offres_path: str = "data/offres_simule.json") -> Optional[dict]:
    """Récupère une offre spécifique par son ID."""
    with open(offres_path, "r", encoding="utf-8") as f:
        offres = json.load(f)
    return next((o for o in offres if o["id"] == offre_id), None)


def lister_domaines(offres_path: str = "data/offres_simule.json") -> list[str]:
    """Retourne la liste des domaines disponibles dans la base."""
    with open(offres_path, "r", encoding="utf-8") as f:
        offres = json.load(f)
    return sorted(set(o.get("domaine", "") for o in offres))


# --- Définition des tools pour le LLM (format OpenAI function calling) ---
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "rechercher_offres",
            "description": "Recherche des offres de stages ou d'alternance selon des critères",
            "parameters": {
                "type": "object",
                "properties": {
                    "mots_cles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Compétences ou domaines à rechercher (ex: ['Python', 'Machine Learning'])"
                    },
                    "localisation": {
                        "type": "string",
                        "description": "Ville souhaitée ou 'toutes'"
                    },
                    "duree_min": {
                        "type": "integer",
                        "description": "Durée minimale en mois"
                    },
                    "duree_max": {
                        "type": "integer",
                        "description": "Durée maximale en mois"
                    },
                    "type_offre": {
                        "type": "string",
                        "enum": ["stage", "alternance"],
                        "description": "Type d'offre recherché"
                    },
                    "remote": {
                        "type": "boolean",
                        "description": "True si télétravail uniquement"
                    }
                },
                "required": ["mots_cles"]
            }
        }
    }
]
