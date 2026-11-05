# Mini-projet 1 — API TMDB

Ce projet a été réalisé dans le cadre de notre formation à l’IPSSI.
Il correspond à la partie TMDB du travail de groupe.

L’objectif est de récupérer des informations sur les films avec une API,
de gérer les erreurs et de stocker les données dans une base SQL.
Une interface Streamlit permet ensuite de consulter les résultats.

## Installation

Depuis la racine du dépôt, entrer dans le dossier :

```bash
cd projet_tmdb
```

Installer les bibliothèques nécessaires :

```bash
python -m pip install -r requirements.txt
```

## Configuration du jeton TMDB

Créer un compte sur https://www.themoviedb.org/ et demander un accès
à l’API dans les paramètres du compte.

Copier `.env.example` dans un fichier nommé `.env`, puis ajouter
son jeton d’accès en lecture :

```dotenv
TMDB_READ_ACCESS_TOKEN=ton_jeton_ici
```

Le fichier `.env` est exclu de Git pour ne pas publier le jeton.

## 1. Récupérer les informations d’un film

La fonction `get_movie_details(movie_id)` récupère :

- le titre ;
- la date de sortie ;
- les genres ;
- la popularité ;
- la note moyenne.

Le programme utilise l’identifiant 550, qui correspond à Fight Club.

```bash
python main.py
```

## 2. Q1 — Gérer les erreurs

La fonction `requete_api()` gère les erreurs rencontrées pendant les appels.

| Erreur | Traitement |
|---|---|
| 400 | Afficher que la requête est incorrecte |
| 401 | Afficher que le jeton est absent ou invalide |
| 403 | Afficher que l’accès est interdit |
| 404 | Afficher que la ressource est introuvable |
| 429 | Attendre avant de réessayer |
| 500, 502, 503, 504 | Réessayer après une pause |
| Connexion impossible ou délai dépassé | Réessayer après une pause |

Le nombre de tentatives est limité à trois par défaut.
Les pauses augmentent entre les tentatives.
Un identifiant invalide est refusé avant l’appel à l’API.

Pour lancer les tests :

```bash
python -m unittest test_api -v
```

Les six tests vérifient les erreurs HTTP, les problèmes réseau,
les pauses et la limite de tentatives.
Les appels et les pauses sont simulés : aucun jeton réel n’est nécessaire.

## 3. Q2 — Simuler une forte charge

```bash
python simulation_async.py
```

Le script simule un million de requêtes sur les trois routes demandées.
Il utilise `asyncio`, avec 100 workers et une file d’attente limitée
à 200 éléments.

Cela permet de traiter les requêtes sans créer un million de tâches
simultanément en mémoire. Les erreurs temporaires déclenchent
de nouvelles tentatives.

Exemple de résultat obtenu :

| Mesure | Résultat |
|---|---:|
| Requêtes demandées | 1 000 000 |
| Succès | 978 981 |
| Échecs | 21 019 |
| Nouvelles tentatives | 41 439 |
| Durée | 7,58 secondes |

Les erreurs sont aléatoires, donc les résultats changent à chaque lancement.
Les appels sont simulés : ce débit ne représente pas les performances de TMDB.

## 4. Q3 — Ajouter un cache d’une heure

```bash
python simulation_cache.py
```

Le cache conserve les réponses réussies pendant 3 600 secondes.

La démonstration réalise un premier appel, puis réutilise les données
pour les appels suivants. Une horloge simulée avance ensuite
de 3 601 secondes pour vérifier l’expiration.

Résultat obtenu :

- 2 lectures depuis l’API simulée ;
- 101 lectures depuis le cache ;
- 1 expiration.

Un verrou par route évite de récupérer plusieurs fois les mêmes données
en même temps. Le cache reste en mémoire pendant l’exécution du programme.

La simulation pouvant produire des erreurs aléatoires, il peut être
nécessaire de la relancer.

## 5. Télécharger l’export quotidien

```bash
python -X utf8 export_tmdb.py
```

Le script télécharge l’export des films correspondant à la date du jour,
décompresse le fichier `.gz` et affiche les cinq premiers films.

Les fichiers sont enregistrés dans le dossier `data`.

