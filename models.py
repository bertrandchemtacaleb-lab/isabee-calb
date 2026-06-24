"""
models.py
---------
Role : definir la structure des donnees manipulees par l'application,
independamment de la base de donnees et de l'interface.

Ces classes ne contiennent aucune logique d'acces aux donnees (ce role
revient a database.py, users.py, archive_manager.py, etc.) et aucune
logique d'affichage (ce role revient a app.py et admin.py). Elles
servent uniquement a representer un enregistrement de maniere typee et
lisible, et a centraliser les regles de validation simples qui leur
sont propres.
"""

from dataclasses import dataclass
from datetime import datetime
import re

ROLES_VALIDES = ("administrateur", "enseignant", "etudiant", "contributeur")
TYPES_DOCUMENT = ("examen", "controle_continu", "corrige", "travaux_pratiques", "support_cours", "autre")
STATUTS_DOCUMENT = ("en_attente", "valide", "rejete")

LIBELLES_TYPE_DOCUMENT = {
    "examen": "Examen",
    "controle_continu": "Controle continu",
    "corrige": "Corrige",
    "travaux_pratiques": "Travaux pratiques",
    "support_cours": "Support de cours",
    "autre": "Autre",
}

LIBELLES_ROLE = {
    "administrateur": "Administrateur",
    "enseignant": "Enseignant",
    "etudiant": "Etudiant",
    "contributeur": "Contributeur",
}


@dataclass
class Utilisateur:
    id: int | None
    matricule: str
    nom: str
    prenom: str
    email: str
    filiere: str
    niveau: str
    role: str
    statut: str = "actif"
    date_inscription: str | None = None
    derniere_connexion: str | None = None

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"

    @staticmethod
    def email_valide(email: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

    @classmethod
    def depuis_ligne(cls, ligne) -> "Utilisateur":
        """Construit un Utilisateur a partir d'une ligne sqlite3.Row."""
        return cls(
            id=ligne["id"],
            matricule=ligne["matricule"],
            nom=ligne["nom"],
            prenom=ligne["prenom"],
            email=ligne["email"],
            filiere=ligne["filiere"],
            niveau=ligne["niveau"],
            role=ligne["role"],
            statut=ligne["statut"],
            date_inscription=ligne["date_inscription"],
            derniere_connexion=ligne["derniere_connexion"],
        )


@dataclass
class Document:
    id: int | None
    titre: str
    description: str
    type_document: str
    cycle: str
    filiere: str
    niveau: str
    annee_academique: str
    enseignant_id: int | None
    chemin_fichier: str
    taille_fichier_ko: int | None
    statut: str = "en_attente"
    ajoute_par: int | None = None
    valide_par: int | None = None
    date_ajout: str | None = None
    date_validation: str | None = None
    motif_rejet: str | None = None

    @property
    def libelle_type(self) -> str:
        return LIBELLES_TYPE_DOCUMENT.get(self.type_document, self.type_document)

    @classmethod
    def depuis_ligne(cls, ligne) -> "Document":
        return cls(
            id=ligne["id"],
            titre=ligne["titre"],
            description=ligne["description"],
            type_document=ligne["type_document"],
            cycle=ligne["cycle"],
            filiere=ligne["filiere"],
            niveau=ligne["niveau"],
            annee_academique=ligne["annee_academique"],
            enseignant_id=ligne["enseignant_id"],
            chemin_fichier=ligne["chemin_fichier"],
            taille_fichier_ko=ligne["taille_fichier_ko"],
            statut=ligne["statut"],
            ajoute_par=ligne["ajoute_par"],
            valide_par=ligne["valide_par"],
            date_ajout=ligne["date_ajout"],
            date_validation=ligne["date_validation"],
            motif_rejet=ligne["motif_rejet"],
        )


@dataclass
class EntreeJournal:
    id: int | None
    date_heure: str
    user_id: int | None
    matricule: str | None
    action: str
    adresse_ip: str | None
    resultat: str
    details: str | None = None
