# SOURCE ISABEE

Plateforme institutionnelle de gestion des ressources pedagogiques de
l'ISABEE : anciennes epreuves, sujets de controle continu, examens,
corriges, travaux pratiques et supports de cours.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

Au premier lancement, aucun compte n'existe : l'application affiche un
formulaire de creation du premier compte administrateur. La base de
donnees SQLite et le dossier de stockage des fichiers PDF sont crees
automatiquement dans `data/`.

## Architecture du projet

```
source_isabee/
    app.py               point d'entree, routage, pages communes
    database.py          acces a SQLite (connexion, initialisation)
    auth.py              authentification, hachage, sessions
    models.py            structures de donnees (Utilisateur, Document...)
    admin.py              pages reservees a l'administration
    archive_manager.py   gestion documentaire (CRUD, validation, recherche)
    statistics.py        agregations pour le tableau de bord
    settings.py          parametres systeme
    users.py             gestion des comptes utilisateurs
    utils.py             fonctions transverses (journal, fichiers, dates)
    schema.sql           schema SQL complet
    requirements.txt     dependances Python
    assets/
        style.css        identite visuelle institutionnelle
    data/                 (cree automatiquement, non versionne)
        source_isabee.db
        documents/
```

### Role de chaque fichier

| Fichier | Role |
|---|---|
| `app.py` | Point d'entree Streamlit. Configure la page, initialise la base au demarrage, affiche la connexion ou la configuration initiale, construit le menu de navigation selon le role, et route vers la bonne page. Contient les pages communes a tous les roles : bibliotheque numerique, depot de document, favoris, profil. |
| `database.py` | Seul module autorise a ouvrir une connexion SQLite. Fournit `get_connection()`, `initialiser_base()` (execution de `schema.sql`) et des fonctions generiques `executer`, `recuperer_un`, `recuperer_tous`. |
| `auth.py` | Authentification par matricule et mot de passe. Hachage SHA-256 sale et etire, limitation des tentatives, gestion de la session via `st.session_state`, fonctions de controle d'acces par role (`exiger_role`). |
| `models.py` | Dataclasses `Utilisateur`, `Document`, `EntreeJournal` et constantes partagees (roles, types de documents, libelles d'affichage). Aucune logique d'acces aux donnees. |
| `admin.py` | Pages reservees a l'administration : tableau de bord (indicateurs, graphiques Plotly), gestion des comptes, validation des documents, journal systeme. |
| `archive_manager.py` | Cycle de vie des documents : ajout, modification, suppression, validation, rejet, recherche multicritere, telechargements, favoris. |
| `statistics.py` | Calcule les indicateurs et series de donnees consommes par `admin.py` pour les graphiques. Ne dessine rien. |
| `settings.py` | Lecture et ecriture des parametres systeme (table `settings`) : nom de l'etablissement, taille maximale des fichiers, regles de moderation. |
| `users.py` | Creation, modification, suspension, recherche des comptes utilisateurs. |
| `utils.py` | Journalisation systeme (`journaliser`), validation et enregistrement des fichiers PDF, formatage de dates, mapping d'icones professionnelles, chargement de la feuille de style. |
| `assets/style.css` | Palette bleu institutionnel / blanc / gris clair, cartes sobres, bordures discretes, coins arrondis, ombres legeres. |

### Principe de dependance

`database.py` et `models.py` ne dependent d'aucun autre module du
projet. `utils.py` et `auth.py` ne dependent que de `database.py` et
`models.py`. Les modules metier (`users.py`, `archive_manager.py`,
`statistics.py`, `settings.py`) dependent de la couche precedente mais
jamais de `app.py` ni `admin.py`. Enfin, `admin.py` et `app.py`
orchestrent l'ensemble. Cette hierarchie evite les dependances
circulaires et permet de tester chaque module metier independamment
de l'interface.

## Roles et droits

| Role | Acces |
|---|---|
| Etudiant | Bibliotheque numerique, favoris, profil |
| Enseignant | Idem etudiant, depot de document, validation des documents |
| Contributeur | Idem etudiant, depot de document |
| Administrateur | Acces complet : tableau de bord, gestion des comptes, validation, journal systeme, parametres |

## Icones

L'interface n'utilise aucun emoji. Les icones demandees (Home,
FileText, Users, Search, Download, Settings, BarChart, Trash, Edit,
Bell) sont fournies par l'ensemble natif "Material Symbols" de
Streamlit (`icon=":material/nom:"`), seul systeme d'icones professionnel
disponible nativement dans ce framework. Le mapping est centralise
dans `utils.icone()`.

## Limite assumee sur le hachage des mots de passe

Le cahier des charges impose SHA-256. Ce module l'implemente avec un
sel unique par compte et un etirement de cle (150 000 iterations) afin
de limiter le risque d'attaque par force brute. Pour un deploiement en
production accessible depuis Internet, un algorithme dedie aux mots de
passe (Argon2id ou bcrypt) reste preferable a toute construction
maison autour de SHA-256, y compris etiree.
