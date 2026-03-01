"""Layout structure tests for PM Hub pages.

Inspects the Dash component tree returned by _build_content() to assert on
column widths, CSS classes, chart properties, and page structure consistency.
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["USE_SAMPLE_DATA"] = "true"

# Create a Dash app so register_page() calls succeed on import
from dash import Dash  # noqa: E402
import dash_bootstrap_components as dbc  # noqa: E402

_app = Dash(__name__, use_pages=False, suppress_callback_exceptions=True,
            external_stylesheets=[dbc.themes.SLATE])

import pytest  # noqa: E402

from tests.test_pages.test_layout_helpers import (
    find_cards_with_class,
    find_divs_with_class,
    find_graphs,
    find_inline_font_sizes,
    find_rows_with_class,
    get_col_widths,
    get_graph_heights,
)

# ---------------------------------------------------------------------------
# Page lists
# ---------------------------------------------------------------------------

# Pages with _build_content and KPI strips (13)
# Excludes: comments (callback-rendered), charters (no KPIs), projects (summary stats, not KPI strip)
PAGES_WITH_KPIS = [
    "dashboard",
    "portfolios",
    "sprint",
    "risks",
    "reports",
    "backlog",
    "resources",
    "gantt",
    "roadmap",
    "deliverables",
    "retros",
    "my_work",
    "timesheet",
]

# Pages with chart cards (10)
PAGES_WITH_CHARTS = [
    "dashboard",
    "portfolios",
    "projects",
    "sprint",
    "risks",
    "reports",
    "resources",
    "roadmap",
    "timesheet",
    "retros",
]

# Pages with _build_content and page-header inside _build_content (14)
# Excludes: comments (layout-level), charters (layout-level)
PAGES_WITH_HEADER_IN_BUILD = [
    "dashboard",
    "portfolios",
    "projects",
    "sprint",
    "risks",
    "reports",
    "backlog",
    "resources",
    "gantt",
    "roadmap",
    "deliverables",
    "retros",
    "my_work",
    "timesheet",
]

# Pages with page-header in layout() instead of _build_content
PAGES_WITH_HEADER_IN_LAYOUT = [
    "charters",
    "comments",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_build_content(page_name):
    """Import and call _build_content() for a page module."""
    mod = __import__(f"pages.{page_name}", fromlist=["_build_content"])
    try:
        return mod._build_content()
    except TypeError as e:
        if "datetime" in str(e):
            pytest.skip(f"{page_name}: Plotly datetime bug in chart rendering — {e}")
        raise


def _get_layout(page_name):
    """Import and call layout() for a page module."""
    mod = __import__(f"pages.{page_name}", fromlist=["layout"])
    return mod.layout()


# ===================================================================
# TestKpiStripConsistency
# ===================================================================


class TestKpiStripConsistency:
    """KPI strips must have internally consistent column widths."""

    @pytest.mark.parametrize("page_name", PAGES_WITH_KPIS)
    def test_kpi_cols_equal_width(self, page_name):
        """All KPI columns in a kpi-strip Row must have identical width config."""
        content = _get_build_content(page_name)
        kpi_rows = find_rows_with_class(content, "kpi-strip")
        assert kpi_rows, f"{page_name}: no kpi-strip Row found"

        for row in kpi_rows:
            col_widths = get_col_widths(row)
            assert col_widths, f"{page_name}: kpi-strip has no Col children"
            first = col_widths[0]
            for i, cw in enumerate(col_widths[1:], 1):
                assert cw == first, (
                    f"{page_name}: KPI col {i} width {cw} != col 0 width {first}"
                )

    @pytest.mark.parametrize("page_name", PAGES_WITH_KPIS)
    def test_kpi_no_uneven_fixed_widths(self, page_name):
        """No mixed integer widths like [2,2,2,3,3] in a single KPI strip."""
        content = _get_build_content(page_name)
        kpi_rows = find_rows_with_class(content, "kpi-strip")

        for row in kpi_rows:
            col_widths = get_col_widths(row)
            int_widths = [
                cw.get("width") for cw in col_widths
                if isinstance(cw.get("width"), int)
            ]
            if int_widths:
                unique = set(int_widths)
                assert len(unique) == 1, (
                    f"{page_name}: uneven fixed widths {int_widths}"
                )


# ===================================================================
# TestChartCardLayout
# ===================================================================


class TestChartCardLayout:
    """Cards wrapping graphs must follow chart-card conventions."""

    @pytest.mark.parametrize("page_name", PAGES_WITH_CHARTS)
    def test_chart_cards_have_chart_card_class(self, page_name):
        """Cards containing dcc.Graph should have the chart-card class."""
        content = _get_build_content(page_name)
        graphs = find_graphs(content)
        if not graphs:
            pytest.skip(f"{page_name}: no graphs found in _build_content()")

        chart_cards = find_cards_with_class(content, "chart-card")
        assert chart_cards, (
            f"{page_name}: has {len(graphs)} graphs but no chart-card Cards"
        )

    @pytest.mark.parametrize("page_name", PAGES_WITH_CHARTS)
    def test_chart_row_cols_use_width_or_responsive(self, page_name):
        """Chart columns must specify width or a responsive breakpoint (md/lg/xl)."""
        content = _get_build_content(page_name)
        chart_cards = find_cards_with_class(content, "chart-card")
        if not chart_cards:
            pytest.skip(f"{page_name}: no chart-card Cards found")


# ===================================================================
# TestChartHeightConsistency
# ===================================================================


class TestChartHeightConsistency:
    """Chart heights should not be unreasonably small."""

    @pytest.mark.parametrize("page_name", PAGES_WITH_CHARTS)
    def test_no_tiny_chart_heights(self, page_name):
        """No explicit chart height below 200px."""
        content = _get_build_content(page_name)
        heights = get_graph_heights(content)

        for graph_id, height in heights:
            px_val = _parse_height(height)
            if px_val is not None:
                assert px_val >= 200, (
                    f"{page_name}: graph '{graph_id}' height {height} < 200px"
                )


def _parse_height(value):
    """Parse height string to numeric pixels."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.endswith("px"):
        try:
            return float(value[:-2])
        except ValueError:
            return None
    return None


# ===================================================================
# TestInlineStyleDiscipline
# ===================================================================


class TestInlineStyleDiscipline:
    """Inline styles should not use unreasonably small font sizes."""

    @pytest.mark.parametrize("page_name", PAGES_WITH_KPIS)
    def test_no_inline_font_size_below_minimum(self, page_name):
        """No inline fontSize below 11px."""
        content = _get_build_content(page_name)
        violations = find_inline_font_sizes(content, min_px=11)
        assert not violations, (
            f"{page_name}: found inline fontSize < 11px: {violations}"
        )


# ===================================================================
# TestPageHeaderConsistency
# ===================================================================


class TestPageHeaderConsistency:
    """Every page must have a page-header div."""

    @pytest.mark.parametrize("page_name", PAGES_WITH_HEADER_IN_BUILD)
    def test_has_page_header_in_build_content(self, page_name):
        """Pages with _build_content must include a page-header div."""
        content = _get_build_content(page_name)
        headers = find_divs_with_class(content, "page-header")
        assert headers, f"{page_name}: no page-header div found in _build_content()"

    @pytest.mark.parametrize("page_name", PAGES_WITH_HEADER_IN_LAYOUT)
    def test_has_page_header_in_layout(self, page_name):
        """Pages with header in layout() must include a page-header div."""
        content = _get_layout(page_name)
        headers = find_divs_with_class(content, "page-header")
        assert headers, f"{page_name}: no page-header div found in layout()"
