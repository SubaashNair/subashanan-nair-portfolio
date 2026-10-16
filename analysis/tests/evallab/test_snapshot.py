import email.message
import io
import json
import urllib.error
import urllib.request
import urllib.response
from pathlib import Path

import pytest

from evallab import snapshot as snapshot_module
from evallab.snapshot import ALLOWED_HOSTS, BNM_LISTING, HEAD_URL, MYNIC_PAGE, MYNIC_URL, OPENDOSM_PAGE, TARBALL_URL, Freezer, check_url, freeze, freeze_dosm, http_get
from evallab.sources import bnm_latest, dosm_period, latest_edition, mynic_points
from forecasting.data import sha256_of

from .world import COMMIT, EDITION, STATS, TODAY, remote, serve, take_snapshot


def test_a_snapshot_records_every_file_and_release(tmp_path: Path) -> None:
    asked: list[str] = []
    snapshot = freeze(tmp_path, STATS, TODAY, serve(remote(), asked))

    assert snapshot["taken"] == "2026-10-15"
    assert snapshot["catalogue"] == {"repository": "data-gov-my/datagovmy-meta", "commit": COMMIT}
    assert all(sha256_of(tmp_path / f["path"]) == f["sha256"] and f["bytes"] == (tmp_path / f["path"]).stat().st_size for f in snapshot["files"])
    assert {f["path"] for f in snapshot["files"] if f["path"].startswith("datasets/")} == {
        "datasets/domains.parquet", "datasets/lfs_month.parquet", "datasets/lfs_month_youth.parquet", "datasets/monetary_aggregates.parquet"}
    assert [r["id"] for r in snapshot["releases"]] == [
        "labour_month_2026-08", "labour_month_2026-07", "labour_month_2026-06", "bnm_mhs_2026-08_table_1.3", "mynic_active_2026", "mynic_active_2025"]
    assert not any("2026-05" in url or url.endswith("2.1.xlsx") for url in asked)  # only the newest three releases, only the tables used
    assert not list(tmp_path.rglob("*.part"))


def test_every_page_the_snapshot_reads_is_saved_with_its_checksum(tmp_path: Path) -> None:
    snapshot = take_snapshot(tmp_path)
    by_url = {f["url"]: f for f in snapshot["files"] if f["url"]}
    for url in (BNM_LISTING, EDITION):
        entry = by_url[url]
        assert (tmp_path / entry["path"]).read_bytes() == remote()[url] and len(entry["sha256"]) == 64


def test_release_text_is_kept_page_by_page(tmp_path: Path) -> None:
    snapshot = take_snapshot(tmp_path)
    august = next(r for r in snapshot["releases"] if r["id"] == "labour_month_2026-08")
    pages = json.loads((tmp_path / august["pages"]).read_text())
    assert august["period"] == "2026-08" and august["page"] == "https://open.dosm.gov.my/publications/labour_month_2026-08"
    assert len(pages) == 2 and "The unemployment rate for August 2026 eased to 2.9 per cent." in pages[1]


def test_bnm_uses_the_newest_edition_and_the_year_on_january_rows(tmp_path: Path) -> None:
    snapshot = take_snapshot(tmp_path)
    table = next(r for r in snapshot["releases"] if r["agency"] == "BNM")
    assert table["page"].endswith("august-2026-1") and table["url"] == "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx"
    assert bnm_latest(tmp_path / table["raw"], 3) == (2636548.767, "2026-08")
    text = json.loads((tmp_path / table["pages"]).read_text())[0]
    assert "Source: Bank Negara Malaysia." in text and "2026-08: money supply M3 2,636,548.7670" in text


def test_a_second_freeze_reads_only_the_disk(tmp_path: Path) -> None:
    first = take_snapshot(tmp_path)
    assert freeze(tmp_path, STATS, TODAY, serve({})) == first  # serve({}) fails on any request


def test_a_changed_file_stops_the_run(tmp_path: Path) -> None:
    take_snapshot(tmp_path)
    (tmp_path / "datasets/lfs_month.parquet").write_bytes(b"edited")
    with pytest.raises(ValueError, match="datasets/lfs_month.parquet changed"):
        freeze(tmp_path, STATS, TODAY, serve({}))


def test_a_commit_that_is_not_a_sha_stops_the_snapshot(tmp_path: Path) -> None:
    files = {**remote(), "https://api.github.com/repos/data-gov-my/datagovmy-meta/commits/HEAD": b'{"message": "API rate limit exceeded"}'}
    with pytest.raises(ValueError, match="unexpected commit"):
        freeze(tmp_path, STATS, TODAY, serve(files))
    assert not (tmp_path / "snapshot.json").exists()


def test_release_periods_come_from_the_release_id() -> None:
    assert dosm_period("labour_month_2026-08") == "2026-08"
    assert dosm_period("bop_2026-q2") == "2026-Q2"
    with pytest.raises(ValueError, match="cannot tell the period"):
        dosm_period("tourism_2025")


def test_the_newest_bnm_edition_wins_whatever_the_link_order() -> None:
    html = ('<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-august-2026-1"></a>'
            '<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-december-2025"></a>'
            '<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-september-2026"></a>')
    assert latest_edition(html) == ("https://www.bnm.gov.my/-/monthly-highlights-statistics-in-september-2026", "2026-09")
    with pytest.raises(ValueError, match="no Monthly Highlights"):
        latest_edition("<html></html>")


def test_mynic_months_without_data_are_left_out(tmp_path: Path) -> None:
    path = tmp_path / "mynic.json"
    path.write_text(json.dumps({"year": "2026", "chartData": {"10": None, "9": 693122, "1": 821903, "2": None}}))
    assert mynic_points(path) == [("2026-01", 821903), ("2026-09", 693122)]


