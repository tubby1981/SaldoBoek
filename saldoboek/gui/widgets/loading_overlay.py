"""LoadingOverlay - Overlay widget voor laden indicator."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout


class LoadingOverlay(QFrame):
    """
    Overlay widget voor tonen van laden status.

    Toont een semi-transparante overlay met een indicatie dat er
    laden gaande is. Handig voor lange operaties.
    """

    def __init__(self, parent=None):
        """
        Initialiseer LoadingOverlay.

        Args:
            parent: Parent widget (should be the widget to overlay)
        """
        super().__init__(parent)
        self.setObjectName("loading_overlay")
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        """Bouwt de UI op."""
        # Overlay styling
        self.setStyleSheet(
            "LoadingOverlay { background-color: rgba(128, 128, 128, 180); }"
        )
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        content_frame = QFrame()
        content_frame.setObjectName("loading_content")
        content_frame.setStyleSheet(
            "background-color: white; border-radius: 10px; padding: 20px;"
        )
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(15)
        content_layout.setAlignment(Qt.AlignCenter)

        # Loading tekst
        self._label = QLabel("Laden...")
        self._label.setObjectName("loading_label")
        self._label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self._label)

        # Progress bar (indeterminate)
        self._progress = QProgressBar()
        self._progress.setObjectName("loading_progress")
        self._progress.setRange(0, 0)  # Indeterminate mode
        self._progress.setMaximumWidth(200)
        content_layout.addWidget(self._progress)

        layout.addWidget(content_frame)

    def set_message(self, message):
        """
        Stel de laadtekst in.

        Args:
            message: Tekst om te tonen
        """
        self._label.setText(message)

    def show_overlay(self, message="Laden..."):
        """
        Toon de overlay met een bericht.

        Args:
            message: Optioneel bericht om te tonen
        """
        self.set_message(message)
        self.show()

    def hide_overlay(self):
        """Verberg de overlay."""
        self.hide()

    def is_visible(self):
        """
        Geef aan of de overlay zichtbaar is.

        Returns:
            bool: True als zichtbaar
        """
        return super().isVisible()
