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
    # on simule un petit delai sans appeler de vrai serveur
    await asyncio.sleep(0.001)

    # on met plus de succes que d'erreurs
    statut = random.choices(
        [200, 429, 500, 503, 404],
        weights=[94, 2, 1, 1, 2]
    )[0]

    return {
        "statut": statut,
        "retry_after": 0.01
    }


async def requete_robuste(url, statistiques, max_tentatives=3):
    attente = 0.01

    for tentative in range(max_tentatives):
        statistiques["appels_simules"] += 1

        reponse = await simuler_api(url)
        statut = reponse["statut"]

        if statut == 200:
            return True

        # pour les erreurs definitive on reessaye pas
        if statut not in (429, 500, 502, 503, 504):
            statistiques[f"erreur_{statut}"] += 1
            return False

        if tentative == max_tentatives - 1:
            statistiques["tentatives_epuisees"] += 1
            return False

        statistiques["retries"] += 1
        pause = attente

        # si le serveur demande plus de temps on prend son delai
        if statut == 429:
            if reponse["retry_after"] > pause:
                pause = reponse["retry_after"]

        # les autres taches continuent pendant la pause
        await asyncio.sleep(pause)
        attente = attente * 2

    return False


async def executer_simulation(nombre_requetes=100_000, concurrence=100):
    if nombre_requetes < 1 or concurrence < 1:
        raise ValueError(
            "Le nombre de requêtes et la concurrence doivent être positifs."
        )

    # la file est limiter pour pas tout garder en memoire
    file = asyncio.Queue(maxsize=concurrence * 2)
    statistiques = Counter()
    debut = time.perf_counter()

    async def worker():
        while True:
            url = await file.get()

            try:
                # None veut dire que le worker peut s'arreter
                if url is None:
                    return

                succes = await requete_robuste(url, statistiques)

                if succes:
                    statistiques["succes"] += 1
                else:
                    statistiques["echecs"] += 1

                statistiques[url] += 1

            finally:
                # on signale que cet element est terminer
                file.task_done()

    workers = []

    for _ in range(concurrence):
        workers.append(asyncio.create_task(worker()))

    # on alterne entre les 3 routes avec le modulo
    for numero in range(nombre_requetes):
        url = ROUTES[numero % len(ROUTES)]
        await file.put(url)

    # on met un signal d'arret pour chaque worker
    for _ in workers:
        await file.put(None)

    # on attend que la file et les workers soient terminer
    await file.join()
    await asyncio.gather(*workers)

    duree = time.perf_counter() - debut

    print(f"Requêtes demandées : {nombre_requetes:,}")
    print(f"Concurrence maximale : {concurrence}")
    print(f"Succès : {statistiques['succes']:,}")
    print(f"Échecs : {statistiques['echecs']:,}")
    print(
        f"Appels simulés, retries inclus : "
        f"{statistiques['appels_simules']:,}"
    )
    print(f"Nouvelles tentatives : {statistiques['retries']:,}")
    print(f"Durée : {duree:.2f} secondes")
    print(f"Débit : {nombre_requetes / duree:.0f} requêtes/seconde")

    print("\nRépartition par route :")

    for url in ROUTES:
        print(f"{url} : {statistiques[url]:,}")


if __name__ == "__main__":
    asyncio.run(executer_simulation(nombre_requetes=1_000_000))