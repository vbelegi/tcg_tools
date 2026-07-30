"""Testes da calculadora de premiação."""

import unittest

from core.calculator import calcular, calcular_premiados
from core.config import DEFAULT
from core.validation import ConfigError, InputError, validar_config, validar_jogadores


class TestCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = DEFAULT.copy()

    def test_soma_premios_igual_jogadores(self) -> None:
        for jogadores in range(4, 33):
            resultado = calcular(jogadores, self.cfg)
            total = sum(resultado["premios"])
            self.assertAlmostEqual(total, jogadores, places=9)

    def test_premiados_com_crescimento_4(self) -> None:
        casos = {
            4: 3,
            14: 3,
            15: 4,
            18: 4,
            19: 5,
            27: 7,
            31: 8,
        }
        for jogadores, esperado in casos.items():
            self.assertEqual(calcular_premiados(jogadores, self.cfg), esperado)

    def test_premiados_nunca_maior_que_jogadores(self) -> None:
        cfg = self.cfg.copy()
        cfg["min_premiados"] = 5
        self.assertEqual(calcular_premiados(4, cfg), 4)

    def test_resultado_estrutura(self) -> None:
        resultado = calcular(10, self.cfg)
        self.assertEqual(resultado["jogadores"], 10)
        self.assertEqual(len(resultado["premios"]), resultado["premiados"])


class TestValidation(unittest.TestCase):
    def test_config_valida(self) -> None:
        validar_config(DEFAULT.copy())

    def test_config_campo_ausente(self) -> None:
        cfg = DEFAULT.copy()
        del cfg["min_jogadores"]
        with self.assertRaises(ConfigError):
            validar_config(cfg)

    def test_config_r_invalido(self) -> None:
        cfg = DEFAULT.copy()
        cfg["r"] = 1.5
        with self.assertRaises(ConfigError):
            validar_config(cfg)

    def test_jogadores_abaixo_minimo(self) -> None:
        with self.assertRaises(InputError):
            validar_jogadores(3, DEFAULT.copy())


if __name__ == "__main__":
    unittest.main()
