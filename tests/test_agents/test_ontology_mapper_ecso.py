"""
Unit tests for ECSO (Ecosystem Ontology) integration in Ontology Mapper.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aurelian.agents.ontology_mapper.ontology_mapper_config import (
    OntologyMapperDependencies,
    get_config,
)
from aurelian.agents.ontology_mapper.ontology_mapper_tools import (
    get_ontology_adapter,
    normalize_curie,
    search_terms,
)


def test_default_config_includes_ecso():
    """Verify that ecso is present in default ontologies list."""
    deps = OntologyMapperDependencies()
    assert "ecso" in deps.ontologies

    config = get_config()
    assert "ecso" in config.ontologies


def test_normalize_curie():
    """Verify CURIE normalization for DataONE ECSO URIs and standard identifiers."""
    # Standard HTTP DataONE URI
    assert (
        normalize_curie("http://purl.dataone.org/odo/ECSO_00001105")
        == "ECSO:00001105"
    )
    # HTTPS DataONE URI
    assert (
        normalize_curie("https://purl.dataone.org/odo/ECSO_00001105")
        == "ECSO:00001105"
    )
    # DataONE URI with www
    assert (
        normalize_curie("http://www.purl.dataone.org/odo/ECSO_00010074")
        == "ECSO:00010074"
    )
    # Angle-bracketed URI
    assert (
        normalize_curie("<http://purl.dataone.org/odo/ECSO_00001105>")
        == "ECSO:00001105"
    )
    # Already normalized CURIE
    assert normalize_curie("ECSO:00001105") == "ECSO:00001105"
    # Other ontology CURIEs should remain unchanged
    assert normalize_curie("CL:0000540") == "CL:0000540"
    assert normalize_curie("MONDO:0004975") == "MONDO:0004975"
    # Non-ECSO URIs should remain unchanged
    assert normalize_curie("http://example.org/test") == "http://example.org/test"


def test_get_ontology_adapter_ecso():
    """Verify adapter resolution for ecso (case-insensitive)."""
    get_ontology_adapter.cache_clear()
    adapter = get_ontology_adapter("ecso")
    assert adapter is not None

    adapter_upper = get_ontology_adapter("ECSO")
    assert adapter_upper is not None


def test_get_ontology_adapter_ecso_custom_env(tmp_path, monkeypatch):
    """Verify that ECSO_PATH environment variable is respected."""
    dummy_db = tmp_path / "custom_ecso.db"
    dummy_db.touch()

    monkeypatch.setenv("ECSO_PATH", str(dummy_db))
    get_ontology_adapter.cache_clear()

    with patch("aurelian.agents.ontology_mapper.ontology_mapper_tools.get_adapter") as mock_get_adapter:
        get_ontology_adapter("ecso")
        mock_get_adapter.assert_called_once_with(f"sqlite:{dummy_db}")

    get_ontology_adapter.cache_clear()


def test_get_ontology_adapter_ecso_fallback_to_owl(tmp_path, monkeypatch):
    """Verify fallback to Pronto adapter with ECSO8.owl when ecso.db is missing."""
    monkeypatch.delenv("ECSO_PATH", raising=False)
    get_ontology_adapter.cache_clear()

    fake_home = tmp_path / "home"
    fake_oaklib = fake_home / ".data" / "oaklib"
    fake_oaklib.mkdir(parents=True)
    owl_file = fake_oaklib / "ECSO8.owl"
    owl_file.touch()

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    with patch("aurelian.agents.ontology_mapper.ontology_mapper_tools.get_adapter") as mock_get_adapter:
        get_ontology_adapter("ecso")
        mock_get_adapter.assert_called_once_with(f"pronto:{owl_file}")

    get_ontology_adapter.cache_clear()


def test_get_ontology_adapter_ecso_download_owl(tmp_path, monkeypatch):
    """Verify pystow download fallback when neither ecso.db nor ECSO8.owl exists locally."""
    monkeypatch.delenv("ECSO_PATH", raising=False)
    get_ontology_adapter.cache_clear()

    fake_home = tmp_path / "home_empty"
    fake_oaklib = fake_home / ".data" / "oaklib"
    fake_oaklib.mkdir(parents=True)

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    downloaded_owl = fake_oaklib / "downloaded_ECSO8.owl"
    downloaded_owl.touch()

    with patch(
        "aurelian.agents.ontology_mapper.ontology_mapper_tools.pystow.ensure",
        return_value=downloaded_owl,
    ) as mock_pystow_ensure, patch(
        "aurelian.agents.ontology_mapper.ontology_mapper_tools.get_adapter"
    ) as mock_get_adapter:
        get_ontology_adapter("ecso")
        mock_pystow_ensure.assert_called_once_with(
            "oaklib",
            name="ECSO8.owl",
            url="https://raw.githubusercontent.com/DataONEorg/sem-prov-ontologies/main/ecso/ECSO8.owl",
        )
        mock_get_adapter.assert_called_once_with(f"pronto:{downloaded_owl}")

    get_ontology_adapter.cache_clear()


@pytest.mark.asyncio
async def test_search_terms_ecso():
    """Verify search_terms on ecso returns expected match and normalized CURIE."""
    get_ontology_adapter.cache_clear()
    deps = OntologyMapperDependencies()
    ctx = MagicMock(deps=deps)

    results = await search_terms(ctx, "ecso", "Carbon Flux")
    assert isinstance(results, list)
    assert len(results) > 0

    match = results[0]
    assert match["id"] == "ECSO:00001105"
    assert match["label"] == "Carbon Flux"
    assert match["ontology"] == "ECSO"
    assert match["match_type"] == "exact_label"
    assert match["confidence"] == 0.95


@pytest.mark.asyncio
async def test_search_terms_ecso_normalizes_pronto_uri():
    """Verify search_terms normalizes URI format returned by Pronto adapter."""
    mock_adapter = MagicMock()
    ctx = MagicMock(deps=OntologyMapperDependencies())

    # Mock search_ontology to simulate pronto returning a full URI
    mock_results = [("http://purl.dataone.org/odo/ECSO_00001105", "Carbon Flux")]

    with patch(
        "aurelian.agents.ontology_mapper.ontology_mapper_tools.get_ontology_adapter",
        return_value=mock_adapter,
    ), patch(
        "aurelian.agents.ontology_mapper.ontology_mapper_tools.search_ontology",
        return_value=mock_results,
    ):
        results = await search_terms(ctx, "ecso", "Carbon Flux")
        assert len(results) == 1
        assert results[0]["id"] == "ECSO:00001105"
        assert results[0]["label"] == "Carbon Flux"
