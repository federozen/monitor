"""Pruebas de la Fase 2 sin red ni credenciales: fetcher y writer falsos.

Validan que el pipeline (a) filtra por frescura antes de recomendar, (b) mapea
las recomendaciones a filas de Agenda, (c) escribe solo si el writer está
disponible, y (d) preserva la Agenda anterior cuando el corte se degrada.
"""
import sys
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from monitor.config import EditorialConfig
from monitor.dates import parse_datetime
from monitor.models import Article
from monitor.pipeline import run_pipeline


AHORA = parse_datetime("2026-08-04T12:00:00-03:00")


def art(article_id, title, publisher, minutos_atras, origin="rss"):
    return Article(
        article_id=article_id,
        title=title,
        url=f"https://ej.example/{article_id}",
        publisher=publisher,
        date_published=AHORA - timedelta(minutes=minutos_atras),
        date_origin=origin,
    )


class FakeFetcher:
    def __init__(self, articulos, ole_titles, salud):
        self._data = (articulos, ole_titles, salud)

    def fetch(self):
        return self._data


class FakeWriter:
    def __init__(self, disponible=True, previas=None):
        self._disp = disponible
        self._previas = previas or []
        self.agenda_escrita = None
        self.snapshot_escrito = None

    def disponible(self):
        return self._disp

    def leer_agenda_previa(self):
        return list(self._previas)

    def escribir_agenda(self, filas):
        self.agenda_escrita = filas

    def escribir_snapshot(self, filas):
        self.snapshot_escrito = filas


class PipelineTests(unittest.TestCase):
    def test_filtra_agregador_y_recomienda_lo_fresco(self):
        articulos = [
            art("a1", "River confirmó una baja para el partido", "River Oficial", 60),
            art("a2", "River tendrá una baja ante su rival", "TyC Sports", 30),
            # Fecha de agregador: no debe entrar al resumen (para_verificar).
            art("old", "Recuerdos de la final del Mundial", "Google News", 20, origin="discovery_timestamp"),
        ]
        fetcher = FakeFetcher(articulos, ole_titles=[], salud=[{"status": "ok"}, {"status": "ok"}])
        writer = FakeWriter(disponible=True)

        resumen = run_pipeline(fetcher, writer, now=AHORA)

        self.assertEqual(resumen["articulos_leidos"], 3)
        self.assertEqual(resumen["articulos_frescos"], 2)  # el de agregador queda afuera
        self.assertEqual(resumen["historias"], 1)          # los dos de River clusterizan
        self.assertTrue(resumen["escribio_planilla"])
        self.assertEqual(len(writer.agenda_escrita), 1)
        fila = writer.agenda_escrita[0]
        self.assertEqual(fila["Medios"], 2)
        self.assertIn(fila["Accion"], {"PUBLICAR", "VERIFICAR", "SEGUIR", "ACTUALIZAR", "NO_HACER_NADA"})

    def test_no_escribe_si_writer_no_disponible(self):
        articulos = [art("a1", "Boca cierra un refuerzo", "ESPN", 15)]
        fetcher = FakeFetcher(articulos, ole_titles=[], salud=[{"status": "ok"}])
        writer = FakeWriter(disponible=False)

        resumen = run_pipeline(fetcher, writer, now=AHORA)

        self.assertFalse(resumen["escribio_planilla"])
        self.assertIsNone(writer.agenda_escrita)
        self.assertEqual(resumen["recomendaciones"], 1)  # igual procesó todo

    def test_corte_degradado_preserva_agenda_anterior(self):
        articulos = [art("a1", "Selección: novedad de último momento", "AFA Oficial", 10)]
        # 1 de 3 fuentes ok = 33% < 60% => corte degradado.
        salud = [{"status": "ok"}, {"status": "error"}, {"status": "error"}]
        fetcher = FakeFetcher(articulos, ole_titles=[], salud=salud)
        previa = {"story_id": "story_vieja", "Clave": "story_vieja",
                  "Tema": "Tema anterior", "Estado": "pendiente"}
        writer = FakeWriter(disponible=True, previas=[previa])

        resumen = run_pipeline(fetcher, writer, now=AHORA)

        self.assertEqual(resumen["calidad"], "DEGRADADO")
        self.assertTrue(resumen["preservo_anterior"])
        claves = {f.get("story_id") for f in writer.agenda_escrita}
        self.assertIn("story_vieja", claves)  # no se perdió la fila anterior

    def test_respeta_tope_de_temas(self):
        articulos = [art(f"a{i}", f"Tema numero {i} distinto", f"Medio{i}", 5) for i in range(10)]
        fetcher = FakeFetcher(articulos, ole_titles=[], salud=[{"status": "ok"}])
        writer = FakeWriter(disponible=True)
        cfg = EditorialConfig(max_summary_topics=3)

        resumen = run_pipeline(fetcher, writer, now=AHORA, cfg=cfg)

        self.assertLessEqual(resumen["recomendaciones"], 3)


if __name__ == "__main__":
    unittest.main()
