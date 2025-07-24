from textual.theme import Theme

hacker_dark_theme = Theme(
    name="hacker-dark",
    primary="#19E6F3",
    secondary="#20ADB6",
    accent="#ae08f0",
    foreground="#19E6F3",
    background="#020610",
    success="#1EFF00",
    warning="#F9C80E",
    error="#FD1D53",
    surface="#0C1C28",
    panel="#020610",
    dark=True,
    variables={
        "border": "double #14CAF4",
        "link-color": "#1C8196",
        "link-color-hover": "#2de2e6",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)

hacker_light_theme = Theme(
    name="hacker-light",
    primary="#19E6F3",
    secondary="#81A1C1",
    accent="#B48EAD",
    foreground="#19E6F3",
    background="#3B4252",
    success="#1EFF00",
    warning="#F9C80E",
    error="#FD1D53",
    surface="#3B4252",
    panel="#434C5E",
    dark=False,
    variables={
        "border": "double #14CAF4",
        "link-color-hover": "#F706CF",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)
