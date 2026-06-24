"""
database.py
-----------
Role : couche d'acces unique a la base de donnees SQLite.

Ce module est le seul point d'entree autorise vers le fichier .db.
Aucun autre module ne doit ouvrir une connexion sqlite3 directement :
tous passent par get_connection() ou par les fonctions execute_*
definies ici. Cela garantit un comportement homogene (cles etrangeres
actives, formats de date, gestion des erreurs) et facilite la migration
future vers un autre moteur (PostgreSQL, par exemple) si la plateforme
doit etre deployee a plus grande echelle.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "source_isabee.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"


def _ensure_directories() -> None:
    """Cree les dossiers de donnees s'ils n'existent pas encore."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    """
    Fournit une connexion SQLite configuree correctement.

    A utiliser systematiquement avec un bloc 'with' :

        with get_connection() as conn:
            conn.execute(...)

    Le commit est realise automatiquement a la sortie du bloc si aucune
    exception n'a ete levee ; en cas d'erreur, un rollback est effectue.
    """
    _ensure_directories()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialiser_base() -> None:
    """
    Cree les tables si elles n'existent pas, a partir de schema.sql.
    Doit etre appelee une fois au demarrage de l'application (app.py).
    """
    _ensure_directories()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema_sql)


def executer(requete: str, parametres: tuple = ()) -> int:
    """
    Execute une requete de modification (INSERT/UPDATE/DELETE).
    Retourne l'id de la derniere ligne inseree (utile pour les INSERT).
    """
    with get_connection() as conn:
        curseur = conn.execute(requete, parametres)
        return curseur.lastrowid


def recuperer_un(requete: str, parametres: tuple = ()) -> sqlite3.Row | None:
    """Execute une requete SELECT et retourne une seule ligne (ou None)."""
    with get_connection() as conn:
        return conn.execute(requete, parametres).fetchone()


def recuperer_tous(requete: str, parametres: tuple = ()) -> list[sqlite3.Row]:
    """Execute une requete SELECT et retourne toutes les lignes."""
    with get_connection() as conn:
        return conn.execute(requete, parametres).fetchall()
