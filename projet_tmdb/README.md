# Mini-projet 1 — API TMDB

Projet Python réalisé dans le cadre de la formation à l’IPSSI.

## Objectif

Exploiter l’API The Movie Database (TMDB), gérer les erreurs de requêtes,
simuler une forte charge, utiliser un cache et stocker les données
dans une base relationnelle.

Une interface Streamlit permet de consulter les films et d’explorer
les données enregistrées dans SQLite.

## Installation

Python 3.11 ou supérieur est nécessaire.

Depuis la racine du dépôt, entrer dans le dossier du projet :

```bash
cd projet_tmdb
```

Installer les dépendances :

```bash
python -m pip install -r requirements.txt
```

Les dépendances sont :
- requests ;
- python-dotenv ;
- pandas ;
- streamlit ;
- urllib3.

## Configuration de l’accès TMDB

Créer un compte sur https://www.themoviedb.org/ puis demander un accès
à l’API dans les paramètres du compte.

Copier le fichier `.env.example` vers un fichier nommé `.env`.

Renseigner son jeton d’accès en lecture :

```dotenv
TMDB_READ_ACCESS_TOKEN=ton_jeton_ici
```

Le fichier `.env` contient une information privée et est exclu du dépôt Git.
Le téléchargement des exports quotidiens ne nécessite pas ce jeton.

## 1. Récupération des informations d’un film

Le fichier `main.py` contient la fonction :

```python
get_movie_details(movie_id)
```

Elle retourne :
- le titre ;
- la date de sortie ;
- les genres ;
- la popularité ;
- la note moyenne.

Pour récupérer les informations du film 550, Fight Club :

```bash
python main.py
```

## 2. Q1 — Gestion des erreurs

La fonction `requete_api()` centralise les appels HTTP et leur gestion
des erreurs.

| Situation | Comportement |
|---|---|
| 400 | Message indiquant une requête incorrecte |
| 401 | Message indiquant un jeton absent ou invalide |
| 403 | Message indiquant un accès interdit |
| 404 | Message indiquant une ressource introuvable |
| 429 | Pause, prise en compte de Retry-After numérique et nouvelle tentative |
| 500, 502, 503, 504 | Pause et nouvelle tentative |
| Erreur de connexion ou délai dépassé | Pause et nouvelle tentative |
| JSON invalide | Message d’erreur explicite |
| Identifiant invalide | Rejet avant l’appel HTTP |

Le nombre de tentatives est limité à trois par défaut.
Les pauses augmentent entre les tentatives.

### Tests automatisés

Depuis le dossier `projet_tmdb` :

```bash
python -m unittest test_api -v
```

Six tests vérifient :
- le statut 429 et le respect de Retry-After ;
- les erreurs 500 et 503 suivies d’un succès ;
- les erreurs réseau suivies d’un succès ;
- les erreurs 400, 401, 403 et 404 sans nouvelle tentative ;
- le rejet d’un identifiant invalide ;
- la limite de trois tentatives.

Les appels HTTP et les pauses sont simulés.
Les tests ne nécessitent pas de jeton réel et ne contactent pas TMDB.

Résultat obtenu : six tests réussis.

## 3. Q2 — Simulation d’une forte charge

Lancer :

```bash
python simulation_async.py
```

Le script simule un million de requêtes réparties entre trois routes :

```text
https://api.example.com/data1
https://api.example.com/data2
https://api.example.com/data3
```

Il utilise :
- asyncio pour exécuter les tâches de manière concurrente ;
- 100 workers maximum ;
- une file d’attente limitée à 200 éléments ;
- des pauses non bloquantes avec asyncio.sleep ;
- des nouvelles tentatives pour les erreurs temporaires.

Le nombre de tâches et la taille de la file sont limités afin de ne pas
créer un million de tâches simultanément en mémoire.

### Exemple de résultat obtenu

| Mesure | Résultat |
|---|---:|
| Requêtes demandées | 1 000 000 |
| Workers | 100 |
| Succès | 978 981 |
| Échecs | 21 019 |
| Nouvelles tentatives | 41 439 |
| Appels simulés, tentatives incluses | 1 041 439 |
| Durée | 7,58 secondes |

Les erreurs sont générées aléatoirement : les résultats varient à chaque
exécution.

Aucun appel réel n’est envoyé à ces routes.
Le débit mesuré concerne uniquement la simulation locale et ne représente
pas les performances de TMDB.

## 4. Q3 — Cache avec expiration d’une heure

Lancer :

```bash
python simulation_cache.py
```

Le cache conserve les réponses réussies pendant 3 600 secondes.

La démonstration vérifie :
1. Un premier appel à l’API simulée.
2. Un deuxième appel utilisant le cache.
3. Cent appels simultanés utilisant le cache.
4. L’expiration après une avance de 3 601 secondes.
5. Un nouvel appel à l’API après expiration.

Une horloge simulée permet de vérifier l’expiration sans attendre une heure.

Un verrou par route empêche plusieurs récupérations simultanées des mêmes
données lorsque le cache doit être alimenté.

### Résultat obtenu

| Mesure | Résultat |
|---|---:|
| Lectures API réussies nécessaires | 2 |
| Lectures depuis le cache | 101 |
| Expirations | 1 |

Les erreurs de l’API simulée étant aléatoires, la démonstration peut nécessiter
une relance.

L’interface Streamlit possède également un cache réel d’une heure pour les
fiches des films, avec une limite de 1 000 entrées.

## 5. Téléchargement de l’export quotidien

Documentation :
https://developer.themoviedb.org/docs/daily-id-exports

Lancer :

```bash
python -X utf8 export_tmdb.py
```

