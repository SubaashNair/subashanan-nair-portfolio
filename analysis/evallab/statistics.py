"""The statistics the study asks about: where each one's open dataset lives and where its latest official figure is published."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

NUMBER = r"(?P<value>-?\d[\d,]*(?:\.\d+)?)"  # a figure in release text, commas allowed


@dataclass(frozen=True)
class Series:
    """Where data.gov.my keeps a statistic: one column of one dataset, filtered to one series."""

    dataset: str  # data.gov.my catalogue id
    column: str
    where: tuple[tuple[str, str], ...] = ()  # (column, value) pairs every row must match
    scale: float = 1.0  # dataset value times scale is the statistic in its own unit


@dataclass(frozen=True)
class Statistic:
    id: str
    agency: str  # "DOSM", "BNM" or "MYNIC"
    name_en: str
    name_ms: str
    unit: str
    decimals: int  # the publication's rounding
    quarterly: bool
    series: Series
    release: str  # DOSM: regex over release ids; BNM: "<table>:<column index>"; MYNIC: the statistics chart type
    pattern: str = ""  # DOSM: regex with a `value` group, searched in the release's English text
    release_scale: float = 1.0  # BNM: table value times release_scale is the statistic in its own unit


def _dosm(id: str, en: str, ms: str, unit: str, decimals: int, series: Series, release: str, pattern: str, quarterly: bool = False) -> Statistic:
    return Statistic(id, "DOSM", en, ms, unit, decimals, quarterly, series, release, pattern.replace("{N}", NUMBER))


def _bnm(id: str, en: str, ms: str, unit: str, decimals: int, series: Series, release: str, release_scale: float = 1.0) -> Statistic:
    return Statistic(id, "BNM", en, ms, unit, decimals, False, series, release, release_scale=release_scale)


def _mynic(id: str, en: str, ms: str, dataset: str, chart: str) -> Statistic:
    return Statistic(id, "MYNIC", en, ms, "domains", 0, False, Series(dataset, "registrations", (("series", "cumulative"), ("domain", "overall"))), chart)


LFS = r"^labour_month_\d{4}-\d{2}$"
TRADE = r"^trade_(?:headline_)?\d{4}-\d{2}$"
MEI = r"^mei_\d{4}-\d{2}$"
BOP = r"^bop_\d{4}-q\d$"
YOUTH = "lfs_month_youth"
COMMERCIAL = ("bank", "commercial")

STATISTICS: tuple[Statistic, ...] = (
    _dosm("cpi_inflation", "consumer price inflation (year on year)", "kadar inflasi harga pengguna (tahun ke tahun)", "per cent", 1,
          Series("cpi_headline_inflation", "inflation_yoy", (("division", "overall"),)), r"^cpi_\d{4}-\d{2}$",
          r"[Ii]nflation (?:increased|decreased|rose|fell|eased|remained|was|stood at|moderated)(?: by| at| to)? {N} per cent in"),
    _dosm("cpi_index", "consumer price index", "indeks harga pengguna", "index points", 1,
          Series("cpi_headline", "index", (("division", "overall"),)), r"^cpi_\d{4}-\d{2}$", r"index points (?:\w+ )?(?:to|at) {N}"),
    _dosm("unemployment_rate", "unemployment rate", "kadar pengangguran", "per cent", 1, Series("lfs_month", "u_rate"), LFS,
          r"[Uu]nemployment rate for \w+ \d{4} (?:\w+ ){1,3}{N} per cent"),
    _dosm("unemployed_persons", "number of unemployed persons", "bilangan penganggur", "thousand persons", 1, Series("lfs_month", "lf_unemployed"), LFS,
          r"number of unemployed in \w+ \d{4} .{0,80}?to {N} thousand persons"),
    _dosm("employed_persons", "number of employed persons", "bilangan penduduk bekerja", "million persons", 2, Series("lfs_month", "lf_employed", scale=0.001), LFS,
          r"number of employed persons .{0,80}?to {N} million persons"),
    _dosm("lfpr", "labour force participation rate", "kadar penyertaan tenaga buruh", "per cent", 1, Series("lfs_month", "p_rate"), LFS,
          r"participation rate \(LFPR\) .{0,60}?to {N} per cent"),
    _dosm("youth_rate_15_24", "youth unemployment rate for ages 15 to 24", "kadar pengangguran belia berumur 15 hingga 24 tahun", "per cent", 1,
          Series(YOUTH, "u_rate_15_24"), LFS, r"youth unemployment rate for those aged 15 to 24 years .{0,60}?to {N} per cent"),
    _dosm("youth_unemployed_15_24", "number of unemployed youth aged 15 to 24", "bilangan belia menganggur berumur 15 hingga 24 tahun", "thousand persons", 1,
          Series(YOUTH, "unemployed_15_24"), LFS, r"youth unemployment rate for those aged 15 to 24 years .{0,80}?with {N} thousand unemployed"),
    _dosm("youth_rate_15_30", "youth unemployment rate for ages 15 to 30", "kadar pengangguran belia berumur 15 hingga 30 tahun", "per cent", 1,
          Series(YOUTH, "u_rate_15_30"), LFS, r"unemployment rate among youth aged 15 to 30 years .{0,60}?to {N} per cent"),
    _dosm("youth_unemployed_15_30", "number of unemployed youth aged 15 to 30", "bilangan belia menganggur berumur 15 hingga 30 tahun", "thousand persons", 1,
          Series(YOUTH, "unemployed_15_30"), LFS, r"unemployment rate among youth aged 15 to 30 years .{0,120}?{N} thousand"),
    _dosm("exports", "value of exports for the month", "nilai eksport bulanan", "RM billion", 1,
          Series("trade_sitc_1d", "exports", (("section", "overall"),), scale=1e-9), TRADE, r"[Ee]xports .{0,60}?to RM{N} billion in \w+ \d{4}"),
    _dosm("imports", "value of imports for the month", "nilai import bulanan", "RM billion", 1,
          Series("trade_sitc_1d", "imports", (("section", "overall"),), scale=1e-9), TRADE, r"Imports .{0,140}?to RM{N} billion in \w+ \d{4}"),
    _dosm("ipi_growth", "industrial production index growth (year on year)", "pertumbuhan indeks pengeluaran perindustrian (tahun ke tahun)", "per cent", 1,
          Series("ipi", "index", (("series", "growth_yoy"),)), r"^ipi_\d{4}-\d{2}$",
          r"Industrial Production Index \(IPI\) (?:increased|decreased|rose|fell|grew|declined|contracted) by {N} per cent year-on-year"),
    _dosm("ppi_growth", "producer price index growth (year on year)", "pertumbuhan indeks harga pengeluar (tahun ke tahun)", "per cent", 1,
          Series("ppi", "index", (("series", "growth_yoy"),)), r"^ppi_\d{4}-\d{2}$",
          r"Producer Price Index (?:increased|decreased|rose|fell|declined) by {N} per cent"),
    _dosm("wrt_sales", "wholesale and retail trade sales value for the month", "nilai jualan perdagangan borong dan runcit bulanan", "RM billion", 1,
          Series("iowrt", "sales", (("series", "abs"),), scale=1e-3), r"^iowrt_\d{4}-\d{2}$", r"[Ww]holesale & retail trade sales value recorded RM{N} billion"),
    _dosm("leading_index", "leading index", "indeks pelopor", "index points", 1, Series("economic_indicators", "leading"), MEI,
          r"LI (?:increased|decreased|rose|fell|declined) by -?\d+(?:\.\d+)? per cent in \w+ \d{4}, recording {N} points"),
    _dosm("coincident_index", "coincident index", "indeks serentak", "index points", 1, Series("economic_indicators", "coincident"), MEI,
          r"the CI recorded .{0,80}?to reach {N} points"),
    _dosm("gdp_growth", "GDP growth (year on year)", "pertumbuhan KDNK (tahun ke tahun)", "per cent", 1,
          Series("gdp_qtr_real", "value", (("series", "growth_yoy"),)), r"^gdp_\d{4}-q\d$", r"quarter of \d{4}, expanding by {N} per cent", quarterly=True),
    _dosm("fdi_net", "net foreign direct investment inflow for the quarter", "aliran masuk bersih pelaburan langsung asing bagi suku tahun", "RM billion", 1,
          Series("fdi_flows", "net"), BOP, r"Foreign Direct Investment \(FDI\) .{0,40}?net inflow of RM{N} billion", quarterly=True),
    _dosm("current_account", "current account balance for the quarter", "imbangan akaun semasa bagi suku tahun", "RM billion", 1,
          Series("bop_balance", "balance", (("account", "ca"),), scale=1e-3), BOP,
          r"Current Account Balance \(CAB\) recorded a (?:surplus|deficit) of RM{N} billion", quarterly=True),
    _dosm("productivity_hour", "labour productivity as value added per hour worked", "produktiviti buruh sebagai nilai ditambah per jam bekerja", "RM per hour", 1,
          Series("productivity_qtr", "output_hour", (("series", "abs"), ("sector", "p0"))), r"^productivity_\d{4}-q\d$", r"value RM{N} per hour", quarterly=True),
    _bnm("m3", "money supply M3", "penawaran wang M3", "RM billion", 1, Series("monetary_aggregates", "value", (("measure", "m3_total"),), scale=1e-3), "1.3:3", 1e-3),
    _bnm("m1", "money supply M1", "penawaran wang M1", "RM billion", 1, Series("monetary_aggregates", "value", (("measure", "m1_total"),), scale=1e-3), "1.3:5", 1e-3),
    _bnm("fd_12mo", "12-month fixed deposit rate at commercial banks", "kadar deposit tetap 12 bulan di bank perdagangan", "per cent", 2,
         Series("interestrates", "value", (COMMERCIAL, ("rate", "fdr_12mo"))), "2.1:7"),
    _bnm("base_rate", "base rate of commercial banks", "kadar asas bank perdagangan", "per cent", 2, Series("interestrates", "value", (COMMERCIAL, ("rate", "br"))), "2.1:15"),
    _bnm("blr", "base lending rate of commercial banks", "kadar pinjaman asas bank perdagangan", "per cent", 2, Series("interestrates", "value", (COMMERCIAL, ("rate", "blr"))), "2.1:17"),
    _bnm("alr", "average lending rate of commercial banks", "kadar pinjaman purata bank perdagangan", "per cent", 2, Series("interestrates", "value", (COMMERCIAL, ("rate", "alr"))), "2.1:19"),
    _mynic("domains_active", "number of active .my domains", "bilangan domain .my yang aktif", "domains", "active"),
    _mynic("domains_ipv6", "number of .my domains with IPv6", "bilangan domain .my dengan IPv6", "domains_ipv6", "ipv6"),
    _mynic("domains_dnssec", "number of .my domains signed with DNSSEC", "bilangan domain .my yang ditandatangani dengan DNSSEC", "domains_dnssec", "dnssec"),
)


def period_of(day: date, quarterly: bool) -> str:
    """The period a dataset row covers: 2026-08 for a month, 2026-Q2 for a quarter."""
    return f"{day.year}-Q{(day.month - 1) // 3 + 1}" if quarterly else f"{day.year}-{day.month:02d}"


def find(statistic_id: str) -> Statistic:
    return next(s for s in STATISTICS if s.id == statistic_id)
