"""
utils.py
--------
Role : regrouper les fonctions transverses utilisees par plusieurs
modules, afin d'eviter la duplication de code.

Contient notamment :
- l'ecriture dans le journal systeme (table logs) ;
- la recuperation de l'adresse IP du client ;
- la validation et l'enregistrement des fichiers PDF ;
- des fonctions de formatage de date.

Ce module ne doit jamais importer admin.py, app.py ni les autres
modules de presentation : il se situe en bas de la hierarchie de
dependances et peut etre importe par n'importe quel autre fichier.
"""

from datetime import datetime
from pathlib import Path
import uuid

import streamlit as st

from database import executer, DOCUMENTS_DIR

TAILLE_MAX_PDF_MO = 25

# ---------------------------------------------------------------------
# Icones professionnelles
# ---------------------------------------------------------------------
# Streamlit ne supporte pas nativement la bibliotheque lucide-react
# (reservee aux interfaces React/HTML). L'equivalent natif et tout
# aussi sobre, integre a Streamlit, est l'ensemble des "Material
# Symbols" (icon=":material/nom:"). La table ci-dessous fait
# correspondre les icones demandees dans le cahier des charges a leur
# equivalent Material Symbols, afin de garantir une interface sans
# emoji et sans pictogramme decoratif.
ICONES = {
    "Home": "home",
    "FileText": "description",
    "Users": "group",
    "Search": "search",
    "Download": "download",
    "Settings": "settings",
    "BarChart": "bar_chart",
    "Trash": "delete",
    "Edit": "edit",
    "Bell": "notifications",
}


def icone(nom: str) -> str:
    """Retourne la chaine d'icone Material Symbols utilisable par Streamlit."""
    return f":material/{ICONES.get(nom, 'circle')}:"


def adresse_ip_client() -> str:
    """
    Retourne l'adresse IP du client si elle est exposee par
    l'environnement d'execution, sinon une valeur par defaut.
    Streamlit ne donne pas un acces direct et fiable a l'IP du
    navigateur ; en environnement de production, cette information
    doit etre recuperee depuis le serveur web ou le reverse proxy
    place devant l'application (en-tete X-Forwarded-For).
    """
    try:
        ctx = st.context
        headers = getattr(ctx, "headers", {}) or {}
        return headers.get("X-Forwarded-For", "non_disponible")
    except Exception:
        return "non_disponible"


def journaliser(action: str, resultat: str, user_id: int | None = None,
                 matricule: str | None = None, details: str | None = None) -> None:
    """
    Enregistre une ligne dans le journal systeme (table logs).
    A appeler pour toute action sensible : connexion, ajout, suppression,
    modification, validation de document, changement de parametre.
    """
    executer(
        """
        INSERT INTO logs (date_heure, user_id, matricule, action, adresse_ip, resultat, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            matricule,
            action,
            adresse_ip_client(),
            resultat,
            details,
        ),
    )


def fichier_est_pdf_valide(fichier_televerse) -> tuple[bool, str]:
    """
    Verifie qu'un fichier televerse est un PDF et respecte la taille
    maximale autorisee. Retourne (valide, message_erreur).
    """
    if fichier_televerse is None:
        return False, "Aucun fichier fourni."
    if not fichier_televerse.name.lower().endswith(".pdf"):
        return False, "Seuls les fichiers au format PDF sont acceptes."
    taille_mo = fichier_televerse.size / (1024 * 1024)
    if taille_mo > TAILLE_MAX_PDF_MO:
        return False, f"Le fichier depasse la taille maximale autorisee ({TAILLE_MAX_PDF_MO} Mo)."
    return True, ""


def enregistrer_pdf(fichier_televerse) -> tuple[str, int]:
    """
    Enregistre un fichier PDF televerse sur le disque, sous un nom
    unique afin d'eviter toute collision ou ecrasement accidentel.
    Retourne le chemin relatif du fichier et sa taille en kilo-octets.
    """
    nom_unique = f"{uuid.uuid4().hex}.pdf"
    chemin_complet = Path(DOCUMENTS_DIR) / nom_unique
    with open(chemin_complet, "wb") as f:
        f.write(fichier_televerse.getbuffer())
    taille_ko = chemin_complet.stat().st_size // 1024
    return str(chemin_complet), taille_ko


def supprimer_fichier(chemin_fichier: str) -> None:
    """Supprime un fichier PDF du disque si celui-ci existe."""
    chemin = Path(chemin_fichier)
    if chemin.exists():
        chemin.unlink()


def formater_date(valeur_iso: str | None, avec_heure: bool = True) -> str:
    """Convertit une date ISO stockee en base vers un format lisible."""
    if not valeur_iso:
        return "Jamais"
    try:
        dt = datetime.strptime(valeur_iso, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return valeur_iso
    return dt.strftime("%d/%m/%Y %H:%M") if avec_heure else dt.strftime("%d/%m/%Y")


def charger_css(chemin_fichier: str) -> None:
    """Injecte une feuille de style CSS externe dans la page Streamlit."""
    with open(chemin_fichier, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
