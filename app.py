"""
app.py
------
Role : point d'entree unique de l'application Streamlit.

Responsabilites :
- configuration de la page et chargement de la feuille de style ;
- initialisation de la base de donnees au premier lancement ;
- creation guidee du premier compte administrateur si la base est vide ;
- affichage de l'ecran de connexion ;
- routage vers les pages selon le role de l'utilisateur connecte
  (etudiant, enseignant, contributeur, administrateur) ;
- pages communes : bibliotheque numerique (recherche de documents),
  depot d'un document, favoris, profil.

Les pages reservees a l'administration sont deleguees a admin.py ;
les parametres systeme sont delegues a settings.py.
"""

import streamlit as st

from database import initialiser_base, recuperer_un
import settings as parametres_systeme
import archive_manager
import users as gestion_utilisateurs
import admin
from auth import authentifier, deconnecter, utilisateur_courant, est_connecte, a_le_role
from models import LIBELLES_ROLE, LIBELLES_TYPE_DOCUMENT, TYPES_DOCUMENT, ROLES_VALIDES
from utils import charger_css, icone, formater_date, adresse_ip_client

st.set_page_config(
    page_title="SOURCE ISABEE",
    page_icon=":material/school:",
    layout="wide",
)


def _initialiser_application() -> None:
    initialiser_base()
    parametres_systeme.initialiser_parametres_par_defaut()
    try:
        charger_css("assets/style.css")
    except FileNotFoundError:
        pass


