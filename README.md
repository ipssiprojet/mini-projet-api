# Mini-projet 1 — API TMDB

Projet Python réalisé dans le cadre de ma formation à l’IPSSI.

## Fonctionnalités

- Consultation des informations d’un film via l’API TMDB.
- Gestion des erreurs HTTP, délais d’attente et nouvelles tentatives.
- Simulation d’un million de requêtes avec asyncio et une concurrence limitée.
- Cache d’une heure avec démonstration de son expiration.
- Téléchargement et décompression de l’export quotidien des films.
- Conversion en tableau JSON et création d’un DataFrame pandas.
- Import et mise à jour des films dans SQLite.
- Interface Streamlit pour consulter l’API et rechercher dans la base SQL.

## Installation

Python 3.11 ou supérieur est nécessaire.

Depuis le dossier du projet :

```bash
python -m pip install -r requirements.txt
```

Copier `.env.example` vers `.env`, puis remplacer la valeur d’exemple par un
jeton d’accès en lecture obtenu dans les paramètres API de son compte TMDB :

```dotenv
TMDB_READ_ACCESS_TOKEN=ton_jeton_ici
```

Le fichier `.env` est privé et exclu du dépôt Git.

## Utilisation

### Consulter le film 550 — Fight Club

```bash
python main.py
```

### Simuler un million de requêtes

```bash
python simulation_async.py
```

Les requêtes sont simulées sur trois routes, avec 100 tâches concurrentes.
Aucun appel réel n’est envoyé à ces routes.
Les temps mesurés correspondent uniquement à la simulation locale.

### Tester le cache d’une heure

```bash
python simulation_cache.py
```

La démonstration vérifie :
- un premier appel à l’API simulée ;
- la réutilisation du cache pour 101 appels ;
- un nouvel appel après expiration.

Une horloge simulée permet d’avancer de 3 601 secondes sans attendre une heure.
Les erreurs étant aléatoires, la démonstration peut demander une relance.

### Télécharger l’export et créer la base SQL

```bash
python -X utf8 export_tmdb.py
python -X utf8 import_sql.py
```

L’export du jour est disponible au plus tard à 8 h UTC.
Il contient les identifiants et quelques attributs des films, pas leurs fiches complètes.

Les fichiers sont créés dans `data/`, notamment :
- l’export compressé et décompressé ;
- le tableau JSON ;
- la base SQLite `tmdb.db`, contenant la table `films`.

Les valeurs manquantes des champs `adult` et `video` sont remplacées par `False`.

### Mettre à jour la base

```bash
python mise_a_jour.py
```

Ce script télécharge l’export du jour puis lance l’import SQL.
Les films existants sont actualisés grâce à leur identifiant.
Les nouveaux films sont ajoutés sans doublons.
Les films absents du nouvel export restent dans la base.

Le journal d’exécution est enregistré dans `data/mises_a_jour.log`.

Pour une exécution tous les trois mois, ce script peut être associé à un
planificateur externe, par exemple cron ou le Planificateur de tâches Windows.
Aucune tâche n’est installée automatiquement par le projet.

### Lancer l’interface

```bash
python -m streamlit run app.py
```

Ouvrir http://localhost:8501.

L’interface propose :
- la consultation d’un film par identifiant, avec un cache d’une heure ;
- une recherche dans les titres originaux de la base SQLite ;
- le classement des dix films les plus populaires de la base.

## Organisation des fichiers

| Fichier | Rôle |
|---|---|
| `main.py` | Appels TMDB et gestion des erreurs |
| `simulation_async.py` | Simulation de forte charge |
| `simulation_cache.py` | Démonstration du cache et de son expiration |
| `export_tmdb.py` | Téléchargement et décompression |
| `import_sql.py` | Conversion JSON, DataFrame et import SQLite |
| `mise_a_jour.py` | Enchaînement du téléchargement et de l’import |
| `app.py` | Interface Streamlit |

## Vérifications réalisées

- Récupération des informations du film 550.
- Rejet d’un identifiant négatif.
- Simulation d’un million de requêtes.
- Vérification du cache et de son expiration.
- Import de 1 269 754 films lors du test du 5 novembre 2026.
- Exécution du script de mise à jour.
- Consultation API et recherche SQL dans Streamlit.

Les scénarios HTTP 429 et 500/503 de `main.py` restent à tester séparément
avec des réponses contrôlées.

## Données et fichiers exclus

Le dossier `data/`, les fichiers compilés Python et le fichier `.env`
ne sont pas versionnés. Les données peuvent être recréées avec les scripts.

## Source

Données : https://www.themoviedb.org/

Ce produit utilise l’API TMDB mais n’est ni approuvé ni certifié par TMDB.