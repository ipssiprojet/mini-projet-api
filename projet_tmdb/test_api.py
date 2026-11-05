import unittest
from unittest.mock import Mock, patch

import requests

from main import get_movie_details, requete_api


def reponse_simulee(statut, donnees=None, headers=None):
    # on fabrique une reponse sans contacter l'API
    reponse = Mock()
    reponse.status_code = statut

    if headers is None:
        headers = {}

    reponse.headers = headers
    reponse.json.return_value = donnees

    return reponse


# on remplace le vrai jeton pendant les tests
@patch("main.TOKEN", "jeton_de_test")
class TestAPI(unittest.TestCase):

    # on remplace les pauses et les appels HTTP
    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_429_puis_succes(self, get, sleep):
        # le premier appel echoue et le deuxieme reussi
        get.side_effect = [
            reponse_simulee(429, headers={"Retry-After": "3"}),
            reponse_simulee(200, {"ok": True})
        ]

        resultat = requete_api("https://api.example.com/test")

        self.assertEqual(resultat, {"ok": True})
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(3.0)

    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_500_503_puis_succes(self, get, sleep):
        get.side_effect = [
            reponse_simulee(500),
            reponse_simulee(503),
            reponse_simulee(200, {"ok": True})
        ]

        resultat = requete_api("https://api.example.com/test")

        self.assertEqual(resultat, {"ok": True})
        self.assertEqual(get.call_count, 3)

        # on verifie les temps de pause demandes
        pauses = []

        for appel in sleep.call_args_list:
            pauses.append(appel.args[0])

        self.assertEqual(pauses, [1, 2])

    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_erreurs_sans_retry(self, get, sleep):
        for statut in [400, 401, 403, 404]:
            with self.subTest(statut=statut):
                # on remet les compteurs a zero pour chaque erreur
                get.reset_mock()
                sleep.reset_mock()

                get.return_value = reponse_simulee(statut)

                with self.assertRaisesRegex(
                    RuntimeError,
                    f"Erreur {statut}"
                ):
                    requete_api("https://api.example.com/test")

                # un seul appel et aucune pause
                get.assert_called_once()
                sleep.assert_not_called()

    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_limite_tentatives(self, get, sleep):
        # tous les appels vont retourner une erreur 503
        get.return_value = reponse_simulee(503)

        with self.assertRaisesRegex(
            RuntimeError,
            "nombre maximal de tentatives"
        ):
            requete_api("https://api.example.com/test")

        # on doit s'arreter apres 3 appels
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_erreurs_reseau_puis_succes(self, get, sleep):
        get.side_effect = [
            requests.Timeout("Délai dépassé"),
            requests.ConnectionError("Connexion impossible"),
            reponse_simulee(200, {"ok": True})
        ]

        resultat = requete_api("https://api.example.com/test")

        self.assertEqual(resultat, {"ok": True})
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("main.requests.get")
    def test_identifiant_invalide(self, get):
        with self.assertRaises(ValueError):
            get_movie_details(-1)

        # l'identifiant est refuse avant tout appel HTTP
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)