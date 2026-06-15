"""Textual TUI skeleton.

Target layout:
- left: categories and feeds
- center: item list
- right: item preview
"""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from feedcopilot.core.config import load_config
from feedcopilot.core.i18n import translate


class FeedCopilotTUI(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    #left {
        width: 25%;
        border: solid $accent;
    }
    #middle {
        width: 35%;
        border: solid $accent;
    }
    #right {
        width: 40%;
        border: solid $accent;
    }
    """

    def compose(self) -> ComposeResult:
        language = load_config().app.language
        yield Header()
        yield Static(translate("tui_left", language), id="left")
        yield Static(translate("tui_middle", language), id="middle")
        yield Static(translate("tui_right", language), id="right")
        yield Footer()
