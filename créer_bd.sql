DROP TABLE IF EXISTS taches;
DROP TABLE IF EXISTS projets;
DROP TABLE IF EXISTS montages;
DROP TABLE IF EXISTS laboratoires;
DROP TABLE IF EXISTS groupes;

CREATE TABLE groupes (
    id              INTEGER PRIMARY KEY,
    nom             TEXT UNIQUE,
    responsable     TEXT,
    description     TEXT
);

CREATE TABLE laboratoires (
    id              INTEGER PRIMARY KEY,
    local           TEXT UNIQUE,
    groupe          TEXT,
    responsable     TEXT,
    FOREIGN KEY (groupe) REFERENCES groupes(nom)
);

CREATE TABLE montages (
    id              INTEGER PRIMARY KEY,
    nom             TEXT UNIQUE,
    groupe          TEXT,
    laboratoire     TEXT,
    responsable     TEXT,
    description     TEXT,
    FOREIGN KEY (groupe) REFERENCES groupes(nom),
    FOREIGN KEY (laboratoire) REFERENCES laboratoires(local)
);

CREATE TABLE projets (
    id              INTEGER PRIMARY KEY,
    nom             TEXT UNIQUE,
    montage         TEXT,
    responsable     TEXT,
    description     TEXT,
    FOREIGN KEY (montage) REFERENCES montages(nom)
);

CREATE TABLE taches (
    id              INTEGER PRIMARY KEY,
    creation        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    maj             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    projet          TEXT UNIQUE,
    parent          TEXT DEFAULT NULL,
    description     TEXT,
    temps           FLOAT,
    fini            BOOLEAN,
    FOREIGN KEY (parent) REFERENCES taches(id),
    FOREIGN KEY (projet) REFERENCES projets(nom)
);
