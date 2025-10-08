#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QListWidget, QSplitter, QPushButton,
    QTextEdit, QListWidgetItem
)


def apply_dark_palette(app: QApplication) -> None:
    """
    Aplica una paleta de colores oscura coherente con el sistema OPTIM.

    Args:
        app: Instancia de QApplication a la cual aplicar el tema
    """
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


def default_config_path() -> Path:
    """
    Obtiene la ruta por defecto del archivo de configuración.

    Returns:
        Path: Ruta al archivo configuracion_labs.json
    """
    return Path(__file__).resolve().parents[2] / "configuracion_labs.json"


class ConfigurarParametrosWindow(QMainWindow):
    """
    Ventana de visualización de parámetros de organización.

    Muestra las restricciones duras y blandas del motor de organización
    en modo solo lectura. Las restricciones están definidas en código
    para mantener consistencia y facilitar actualizaciones.
    """

    def __init__(self, cfg_path: Path = None):
        """
        Inicializa la ventana de parámetros.

        Args:
            cfg_path: Ruta opcional al archivo de configuración
        """
        super().__init__()
        self.setWindowTitle("Restricciones de Organización - OPTIM Labs")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)

        self.cfg_path = cfg_path or default_config_path()

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

        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        """
        Construye la interfaz de usuario de la ventana.

        Organiza los elementos en un layout vertical con splitter para
        separar restricciones duras de blandas, más información adicional.
        """
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
        panel_duras = self._create_restriction_panel(
            "Restricciones Duras (Obligatorias)",
            self.restricciones_duras,
            "Las restricciones duras son condiciones que NUNCA pueden violarse durante la organización."
        )
        splitter.addWidget(panel_duras)

        # Panel de restricciones blandas
        panel_blandas = self._create_restriction_panel(
            "Restricciones Blandas (Preferencias)",
            self.restricciones_blandas,
            "Las restricciones blandas son preferencias que el motor intentará satisfacer cuando sea posible."
        )
        splitter.addWidget(panel_blandas)

        # Panel de información adicional
        panel_info = self._create_info_panel()
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

    def _create_restriction_panel(self, titulo: str, restricciones: List[str], descripcion: str) -> QWidget:
        """
        Crea un panel para mostrar un tipo de restricciones.

        Args:
            titulo: Título del panel
            restricciones: Lista de restricciones a mostrar
            descripcion: Descripción explicativa del tipo de restricción

        Returns:
            QWidget: Panel configurado con las restricciones
        """
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

    def _create_info_panel(self) -> QWidget:
        """
        Crea el panel de información adicional del sistema.

        Returns:
            QWidget: Panel con información técnica y metadatos
        """
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

    def _load_data(self) -> None:
        """
        Carga datos del sistema.

        En esta implementación, los datos se cargan desde las constantes
        definidas en código, no desde el archivo JSON. Esto garantiza
        consistencia y facilita el mantenimiento.
        """
        # Los datos ya están cargados desde las constantes de clase
        # Este método se mantiene para consistencia con la interfaz base
        # y futuras extensiones que puedan requerir carga dinámica
        pass


def main():
    """
    Función principal para ejecutar la ventana de forma independiente.

    Configura la aplicación con tema oscuro y muestra la ventana principal.
    Útil para desarrollo y testing de la interfaz.
    """
    app = QApplication(sys.argv)
    apply_dark_palette(app)

    win = ConfigurarParametrosWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()