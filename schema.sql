-- =====================================================================
-- SOURCE ISABEE - Schema de base de donnees
-- SGBD : SQLite 3
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Table : users
-- Comptes de la plateforme (administrateur, enseignant, etudiant,
-- contributeur). Le mot de passe n'est jamais stocke en clair.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    matricule           TEXT    NOT NULL UNIQUE,
    nom                 TEXT    NOT NULL,
    prenom              TEXT    NOT NULL,
    email               TEXT    NOT NULL UNIQUE,
    filiere             TEXT,
    niveau              TEXT,
    role                TEXT    NOT NULL CHECK (role IN ('administrateur', 'enseignant', 'etudiant', 'contributeur')),
    mot_de_passe_hash   TEXT    NOT NULL,
    sel                 TEXT    NOT NULL,
    statut              TEXT    NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'suspendu')),
    date_inscription    TEXT    NOT NULL DEFAULT (datetime('now')),
    derniere_connexion  TEXT
);

-- ---------------------------------------------------------------------
-- Table : subjects
-- Documents pedagogiques : epreuves, sujets de controle continu,
-- examens, corriges, travaux pratiques, supports de cours.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    titre               TEXT    NOT NULL,
    description         TEXT,
    type_document       TEXT    NOT NULL CHECK (type_document IN ('examen', 'controle_continu', 'corrige', 'travaux_pratiques', 'support_cours', 'autre')),
    cycle               TEXT    NOT NULL,
    filiere             TEXT    NOT NULL,
    niveau              TEXT    NOT NULL,
    annee_academique    TEXT    NOT NULL,
    enseignant_id       INTEGER,
    chemin_fichier      TEXT    NOT NULL,
    taille_fichier_ko   INTEGER,
    statut              TEXT    NOT NULL DEFAULT 'en_attente' CHECK (statut IN ('en_attente', 'valide', 'rejete')),
    ajoute_par          INTEGER NOT NULL,
    valide_par          INTEGER,
    date_ajout          TEXT    NOT NULL DEFAULT (datetime('now')),
    date_validation     TEXT,
    motif_rejet         TEXT,
    FOREIGN KEY (enseignant_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (ajoute_par)    REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (valide_par)    REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Table : downloads
-- Historique des telechargements, utilise pour les statistiques.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS downloads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    date_telechargement TEXT    NOT NULL DEFAULT (datetime('now')),
    adresse_ip          TEXT,
    FOREIGN KEY (document_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES users(id)    ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table : favorites
-- Documents marques par un utilisateur pour un acces rapide.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS favorites (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    document_id         INTEGER NOT NULL,
    date_ajout          TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, document_id),
    FOREIGN KEY (user_id)     REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table : comments
-- Remarques deposees sur un document, soumises a moderation.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    contenu             TEXT    NOT NULL,
    statut              TEXT    NOT NULL DEFAULT 'visible' CHECK (statut IN ('visible', 'masque')),
    date_creation       TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES users(id)    ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Table : logs
-- Journal systeme : trace toute action sensible (connexion, ajout,
-- suppression, validation, modification de parametres...).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date_heure          TEXT    NOT NULL DEFAULT (datetime('now')),
    user_id             INTEGER,
    matricule           TEXT,
    action              TEXT    NOT NULL,
    adresse_ip          TEXT,
    resultat            TEXT    NOT NULL CHECK (resultat IN ('succes', 'echec')),
    details              TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Table : settings
-- Parametres globaux de la plateforme, modifiables par un
-- administrateur uniquement.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cle                 TEXT    NOT NULL UNIQUE,
    valeur              TEXT,
    description         TEXT,
    modifie_par         INTEGER,
    date_modification   TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (modifie_par) REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- Index utiles aux recherches multicriteres et aux statistiques
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_subjects_filiere   ON subjects(filiere);
CREATE INDEX IF NOT EXISTS idx_subjects_niveau     ON subjects(niveau);
CREATE INDEX IF NOT EXISTS idx_subjects_annee      ON subjects(annee_academique);
CREATE INDEX IF NOT EXISTS idx_subjects_type       ON subjects(type_document);
CREATE INDEX IF NOT EXISTS idx_subjects_statut     ON subjects(statut);
CREATE INDEX IF NOT EXISTS idx_users_role          ON users(role);
CREATE INDEX IF NOT EXISTS idx_logs_date           ON logs(date_heure);
