# -*- coding: utf-8 -*-
"""
dessin_viewer.py
================

Interface graphique Qt 

Ce module joue le même rôle que ``image_viewer.py`` dans le TP2 :
il gère la fenêtre et les interactions utilisateur, tandis que les calculs
sur les images sont dans ``dessin_process.py``.
"""

from pathlib import Path

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from dessin_process import paint_disk, paint_segment, save_bitmap


# =====================================================================
# CANEVAS DE DESSIN
# =====================================================================

class DrawingCanvas(QtWidgets.QWidget):
    """
    Widget Qt contenant le bitmap et gérant les événements souris.
    self.array= bitmap
    """

    changed = QtCore.pyqtSignal()

    def __init__(self, size=280, brush=7, parent=None):
        super().__init__(parent)

        self.size = int(size)
        self.brush = float(brush)

        if self.size <= 0:
            raise ValueError("size doit être strictement positif.")

        if self.brush <= 0:
            raise ValueError("brush doit être strictement positif.")

        self.array = np.zeros(
            (self.size, self.size),
            dtype=float,
        )

        self.drawing = False
        self.last_point = None

        self.setFixedSize(self.size, self.size)
        self.setCursor(QtCore.Qt.CrossCursor)


    def clear(self):
        """Efface complètement le canevas."""
        self.array[:] = 0.0
        self.last_point = None

        self.update()
        self.changed.emit()


    def mousePressEvent(self, event):
        """Débute un trait avec le bouton gauche."""
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = True
            self.last_point = None

            self._paint_at(
                event.pos().x(),
                event.pos().y(),
            )


    def mouseMoveEvent(self, event):
        """Prolonge le trait lorsque le bouton gauche est maintenu."""
        if self.drawing:
            self._paint_at(
                event.pos().x(),
                event.pos().y(),
            )


    def mouseReleaseEvent(self, event):
        """Termine le trait."""
        if event.button() == QtCore.Qt.LeftButton:
            self.drawing = False
            self.last_point = None


    def _paint_at(self, x, y):
        """
        Ajoute le point courant au dessin.

        Les calculs sont dans ``dessin_process.py``.
        """
        point = (float(x), float(y))

        if self.last_point is None:
            ...

        else:
            ...

        self.last_point = ...

        self.update()
        self.changed.emit()


    def paintEvent(self, event):
        """Affiche le tableau NumPy dans le widget Qt."""
        gray = np.ascontiguousarray(
            np.uint8(
                np.clip(self.array, 0.0, 1.0) * 255
            )
        )

        qimage = QtGui.QImage(
            gray.data,
            gray.shape[1],
            gray.shape[0],
            gray.strides[0],
            QtGui.QImage.Format_Grayscale8,
        )

        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.black)
        painter.drawImage(self.rect(), qimage)
        painter.end()


# =====================================================================
# FENÊTRE PRINCIPALE
# =====================================================================

class Draw(QtWidgets.QMainWindow):
    """
    Fenêtre principale du dessin QuickDraw.

    Trois boutons sont disponibles :

    - Effacer
    - Classifier
    - Sauver
    """

    def __init__(
        self,
        size=280,
        brush=7,
        classify_callback=None,
        title="Dessin",
    ):
        super().__init__()

        self.classify_callback = classify_callback

        self.setWindowTitle(title)

        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)

        # Canevas
        self.canvas = DrawingCanvas(
            size=size,
            brush=brush,
            parent=central,
        )

        layout.addWidget(
            self.canvas,
            alignment=QtCore.Qt.AlignCenter,
        )

        # Boutons
        buttons = QtWidgets.QHBoxLayout()

        self.clear_button = QtWidgets.QPushButton("Effacer")
        self.classify_button = QtWidgets.QPushButton("Classifier")
        self.save_button = QtWidgets.QPushButton("Sauver")

        buttons.addWidget(self.clear_button)
        buttons.addWidget(self.classify_button)
        buttons.addWidget(self.save_button)

        layout.addLayout(buttons)

        # Zone de résultat
        self.result_label = QtWidgets.QLabel(
            "Dessinez puis cliquez sur « Classifier »."
        )

        self.result_label.setAlignment(
            QtCore.Qt.AlignCenter
        )

        self.result_label.setWordWrap(True)

        layout.addWidget(self.result_label)

        self.setCentralWidget(central)

        # Connexion signaux -> méthodes
        self.clear_button.clicked.connect(self.clear)
        self.classify_button.clicked.connect(self.classify)
        self.save_button.clicked.connect(self.save)

        self.canvas.changed.connect(
            self._drawing_changed
        )

        self.adjustSize()


    @property
    def array(self):
        """
        Donne accès au bitmap via ``pad.array``.
        """
        return self.canvas.array


    def _drawing_changed(self):
        """
        Signale qu'un résultat affiché n'est plus valable après modification.
        """
        if self.result_label.text().startswith("Prédiction"):
            self.result_label.setText(
                "Dessin modifié — recliquez sur « Classifier »."
            )


    def clear(self):
        """Action associée au bouton Effacer."""
        self.canvas.clear()

        self.result_label.setText(
            "Canevas effacé."
        )


    def classify(self):
        """Action associée au bouton Classifier."""
        if self.classify_callback is None:
            self.result_label.setText(
                "Aucune fonction de classification n'a été fournie."
            )
            return

        if not np.any(self.array > 0):
            self.result_label.setText(
                "Le canevas est vide."
            )
            return

        try:
            result = self.classify_callback(
                self.array.copy()
            )

        except Exception as exc:
            self.result_label.setText(
                f"Erreur de classification : {exc}"
            )
            return

        # La callback peut renvoyer un dictionnaire structuré.
        if isinstance(result, dict):
            label = result.get("label", "?")
            probability = result.get(
                "probability",
                None,
            )
            class1_name = result.get(
                "class1_name",
                "classe 1",
            )

            if probability is None:
                text = f"Prédiction : {label}"

            else:
                text = (
                    f"Prédiction : {label}"
                    f" — P({class1_name}) = {probability:.3f}"
                )

        else:
            text = f"Prédiction : {result}"

        self.result_label.setText(text)


    def save(self):
        """Action associée au bouton Sauver."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Sauver le dessin",
            "mon_dessin.png",
            "Images PNG (*.png);;Toutes les images (*)",
        )

        if not filename:
            return

        if Path(filename).suffix == "":
            filename += ".png"

        try:
            save_bitmap(
                self.array,
                filename,
            )

        except Exception as exc:
            self.result_label.setText(
                f"Erreur lors de la sauvegarde : {exc}"
            )
            return

        self.result_label.setText(
            f"Dessin sauvé : {Path(filename).name}"
        )


# =====================================================================
# OUTILS DE LANCEMENT
# =====================================================================

def get_qapp():
    """
    Renvoie l'application Qt existante ou en crée une.

    Dans Jupyter, exécuter d'abord :

        %gui qt5

    afin que la boucle événementielle Qt soit intégrée à IPython.
    """
    app = QtWidgets.QApplication.instance()

    if app is None:
        app = QtWidgets.QApplication([])

    return app


def show_draw(
    size=280,
    brush=7,
    classify_callback=None,
    title="QuickDraw",
):
    """
    Crée, affiche et renvoie une fenêtre ``Draw``.

        %gui qt5
        pad = show_draw(...)
    """
    get_qapp()

    window = Draw(
        size=size,
        brush=brush,
        classify_callback=classify_callback,
        title=title,
    )

    window.show()
    window.raise_()
    window.activateWindow()

    return window
