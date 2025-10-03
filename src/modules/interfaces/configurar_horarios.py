#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Horarios - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Sistema de configuración de horarios con franjas fijas para laboratorios universitarios.
Permite asignar cursos a horarios específicos en un grid semanal estructurado.

Funcionalidades:
- Configuración de horarios por semestre
- Gestión de asignaturas y cursos
- Grid semanal con franjas horarias fijas
- Edición y eliminación de franjas
- Integración con sistema central

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QFrame, QScrollArea, QMessageBox, QDialog, QDialogButtonBox,
    QCheckBox, QFileDialog, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


def center_window_on_screen(window, width, height):
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


class GestionAsignaturaDialog(QDialog):
    """Dialog para añadir/editar asignatura"""

    def __init__(self, asignatura_existente=None, parent=None):
        super().__init__(parent)
        self.asignatura_existente = asignatura_existente
        self.setWindowTitle("Editar Asignatura" if asignatura_existente else "Nueva Asignatura")
        self.setModal(True)
        center_window_on_screen(self, 400, 200)

        self.setup_ui()
        self.apply_dark_theme()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Nombre de asignatura
        nombre_layout = QHBoxLayout()
        nombre_layout.addWidget(QLabel("Nombre de Asignatura:"))
        self.edit_nombre = QLineEdit()
        if self.asignatura_existente:
            self.edit_nombre.setText(self.asignatura_existente)
        nombre_layout.addWidget(self.edit_nombre)
        layout.addLayout(nombre_layout)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_nombre(self):
        return self.edit_nombre.text().strip()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
        """)


class EditarCursosDialog(QDialog):
    """Dialog para editar cursos de una franja horaria"""

    def __init__(self, dia, horario, cursos_disponibles, cursos_actuales=None, parent=None):
        super().__init__(parent)
        self.dia = dia
        self.horario = horario
        self.cursos_disponibles = cursos_disponibles
        self.cursos_actuales = cursos_actuales or []

        self.setWindowTitle(f"Configurar {dia} - {horario}")
        self.setModal(True)
        center_window_on_screen(self, 400, 350)

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Título
        titulo = QLabel(f"📚 {self.dia} - {self.horario}")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Cursos disponibles
        cursos_group = QGroupBox("Cursos que tendrán clase:")
        cursos_layout = QVBoxLayout()

        self.check_cursos = {}

        if not self.cursos_disponibles:
            info_label = QLabel("⚠️ No hay cursos configurados para esta asignatura")
            info_label.setStyleSheet("color: #ffaa00;")
            cursos_layout.addWidget(info_label)
        else:
            if isinstance(self.cursos_disponibles, dict):
                for codigo, nombre in sorted(self.cursos_disponibles.items()):
                    texto_check = f"{codigo} - {nombre}"
                    check = QCheckBox(texto_check)
                    if codigo in self.cursos_actuales:
                        check.setChecked(True)
                    self.check_cursos[codigo] = check
                    cursos_layout.addWidget(check)
            else:
                # Retrocompatibilidad
                for curso in sorted(self.cursos_disponibles):
                    check = QCheckBox(curso)
                    if curso in self.cursos_actuales:
                        check.setChecked(True)
                    self.check_cursos[curso] = check
                    cursos_layout.addWidget(check)

        cursos_group.setLayout(cursos_layout)
        layout.addWidget(cursos_group)

        # Botones de acción rápida
        if self.cursos_disponibles:
            botones_layout = QHBoxLayout()

            btn_todos = QPushButton("Todos")
            btn_todos.clicked.connect(self.seleccionar_todos)
            botones_layout.addWidget(btn_todos)

            btn_ninguno = QPushButton("Ninguno")
            btn_ninguno.clicked.connect(self.seleccionar_ninguno)
            botones_layout.addWidget(btn_ninguno)

            botones_layout.addStretch()
            layout.addLayout(botones_layout)

        # Botones principales
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def seleccionar_todos(self):
        """Selecciona todos los cursos"""
        for check in self.check_cursos.values():
            check.setChecked(True)

    def seleccionar_ninguno(self):
        """Deselecciona todos los cursos"""
        for check in self.check_cursos.values():
            check.setChecked(False)

    def get_cursos_seleccionados(self):
        """Obtiene la lista de cursos seleccionados"""
        return [curso for curso, check in self.check_cursos.items() if check.isChecked()]

    def apply_theme(self):
        """Aplica el tema oscuro al diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #555555;
                margin-top: 10px;
                padding-top: 10px;
                border-radius: 3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)


