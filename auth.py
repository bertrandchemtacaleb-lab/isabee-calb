"""
auth.py
-------
Role : gerer l'authentification des utilisateurs et leur session.

Remplace integralement l'ancien systeme (connexion par numero de
telephone, codes d'acces, identifiants generes aleatoirement). La
connexion se fait desormais par matricule et mot de passe.

Principes de securite appliques :
- chaque mot de passe est associe a un sel (salt) unique, genere
  aleatoirement a la creation du compte ;
- le mot de passe n'est jamais stocke en clair : seul le resultat du
  hachage SHA-256(sel + mot_de_passe) est conserve en base ;
- le nombre de tentatives successives est limite afin de ralentir les
  attaques par force brute ;
- la session est maintenue via st.session_state, propre a chaque
  utilisateur connecte au serveur Streamlit, et reinitialisee a la
  deconnexion.

Limite assumee : SHA-256 avec sel est le mecanisme demande par le
cahier des charges. Pour un deploiement en production exposé sur
Internet, un algorithme dedie aux mots de passe (Argon2id ou bcrypt),
avec un cout de calcul reglable, est preferable a un hachage rapide
comme SHA-256. Ce point est repris dans la critique finale.
"""

import hashlib
import secrets
from datetime import datetime

import streamlit as st

from database import recuperer_un, executer
from models import Utilisateur
from utils import journaliser, adresse_ip_client

NB_ITERATIONS_HACHAGE = 150_000
NB_TENTATIVES_MAX = 5


def generer_sel() -> str:
    """Genere un sel cryptographiquement aleatoire, propre a un compte."""
    return secrets.token_hex(16)


def hacher_mot_de_passe(mot_de_passe: str, sel: str) -> str:
    """
    Calcule le hachage SHA-256 d'un mot de passe avec son sel.
    Le hachage est applique de maniere repetee (etirement de cle) afin
    de ralentir les attaques par dictionnaire, tout en restant base sur
    l'algorithme SHA-256 impose par le cahier des charges.
    """
    valeur = (sel + mot_de_passe).encode("utf-8")
    for _ in range(NB_ITERATIONS_HACHAGE):
        valeur = hashlib.sha256(valeur).digest()
    return valeur.hex()


def mot_de_passe_correct(mot_de_passe: str, sel: str, hachage_attendu: str) -> bool:
    """Compare un mot de passe fourni au hachage stocke, en temps constant."""
    calcule = hacher_mot_de_passe(mot_de_passe, sel)
    return secrets.compare_digest(calcule, hachage_attendu)


def _cle_tentatives(matricule: str) -> str:
    return f"tentatives_{matricule}"


def authentifier(matricule: str, mot_de_passe: str) -> tuple[bool, str]:
    """
    Verifie les identifiants fournis et ouvre la session si valides.
    Retourne (succes, message).
    """
    cle = _cle_tentatives(matricule)
    tentatives = st.session_state.get(cle, 0)
    if tentatives >= NB_TENTATIVES_MAX:
        journaliser("Connexion", "echec", matricule=matricule,
                     details="Nombre maximal de tentatives atteint.")
        return False, "Trop de tentatives. Veuillez contacter un administrateur."

    ligne = recuperer_un("SELECT * FROM users WHERE matricule = ?", (matricule,))
    if ligne is None or not mot_de_passe_correct(mot_de_passe, ligne["sel"], ligne["mot_de_passe_hash"]):
        st.session_state[cle] = tentatives + 1
        journaliser("Connexion", "echec", matricule=matricule, details="Identifiants invalides.")
        return False, "Matricule ou mot de passe incorrect."

    if ligne["statut"] == "suspendu":
        journaliser("Connexion", "echec", user_id=ligne["id"], matricule=matricule,
                     details="Compte suspendu.")
        return False, "Ce compte a ete suspendu. Contactez un administrateur."

    st.session_state.pop(cle, None)
    executer("UPDATE users SET derniere_connexion = ? WHERE id = ?",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ligne["id"]))

    st.session_state["utilisateur_connecte"] = Utilisateur.depuis_ligne(ligne)
    journaliser("Connexion", "succes", user_id=ligne["id"], matricule=matricule)
    return True, "Connexion reussie."


def deconnecter() -> None:
    """Termine la session de l'utilisateur courant."""
    utilisateur = utilisateur_courant()
    if utilisateur is not None:
        journaliser("Deconnexion", "succes", user_id=utilisateur.id, matricule=utilisateur.matricule)
    for cle in ("utilisateur_connecte",):
        st.session_state.pop(cle, None)


def utilisateur_courant() -> Utilisateur | None:
    """Retourne l'utilisateur actuellement connecte, ou None."""
    return st.session_state.get("utilisateur_connecte")


def est_connecte() -> bool:
    return utilisateur_courant() is not None


def a_le_role(*roles_autorises: str) -> bool:
    """Verifie que l'utilisateur connecte possede l'un des roles donnes."""
    utilisateur = utilisateur_courant()
    return utilisateur is not None and utilisateur.role in roles_autorises


def exiger_role(*roles_autorises: str) -> bool:
    """
    Bloque l'affichage de la page courante si l'utilisateur connecte
    n'a pas l'un des roles requis. A appeler en tete de chaque page
    sensible (admin.py, settings.py, etc.).
    """
    if not a_le_role(*roles_autorises):
        st.error("Acces refuse : cette section ne vous est pas accessible.")
        st.stop()
    return True