def _afficher_en_tete() -> None:
    nom_etablissement = parametres_systeme.obtenir_parametre("nom_etablissement", "ISABEE")
    st.markdown(
        f"""
        <div class="en-tete-institution">
            <h1>SOURCE {nom_etablissement}</h1>
            <p>Plateforme institutionnelle de gestion des ressources pedagogiques</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _aucun_compte_existant() -> bool:
    return recuperer_un("SELECT id FROM users LIMIT 1") is None


def page_initialisation() -> None:
    """Affichee une seule fois : creation du premier compte administrateur."""
    st.subheader("Configuration initiale")
    st.write(
        "Aucun compte n'existe encore sur cette installation. "
        "Creez le premier compte administrateur pour commencer."
    )
    with st.form("formulaire_initialisation"):
        colonne_gauche, colonne_droite = st.columns(2)
        with colonne_gauche:
            matricule = st.text_input("Matricule")
            nom = st.text_input("Nom")
            email = st.text_input("Adresse e-mail")
        with colonne_droite:
            prenom = st.text_input("Prenom")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            confirmation = st.text_input("Confirmer le mot de passe", type="password")

        valide = st.form_submit_button("Creer le compte administrateur")
        if valide:
            if mot_de_passe != confirmation:
                st.error("Les mots de passe ne correspondent pas.")
            elif not all([matricule, nom, prenom, email, mot_de_passe]):
                st.error("Tous les champs sont obligatoires.")
            else:
                succes, message = gestion_utilisateurs.creer_utilisateur(
                    matricule=matricule, nom=nom, prenom=prenom, email=email,
                    filiere="-", niveau="-", role="administrateur",
                    mot_de_passe=mot_de_passe,
                )
                if succes:
                    st.success("Compte administrateur cree. Vous pouvez vous connecter.")
                else:
                    st.error(message)


def page_connexion() -> None:
    st.subheader("Connexion")
    with st.form("formulaire_connexion"):
        matricule = st.text_input("Matricule")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        valide = st.form_submit_button("Se connecter")
        if valide:
            succes, message = authentifier(matricule.strip(), mot_de_passe)
            if succes:
                st.rerun()
            else:
                st.error(message)


def page_bibliotheque_numerique() -> None:
    st.subheader("Bibliotheque numerique")

    with st.expander("Filtres de recherche", expanded=True, icon=icone("Search")):
        colonne_1, colonne_2, colonne_3, colonne_4 = st.columns(4)
        with colonne_1:
            cycle = st.selectbox("Cycle", ["Tous", "Licence", "Ingenieur", "Master"])
        with colonne_2:
            niveau = st.selectbox("Niveau", ["Tous", "1A", "2A", "3A", "4A", "5A"])
        with colonne_3:
            type_document = st.selectbox(
                "Type", ["Tous"] + list(TYPES_DOCUMENT),
                format_func=lambda v: "Tous" if v == "Tous" else LIBELLES_TYPE_DOCUMENT.get(v, v),
            )
        with colonne_4:
            annee = st.text_input("Annee academique", placeholder="ex. 2025-2026")
        terme = st.text_input("Mots-cles", placeholder="Titre ou description du document")

    resultats = archive_manager.rechercher_documents(
        terme=terme,
        cycle="" if cycle == "Tous" else cycle,
        niveau="" if niveau == "Tous" else niveau,
        annee=annee,
        type_document="" if type_document == "Tous" else type_document,
    )

    st.caption(f"{len(resultats)} document(s) trouve(s)")
    utilisateur = utilisateur_courant()

    for document in resultats:
        with st.container(border=True):
            colonne_info, colonne_action = st.columns([4, 1])
            with colonne_info:
                st.markdown(f"**{document.titre}**")
                st.caption(
                    f"{document.libelle_type} - {document.cycle} - {document.filiere} - "
                    f"{document.niveau} - {document.annee_academique}"
                )
                if document.description:
                    st.write(document.description)
            with colonne_action:
                with open(document.chemin_fichier, "rb") as fichier:
                    if st.download_button(
                        "Telecharger", data=fichier, file_name=f"{document.titre}.pdf",
                        mime="application/pdf", key=f"telecharger_{document.id}",
                        icon=icone("Download"),
                    ):
                        archive_manager.enregistrer_telechargement(
                            document.id, utilisateur.id, adresse_ip_client()
                        )
                if st.button("Favori", key=f"favori_{document.id}"):
                    archive_manager.basculer_favori(document.id, utilisateur.id)
                    st.rerun()


def page_depot_document() -> None:
    st.subheader("Deposer un document")
    utilisateur = utilisateur_courant()

    with st.form("formulaire_depot", clear_on_submit=True):
        titre = st.text_input("Titre du document")
        description = st.text_area("Description", height=80)
        colonne_1, colonne_2, colonne_3 = st.columns(3)
        with colonne_1:
            cycle = st.selectbox("Cycle", ["Licence", "Ingenieur", "Master"])
            filiere = st.text_input("Filiere")
        with colonne_2:
            niveau = st.selectbox("Niveau", ["1A", "2A", "3A", "4A", "5A"])
            annee_academique = st.text_input("Annee academique", placeholder="ex. 2025-2026")
        with colonne_3:
            type_document = st.selectbox(
                "Type de document", list(TYPES_DOCUMENT),
                format_func=lambda v: LIBELLES_TYPE_DOCUMENT.get(v, v),
            )
        fichier = st.file_uploader("Fichier PDF", type=["pdf"])

        valide = st.form_submit_button("Soumettre pour validation")
        if valide:
            if not all([titre, filiere, annee_academique, fichier]):
                st.error("Veuillez renseigner les champs obligatoires et joindre un fichier PDF.")
            else:
                succes, message = archive_manager.ajouter_document(
                    titre=titre, description=description, type_document=type_document,
                    cycle=cycle, filiere=filiere, niveau=niveau,
                    annee_academique=annee_academique,
                    enseignant_id=utilisateur.id if utilisateur.role == "enseignant" else None,
                    fichier_televerse=fichier, ajoute_par=utilisateur.id,
                )
                (st.success if succes else st.error)(message)


def page_favoris() -> None:
    st.subheader("Mes favoris")
    utilisateur = utilisateur_courant()
    documents = archive_manager.favoris_utilisateur(utilisateur.id)
    if not documents:
        st.info("Aucun document enregistre dans vos favoris.")
        return
    for document in documents:
        with st.container(border=True):
            st.markdown(f"**{document.titre}**")
            st.caption(f"{document.libelle_type} - {document.filiere} - {document.niveau}")


def page_profil() -> None:
    st.subheader("Mon profil")
    utilisateur = utilisateur_courant()
    st.write(f"**Nom complet :** {utilisateur.nom_complet}")
    st.write(f"**Matricule :** {utilisateur.matricule}")
    st.write(f"**E-mail :** {utilisateur.email}")
    st.write(f"**Role :** {LIBELLES_ROLE.get(utilisateur.role, utilisateur.role)}")
    st.write(f"**Filiere :** {utilisateur.filiere or '-'}")
    st.write(f"**Niveau :** {utilisateur.niveau or '-'}")
    st.write(f"**Inscription :** {formater_date(utilisateur.date_inscription, avec_heure=False)}")
    st.write(f"**Derniere connexion :** {formater_date(utilisateur.derniere_connexion)}")


def page_parametres() -> None:
    st.subheader("Parametres de la plateforme")
    utilisateur = utilisateur_courant()
    for parametre in parametres_systeme.lister_parametres():
        nouvelle_valeur = st.text_input(
            parametre["description"] or parametre["cle"],
            value=parametre["valeur"],
            key=f"parametre_{parametre['cle']}",
        )
        if nouvelle_valeur != parametre["valeur"]:
            parametres_systeme.definir_parametre(parametre["cle"], nouvelle_valeur, utilisateur.id)
            st.rerun()


def _menu_navigation() -> str:
    utilisateur = utilisateur_courant()
    options = [("Bibliotheque numerique", "FileText")]

    if a_le_role("enseignant", "contributeur", "administrateur"):
        options.append(("Deposer un document", "Edit"))
    if a_le_role("enseignant", "administrateur"):
        options.append(("Validation des documents", "Bell"))
    if a_le_role("etudiant", "enseignant", "contributeur"):
        options.append(("Mes favoris", "Home"))
    if a_le_role("administrateur"):
        options.extend([
            ("Tableau de bord", "BarChart"),
            ("Gestion des comptes", "Users"),
            ("Journal systeme", "FileText"),
            ("Parametres", "Settings"),
        ])
    options.append(("Mon profil", "Users"))

    with st.sidebar:
        st.caption(f"Connecte en tant que {LIBELLES_ROLE.get(utilisateur.role, utilisateur.role)}")
        st.markdown(f"**{utilisateur.nom_complet}**")
        st.divider()
        libelles = [libelle for libelle, _ in options]
        choix = st.radio("Navigation", libelles, label_visibility="collapsed")
        st.divider()
        if st.button("Se deconnecter", icon=icone("Trash")):
            deconnecter()
            st.rerun()
    return choix


def main() -> None:
    _initialiser_application()
    _afficher_en_tete()

    if _aucun_compte_existant():
        page_initialisation()
        return

    if not est_connecte():
        page_connexion()
        return

    page_choisie = _menu_navigation()

    pages = {
        "Tableau de bord": admin.page_tableau_de_bord,
        "Bibliotheque numerique": page_bibliotheque_numerique,
        "Deposer un document": page_depot_document,
        "Validation des documents": admin.page_moderation_documents,
        "Mes favoris": page_favoris,
        "Gestion des comptes": admin.page_gestion_utilisateurs,
        "Journal systeme": admin.page_journal_systeme,
        "Parametres": page_parametres,
        "Mon profil": page_profil,
    }
    pages[page_choisie]()


if __name__ == "__main__":
    main()
