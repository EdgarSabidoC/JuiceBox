## Desinstalacion de `Juice Box`

---

### Desinstalacion manual

Para desinstalar manualmente el servicio de `Juice Box Engine` en tu servidor o computadora con `Linux (Debian/Ubuntu/Arch)` [ver el siguiente enlace](JuiceBoxService.MD).

### Desinstalacion automatica (script)

Si se desea utilizar alguno de los scripts de desinstalacion para automatizar el proceso, estos se encuentran disponibles en el directorio `/opt/juicebox/Uninstall`.

**NOTA:** Estos scripts desinstalan automaticamente `Juice Box Engine`, `Juice Box Manager TUI` y `Juice Box WebClient`.

#### Para distros basadas en Ubuntu/Debian con shell bash:

```bash
chmod +x uninstall_juicebox.sh
./uninstall_juicebox.sh
```

#### Para distros basadas en Arch con shell fish:

```bash
chmod +x uninstall_juicebox.fish
./uninstall_juicebox.fish
```

---

## Desinstalacion de la Manager TUI de `Juice Box`

Para desinstalar la TUI como ejecutable [ver el siguiente enlace](TUI.MD).

---

## Desinstalacion del WebClient de `Juice Box`

Para desinstalar el WebClient como servicio [ver el siguiente enlace](WebClient.MD).