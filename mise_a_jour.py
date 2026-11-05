import subprocess
import sys
from datetime import datetime
from pathlib import Path


def mise_a_jour():
    dossier = Path(__file__).resolve().parent
    journal = dossier / "data" / "mises_a_jour.log"
    journal.parent.mkdir(exist_ok=True)

    with journal.open("a", encoding="utf-8") as fichier:
        fichier.write(
            f"\nDébut : {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        )
        fichier.flush()

        for script in ["export_tmdb.py", "import_sql.py"]:
            print(f"Exécution de {script}...")

            resultat = subprocess.run(
                [sys.executable, "-X", "utf8", "-u", str(dossier / script)],
                cwd=dossier,
                stdout=fichier,
                stderr=subprocess.STDOUT
            )

            fichier.flush()

            if resultat.returncode != 0:
                raise RuntimeError(
                    f"Échec de {script}. Consulte {journal}"
                )

        fichier.write(
            f"Fin : {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        )

    print("Mise à jour terminée.")
    print(f"Journal : {journal}")


if __name__ == "__main__":
    try:
        mise_a_jour()
    except (OSError, RuntimeError) as erreur:
        print(f"Échec : {erreur}")
        sys.exit(1)