"""
settings.py
-----------
Role : gerer les parametres globaux de la plateforme (table settings),
tels que le nom de l'etablissement, la taille maximale des fichiers,
ou l'activation de la moderation prealable des commentaires.

Separe la configuration du code : un administrateur modifie ces
valeurs depuis l'interface, sans intervention sur les fichiers source.
"""

from database import executer, recuperer_un, recuperer_tous
from utils import journaliser
from datetime import datetime

PARAMETRES_PAR_DEFAUT = {
    "nom_etablissement": ("ISABEE", "Nom affiche dans l'en-tete de la plateforme."),
    "taille_max_pdf_mo": ("25", "Taille maximale autorisee pour un document, en megaoctets."),
    "validation_obligatoire": ("oui", "Un document doit etre valide avant d'etre visible des etudiants."),
    "moderation_commentaires": ("oui", "Les commentaires sont soumis a moderation avant publication."),
}


def initialiser_parametres_par_defaut() -> None:
    """Insere les parametres par defaut s'ils sont absents de la base."""
    for cle, (valeur, description) in PARAMETRES_PAR_DEFAUT.items():
        if recuperer_un("SELECT id FROM settings WHERE cle = ?", (cle,)) is None:
            executer(
                "INSERT INTO settings (cle, valeur, description) VALUES (?, ?, ?)",
                (cle, valeur, description),
            )


def obtenir_parametre(cle: str, valeur_defaut: str = "") -> str:
    ligne = recuperer_un("SELECT valeur FROM settings WHERE cle = ?", (cle,))
    return ligne["valeur"] if ligne else valeur_defaut


def definir_parametre(cle: str, valeur: str, modifie_par: int) -> None:
    executer(
        "UPDATE settings SET valeur = ?, modifie_par = ?, date_modification = ? WHERE cle = ?",
        (valeur, modifie_par, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cle),
    )
    journaliser("Modification parametre", "succes", user_id=modifie_par, details=f"{cle} = {valeur}")


def lister_parametres() -> list[dict]:
    lignes = recuperer_tous("SELECT * FROM settings ORDER BY cle")
    return [dict(l) for l in lignes]
