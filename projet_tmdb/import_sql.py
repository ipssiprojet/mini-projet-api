import sys
import json
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd


def importer_films():
    dossier = Path(__file__).resolve().parent / "data"
    date_export = date.today().strftime("%m_%d_%Y")

    source = dossier / f"movie_ids_{date_export}.json"
    destination = dossier / f"movie_ids_{date_export}_array.json"
    base = dossier / "tmdb.db"

    if not source.exists():
        raise FileNotFoundError(
            f"Export introuvable : {source.name}. "
            "Lance d'abord export_tmdb.py."
        )

    print("Lecture de l'export...")

    films = []

    # chaque ligne contient les donnees d'un film
    with source.open(encoding="utf-8") as fichier:
        for ligne in fichier:
            if ligne.strip():
                films.append(json.loads(ligne))

    print("Création du tableau JSON...")

    with destination.open("w", encoding="utf-8") as fichier:
        json.dump(films, fichier, ensure_ascii=False)

    print(f"Tableau JSON créé : {destination.name}")

    df = pd.DataFrame(films)

    # on libere la liste maintenant que le DataFrame est cree
    del films

    colonnes = [
        "id",
        "original_title",
        "adult",
        "popularity",
        "video"
    ]

    df = df[colonnes].copy()

    # on remplace les valeurs manquantes dans ces deux colonnes
    df["adult"] = df["adult"].fillna(False).astype(bool)
    df["video"] = df["video"].fillna(False).astype(bool)

    if df["id"].isna().any():
        raise ValueError("Certains identifiants sont absents.")

    if df["id"].duplicated().any():
        raise ValueError("Certains identifiants sont dupliqués.")

    print("\nAperçu du DataFrame :")
    print(df.head().to_string(index=False))
    print(f"\nNombre de films : {len(df):,}")

    requete_insertion = """
        INSERT INTO films (
            id, original_title, adult, popularity, video
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            original_title = excluded.original_title,
            adult = excluded.adult,
            popularity = excluded.popularity,
            video = excluded.video
    """

    connexion = sqlite3.connect(base)

    try:
        # si l'import echoue les changements sont annules
        with connexion:
            connexion.execute("""
                CREATE TABLE IF NOT EXISTS films (
                    id INTEGER PRIMARY KEY,
                    original_title TEXT NOT NULL,
                    adult INTEGER NOT NULL,
                    popularity REAL NOT NULL,
                    video INTEGER NOT NULL
                )
            """)

            lot = []

            # itertuples permet de parcourir les lignes du DataFrame
            for ligne in df.itertuples(index=False, name=None):
                identifiant, titre, adulte, popularite, video = ligne

                lot.append((
                    int(identifiant),
                    titre,
                    int(adulte),
                    float(popularite),
                    int(video)
                ))

                # on envoie les films par groupes de 5000
                if len(lot) == 5000:
                    connexion.executemany(requete_insertion, lot)
                    lot.clear()

            # on ajoute les derniers films s'il en reste
            if lot:
                connexion.executemany(requete_insertion, lot)

            resultat = connexion.execute(
                "SELECT COUNT(*) FROM films"
            ).fetchone()

            nombre = resultat[0]

            # la base peut aussi contenir des films des anciens exports
            if nombre < len(df):
                raise RuntimeError(
                    "Le nombre de films dans la base est insuffisant."
                )

        print(f"\nImport terminé : {len(df):,} films traités.")
        print(f"Total dans la table films : {nombre:,}")
        print(f"Base SQL : {base}")

        apercu = pd.read_sql_query(
            """
            SELECT id, original_title, popularity
            FROM films
            ORDER BY popularity DESC, id
            LIMIT 5
            """,
            connexion
        )

        print("\nLes cinq films les plus populaires de la base :")
        print(apercu.to_string(index=False))

    finally:
        connexion.close()


if __name__ == "__main__":
    try:
        importer_films()

    except (OSError, ValueError, sqlite3.Error, RuntimeError) as erreur:
        print(f"Échec : {erreur}")
        sys.exit(1)