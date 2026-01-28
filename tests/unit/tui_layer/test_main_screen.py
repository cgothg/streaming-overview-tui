import pytest
from textual.app import App
from textual.app import ComposeResult
from textual.widgets import Input

from streaming_overview_tui.tui_layer.main_screen import MainScreen
from streaming_overview_tui.tui_layer.widgets import DetailPanel
from streaming_overview_tui.tui_layer.widgets import ResultsList


class MainScreenApp(App):
    """Test app for MainScreen."""

    def compose(self) -> ComposeResult:
        yield MainScreen()


class TestMainScreen:
    @pytest.mark.asyncio
    async def test_has_search_input(self):
        async with MainScreenApp().run_test() as pilot:
            inputs = pilot.app.query(Input)
            assert len(inputs) >= 1

    @pytest.mark.asyncio
    async def test_has_results_list(self):
        async with MainScreenApp().run_test() as pilot:
            results_list = pilot.app.query(ResultsList)
            assert len(results_list) == 1

    @pytest.mark.asyncio
    async def test_has_detail_panel(self):
        async with MainScreenApp().run_test() as pilot:
            detail_panel = pilot.app.query(DetailPanel)
            assert len(detail_panel) == 1

    @pytest.mark.asyncio
    async def test_shows_placeholder_initially(self):
        async with MainScreenApp().run_test() as pilot:
            results_list = pilot.app.query_one(ResultsList)
            rendered = results_list.render_str()
            assert "Start typing" in rendered or "search" in rendered.lower()
