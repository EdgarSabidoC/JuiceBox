from pathlib import PurePath
from textual.widgets import MarkdownViewer, Markdown
import webbrowser


class LinkableMarkdownViewer(MarkdownViewer):
    """
    Visor de Markdown personalizado que extiende `MarkdownViewer` para
    manejar enlaces externos de manera diferente.

    Características:
    - Si el enlace es externo (comienza con "http://" o "https://"), se abre
      automáticamente en el navegador web predeterminado del sistema.
    - Si el enlace es interno (anclas dentro del documento) o una ruta local,
      se delega el comportamiento al método original de `MarkdownViewer`.

    Esto evita que el visor intente interpretar URLs externas como rutas de
    archivos locales, lo que normalmente provocaría errores de tipo
    `FileNotFoundError`.
    """

    async def go(self, location: str | PurePath) -> None:
        """
        Navega a la ubicación indicada.

        Comportamiento:
        - Si `location` es una URL externa (http/https), se abre en el navegador
          mediante `webbrowser.open()`.
        - En cualquier otro caso, se llama al método `go()` de la superclase
          para mantener el comportamiento estándar de navegación en MarkdownViewer.

        Args:
            location : str | PurePath
                Puede ser una URL externa, un ancla interna o una ruta local.
        """
        href = location if isinstance(location, str) else str(location)
        if href.startswith("http://") or href.startswith("https://"):
            webbrowser.open(href)  # abre en el navegador
            return
        await super().go(location)