# Security: URLs and file names partly come from downloaded data, so they are checked before they are used.


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the network was touched")
    monkeypatch.setattr(snapshot_module, "opener", refuse)
    monkeypatch.setattr(snapshot_module, "POLITE_SECONDS", 0)


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "http://storage.dosm.gov.my/x", "ftp://storage.dosm.gov.my/x", "https://169.254.169.254/latest", "https://evil.example/x",
    "https://user@storage.dosm.gov.my/x", "https://storage.dosm.gov.my:8443/x", "https://storage.dosm.gov.my@evil.example/x",
    "https://storage.dosm.gov.my.evil.example/x", "https://storage.dosm.gov.my./x", "", "/etc/passwd"])
def test_http_get_refuses_any_url_off_the_allow_list(url: str, no_network: None) -> None:
    with pytest.raises(ValueError, match="refusing to fetch"):
        http_get(url)


def test_the_allow_list_is_the_publishers_hosts() -> None:
    assert ALLOWED_HOSTS == {"api.github.com", "codeload.github.com", "storage.data.gov.my", "storage.dosm.gov.my", "open.dosm.gov.my", "www.bnm.gov.my", "mynic.my"}


def test_the_publishers_own_urls_pass_the_check() -> None:
    for url in (HEAD_URL, TARBALL_URL.format(commit=COMMIT), BNM_LISTING, EDITION, MYNIC_URL.format(chart="active", year=2026), MYNIC_PAGE, OPENDOSM_PAGE.format(id="x"),
                "https://storage.dosm.gov.my:443/x.parquet"):
        assert check_url(url) == url


class Bounce(urllib.request.HTTPSHandler):
    """An allowed host that answers every request with a redirect to `location`."""

    location = ""

    def https_open(self, req: urllib.request.Request):  # type: ignore[override]
        response = urllib.response.addinfourl(io.BytesIO(b""), email.message.Message(), req.full_url, 302)
        response.msg = "Found"
        response.headers["Location"] = self.location
        return response


@pytest.mark.parametrize("target", ["file:///etc/passwd", "https://169.254.169.254/latest", "http://localhost:11434/api", "https://evil.example/x"])
def test_a_redirect_off_the_allow_list_is_refused(target: str, monkeypatch: pytest.MonkeyPatch) -> None:
    bounce = type("BounceTo", (Bounce,), {"location": target})
    monkeypatch.setattr(snapshot_module, "opener", lambda: urllib.request.build_opener(snapshot_module.CheckedRedirects, bounce))
    monkeypatch.setattr(snapshot_module, "POLITE_SECONDS", 0)
    with pytest.raises((ValueError, urllib.error.HTTPError)):  # urllib itself rejects a file:// target before our handler sees it
        http_get("https://storage.dosm.gov.my/x")


def test_a_redirect_to_another_allowed_host_is_followed() -> None:
    handler = snapshot_module.CheckedRedirects()
    request = urllib.request.Request("https://storage.dosm.gov.my/x")
    followed = handler.redirect_request(request, io.BytesIO(), 302, "Found", email.message.Message(), "https://storage.data.gov.my/y")
    assert followed is not None and followed.full_url == "https://storage.data.gov.my/y"
    with pytest.raises(ValueError, match="refusing to fetch"):
        handler.redirect_request(request, io.BytesIO(), 302, "Found", email.message.Message(), "https://169.254.169.254/latest")


def test_fetching_does_not_replace_the_global_opener(monkeypatch: pytest.MonkeyPatch) -> None:
    installed: list[object] = []
    monkeypatch.setattr(urllib.request, "install_opener", installed.append)
    assert snapshot_module.opener() is not None and installed == []


def test_save_refuses_a_path_outside_the_raw_directory(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    freezer = Freezer(raw, serve({}))
    for name in ("../escape.txt", "releases/../../escape.txt", "/tmp/escape.txt", "", "."):
        with pytest.raises(ValueError, match="outside"):
            freezer.save(name, b"x", None)
    assert not (tmp_path / "escape.txt").exists() and freezer.files == []


def test_save_refuses_a_symlink_that_leaves_the_raw_directory(tmp_path: Path) -> None:
    raw, outside = tmp_path / "raw", tmp_path / "outside"
    raw.mkdir(), outside.mkdir()
    (raw / "releases").symlink_to(outside)
    with pytest.raises(ValueError, match="outside"):
        Freezer(raw, serve({})).save("releases/a.pdf", b"x", None)
    assert list(outside.iterdir()) == []


def test_the_raw_directory_is_resolved_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "raw").mkdir()
    freezer = Freezer(tmp_path / "raw" / ".." / "raw", serve({}))
    monkeypatch.chdir(tmp_path)
    assert freezer.raw_dir == (tmp_path / "raw").resolve() and freezer.save("a.txt", b"x", None) == freezer.raw_dir / "a.txt"


@pytest.mark.parametrize("release_id", ["a/b", "../x", "a b", "a\\b", "", "x\n", "café"])
def test_a_release_id_outside_the_safe_characters_is_refused(release_id: str, tmp_path: Path) -> None:
    freezer = Freezer(tmp_path, serve({}))
    with pytest.raises(ValueError, match="not a safe file name"):
        freezer.pages(release_id, ["text"])
    index = [{"publication": release_id, "release_date": "2026-10-09", "en": {"title": "t", "resources": [{"resource_type": "pdf", "resource_link": "https://storage.dosm.gov.my/x.pdf"}]}}]
    with pytest.raises(ValueError, match="not a safe file name"):
        freeze_dosm(freezer, index, [r"^.*$"])
    assert freezer.files == []
