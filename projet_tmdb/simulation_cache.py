import asyncio
import time
from collections import Counter

from simulation_async import ROUTES, requete_robuste


class CacheAPI:
    def __init__(self, duree=3600, horloge=time.monotonic):
        self.duree = duree
        self.horloge = horloge
        self.cache = {}
        self.statistiques = Counter()

        # un verrou par route pour eviter les appels en double
        self.verrous = {}

        for url in ROUTES:
            self.verrous[url] = asyncio.Lock()

    async def get(self, url):
        if url not in self.verrous:
            raise ValueError("Route inconnue.")

        async with self.verrous[url]:
            entree = self.cache.get(url)

            if entree is not None:
                expiration, donnees = entree

                # si le cache est encore valide on reprend les donnees
                if self.horloge() < expiration:
                    self.statistiques["lectures_cache"] += 1
                    return donnees.copy()

                # sinon on supprime les anciennes donnees
                del self.cache[url]
                self.statistiques["expirations"] += 1

            succes = await requete_robuste(
                url,
                self.statistiques
            )

            if not succes:
                raise RuntimeError(f"Échec de la requête vers {url}")

            self.statistiques["lectures_api"] += 1

            # la version sert a voir si les donnees ont ete rechargees
            donnees = {
                "url": url,
                "message": "Données simulées",
                "version": self.statistiques["lectures_api"]
            }

            expiration = self.horloge() + self.duree

            # on garde une copie pour proteger le contenu du cache
            self.cache[url] = (expiration, donnees.copy())

            return donnees


class HorlogeSimulee:
    def __init__(self):
        self.temps = 0

    def maintenant(self):
        return self.temps

    def avancer(self, secondes):
        self.temps += secondes


async def demonstration():
    # cette horloge permet de tester sans attendre une heure
    horloge = HorlogeSimulee()

    client = CacheAPI(
        duree=3600,
        horloge=horloge.maintenant
    )

    url = ROUTES[0]

    print("1. Premier appel : récupération depuis l'API")
    resultat1 = await client.get(url)
    print(resultat1)

    print("\n2. Deuxième appel : récupération depuis le cache")
    resultat2 = await client.get(url)
    print(resultat2)

    # assert arrete le test si le resultat est incorrect
    assert resultat1 == resultat2
    assert client.statistiques["lectures_api"] == 1
    assert client.statistiques["lectures_cache"] == 1

    print("\n3. Cent appels simultanés sur la même route")

    appels = []

    for _ in range(100):
        appels.append(client.get(url))

    resultats = await asyncio.gather(*appels)

    for resultat in resultats:
        assert resultat == resultat1

    assert client.statistiques["lectures_api"] == 1

    print("Les 100 appels utilisent le cache.")

    print("\n4. Simulation du passage de 3 601 secondes")

    # on avance le temps pour faire expirer le cache
    horloge.avancer(3601)

    resultat3 = await client.get(url)
    print(resultat3)

    assert resultat3["version"] != resultat1["version"]
    assert client.statistiques["lectures_api"] == 2
    assert client.statistiques["expirations"] == 1

    print("Le cache a expiré : nouvel appel à l'API.")

    print("\nBilan")
    print(f"Lectures API : {client.statistiques['lectures_api']}")
    print(f"Lectures cache : {client.statistiques['lectures_cache']}")
    print(f"Expirations : {client.statistiques['expirations']}")
    print(
        "Appels simulés, retries inclus : "
        f"{client.statistiques['appels_simules']}"
    )
    print("\nTous les tests du cache sont validés.")


if __name__ == "__main__":
    try:
        asyncio.run(demonstration())

    except RuntimeError as erreur:
        print(f"Erreur simulée : {erreur}")
        print("Relance le script pour refaire la démonstration.")