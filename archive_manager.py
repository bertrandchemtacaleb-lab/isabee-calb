"""
archive_manager.py
-------------------
Role : gerer le cycle de vie complet des documents pedagogiques
(epreuves, examens, corriges, travaux pratiques, supports de cours)
stockes dans la table subjects.

Responsabilites :
- ajout d'un document avec son fichier PDF ;
- modification des metadonnees ;
- suppression (fichier + enregistrement) ;
- circuit de validation avant publication ;
- recherche multicritere (cycle, filiere, niveau, annee, type, enseignant) ;
- gestion des favoris et des telechargements.

Ce module ne realise aucun affichage : il est consomme par app.py
(espace etudiant/enseignant) et par admin.py (moderation).
"""

from database import executer, recuperer_un, recuperer_tous
from models import Document
from utils import enregistrer_pdf, supprimer_fichier, journaliser
from datetime import datetime


def ajouter_document(titre: str, description: str, type_document: str, cycle: str,
                      filiere: str, niveau: str, annee_academique: str,
                      enseignant_id: int | None, fichier_televerse,
                      ajoute_par: int) -> tuple[bool, str]:
    """
    Enregistre un nouveau document. Le document est cree avec le statut
    'en_attente' : il ne sera visible des etudiants qu'apres validation
    par un enseignant, un contributeur habilite ou un administrateur.
    """
    chemin_fichier, taille_ko = enregistrer_pdf(fichier_televerse)
    executer(
        """
        INSERT INTO subjects (titre, description, type_document, cycle, filiere, niveau,
                               annee_academique, enseignant_id, chemin_fichier,
                               taille_fichier_ko, statut, ajoute_par)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'en_attente', ?)
        """,
        (titre, description, type_document, cycle, filiere, niveau, annee_academique,
         enseignant_id, chemin_fichier, taille_ko, ajoute_par),
    )
    journaliser("Ajout document", "succes", user_id=ajoute_par, details=titre)
    return True, "Document soumis. Il sera visible apres validation."


def modifier_document(document_id: int, modifie_par: int, **champs) -> tuple[bool, str]:
    champs_autorises = {
        "titre", "description", "type_document", "cycle", "filiere",
        "niveau", "annee_academique", "enseignant_id",
    }
    a_mettre_a_jour = {k: v for k, v in champs.items() if k in champs_autorises}
    if not a_mettre_a_jour:
        return False, "Aucun champ valide a mettre a jour."

    assignations = ", ".join(f"{champ} = ?" for champ in a_mettre_a_jour)
    valeurs = list(a_mettre_a_jour.values()) + [document_id]
    executer(f"UPDATE subjects SET {assignations} WHERE id = ?", tuple(valeurs))
    journaliser("Modification document", "succes", user_id=modifie_par, details=str(document_id))
    return True, "Document mis a jour."


def supprimer_document(document_id: int, supprime_par: int) -> tuple[bool, str]:
    document = obtenir_document(document_id)
    if document is None:
        return False, "Document introuvable."
    supprimer_fichier(document.chemin_fichier)
    executer("DELETE FROM subjects WHERE id = ?", (document_id,))
    journaliser("Suppression document", "succes", user_id=supprime_par, details=document.titre)
    return True, "Document supprime."


def valider_document(document_id: int, valide_par: int) -> tuple[bool, str]:
    executer(
        "UPDATE subjects SET statut = 'valide', valide_par = ?, date_validation = ? WHERE id = ?",
        (valide_par, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), document_id),
    )
    journaliser("Validation document", "succes", user_id=valide_par, details=str(document_id))
    return True, "Document valide et publie."


def rejeter_document(document_id: int, rejete_par: int, motif: str) -> tuple[bool, str]:
    executer(
        "UPDATE subjects SET statut = 'rejete', valide_par = ?, date_validation = ?, motif_rejet = ? WHERE id = ?",
        (rejete_par, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), motif, document_id),
    )
    journaliser("Rejet document", "succes", user_id=rejete_par, details=f"{document_id} - {motif}")
    return True, "Document rejete."


def obtenir_document(document_id: int) -> Document | None:
    ligne = recuperer_un("SELECT * FROM subjects WHERE id = ?", (document_id,))
    return Document.depuis_ligne(ligne) if ligne else None


def documents_en_attente() -> list[Document]:
    lignes = recuperer_tous("SELECT * FROM subjects WHERE statut = 'en_attente' ORDER BY date_ajout")
    return [Document.depuis_ligne(l) for l in lignes]


def documents_recents(limite: int = 10) -> list[Document]:
    lignes = recuperer_tous(
        "SELECT * FROM subjects WHERE statut = 'valide' ORDER BY date_ajout DESC LIMIT ?",
        (limite,),
    )
    return [Document.depuis_ligne(l) for l in lignes]


def rechercher_documents(terme: str = "", cycle: str = "", filiere: str = "",
                          niveau: str = "", annee: str = "", type_document: str = "",
                          enseignant_id: int | None = None,
                          uniquement_valides: bool = True) -> list[Document]:
    """
    Recherche multicritere parmi les documents. Tous les criteres sont
    optionnels et combinables (ET logique). Par defaut, seuls les
    documents valides sont retournes (consultation cote etudiant).
    """
    conditions = []
    parametres: list = []

    if uniquement_valides:
        conditions.append("statut = 'valide'")
    if terme:
        conditions.append("(titre LIKE ? OR description LIKE ?)")
        parametres += [f"%{terme}%", f"%{terme}%"]
    if cycle:
        conditions.append("cycle = ?")
        parametres.append(cycle)
    if filiere:
        conditions.append("filiere = ?")
        parametres.append(filiere)
    if niveau:
        conditions.append("niveau = ?")
        parametres.append(niveau)
    if annee:
        conditions.append("annee_academique = ?")
        parametres.append(annee)
    if type_document:
        conditions.append("type_document = ?")
        parametres.append(type_document)
    if enseignant_id:
        conditions.append("enseignant_id = ?")
        parametres.append(enseignant_id)

    clause_where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    requete = f"SELECT * FROM subjects {clause_where} ORDER BY date_ajout DESC"
    lignes = recuperer_tous(requete, tuple(parametres))
    return [Document.depuis_ligne(l) for l in lignes]


def enregistrer_telechargement(document_id: int, user_id: int, adresse_ip: str) -> None:
    executer(
        "INSERT INTO downloads (document_id, user_id, adresse_ip) VALUES (?, ?, ?)",
        (document_id, user_id, adresse_ip),
    )
    journaliser("Telechargement document", "succes", user_id=user_id, details=str(document_id))


def basculer_favori(document_id: int, user_id: int) -> bool:
    """Ajoute ou retire un document des favoris. Retourne le nouvel etat (True = favori)."""
    existe = recuperer_un(
        "SELECT id FROM favorites WHERE user_id = ? AND document_id = ?",
        (user_id, document_id),
    )
    if existe:
        executer("DELETE FROM favorites WHERE id = ?", (existe["id"],))
        return False
    executer("INSERT INTO favorites (user_id, document_id) VALUES (?, ?)", (user_id, document_id))
    return True


def favoris_utilisateur(user_id: int) -> list[Document]:
    lignes = recuperer_tous(
        """
        SELECT s.* FROM subjects s
        JOIN favorites f ON f.document_id = s.id
        WHERE f.user_id = ?
        ORDER BY f.date_ajout DESC
        """,
        (user_id,),
    )
    return [Document.depuis_ligne(l) for l in lignes]
