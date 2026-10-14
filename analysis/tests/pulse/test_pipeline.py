import pytest

from pulse.export import build_results
from pulse.pipeline import PulseRun

from .contract import check_results

RUN_INFO = {"commit": "abc1234", "manifest": "analysis/outputs/penang-pulse-manifest.json", "python": "3.12.9", "lastRun": "2026-10-14"}


def test_the_pipeline_writes_a_file_the_site_accepts(pulse_run: PulseRun) -> None:
    results = build_results(pulse_run.findings, pulse_run.geometry, pulse_run.points, RUN_INFO, {"OpenStreetMap": "2026-10-14"}, "2026-10-14T01:02:03+00:00")
    check_results(results)
    assert [d["population"] for d in results["districts"]] == [6000, 3000, 4000, 4500, 2500]
    assert results["keyNumbers"][1]["value"] == str(len(results["points"]))


def test_every_facility_used_is_a_point_and_the_dental_clinic_is_not(pulse_run: PulseRun) -> None:
    assert pulse_run.findings.counts == {"clinic": 3, "school": 3, "transit": 2}
    assert [p["category"] for p in pulse_run.points] == ["clinic"] * 3 + ["school"] * 3 + ["transit"] * 2
    assert pulse_run.outside == {"clinic": 1, "school": 0, "transit": 0}
    assert pulse_run.findings.years == (2013, 2022)


def test_both_population_maps_cover_every_district(pulse_run: PulseRun) -> None:
    assert pulse_run.cells == {"worldpop": [5, 6, 6, 6, 6], "meta": [5, 6, 6, 6, 6]}
    for shares in pulse_run.findings.shares.values():
        assert shares.shape == (5, 3, 3)
        assert shares.sum(axis=2) == pytest.approx(100)


def test_the_road_graph_drops_only_the_fragment(pulse_run: PulseRun) -> None:
    assert pulse_run.roads == {"nodes": 14, "edges": 14, "dropped_nodes": 2}


def test_the_map_has_both_bridges_and_all_six_towns(pulse_run: PulseRun) -> None:
    assert len(pulse_run.geometry["bridges"]) == 2
    assert len(pulse_run.geometry["places"]) == 6
    assert len(pulse_run.geometry["boundaries"]) == 3
