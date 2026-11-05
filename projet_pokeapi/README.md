# Mini projet 2 - PokéAPI

Utilisation de la [PokéAPI](https://pokeapi.co/) :
- stats d'un Pokémon, comparaison de 2 Pokémon, stats par type (nombre + PV moyen)
- simulation d'un combat en 5 tours
- liste des Pokémon avec filtre par type et tri (taille, poids, stats)
- Q1 : gestion des erreurs (retry, 429, 5xx, 4xx)
- Q2 : beaucoup de requêtes en parallèle avec asyncio + simulation de charge
- Q3 : cache d'1h
- front Streamlit

## Fichiers
- `poke_api.ipynb` : le notebook avec le code et les réponses
- `app_pokemon.py` : l'appli Streamlit

## Lancer
```
pip install -r requirements.txt
streamlit run app_pokemon.py
```
