PRAGMA foreign_keys = ON;

-------------------------------------------------
-- USERS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS users(

id INTEGER PRIMARY KEY AUTOINCREMENT,

nom TEXT NOT NULL,

prenom TEXT NOT NULL,

matricule TEXT UNIQUE NOT NULL,

email TEXT UNIQUE,

filiere TEXT NOT NULL,

niveau TEXT NOT NULL,

role TEXT NOT NULL CHECK(

role IN(

'administrateur',
'enseignant',
'etudiant',
'contributeur'

)

),

password_hash TEXT NOT NULL,

photo TEXT,

est_actif INTEGER DEFAULT 1,

tentatives_connexion INTEGER DEFAULT 0,

date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,

derniere_connexion DATETIME

);


-------------------------------------------------
-- DOCUMENTS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS subjects(

id INTEGER PRIMARY KEY AUTOINCREMENT,

titre TEXT NOT NULL,

description TEXT,

cycle TEXT,

filiere TEXT,

niveau TEXT,

annee INTEGER,

type_document TEXT,

enseignant_id INTEGER,

auteur_id INTEGER,

pdf_path TEXT,

version INTEGER DEFAULT 1,

statut TEXT DEFAULT 'brouillon'

CHECK(

statut IN(

'brouillon',
'en_attente',
'publie',
'rejete',
'archive',
'corbeille'

)

),

est_payant INTEGER DEFAULT 0,

prix INTEGER DEFAULT 300,

mode_paiement TEXT,

date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,

date_validation DATETIME,

FOREIGN KEY(enseignant_id)

REFERENCES users(id),

FOREIGN KEY(auteur_id)

REFERENCES users(id)

);


-------------------------------------------------
-- DOWNLOADS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS downloads(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

subject_id INTEGER,

date_download DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id),

FOREIGN KEY(subject_id)

REFERENCES subjects(id)

);


-------------------------------------------------
-- FAVORITES
-------------------------------------------------

CREATE TABLE IF NOT EXISTS favorites(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

subject_id INTEGER,

date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id),

FOREIGN KEY(subject_id)

REFERENCES subjects(id)

);


-------------------------------------------------
-- COMMENTS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS comments(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

subject_id INTEGER,

contenu TEXT,

date_comment DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id),

FOREIGN KEY(subject_id)

REFERENCES subjects(id)

);


-------------------------------------------------
-- PRIVATE MESSAGES
-------------------------------------------------

CREATE TABLE IF NOT EXISTS messages(

id INTEGER PRIMARY KEY AUTOINCREMENT,

expediteur_id INTEGER,

destinataire_id INTEGER,

contenu TEXT,

date_message DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(expediteur_id)

REFERENCES users(id),

FOREIGN KEY(destinataire_id)

REFERENCES users(id)

);


-------------------------------------------------
-- REVIEWS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS reviews(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

note INTEGER,

commentaire TEXT,

date_review DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id)

);


-------------------------------------------------
-- ANNOUNCEMENTS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS announcements(

id INTEGER PRIMARY KEY AUTOINCREMENT,

titre TEXT,

contenu TEXT,

auteur_id INTEGER,

date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(auteur_id)

REFERENCES users(id)

);


-------------------------------------------------
-- NOTIFICATIONS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS notifications(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

message TEXT,

type_notification TEXT,

est_lu INTEGER DEFAULT 0,

date_notification DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id)

);


-------------------------------------------------
-- PAYMENTS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS payments(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

subject_id INTEGER,

montant INTEGER DEFAULT 300,

mode_paiement TEXT DEFAULT 'presentiel',

statut TEXT DEFAULT 'en_attente'

CHECK(

statut IN(

'en_attente',
'valide',
'refuse'

)

),

date_paiement DATETIME,

valide_par INTEGER,

FOREIGN KEY(user_id)

REFERENCES users(id),

FOREIGN KEY(subject_id)

REFERENCES subjects(id),

FOREIGN KEY(valide_par)

REFERENCES users(id)

);


-------------------------------------------------
-- REPORTS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS reports(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

subject_id INTEGER,

motif TEXT,

date_report DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id),

FOREIGN KEY(subject_id)

REFERENCES subjects(id)

);


-------------------------------------------------
-- SETTINGS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS settings(

id INTEGER PRIMARY KEY AUTOINCREMENT,

setting_key TEXT UNIQUE,

setting_value TEXT

);


-------------------------------------------------
-- LOGS
-------------------------------------------------

CREATE TABLE IF NOT EXISTS logs(

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER,

action TEXT,

adresse_ip TEXT,

resultat TEXT,

date_action DATETIME DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id)

REFERENCES users(id)

);
