# Mini-projets API — IPSSI

Ce dépôt regroupe les deux mini-projets Python réalisés en groupe sur la consommation d'API.
Les deux projets répondent aux mêmes questions communes :

- **Q1** : gérer les erreurs des requêtes (pauses, nouvelles tentatives, codes 429, 5xx, 400, 401, 403, 404)
- **Q2** : envoyer un très grand nombre de requêtes avec `asyncio` et simuler une forte charge sur plusieurs routes
- **Q3** : ajouter un cache avec une expiration d'1 heure et montrer qu'il fonctionne
- présenter les résultats dans une interface **Streamlit**

| Projet | Application en ligne |
|---|---|
| Projet 1 — TMDB | https://mini-projet-api-chnqlc4b2pwfdgnzkzesdc.streamlit.app/ |
| Projet 2 — PokéAPI | https://pokeapi-ipssi.streamlit.app/ |

---

## Projet 1 — TMDB (`projet_tmdb/`)

Consultation de films via l'API TMDB, gestion des erreurs, simulation de forte charge,
cache, import SQLite et interface Streamlit.

Notebook Google Colab : https://colab.research.google.com/drive/1e5D08M7NJ4ZH_aXakpo5RJmxLqvobKEV?authuser=1

### Installation

```bash
cd projet_tmdb
python -m pip install -r requirements.txt
```

Créer un compte sur https://www.themoviedb.org/ et récupérer un jeton d'accès en lecture
(paramètres API). Copier `.env.example` en `.env` puis renseigner le jeton :

```dotenv
TMDB_READ_ACCESS_TOKEN=ton_jeton_ici
```

Le fichier `.env` reste privé et n'est pas envoyé sur GitHub.

### Utilisation (depuis `projet_tmdb/`)

| Commande | Rôle |
|---|---|
| `python main.py` | Informations du film 550 (Fight Club) |
| `python -m unittest test_api -v` | 6 tests automatisés de la gestion des erreurs (sans contacter TMDB) |
| `python simulation_async.py` | Q2 : un million de requêtes sur trois routes, 100 workers, file limitée |
| `python simulation_cache.py` | Q3 : cache d'1 h, expiration testée avec une horloge simulée |
| `python -X utf8 export_tmdb.py` | Téléchargement de l'export quotidien TMDB |
| `python -X utf8 import_sql.py` | Création de la base `data/tmdb.db` (insertions par lots de 5 000) |
| `python -X utf8 mise_a_jour.py` | Mise à jour trimestrielle : téléchargement puis import |
| `python -m streamlit run app.py` | Interface Streamlit |

Les simulations ne contactent pas de serveur réel. Les erreurs étant aléatoires,
les résultats peuvent varier.

L'export du jour est disponible au plus tard à 8 h UTC. La table `films` contient
`id` (clé primaire), `original_title`, `adult`, `popularity` et `video` ; les valeurs
manquantes de `adult` et `video` sont remplacées par `False`. Lors du test du
5 novembre 2026, 1 269 754 films ont été enregistrés.

L'interface permet de rechercher un film par identifiant (cache d'1 h), de rechercher
un titre dans SQLite et de consulter les dix films les plus populaires de la base.

Mise à jour trimestrielle (exemple cron, 5 janvier, avril, juillet et octobre à 10 h) :

```cron
0 10 5 1,4,7,10 * /chemin/vers/python -X utf8 /chemin/vers/projet_tmdb/mise_a_jour.py
```

Les nouveaux films sont ajoutés et les films existants actualisés, sans doublons.

---

## Projet 2 — PokéAPI (`projet_pokeapi/`)

Utilisation de la [PokéAPI](https://pokeapi.co/) (`/pokemon/{id ou nom}` et `/type/{type}`) :

- statistiques d'un Pokémon (PV, attaque, défense...) à partir de son nom ou de son id
- comparaison de deux Pokémon : lequel a le plus de PV et d'attaque
- pour un type : nombre de Pokémon et moyenne des PV
- simulation d'un combat en 5 tours (le plus de dégâts totaux gagne)
- liste des Pokémon filtrable par type et triable par taille, poids ou caractéristique de combat
- Q1, Q2 (avec un serveur local qui simule `/data1`, `/data2`, `/data3`) et Q3

### Fichiers

| Fichier | Rôle |
|---|---|
| `poke_api.ipynb` | Notebook : code, résultats et réponses aux questions |
| `app_pokemon.py` | Interface Streamlit (Pokédex, fiche, comparaison, type, combat) |
| `requirements.txt` | Dépendances |

### Lancer

```bash
cd projet_pokeapi
pip install -r requirements.txt
streamlit run app_pokemon.py
```

Aucune clé d'API n'est nécessaire.

---

## Source des données

- TMDB : https://www.themoviedb.org/ — ce produit utilise l'API TMDB mais n'est ni approuvé ni certifié par TMDB.
- PokéAPI : https://pokeapi.co/
