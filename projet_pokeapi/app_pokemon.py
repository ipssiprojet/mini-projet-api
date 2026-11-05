import asyncio
import random
import time

import aiohttp
import requests
import streamlit as st

URL = "https://pokeapi.co/api/v2"
STATS = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]


def safe_get(url, retries=5):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=10)
        except requests.RequestException:
            time.sleep(2 ** i)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** i)
            continue
        return None  # 400, 401, 403, 404 : pas la peine de réessayer
    return None


def resume(data):
    p = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    p["name"] = data["name"]
    p["id"] = data["id"]
    p["types"] = [t["type"]["name"] for t in data["types"]]
    p["taille"] = data["height"] / 10
    p["poids"] = data["weight"] / 10
    p["image"] = data["sprites"]["front_default"]
    p["total"] = sum(p[s] for s in STATS)
    return p


# cache d'1h (Q3)
@st.cache_data(ttl=3600)
def get_pokemon(nom):
    data = safe_get(f"{URL}/pokemon/{nom.lower().strip()}")
    return resume(data) if data else None


@st.cache_data(ttl=3600)
def get_type(t):
    return safe_get(f"{URL}/type/{t}")


@st.cache_data(ttl=3600)
def pokedex(debut, fin):
    # Q2 : on charge tout en parallèle
    async def fetch(session, sem, i):
        async with sem:
            for essai in range(5):
                try:
                    async with session.get(f"{URL}/pokemon/{i}") as r:
                        if r.status == 200:
                            return resume(await r.json())
                        if r.status not in (429, 500, 502, 503, 504):
                            return None
                except aiohttp.ClientError:
                    pass
                await asyncio.sleep(2 ** essai)

    async def main():
        sem = asyncio.Semaphore(50)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[fetch(session, sem, i) for i in range(debut, fin + 1)])

    return [p for p in asyncio.run(main()) if p]


def tableau(lignes, colonnes):
    # tableau en markdown (st.dataframe ne marche pas chez moi à cause de pyarrow)
    txt = "| " + " | ".join(colonnes) + " |\n|" + "---|" * len(colonnes) + "\n"
    for l in lignes:
        txt += "| " + " | ".join(str(x) for x in l) + " |\n"
    st.markdown(txt, unsafe_allow_html=True)


def combat(p1, p2):
    degats = {p1["name"]: 0, p2["name"]: 0}
    log = []
    for tour in range(1, 6):
        for att, dfs in [(p1, p2), (p2, p1)]:
            d = round(att["attack"] / dfs["defense"] * 20 * random.uniform(0.85, 1))
            degats[att["name"]] += d
            log.append([tour, att["name"], dfs["name"], d])
    return degats, log


st.title("PokéAPI - Mini projet 2")
onglets = st.tabs(["Pokédex", "Fiche", "Comparaison", "Type", "Combat"])

with onglets[0]:
    debut, fin = st.slider("Numéros", 1, 1025, (1, 151))
    types = st.multiselect("Type", ["normal", "fire", "water", "grass", "electric", "ice", "fighting", "poison",
                                    "ground", "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark",
                                    "steel", "fairy"])
    tri = st.selectbox("Trier par", ["total"] + STATS + ["taille", "poids", "id"])
    croissant = st.checkbox("Ordre croissant")

    liste = pokedex(debut, fin)
    if types:
        liste = [p for p in liste if any(t in p["types"] for t in types)]
    liste = sorted(liste, key=lambda p: p[tri], reverse=not croissant)

    st.write(f"{len(liste)} pokémons")
    tableau([[f"<img src='{p['image']}' width='40'>", p["id"], p["name"], ", ".join(p["types"]), p["taille"],
              p["poids"]] + [p[s] for s in STATS] + [p["total"]] for p in liste],
            ["", "id", "nom", "types", "taille", "poids", "pv", "att", "def", "att spé", "def spé", "vitesse", "total"])

with onglets[1]:
    nom = st.text_input("Nom ou id", "pikachu")
    p = get_pokemon(nom)
    if p is None:
        st.error("Pokémon introuvable")
    else:
        st.image(p["image"])
        st.write(f"**{p['name']}** - {', '.join(p['types'])} - {p['taille']} m - {p['poids']} kg")
        cols = st.columns(6)
        for c, s in zip(cols, STATS):
            c.metric(s, p[s])

with onglets[2]:
    c1, c2 = st.columns(2)
    a = get_pokemon(c1.text_input("Pokémon 1", "charizard"))
    b = get_pokemon(c2.text_input("Pokémon 2", "blastoise"))
    if a and b:
        for s in STATS + ["total"]:
            c1.metric(f"{a['name']} - {s}", a[s], a[s] - b[s])
            c2.metric(f"{b['name']} - {s}", b[s], b[s] - a[s])
        st.write("Plus de PV :", a["name"] if a["hp"] > b["hp"] else b["name"])
        st.write("Plus d'attaque :", a["name"] if a["attack"] > b["attack"] else b["name"])

with onglets[3]:
    t = st.text_input("Type", "fire")
    data = get_type(t)
    if data is None:
        st.error("Type introuvable")
    else:
        noms = [x["pokemon"]["name"] for x in data["pokemon"]]
        pvs = [get_pokemon(n)["hp"] for n in noms]
        st.metric("Nombre de pokémons", len(noms))
        st.metric("PV moyen", round(sum(pvs) / len(pvs), 1))

with onglets[4]:
    c1, c2 = st.columns(2)
    n1 = c1.text_input("Combattant 1", "pikachu")
    n2 = c2.text_input("Combattant 2", "gyarados")
    if st.button("Combat !"):
        p1, p2 = get_pokemon(n1), get_pokemon(n2)
        if p1 and p2:
            degats, log = combat(p1, p2)
            tableau(log, ["tour", "attaquant", "défenseur", "dégâts"])
            st.write("Dégâts totaux :", degats)
            st.success("Gagnant : " + max(degats, key=degats.get))
