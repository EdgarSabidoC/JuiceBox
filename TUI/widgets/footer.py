from textual.widgets import Footer


def get_footer() -> Footer:
    footer = Footer()
    footer.show_command_palette = True
    footer.can_focus = False
    footer.compact = True
    footer.styles.content_align = ("center", "middle")
    footer.styles.align = ("center", "middle")
    return footer
