"""Unit tests for premiacao calculator."""

import pytest

from app.core.premiacao.calculator import calcular, calcular_premiados
from app.core.premiacao.presets import DEFAULT_PRESET
from app.core.premiacao.validation import ConfigError, InputError, validar_config, validar_jogadores


@pytest.fixture
def cfg():
    return {k: v for k, v in DEFAULT_PRESET.items() if k != "label"}


class TestCalculator:
    def test_soma_premios_igual_jogadores(self, cfg):
        for jogadores in range(4, 33):
            resultado = calcular(jogadores, cfg)
            total = sum(resultado["premios"])
            assert total == pytest.approx(jogadores, abs=1e-9)

    def test_premiados_com_crescimento_4(self, cfg):
        casos = {4: 3, 14: 3, 15: 4, 18: 4, 19: 5, 27: 7, 31: 8}
        for jogadores, esperado in casos.items():
            assert calcular_premiados(jogadores, cfg) == esperado

    def test_premiados_nunca_maior_que_jogadores(self, cfg):
        cfg2 = {**cfg, "min_premiados": 5}
        assert calcular_premiados(4, cfg2) == 4

    def test_resultado_estrutura(self, cfg):
        resultado = calcular(10, cfg)
        assert resultado["jogadores"] == 10
        assert len(resultado["premios"]) == resultado["premiados"]


class TestValidation:
    def test_config_valida(self, cfg):
        validar_config(cfg.copy())

    def test_config_campo_ausente(self, cfg):
        cfg2 = cfg.copy()
        del cfg2["min_jogadores"]
        with pytest.raises(ConfigError):
            validar_config(cfg2)

    def test_config_r_invalido(self, cfg):
        cfg2 = {**cfg, "r": 1.5}
        with pytest.raises(ConfigError):
            validar_config(cfg2)

    def test_jogadores_abaixo_minimo(self, cfg):
        with pytest.raises(InputError):
            validar_jogadores(3, cfg)
