import re
from datetime import date

import pytest

from evallab.statistics import STATISTICS, period_of

# Headline sentences from the real releases, checked on 2026-10-15 (whitespace collapsed as pdf_pages does), with the figure each pattern must find.
REAL_SENTENCES = {
    "cpi_inflation": ("Malaysia's inflation increased 1.9 per cent in August 2026 as compared to 1.8 per cent in the previous month", "1.9"),
    "cpi_index": ("with the index points increased to 137.5 from 134.9 (August 2025)", "137.5"),
    "unemployment_rate": ("The unemployment rate for August 2026 eased to 2.9 per cent", "2.9"),
    "unemployed_persons": ("The number of unemployed in August 2026 declined by 8.7 thousand persons (-1.7%) to 511.6 thousand persons, compared to", "511.6"),
    "employed_persons": ("the number of employed persons grew modestly by 0.2 per cent (+28.8 thousand persons) to 16.87 million persons, up from", "16.87"),
    "lfpr": ("The labour force participation rate (LFPR) edged up by 0.1 percentage point to 71.0 per cent (July 2026: 70.9%)", "71.0"),
    "youth_rate_15_24": ("The youth unemployment rate for those aged 15 to 24 years decreased by 0.1 percentage point to 10.1 per cent, with 291.3 thousand unemployed persons", "10.1"),
    "youth_unemployed_15_24": ("The youth unemployment rate for those aged 15 to 24 years decreased by 0.1 percentage point to 10.1 per cent, with 291.3 thousand unemployed persons", "291.3"),
    "youth_rate_15_30": ("the unemployment rate among youth aged 15 to 30 years also decreased by 0.1 percentage point to 6.3 per cent, corresponding to 394.6 thousand", "6.3"),
    "youth_unemployed_15_30": ("the unemployment rate among youth aged 15 to 30 years also decreased by 0.1 percentage point to 6.3 per cent, corresponding to 394.6 thousand", "394.6"),
    "exports": ("Malaysia's exports surged by 45.5 per cent y-o-y to RM191.0 billion in August 2026.", "191.0"),
    "imports": ("Imports recorded double-digit growth of 41.1 per cent or RM47.5 billion, rising from RM115.5 billion to RM163.0 billion in August 2026.", "163.0"),
    "ipi_growth": ("The Industrial Production Index (IPI) increased by 5.0 per cent year-on-year in August 2026", "5.0"),
    "ppi_growth": ("Malaysia's Producer Price Index increased by 10.7 per cent in August 2026", "10.7"),
    "wrt_sales": ("Wholesale & retail trade sales value recorded RM173.0 billion in August 2026", "173.0"),
    "leading_index": ("The annual growth of the LI increased by 1.1 per cent in July 2026, recording 115.3 points compared to 114.0 points", "115.3"),
    "coincident_index": ("the CI recorded a year-on-year growth of 1.7 per cent to reach 131.5 points in July 2026", "131.5"),
    "gdp_growth": ("in the second quarter of 2026, expanding by 6.0 per cent as compared to 5.4 per cent in the preceding quarter", "6.0"),
    "fdi_net": ("Foreign Direct Investment (FDI) registered a lower net inflow of RM7.4 billion in the second quarter of 2026", "7.4"),
    "current_account": ("Malaysia's Current Account Balance (CAB) recorded a surplus of RM10.8 billion in the second quarter of 2026", "10.8"),
    "productivity_hour": ("recorded a growth of 5.5 per cent with value RM46.5 per hour compared to the preceding quarter", "46.5"),
}


def test_there_are_thirty_statistics_from_three_agencies() -> None:
    assert len(STATISTICS) == 30
    assert len({s.id for s in STATISTICS}) == 30
    assert {a: sum(s.agency == a for s in STATISTICS) for a in ("DOSM", "BNM", "MYNIC")} == {"DOSM": 21, "BNM": 6, "MYNIC": 3}


@pytest.mark.parametrize("statistic", [s for s in STATISTICS if s.agency == "DOSM"], ids=lambda s: s.id)
def test_each_dosm_pattern_finds_its_headline_figure(statistic) -> None:
    sentence, figure = REAL_SENTENCES[statistic.id]
    match = re.search(statistic.pattern, sentence)
    assert match is not None and match["value"] == figure


def test_bnm_and_mynic_name_a_table_column_or_a_chart() -> None:
    assert all(re.fullmatch(r"\d\.\d:\d+", s.release) and s.release_scale > 0 for s in STATISTICS if s.agency == "BNM")
    assert {s.release for s in STATISTICS if s.agency == "MYNIC"} == {"active", "ipv6", "dnssec"}


def test_periods_are_months_or_quarters() -> None:
    assert period_of(date(2026, 8, 1), quarterly=False) == "2026-08"
    assert period_of(date(2026, 4, 1), quarterly=True) == "2026-Q2"
    assert period_of(date(2026, 12, 1), quarterly=True) == "2026-Q4"
