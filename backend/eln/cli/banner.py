"""
ASCII art banner for the CoSci CLI.
"""

from rich.console import Console
from rich.text import Text

# The mascot is a little Erlenmeyer flask with bubbles and a DNA strand,
# placed to the left of the CoSci wordmark.

BANNER = r"""
        _  ○
       ( )  ○        ██████╗  ██████╗ ███████╗ ██████╗██╗
      ( ○ )          ██╔════╝██╔═══██╗██╔════╝██╔════╝██║
       )○(           ██║     ██║   ██║███████╗██║     ██║
    /```````\        ██║     ██║   ██║╚════██║██║     ██║
   /  ~ ~ ~  \       ██████╗╚██████╔╝███████║╚██████╗██║
  /  ~ ~ ~ ~  \      ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝╚═╝
 /   ~ ~ ~ ~   \
 ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾    AI Co-Scientist for Biology
  ╱╲ ╱╲ ╱╲ ╱╲       Post-run ELN assistant  ·  v0.1.0
"""

TAGLINE_COMMANDS = """\
  [dim]--chat[/dim]     Interactive CLI chat        [dim]--search[/dim]  Search knowledge base
  [dim]--ui[/dim]       Launch Streamlit UI         [dim]--ingest[/dim]  Ingest documents
  [dim]--export[/dim]   Export run bundle           [dim]--validate[/dim] Audit trail check
"""


def print_banner(con: Console | None = None) -> None:
    """Print the CoSci ASCII banner in light blue."""
    c = con or Console()

    banner_text = Text(BANNER)
    banner_text.stylize("bright_cyan")

    c.print(banner_text, highlight=False)
    c.print(TAGLINE_COMMANDS, highlight=False)