Le script :
1. Détermine la date courante de l’ordinateur.
2. Télécharge le fichier movie_ids_MM_DD_YYYY.json.gz.
3. Le décompresse dans le dossier data.
4. Affiche les cinq premiers objets JSON.

Les exports sont disponibles quotidiennement au plus tard à 8 h UTC.
Si l’export du jour n’est pas encore disponible, le script affiche une erreur.

L’export contient les identifiants et certains attributs des films.
Il ne contient pas les fiches complètes.

Le fichier décompressé contient un objet JSON par ligne.

## 6. Tableau JSON, DataFrame et base relationnelle

Après le téléchargement, lancer :

```bash
python -X utf8 import_sql.py
```

Le script :
1. Lit les objets JSON de l’export du jour.
2. Les enregistre dans un tableau JSON.
3. Crée un DataFrame pandas.
4. Vérifie que les identifiants ne sont ni absents ni dupliqués.
5. Remplace les valeurs manquantes de adult et video par False.
6. Insère ou actualise les films dans SQLite.
7. Affiche le nombre de films et un aperçu des données.

La base est créée dans :

```text
data/tmdb.db
```

### Schéma de la table films

| Colonne | Type SQLite | Contrainte |
|---|---|---|
| id | INTEGER | Clé primaire |
| original_title | TEXT | Non nul |
| adult | INTEGER | Non nul, booléen stocké en 0 ou 1 |
| popularity | REAL | Non nul |
| video | INTEGER | Non nul, booléen stocké en 0 ou 1 |

Le champ id identifie chaque film de manière unique.

Lors d’un nouvel import :
- les nouveaux films sont ajoutés ;
- les films existants sont actualisés ;
- aucun doublon d’identifiant n’est créé ;
- les films absents du nouvel export restent dans la base.

Lors du test du 5 novembre 2026, 1 269 754 films ont été importés.

La conversion charge l’export en mémoire : la mémoire nécessaire dépend
de la taille du fichier.

## 7. Mise à jour trimestrielle

Lancer :

```bash
python mise_a_jour.py
```

Le script enchaîne :
1. Le téléchargement et la décompression de l’export du jour.
2. La conversion et la mise à jour de la table SQL.

Les scripts sont exécutés avec le même interpréteur Python et en UTF-8.
Si une étape échoue, la suivante n’est pas lancée.

Les résultats sont enregistrés dans :

```text
data/mises_a_jour.log
```

Éviter de lancer plusieurs mises à jour simultanément.

### Exemple de planification trimestrielle

Sur un serveur Linux, cette configuration cron lancerait la mise à jour
le 5 janvier, avril, juillet et octobre à 10 h :

```cron
0 10 5 1,4,7,10 * /chemin/vers/python -X utf8 /chemin/vers/mini-projet-api/projet_tmdb/mise_a_jour.py
```

Les chemins doivent être adaptés à l’environnement.

L’horaire dépend du fuseau du serveur. Il faut choisir une heure postérieure
à la disponibilité de l’export, à 8 h UTC.

Le script effectue une mise à jour à chaque lancement.
La fréquence trimestrielle est assurée par le planificateur externe.

Cet exemple est fourni pour le déploiement.
Aucune planification n’est installée automatiquement sur l’ordinateur.

## 8. Interface Streamlit

Depuis le dossier projet_tmdb, lancer :

```bash
python -m streamlit run app.py
```

Ouvrir :

http://localhost:8501

Garder le terminal ouvert pendant l’utilisation.
Pour arrêter l’application, utiliser Ctrl + C.

### Onglet Consulter l’API

- Recherche par identifiant TMDB.
- Affichage du titre, de la date de sortie et des genres.
- Affichage de la note moyenne et de la popularité.
- Conservation des résultats en cache pendant une heure.

### Onglet Explorer la base SQL

- Affichage du nombre de films.
- Recherche dans les titres originaux.
- Limitation du nombre de résultats.
- Affichage des dix films les plus populaires de la base.

La base doit avoir été créée avant d’utiliser les fonctionnalités SQL.

## Organisation des fichiers

| Fichier | Rôle |
|---|---|
| main.py | Appels TMDB et gestion des erreurs |
| test_api.py | Tests automatisés de la gestion des erreurs |
| simulation_async.py | Simulation d’un million de requêtes |
| simulation_cache.py | Démonstration du cache et de son expiration |
| export_tmdb.py | Téléchargement et décompression de l’export |
| import_sql.py | Tableau JSON, DataFrame et import SQLite |
| mise_a_jour.py | Enchaînement du téléchargement et de l’import |
| app.py | Interface Streamlit |
| requirements.txt | Dépendances Python |
| .env.example | Exemple de configuration sans secret |

## Vérifications réalisées

- Récupération des informations du film 550.
- Rejet d’un identifiant négatif.
- Réussite des six tests automatisés de gestion des erreurs.
- Simulation d’un million de requêtes.
- Vérification du cache et de son expiration.
- Téléchargement et décompression de l’export quotidien.
- Conversion en tableau JSON et DataFrame.
- Import de 1 269 754 films dans SQLite.
- Exécution du script de mise à jour.
- Consultation API et recherche SQL dans Streamlit.

## Fichiers exclus du dépôt

Les éléments suivants ne sont pas versionnés :
- le fichier .env contenant le jeton ;
- le dossier data contenant les exports, la base et les journaux ;
- les fichiers compilés Python ;
- les environnements virtuels.

Les données peuvent être recréées avec les scripts fournis.

## Source et attribution

Données :
https://www.themoviedb.org/

Ce produit utilise l’API TMDB mais n’est ni approuvé ni certifié par TMDB.