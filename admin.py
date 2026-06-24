"""
admin.py
--------
Role : rendre les pages reservees a l'administrateur :
- tableau de bord (indicateurs cles, graphiques Plotly, listes recentes) ;
- gestion des comptes utilisateurs ;
- moderation des documents en attente de validation ;
- consultation du journal systeme ;
- acces aux parametres de la plateforme (delegue a settings.py).

Ce module orchestre les autres modules metier (statistics.py,
users.py, archive_manager.py, settings.py) et ne contient lui-meme
aucune requete SQL directe.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

import statistics as stats
import users as gestion_utilisateurs
import archive_manager
from database import recuperer_tous
from models import LIBELLES_ROLE, LIBELLES_TYPE_DOCUMENT
from utils import formater_date, icone
from auth import exiger_role, utilisateur_courant


def page_tableau_de_bord() -> None:
    exiger_role("administrateur")
    st.subheader("Tableau de bord")

    indicateurs = stats.indicateurs_generaux()
    colonnes = st.columns(4)
    donnees_cartes = [
        ("Documents publies", indicateurs["documents_valides"]),
        ("En attente de validation", indicateurs["documents_en_attente"]),
        ("Etudiants inscrits", indicateurs["etudiants"]),
        ("Telechargements", indicateurs["telechargements"]),
    ]
    for colonne, (libelle, valeur) in zip(colonnes, donnees_cartes):
        with colonne:
            st.markdown(
                f"""
                <div class="carte carte-indicateur">
                    <div class="valeur">{valeur}</div>
                    <div class="libelle">{libelle}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    colonne_gauche, colonne_droite = st.columns(2)

    with colonne_gauche:
        st.caption("Telechargements sur les 30 derniers jours")
        serie = stats.telechargements_par_jour(30)
        if serie:
            df = pd.DataFrame(serie)
            figure = px.line(df, x="jour", y="total", markers=True)
            figure.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.info("Aucun telechargement enregistre pour le moment.")

    with colonne_droite:
        st.caption("Repartition des documents par type")
        repartition = stats.documents_par_type()
        if repartition:
            df = pd.DataFrame(repartition)
            df["libelle"] = df["type_document"].map(LIBELLES_TYPE_DOCUMENT)
            figure = px.pie(df, names="libelle", values="total", hole=0.45)
            figure.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
            st.plotly_chart(figure, use_container_width=True)
        else:
            st.info("Aucun document publie pour le moment.")

    st.caption("Documents publies par filiere")
    repartition_filiere = stats.documents_par_filiere()
    if repartition_filiere:
        df = pd.DataFrame(repartition_filiere)
        figure = px.bar(df, x="filiere", y="total")
        figure.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
        st.plotly_chart(figure, use_container_width=True)

    st.divider()
    colonne_documents, colonne_utilisateurs = st.columns(2)

    with colonne_documents:
        st.caption("Documents recemment ajoutes")
        for document in archive_manager.documents_recents(6):
            st.markdown(
                f"""
                <div class="carte carte-document">
                    <strong>{document.titre}</strong><br>
                    <span style="color:#6B7280; font-size:0.85rem;">
                        {document.libelle_type} - {document.filiere} - {document.niveau} - {formater_date(document.date_ajout, avec_heure=False)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with colonne_utilisateurs:
        st.caption("Utilisateurs recemment connectes")
        for utilisateur in gestion_utilisateurs.utilisateurs_recemment_connectes(6):
            st.markdown(
                f"""
                <div class="carte carte-document">
                    <strong>{utilisateur.nom_complet}</strong><br>
                    <span style="color:#6B7280; font-size:0.85rem;">
                        {LIBELLES_ROLE.get(utilisateur.role, utilisateur.role)} - derniere connexion : {formater_date(utilisateur.derniere_connexion)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def page_moderation_documents() -> None:
    exiger_role("administrateur", "enseignant")
    st.subheader("Validation des documents")

    en_attente = archive_manager.documents_en_attente()
    if not en_attente:
        st.info("Aucun document en attente de validation.")
        return

    for document in en_attente:
        with st.container(border=True):
            st.markdown(f"**{document.titre}**")
            st.caption(
                f"{document.libelle_type} - {document.cycle} - {document.filiere} - "
                f"{document.niveau} - {document.annee_academique}"
            )
            if document.description:
                st.write(document.description)

            colonne_validation, colonne_rejet, colonne_motif = st.columns([1, 1, 2])
            with colonne_validation:
                if st.button("Valider", key=f"valider_{document.id}", icon=icone("FileText")):
                    archive_manager.valider_document(document.id, utilisateur_courant().id)
                    st.rerun()
            with colonne_rejet:
                motif = st.session_state.get(f"motif_{document.id}", "")
                if st.button("Rejeter", key=f"rejeter_{document.id}", icon=icone("Trash")):
                    archive_manager.rejeter_document(
                        document.id, utilisateur_courant().id, motif or "Non motive"
                    )
                    st.rerun()
            with colonne_motif:
                st.text_input(
                    "Motif de rejet (optionnel)",
                    key=f"motif_{document.id}",
                    label_visibility="collapsed",
                    placeholder="Motif de rejet (optionnel)",
                )


def page_gestion_utilisateurs() -> None:
    exiger_role("administrateur")
    st.subheader("Gestion des comptes")

    terme = st.text_input("Rechercher un utilisateur", placeholder="Nom, prenom, matricule ou e-mail")
    liste = gestion_utilisateurs.rechercher_utilisateurs(terme) if terme else gestion_utilisateurs.lister_utilisateurs()

    for utilisateur in liste:
        with st.container(border=True):
            colonne_info, colonne_role, colonne_statut, colonne_action = st.columns([3, 2, 1, 1])
            with colonne_info:
                st.markdown(f"**{utilisateur.nom_complet}**")
                st.caption(f"{utilisateur.matricule} - {utilisateur.email}")
            with colonne_role:
                st.write(LIBELLES_ROLE.get(utilisateur.role, utilisateur.role))
                st.caption(f"{utilisateur.filiere or '-'} - {utilisateur.niveau or '-'}")
            with colonne_statut:
                etiquette = "valide" if utilisateur.statut == "actif" else "rejete"
                st.markdown(
                    f'<span class="etiquette-statut etiquette-{etiquette}">{utilisateur.statut}</span>',
                    unsafe_allow_html=True,
                )
            with colonne_action:
                if utilisateur.statut == "actif":
                    if st.button("Suspendre", key=f"suspendre_{utilisateur.id}"):
                        gestion_utilisateurs.suspendre_utilisateur(utilisateur.id)
                        st.rerun()
                else:
                    if st.button("Reactiver", key=f"reactiver_{utilisateur.id}"):
                        gestion_utilisateurs.reactiver_utilisateur(utilisateur.id)
                        st.rerun()


def page_journal_systeme() -> None:
    exiger_role("administrateur")
    st.subheader("Journal systeme")

    lignes = recuperer_tous("SELECT * FROM logs ORDER BY date_heure DESC LIMIT 200")
    if not lignes:
        st.info("Aucune entree dans le journal systeme.")
        return

    df = pd.DataFrame([dict(l) for l in lignes])
    df = df.rename(columns={
        "date_heure": "Date",
        "matricule": "Utilisateur",
        "action": "Action",
        "adresse_ip": "Adresse IP",
        "resultat": "Resultat",
        "details": "Details",
    })
    colonnes_affichees = ["Date", "Utilisateur", "Action", "Adresse IP", "Resultat", "Details"]
    st.dataframe(df[colonnes_affichees], use_container_width=True, hide_index=True)
