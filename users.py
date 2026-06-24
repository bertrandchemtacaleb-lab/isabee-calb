"""
users.py
--------
Role : centraliser toutes les operations de gestion des comptes
utilisateurs (creation, modification, suspension, recherche).

Ce module est utilise par admin.py pour la gestion des comptes, et par
auth.py indirectement via database.py. Il ne contient aucun code
d'affichage Streamlit : il retourne des objets Utilisateur ou des
listes, que les modules de presentation se chargent d'afficher.
"""

from database import executer, recuperer_un, recuperer_tous
from models import Utilisateur, ROLES_VALIDES
from auth import generer_sel, hacher_mot_de_passe
from utils import journaliser


def creer_utilisateur(matricule: str, nom: str, prenom: str, email: str,
                       filiere: str, niveau: str, role: str,
                       mot_de_passe: str, cree_par_id: int | None = None) -> tuple[bool, str]:
    """Cree un nouveau compte utilisateur. Retourne (succes, message)."""
    if role not in ROLES_VALIDES:
        return False, "Role invalide."
    if not Utilisateur.email_valide(email):
        return False, "Adresse e-mail invalide."
    if recuperer_un("SELECT id FROM users WHERE matricule = ?", (matricule,)):
        return False, "Ce matricule est deja utilise."
    if recuperer_un("SELECT id FROM users WHERE email = ?", (email,)):
        return False, "Cette adresse e-mail est deja utilisee."

    sel = generer_sel()
    hachage = hacher_mot_de_passe(mot_de_passe, sel)
    executer(
        """
        INSERT INTO users (matricule, nom, prenom, email, filiere, niveau, role,
                            mot_de_passe_hash, sel, statut)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'actif')
        """,
        (matricule, nom, prenom, email, filiere, niveau, role, hachage, sel),
    )
    journaliser("Creation utilisateur", "succes", user_id=cree_par_id,
                 details=f"Compte cree pour {matricule} ({role}).")
    return True, "Compte cree avec succes."


def modifier_utilisateur(utilisateur_id: int, **champs) -> tuple[bool, str]:
    """
    Met a jour un ou plusieurs champs d'un utilisateur.
    Exemple : modifier_utilisateur(12, filiere="Genie Informatique", niveau="3A")
    """
    champs_autorises = {"nom", "prenom", "email", "filiere", "niveau", "role", "statut"}
    a_mettre_a_jour = {k: v for k, v in champs.items() if k in champs_autorises}
    if not a_mettre_a_jour:
        return False, "Aucun champ valide a mettre a jour."

    assignations = ", ".join(f"{champ} = ?" for champ in a_mettre_a_jour)
    valeurs = list(a_mettre_a_jour.values()) + [utilisateur_id]
    executer(f"UPDATE users SET {assignations} WHERE id = ?", tuple(valeurs))
    journaliser("Modification utilisateur", "succes", user_id=utilisateur_id,
                 details=str(a_mettre_a_jour))
    return True, "Utilisateur mis a jour."


def reinitialiser_mot_de_passe(utilisateur_id: int, nouveau_mot_de_passe: str) -> tuple[bool, str]:
    """Reinitialise le mot de passe d'un utilisateur (action administrateur)."""
    sel = generer_sel()
    hachage = hacher_mot_de_passe(nouveau_mot_de_passe, sel)
    executer("UPDATE users SET mot_de_passe_hash = ?, sel = ? WHERE id = ?",
              (hachage, sel, utilisateur_id))
    journaliser("Reinitialisation mot de passe", "succes", user_id=utilisateur_id)
    return True, "Mot de passe reinitialise."


def suspendre_utilisateur(utilisateur_id: int) -> None:
    executer("UPDATE users SET statut = 'suspendu' WHERE id = ?", (utilisateur_id,))
    journaliser("Suspension de compte", "succes", user_id=utilisateur_id)


def reactiver_utilisateur(utilisateur_id: int) -> None:
    executer("UPDATE users SET statut = 'actif' WHERE id = ?", (utilisateur_id,))
    journaliser("Reactivation de compte", "succes", user_id=utilisateur_id)


def obtenir_utilisateur(utilisateur_id: int) -> Utilisateur | None:
    ligne = recuperer_un("SELECT * FROM users WHERE id = ?", (utilisateur_id,))
    return Utilisateur.depuis_ligne(ligne) if ligne else None


def lister_utilisateurs(role: str | None = None) -> list[Utilisateur]:
    """Liste les utilisateurs, avec filtre optionnel par role."""
    if role:
        lignes = recuperer_tous("SELECT * FROM users WHERE role = ? ORDER BY nom", (role,))
    else:
        lignes = recuperer_tous("SELECT * FROM users ORDER BY nom")
    return [Utilisateur.depuis_ligne(l) for l in lignes]


def rechercher_utilisateurs(terme: str) -> list[Utilisateur]:
    """Recherche par nom, prenom, matricule ou e-mail."""
    motif = f"%{terme}%"
    lignes = recuperer_tous(
        """
        SELECT * FROM users
        WHERE nom LIKE ? OR prenom LIKE ? OR matricule LIKE ? OR email LIKE ?
        ORDER BY nom
        """,
        (motif, motif, motif, motif),
    )
    return [Utilisateur.depuis_ligne(l) for l in lignes]


def utilisateurs_recemment_connectes(limite: int = 10) -> list[Utilisateur]:
    lignes = recuperer_tous(
        """
        SELECT * FROM users
        WHERE derniere_connexion IS NOT NULL
        ORDER BY derniere_connexion DESC
        LIMIT ?
        """,
        (limite,),
    )
    return [Utilisateur.depuis_ligne(l) for l in lignes]
