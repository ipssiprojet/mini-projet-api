import asyncio
import random
import time
from collections import Counter

ROUTES = [
    "https://api.example.com/data1",
    "https://api.example.com/data2",
    "https://api.example.com/data3"
]


async def simuler_api(url):
    await asyncio.sleep(0.001)

    statut = random.choices(
        [200, 429, 500, 503, 404],
        weights=[94, 2, 1, 1, 2]
    )[0]

    return {
        "statut": statut,
        "url": url,
        "retry_after": 0.01
    }


async def requete_robuste(url, statistiques, max_tentatives=3):
    for tentative in range(max_tentatives):
        statistiques["appels_simules"] += 1

        try:
            reponse = await simuler_api(url)
        except (OSError, TimeoutError):
            statut = "reseau"
        else:
            statut = reponse["statut"]

        if statut == 200:
            return True

        if statut not in (429, 500, 502, 503, 504, "reseau"):
            statistiques[f"erreur_{statut}"] += 1
            return False

        if tentative == max_tentatives - 1:
            statistiques["tentatives_epuisees"] += 1
            return False

        statistiques["retries"] += 1
        attente = 0.01 * (2 ** tentative)

        if statut == 429:
            attente = max(attente, reponse["retry_after"])

        await asyncio.sleep(attente)

    return False


async def executer_simulation(nombre_requetes=100_000, concurrence=100):
    file = asyncio.Queue(maxsize=concurrence * 2)
    statistiques = Counter()
    debut = time.perf_counter()

    async def worker():
        while True:
            url = await file.get()

            try:
                if url is None:
                    return

                succes = await requete_robuste(url, statistiques)

                statistiques["succes" if succes else "echecs"] += 1
                statistiques[url] += 1
            finally:
                file.task_done()

    workers = [
        asyncio.create_task(worker())
        for _ in range(concurrence)
    ]

    for numero in range(nombre_requetes):
        await file.put(ROUTES[numero % len(ROUTES)])

    for _ in workers:
        await file.put(None)

    await file.join()
    await asyncio.gather(*workers)

    duree = time.perf_counter() - debut

    print(f"Requêtes demandées : {nombre_requetes:,}")
    print(f"Concurrence maximale : {concurrence}")
    print(f"Succès : {statistiques['succes']:,}")
    print(f"Échecs : {statistiques['echecs']:,}")
    print(f"Appels simulés, retries inclus : {statistiques['appels_simules']:,}")
    print(f"Nouvelles tentatives : {statistiques['retries']:,}")
    print(f"Durée : {duree:.2f} secondes")
    print(f"Débit : {nombre_requetes / duree:.0f} requêtes/seconde")

    print("\nRépartition par route :")

    for url in ROUTES:
        print(f"{url} : {statistiques[url]:,}")


if __name__ == "__main__":
    asyncio.run(executer_simulation(nombre_requetes=1_000_000))