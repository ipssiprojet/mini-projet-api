import sys

import requests

from export_tmdb import telecharger_export
from import_sql import importer_films


def mise_a_jour():
    print("1. Téléchargement de l'export...")
    telecharger_export()

    # cette etape se lance seulement si le telechargement a reussi
    print("\n2. Mise à jour de la base SQL...")
    importer_films()

    print("\nMise à jour terminée.")


if __name__ == "__main__":
    try:
        mise_a_jour()

    except (OSError, ValueError, RuntimeError, requests.RequestException) as erreur:
        print(f"Échec : {erreur}")
        sys.exit(1)

    except Exception as erreur:
        print(f"Erreur inattendue : {erreur}")
        sys.exit(1)