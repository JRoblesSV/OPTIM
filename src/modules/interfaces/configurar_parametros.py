
"""
Configurar Parámetros - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
from pathlib import Path
from typing import List
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QFont, QCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QListWidget, QSplitter, QPushButton,
    QTextEdit, QListWidgetItem, QGroupBox
)


def center_window_on_screen(window, width, height) -> None:
    """Centrar ventana en la pantalla donde está el cursor"""
    try:
        # Obtener la pantalla donde está el cursor
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)

        if not screen:
            screen = QApplication.primaryScreen()

        # Obtener información de la pantalla
        if screen:
            screen_geometry = screen.availableGeometry()

            # Calcular posición centrada usando las dimensiones proporcionadas
            center_x = (screen_geometry.width() - width) // 2 + screen_geometry.x()
            center_y = (screen_geometry.height() - height) // 2 + screen_geometry.y()

            # Asegurar que la ventana no se salga de la pantalla
            final_x = max(screen_geometry.x(), min(center_x, screen_geometry.x() + screen_geometry.width() - width))
            final_y = max(screen_geometry.y(), min(center_y, screen_geometry.y() + screen_geometry.height() - height))

            # Establecer geometría completa de una vez (posición + tamaño)
            window.setGeometry(final_x, final_y, width, height)

        else:
            # Fallback si no se puede obtener la pantalla
            window.setGeometry(100, 100, width, height)

    except Exception as e:
        # Fallback en caso de error
        window.setGeometry(100, 100, width, height)


def apply_dark_palette(app: QApplication) -> None:
    """Aplica una paleta de colores oscura"""
    app.setStyle("Fusion")
    palette = QPalette()

    # Definición de colores del tema oscuro OPTIM
    base = QColor(25, 25, 25)
    alt_base = QColor(35, 35, 35)
    text = QColor(210, 210, 210)
    disabled_text = QColor(120, 120, 120)
    button = QColor(45, 45, 45)
    highlight = QColor(0, 120, 215)

    # Aplicación de colores a la paleta
    palette.setColor(QPalette.ColorRole.Window, base)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, alt_base)
    palette.setColor(QPalette.ColorRole.AlternateBase, base)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    # Estados deshabilitados
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)

    app.setPalette(palette)


# ========= Ventana Principal =========
class ConfigurarParametrosWindow(QMainWindow):

    def __init__(self, cfg_path: Path = None):
        super().__init__()
        self.setWindowTitle("Restricciones de Organización - OPTIM")
        self.setMinimumSize(700, 600)
        #self.resize(800, 700)

        # Definición de restricciones en código fuente
        self.restricciones_duras = [
            "Un profesor no puede estar en dos franjas horarias a la vez",
            "Un aula no puede estar asignada a dos grupos en la misma franja horaria",
            "No superar la capacidad máxima del aula",
            "Respetar franjas no disponibles de los profesores",
            "Respetar los días no disponibles de los profesores",
            "Respetar los días no disponibles de las aulas"
        ]

        self.restricciones_blandas = [
            "Paridad de grupos: intentar que todos los grupos sean pares"
            "Mantener tamaños de grupos equilibrados",
            "Favorecer el uso del aula preferente de la asignatura cuando sea posible",
            "Balancear la carga de grupos por profesor"
        ]

        self.setup_ui()

        window_width = 800
        window_height = 600
        center_window_on_screen(self, window_width, window_height)

    def setup_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Título principal
        titulo = QLabel("PARÁMETROS DEL MOTOR DE ORGANIZACIÓN")
        titulo.setStyleSheet("""
            QLabel {
                color: rgb(100,180,255);
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                background-color: transparent;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Splitter principal para organizar secciones
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Panel de restricciones duras
        panel_duras = self.create_restriction_panel(
            "Restricciones Duras (Obligatorias)",
            self.restricciones_duras,
            "Las restricciones duras son condiciones que NUNCA pueden violarse durante la organización."
        )
        splitter.addWidget(panel_duras)

        # Panel de restricciones blandas
        panel_blandas = self.create_restriction_panel(
            "Restricciones Blandas (Preferencias)",
            self.restricciones_blandas,
            "Las restricciones blandas son preferencias que el motor intentará satisfacer cuando sea posible."
        )
        splitter.addWidget(panel_blandas)

        # Configurar proporciones del splitter
        splitter.setSizes([250, 250, 150])
        layout.addWidget(splitter)

        # Botón de cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: rgb(50,50,50);
                color: rgb(220,220,220);
                border: 1px solid rgb(70,70,70);
                border-radius: 5px;
                padding: 10px 25px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(60,60,60);
                border-color: rgb(100,180,255);
            }
            QPushButton:pressed {
                background-color: rgb(70,70,70);
            }
        """)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

        self.setCentralWidget(central)

    def create_restriction_panel(self, titulo: str, restricciones: List[str], descripcion: str) -> QGroupBox:
        """Crea un panel para mostrar un tipo de restricciones"""
        from PyQt6.QtWidgets import QGroupBox

        panel = QGroupBox(titulo)
        panel.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                border: 2px solid #4a4a4a;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)

        # Descripción
        label_desc = QLabel(descripcion)
        label_desc.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: rgb(200,200,200);
                padding: 5px 8px;
                font-style: italic;
                background-color: transparent;
            }
        """)
        label_desc.setWordWrap(True)
        layout.addWidget(label_desc)

        # Lista de restricciones
        lista = QListWidget()
        lista.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        lista.setStyleSheet("""
            QListWidget {
                background-color: rgb(43,43,43);
                border: 1px solid rgb(70,70,70);
                border-radius: 4px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 3px 0px;
                color: rgb(220,220,220);
                background-color: rgb(50,50,50);
                border-radius: 4px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: rgb(60,60,60);
                border-radius: 4px;
            }
        """)

        # Agregar restricciones a la lista
        for i, restriccion in enumerate(restricciones, 1):
            item = QListWidgetItem(f"{i}. {restriccion}")
            item.setFont(QFont("Segoe UI", 10))
            lista.addItem(item)

        layout.addWidget(lista)
        panel.setLayout(layout)
        return panel


# ========= main =========
def main():
    app = QApplication(sys.argv)
    apply_dark_palette(app)

    win = ConfigurarParametrosWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()