"""Unit tests for rounds."""

import pytest

from app.core.torneios.rounds import calcular_rodadas


@pytest.mark.parametrize("n,expected", [(8, 3), (9, 4), (4, 2), (32, 5)])
def test_calcular_rodadas(n, expected):
    assert calcular_rodadas(n) == expected
