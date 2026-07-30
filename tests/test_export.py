"""Testes de exportação."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helpers.export import limpar_exports, listar_exports, salvar_csv


class TestExport(unittest.TestCase):
    def test_salvar_substituir_e_limpar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exports = Path(tmp)

            with patch("helpers.export.EXPORTS_DIR", exports):
                resultados = [
                    {"jogadores": 4, "premiados": 3, "premios": [1.79, 1.29, 0.92]},
                ]

                caminho, substituiu = salvar_csv(resultados, 4, 8)
                self.assertFalse(substituiu)
                self.assertTrue(Path(caminho).exists())

                _, substituiu = salvar_csv(resultados, 4, 8)
                self.assertTrue(substituiu)

                self.assertEqual(len(listar_exports()), 1)
                self.assertEqual(limpar_exports(), 1)
                self.assertEqual(listar_exports(), [])


if __name__ == "__main__":
    unittest.main()
