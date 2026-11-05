import sys
import gzip
import json
import shutil
from datetime import date
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def telecharger_export():
    date_du_jour = date.today().strftime("%m_%d_%Y")
    nom = f"movie_ids_{date_du_jour}.json.gz"

    url = f"https://files.tmdb.org/p/exports/{nom}"

    dossier = Path(__file__).resolve().parent / "data"
    dossier.mkdir(exist_ok=True)

    chemin_gz = dossier / nom
    chemin_json = chemin_gz.with_suffix("")
    temporaire = chemin_gz.with_suffix(".part")

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True
    )

    print(f"Téléchargement : {nom}")

    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))

        with session.get(url, stream=True, timeout=(10, 120)) as reponse:
            if reponse.status_code == 404:
                raise RuntimeError(
                    "L'export du jour n'est pas encore disponible. "
                    "Réessaie après 8 h UTC."
                )

            reponse.raise_for_status()

            with temporaire.open("wb") as fichier:
                for bloc in reponse.iter_content(chunk_size=1024 * 1024):
                    if bloc:
                        fichier.write(bloc)

    temporaire.replace(chemin_gz)
    print("Téléchargement terminé.")

    with gzip.open(chemin_gz, "rb") as source:
        with chemin_json.open("wb") as destination:
            shutil.copyfileobj(source, destination)

    print(f"Fichier décompressé : {chemin_json.name}")
    print("\nLes cinq premiers films :")

    with chemin_json.open(encoding="utf-8") as fichier:
        for numero, ligne in enumerate(fichier):
            if numero == 5:
                break

            film = json.loads(ligne)
            print(json.dumps(film, ensure_ascii=False, indent=2))

    return chemin_json


if __name__ == "__main__":
    try:
        telecharger_export()
    except (requests.RequestException, OSError, ValueError, RuntimeError) as erreur:
        print(f"Échec : {erreur}")
        sys.exit(1)