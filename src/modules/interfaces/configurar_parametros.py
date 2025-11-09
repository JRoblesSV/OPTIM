
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
    QTextEdit, QListWidgetItem
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
            screen_geometry = screen.availableGeometry()  # Considera la barra de tareas

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
    base = QColor(30, 30, 30)
    alt_base = QColor(45, 45, 45)
    text = QColor(220, 220, 220)
    disabled_text = QColor(127, 127, 127)
    button = QColor(53, 53, 53)
    highlight = QColor(42, 130, 218)

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
            "Respetar los días no disponibles de las aulas",
            "Paridad de grupos: todos pares; si el total es impar, solo un grupo impar"
        ]

        self.restricciones_blandas = [
            "Evitar que un alumno tenga dos asignaturas en la misma franja horaria",
            "Mantener tamaños de grupos equilibrados",
            "Favorecer el uso del aula preferente de la asignatura cuando sea posible",
            "Balancear la carga de grupos por profesor"
        ]

        self.setup_ui()

        window_width = 800
        window_height = 700
        center_window_on_screen(self, window_width, window_height)

    def setup_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Título principal
        titulo = QLabel("Parámetros del Motor de Organización")
        titulo.setStyleSheet("""
            QLabel {
                color: rgb(42,130,218);
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border: 2px solid rgb(42,130,218);
                border-radius: 8px;
                background-color: rgb(35,35,35);
            }
        """)
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

        # Panel de información adicional
        panel_info = self.create_info_panel()
        splitter.addWidget(panel_info)

        # Configurar proporciones del splitter
        splitter.setSizes([250, 250, 150])
        layout.addWidget(splitter)

        # Botón de cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: rgb(53,53,53);
                color: white;
                border: 1px solid rgb(127,127,127);
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(66,66,66);
                border-color: rgb(42,130,218);
            }
        """)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

        self.setCentralWidget(central)

    def create_restriction_panel(self, titulo: str, restricciones: List[str], descripcion: str) -> QWidget:
        """Crea un panel para mostrar un tipo de restricciones"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Título del panel
        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: rgb(42,130,218);
                padding: 5px;
            }
        """)
        layout.addWidget(label_titulo)

        # Descripción
        label_desc = QLabel(descripcion)
        label_desc.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: rgb(180,180,180);
                padding: 3px;
                font-style: italic;
            }
        """)
        label_desc.setWordWrap(True)
        layout.addWidget(label_desc)

        # Lista de restricciones
        lista = QListWidget()
        lista.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        lista.setStyleSheet("""
            QListWidget {
                background-color: rgb(42,42,42);
                border: 1px solid rgb(127,127,127);
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgb(60,60,60);
                color: rgb(220,220,220);
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)

        # Agregar restricciones a la lista
        for i, restriccion in enumerate(restricciones, 1):
            item = QListWidgetItem(f"{i}. {restriccion}")
            item.setFont(QFont("Segoe UI", 10))
            lista.addItem(item)

        layout.addWidget(lista)
        return panel

    def create_info_panel(self) -> QWidget:
        """Crea el panel de información adicional del sistema"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Título
        label_titulo = QLabel("Información del Sistema")
        label_titulo.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: rgb(42,130,218);
                padding: 5px;
            }
        """)
        layout.addWidget(label_titulo)

        # Área de texto para información
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: rgb(35,35,35);
                color: rgb(200,200,200);
                border: 1px solid rgb(127,127,127);
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)

        # Contenido informativo
        info_content = f"""Información Técnica:
- Versión de parámetros: 1.0
- Total restricciones duras: {len(self.restricciones_duras)}
- Total restricciones blandas: {len(self.restricciones_blandas)}
- Generado automáticamente: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Nota: Estas restricciones están definidas en el código fuente del sistema
para garantizar consistencia entre ejecuciones y facilitar el mantenimiento."""

        info_text.setPlainText(info_content)
        layout.addWidget(info_text)

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