L’export contient un objet JSON par ligne, avec les identifiants
et quelques attributs des films. Il ne contient pas leurs fiches complètes.

L’export du jour est disponible au plus tard à 8 h UTC.
Ce téléchargement ne nécessite pas de jeton.

## 6. Créer le DataFrame et importer dans SQLite

Après le téléchargement :

```bash
python -X utf8 import_sql.py
```

Le script :

1. Lit l’export.
2. Le transforme en tableau JSON.
3. Crée un DataFrame avec pandas.
4. Vérifie les identifiants.
5. Importe les films dans SQLite.

Les valeurs manquantes de `adult` et `video` sont remplacées par `False`.

La base est enregistrée dans `data/tmdb.db`.
Elle contient la table `films` :

| Colonne | Type SQLite | Description |
|---|---|---|
| id | INTEGER | Identifiant du film, clé primaire |
| original_title | TEXT | Titre original |
| adult | INTEGER | Booléen stocké en 0 ou 1 |
| popularity | REAL | Popularité |
| video | INTEGER | Booléen stocké en 0 ou 1 |

Lors du test du 5 novembre 2026, 1 269 754 films ont été importés.

L’import complet charge les données en mémoire.
La mémoire nécessaire dépend donc de la taille de l’export.

## 7. Mettre à jour la base tous les trois mois

```bash
python mise_a_jour.py
```

Ce script lance le téléchargement puis l’import SQL.
Il utilise le même interpréteur Python pour les deux étapes et écrit
les résultats dans `data/mises_a_jour.log`.

Les nouveaux films sont ajoutés et les films existants sont actualisés
grâce à leur identifiant, sans doublons.
Les films absents du nouvel export restent dans la base.

Pour une exécution trimestrielle, on peut utiliser un planificateur externe.
Exemple avec cron, le 5 janvier, avril, juillet et octobre à 10 h :

```cron
0 10 5 1,4,7,10 * /chemin/vers/python -X utf8 /chemin/vers/projet_tmdb/mise_a_jour.py
```

Les chemins et le fuseau horaire doivent être adaptés.
L’exécution doit avoir lieu après la disponibilité de l’export à 8 h UTC.

Cet exemple est fourni pour le rendu.
Aucune planification n’est installée automatiquement.

## 8. Utiliser l’interface Streamlit

```bash
python -m streamlit run app.py
```

Ouvrir http://localhost:8501 sur le même ordinateur.

L’interface contient deux onglets :

- **Consulter l’API** : rechercher un film par identifiant et afficher
  ses informations. Les réponses sont conservées en cache pendant une heure.
- **Explorer la base SQL** : afficher le nombre de films, rechercher
  un titre original et consulter les dix films les plus populaires.

Il faut créer la base avant d’utiliser l’onglet SQL.
Garder le terminal ouvert pendant l’utilisation.
Pour arrêter l’application, faire `Ctrl + C`.

L’application fonctionne localement et ne nécessite pas de publication
sur Internet.

## Organisation des fichiers

| Fichier | Rôle |
|---|---|
| main.py | Appels TMDB et gestion des erreurs |
| test_api.py | Tests automatisés |
| simulation_async.py | Simulation de forte charge |
| simulation_cache.py | Test du cache et de son expiration |
| export_tmdb.py | Téléchargement et décompression |
| import_sql.py | Tableau JSON, DataFrame et import SQLite |
| mise_a_jour.py | Mise à jour des données |
| app.py | Interface Streamlit |
| requirements.txt | Bibliothèques à installer |
| .env.example | Exemple de configuration sans jeton réel |

## Vérifications réalisées

- Récupération des informations du film 550.
- Rejet d’un identifiant invalide.
- Six tests automatisés réussis.
- Simulation d’un million de requêtes.
- Vérification du cache et de son expiration.
- Téléchargement et conversion de l’export.
- Import et mise à jour de la base SQLite.
- Recherche API et SQL dans Streamlit.

Le fichier `.env`, le dossier `data` et les fichiers `__pycache__`
sont exclus du dépôt. Les données peuvent être recréées avec les scripts.

## Source

Données : https://www.themoviedb.org/

Ce produit utilise l’API TMDB mais n’est ni approuvé ni certifié par TMDB.