from textual.widgets import Footer

def get_footer() -> Footer:
  footer = Footer()
  footer.show_command_palette = False
  footer.can_focus = False
  footer.compact = True
  return footer