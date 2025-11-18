"""
Tests for chart loaders and operations modules.

This module tests the chart file loading and manipulation functions.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_utils import setup_test_imports
setup_test_imports()

from holdem_cli.charts.loaders import (
    create_chart_from_file, load_json_chart, load_simple_chart,
    load_pio_chart, load_gto_wizard_chart,
    _normalize_pio_hand, _parse_pio_action, _parse_frequency, _parse_ev,
    _normalize_gto_hand, _parse_gto_action
)
from holdem_cli.charts.operations import (
    merge_charts, filter_chart_by_action, filter_chart_by_frequency,
    get_chart_statistics, export_chart_statistics, validate_chart
)
from holdem_cli.types import HandAction, ChartAction


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_actions():
    """Create sample chart actions."""
    return {
        "AA": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=2.5, notes="Premium"),
        "KK": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=2.0, notes="Premium"),
        "QQ": HandAction(action=ChartAction.RAISE, frequency=0.9, ev=1.5, notes="Strong"),
        "AKs": HandAction(action=ChartAction.CALL, frequency=0.8, ev=1.0, notes="Suited"),
        "72o": HandAction(action=ChartAction.FOLD, frequency=1.0, ev=-0.5, notes="Trash"),
    }


@pytest.fixture
def json_chart_file():
    """Create a temporary JSON chart file."""
    data = {
        "ranges": {
            "AA": {"action": "raise", "frequency": 1.0, "ev": 2.5, "notes": "Premium"},
            "KK": {"action": "raise", "frequency": 1.0, "ev": 2.0, "notes": "Premium"},
            "72o": {"action": "fold", "frequency": 1.0}
        }
    }
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as f:
        json.dump(data, f)
        filepath = f.name
    yield filepath
    os.unlink(filepath)


@pytest.fixture
def simple_chart_file():
    """Create a temporary simple chart file."""
    content = """# Sample chart
AA raise 1.0
KK raise 1.0
QQ raise 0.9
72o fold 1.0
"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as f:
        f.write(content)
        filepath = f.name
    yield filepath
    os.unlink(filepath)