class FranjaHorarioWidget(QFrame):
    """Widget para mostrar una franja horaria con sus cursos"""

    franja_editada = pyqtSignal(str, str, list)
    franja_eliminada = pyqtSignal(str, str)

    def __init__(self, dia, horario, cursos=None, parent=None):
        super().__init__(parent)
        self.dia = dia
        self.horario = horario
        self.cursos = cursos or []
        self.parent_window = parent
        self._widgets_creados = False

        self.setFixedSize(140, 80)
        self.setup_ui_inicial()
        self.apply_style()

    def setup_ui_inicial(self):
        """Configura la interfaz inicial UNA SOLA VEZ"""
        if self._widgets_creados:
            return

        # Crear layout principal
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)

        # Crear widgets que se reutilizarán
        self.cursos_label = QLabel()
        self.cursos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cursos_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.cursos_label.setWordWrap(True)

        self.vacio_label = QLabel("Sin cursos")
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
        self.btn_anadir.setToolTip(f"Añadir cursos a {self.dia} {self.horario}")

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
        self.main_layout.addWidget(self.cursos_label)
        self.main_layout.addWidget(self.vacio_label)
        self.main_layout.addWidget(self.separador)
        self.main_layout.addLayout(self.btn_layout)
        self.main_layout.addWidget(self.btn_anadir, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.main_layout)
        self._widgets_creados = True

        # Actualizar contenido inicial
        self.actualizar_contenido()

    def actualizar_contenido(self):
        """Actualiza solo el contenido visible sin recrear widgets"""
        if not self._widgets_creados:
            return

        if self.cursos:
            # Mostrar estado con cursos
            cursos_text = ", ".join(self.cursos)
            if len(cursos_text) > 12:
                cursos_text = cursos_text[:12] + "..."

            self.cursos_label.setText(cursos_text)
            self.cursos_label.setVisible(True)
            self.vacio_label.setVisible(False)
            self.btn_editar.setVisible(True)
            self.btn_eliminar.setVisible(True)
            self.btn_anadir.setVisible(False)
        else:
            # Mostrar estado vacío
            self.cursos_label.setVisible(False)
            self.vacio_label.setVisible(True)
            self.btn_editar.setVisible(False)
            self.btn_eliminar.setVisible(False)
            self.btn_anadir.setVisible(True)

    def aplicar_estilos_botones(self):
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

    def actualizar_cursos(self, nuevos_cursos):
        """Actualiza los cursos SIN recrear widgets"""
        if self.cursos != nuevos_cursos:
            self.cursos = nuevos_cursos
            self.actualizar_contenido()  # Solo actualizar contenido
            self.apply_style()  # Aplicar estilos

    def editar_franja(self):
        """Abre el diálogo para editar esta franja"""
        if not self.parent_window:
            return

        cursos_disponibles = self.parent_window.obtener_cursos_asignatura_actual()

        if not cursos_disponibles:
            QMessageBox.warning(
                self, "Sin Cursos",
                "No hay cursos configurados para esta asignatura.\n"
                "Añade cursos primero en la sección de cursos."
            )
            return

        dialog = EditarCursosDialog(
            self.dia, self.horario,
            cursos_disponibles, self.cursos,
            self.parent_window
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nuevos_cursos = dialog.get_cursos_seleccionados()
            self.actualizar_cursos(nuevos_cursos)
            self.franja_editada.emit(self.dia, self.horario, nuevos_cursos)

    def eliminar_franja(self):
        """Elimina todos los cursos de esta franja"""
        if not self.cursos:
            return

        respuesta = QMessageBox.question(
            self, "Eliminar Cursos",
            f"¿Eliminar todos los cursos de {self.dia} {self.horario}?\n\n"
            f"Cursos actuales: {', '.join(self.cursos)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.actualizar_cursos([])
            self.franja_eliminada.emit(self.dia, self.horario)

    def apply_style(self):
        """Aplica el estilo según el contenido"""
        if self.cursos:
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


class ConfigurarHorarios(QMainWindow):
    """Ventana principal para configurar horarios de laboratorios"""

    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Horarios - OPTIM Labs")
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
            self.log_mensaje("📥 Cargando configuración existente del sistema...", "info")
        else:
            self.datos_configuracion = {
                "semestre_actual": "1",
                "asignaturas": {"1": {}, "2": {}}
            }
            self.log_mensaje("📝 Iniciando configuración nueva...", "info")

        # Control de cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados = datos_existentes is not None

        self.asignatura_actual = None
        self.franjas_widgets = {}

        self.setup_ui()
        self.apply_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    def setup_ui(self):
        """Configura la interfaz principal - SIN BOTONES DE GESTIÓN"""
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

        # Panel central - Cursos (SOLO LECTURA)
        center_panel = QGroupBox("🎓 CURSOS DE LA ASIGNATURA")
        center_layout = QVBoxLayout()

        self.label_asignatura_cursos = QLabel("Seleccione una asignatura")
        self.label_asignatura_cursos.setStyleSheet("color: #4a9eff; font-weight: bold;")
        center_layout.addWidget(self.label_asignatura_cursos)

        # Header sin botones de gestión
        cursos_header = QHBoxLayout()
        cursos_header.addWidget(QLabel("Cursos configurados:"))
        cursos_header.addStretch()

        center_layout.addLayout(cursos_header)

        self.list_cursos = QListWidget()
        self.list_cursos.setMaximumWidth(250)
        center_layout.addWidget(self.list_cursos)

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

        self.btn_cargar = QPushButton("📁 Cargar Archivo")
        self.btn_guardar = QPushButton("💾 Guardar Archivo")
        self.btn_guardar_sistema = QPushButton("✅ Guardar en Sistema")
        self.btn_borrar_horarios = QPushButton("🗑️ Borrar Horarios")

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


    def create_action_button(self, icon, color, tooltip):
        """Crea un botón de acción con estilo"""
        btn = QPushButton(icon)
        btn.setMinimumSize(40, 30)
        btn.setMaximumSize(50, 50)
        btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 6px;
                background-color: #444;
                color: {color};
                padding: 4px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba({self.hex_to_rgb(color)}, 0.3);
                border-color: {color};
            }}
        """)
        btn.setToolTip(tooltip)
        return btn

    def hex_to_rgb(self, hex_color):
        """Convierte color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ','.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

    def crear_grid_horarios(self, parent_layout):
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
                franja = FranjaHorarioWidget(dia, horario, [], self)
                franja.franja_editada.connect(self.actualizar_franja)
                franja.franja_eliminada.connect(self.eliminar_franja)

                key = (dia, horario)
                self.franjas_widgets[key] = franja
                grid_layout.addWidget(franja, fila + 1, col + 1)

        grid_widget.setLayout(grid_layout)
        parent_layout.addWidget(grid_widget)

    def conectar_signals(self):
        """Conecta las señales de los controles - SIN GESTIÓN DE ASIGNATURAS/CURSOS"""
        self.radio_sem1.clicked.connect(self.cambiar_semestre)
        self.radio_sem2.clicked.connect(self.cambiar_semestre)
        self.list_asignaturas.itemClicked.connect(self.seleccionar_asignatura)

        # Solo botones de archivo y sistema
        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        self.btn_guardar.clicked.connect(self.guardar_configuracion)
        self.btn_guardar_sistema.clicked.connect(self.guardar_en_sistema)
        self.btn_borrar_horarios.clicked.connect(self.borrar_horarios)

    def cargar_datos_iniciales(self):
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
                self.log_mensaje(f"✅ Datos cargados: {total_asignaturas} asignaturas", "success")
                self.auto_seleccionar_primera_asignatura()
            else:
                self.log_mensaje("📝 Configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos: {e}", "warning")

    def auto_seleccionar_primera_asignatura(self):
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
                            self.log_mensaje(f"✅ Auto-seleccionada primera asignatura: {asignatura}", "info")
                            return

                self.log_mensaje("⚠️ No hay asignaturas válidas para auto-seleccionar", "warning")
            else:
                self.log_mensaje("⚠️ Lista de asignaturas vacía", "warning")
        except Exception as e:
            self.log_mensaje(f"❌ Error en auto-selección: {e}", "error")

    def cambiar_semestre(self):
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

    def cargar_asignaturas(self):
        """Carga asignaturas SOLO desde el sistema central (configuracion_labs.json)"""
        self.list_asignaturas.clear()

        try:
            semestre_actual = self.datos_configuracion["semestre_actual"]
            self.log_mensaje(f"📚 Cargando asignaturas del sistema para {semestre_actual}º Semestre", "info")

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
                                    nombre = datos.get('nombre', codigo)
                                    cursos = datos.get('cursos_que_cursan', [])

                                    # USAR CÓDIGO EN LUGAR DE NOMBRE para compatibilidad
                                    clave_asignatura = codigo

                                    # Actualizar estructura local para horarios
                                    if semestre_actual not in self.datos_configuracion["asignaturas"]:
                                        self.datos_configuracion["asignaturas"][semestre_actual] = {}

                                    if codigo not in self.datos_configuracion["asignaturas"][semestre_actual]:
                                        self.datos_configuracion["asignaturas"][semestre_actual][codigo] = {
                                            "cursos": cursos.copy(),
                                            "horarios_grid": {}
                                        }
                                    else:
                                        # Actualizar cursos desde el sistema
                                        self.datos_configuracion["asignaturas"][semestre_actual][codigo]["cursos"] = cursos.copy()

                                    asignaturas_encontradas.append((codigo, cursos))

                            self.log_mensaje(f"🔄 Sincronizadas {len(asignaturas_encontradas)} asignaturas", "info")
                        else:
                            self.log_mensaje("⚠️ Asignaturas no configuradas en el sistema", "warning")
                    else:
                        self.log_mensaje("⚠️ No se encontró configuración de asignaturas", "warning")
                except Exception as e:
                    self.log_mensaje(f"❌ Error accediendo al sistema: {e}", "error")
            else:
                self.log_mensaje("⚠️ No hay conexión con el sistema principal", "warning")

            # Mostrar asignaturas encontradas
            if asignaturas_encontradas:
                for codigo, cursos in sorted(asignaturas_encontradas):
                    # Buscar nombre completo
                    nombre_completo = None
                    for cod, datos in asignaturas_datos.items():
                        if cod == codigo:
                            nombre_completo = datos.get('nombre', codigo)
                            break

                    # Crear texto descriptivo con código y nombre
                    texto = f"📚 {codigo} - {nombre_completo if nombre_completo else codigo}"
                    if cursos:
                        texto += f"\n   📝 {len(cursos)} cursos: {', '.join(cursos)}"
                    else:
                        texto += f"\n   ⚠️ Sin cursos configurados"

                    item = QListWidgetItem(texto)
                    item.setData(Qt.ItemDataRole.UserRole, codigo)

                    # Colorear según el estado
                    if cursos:
                        item.setBackground(QColor(0, 100, 0, 80))  # Verde para asignaturas con cursos
                    else:
                        item.setBackground(QColor(100, 100, 0, 80))  # Amarillo para sin cursos

                    self.list_asignaturas.addItem(item)

                self.log_mensaje(f"✅ Cargadas {len(asignaturas_encontradas)} asignaturas del sistema", "success")
            else:
                # No hay asignaturas en el sistema
                if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                    item = QListWidgetItem(f"📭 No hay asignaturas para {semestre_actual}º Semestre en el sistema")
                    item.setBackground(QColor(100, 100, 100, 80))
                    self.log_mensaje(f"⚠️ No hay asignaturas para {semestre_actual}º Semestre en el sistema", "warning")
                else:
                    item = QListWidgetItem("❌ No hay conexión con el sistema principal")
                    item.setBackground(QColor(100, 0, 0, 80))
                    self.log_mensaje("❌ No hay conexión con el sistema principal", "error")

                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list_asignaturas.addItem(item)

        except Exception as e:
            self.log_mensaje(f"❌ Error cargando asignaturas: {e}", "error")
            import traceback
            traceback.print_exc()

            # Mostrar error
            item = QListWidgetItem(f"❌ Error: {str(e)}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setBackground(QColor(100, 0, 0, 80))
            self.list_asignaturas.addItem(item)

    def seleccionar_asignatura(self, item):
        """Selecciona una asignatura"""
        if not item:
            self.log_mensaje("⚠️ No hay item seleccionado", "warning")
            return

        # Verificar si es un item válido
        if not (item.flags() & Qt.ItemFlag.ItemIsEnabled):
            self.log_mensaje("⚠️ Item no seleccionable", "warning")
            return

        asignatura = item.data(Qt.ItemDataRole.UserRole)
        if not asignatura:
            self.log_mensaje("⚠️ No se pudo obtener el nombre de la asignatura", "warning")
            return

        # Limpiar selección anterior
        self.limpiar_seleccion()

        # Establecer nueva selección
        self.asignatura_actual = asignatura
        self.label_asignatura.setText(f"📚 {asignatura}")
        self.label_asignatura_cursos.setText(asignatura)

        self.log_mensaje(f"✅ Seleccionada asignatura: {asignatura}", "success")

        # Cargar datos de la asignatura
        try:
            self.inicializar_estructura_asignatura()
            self.cargar_cursos_asignatura()
            self.cargar_horarios_asignatura()
            self.log_mensaje(f"✅ Datos cargados para '{asignatura}'", "success")
        except Exception as e:
            self.log_mensaje(f"❌ Error cargando datos de '{asignatura}': {e}", "error")

    def inicializar_estructura_asignatura(self):
        """Inicializa la estructura de datos para la asignatura"""
        if not self.asignatura_actual:
            self.log_mensaje("⚠️ No hay asignatura actual para inicializar", "warning")
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
                self.log_mensaje(f"ℹ️ Estructura ya existe para '{self.asignatura_actual}'", "info")
                return

            # Obtener cursos desde el sistema principal
            cursos_sistema = self.obtener_cursos_asignatura(self.asignatura_actual)

            if not cursos_sistema:
                self.log_mensaje(f"⚠️ No se encontraron cursos para '{self.asignatura_actual}'", "warning")
                cursos_sistema = []

            # Crear estructura inicial
            self.datos_configuracion["asignaturas"][semestre][self.asignatura_actual] = {
                "cursos": cursos_sistema.copy(),
                "horarios_grid": {}
            }

            self.log_mensaje(
                f"✅ Estructura inicializada para '{self.asignatura_actual}' con {len(cursos_sistema)} cursos",
                "success")

        except Exception as e:
            self.log_mensaje(f"❌ Error inicializando estructura: {e}", "error")
            import traceback
            traceback.print_exc()

    def cargar_cursos_asignatura(self):
        """Carga cursos mostrando código - nombre"""
        self.list_cursos.clear()

        if not self.asignatura_actual:
            return

        try:
            cursos_dict = self.obtener_cursos_asignatura(self.asignatura_actual)

            if cursos_dict:
                for codigo, nombre in sorted(cursos_dict.items()):
                    # Mostrar "código - nombre"
                    texto_curso = f"🎓 {codigo} - {nombre}"
                    item = QListWidgetItem(texto_curso)
                    item.setData(Qt.ItemDataRole.UserRole, codigo)
                    item.setBackground(QColor(0, 0, 100, 80))
                    self.list_cursos.addItem(item)

                self.log_mensaje(f"✅ Cargados {len(cursos_dict)} cursos", "info")
            else:
                # Sin cursos
                item = QListWidgetItem("⚠️ No hay cursos configurados para esta asignatura")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setBackground(QColor(100, 100, 0, 80))
                self.list_cursos.addItem(item)

        except Exception as e:
            self.log_mensaje(f"❌ Error cargando cursos: {e}", "error")

    def obtener_nombre_curso(self, codigo_curso):
        """Obtiene el nombre completo de un curso por su código"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config = self.parent_window.configuracion
                if "configuracion" in config and "cursos" in config["configuracion"]:
                    cursos_config = config["configuracion"]["cursos"]
                    if cursos_config.get("configurado", False):
                        cursos_datos = cursos_config.get("datos", {})
                        if codigo_curso in cursos_datos:
                            return cursos_datos[codigo_curso].get('nombre', codigo_curso)
            return codigo_curso
        except Exception:
            return codigo_curso

    def obtener_cursos_asignatura(self, asignatura):
        """Obtiene cursos con sus nombres desde el sistema central"""
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
                                cursos_codigos = datos.get('cursos_que_cursan', [])
                                if cursos_codigos:
                                    # Crear diccionario código: nombre
                                    cursos_con_nombres = {}
                                    for codigo_curso in cursos_codigos:
                                        nombre_curso = self.obtener_nombre_curso(codigo_curso)
                                        cursos_con_nombres[codigo_curso] = nombre_curso

                                    return cursos_con_nombres
                                break
            return {}
        except Exception as e:
            self.log_mensaje(f"❌ Error obteniendo cursos: {e}", "error")
            return {}

    def obtener_cursos_asignatura_actual(self):
        """Obtiene los cursos de la asignatura actual"""
        if not self.asignatura_actual:
            return []
        return self.obtener_cursos_asignatura(self.asignatura_actual)

    def cargar_horarios_asignatura(self):
        """Carga los horarios de la asignatura actual"""
        if not self.asignatura_actual:
            self.log_mensaje("⚠️ No hay asignatura seleccionada", "warning")
            return

        try:
            # Limpiar grid primero
            self.limpiar_grid()

            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

            # Verificar que la asignatura existe en la estructura local
            if self.asignatura_actual not in asignaturas:
                self.log_mensaje(f"⚠️ Asignatura '{self.asignatura_actual}' no encontrada en datos locales", "warning")
                self.inicializar_estructura_asignatura()
                asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

            if self.asignatura_actual in asignaturas:
                horarios_grid = asignaturas[self.asignatura_actual].get("horarios_grid", {})

                if not horarios_grid:
                    self.log_mensaje(f"📝 No hay horarios configurados para '{self.asignatura_actual}'", "info")
                    return

                total_franjas = 0

                # Recorrer los horarios configurados
                for horario, dias_data in horarios_grid.items():
                    if not isinstance(dias_data, dict):
                        self.log_mensaje(f"⚠️ Estructura inválida en horario {horario}", "warning")
                        continue

                    for dia, cursos in dias_data.items():
                        if not isinstance(cursos, list):
                            self.log_mensaje(f"⚠️ Cursos inválidos en {dia} {horario}", "warning")
                            continue

                        if cursos:  # Solo procesar si hay cursos
                            key = (dia, horario)
                            if key in self.franjas_widgets:
                                try:
                                    # Actualizar widget existente
                                    self.franjas_widgets[key].actualizar_cursos(cursos)
                                    total_franjas += 1
                                    self.log_mensaje(f"✅ Cargado {dia} {horario}: {', '.join(cursos)}", "success")
                                except Exception as e:
                                    self.log_mensaje(f"❌ Error actualizando {dia} {horario}: {e}", "error")
                            else:
                                self.log_mensaje(f"⚠️ Widget no encontrado para {dia} {horario}", "warning")

                if total_franjas > 0:
                    self.log_mensaje(f"✅ Cargadas {total_franjas} franjas para '{self.asignatura_actual}'", "success")
                else:
                    self.log_mensaje(f"📝 No hay franjas con cursos para '{self.asignatura_actual}'", "info")

            else:
                self.log_mensaje(f"❌ No se pudo inicializar estructura para '{self.asignatura_actual}'", "error")

        except Exception as e:
            self.log_mensaje(f"❌ Error cargando horarios: {e}", "error")
            import traceback
            traceback.print_exc()

    def limpiar_grid(self):
        """Limpia todas las franjas del grid"""
        try:
            contador_limpiado = 0
            for key, franja in self.franjas_widgets.items():
                if franja and hasattr(franja, 'actualizar_cursos'):
                    franja.actualizar_cursos([])
                    contador_limpiado += 1

            if contador_limpiado > 0:
                self.log_mensaje(f"🧹 Grid limpiado ({contador_limpiado} franjas)", "info")

        except Exception as e:
            self.log_mensaje(f"❌ Error limpiando grid: {e}", "error")

    def limpiar_seleccion(self):
        """Limpia la selección actual"""
        self.limpiar_grid()
        self.asignatura_actual = None
        self.label_asignatura.setText("Seleccione una asignatura")
        self.label_asignatura_cursos.setText("Seleccione una asignatura")
        self.list_cursos.clear()

    def actualizar_franja(self, dia, horario, cursos):
        """Actualiza una franja horaria"""
        if not self.asignatura_actual:
            self.log_mensaje("⚠️ No hay asignatura seleccionada", "warning")
            return

        try:
            # Asegurar que la estructura existe
            self.inicializar_estructura_asignatura()

            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"][semestre]

            # Verificar que la asignatura existe
            if self.asignatura_actual not in asignaturas:
                self.log_mensaje(f"❌ Asignatura '{self.asignatura_actual}' no encontrada", "error")
                return

            # Inicializar estructura de horarios si no existe
            if "horarios_grid" not in asignaturas[self.asignatura_actual]:
                asignaturas[self.asignatura_actual]["horarios_grid"] = {}

            if horario not in asignaturas[self.asignatura_actual]["horarios_grid"]:
                asignaturas[self.asignatura_actual]["horarios_grid"][horario] = {}

            # Actualizar datos
            asignaturas[self.asignatura_actual]["horarios_grid"][horario][dia] = cursos

            # Marcar cambios
            self.marcar_cambio()

            # Log del cambio
            if cursos:
                self.log_mensaje(f"✅ Actualizado {dia} {horario}: {', '.join(cursos)}", "success")
            else:
                self.log_mensaje(f"🗑️ Limpiado {dia} {horario}", "info")

        except Exception as e:
            self.log_mensaje(f"❌ Error actualizando franja: {e}", "error")
            import traceback
            traceback.print_exc()

    def eliminar_franja(self, dia, horario):
        """Elimina una franja horaria"""
        self.actualizar_franja(dia, horario, [])

    def cargar_configuracion(self):
        """Carga configuración desde archivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración", "", "Archivos JSON (*.json)"
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

    def guardar_configuracion(self):
        """Guarda configuración en archivo"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración",
            f"horarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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

    def guardar_en_sistema(self):
        """Guarda la configuración en el sistema principal"""
        try:
            total_asignaturas = sum(
                len(asignaturas) for asignaturas in self.datos_configuracion["asignaturas"].values())
            total_franjas = 0

            for semestre, asignaturas in self.datos_configuracion["asignaturas"].items():
                for asig_data in asignaturas.values():
                    horarios_grid = asig_data.get("horarios_grid", {})
                    for horario_data in horarios_grid.values():
                        for dia_data in horario_data.values():
                            if dia_data:
                                total_franjas += 1

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

    def borrar_horarios(self):
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

    def marcar_cambio(self):
        """Marca que hubo cambios"""
        self.datos_guardados = False

    def hay_cambios_sin_guardar(self):
        """Verifica si hay cambios sin guardar"""
        datos_actuales = json.dumps(self.datos_configuracion, sort_keys=True)
        return datos_actuales != self.datos_iniciales and not self.datos_guardados

    def log_mensaje(self, mensaje, tipo="info"):
        """Registra un mensaje"""
        if self.parent_window and hasattr(self.parent_window, 'log_mensaje'):
            self.parent_window.log_mensaje(mensaje, tipo)
        else:
            iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            print(f"{iconos.get(tipo, 'ℹ️')} {mensaje}")

    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        if not self.hay_cambios_sin_guardar():
            self.log_mensaje("🔚 Cerrando configuración de horarios", "info")
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
            self.log_mensaje("🔚 Cerrando sin guardar cambios", "warning")
            event.accept()
        else:
            event.ignore()

    def cancelar_cambios_en_sistema(self):
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
                        "origen": "ConfigurarHorarios"
                    }
                }
                self.configuracion_actualizada.emit(datos_cancelacion)

            self.log_mensaje("🔄 Cambios cancelados - estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cancelando cambios: {e}", "warning")

    def apply_theme(self):
        """Aplica el tema oscuro"""
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
            QPushButton:checked {
                background-color: #4a9eff;
                border-color: #3a8eef;
            }
            QLabel {
                color: #ffffff;
            }
        """)


def main():
    """Función principal"""
    app = QApplication(sys.argv)

    # Tema oscuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = ConfigurarHorarios()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()