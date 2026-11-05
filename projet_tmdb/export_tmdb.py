import sys
import time
import gzip
import json
import shutil
from datetime import date
from pathlib import Path

import requests


def telecharger_export():
    # on construit le nom du fichier avec la date du jour
    date_du_jour = date.today().strftime("%m_%d_%Y")
    nom = f"movie_ids_{date_du_jour}.json.gz"

    url = f"https://files.tmdb.org/p/exports/{nom}"

    dossier = Path(__file__).resolve().parent / "data"
    dossier.mkdir(exist_ok=True)

    chemin_gz = dossier / nom
    chemin_json = chemin_gz.with_suffix("")
    temporaire = dossier / f"{nom}.part"

    attente = 1

    # on fait au maximum 3 tentatives
    for tentative in range(1, 4):
        print(f"Téléchargement : {nom} — tentative {tentative}")

        try:
            with requests.get(url, stream=True, timeout=60) as reponse:
                if reponse.status_code == 404:
                    raise RuntimeError(
                        "Export du jour introuvable. "
                        "Il peut ne pas être encore disponible avant 8 h UTC."
                    )

                if reponse.status_code in (429, 500, 502, 503, 504):
                    if tentative == 3:
                        raise RuntimeError(
                            f"Erreur {reponse.status_code} : "
                            "nombre maximal de tentatives atteint."
                        )

                    pause = attente

                    if reponse.status_code == 429:
                        try:
                            delai = float(
                                reponse.headers.get("Retry-After", attente)
                            )

                            if delai > pause:
                                pause = delai

                        except ValueError:
                            pass

                    print(
                        f"Erreur {reponse.status_code}. "
                        f"Nouvelle tentative dans {pause} s."
                    )

                    time.sleep(pause)
                    attente = attente * 2
                    continue

                reponse.raise_for_status()

                # on ecrit le fichier par morceaux de 1 Mo
                with temporaire.open("wb") as fichier:
                    for bloc in reponse.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if bloc:
                            fichier.write(bloc)

        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.exceptions.ChunkedEncodingError
        ):
            if tentative == 3:
                raise RuntimeError(
                    "Le téléchargement a échoué après trois tentatives."
                )

            print(f"Problème réseau. Nouvelle tentative dans {attente} s.")
            time.sleep(attente)
            attente = attente * 2
            continue

        # on sort de la boucle si le telechargement a reussi
        break

    temporaire.replace(chemin_gz)
    print("Téléchargement terminé.")

    # on ouvre le fichier compresse et on copie son contenu decompresse
    with gzip.open(chemin_gz, "rb") as source:
        with chemin_json.open("wb") as destination:
            shutil.copyfileobj(source, destination)

    print(f"Fichier décompressé : {chemin_json.name}")
    print("\nLes cinq premiers films :")

    with chemin_json.open(encoding="utf-8") as fichier:
        for numero in range(5):
            ligne = fichier.readline()

            if not ligne:
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