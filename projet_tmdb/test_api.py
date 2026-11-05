import unittest
from unittest.mock import Mock, patch

import requests

from main import get_movie_details, requete_api


def reponse_simulee(statut, donnees=None, headers=None):
    reponse = Mock()
    reponse.status_code = statut
    reponse.headers = headers or {}
    reponse.json.return_value = donnees
    return reponse


@patch("main.TOKEN", "jeton_de_test")
class TestAPI(unittest.TestCase):
    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_429_puis_succes(self, get, sleep):
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
        self.assertEqual(
            [appel.args[0] for appel in sleep.call_args_list],
            [1, 2]
        )

    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_erreurs_sans_retry(self, get, sleep):
        for statut in [400, 401, 403, 404]:
            with self.subTest(statut=statut):
                get.reset_mock()
                sleep.reset_mock()
                get.return_value = reponse_simulee(statut)

                with self.assertRaisesRegex(
                    RuntimeError,
                    f"Erreur {statut}"
                ):
                    requete_api("https://api.example.com/test")

                get.assert_called_once()
                sleep.assert_not_called()

    @patch("main.time.sleep")
    @patch("main.requests.get")
    def test_limite_tentatives(self, get, sleep):
        get.return_value = reponse_simulee(503)

        with self.assertRaisesRegex(
            RuntimeError,
            "nombre maximal de tentatives"
        ):
            requete_api("https://api.example.com/test")

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

        get.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)