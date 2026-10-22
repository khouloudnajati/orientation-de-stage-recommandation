"""
profil_store.py — Persistance des profils étudiants via SQLite
Permet de sauvegarder, récupérer et mettre à jour les profils entre les sessions.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional


class ProfilStore:
    """Gère la persistance des profils étudiants dans SQLite."""

    def __init__(self, db_path: str = "memory/profiles.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Crée les tables si elles n'existent pas."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profils (
                    id TEXT PRIMARY KEY,
                    nom TEXT,
                    email TEXT UNIQUE,
                    profil_json TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historique_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    etudiant_email TEXT,
                    session_date TEXT,
                    recommandations_json TEXT,
                    feedback TEXT,
                    FOREIGN KEY (etudiant_email) REFERENCES profils(email)
                )
            """)
            conn.commit()

    def sauvegarder_profil(self, profil: dict) -> bool:
        """Sauvegarde ou met à jour un profil étudiant."""
        now = datetime.now().isoformat()
        email = profil.get("email", f"anonyme_{now}")

        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM profils WHERE email = ?", (email,)
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE profils SET profil_json=?, nom=?, updated_at=?
                    WHERE email=?
                """, (json.dumps(profil, ensure_ascii=False), profil.get("nom", ""),
                      now, email))
            else:
                conn.execute("""
                    INSERT INTO profils (id, nom, email, profil_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"ETU_{now}", profil.get("nom", ""), email,
                      json.dumps(profil, ensure_ascii=False), now, now))
            conn.commit()
        return True

    def charger_profil(self, email: str) -> Optional[dict]:
        """Charge un profil par email. Retourne None si introuvable."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT profil_json FROM profils WHERE email = ?", (email,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def sauvegarder_session(self, email: str, recommandations: list, feedback: str = ""):
        """Enregistre une session de recommandation dans l'historique."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO historique_sessions (etudiant_email, session_date, recommandations_json, feedback)
                VALUES (?, ?, ?, ?)
            """, (email, datetime.now().isoformat(),
                  json.dumps(recommandations, ensure_ascii=False), feedback))
            conn.commit()

    def lister_profils(self) -> list[dict]:
        """Retourne la liste de tous les profils (nom + email + date)."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT nom, email, updated_at FROM profils ORDER BY updated_at DESC"
            ).fetchall()
        return [{"nom": r[0], "email": r[1], "updated_at": r[2]} for r in rows]
