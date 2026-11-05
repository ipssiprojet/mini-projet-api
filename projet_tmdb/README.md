# Mini-projet 1 — API TMDB

Projet réalisé dans le cadre de notre formation à l’IPSSI.

Cette partie utilise l’API TMDB pour consulter des films, gérer les erreurs
et enregistrer les données dans SQLite. Une interface Streamlit permet
de consulter les résultats.

## Installation

Depuis la racine du dépôt :

```bash
cd projet_tmdb
python -m pip install -r requirements.txt
```

Créer un compte sur https://www.themoviedb.org/ et obtenir un jeton
d’accès en lecture dans les paramètres API.

Copier `.env.example` dans un fichier `.env`, puis renseigner son jeton :

```dotenv
TMDB_READ_ACCESS_TOKEN=ton_jeton_ici
```

Le fichier `.env` reste privé et n’est pas envoyé sur GitHub.

## Utilisation

Toutes les commandes suivantes se lancent depuis le dossier `projet_tmdb`.

### Consulter un film et tester les erreurs

Afficher les informations du film 550, Fight Club :

```bash
python main.py
```

Lancer les six tests automatisés :

```bash
python -m unittest test_api -v
```

Les tests simulent les réponses et les pauses, sans contacter TMDB.

### Lancer les simulations

```bash
python simulation_async.py
python simulation_cache.py
```

La première simulation traite un million de requêtes sur trois routes,
avec 100 workers et une file d’attente limitée.

La deuxième vérifie un cache d’une heure. Une horloge simulée permet
de tester son expiration sans attendre réellement une heure.

Ces simulations ne contactent pas de serveur réel.
Les erreurs étant aléatoires, les résultats peuvent varier et le test
du cache peut parfois nécessiter une relance.

### Télécharger les données et créer la base

```bash
python -X utf8 export_tmdb.py
python -X utf8 import_sql.py
```

L’export du jour est disponible au plus tard à 8 h UTC.
Il contient les identifiants et quelques attributs des films,
pas leurs fiches complètes.

Le script d’import crée un tableau JSON, un DataFrame pandas et la base
`data/tmdb.db`. Les insertions SQL sont effectuées par lots de 5 000 films.

La table `films` contient les colonnes :
`id`, `original_title`, `adult`, `popularity` et `video`.
L’identifiant est la clé primaire. Les valeurs manquantes de `adult`
et `video` sont remplacées par `False`.

La conversion de l’export complet nécessite de la mémoire disponible.

### Lancer Streamlit

```bash
python -m streamlit run app.py
```

Ouvrir http://localhost:8501 sur le même ordinateur.

L’interface permet de :
- rechercher un film par identifiant, avec un cache d’une heure ;
- rechercher un titre original dans SQLite ;
- consulter les dix films les plus populaires de la base.

Créer la base avant d’utiliser l’onglet SQL.
Garder le terminal ouvert et utiliser Ctrl + C pour arrêter l’application.

## Mise à jour trimestrielle

```bash
python -X utf8 mise_a_jour.py
```

Le script lance le téléchargement puis l’import.
Les résultats s’affichent dans le terminal.
Si le téléchargement échoue, l’import n’est pas lancé.

Les nouveaux films sont ajoutés et les films existants sont actualisés
sans doublons. Les films absents du nouvel export restent dans la base.

Exemple cron pour une exécution le 5 janvier, avril, juillet et octobre
à 10 h :

```cron
0 10 5 1,4,7,10 * /chemin/vers/python -X utf8 /chemin/vers/projet_tmdb/mise_a_jour.py
```

Les chemins et le fuseau horaire sont à adapter pour exécuter le script
après 8 h UTC. Cet exemple est fourni pour le rendu :
aucune planification n’est installée automatiquement.

## Organisation des fichiers

| Fichier | Rôle |
|---|---|
| main.py | Informations des films, erreurs et nouvelles tentatives |
| test_api.py | Tests automatisés de la gestion des erreurs |
| simulation_async.py | Simulation de forte charge avec asyncio |
| simulation_cache.py | Cache d’une heure et test d’expiration |
| export_tmdb.py | Téléchargement et décompression de l’export |
| import_sql.py | Tableau JSON, DataFrame et import SQLite |
| mise_a_jour.py | Enchaînement du téléchargement et de l’import |
| app.py | Interface Streamlit |
| requirements.txt | Dépendances du projet |
| .env.example | Exemple de configuration sans jeton réel |

## Vérifications

Les tests réalisés couvrent la récupération du film 550,
les erreurs API, la simulation d’un million de requêtes,
le cache et son expiration, ainsi que le téléchargement et l’import SQL.

Lors du test du 5 novembre 2026, 1 269 754 films ont été enregistrés.
L’interface Streamlit a également été testée pour la consultation API
et la recherche SQL.

Le fichier `.env`, le dossier `data` et les fichiers compilés Python
sont exclus de Git. Les données sont à recréer avec les scripts.

## Source

Données : https://www.themoviedb.org/

Ce produit utilise l’API TMDB mais n’est ni approuvé ni certifié par TMDB.