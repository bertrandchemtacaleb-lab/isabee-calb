"""
statistics.py
-------------
Role : calculer les indicateurs et preparer les donnees affichees sur
le tableau de bord administrateur (compteurs, listes recentes,
series pour les graphiques Plotly).

Ce module ne dessine aucun graphique : il retourne des structures de
donnees simples (dictionnaires, listes) que admin.py transmet a
Plotly. Cette separation permet de tester les calculs independamment
de l'affichage.
"""

from database import recuperer_un, recuperer_tous


def nombre_documents(statut: str = "valide") -> int:
    ligne = recuperer_un("SELECT COUNT(*) AS total FROM subjects WHERE statut = ?", (statut,))
    return ligne["total"] if ligne else 0


def nombre_utilisateurs(role: str) -> int:
    ligne = recuperer_un("SELECT COUNT(*) AS total FROM users WHERE role = ?", (role,))
    return ligne["total"] if ligne else 0


def nombre_telechargements() -> int:
    ligne = recuperer_un("SELECT COUNT(*) AS total FROM downloads")
    return ligne["total"] if ligne else 0


def indicateurs_generaux() -> dict:
    """Regroupe les indicateurs cles affiches en tete du tableau de bord."""
    return {
        "documents_valides": nombre_documents("valide"),
        "documents_en_attente": nombre_documents("en_attente"),
        "etudiants": nombre_utilisateurs("etudiant"),
        "enseignants": nombre_utilisateurs("enseignant"),
        "contributeurs": nombre_utilisateurs("contributeur"),
        "telechargements": nombre_telechargements(),
    }


def telechargements_par_jour(nb_jours: int = 30) -> list[dict]:
    """Serie temporelle du nombre de telechargements, pour une courbe Plotly."""
    lignes = recuperer_tous(
        """
        SELECT date(date_telechargement) AS jour, COUNT(*) AS total
        FROM downloads
        WHERE date(date_telechargement) >= date('now', ?)
        GROUP BY jour
        ORDER BY jour
        """,
        (f"-{nb_jours} days",),
    )
    return [{"jour": l["jour"], "total": l["total"]} for l in lignes]


def documents_par_type() -> list[dict]:
    """Repartition des documents valides par type, pour un diagramme circulaire."""
    lignes = recuperer_tous(
        """
        SELECT type_document, COUNT(*) AS total
        FROM subjects
        WHERE statut = 'valide'
        GROUP BY type_document
        ORDER BY total DESC
        """
    )
    return [{"type_document": l["type_document"], "total": l["total"]} for l in lignes]


def documents_par_filiere() -> list[dict]:
    """Repartition des documents valides par filiere, pour un histogramme."""
    lignes = recuperer_tous(
        """
        SELECT filiere, COUNT(*) AS total
        FROM subjects
        WHERE statut = 'valide'
        GROUP BY filiere
        ORDER BY total DESC
        """
    )
    return [{"filiere": l["filiere"], "total": l["total"]} for l in lignes]


def documents_les_plus_telecharges(limite: int = 5) -> list[dict]:
    lignes = recuperer_tous(
        """
        SELECT s.titre, COUNT(d.id) AS total
        FROM subjects s
        JOIN downloads d ON d.document_id = s.id
        GROUP BY s.id
        ORDER BY total DESC
        LIMIT ?
        """,
        (limite,),
    )
    return [{"titre": l["titre"], "total": l["total"]} for l in lignes]
