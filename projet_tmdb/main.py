import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# On charge le fichier .env situé dans le même dossier que le script
dossier = Path(__file__).resolve().parent
load_dotenv(dossier / ".env")

TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")


def requete_api(url, params=None, max_tentatives=3):
    if not TOKEN:
        raise ValueError(
            "Le jeton TMDB est absent. Vérifie la variable "
            "TMDB_READ_ACCESS_TOKEN."
        )

    if max_tentatives < 1:
        raise ValueError("Il faut autoriser au moins une tentative.")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "accept": "application/json"
    }

    erreurs = {
        400: "Requête incorrecte.",
        401: "Jeton absent ou invalide.",
        403: "Accès interdit.",
        404: "Ressource introuvable : vérifie l'identifiant."
    }

    attente = 1

    for tentative in range(1, max_tentatives + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

        except (requests.ConnectionError, requests.Timeout) as erreur:
            if tentative == max_tentatives:
                raise RuntimeError(
                    "Impossible de contacter l'API après plusieurs tentatives."
                ) from erreur

            print(f"Problème réseau. Nouvelle tentative dans {attente} s.")
            time.sleep(attente)
            attente *= 2
            continue

        if response.status_code in erreurs:
            raise RuntimeError(
                f"Erreur {response.status_code} : "
                f"{erreurs[response.status_code]}"
            )

        if response.status_code in (429, 500, 502, 503, 504):
            if tentative == max_tentatives:
                raise RuntimeError(
                    f"Erreur {response.status_code} : "
                    "nombre maximal de tentatives atteint."
                )

            pause = attente

            if response.status_code == 429:
                try:
                    delai_serveur = float(
                        response.headers.get("Retry-After", attente)
                    )

                    if delai_serveur > pause:
                        pause = delai_serveur

                except ValueError:
                    pass

            print(
                f"Erreur {response.status_code}. "
                f"Nouvelle tentative dans {pause} s."
            )

            time.sleep(pause)
            attente *= 2
            continue

        response.raise_for_status()

        try:
            return response.json()

        except ValueError as erreur:
            raise RuntimeError(
                "La réponse de l'API n'est pas un JSON valide."
            ) from erreur


def get_movie_details(movie_id):
    if isinstance(movie_id, bool):
        raise ValueError("L'identifiant doit être un entier positif.")

    if not str(movie_id).isdigit() or int(movie_id) <= 0:
        raise ValueError("L'identifiant doit être un entier positif.")

    movie = requete_api(
        f"https://api.themoviedb.org/3/movie/{int(movie_id)}",
        params={"language": "fr-FR"}
    )

    genres = []

    for genre in movie["genres"]:
        genres.append(genre["name"])

    chemin_affiche = movie.get("poster_path")

    affiche = (
        f"https://image.tmdb.org/t/p/w500{chemin_affiche}"
        if chemin_affiche
        else None
    )

    return {
        "titre": movie["title"],
        "date_sortie": movie["release_date"],
        "genres": genres,
        "popularite": movie["popularity"],
        "note_moyenne": movie["vote_average"],
        "affiche": affiche
    }


if __name__ == "__main__":
    try:
        film = get_movie_details(550)

        for champ, valeur in film.items():
            print(f"{champ} : {valeur}")

    except (ValueError, RuntimeError, requests.RequestException) as erreur:
        print(f"Échec : {erreur}")