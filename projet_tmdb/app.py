import sqlite3
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from main import get_movie_details

st.set_page_config(
    page_title="Projet TMDB",
    page_icon="🎬",
    layout="wide"
)

BASE = Path(__file__).resolve().parent / "data" / "tmdb.db"


@st.cache_data(ttl=3600, max_entries=1000)
def charger_film(movie_id):
    return get_movie_details(movie_id)


def lire_base(requete, parametres=()):
    connexion = sqlite3.connect(BASE)

    try:
        return pd.read_sql_query(
            requete,
            connexion,
            params=parametres
        )
    finally:
        connexion.close()


st.title("🎬 Exploration des films TMDB")
st.write("Mini-projet API — IPSSI")

onglet_api, onglet_base = st.tabs([
    "Consulter l’API",
    "Explorer la base SQL"
])

with onglet_api:
    st.subheader("Rechercher un film par son identifiant")
    st.caption("Les réponses sont conservées en cache pendant une heure.")

    with st.form("recherche_api"):
        movie_id = st.number_input(
            "Identifiant TMDB",
            min_value=1,
            value=550,
            step=1
        )

        rechercher = st.form_submit_button("Afficher le film")

    if rechercher:
        try:
            with st.spinner("Chargement du film..."):
                film = charger_film(int(movie_id))

            st.header(film["titre"])
            st.write(f"**Date de sortie :** {film['date_sortie']}")
            st.write(f"**Genres :** {', '.join(film['genres'])}")

            colonne1, colonne2 = st.columns(2)

            colonne1.metric(
                "Note moyenne / 10",
                f"{film['note_moyenne']:.2f}"
            )

            colonne2.metric(
                "Popularité",
                f"{film['popularite']:.2f}"
            )

        except (ValueError, RuntimeError, requests.RequestException) as erreur:
            st.error(str(erreur))

with onglet_base:
    st.subheader("Films enregistrés dans SQLite")

    if not BASE.exists():
        st.warning("Base absente. Lance d’abord import_sql.py.")

    else:
        try:
            nombre = lire_base(
                "SELECT COUNT(*) AS total FROM films"
            ).iloc[0]["total"]

            st.metric("Nombre de films", f"{int(nombre):,}")

            with st.form("recherche_sql"):
                titre = st.text_input(
                    "Rechercher dans les titres originaux"
                )

                limite = st.selectbox(
                    "Nombre maximal de résultats",
                    [10, 25, 50, 100],
                    index=1
                )

                filtrer = st.form_submit_button("Rechercher")

            if filtrer:
                tableau = lire_base(
                    """
                    SELECT
                        id,
                        original_title AS titre_original,
                        popularity AS popularite
                    FROM films
                    WHERE INSTR(LOWER(original_title), LOWER(?)) > 0
                    ORDER BY popularity DESC, id
                    LIMIT ?
                    """,
                    (titre.strip(), int(limite))
                )

                if tableau.empty:
                    st.info("Aucun film trouvé.")
                else:
                    st.dataframe(
                        tableau,
                        hide_index=True,
                        width="stretch"
                    )

            st.subheader("Les dix films les plus populaires")

            populaires = lire_base(
                """
                SELECT
                    id,
                    original_title AS titre_original,
                    popularity AS popularite
                FROM films
                ORDER BY popularity DESC, id
                LIMIT 10
                """
            )

            st.dataframe(
                populaires,
                hide_index=True,
                width="stretch"
            )

        except (sqlite3.Error, pd.errors.DatabaseError) as erreur:
            st.error(f"Erreur SQL : {erreur}")

st.caption(
    "Ce produit utilise l’API TMDB mais n’est ni approuvé "
    "ni certifié par TMDB."
)