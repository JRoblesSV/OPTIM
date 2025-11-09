
"""
Configurar Horarios - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)


Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QFrame, QMessageBox, QDialog, QDialogButtonBox,
    QCheckBox, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


def center_window_on_screen(window, width, height) -> None:
    """Centra la ventana en la pantalla"""
    try:
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            center_x = (screen_geometry.width() - width) // 2 + screen_geometry.x()
            center_y = (screen_geometry.height() - height) // 2 + screen_geometry.y()
            final_x = max(screen_geometry.x(), min(center_x, screen_geometry.x() + screen_geometry.width() - width))
            final_y = max(screen_geometry.y(), min(center_y, screen_geometry.y() + screen_geometry.height() - height))
            window.setGeometry(final_x, final_y, width, height)
        else:
            window.setGeometry(100, 100, width, height)
    except Exception:
        window.setGeometry(100, 100, width, height)


def dir_downloads() -> str:
    """Obtener ruta del directorio de Descargas del usuario"""
    home = Path.home()
    for name in ("Descargas", "Downloads"):
        p = home / name
        if p.exists() and p.is_dir():
            return str(p)
    return str(home)


# ========= Diálogo/Ventana Gestión Franja Horaria =========
class GestionAsignaturaDialog(QDialog):
    """Dialog para editar grupos de una franja horaria"""

    # ========= INICIALIZACIÓN =========
    def __init__(self, dia, horario, grupos_disponibles, grupos_actuales=None, letras_actuales=None, parent=None):
        super().__init__(parent)
        self.dia = dia
        self.horario = horario
        self.grupos_disponibles = grupos_disponibles
        self.grupos_actuales = grupos_actuales or []
        self.letras_actuales = letras_actuales or []  # agregado nuevo para las letras

        self.setWindowTitle(f"Configurar {dia} - {horario}")
        self.setModal(True)
        center_window_on_screen(self, 600, 400)

        self.setup_ui()
        self.apply_dark_theme()

    # ========= CONFIGURACIÓN UI =========
    def setup_ui(self) -> None:
        """Configurar interfaz del diálogo de edición de grupos"""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel(f"📚 {self.dia} - {self.horario}")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Layout horizontal para los dos grids
        grids_layout = QHBoxLayout()

        # ==================== GRID IZQUIERDO - GRUPOS ====================
        grupos_group = QGroupBox("Grupos que tendrán clase:")
        grupos_layout = QVBoxLayout()

        self.check_grupos = {}

        if not self.grupos_disponibles:
            info_label = QLabel("⚠️ No hay grupos configurados para esta asignatura")
            info_label.setStyleSheet("color: #ffaa00;")
            grupos_layout.addWidget(info_label)
        else:
            if isinstance(self.grupos_disponibles, dict):
                for codigo, nombre in sorted(self.grupos_disponibles.items()):
                    texto_check = f"{codigo} - {nombre}"
                    check = QCheckBox(texto_check)
                    if codigo in self.grupos_actuales:
                        check.setChecked(True)
                    self.check_grupos[codigo] = check
                    grupos_layout.addWidget(check)
            else:
                # Retrocompatibilidad
                for grupo in sorted(self.grupos_disponibles):
                    check = QCheckBox(grupo)
                    if grupo in self.grupos_actuales:
                        check.setChecked(True)
                    self.check_grupos[grupo] = check
                    grupos_layout.addWidget(check)

        # Botones de acción rápida para grupos
        if self.grupos_disponibles:
            botones_grupos_layout = QHBoxLayout()
            btn_todos_grupos = QPushButton("Todos")
            btn_todos_grupos.clicked.connect(self.seleccionar_todos)
            botones_grupos_layout.addWidget(btn_todos_grupos)

            btn_ninguno_grupos = QPushButton("Ninguno")
            btn_ninguno_grupos.clicked.connect(self.seleccionar_ninguno)
            botones_grupos_layout.addWidget(btn_ninguno_grupos)

            grupos_layout.addLayout(botones_grupos_layout)

        grupos_group.setLayout(grupos_layout)
        grids_layout.addWidget(grupos_group)

        # ==================== GRID DERECHO - LETRAS (2 COLUMNAS) ====================
        letras_group = QGroupBox("Seleccionar Letras:")
        letras_main_layout = QVBoxLayout()

        # Grid de letras en 2 columnas
        letras_grid = QGridLayout()
        letras_grid.setSpacing(5)

        self.check_letras = {}
        letras_disponibles = ['A', 'B', 'C', 'D', 'E', 'F']

        # Organizar en 2 columnas: A, B, C a la izquierda y D, E, F a la derecha
        for i, letra in enumerate(letras_disponibles):
            check = QCheckBox(letra)
            if letra in self.letras_actuales:  # marca las letras actuales
                check.setChecked(True)
            self.check_letras[letra] = check

            fila = i % 3
            columna = i // 3

            letras_grid.addWidget(check, fila, columna)

        letras_main_layout.addLayout(letras_grid)

        # Botones de acción rápida para letras
        botones_letras_layout = QHBoxLayout()
        btn_todas_letras = QPushButton("Todas")
        btn_todas_letras.clicked.connect(self.seleccionar_todas_letras)
        botones_letras_layout.addWidget(btn_todas_letras)

        btn_ninguna_letra = QPushButton("Ninguna")
        btn_ninguna_letra.clicked.connect(self.seleccionar_ninguna_letra)
        botones_letras_layout.addWidget(btn_ninguna_letra)

        letras_main_layout.addLayout(botones_letras_layout)

        letras_group.setLayout(letras_main_layout)
        grids_layout.addWidget(letras_group)

        # Se crea el layout horizontal con los dos grids
        layout.addLayout(grids_layout)

        # Botones principales
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    # ========= ACCIONES RÁPIDAS - GRUPOS =========
    def seleccionar_todos(self) -> None:
        """Selecciona todos los grupos"""
        for check in self.check_grupos.values():
            check.setChecked(True)

    def seleccionar_ninguno(self) -> None:
        """Deselecciona todos los grupos"""
        for check in self.check_grupos.values():
            check.setChecked(False)

    def get_grupos_seleccionados(self) -> list[str]:
        """Obtiene la lista de grupos seleccionados"""
        return [grupo for grupo, check in self.check_grupos.items() if check.isChecked()]

    # ========= ACCIONES RÁPIDAS - LETRAS =========
    def seleccionar_todas_letras(self) -> None:
        """Selecciona todas las letras"""
        for check in self.check_letras.values():
            check.setChecked(True)

    def seleccionar_ninguna_letra(self) -> None:
        """Deselecciona todas las letras"""
        for check in self.check_letras.values():
            check.setChecked(False)

    def get_letras_seleccionadas(self) -> list[str]:
        """Obtiene la lista de letras seleccionadas"""
        return [letra for letra, check in self.check_letras.items() if check.isChecked()]

    # ========= TEMA / ESTILOS =========
    def apply_dark_theme(self) -> None:
        """Aplicar tema oscuro completo idéntico al de aulas"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
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
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #444444;
            }
            QPushButton:checked {
                background-color: #4a9eff;
                border-color: #3a8eef;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #4a9eff;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4a9eff;
                border: 2px solid #4a9eff;
                border-radius: 3px;
            }
            QToolTip {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #4a9eff;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: normal;
            }
        """)


# ========= Widget Visual de Franja Horaria =========
class FranjaHorarioWidget(QFrame):
    """Widget para mostrar una franja horaria con sus grupos"""

    franja_editada = pyqtSignal(str, str, list, list)  # Se añade list para letras
    franja_eliminada = pyqtSignal(str, str)

    # ========= INICIALIZACIÓN =========
    def __init__(self, dia, horario, grupos=None, letras=None, parent=None):
        super().__init__(parent)
        self.dia = dia
        self.horario = horario
        self.grupos = grupos or []
        self.letras = letras or []  # agregado para las letras
        self.parent_window = parent
        self._widgets_creados = False

        self.setFixedSize(140, 80)
        self.setup_ui()
        self.apply_style()

    def setup_ui(self) -> None:
        """Configura la interfaz inicial UNA SOLA VEZ"""
        if self._widgets_creados:
            return

        # Crear layout principal
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)

        # NEW LETRAS!! - Label para letras (pequeño, arriba a la izquierda)
        self.letras_label = QLabel()
        self.letras_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.letras_label.setFont(QFont("Arial", 7))
        self.letras_label.setStyleSheet("color: #aaaaaa; padding: 0px; margin: 0px;")
        self.letras_label.setWordWrap(True)
        self.letras_label.setMaximumHeight(20)

        # Crear widgets que se reutilizarán
        self.grupos_label = QLabel()
        self.grupos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grupos_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.grupos_label.setWordWrap(True)

        self.vacio_label = QLabel("Sin grupos")
        self.vacio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vacio_label.setStyleSheet("color: #888888; font-style: italic;")

        # Separador reutilizable
        self.separador = QFrame()
        self.separador.setFrameShape(QFrame.Shape.HLine)
        self.separador.setStyleSheet("color: #555555;")

        # Crear botones que se reutilizarán
        self.btn_editar = QPushButton("✏️")
        self.btn_editar.setFixedSize(25, 25)
        self.btn_editar.clicked.connect(self.editar_franja)
        self.btn_editar.setToolTip("Editar franja")

        self.btn_eliminar = QPushButton("🗑️")
        self.btn_eliminar.setFixedSize(25, 25)
        self.btn_eliminar.clicked.connect(self.eliminar_franja)
        self.btn_eliminar.setToolTip("Eliminar franja")

        self.btn_anadir = QPushButton("➕")
        self.btn_anadir.setFixedSize(30, 30)
        self.btn_anadir.clicked.connect(self.editar_franja)
        self.btn_anadir.setToolTip(f"Añadir grupos a {self.dia} {self.horario}")

        # Layout para botones - CENTRADO
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(2)
        self.btn_layout.addStretch()  # Espacio a la izquierda
        self.btn_layout.addWidget(self.btn_editar)
        self.btn_layout.addWidget(self.btn_eliminar)
        self.btn_layout.addStretch()  # Espacio a la derecha

        # Aplicar estilos a los botones
        self.aplicar_estilos_botones()

        # Añadir widgets al layout principal
        self.main_layout.addWidget(self.letras_label)
        self.main_layout.addWidget(self.grupos_label)
        self.main_layout.addWidget(self.vacio_label)
        self.main_layout.addWidget(self.separador)
        self.main_layout.addLayout(self.btn_layout)
        self.main_layout.addWidget(self.btn_anadir, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.main_layout)
        self._widgets_creados = True

        # Actualizar contenido inicial
        self.actualizar_contenido()

    # ========= ACTUALIZACIÓN DE UI =========
    def actualizar_contenido(self) -> None:
        """Actualiza solo el contenido visible sin recrear widgets"""
        if not self._widgets_creados:
            return

        # Actualizar letras
        if self.letras:
            # Formatear letras en dos líneas: A,B,C / D,E,F
            primera_linea = ", ".join(self.letras[:3]) if len(self.letras) > 0 else ""
            segunda_linea = ", ".join(self.letras[3:]) if len(self.letras) > 3 else ""

            if segunda_linea:
                letras_text = f"{primera_linea}\n{segunda_linea}"
            else:
                letras_text = primera_linea

            self.letras_label.setText(letras_text)
            self.letras_label.setVisible(True)
        else:
            self.letras_label.setVisible(False)

        # Actualizar grupos
        if self.grupos:
            # Mostrar estado con grupos
            grupos_text = ", ".join(self.grupos)
            if len(grupos_text) > 12:
                grupos_text = grupos_text[:12] + "..."

            self.grupos_label.setText(grupos_text)
            self.grupos_label.setVisible(True)
            self.vacio_label.setVisible(False)
            self.btn_editar.setVisible(True)
            self.btn_eliminar.setVisible(True)
            self.btn_anadir.setVisible(False)
        else:
            # Mostrar estado vacío
            self.grupos_label.setVisible(False)
            self.vacio_label.setVisible(True)
            self.btn_editar.setVisible(False)
            self.btn_eliminar.setVisible(False)
            self.btn_anadir.setVisible(True)

    # ========= ESTILO =========
    def apply_style(self) -> None:
        """Aplica el estilo según el contenido"""
        if self.grupos:
            # Celda con contenido - verde
            self.setStyleSheet("""
                FranjaHorarioWidget {
                    background-color: #004a00;
                    border: 2px solid #00aa00;
                    border-radius: 5px;
                    margin: 2px;
                }
                QLabel {
                    color: #ffffff;
                    background-color: transparent;
                    border: none;
                }
            """)
        else:
            # Celda vacía - gris
            self.setStyleSheet("""
                FranjaHorarioWidget {
                    background-color: #3c3c3c;
                    border: 1px dashed #666666;
                    border-radius: 5px;
                    margin: 2px;
                }
                QLabel {
                    color: #888888;
                    background-color: transparent;
                    border: none;
                }
            """)

    def aplicar_estilos_botones(self) -> None:
        """Aplica estilos a los botones"""
        estilo_editar = """
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: #2196F3;
                padding: 2px;
                margin: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 0.3);
                border-color: #2196F3;
                color: #2196F3;
            }
            QPushButton:pressed {
                background-color: rgba(33, 150, 243, 0.5);
                border-color: #1976D2;
            }
        """

        estilo_eliminar = """
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: #f44336;
                padding: 2px;
                margin: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 0.3);
                border-color: #f44336;
                color: #f44336;
            }
            QPushButton:pressed {
                background-color: rgba(244, 67, 54, 0.5);
                border-color: #d32f2f;
            }
        """

        estilo_anadir = """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 6px;
                background-color: #444;
                color: #4CAF50;
                padding: 4px;
                margin: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 0.3);
                border-color: #4CAF50;
                color: #4CAF50;
            }
            QPushButton:pressed {
                background-color: rgba(76, 175, 80, 0.5);
                border-color: #45a049;
            }
        """

        self.btn_editar.setStyleSheet(estilo_editar)
        self.btn_eliminar.setStyleSheet(estilo_eliminar)
        self.btn_anadir.setStyleSheet(estilo_anadir)

    def actualizar_grupos(self, nuevos_grupos, nuevas_letras) -> None:
        """Actualiza los grupos y letras SIN recrear widgets"""
        cambio = False

        if self.grupos != nuevos_grupos:
            self.grupos = nuevos_grupos
            cambio = True

        if nuevas_letras is not None and self.letras != nuevas_letras:
            self.letras = nuevas_letras
            cambio = True

        if cambio:
            self.actualizar_contenido()
            self.apply_style()

    # ========= ACCIONES DE USUARIO =========
    def editar_franja(self) -> None:
        """Abre el diálogo para editar esta franja"""
        if not self.parent_window:
            return

        grupos_disponibles = self.parent_window.obtener_grupos_asignatura_actual()

        if not grupos_disponibles:
            QMessageBox.warning(
                self, "Sin Grupos",
                "No hay grupos configurados para esta asignatura.\n"
                "Añade grupos primero en la sección de grupos."
            )
            return

        # Obtener letras actuales desde el JSON
        letras_actuales = self.parent_window.obtener_letras_franja(self.dia, self.horario)

        dialog = GestionAsignaturaDialog(
            self.dia, self.horario,
            grupos_disponibles, self.grupos,
            letras_actuales,  # agregado nuevo agregado para las letras
            self.parent_window
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nuevos_grupos = dialog.get_grupos_seleccionados()
            letras_seleccionadas = dialog.get_letras_seleccionadas()
            self.actualizar_grupos(nuevos_grupos, letras_seleccionadas)
            self.franja_editada.emit(self.dia, self.horario, nuevos_grupos, letras_seleccionadas)

    def eliminar_franja(self) -> None:
        """Elimina todos los grupos de esta franja"""
        if not self.grupos:
            return

        respuesta = QMessageBox.question(
            self, "Eliminar Grupos",
            f"¿Eliminar todos los grupos de {self.dia} {self.horario}?\n\n"
            f"Grupos actuales: {', '.join(self.grupos)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.actualizar_grupos([], [])
            self.franja_eliminada.emit(self.dia, self.horario)


# ========= Ventana Principal =========
class ConfigurarHorariosWindow(QMainWindow):
    """Ventana principal para configurar horarios de laboratorios"""

    configuracion_actualizada = pyqtSignal(dict)

    # ========= INICIALIZACIÓN =========
    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Horarios - OPTIM")
        center_window_on_screen(self, 1400, 800)

        # Horarios fijos del sistema
        self.horarios_fijos = [
            "9:30-11:30",
            "11:30-13:30",
            "15:30-17:30",
            "17:30-19:30"
        ]
        self.dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

        # Estructura de datos
        if datos_existentes:
            self.datos_configuracion = {
                "semestre_actual": datos_existentes.get("semestre_actual", "1"),
                "asignaturas": datos_existentes.get("asignaturas", {"1": {}, "2": {}})
            }
            self.log_mensaje("Cargando configuración existente del sistema...", "info")
        else:
            self.datos_configuracion = {
                "semestre_actual": "1",
                "asignaturas": {"1": {}, "2": {}}
            }
            self.log_mensaje("Iniciando configuración nueva...", "info")

        # Control de cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados = datos_existentes is not None

        self.asignatura_actual = None
        self.franjas_widgets = {}

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    # ========= CONFIGURACIÓN UI =========
    def setup_ui(self) -> None:
        """Configura la interfaz principal"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Selector de semestre
        semestre_group = QGroupBox("📚 SELECCIÓN DE SEMESTRE")
        semestre_layout = QHBoxLayout()

        self.radio_sem1 = QPushButton("1º Semestre")
        self.radio_sem1.setCheckable(True)
        self.radio_sem2 = QPushButton("2º Semestre")
        self.radio_sem2.setCheckable(True)
        self.radio_sem1.setChecked(True)

        semestre_layout.addWidget(self.radio_sem1)
        semestre_layout.addWidget(self.radio_sem2)
        semestre_layout.addStretch()

        semestre_group.setLayout(semestre_layout)
        main_layout.addWidget(semestre_group)

        # Contenido principal
        content_layout = QHBoxLayout()

        # Panel izquierdo - Asignaturas (SOLO LECTURA)
        left_panel = QGroupBox("📋 ASIGNATURAS DEL SEMESTRE")
        left_layout = QVBoxLayout()

        # Header sin botones de gestión
        asignatura_header = QHBoxLayout()
        asignatura_header.addWidget(QLabel("Asignaturas del sistema:"))
        asignatura_header.addStretch()

        left_layout.addLayout(asignatura_header)

        self.list_asignaturas = QListWidget()
        self.list_asignaturas.setMaximumWidth(300)
        left_layout.addWidget(self.list_asignaturas)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Panel central - Grupos (SOLO LECTURA)
        center_panel = QGroupBox("🎓 GRUPOS DE LA ASIGNATURA")
        center_layout = QVBoxLayout()

        self.label_asignatura_grupos = QLabel("Seleccione una asignatura")
        self.label_asignatura_grupos.setStyleSheet("color: #4a9eff; font-weight: bold;")
        center_layout.addWidget(self.label_asignatura_grupos)

        # Header sin botones de gestión
        grupos_header = QHBoxLayout()
        grupos_header.addWidget(QLabel("Grupos configurados:"))
        grupos_header.addStretch()

        center_layout.addLayout(grupos_header)

        self.list_grupos = QListWidget()
        self.list_grupos.setMaximumWidth(250)
        center_layout.addWidget(self.list_grupos)

        center_panel.setLayout(center_layout)
        content_layout.addWidget(center_panel)

        # Panel derecho - Grid de horarios
        right_panel = QGroupBox("⚙️ CONFIGURACIÓN DE HORARIOS")
        right_layout = QVBoxLayout()

        self.label_asignatura = QLabel("Seleccione una asignatura")
        self.label_asignatura.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(self.label_asignatura)

        # Grid de horarios
        grid_group = QGroupBox("🗓️ HORARIOS DE LABORATORIO")
        grid_layout = QVBoxLayout()

        self.crear_grid_horarios(grid_layout)

        grid_group.setLayout(grid_layout)
        right_layout.addWidget(grid_group)

        # Botones de acción (solo archivos y sistema)
        buttons_layout = QHBoxLayout()

        self.btn_cargar = QPushButton("📥 Importar Datos")
        self.btn_guardar = QPushButton("💾 Exportar Datos")
        self.btn_guardar_sistema = QPushButton("Guardar en Sistema")
        self.btn_borrar_horarios = QPushButton("Borrar Horarios")

        self.btn_guardar_sistema.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: 1px solid #45a049;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.btn_borrar_horarios.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: #ffffff;
                border: 1px solid #b71c1c;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)

        buttons_layout.addWidget(self.btn_cargar)
        buttons_layout.addWidget(self.btn_guardar)
        buttons_layout.addWidget(self.btn_guardar_sistema)
        buttons_layout.addWidget(self.btn_borrar_horarios)
        buttons_layout.addStretch()

        right_layout.addLayout(buttons_layout)
        right_panel.setLayout(right_layout)
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

    def apply_dark_theme(self) -> None:
        """Aplicar tema oscuro completo idéntico al de aulas"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
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
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #444444;
            }
            QPushButton:checked {
                background-color: #4a9eff;
                border-color: #3a8eef;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #4a9eff;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 2px solid #555555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4a9eff;
                border: 2px solid #4a9eff;
                border-radius: 3px;
            }
            QToolTip {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #4a9eff;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: normal;
            }
        """)

    def crear_grid_horarios(self, parent_layout) -> None:
        """Crea el grid de horarios 4x5"""
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        # Header vacío
        grid_layout.addWidget(QLabel(""), 0, 0)

        # Headers de días
        for col, dia in enumerate(self.dias_semana):
            header = QLabel(dia)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header.setStyleSheet("background-color: #4a4a4a; padding: 8px; border-radius: 3px; color: white;")
            header.setFixedWidth(140)
            grid_layout.addWidget(header, 0, col + 1)

        # Filas de horarios
        for fila, horario in enumerate(self.horarios_fijos):
            # Header de horario
            horario_header = QLabel(horario)
            horario_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            horario_header.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            horario_header.setStyleSheet("background-color: #5a5a5a; padding: 8px; border-radius: 3px; color: white;")
            horario_header.setFixedWidth(80)
            grid_layout.addWidget(horario_header, fila + 1, 0)

            # Franjas del horario
            for col, dia in enumerate(self.dias_semana):
                franja = FranjaHorarioWidget(dia, horario, grupos=[], letras=[], parent=self)
                franja.franja_editada.connect(self.actualizar_franja)
                franja.franja_eliminada.connect(self.eliminar_franja)

                key = (dia, horario)
                self.franjas_widgets[key] = franja
                grid_layout.addWidget(franja, fila + 1, col + 1)

        grid_widget.setLayout(grid_layout)
        parent_layout.addWidget(grid_widget)

    # ========= CONEXIONES / SIGNALS =========
    def conectar_signals(self) -> None:
        """Conecta las señales de los controles"""
        self.radio_sem1.clicked.connect(self.cambiar_semestre)
        self.radio_sem2.clicked.connect(self.cambiar_semestre)
        self.list_asignaturas.itemClicked.connect(self.seleccionar_asignatura)

        # Solo botones de archivo y sistema
        self.btn_cargar.clicked.connect(self.import_config)
        self.btn_guardar.clicked.connect(self.export_config)
        self.btn_guardar_sistema.clicked.connect(self.guardar_en_sistema)
        self.btn_borrar_horarios.clicked.connect(self.eliminar_todo)

    # ========= CARGA INICIAL =========
    def cargar_datos_iniciales(self) -> None:
        """Carga los datos iniciales"""
        try:
            semestre_actual = self.datos_configuracion.get("semestre_actual", "1")
            if semestre_actual == "1":
                self.radio_sem1.setChecked(True)
                self.radio_sem2.setChecked(False)
            else:
                self.radio_sem1.setChecked(False)
                self.radio_sem2.setChecked(True)

            self.cargar_asignaturas()

            total_asignaturas = sum(
                len(asignaturas) for asignaturas in self.datos_configuracion["asignaturas"].values())
            if total_asignaturas > 0:
                self.log_mensaje(f"Datos cargados: {total_asignaturas} asignaturas", "success")
                self.auto_seleccionar_primera_asignatura()
            else:
                self.log_mensaje("Configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"Error cargando datos: {e}", "warning")

    def cargar_asignaturas(self) -> None:
        """Carga asignaturas SOLO desde el sistema central (configuracion_labs.json)"""
        self.list_asignaturas.clear()

        try:
            semestre_actual = self.datos_configuracion["semestre_actual"]
            self.log_mensaje(f"Cargando asignaturas del sistema para {semestre_actual}º Semestre", "info")

            # Solo cargar desde el sistema central
            asignaturas_encontradas = []

            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                try:
                    config = self.parent_window.configuracion
                    if "configuracion" in config and "asignaturas" in config["configuracion"]:
                        asignaturas_config = config["configuracion"]["asignaturas"]

                        if asignaturas_config.get("configurado", False):
                            asignaturas_datos = asignaturas_config.get("datos", {})
                            semestre_texto = f"{semestre_actual}º Semestre"

                            # Filtrar asignaturas por semestre
                            for codigo, datos in asignaturas_datos.items():
                                if datos.get('semestre') == semestre_texto:
                                    # nombre = datos.get('nombre', codigo)
                                    grupos = datos.get('grupos_asociados', [])

                                    # clave_asignatura = codigo

                                    # Actualizar estructura local para horarios
                                    if semestre_actual not in self.datos_configuracion["asignaturas"]:
                                        self.datos_configuracion["asignaturas"][semestre_actual] = {}

                                    if codigo not in self.datos_configuracion["asignaturas"][semestre_actual]:
                                        self.datos_configuracion["asignaturas"][semestre_actual][codigo] = {
                                            "grupos": grupos.copy(),
                                            "horarios_grid": {}
                                        }
                                    else:
                                        # Actualizar grupos desde el sistema
                                        self.datos_configuracion["asignaturas"][semestre_actual][codigo]["grupos"] = grupos.copy()

                                    asignaturas_encontradas.append((codigo, grupos))

                            self.log_mensaje(f"Sincronizadas {len(asignaturas_encontradas)} asignaturas", "info")
                        else:
                            self.log_mensaje("Asignaturas no configuradas en el sistema", "warning")
                    else:
                        self.log_mensaje("No se encontró configuración de asignaturas", "warning")
                except Exception as e:
                    self.log_mensaje(f"Error accediendo al sistema: {e}", "error")
            else:
                self.log_mensaje("No hay conexión con el sistema principal", "warning")

            # Mostrar asignaturas encontradas
            if asignaturas_encontradas:
                for codigo, grupos in sorted(asignaturas_encontradas):
                    # Buscar nombre completo
                    nombre_completo = None
                    for cod, datos in asignaturas_datos.items():
                        if cod == codigo:
                            nombre_completo = datos.get('nombre', codigo)
                            break

                    # Crear texto descriptivo con código y nombre
                    texto = f"📚 {codigo} - {nombre_completo if nombre_completo else codigo}"
                    if grupos:
                        texto += f"\n   📝 {len(grupos)} grupos: {', '.join(grupos)}"
                    else:
                        texto += f"\n   ⚠️ Sin grupos configurados"

                    item = QListWidgetItem(texto)
                    item.setData(Qt.ItemDataRole.UserRole, codigo)

                    # Colorear según el estado
                    if grupos:
                        item.setBackground(QColor(0, 100, 0, 80))  # Verde para asignaturas con grupos
                    else:
                        item.setBackground(QColor(100, 100, 0, 80))  # Amarillo para sin grupos

                    self.list_asignaturas.addItem(item)

                self.log_mensaje(f"Cargadas {len(asignaturas_encontradas)} asignaturas del sistema", "success")
            else:
                # No hay asignaturas en el sistema
                if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                    item = QListWidgetItem(f"❌ No hay asignaturas para {semestre_actual}º Semestre en el sistema")
                    item.setBackground(QColor(100, 100, 100, 80))
                    self.log_mensaje(f"No hay asignaturas para {semestre_actual}º Semestre en el sistema", "warning")
                else:
                    item = QListWidgetItem("❌ No hay conexión con el sistema principal")
                    item.setBackground(QColor(100, 0, 0, 80))
                    self.log_mensaje("No hay conexión con el sistema principal", "error")

                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list_asignaturas.addItem(item)

        except Exception as e:
            self.log_mensaje(f"Error cargando asignaturas: {e}", "error")
            traceback.print_exc()

            # Mostrar error
            item = QListWidgetItem(f"❌ Error: {str(e)}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QColor(100, 0, 0, 80))
            self.list_asignaturas.addItem(item)

    def auto_seleccionar_primera_asignatura(self) -> None:
        """Selecciona automáticamente la primera asignatura"""
        try:
            if self.list_asignaturas.count() > 0:
                # Buscar el primer item válido
                for i in range(self.list_asignaturas.count()):
                    item = self.list_asignaturas.item(i)
                    if item and (item.flags() & Qt.ItemFlag.ItemIsEnabled):
                        asignatura = item.data(Qt.ItemDataRole.UserRole)
                        if asignatura:
                            self.list_asignaturas.setCurrentItem(item)
                            self.seleccionar_asignatura(item)
                            self.log_mensaje(f"Auto-seleccionada primera asignatura: {asignatura}", "info")
                            return

                self.log_mensaje("No hay asignaturas válidas para auto-seleccionar", "warning")
            else:
                self.log_mensaje("Lista de asignaturas vacía", "warning")
        except Exception as e:
            self.log_mensaje(f"Error en auto-selección: {e}", "error")

    # ========= CONTEXTO / SELECCIÓN =========
    def cambiar_semestre(self) -> None:
        """Cambia el semestre activo"""
        sender = self.sender()

        if sender == self.radio_sem1:
            self.radio_sem2.setChecked(False)
            self.datos_configuracion["semestre_actual"] = "1"
        else:
            self.radio_sem1.setChecked(False)
            self.datos_configuracion["semestre_actual"] = "2"

        self.cargar_asignaturas()
        self.limpiar_seleccion()
        self.marcar_cambio()

    def seleccionar_asignatura(self, item) -> None:
        """Selecciona una asignatura"""
        if not item:
            self.log_mensaje("No hay item seleccionado", "warning")
            return

        # Verificar si es un item válido
        if not (item.flags() & Qt.ItemFlag.ItemIsEnabled):
            self.log_mensaje("Item no seleccionable", "warning")
            return

        asignatura = item.data(Qt.ItemDataRole.UserRole)
        if not asignatura:
            self.log_mensaje("No se pudo obtener el nombre de la asignatura", "warning")
            return

        # Limpiar selección anterior
        self.limpiar_seleccion()

        # Establecer nueva selección
        self.asignatura_actual = asignatura
        self.label_asignatura.setText(f"📚 {asignatura}")
        self.label_asignatura_grupos.setText(asignatura)

        self.log_mensaje(f"Seleccionada asignatura: {asignatura}", "success")

        # Cargar datos de la asignatura
        try:
            self.inicializar_estructura_asignatura()
            self.cargar_grupos_asignatura()
            self.cargar_horarios_asignatura()
            self.log_mensaje(f"Datos cargados para '{asignatura}'", "success")
        except Exception as e:
            self.log_mensaje(f"Error cargando datos de '{asignatura}': {e}", "error")

    def limpiar_seleccion(self) -> None:
        """Limpia la selección actual"""
        self.limpiar_grid()
        self.asignatura_actual = None
        self.label_asignatura.setText("Seleccione una asignatura")
        self.label_asignatura_grupos.setText("Seleccione una asignatura")
        self.list_grupos.clear()

    # ========= DATOS DE ASIGNATURA / GRUPOS =========
    def inicializar_estructura_asignatura(self) -> None:
        """Inicializa la estructura de datos para la asignatura"""
        if not self.asignatura_actual:
            self.log_mensaje("No hay asignatura actual para inicializar", "warning")
            return

        try:
            semestre = self.datos_configuracion["semestre_actual"]

            # Asegurar que existe la estructura básica
            if "asignaturas" not in self.datos_configuracion:
                self.datos_configuracion["asignaturas"] = {"1": {}, "2": {}}

            if semestre not in self.datos_configuracion["asignaturas"]:
                self.datos_configuracion["asignaturas"][semestre] = {}

            # Verificar si ya existe la asignatura
            if self.asignatura_actual in self.datos_configuracion["asignaturas"][semestre]:
                self.log_mensaje(f"Estructura ya existe para '{self.asignatura_actual}'", "info")
                return

            # Obtener grupos desde el sistema principal
            grupos_sistema = self.obtener_grupos_asignatura(self.asignatura_actual)

            if not grupos_sistema:
                self.log_mensaje(f"No se encontraron grupos para '{self.asignatura_actual}'", "warning")
                grupos_sistema = []

            # Crear estructura inicial
            self.datos_configuracion["asignaturas"][semestre][self.asignatura_actual] = {
                "grupos": grupos_sistema.copy(),
                "horarios_grid": {}
            }

            self.log_mensaje(
                f"Estructura inicializada para '{self.asignatura_actual}' con {len(grupos_sistema)} grupos",
                "success")

        except Exception as e:
            self.log_mensaje(f"Error inicializando estructura: {e}", "error")
            traceback.print_exc()

    def cargar_grupos_asignatura(self) -> None:
        """Carga grupos mostrando código - nombre"""
        self.list_grupos.clear()

        if not self.asignatura_actual:
            return

        try:
            grupos_dict = self.obtener_grupos_asignatura(self.asignatura_actual)

            if grupos_dict:
                for codigo, nombre in sorted(grupos_dict.items()):
                    # Mostrar "código - nombre"
                    texto_grupo = f"🎓 {codigo} - {nombre}"
                    item = QListWidgetItem(texto_grupo)
                    item.setData(Qt.ItemDataRole.UserRole, codigo)
                    item.setBackground(QColor(0, 0, 100, 80))
                    self.list_grupos.addItem(item)

                self.log_mensaje(f"Cargados {len(grupos_dict)} grupos", "info")
            else:
                # Sin grupos
                item = QListWidgetItem("⚠️ No hay grupos configurados para esta asignatura")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setBackground(QColor(100, 100, 0, 80))
                self.list_grupos.addItem(item)

        except Exception as e:
            self.log_mensaje(f"Error cargando grupos: {e}", "error")

    def obtener_grupos_asignatura(self, asignatura) -> dict[str, str]:
        """Obtiene grupos con sus nombres desde el sistema central"""
        if not asignatura:
            return {}

        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config = self.parent_window.configuracion
                if "configuracion" in config and "asignaturas" in config["configuracion"]:
                    asignaturas_config = config["configuracion"]["asignaturas"]

                    if asignaturas_config.get("configurado", False):
                        asignaturas_datos = asignaturas_config.get("datos", {})

                        # Buscar por nombre o código
                        for codigo, datos in asignaturas_datos.items():
                            nombre_asig = datos.get('nombre', '')
                            if nombre_asig == asignatura or codigo == asignatura:
                                grupos_codigos = datos.get('grupos_asociados', [])
                                if grupos_codigos:
                                    # Crear diccionario código: nombre
                                    grupos_con_nombres = {}
                                    for codigo_grupo in grupos_codigos:
                                        nombre_grupo = self.obtener_nombre_grupo(codigo_grupo)
                                        grupos_con_nombres[codigo_grupo] = nombre_grupo

                                    return grupos_con_nombres
                                break
            return {}
        except Exception as e:
            self.log_mensaje(f"Error obteniendo grupos: {e}", "error")
            return {}

    def obtener_grupos_asignatura_actual(self) -> list[str]:
        """Obtiene los grupos de la asignatura actual"""
        if not self.asignatura_actual:
            return []
        return self.obtener_grupos_asignatura(self.asignatura_actual)

    def obtener_nombre_grupo(self, codigo_grupo) -> str:
        """Obtiene el nombre completo de un grupo por su código"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config = self.parent_window.configuracion
                if "configuracion" in config and "grupos" in config["configuracion"]:
                    grupos_config = config["configuracion"]["grupos"]
                    if grupos_config.get("configurado", False):
                        grupos_datos = grupos_config.get("datos", {})
                        if codigo_grupo in grupos_datos:
                            return grupos_datos[codigo_grupo].get('nombre', codigo_grupo)
            return codigo_grupo
        except Exception:
            return codigo_grupo

    # ========= GRID DE HORARIOS =========
    def cargar_horarios_asignatura(self) -> None:
        """Carga los horarios de la asignatura actual"""
        if not self.asignatura_actual:
            self.log_mensaje("No hay asignatura seleccionada", "warning")
            return

        try:
            # Limpiar grid primero
            self.limpiar_grid()

            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

            # Verificar que la asignatura existe en la estructura local
            if self.asignatura_actual not in asignaturas:
                self.log_mensaje(f"Asignatura '{self.asignatura_actual}' no encontrada en datos locales", "warning")
                self.inicializar_estructura_asignatura()
                asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

            if self.asignatura_actual in asignaturas:
                horarios_grid = asignaturas[self.asignatura_actual].get("horarios_grid", {})

                if not horarios_grid:
                    self.log_mensaje(f"No hay horarios configurados para '{self.asignatura_actual}'", "info")
                    return

                total_franjas = 0

                # Recorrer los horarios configurados
                for horario, dias_data in horarios_grid.items():
                    if not isinstance(dias_data, dict):
                        self.log_mensaje(f"Estructura inválida en horario {horario}", "warning")
                        continue

                    for dia, entry in dias_data.items():
                        # Aceptar ambos formatos: lista o dict {"grupos": [...], "letras": [...], "mixta": bool}
                        if isinstance(entry, dict):
                            grupos = entry.get("grupos", [])
                            letras = entry.get("letras", [])
                        else:
                            grupos = entry if isinstance(entry, list) else []
                            letras = []

                        if not isinstance(grupos, list):
                            self.log_mensaje(f"Grupos inválidos en {dia} {horario}", "warning")
                            continue

                        if grupos:  # Solo procesar si hay grupos
                            key = (dia, horario)
                            if key in self.franjas_widgets:
                                try:
                                    # Actualizar widget existente con grupos Y letras
                                    self.franjas_widgets[key].actualizar_grupos(grupos, letras)
                                    total_franjas += 1
                                    letras_str = f" | Letras: {', '.join(letras)}" if letras else ""
                                    self.log_mensaje(f"Cargado {dia} {horario}: {', '.join(grupos)}{letras_str}",
                                                     "success")
                                except Exception as e:
                                    self.log_mensaje(f"Error actualizando {dia} {horario}: {e}", "error")
                            else:
                                self.log_mensaje(f"Widget no encontrado para {dia} {horario}", "warning")

                if total_franjas > 0:
                    self.log_mensaje(f"Cargadas {total_franjas} franjas para '{self.asignatura_actual}'", "success")
                else:
                    self.log_mensaje(f"No hay franjas con grupos para '{self.asignatura_actual}'", "info")

            else:
                self.log_mensaje(f"No se pudo inicializar estructura para '{self.asignatura_actual}'", "error")

        except Exception as e:
            self.log_mensaje(f"Error cargando horarios: {e}", "error")
            traceback.print_exc()

    def limpiar_grid(self) -> None:
        """Limpia todas las franjas del grid"""
        try:
            contador_limpiado = 0
            for key, franja in self.franjas_widgets.items():
                if franja and hasattr(franja, 'actualizar_grupos'):
                    franja.actualizar_grupos([], [])
                    contador_limpiado += 1

            if contador_limpiado > 0:
                self.log_mensaje(f"Grid limpiado ({contador_limpiado} franjas)", "info")

        except Exception as e:
            self.log_mensaje(f"Error limpiando grid: {e}", "error")

    def actualizar_franja(self, dia, horario, grupos, letras=None) -> None:
        """Actualiza una franja horaria"""
        if not self.asignatura_actual:
            self.log_mensaje("No hay asignatura seleccionada", "warning")
            return

        try:
            # Asegurar que la estructura existe
            self.inicializar_estructura_asignatura()

            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"][semestre]

            # Verificar que la asignatura existe
            if self.asignatura_actual not in asignaturas:
                self.log_mensaje(f"Asignatura '{self.asignatura_actual}' no encontrada", "error")
                return

            # Inicializar estructura de horarios si no existe
            if "horarios_grid" not in asignaturas[self.asignatura_actual]:
                asignaturas[self.asignatura_actual]["horarios_grid"] = {}

            if horario not in asignaturas[self.asignatura_actual]["horarios_grid"]:
                asignaturas[self.asignatura_actual]["horarios_grid"][horario] = {}

            # Actualizar datos con la nueva estructura
            if letras is None:
                letras = []

            asignaturas[self.asignatura_actual]["horarios_grid"][horario][dia] = {
                "grupos": grupos,
                "letras": letras,
                "mixta": False  # Valor por defecto
            }

            # Marcar cambios
            self.marcar_cambio()

            # Log del cambio
            if grupos:
                letras_str = f" | Letras: {', '.join(letras)}" if letras else ""
                self.log_mensaje(f"Actualizado {dia} {horario}: {', '.join(grupos)}{letras_str}", "success")
            else:
                self.log_mensaje(f"Limpiado {dia} {horario}", "info")

        except Exception as e:
            self.log_mensaje(f"Error actualizando franja: {e}", "error")
            traceback.print_exc()

    def eliminar_franja(self, dia, horario) -> None:
        """Elimina una franja horaria"""
        self.actualizar_franja(dia, horario, [])

    def obtener_letras_franja(self, dia, horario) -> list[str]:
        """Obtiene las letras de una franja específica"""
        try:
            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"][semestre]

            if self.asignatura_actual in asignaturas:
                horarios_grid = asignaturas[self.asignatura_actual].get("horarios_grid", {})
                if horario in horarios_grid and dia in horarios_grid[horario]:
                    entry = horarios_grid[horario][dia]
                    if isinstance(entry, dict):
                        return entry.get("letras", [])
            return []
        except Exception as e:
            self.log_mensaje(f"Error obteniendo letras: {e}", "warning")
            return []

    # ========= GUARDAR / IMPORTAR / EXPORTAR =========
    def import_config(self) -> None:
        """Carga configuración desde archivo"""
        ruta_inicial = dir_downloads()

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración",
            ruta_inicial,
            "Archivos JSON (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    datos = json.load(f)

                if "asignaturas" not in datos:
                    raise ValueError("Archivo inválido")

                self.datos_configuracion = datos
                self.cargar_datos_iniciales()
                QMessageBox.information(self, "Éxito", "Configuración cargada")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar: {str(e)}")

    def export_config(self) -> None:
        """Guarda configuración en archivo"""
        ruta_inicial = dir_downloads()
        nombre_archivo = f"horarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ruta_completa = os.path.join(ruta_inicial, nombre_archivo)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración",
            ruta_completa,
            "Archivos JSON (*.json)"
        )

        if file_path:
            try:
                config_data = self.datos_configuracion.copy()
                config_data["metadata"] = {
                    "version": "1.0",
                    "timestamp": datetime.now().isoformat(),
                    "asignatura_actual": self.asignatura_actual
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "Éxito", "Configuración guardada")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    def guardar_en_sistema(self) -> None:
        """Guarda la configuración en el sistema principal (conteo robusto de franjas)."""
        try:
            total_asignaturas = sum(len(asignaturas)
                                    for asignaturas in self.datos_configuracion["asignaturas"].values())

            def _contar_franjas(asignaturas_por_sem) -> int:
                """Cuenta total de franjas horarias asignadas"""
                total = 0
                for _, asig_data in asignaturas_por_sem.items():
                    horarios_grid = asig_data.get("horarios_grid", {})
                    for _, dias_data in horarios_grid.items():
                        for _, entry in dias_data.items():
                            # Aceptar ambos formatos: lista o dict {"grupos": [.], "mixta": bool}
                            grupos = entry.get("grupos", []) if isinstance(entry, dict) else entry
                            if isinstance(grupos, list) and len(grupos) > 0:
                                total += 1
                return total

            total_franjas = 0
            for semestre, asignaturas in self.datos_configuracion["asignaturas"].items():
                total_franjas += _contar_franjas(asignaturas)

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración?\n\n"
                f"• {total_asignaturas} asignaturas\n"
                f"• {total_franjas} franjas configuradas",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                datos_sistema = {
                    "semestre_actual": self.datos_configuracion["semestre_actual"],
                    "asignaturas": self.datos_configuracion["asignaturas"],
                    "metadata": {
                        "total_asignaturas": total_asignaturas,
                        "total_franjas": total_franjas,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                self.configuracion_actualizada.emit(datos_sistema)
                self.datos_guardados = True
                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    # ========= ELIMINACIÓN COMPLETA =========
    def eliminar_todo(self) -> None:
        """Borra todos los horarios configurados"""
        respuesta = QMessageBox.question(
            self, "Borrar Horarios",
            "¿Borrar todos los horarios configurados?\n\n"
            "Se limpiarán todas las franjas horarias.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            for semestre in self.datos_configuracion["asignaturas"]:
                for asignatura in self.datos_configuracion["asignaturas"][semestre]:
                    self.datos_configuracion["asignaturas"][semestre][asignatura]["horarios_grid"] = {}

            self.limpiar_grid()
            self.marcar_cambio()
            QMessageBox.information(self, "Horarios Borrados", "Todos los horarios han sido borrados")

    # ========= ESTADO Y CIERRE =========
    def marcar_cambio(self) -> None:
        """Marca que hubo cambios"""
        self.datos_guardados = False

    def hay_cambios_sin_guardar(self) -> bool:
        """Verifica si hay cambios sin guardar"""
        datos_actuales = json.dumps(self.datos_configuracion, sort_keys=True)
        return datos_actuales != self.datos_iniciales and not self.datos_guardados

    def closeEvent(self, event) -> None:
        """
        Manejar cierre de ventana cancelando modificaciones pendientes si es necesario
        Debe ser closeEvent y no close_event por la libreria pyQt6, es como lo detecta para cerrarlo
        """
        if not self.hay_cambios_sin_guardar():
            self.log_mensaje("Cerrando configuración de horarios", "info")
            event.accept()
            return

        respuesta = QMessageBox.question(
            self, "Cambios sin Guardar",
            "Hay cambios sin guardar en la configuración.\n\n"
            "¿Cerrar sin guardar?\n\n"
            "💡 Tip: Usa 'Guardar en Sistema' para conservar los cambios.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.cancelar_cambios_en_sistema()
            self.log_mensaje("Cerrando sin guardar cambios", "warning")
            event.accept()
        else:
            event.ignore()

    def cancelar_cambios_en_sistema(self) -> None:
        """Cancela cambios y restaura estado original"""
        try:
            datos_originales = json.loads(self.datos_iniciales)

            # Emitir señal de cancelación
            if hasattr(self, 'configuracion_actualizada'):
                datos_cancelacion = {
                    "semestre_actual": datos_originales.get("semestre_actual", "1"),
                    "asignaturas": datos_originales.get("asignaturas", {"1": {}, "2": {}}),
                    "metadata": {
                        "accion": "CANCELAR_CAMBIOS",
                        "timestamp": datetime.now().isoformat(),
                        "origen": "ConfigurarHorariosWindow"
                    }
                }
                self.configuracion_actualizada.emit(datos_cancelacion)

            self.log_mensaje("Cambios cancelados - estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"Error cancelando cambios: {e}", "warning")

    # ========= UTILIDADES / LOG =========
    def hex_to_rgb(self, hex_color) -> str:
        """Convierte color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ','.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

    def log_mensaje(self, mensaje, tipo="info") -> None:
        """Registra un mensaje"""
        if self.parent_window and hasattr(self.parent_window, 'log_mensaje'):
            self.parent_window.log_mensaje(mensaje, tipo)
        else:
            iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            print(f"{iconos.get(tipo, 'ℹ️')} {mensaje}")


def main():
    """Función principal"""
    app = QApplication(sys.argv)

    # Tema oscuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = ConfigurarHorariosWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()