@pytest.fixture
def csv_chart_file():
    """Create a temporary CSV chart file."""
    content = """Hand,Action,Frequency,EV,Notes
AA,Raise,1.0,2.5,Premium
KK,Raise,1.0,2.0,Premium
72o,Fold,1.0,-0.5,Trash
"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w') as f:
        f.write(content)
        filepath = f.name
    yield filepath
    os.unlink(filepath)


# =============================================================================
# Loader Tests
# =============================================================================

class TestCreateChartFromFile:
    def test_load_json(self, json_chart_file):
        chart = create_chart_from_file(json_chart_file, "json")
        assert "AA" in chart
        assert "KK" in chart
        assert chart["AA"].action == ChartAction.RAISE

    def test_load_simple(self, simple_chart_file):
        chart = create_chart_from_file(simple_chart_file, "simple")
        assert "AA" in chart
        assert chart["AA"].action == ChartAction.RAISE

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            create_chart_from_file("/nonexistent/file.json", "json")

    def test_unsupported_format(self, json_chart_file):
        with pytest.raises(ValueError, match="Unsupported"):
            create_chart_from_file(json_chart_file, "unsupported")


class TestLoadJsonChart:
    def test_load_basic(self, json_chart_file):
        chart = load_json_chart(Path(json_chart_file))
        assert len(chart) == 3
        assert "AA" in chart

    def test_load_with_ev(self, json_chart_file):
        chart = load_json_chart(Path(json_chart_file))
        assert chart["AA"].ev == 2.5

    def test_load_with_notes(self, json_chart_file):
        chart = load_json_chart(Path(json_chart_file))
        assert chart["AA"].notes == "Premium"

    def test_default_values(self, json_chart_file):
        chart = load_json_chart(Path(json_chart_file))
        # 72o doesn't have ev/notes in the test data
        assert chart["72o"].ev is None or chart["72o"].notes == ""


class TestLoadSimpleChart:
    def test_load_basic(self, simple_chart_file):
        chart = load_simple_chart(Path(simple_chart_file))
        assert len(chart) == 4
        assert "AA" in chart

    def test_ignores_comments(self, simple_chart_file):
        chart = load_simple_chart(Path(simple_chart_file))
        # Comments should be ignored
        for hand in chart.keys():
            assert not hand.startswith("#")

    def test_parses_frequency(self, simple_chart_file):
        chart = load_simple_chart(Path(simple_chart_file))
        assert chart["QQ"].frequency == 0.9


class TestLoadPioChart:
    def test_load_csv_format(self, csv_chart_file):
        chart = load_pio_chart(Path(csv_chart_file))
        assert "AA" in chart
        assert chart["AA"].action == ChartAction.RAISE

    def test_load_with_ev(self, csv_chart_file):
        chart = load_pio_chart(Path(csv_chart_file))
        assert chart["AA"].ev == 2.5


class TestLoadGtoWizardChart:
    def test_load_csv_format(self, csv_chart_file):
        chart = load_gto_wizard_chart(Path(csv_chart_file))
        assert "AA" in chart


# =============================================================================
# Parser Helper Tests
# =============================================================================

class TestNormalizePioHand:
    def test_empty_string(self):
        assert _normalize_pio_hand("") == ""

    def test_pocket_pair(self):
        assert _normalize_pio_hand("AA") == "AA"
        assert _normalize_pio_hand("KK") == "KK"

    def test_suited(self):
        assert _normalize_pio_hand("AKS") == "AKS"

    def test_offsuit(self):
        assert _normalize_pio_hand("AKO") == "AKO"

    def test_adds_offsuit_default(self):
        result = _normalize_pio_hand("AK")
        assert result == "AKo"

    def test_removes_brackets(self):
        result = _normalize_pio_hand("[AA]")
        assert result == "AA"


class TestParsePioAction:
    def test_raise(self):
        assert _parse_pio_action("Raise") == ChartAction.RAISE
        assert _parse_pio_action("R") == ChartAction.RAISE

    def test_call(self):
        assert _parse_pio_action("Call") == ChartAction.CALL
        assert _parse_pio_action("C") == ChartAction.CALL

    def test_fold(self):
        assert _parse_pio_action("Fold") == ChartAction.FOLD
        assert _parse_pio_action("F") == ChartAction.FOLD

    def test_mixed(self):
        assert _parse_pio_action("Mixed") == ChartAction.MIXED

    def test_check(self):
        assert _parse_pio_action("Check") == ChartAction.CHECK
        assert _parse_pio_action("X") == ChartAction.CHECK

    def test_unknown_defaults_to_fold(self):
        assert _parse_pio_action("Unknown") == ChartAction.FOLD


class TestParseFrequency:
    def test_empty_string(self):
        assert _parse_frequency("") == 1.0

    def test_decimal(self):
        assert _parse_frequency("0.75") == 0.75

    def test_percentage(self):
        assert _parse_frequency("75%") == 0.75

    def test_invalid(self):
        assert _parse_frequency("invalid") == 1.0


class TestParseEv:
    def test_empty_string(self):
        assert _parse_ev("") is None

    def test_valid_float(self):
        assert _parse_ev("2.5") == 2.5

    def test_negative(self):
        assert _parse_ev("-0.5") == -0.5

    def test_invalid(self):
        assert _parse_ev("invalid") is None


class TestNormalizeGtoHand:
    def test_empty_string(self):
        assert _normalize_gto_hand("") == ""

    def test_pocket_pair(self):
        assert _normalize_gto_hand("AA") == "AA"

    def test_suit_indicators(self):
        assert _normalize_gto_hand("AKH") == "AKs"  # Hearts -> suited
        assert _normalize_gto_hand("AKD") == "AKs"  # Diamonds -> suited
        assert _normalize_gto_hand("AKS") == "AKs"  # Spades -> suited


class TestParseGtoAction:
    def test_raise_variants(self):
        assert _parse_gto_action("Raise") == ChartAction.RAISE
        assert _parse_gto_action("3Bet") == ChartAction.RAISE
        assert _parse_gto_action("Bet") == ChartAction.RAISE

    def test_call(self):
        assert _parse_gto_action("Call") == ChartAction.CALL

    def test_fold(self):
        assert _parse_gto_action("Fold") == ChartAction.FOLD

    def test_limp_check(self):
        assert _parse_gto_action("Limp") == ChartAction.CHECK
        assert _parse_gto_action("Check") == ChartAction.CHECK


# =============================================================================
# Operations Tests
# =============================================================================

class TestMergeCharts:
    def test_merge_no_overlap(self, sample_actions):
        chart1 = {"AA": sample_actions["AA"]}
        chart2 = {"KK": sample_actions["KK"]}

        merged = merge_charts(chart1, chart2)
        assert "AA" in merged
        assert "KK" in merged

    def test_merge_override(self, sample_actions):
        chart1 = {"AA": HandAction(action=ChartAction.FOLD, frequency=1.0)}
        chart2 = {"AA": HandAction(action=ChartAction.RAISE, frequency=1.0)}

        merged = merge_charts(chart1, chart2, "override")
        assert merged["AA"].action == ChartAction.RAISE

    def test_merge_keep_existing(self, sample_actions):
        chart1 = {"AA": HandAction(action=ChartAction.FOLD, frequency=1.0)}
        chart2 = {"AA": HandAction(action=ChartAction.RAISE, frequency=1.0)}

        merged = merge_charts(chart1, chart2, "keep_existing")
        assert merged["AA"].action == ChartAction.FOLD

    def test_merge_average(self):
        chart1 = {"AA": HandAction(action=ChartAction.RAISE, frequency=0.8, ev=2.0)}
        chart2 = {"AA": HandAction(action=ChartAction.RAISE, frequency=1.0, ev=3.0)}

        merged = merge_charts(chart1, chart2, "average")
        assert merged["AA"].frequency == 0.9
        assert merged["AA"].ev == 2.5


class TestFilterChartByAction:
    def test_filter_raise(self, sample_actions):
        filtered = filter_chart_by_action(sample_actions, [ChartAction.RAISE])
        assert len(filtered) == 3  # AA, KK, QQ
        assert all(a.action == ChartAction.RAISE for a in filtered.values())

    def test_filter_multiple_actions(self, sample_actions):
        filtered = filter_chart_by_action(
            sample_actions, [ChartAction.RAISE, ChartAction.CALL]
        )
        assert len(filtered) == 4  # AA, KK, QQ, AKs

    def test_filter_no_matches(self, sample_actions):
        filtered = filter_chart_by_action(sample_actions, [ChartAction.BLUFF])
        assert len(filtered) == 0


class TestFilterChartByFrequency:
    def test_filter_high_frequency(self, sample_actions):
        filtered = filter_chart_by_frequency(sample_actions, min_frequency=0.95)
        assert "AA" in filtered
        assert "KK" in filtered
        assert "72o" in filtered
        assert "QQ" not in filtered

    def test_filter_range(self, sample_actions):
        filtered = filter_chart_by_frequency(
            sample_actions, min_frequency=0.8, max_frequency=0.95
        )
        assert "QQ" in filtered
        assert "AKs" in filtered
        assert "AA" not in filtered


class TestGetChartStatistics:
    def test_empty_chart(self):
        stats = get_chart_statistics({})
        assert stats == {}

    def test_total_hands(self, sample_actions):
        stats = get_chart_statistics(sample_actions)
        assert stats["total_hands"] == 5

    def test_action_distribution(self, sample_actions):
        stats = get_chart_statistics(sample_actions)
        assert "actions" in stats
        assert stats["actions"]["raise"] == 3
        assert stats["actions"]["call"] == 1
        assert stats["actions"]["fold"] == 1

    def test_frequency_stats(self, sample_actions):
        stats = get_chart_statistics(sample_actions)
        assert "frequency_stats" in stats
        assert "min" in stats["frequency_stats"]
        assert "max" in stats["frequency_stats"]
        assert "avg" in stats["frequency_stats"]

    def test_ev_stats(self, sample_actions):
        stats = get_chart_statistics(sample_actions)
        assert "ev_stats" in stats
        assert "positive_ev_hands" in stats["ev_stats"]

    def test_hand_types(self, sample_actions):
        stats = get_chart_statistics(sample_actions)
        assert "hand_types" in stats
        assert stats["hand_types"]["pocket_pairs"] == 3  # AA, KK, QQ
        assert stats["hand_types"]["suited"] == 1  # AKs
        assert stats["hand_types"]["offsuit"] == 1  # 72o


class TestExportChartStatistics:
    def test_export_creates_file(self, sample_actions):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            filepath = f.name

        try:
            export_chart_statistics(sample_actions, filepath)
            assert os.path.exists(filepath)

            with open(filepath) as f:
                data = json.load(f)

            assert "export_format" in data
            assert "statistics" in data
            assert data["statistics"]["total_hands"] == 5
        finally:
            os.unlink(filepath)


class TestValidateChart:
    def test_empty_chart(self):
        warnings = validate_chart({})
        assert "Chart is empty" in warnings

    def test_valid_chart(self, sample_actions):
        warnings = validate_chart(sample_actions)
        assert len(warnings) == 0

    def test_invalid_hand_format(self):
        invalid_chart = {
            "XYZ": HandAction(action=ChartAction.RAISE, frequency=1.0)
        }
        warnings = validate_chart(invalid_chart)
        assert any("Invalid" in w for w in warnings)

    def test_invalid_frequency(self):
        invalid_chart = {
            "AA": HandAction(action=ChartAction.RAISE, frequency=1.5)
        }
        warnings = validate_chart(invalid_chart)
        assert any("frequency" in w for w in warnings)

    def test_valid_pocket_pair(self):
        chart = {"AA": HandAction(action=ChartAction.RAISE, frequency=1.0)}
        warnings = validate_chart(chart)
        assert len(warnings) == 0

    def test_valid_suited(self):
        chart = {"AKs": HandAction(action=ChartAction.RAISE, frequency=1.0)}
        warnings = validate_chart(chart)
        assert len(warnings) == 0

    def test_valid_offsuit(self):
        chart = {"AKo": HandAction(action=ChartAction.RAISE, frequency=1.0)}
        warnings = validate_chart(chart)
        assert len(warnings) == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestLoadersOperationsIntegration:
    def test_load_validate_filter_workflow(self, json_chart_file):
        """Test complete workflow: load -> validate -> filter -> statistics."""
        # Load chart
        chart = create_chart_from_file(json_chart_file, "json")
        assert len(chart) > 0

        # Validate
        warnings = validate_chart(chart)
        assert len(warnings) == 0

        # Filter by action
        raises = filter_chart_by_action(chart, [ChartAction.RAISE])
        assert len(raises) > 0

        # Get statistics
        stats = get_chart_statistics(raises)
        assert stats["total_hands"] == len(raises)

    def test_merge_and_validate(self, sample_actions):
        """Test merging two charts and validating result."""
        chart1 = {"AA": sample_actions["AA"], "KK": sample_actions["KK"]}
        chart2 = {"QQ": sample_actions["QQ"], "AKs": sample_actions["AKs"]}

        merged = merge_charts(chart1, chart2)
        warnings = validate_chart(merged)

        assert len(merged) == 4
        assert len(warnings) == 0
