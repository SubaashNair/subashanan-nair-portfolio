import re

import numpy as np

from pulse.export import Findings, answer_text, district_entries, join_names, key_numbers, pct, shares_json

DASHES = re.compile("[–—]")
CLINIC = [(72.3, 23.5, 4.2), (48.2, 33.6, 18.2), (55.0, 33.0, 12.0), (61.0, 30.0, 9.0), (40.6, 38.2, 21.2)]
SCHOOL = [(90.0, 9.6, 0.4), (69.8, 25.0, 5.2), (81.0, 15.0, 4.0), (85.0, 12.0, 3.0), (59.6, 35.0, 5.4)]  # Barat Daya and SP Selatan tie at 5%
TRANSIT = [(95.0, 4.7, 0.3), (60.0, 20.0, 20.0), (70.0, 20.0, 10.0), (80.0, 15.0, 5.0), (50.0, 22.6, 27.4)]


def shares(clinic: list = CLINIC, school: list = SCHOOL, transit: list = TRANSIT) -> np.ndarray:
    return np.stack([np.array(clinic), np.array(school), np.array(transit)], axis=1)


def findings(worldpop: np.ndarray | None = None, meta: np.ndarray | None = None, transit_near: float = 57.6) -> Findings:
    wp = shares() if worldpop is None else worldpop
    return Findings(
        shares={"worldpop": wp, "meta": wp if meta is None else meta},
        transit_near=transit_near,
        totals=(556600, 237700, 339100, 423000, 184000),
        counts={"clinic": 120, "school": 432, "transit": 1885},
        years=(2013, 2022),
    )


def test_the_answer_names_the_best_and_worst_district_from_the_rounded_shares() -> None:
    assert answer_text(findings()) == (
        "In Timur Laut, 72% of residents live within 1 km of a public clinic by road. "
        "In Seberang Perai Selatan, 21% live more than 3 km away. "
        "For schools, the largest share more than 3 km away is 5%, in Barat Daya and Seberang Perai Selatan; "
        "for Rapid Penang stops, it is 27%, in Seberang Perai Selatan."
    )


def test_a_different_worst_district_with_meta_adds_a_sentence() -> None:
    meta_clinic = [*CLINIC[:1], (40.0, 35.0, 25.0), *CLINIC[2:]]
    assert answer_text(findings(meta=shares(clinic=meta_clinic))).endswith(
        "With Meta's 30 m population map instead of WorldPop, Barat Daya has the largest share more than 3 km from a clinic."
    )


def test_a_share_that_rounds_to_zero_reads_under_1_percent() -> None:
    low = [(99.5, 0.2, 0.3)] * 5
    text = answer_text(findings(shares(clinic=low, school=low, transit=low)))
    assert "In Timur Laut, under 1% live more than 3 km away." in text
    assert "is under 1%, in Timur Laut, Barat Daya, Seberang Perai Utara, Seberang Perai Tengah and Seberang Perai Selatan;" in text
    assert key_numbers(findings(transit_near=0.4), "2026-10-14")[2]["value"] == "under 1%"


def test_key_numbers_come_from_templates() -> None:
    meta_clinic = [*CLINIC[:4], (45.0, 36.0, 19.0)]
    assert key_numbers(findings(meta=shares(clinic=meta_clinic)), "2026-10-14T03:04:05+00:00") == [
        {
            "value": "21%",
            "label": "of Seberang Perai Selatan residents live more than 3 km by road from a public clinic.",
            "caveat": "19% with Meta's 30 m population map instead of WorldPop.",
        },
        {
            "value": "2,437",
            "label": "public clinics, schools and Rapid Penang stops mapped.",
            "caveat": "Dental clinics and private clinics are not included; facility records are dated 2013 to 2022.",
        },
        {
            "value": "58%",
            "label": "of Penang residents live within 1 km by road of a Rapid Penang stop.",
            "caveat": "Stops from the GTFS feed retrieved on 14 October 2026; distance says nothing about how often buses run.",
        },
    ]


def test_district_entries_keep_the_tiles_and_the_table_consistent() -> None:
    entries = district_entries(findings())
    assert [e["id"] for e in entries] == ["tl", "bd", "spu", "spt", "sps"]
    assert [e["short"] for e in entries] == ["Timur Laut", "Barat Daya", "SP Utara", "SP Tengah", "SP Selatan"]
    assert entries[0]["bands"] == [72, 24, 4] and entries[4]["bands"] == [41, 38, 21]
    assert all(sum(e["bands"]) == 100 and e["far"]["clinic"] == e["bands"][2] for e in entries)
    assert entries[4]["far"] == {"clinic": 21, "school": 5, "transit": 27}
    assert [e["population"] for e in entries] == [556600, 237700, 339100, 423000, 184000]


def test_helpers_and_copy_rules() -> None:
    assert [pct(0), pct(7)] == ["under 1%", "7%"]
    assert [join_names(["A"]), join_names(["A", "B"]), join_names(["A", "B", "C"])] == ["A", "A and B", "A, B and C"]
    assert shares_json(shares())["sps"]["transit"] == [50.0, 22.6, 27.4]
    prose = [answer_text(findings()), *(v for n in key_numbers(findings(), "2026-10-14") for v in n.values())]
    assert not any(DASHES.search(p) for p in prose)


def test_a_caveat_that_starts_with_a_zero_share_reads_under_1_percent_capitalised() -> None:
    meta_clinic = [*CLINIC[:4], (60.0, 39.8, 0.2)]
    caveat = key_numbers(findings(meta=shares(clinic=meta_clinic)), "2026-10-14")[0]["caveat"]
    assert caveat == "Under 1% with Meta's 30 m population map instead of WorldPop."
