import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN")


def requete_api(url, params=None, max_tentatives=3):
    if not TOKEN:
        raise ValueError("Le jeton TMDB est absent du fichier .env.")

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

    for tentative in range(1, max_tentatives + 1):
        attente = 2 ** (tentative - 1)

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

            if response.status_code == 429:
                try:
                    attente = max(
                        attente,
                        float(response.headers.get("Retry-After", attente))
                    )
                except ValueError:
                    pass

            print(
                f"Erreur {response.status_code}. "
                f"Nouvelle tentative dans {attente} s."
            )
            time.sleep(attente)
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

    return {
        "titre": movie["title"],
        "date_sortie": movie["release_date"],
        "genres": [genre["name"] for genre in movie["genres"]],
        "popularite": movie["popularity"],
        "note_moyenne": movie["vote_average"]
    }


if __name__ == "__main__":
    try:
        film = get_movie_details(550) 

        for champ, valeur in film.items():
            print(f"{champ} : {valeur}")

    except (ValueError, RuntimeError, requests.RequestException) as erreur:
        print(f"Échec : {erreur}")