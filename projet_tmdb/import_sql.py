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

    with source.open(encoding="utf-8") as fichier:
        films = [
            json.loads(ligne)
            for ligne in fichier
            if ligne.strip()
        ]

    print("Création du tableau JSON...")

    with destination.open("w", encoding="utf-8") as fichier:
        json.dump(films, fichier, ensure_ascii=False)

    print(f"Tableau JSON créé : {destination.name}")

    df = pd.DataFrame(films)
    del films

    colonnes = [
        "id",
        "original_title",
        "adult",
        "popularity",
        "video"
    ]

    df = df[colonnes]
    df["adult"] = df["adult"].fillna(False).astype(bool)
    df["video"] = df["video"].fillna(False).astype(bool)

    if df["id"].isna().any() or df["id"].duplicated().any():
        raise ValueError("Certains identifiants sont absents ou dupliqués.")

    print("\nAperçu du DataFrame :")
    print(df.head().to_string(index=False))
    print(f"\nNombre de films : {len(df):,}")

    lignes = (
        (
            int(identifiant),
            titre,
            int(adulte),
            float(popularite),
            int(video)
        )
        for identifiant, titre, adulte, popularite, video
        in df.itertuples(index=False, name=None)
    )

    connexion = sqlite3.connect(base)

    try:
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

            connexion.executemany("""
                INSERT INTO films (
                    id, original_title, adult, popularity, video
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    original_title = excluded.original_title,
                    adult = excluded.adult,
                    popularity = excluded.popularity,
                    video = excluded.video
            """, lignes)

            nombre = connexion.execute(
                "SELECT COUNT(*) FROM films"
            ).fetchone()[0]

            manquants = connexion.execute(
                "SELECT COUNT(*) FROM films WHERE original_title IS NULL"
            ).fetchone()[0]

            if nombre < len(df) or manquants:
                raise RuntimeError("La vérification de l'import a échoué.")

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