from textual.widgets import Header


def get_header() -> Header:
  header = Header()
  header._show_clock = True
  header.can_focus = False
  header.icon = "🍊"
  return header