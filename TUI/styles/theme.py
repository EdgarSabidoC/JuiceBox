from textual.theme import Theme

# Dark themes

juice_box_theme = Theme(
    name="juice-box",
    primary="#FF8C00",  # naranja vibrante
    secondary="#1eff00",  # verde lima
    accent="#FFD700",  # amarillo dorado
    foreground="#FFFFFF",  # blanco puro para texto
    background="#0B0A0A",  # casi negro profundo
    success="#00FF00",  # verde brillante
    warning="#FFA500",  # naranja para alertas
    error="#FF3333",  # rojo intenso
    surface="#1A1A1A",  # gris muy oscuro como “cartón”
    panel="#0D0D0D",  # paneles casi negros
    dark=True,
    variables={
        "border": "double #FF8C00",  # marco naranja
        "link-color": "#FFD700",  # enlaces verdes
        "link-color-hover": "#32CD32",  # hover amarillo
        "link-background-hover": "#FFD700 15%",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#32CD32",
        "footer-description-foreground": "#FFFFFF",
        "input-selection-background": "#FFD700 35%",  # selección en amarillo suave
        "button-focus-text-style": "bold",
    },
)

dark_blueberry_juice_theme = Theme(
    name="dark-blueberry-juice-theme",
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
        "link-background-hover": "#1C8196 15%",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#2de2e6",
        "footer-description-foreground": "#3984E6",
        "input-selection-background": "#81a1c1 35%",
        "button-focus-text-style": "bold",
    },
)

dark_lime_juice_theme = Theme(
    name="dark-lime-juice-theme",
    primary="#2ECC71",  # verde esmeralda vibrante
    secondary="#27AE60",  # verde bosque medio
    accent="#21F10E",  # verde azulado oscuro
    foreground="#2ECC71",  # texto principal en verde esmeralda
    background="#061006",  # negro con matiz verde muy oscuro
    success="#1EFF00",  # verde neón para éxito
    warning="#F9C80E",  # ámbar para advertencias
    error="#E74C3C",  # rojo ladrillo para errores
    surface="#0A1C12",  # verde oscuro suave para tarjetas
    panel="#061006",  # mismo que el fondo para paneles
    dark=True,
    variables={
        "border": "double #27AE60",  # borde en verde bosque
        "link-color": "#1ABC9C",  # enlaces en turquesa claro
        "link-color-hover": "#16A085",  # hover en verde azulado
        "link-background-hover": "#1ABC9C 15%",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#21F10E",  # gris suave para pie de página
        "footer-description-foreground": "#16A085",
        "input-selection-background": "#27AE60 35%",  # selección semitransparente
        "button-focus-text-style": "bold",
    },
)

synthwave_80s_theme = Theme(
    name="synthwave-80s",
    primary="#FF43A4",  # neón rosa vibrante
    secondary="#04D9FF",  # cian eléctrico
    accent="#9D00FF",  # púrpura neón
    foreground="gold",  # "#F8F8F2",  # blanco suave para texto
    background="#100018",  # púrpura casi negro de noche
    success="#00FF9F",  # verde neón para éxito
    warning="#FF9F00",  # naranja neón para atención
    error="#FF005C",  # rojo neón para errores
    surface="#2A012F",  # púrpura oscuro para superficies
    panel="#25002E",  # paneles con tono aún más oscuro
    dark=True,
    variables={
        "border": "double #FF43A4",  # marco neón rosa
        "link-color": "#04D9FF",  # enlaces cian eléctrico
        "link-color-hover": "#FF43A4",  # hover en neón rosa
        "link-background-hover": "#04D9FF 20%",  # fondo cian semitransparente
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#1EFF00",  # pie de página en blanco suave
        "footer-description-foreground": "#04D9FF",
        "input-selection-background": "#9D00FF 35%",  # selección púrpura semitransparente
        "button-focus-text-style": "bold",
    },
)

# Light themes

hacker_light_blue_theme = Theme(
    name="hacker-light-blue",
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
        "link-color": "#1C8196",
        "link-color-hover": "#F706CF",
        "link-background-hover": "#1C8196 15%",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
        "button-focus-text-style": "bold",
    },
)

hacker_light_green_theme = Theme(
    name="hacker-light-green",
    primary="#2ECC71",  # verde esmeralda
    secondary="#58D68D",  # verde menta
    accent="#27AE60",  # verde bosque
    foreground="#2ECC71",  # texto principal en verde
    background="#3B5D42",  # verde oscuro suave como base
    success="#1EFF00",  # verde neón para éxito
    warning="#F9C80E",  # amarillo ámbar
    error="#FD1D53",  # rojo intenso
    surface="#3B5D42",  # mima superficie al fondo
    panel="#435E4A",  # panel ligeramente más claro
    dark=False,
    variables={
        "border": "double #27AE60",  # marco en verde bosque
        "link-color": "#58D68D",  # enlaces en verde menta
        "link-color-hover": "#82E0AA",  # hover en verde pálido
        "link-background-hover": "#58D68D 15%",
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#95A5A6",  # pie de página gris suave
        "input-selection-background": "#82E0AA 35%",  # selección semitransparente
        "button-focus-text-style": "bold",
    },
)
