#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Horarios - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Configuración manual de franjas horarias por asignatura
2. Gestión automática de solapamientos temporales
3. Sistema de semestres con asignaturas filtradas
4. Gestión dinámica de grados por asignatura
5. Vista de calendario semanal con edición in-situ
6. Validación automática de conflictos horarios
7. Fusión inteligente de franjas con grados compartidos
8. Edición completa de franjas existentes
9. Import/Export de configuraciones en formato JSON
10. Sincronización con sistema central de asignaturas

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
from datetime import datetime, time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QGroupBox, QFrame, QScrollArea, QMessageBox,
    QTimeEdit, QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


def center_window_on_screen_immediate(window, width, height):
    """Centrar ventana a la pantalla"""
    try:
        # Obtener información de la pantalla
        screen = QApplication.primaryScreen()
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


class GestionAsignaturaDialog(QDialog):
    """Dialog para añadir/editar asignatura"""

    def __init__(self, asignatura_existente=None, parent=None):
        super().__init__(parent)
        self.asignatura_existente = asignatura_existente
        self.setWindowTitle("Editar Asignatura" if asignatura_existente else "Nueva Asignatura")
        self.setModal(True)
        window_width = 400
        window_height = 200
        center_window_on_screen_immediate(self, window_width, window_height)

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


class AnadirFranjaDialog(QDialog):
    """Dialog para añadir/editar franja horaria"""

    def __init__(self, asignatura_actual, parent=None, franja_existente=None):
        super().__init__(parent)
        self.asignatura_actual = asignatura_actual
        self.franja_existente = franja_existente  # Para modo edición

        # Determinar si es edición o creación nueva
        self.es_edicion = franja_existente is not None

        titulo = f"Editar Franja - {asignatura_actual}" if self.es_edicion else f"Añadir Franja - {asignatura_actual}"
        self.setWindowTitle(titulo)
        self.setModal(True)
        window_width = 300
        window_height = 200
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

        # Si es edición, cargar datos existentes
        if self.es_edicion:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Día de la semana
        dia_layout = QHBoxLayout()
        dia_layout.addWidget(QLabel("Día:"))
        self.combo_dia = QComboBox()
        self.combo_dia.addItems(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])
        dia_layout.addWidget(self.combo_dia)
        layout.addLayout(dia_layout)

        # MODIFICACIÓN 1: Hora inicio - entrada manual
        inicio_layout = QHBoxLayout()
        inicio_layout.addWidget(QLabel("Hora Inicio:"))
        self.time_inicio = QTimeEdit()
        self.time_inicio.setTime(QTime(9, 0))
        self.time_inicio.setDisplayFormat("HH:mm")
        inicio_layout.addWidget(self.time_inicio)
        layout.addLayout(inicio_layout)

        # Hora fin - calculada automáticamente (2h después del inicio)
        fin_layout = QHBoxLayout()
        fin_layout.addWidget(QLabel("Hora Fin:"))
        self.label_hora_fin = QLabel("11:00")
        self.label_hora_fin.setStyleSheet(
            "color: #4a9eff; font-weight: bold; background-color: #3c3c3c; padding: 5px; border: 1px solid #555555; border-radius: 3px;")
        fin_layout.addWidget(self.label_hora_fin)
        fin_layout.addWidget(QLabel("(automático: +2h)"))
        layout.addLayout(fin_layout)

        # Grados que cursan esta asignatura
        grados_group = QGroupBox(f"Grados que cursan '{self.asignatura_actual}':")
        grados_layout = QVBoxLayout()

        self.check_grados = {}
        # Obtener grados desde la configuración de la asignatura
        grados_asignatura = self.parent().obtener_grados_asignatura(self.asignatura_actual)
        for grado in grados_asignatura:
            check = QCheckBox(grado)
            self.check_grados[grado] = check
            grados_layout.addWidget(check)

        if not grados_asignatura:
            label_info = QLabel("⚠️ No hay grados configurados para esta asignatura")
            label_info.setStyleSheet("color: #ffaa00;")
            grados_layout.addWidget(label_info)

        grados_group.setLayout(grados_layout)
        layout.addWidget(grados_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)  # Validación antes de aceptar
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Conectar señal para calcular hora fin automáticamente
        self.time_inicio.timeChanged.connect(self.actualizar_hora_fin_automatica)
        self.actualizar_hora_fin_automatica()  # Calcular inicial

    def cargar_datos_existentes(self):
        """Carga los datos de la franja existente para edición"""
        if not self.franja_existente:
            return

        # Determinar el día desde el widget padre
        dia_franja = self.obtener_dia_franja()
        if dia_franja:
            self.combo_dia.setCurrentText(dia_franja)

        # Cargar horas
        hora_inicio = QTime.fromString(self.franja_existente.hora_inicio, "HH:mm")
        hora_fin = QTime.fromString(self.franja_existente.hora_fin, "HH:mm")

        self.time_inicio.setTime(hora_inicio)
        # La hora fin se calculará automáticamente al cambiar la hora de inicio

        # Cargar grados seleccionados
        for grado in self.franja_existente.grados:
            if grado in self.check_grados:
                self.check_grados[grado].setChecked(True)

    def obtener_dia_franja(self):
        """Obtiene el día de la semana de la franja desde el widget padre"""
        if not self.franja_existente:
            return None

        # Buscar en qué día está esta franja
        for dia, widgets in self.parent().franjas_widgets.items():
            if self.franja_existente in widgets:
                return dia
        return None

    def actualizar_hora_fin_automatica(self):
        """Calcula automáticamente la hora fin sumando 2h a la hora de inicio"""
        hora_inicio = self.time_inicio.time()
        hora_fin = hora_inicio.addSecs(2 * 3600)  # +2 horas
        self.label_hora_fin.setText(hora_fin.toString("HH:mm"))

    def validar_y_aceptar(self):
        """Valida los datos antes de aceptar el diálogo"""
        # La validación de hora inicio < hora fin ya no es necesaria porque es automática

        # Validar que al menos un grado esté seleccionado
        grados_seleccionados = [grado for grado, check in self.check_grados.items() if check.isChecked()]
        if not grados_seleccionados:
            QMessageBox.warning(self, "Error de Grados",
                                "Debe seleccionar al menos un grado.")
            return

        # Si todo está correcto, aceptar
        self.accept()

    def get_datos_franja(self):
        """Obtiene los datos configurados en el diálogo"""
        grados_seleccionados = []
        for grado, check in self.check_grados.items():
            if check.isChecked():
                grados_seleccionados.append(grado)

        return {
            'dia': self.combo_dia.currentText(),
            'hora_inicio': self.time_inicio.time().toString("HH:mm"),
            'hora_fin': self.label_hora_fin.text(),  # usar label en lugar de QTimeEdit
            'grados': grados_seleccionados
        }

    def apply_dark_theme(self):
        """Aplica tema oscuro al dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox, QTimeEdit, QCheckBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
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
        """)


class FranjaWidget(QFrame):
    """Widget personalizado para mostrar una franja horaria"""

    # Señal para comunicar eliminación
    eliminado = pyqtSignal(object)
    editado = pyqtSignal(object)

    def __init__(self, franja_id, hora_inicio, hora_fin, grados, parent=None):
        super().__init__(parent)
        self.franja_id = franja_id
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.grados = grados
        self.setup_ui()
        self.apply_style()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Horario
        hora_label = QLabel(f"{self.hora_inicio} - {self.hora_fin}")
        hora_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hora_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(hora_label)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #555555;")
        layout.addWidget(separador)

        # Grados
        if self.grados:
            for grado in self.grados:
                grado_label = QLabel(f"📚 {grado}")
                grado_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                grado_label.setFont(QFont("Arial", 8))
                layout.addWidget(grado_label)
        else:
            vacio_label = QLabel("Sin grados")
            vacio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vacio_label.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(vacio_label)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        # Botón EDITAR - Color verde/azul más suave
        btn_editar = QPushButton("✏️")
        btn_editar.setMinimumSize(30, 30)
        btn_editar.setMaximumSize(40, 40)
        btn_editar.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: #2196F3;  /* Azul Material Design */
                padding: 2px;
                margin: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 0.3);  /* Azul difuminado */
                border-color: #2196F3;
                color: #2196F3;
            }
            QPushButton:pressed {
                background-color: rgba(33, 150, 243, 0.5);
                border-color: #1976D2;
            }
        """)
        btn_editar.setToolTip("Editar franja")
        btn_editar.clicked.connect(self.editar_franja)

        # Botón ELIMINAR - Color rojo más suave
        btn_eliminar = QPushButton("🗑️")
        btn_eliminar.setMinimumSize(30, 30)
        btn_eliminar.setMaximumSize(40, 40)
        btn_eliminar.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: #f44336;  /* Rojo */
                padding: 4px;
                margin: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 0.3);  /* Rojo difuminado */
                border-color: #f44336;
                color: #f44336;
            }
            QPushButton:pressed {
                background-color: rgba(244, 67, 54, 0.5);
                border-color: #d32f2f;
            }
        """)
        btn_eliminar.setToolTip("Eliminar franja")
        btn_eliminar.clicked.connect(self.eliminar_franja)

        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def apply_style(self):
        self.setStyleSheet("""
            FranjaWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                margin: 2px;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 3px;
                color: #ffffff;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)

    def editar_franja(self):
        """Emite señal para editar esta franja"""
        self.editado.emit(self)

    def eliminar_franja(self):
        """Confirma y emite señal para eliminar esta franja"""
        respuesta = QMessageBox.question(
            self, "Eliminar Franja",
            f"¿Eliminar franja {self.hora_inicio}-{self.hora_fin}?\n\nGrados: {', '.join(self.grados)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self.eliminado.emit(self)


class ConfigurarHorarios(QMainWindow):
    """Ventana principal para configurar horarios de laboratorios"""
    configuracion_actualizada = pyqtSignal(dict)
    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Horarios - OPTIM Labs")
        window_width = 1400
        window_height = 800
        center_window_on_screen_immediate(self, window_width, window_height)

        # Estructura de datos principal
        if datos_existentes:
            # Cargar datos existentes del sistema principal
            self.datos_configuracion = {
                "semestre_actual": datos_existentes.get("semestre_actual", "1"),
                "asignaturas": datos_existentes.get("asignaturas", {
                    "1": {},
                    "2": {}
                })
            }
            self.log_mensaje("📥 Cargando configuración existente del sistema...", "info")
        else:
            # Datos por defecto si no hay nada
            self.datos_configuracion = {
                "semestre_actual": "1",
                "asignaturas": {
                    "1": {},
                    "2": {}
                }
            }
            self.log_mensaje("📝 Iniciando configuración nueva...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)  # Snapshot inicial
        self.datos_guardados_en_sistema = datos_existentes is not None  # Si se cargó del sistema

        self.asignatura_actual = None
        self.contador_franjas = 0  # Para IDs únicos
        self.franjas_widgets = {dia: [] for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]}

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    def cargar_datos_iniciales(self):
        """Carga los datos existentes al inicializar la ventana - CON ORDENAMIENTO INICIAL"""
        try:
            # Configurar semestre actual
            semestre_actual = self.datos_configuracion.get("semestre_actual", "2")
            if semestre_actual == "1":
                self.radio_sem1.setChecked(True)
                self.radio_sem2.setChecked(False)
            else:
                self.radio_sem1.setChecked(False)
                self.radio_sem2.setChecked(True)

            # 🔑 ORDENAR TODO AL CARGAR
            self.ordenar_asignaturas_alfabeticamente()

            # Cargar lista de asignaturas
            self.cargar_asignaturas()

            # Mostrar resumen de datos cargados
            total_asignaturas = 0
            total_franjas = 0

            for semestre, asignaturas in self.datos_configuracion["asignaturas"].items():
                total_asignaturas += len(asignaturas)
                for asig_data in asignaturas.values():
                    horarios = asig_data.get("horarios", {})
                    for dia_franjas in horarios.values():
                        total_franjas += len(dia_franjas)

            if total_asignaturas > 0:
                self.log_mensaje(
                    f"✅ Datos cargados y ordenados: {total_asignaturas} asignaturas, {total_franjas} franjas horarias",
                    "success"
                )

                # Auto-seleccionar la primera asignatura del semestre actual
                self.auto_seleccionar_primera_asignatura()
            else:
                self.log_mensaje("📝 No hay datos previos - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primera_asignatura(self):
        """Auto-selecciona la primera asignatura disponible"""
        try:
            if self.list_asignaturas.count() > 0:
                # Seleccionar primer item
                primer_item = self.list_asignaturas.item(0)
                self.list_asignaturas.setCurrentItem(primer_item)
                self.seleccionar_asignatura(primer_item)

                self.log_mensaje(f"🎯 Auto-seleccionada: {primer_item.text()}", "info")
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando asignatura: {e}", "warning")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Selector de semestre
        semestre_group = QGroupBox("📚 SELECCIÓN DE SEMESTRE")
        semestre_layout = QHBoxLayout()

        self.radio_sem1 = QPushButton("1º Cuatrimestre")
        self.radio_sem1.setCheckable(True)
        self.radio_sem2 = QPushButton("2º Cuatrimestre")
        self.radio_sem2.setCheckable(True)
        self.radio_sem1.setChecked(True)  # Por defecto

        semestre_layout.addWidget(self.radio_sem1)
        semestre_layout.addWidget(self.radio_sem2)
        semestre_layout.addStretch()

        semestre_group.setLayout(semestre_layout)
        main_layout.addWidget(semestre_group)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de asignaturas
        left_panel = QGroupBox("📋 ASIGNATURAS DEL SEMESTRE")
        left_layout = QVBoxLayout()

        # Lista de asignaturas con botones de gestión
        asignatura_header = QHBoxLayout()
        asignatura_header.addWidget(QLabel("Asignaturas:"))
        asignatura_header.addStretch()

        btn_add_asignatura = QPushButton("➕")
        btn_add_asignatura.setMinimumSize(40, 30)
        btn_add_asignatura.setMaximumSize(50, 50)
        btn_add_asignatura.setStyleSheet("""
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
        """)
        btn_add_asignatura.setToolTip("Añadir nueva asignatura")
        btn_add_asignatura.clicked.connect(self.anadir_asignatura)
        asignatura_header.addWidget(btn_add_asignatura)

        # BOTÓN EDITAR - Azul
        btn_edit_asignatura = QPushButton("✏️")
        btn_edit_asignatura.setMinimumSize(40, 30)
        btn_edit_asignatura.setMaximumSize(50, 50)
        btn_edit_asignatura.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 6px;
                background-color: #444;
                color: #2196F3;
                padding: 4px;
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
        """)
        btn_edit_asignatura.setToolTip("Editar asignatura seleccionada")
        btn_edit_asignatura.clicked.connect(self.editar_asignatura_seleccionada)
        asignatura_header.addWidget(btn_edit_asignatura)

        # BOTÓN ELIMINAR - Rojo
        btn_delete_asignatura = QPushButton("🗑️")
        btn_delete_asignatura.setMinimumSize(40, 30)
        btn_delete_asignatura.setMaximumSize(50, 50)
        btn_delete_asignatura.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 6px;
                background-color: #444;
                color: #f44336;
                padding: 4px;
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
        """)
        btn_delete_asignatura.setToolTip("Eliminar asignatura seleccionada")
        btn_delete_asignatura.clicked.connect(self.eliminar_asignatura_seleccionada)
        asignatura_header.addWidget(btn_delete_asignatura)

        left_layout.addLayout(asignatura_header)

        self.list_asignaturas = QListWidget()
        self.list_asignaturas.setMaximumWidth(300)
        left_layout.addWidget(self.list_asignaturas)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Gestión de grados
        center_panel = QGroupBox("🎓 GRADOS DE LA ASIGNATURA")
        center_layout = QVBoxLayout()

        # Asignatura seleccionada
        self.label_asignatura_grados = QLabel("Seleccione una asignatura")
        self.label_asignatura_grados.setStyleSheet("color: #4a9eff; font-weight: bold;")
        center_layout.addWidget(self.label_asignatura_grados)

        # Lista de grados con botones de gestión
        grados_header = QHBoxLayout()
        grados_header.addWidget(QLabel("Grados:"))
        grados_header.addStretch()

        btn_add_grado = QPushButton("➕")
        btn_add_grado.setMinimumSize(40, 30)
        btn_add_grado.setMaximumSize(50, 50)
        btn_add_grado.setStyleSheet("""
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
                """)
        btn_add_grado.setToolTip("Añadir nuevo grado")
        btn_add_grado.clicked.connect(self.anadir_grado)
        grados_header.addWidget(btn_add_grado)

        # Botones de gestión de grados
        btn_edit_grado = QPushButton("✏️")
        btn_edit_grado.setMinimumSize(40, 30)
        btn_edit_grado.setMaximumSize(50, 50)
        btn_edit_grado.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        border: 2px solid #666;
                        border-radius: 6px;
                        background-color: #444;
                        color: #2196F3;
                        padding: 4px;
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
                """)
        btn_edit_grado.setToolTip("Editar grado seleccionado")
        btn_edit_grado.clicked.connect(self.editar_grado_seleccionado)
        grados_header.addWidget(btn_edit_grado)

        btn_delete_grado = QPushButton("🗑️")
        btn_delete_grado.setMinimumSize(40, 30)
        btn_delete_grado.setMaximumSize(50, 50)
        btn_delete_grado.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        border: 2px solid #666;
                        border-radius: 6px;
                        background-color: #444;
                        color: #f44336;
                        padding: 4px;
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
                """)
        btn_delete_grado.setToolTip("Eliminar grado seleccionado")
        btn_delete_grado.clicked.connect(self.eliminar_grado_seleccionado)
        grados_header.addWidget(btn_delete_grado)

        center_layout.addLayout(grados_header)

        self.list_grados = QListWidget()
        self.list_grados.setMaximumWidth(250)
        center_layout.addWidget(self.list_grados)

        center_panel.setLayout(center_layout)
        content_layout.addWidget(center_panel)

        # Columna derecha - Configuración de horarios
        right_panel = QGroupBox("⚙️ CONFIGURACIÓN DE HORARIOS")
        right_layout = QVBoxLayout()

        # Asignatura seleccionada
        self.label_asignatura = QLabel("Seleccione una asignatura")
        self.label_asignatura.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(self.label_asignatura)

        # Vista calendario semanal
        calendario_group = QGroupBox("🗓️ HORARIOS DE LABORATORIO - Vista Semanal")
        calendario_layout = QVBoxLayout()

        # Encabezados de días
        dias_layout = QHBoxLayout()
        dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]

        self.columnas_dias = {}
        for dia in dias:
            columna = QVBoxLayout()

            # Encabezado del día
            header = QLabel(dia)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header.setStyleSheet("background-color: #4a4a4a; padding: 10px; border-radius: 5px;")
            columna.addWidget(header)

            # Scroll area para las franjas
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setMinimumHeight(400)

            franjas_widget = QWidget()
            franjas_layout = QVBoxLayout()
            franjas_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Botón añadir franja
            btn_add = QPushButton(f"➕ Añadir\nFranja")
            btn_add.setMinimumHeight(50)
            btn_add.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 0.3);
                    border-color: #4CAF50;
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: #45a049;
                    border-color: #3d8b40;
                }
            """)
            btn_add.clicked.connect(lambda checked, d=dia.lower().capitalize(): self.anadir_franja(d))
            franjas_layout.addWidget(btn_add)

            franjas_layout.addStretch()
            franjas_widget.setLayout(franjas_layout)
            scroll.setWidget(franjas_widget)

            columna.addWidget(scroll)
            self.columnas_dias[dia.lower().capitalize()] = franjas_layout

            dias_layout.addLayout(columna)

        calendario_layout.addLayout(dias_layout)
        calendario_group.setLayout(calendario_layout)
        right_layout.addWidget(calendario_group)

        # Botones de acción
        buttons_layout = QHBoxLayout()

        self.btn_cargar = QPushButton("📁 Cargar")
        self.btn_cargar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)

        self.btn_guardar = QPushButton("💾 Guardar Archivo")
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)

        self.btn_guardar_sistema = QPushButton("✅ Guardar en Sistema")
        self.btn_guardar_sistema.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;  /* Verde */
                        color: #ffffff;
                        border: 1px solid #45a049;
                        border-radius: 5px;
                        padding: 8px 16px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                        border-color: #3d8b40;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                    }
                """)
        self.btn_guardar_sistema.setToolTip("Guardar configuración en el sistema principal y cerrar ventana")

        self.btn_borrar_horarios = QPushButton("🗑️ Borrar Horarios")
        self.btn_borrar_horarios.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;  /* Rojo más visible */
                color: #ffffff;
                border: 1px solid #b71c1c;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f44336;
                border-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.btn_borrar_horarios.setToolTip("Borrar todos los horarios configurados (sin guardar automáticamente)")

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

    def apply_dark_theme(self):
        """Aplicar tema oscuro idéntico al sistema"""
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
            QPushButton:checked {
                background-color: #4a9eff;
                border-color: #3a8eef;
            }
            QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                min-width: 60px;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #3c3c3c;
            }
        """)

    def conectar_signals(self):
        """Conecta las señales de los widgets"""
        self.radio_sem1.clicked.connect(self.cambiar_semestre)
        self.radio_sem2.clicked.connect(self.cambiar_semestre)
        self.list_asignaturas.itemClicked.connect(self.seleccionar_asignatura)

        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        self.btn_guardar.clicked.connect(self.guardar_configuracion)
        self.btn_guardar_sistema.clicked.connect(self.guardar_en_sistema)
        self.btn_borrar_horarios.clicked.connect(self.borrar_horarios_configurados)

    def cambiar_semestre(self):
        """Cambia entre semestres y actualiza la lista de asignaturas"""
        sender = self.sender()

        # Lógica de radio buttons exclusivos
        if sender == self.radio_sem1:
            self.radio_sem2.setChecked(False)
            self.datos_configuracion["semestre_actual"] = "1"
        else:
            self.radio_sem1.setChecked(False)
            self.datos_configuracion["semestre_actual"] = "2"

        self.cargar_asignaturas()
        self.limpiar_horarios()
        self.asignatura_actual = None
        self.label_asignatura.setText("Seleccione una asignatura")
        self.label_asignatura_grados.setText("Seleccione una asignatura")
        self.list_grados.clear()
        self.marcar_cambio_realizado()

    def cargar_asignaturas(self):
        """Carga asignaturas SOLO del semestre actual desde el sistema central"""
        self.list_asignaturas.clear()

        try:
            # Obtener asignaturas desde el sistema central
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                asignaturas_sistema = self.parent_window.configuracion["configuracion"]["asignaturas"]["datos"]

                if not asignaturas_sistema:
                    item = QListWidgetItem("📭 No hay asignaturas en el sistema")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.list_asignaturas.addItem(item)
                    return

                # FILTRAR por semestre actual
                semestre_actual = self.datos_configuracion["semestre_actual"]
                semestre_texto = f"{semestre_actual}º Cuatrimestre"

                asignaturas_filtradas = []
                for codigo, datos in asignaturas_sistema.items():
                    # Solo mostrar asignaturas del semestre actual
                    if datos.get('semestre') == semestre_texto:
                        asignaturas_filtradas.append((codigo, datos))

                if not asignaturas_filtradas:
                    item = QListWidgetItem(f"📭 No hay asignaturas para {semestre_texto}")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.list_asignaturas.addItem(item)
                    return

                # Mostrar asignaturas filtradas
                for codigo, datos in sorted(asignaturas_filtradas):
                    nombre = datos.get('nombre', codigo)
                    grados = datos.get('grados_que_cursan', [])

                    texto = f"📚 {nombre} ({codigo})"
                    if grados:
                        texto += f"\n   Grados: {', '.join(grados)}"

                    item = QListWidgetItem(texto)
                    item.setData(Qt.ItemDataRole.UserRole, nombre)
                    self.list_asignaturas.addItem(item)

                self.log_mensaje(f"✅ Cargadas {len(asignaturas_filtradas)} asignaturas de {semestre_texto}", "info")
            else:
                # Fallback: usar estructura interna
                semestre = self.datos_configuracion["semestre_actual"]
                asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

                for asignatura in asignaturas.keys():
                    item = QListWidgetItem(asignatura)
                    item.setData(Qt.ItemDataRole.UserRole, asignatura)
                    self.list_asignaturas.addItem(item)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando asignaturas: {e}", "warning")

    def recargar_asignaturas_desde_sistema(self):
        """Recarga asignaturas cuando el sistema central cambia"""
        try:
            self.log_mensaje("🔄 Recargando asignaturas desde sistema central...", "info")
            self.cargar_asignaturas()

            # Si había una asignatura seleccionada, intentar mantenerla
            if self.asignatura_actual:
                self.auto_seleccionar_asignatura(self.asignatura_actual)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error recargando asignaturas: {e}", "warning")

    def anadir_asignatura(self):
        """Añade una nueva asignatura - CON AUTO-ORDENAMIENTO"""
        dialog = GestionAsignaturaDialog(parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nombre = dialog.get_nombre()
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre de la asignatura no puede estar vacío")
                return

            semestre = self.datos_configuracion["semestre_actual"]

            if nombre in self.datos_configuracion["asignaturas"][semestre]:
                QMessageBox.warning(self, "Error", "Ya existe una asignatura con ese nombre")
                return

            # Añadir nueva asignatura
            self.datos_configuracion["asignaturas"][semestre][nombre] = {
                "grados": [],
                "horarios": {}
            }

            # 🔑 AUTO-ORDENAR: Reordenar automáticamente después de añadir
            self.ordenar_asignaturas_alfabeticamente()

            self.cargar_asignaturas()
            self.marcar_cambio_realizado()

            # Auto-seleccionar la asignatura recién añadida
            self.auto_seleccionar_asignatura(nombre)

            QMessageBox.information(self, "Éxito", f"Asignatura '{nombre}' añadida correctamente")

    def editar_asignatura_directa(self, asignatura_original):
        """Edita el nombre de una asignatura - CON AUTO-ORDENAMIENTO"""
        dialog = GestionAsignaturaDialog(asignatura_original, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            nuevo_nombre = dialog.get_nombre()
            if not nuevo_nombre:
                QMessageBox.warning(self, "Error", "El nombre de la asignatura no puede estar vacío")
                return

            if nuevo_nombre == asignatura_original:
                return

            semestre = self.datos_configuracion["semestre_actual"]

            if nuevo_nombre in self.datos_configuracion["asignaturas"][semestre]:
                QMessageBox.warning(self, "Error", "Ya existe una asignatura con ese nombre")
                return

            # Renombrar asignatura
            asignaturas = self.datos_configuracion["asignaturas"][semestre]
            asignaturas[nuevo_nombre] = asignaturas.pop(asignatura_original)

            # 🔑 AUTO-ORDENAR: Reordenar después de renombrar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar asignatura actual si era la seleccionada
            if self.asignatura_actual == asignatura_original:
                self.asignatura_actual = nuevo_nombre
                self.label_asignatura.setText(f"📚 {nuevo_nombre}")
                self.label_asignatura_grados.setText(nuevo_nombre)

            self.cargar_asignaturas()

            # Auto-seleccionar la asignatura renombrada
            self.auto_seleccionar_asignatura(nuevo_nombre)

            self.marcar_cambio_realizado()
            QMessageBox.information(self, "Éxito", f"Asignatura renombrada a '{nuevo_nombre}'")

    def eliminar_asignatura(self, asignatura):
        """Elimina una asignatura completa"""
        respuesta = QMessageBox.question(
            self, "Eliminar Asignatura",
            f"¿Está seguro de eliminar la asignatura '{asignatura}'?\n\n"
            "Se perderán todos sus grados, horarios y configuración.\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            semestre = self.datos_configuracion["semestre_actual"]

            # Eliminar asignatura de los datos
            if asignatura in self.datos_configuracion["asignaturas"][semestre]:
                del self.datos_configuracion["asignaturas"][semestre][asignatura]

            # Si era la asignatura actual, limpiar selección
            if self.asignatura_actual == asignatura:
                self.asignatura_actual = None
                self.label_asignatura.setText("Seleccione una asignatura")
                self.label_asignatura_grados.setText("Seleccione una asignatura")
                self.list_grados.clear()
                self.limpiar_horarios()

            self.cargar_asignaturas()
            self.marcar_cambio_realizado()
            QMessageBox.information(self, "Éxito", f"Asignatura '{asignatura}' eliminada correctamente")

    def seleccionar_asignatura(self, item):
        """Selecciona una asignatura y carga/inicializa su configuración"""
        if not item:
            return

        # Obtener el nombre de la asignatura
        asignatura = item.data(Qt.ItemDataRole.UserRole) or item.text()
        if not asignatura:
            return

        self.asignatura_actual = asignatura
        self.label_asignatura.setText(f"📚 {self.asignatura_actual}")
        self.label_asignatura_grados.setText(self.asignatura_actual)

        # NUEVO: Inicializar estructura si no existe
        self.inicializar_estructura_asignatura()

        # Limpiar horarios anteriores
        self.limpiar_horarios()

        # Cargar configuración de la asignatura
        self.cargar_config_asignatura()

        # Cargar grados de la asignatura
        self.cargar_grados_asignatura()

        # Cargar horarios de la asignatura
        self.cargar_horarios_asignatura()

    def inicializar_estructura_asignatura(self):
        """Inicializa la estructura interna para una asignatura del sistema central"""
        if not self.asignatura_actual:
            return

        try:
            semestre = self.datos_configuracion["semestre_actual"]

            # Verificar si la asignatura ya existe en la estructura interna
            if semestre not in self.datos_configuracion["asignaturas"]:
                self.datos_configuracion["asignaturas"][semestre] = {}

            if self.asignatura_actual not in self.datos_configuracion["asignaturas"][semestre]:
                # Obtener grados desde el sistema central
                grados_sistema = self.obtener_grados_asignatura(self.asignatura_actual)

                # Crear estructura inicial
                self.datos_configuracion["asignaturas"][semestre][self.asignatura_actual] = {
                    "grados": grados_sistema.copy(),  # Copiar desde sistema central
                    "horarios": {}
                }

                self.log_mensaje(
                    f"🔧 Estructura inicializada para '{self.asignatura_actual}' con {len(grados_sistema)} grados",
                    "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error inicializando estructura: {e}", "warning")

    def cargar_grados_asignatura(self):
        """Carga los grados de la asignatura actual"""
        self.list_grados.clear()

        if not self.asignatura_actual:
            return

        grados = self.obtener_grados_asignatura(self.asignatura_actual)

        for grado in grados:
            item = QListWidgetItem(grado)
            item.setData(Qt.ItemDataRole.UserRole, grado)
            self.list_grados.addItem(item)

    def editar_asignatura_seleccionada(self):
        """Edita la asignatura seleccionada"""
        item_actual = self.list_asignaturas.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para editar")
            return

        asignatura_original = item_actual.data(Qt.ItemDataRole.UserRole) or item_actual.text()
        self.editar_asignatura_directa(asignatura_original)

    def eliminar_asignatura_seleccionada(self):
        """Elimina la asignatura seleccionada"""
        item_actual = self.list_asignaturas.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para eliminar")
            return

        asignatura = item_actual.data(Qt.ItemDataRole.UserRole) or item_actual.text()
        self.eliminar_asignatura(asignatura)

    def editar_grado_seleccionado(self):
        """Edita el grado seleccionado"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione primero una asignatura")
            return

        item_actual = self.list_grados.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grado para editar")
            return

        grado_original = item_actual.data(Qt.ItemDataRole.UserRole) or item_actual.text()
        self.editar_grado(grado_original)

    def eliminar_grado_seleccionado(self):
        """Elimina el grado seleccionado"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione primero una asignatura")
            return

        item_actual = self.list_grados.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grado para eliminar")
            return

        grado = item_actual.data(Qt.ItemDataRole.UserRole) or item_actual.text()
        self.eliminar_grado(grado)

    def editar_grado(self, grado_original):
        """Edita un grado existente - CON AUTO-ORDENAMIENTO"""
        nuevo_grado, ok = QInputDialog.getText(
            self, "Editar Grado",
            f"Editar código del grado:",
            text=grado_original
        )

        if ok and nuevo_grado.strip():
            nuevo_grado = nuevo_grado.strip().upper()

            if nuevo_grado == grado_original:
                return

            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"][semestre]
            grados_list = asignaturas[self.asignatura_actual]["grados"]

            if nuevo_grado in grados_list:
                QMessageBox.warning(self, "Error", "Este grado ya existe en la asignatura")
                return

            # Reemplazar grado
            try:
                index = grados_list.index(grado_original)
                grados_list[index] = nuevo_grado

                # 🔑 AUTO-ORDENAR: Reordenar después de editar
                grados_list.sort()

                self.cargar_grados_asignatura()

                # Auto-seleccionar el grado editado
                self.auto_seleccionar_grado(nuevo_grado)

                self.marcar_cambio_realizado()
                QMessageBox.information(self, "Éxito", f"Grado actualizado: {grado_original} → {nuevo_grado}")
            except ValueError:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el grado original")

    def eliminar_grado(self, grado):
        """Elimina un grado de la asignatura actual"""
        respuesta = QMessageBox.question(
            self, "Eliminar Grado",
            f"¿Está seguro de eliminar el grado '{grado}' de la asignatura '{self.asignatura_actual}'?\n\n"
            "También se eliminarán todas sus franjas horarias asociadas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"][semestre]

            # Eliminar grado de la lista
            if grado in asignaturas[self.asignatura_actual]["grados"]:
                asignaturas[self.asignatura_actual]["grados"].remove(grado)

            # Eliminar grado de todas las franjas horarias
            horarios = asignaturas[self.asignatura_actual].get("horarios", {})
            for dia, franjas in horarios.items():
                for franja in franjas:
                    if grado in franja["grados"]:
                        franja["grados"].remove(grado)

            # Recargar interfaz
            self.cargar_grados_asignatura()
            self.cargar_horarios_asignatura()
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Grado '{grado}' eliminado correctamente")

    def anadir_grado(self):
        """Añade un nuevo grado - CON INICIALIZACIÓN SEGURA"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione primero una asignatura")
            return

        # NUEVO: Asegurar que la estructura existe
        self.inicializar_estructura_asignatura()

        grado, ok = QInputDialog.getText(self, "Nuevo Grado", "Código del grado (ej: A302, EE309):")

        if ok and grado.strip():
            grado = grado.strip().upper()

            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"][semestre]

            if grado not in asignaturas[self.asignatura_actual]["grados"]:
                asignaturas[self.asignatura_actual]["grados"].append(grado)
                asignaturas[self.asignatura_actual]["grados"].sort()

                self.cargar_grados_asignatura()
                self.auto_seleccionar_grado(grado)
                self.marcar_cambio_realizado()
                QMessageBox.information(self, "Éxito", f"Grado '{grado}' añadido correctamente")
            else:
                QMessageBox.warning(self, "Error", "Este grado ya existe en la asignatura")

    def obtener_asignaturas_del_sistema(self):
        if self.parent_window:
            return self.parent_window.configuracion["configuracion"]["asignaturas"]["datos"]
        return {}

    def obtener_grados_asignatura(self, asignatura):
        """Obtiene grados desde el sistema central de asignaturas"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                asignaturas_sistema = self.parent_window.configuracion["configuracion"]["asignaturas"]["datos"]

                # Buscar por nombre o código de asignatura
                for codigo, datos in asignaturas_sistema.items():
                    if datos.get('nombre') == asignatura or codigo == asignatura:
                        return datos.get('grados_que_cursan', [])

                self.log_mensaje(f"⚠️ Asignatura '{asignatura}' no encontrada en sistema central", "warning")
                return []
            return []
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo grados: {e}", "warning")
            return []

    def cargar_config_asignatura(self):
        """Carga la configuración específica de una asignatura - SIMPLIFICADO"""
        if not self.asignatura_actual:
            return

        # Ya no hay configuración específica de asignatura que cargar
        # Solo se mantiene la estructura para compatibilidad futura
        pass

    def guardar_config_asignatura(self):
        """Guarda la configuración básica de la asignatura actual - SIMPLIFICADO"""
        if not self.asignatura_actual:
            return

        # Ya no hay configuración específica de asignatura que guardar
        # Solo se mantiene la estructura para compatibilidad futura
        pass

    def cargar_horarios_asignatura(self):
        """Carga los horarios configurados para la asignatura actual"""
        if not self.asignatura_actual:
            return

        try:
            semestre = self.datos_configuracion["semestre_actual"]
            asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

            # Si la asignatura existe en la estructura interna, cargar sus horarios
            if self.asignatura_actual in asignaturas:
                horarios = asignaturas[self.asignatura_actual].get("horarios", {})

                # Cargar franjas existentes
                total_franjas = 0
                for dia, franjas in horarios.items():
                    if dia in self.columnas_dias:
                        for franja_data in franjas:
                            self.crear_franja_widget(
                                dia,
                                franja_data["hora_inicio"],
                                franja_data["hora_fin"],
                                franja_data["grados"],
                                franja_data.get("id", self.generar_id_franja())
                            )
                            total_franjas += 1

                if total_franjas > 0:
                    self.log_mensaje(f"✅ Cargadas {total_franjas} franjas horarias para '{self.asignatura_actual}'",
                                     "info")
                else:
                    self.log_mensaje(f"📝 No hay horarios previos para '{self.asignatura_actual}'", "info")
            else:
                self.log_mensaje(f"⚠️ Asignatura '{self.asignatura_actual}' no encontrada en estructura interna",
                                 "warning")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando horarios: {e}", "warning")

    def generar_id_franja(self):
        """Genera un ID único para una franja"""
        self.contador_franjas += 1
        return f"franja_{self.contador_franjas}"

    def anadir_franja(self, dia):
        """Abre dialog para añadir nueva franja horaria"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione primero una asignatura")
            return

        dialog = AnadirFranjaDialog(self.asignatura_actual, self)
        dialog.combo_dia.setCurrentText(dia)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Obtener datos del dialog
            datos_franja = dialog.get_datos_franja()

            # MODIFICACIÓN: Usar las horas tal como las configuró el usuario
            hora_inicio = datos_franja['hora_inicio']
            hora_fin = datos_franja['hora_fin']
            grados_seleccionados = datos_franja['grados']

            # Crear franja y manejar solapamientos
            self.procesar_nueva_franja(dia, hora_inicio, hora_fin, grados_seleccionados)

    def tiempo_a_minutos(self, hora_str):
        """Convierte una hora en formato HH:MM a minutos desde medianoche"""
        h, m = map(int, hora_str.split(':'))
        return h * 60 + m

    def minutos_a_tiempo(self, minutos):
        """Convierte minutos desde medianoche a formato HH:MM"""
        h = minutos // 60
        m = minutos % 60
        return f"{h:02d}:{m:02d}"

    def procesar_nueva_franja(self, dia, hora_inicio, hora_fin, grados):
        """Procesa nueva franja manejando solapamientos automáticamente"""
        # NUEVO: Asegurar que la estructura existe
        self.inicializar_estructura_asignatura()

        inicio_minutos = self.tiempo_a_minutos(hora_inicio)
        fin_minutos = self.tiempo_a_minutos(hora_fin)

        # Obtener franjas existentes para este día y asignatura
        semestre = self.datos_configuracion["semestre_actual"]
        asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

        # VERIFICAR que la asignatura existe
        if self.asignatura_actual not in asignaturas:
            self.log_mensaje(f"⚠️ Inicializando estructura para {self.asignatura_actual}", "warning")
            self.inicializar_estructura_asignatura()
            asignaturas = self.datos_configuracion["asignaturas"][semestre]

        horarios_dia = asignaturas.get(self.asignatura_actual, {}).get("horarios", {}).get(dia, [])

        # Convertir a formato de trabajo (minutos)
        franjas_existentes = []
        for franja in horarios_dia:
            franjas_existentes.append({
                'id': franja['id'],
                'inicio': self.tiempo_a_minutos(franja['hora_inicio']),
                'fin': self.tiempo_a_minutos(franja['hora_fin']),
                'grados': set(franja['grados'])
            })

        # Procesar solapamientos
        nueva_franja = {
            'id': self.generar_id_franja(),
            'inicio': inicio_minutos,
            'fin': fin_minutos,
            'grados': set(grados)
        }

        franjas_finales = self.fusionar_franjas(franjas_existentes, nueva_franja)

        # Limpiar widgets del día
        self.limpiar_horarios_dia(dia)

        # Actualizar datos
        asignaturas[self.asignatura_actual]["horarios"][dia] = []

        # Crear nuevos widgets y guardar datos
        for franja in franjas_finales:
            hora_inicio_str = self.minutos_a_tiempo(franja['inicio'])
            hora_fin_str = self.minutos_a_tiempo(franja['fin'])
            grados_list = list(franja['grados'])

            self.crear_franja_widget(dia, hora_inicio_str, hora_fin_str, grados_list, franja['id'])
            self.guardar_franja_en_datos(dia, franja['id'], hora_inicio_str, hora_fin_str, grados_list)

        # Marcar que se han realizado cambios
        self.marcar_cambio_realizado()

    def fusionar_franjas(self, franjas_existentes, nueva_franja):
        """Fusiona las franjas manejando solapamientos"""
        todas_franjas = franjas_existentes + [nueva_franja]

        # Crear eventos de inicio y fin
        eventos = []
        for i, franja in enumerate(todas_franjas):
            eventos.append((franja['inicio'], 'inicio', i, franja))
            eventos.append((franja['fin'], 'fin', i, franja))

        # Ordenar eventos por tiempo
        eventos.sort(key=lambda x: (x[0], x[1] == 'fin'))  # Priorizar inicio sobre fin en empates

        # Procesar eventos para crear franjas fusionadas
        franjas_activas = []  # Usar lista en lugar de set
        franjas_resultado = []
        tiempo_anterior = None

        for tiempo, tipo, indice, franja in eventos:
            # Si hay un gap de tiempo y hay franjas activas, crear franja resultado
            if tiempo_anterior is not None and tiempo > tiempo_anterior and franjas_activas:
                grados_combinados = set()
                for f_activa in franjas_activas:
                    grados_combinados.update(f_activa['grados'])

                franjas_resultado.append({
                    'id': self.generar_id_franja(),
                    'inicio': tiempo_anterior,
                    'fin': tiempo,
                    'grados': grados_combinados
                })

            # Actualizar franjas activas
            if tipo == 'inicio':
                franjas_activas.append(franja)
            else:
                # Eliminar franja específica de la lista
                franjas_activas = [f for f in franjas_activas if f['id'] != franja['id']]

            tiempo_anterior = tiempo

        return franjas_resultado

    def limpiar_horarios_dia(self, dia):
        """Limpia los horarios de un día específico"""
        widgets = self.franjas_widgets[dia].copy()
        for widget in widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.franjas_widgets[dia].clear()

    def crear_franja_widget(self, dia, hora_inicio, hora_fin, grados, franja_id):
        """Crea y añade un widget de franja al calendario"""
        franja_widget = FranjaWidget(franja_id, hora_inicio, hora_fin, grados, self)

        # Conectar señales
        franja_widget.eliminado.connect(self.eliminar_franja_widget)
        franja_widget.editado.connect(self.editar_franja_widget)

        # Insertar antes del botón "Añadir" y el stretch
        layout = self.columnas_dias[dia]
        layout.insertWidget(layout.count() - 2, franja_widget)

        # Guardar referencia
        self.franjas_widgets[dia].append(franja_widget)

    def guardar_franja_en_datos(self, dia, franja_id, hora_inicio, hora_fin, grados):
        """Guarda una franja en la estructura de datos"""
        if not self.asignatura_actual:
            return

        semestre = self.datos_configuracion["semestre_actual"]
        asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

        if self.asignatura_actual not in asignaturas:
            return

        # Inicializar horarios si no existen
        if "horarios" not in asignaturas[self.asignatura_actual]:
            asignaturas[self.asignatura_actual]["horarios"] = {}

        if dia not in asignaturas[self.asignatura_actual]["horarios"]:
            asignaturas[self.asignatura_actual]["horarios"][dia] = []

        # Añadir franja
        franja_data = {
            "id": franja_id,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "grados": grados.copy()
        }

        asignaturas[self.asignatura_actual]["horarios"][dia].append(franja_data)

    def eliminar_franja_widget(self, franja_widget):
        """Elimina un widget de franja del calendario y de los datos"""
        # Eliminar de los datos
        self.eliminar_franja_de_datos(franja_widget.franja_id)

        # Eliminar de la lista de widgets
        for dia, widgets in self.franjas_widgets.items():
            if franja_widget in widgets:
                widgets.remove(franja_widget)
                break

        # Eliminar del layout
        franja_widget.setParent(None)
        franja_widget.deleteLater()

        # MArcar que se han realizado cambios
        self.marcar_cambio_realizado()

    def eliminar_franja_de_datos(self, franja_id):
        """Elimina una franja de la estructura de datos"""
        if not self.asignatura_actual:
            return

        semestre = self.datos_configuracion["semestre_actual"]
        asignaturas = self.datos_configuracion["asignaturas"].get(semestre, {})

        if self.asignatura_actual not in asignaturas:
            return

        horarios = asignaturas[self.asignatura_actual].get("horarios", {})

        for dia, franjas in horarios.items():
            franjas[:] = [f for f in franjas if f.get("id") != franja_id]

    def editar_franja_widget(self, franja_widget):
        """Edita una franja existente - IMPLEMENTACIÓN COMPLETA"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Error", "No hay asignatura seleccionada")
            return

        # Crear diálogo de edición usando el mismo diálogo pero en modo edición
        dialog = AnadirFranjaDialog(self.asignatura_actual, self, franja_widget)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Obtener nuevos datos
            datos_nuevos = dialog.get_datos_franja()

            # Obtener día original de la franja
            dia_original = None
            for dia, widgets in self.franjas_widgets.items():
                if franja_widget in widgets:
                    dia_original = dia
                    break

            if not dia_original:
                QMessageBox.warning(self, "Error", "No se pudo determinar el día de la franja")
                return

            # Eliminar franja original
            self.eliminar_franja_widget(franja_widget)

            # Crear nueva franja con los datos actualizados
            dia_nuevo = datos_nuevos['dia']
            self.procesar_nueva_franja(
                dia_nuevo,
                datos_nuevos['hora_inicio'],
                datos_nuevos['hora_fin'],
                datos_nuevos['grados']
            )

            # Mostrar mensaje de confirmación
            mensaje = f"Franja editada correctamente:\n"
            mensaje += f"• Horario: {datos_nuevos['hora_inicio']} - {datos_nuevos['hora_fin']}\n"
            mensaje += f"• Día: {dia_nuevo}\n"
            mensaje += f"• Grados: {', '.join(datos_nuevos['grados'])}"

            QMessageBox.information(self, "Franja Actualizada", mensaje)

    def limpiar_horarios(self):
        """Limpia todos los horarios del calendario"""
        for dia, widgets in self.franjas_widgets.items():
            for widget in widgets:
                widget.setParent(None)
                widget.deleteLater()
            widgets.clear()

    def cargar_configuracion(self):
        """Carga configuración desde archivo JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Horarios",
            "", "Archivos JSON (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    datos_cargados = json.load(f)

                # Validar estructura básica
                if "asignaturas" not in datos_cargados:
                    raise ValueError("Archivo JSON inválido: falta 'asignaturas'")

                # Cargar datos
                self.datos_configuracion = datos_cargados

                # 🔑 ORDENAR TODO AL CARGAR DESDE ARCHIVO
                self.ordenar_asignaturas_alfabeticamente()

                # Actualizar interfaz
                semestre = self.datos_configuracion.get("semestre_actual", "2")
                if semestre == "1":
                    self.radio_sem1.setChecked(True)
                    self.radio_sem2.setChecked(False)
                else:
                    self.radio_sem1.setChecked(False)
                    self.radio_sem2.setChecked(True)

                self.cargar_asignaturas()
                self.limpiar_horarios()
                self.asignatura_actual = None
                self.label_asignatura.setText("Seleccione una asignatura")
                self.label_asignatura_grados.setText("Seleccione una asignatura")
                self.list_grados.clear()

                QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def guardar_configuracion(self):
        """Guarda configuración actual en archivo JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Horarios",
            f"horarios_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )

        if file_path:
            try:
                # Guardar configuración actual de la asignatura
                if self.asignatura_actual:
                    self.guardar_config_asignatura()

                # Añadir metadatos
                config_data = self.datos_configuracion.copy()
                config_data["metadata"] = {
                    "version": "1.0",
                    "timestamp": datetime.now().isoformat(),
                    "asignatura_actual": self.asignatura_actual,
                    "generado_por": "OPTIM Labs - Configurar Horarios"
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "Éxito", f"Configuración guardada correctamente en:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar configuración:\n{str(e)}")

    def guardar_en_sistema(self):
        """Guarda la configuración en el sistema principal y cierra la ventana"""
        try:
            # Verificar que hay datos para guardar
            if not self.datos_configuracion["asignaturas"]:
                QMessageBox.warning(
                    self, "Sin datos",
                    "No hay asignaturas configuradas para guardar."
                )
                return

            # Contar asignaturas y franjas
            total_asignaturas = 0
            total_franjas = 0

            for semestre, asignaturas in self.datos_configuracion["asignaturas"].items():
                total_asignaturas += len(asignaturas)
                for asig_data in asignaturas.values():
                    horarios = asig_data.get("horarios", {})
                    for dia_franjas in horarios.values():
                        total_franjas += len(dia_franjas)

            # UNA SOLA CONFIRMACIÓN
            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• {total_asignaturas} asignaturas configuradas\n"
                f"• {total_franjas} franjas horarias totales\n\n"
                f"La configuración se integrará con OPTIM y la ventana se cerrará.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Preparar datos para enviar al sistema principal
                datos_para_sistema = {
                    "semestre_actual": self.datos_configuracion["semestre_actual"],
                    "asignaturas": self.datos_configuracion["asignaturas"],
                    "metadata": {
                        "total_asignaturas": total_asignaturas,
                        "total_franjas": total_franjas,
                        "timestamp": datetime.now().isoformat(),
                        "origen": "ConfigurarHorarios"
                    }
                }

                # Enviar señal al sistema principal (SILENCIOSO - sin más diálogos)
                self.configuracion_actualizada.emit(datos_para_sistema)

                # Marcar como guardado para evitar preguntas al cerrar
                self.datos_guardados_en_sistema = True
                self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)

                # Cerrar directamente SIN MÁS MENSAJES
                self.close()

        except Exception as e:
            QMessageBox.critical(
                self, "❌ Error",
                f"Error al guardar en el sistema:\n{str(e)}"
            )

    def borrar_horarios_configurados(self):
        """Borra todos los horarios configurados SIN guardar automáticamente"""
        respuesta = QMessageBox.question(
            self, "Borrar Horarios",
            "¿Está seguro de que desea borrar todos los horarios configurados?\n\n"
            "⚠️ Se eliminarán todas las franjas horarias de todas las asignaturas.\n"
            "💡 Los cambios NO se guardarán automáticamente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Por defecto NO borrar
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            # Limpiar horarios de todas las asignaturas
            for semestre in self.datos_configuracion["asignaturas"]:
                for asignatura in self.datos_configuracion["asignaturas"][semestre]:
                    self.datos_configuracion["asignaturas"][semestre][asignatura]["horarios"] = {}

            # Limpiar interfaz visual
            self.limpiar_horarios()
            self.list_asignaturas.setCurrentRow(-1)
            self.list_grados.clear()
            self.asignatura_actual = None
            self.label_asignatura.setText("Seleccione una asignatura")
            self.label_asignatura_grados.setText("Seleccione una asignatura")

            # 🔑 MARCAR COMO CAMBIO SIN GUARDAR
            self.marcar_cambio_realizado()

            # Mostrar confirmación
            QMessageBox.information(
                self, "Horarios Borrados",
                "✅ Todos los horarios han sido borrados.\n\n"
                "💡 Recuerda usar 'Guardar en Sistema' para aplicar los cambios permanentemente."
            )

            self.log_mensaje("🗑️ Horarios borrados (cambios sin guardar)", "warning")

    def log_mensaje(self, mensaje, tipo="info"):
        """Método simple de logging para la ventana de horarios"""
        # Si la ventana padre tiene logging, usarlo
        if self.parent_window and hasattr(self.parent_window, 'log_mensaje'):
            self.parent_window.log_mensaje(mensaje, tipo)
        else:
            # Sino, imprimir en consola
            iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            icono = iconos.get(tipo, "ℹ️")
            print(f"{icono} {mensaje}")

    def hay_cambios_sin_guardar(self):
        """Detecta si hay cambios sin guardar"""
        datos_actuales = json.dumps(self.datos_configuracion, sort_keys=True)
        hay_cambios = datos_actuales != self.datos_iniciales

        # Si hay cambios y no se han guardado en sistema, hay cambios pendientes
        if hay_cambios and not self.datos_guardados_en_sistema:
            return True

        # Si había datos guardados pero ahora hay cambios, también hay pendientes
        if self.datos_guardados_en_sistema and hay_cambios:
            return True

        return False

    def marcar_cambio_realizado(self):
        """Marcar que se hizo un cambio (llamar desde métodos que modifican datos)"""
        # Actualizar el snapshot de datos guardados si es necesario
        self.datos_guardados_en_sistema = False

    def closeEvent(self, event):
        """Manejar el cierre de la ventana - SOLO pregunta si hay cambios sin guardar"""

        # Si no hay cambios pendientes, cerrar directamente
        if not self.hay_cambios_sin_guardar():
            self.log_mensaje("🔚 Cerrando configuración de horarios", "info")
            event.accept()
            return

        # Solo preguntar si HAY cambios sin guardar
        respuesta = QMessageBox.question(
            self, "Cambios sin Guardar",
            "Hay cambios sin guardar en la configuración.\n\n"
            "¿Cerrar sin guardar?\n\n"
            "💡 Tip: Usa 'Guardar en Sistema' para conservar los cambios.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Por defecto NO cerrar
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.cancelar_cambios_en_sistema()
            self.log_mensaje("🔚 Cerrando sin guardar cambios - datos restablecidos", "warning")
            event.accept()
        else:
            event.ignore()

    def cancelar_cambios_en_sistema(self):
        """Cancela los cambios enviando datos originales al sistema principal"""
        try:
            # Restaurar desde el snapshot inicial
            datos_originales = json.loads(self.datos_iniciales)

            # Preparar datos originales con metadata de cancelación
            datos_para_sistema = {
                "semestre_actual": datos_originales["semestre_actual"],
                "asignaturas": datos_originales["asignaturas"],
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",  # ← IMPORTANTE: Indica cancelación
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarHorarios",
                    "cambios_descartados": True,
                    "restaurar_estado_original": True
                }
            }

            # 🔑 CLAVE: ENVIAR SEÑAL CON DATOS ORIGINALES
            self.configuracion_actualizada.emit(datos_para_sistema)

            # Solo ahora restaurar datos locales
            self.datos_configuracion = datos_originales
            self.datos_guardados_en_sistema = False  # NO marcar como guardado
            self.datos_iniciales = json.dumps(datos_originales, sort_keys=True)

            self.log_mensaje("📤 Señal de cancelación enviada al sistema principal", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cancelando cambios: {e}", "warning")

            # Fallback: enviar señal con datos vacíos
            datos_vacios = {
                "semestre_actual": "1",
                "asignaturas": {"1": {}, "2": {}},
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "error_restauracion": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            self.configuracion_actualizada.emit(datos_vacios)

    def ordenar_asignaturas_alfabeticamente(self):
        """Reordena todas las asignaturas alfabéticamente manteniendo datos"""
        for semestre in ["1", "2"]:
            if semestre in self.datos_configuracion["asignaturas"]:
                # Obtener diccionario actual
                asignaturas_dict = self.datos_configuracion["asignaturas"][semestre]

                # Crear nuevo diccionario ordenado
                asignaturas_ordenadas = {}
                for nombre in sorted(asignaturas_dict.keys()):
                    asignaturas_ordenadas[nombre] = asignaturas_dict[nombre]

                    # También ordenar grados dentro de cada asignatura
                    if "grados" in asignaturas_ordenadas[nombre]:
                        asignaturas_ordenadas[nombre]["grados"].sort()

                self.datos_configuracion["asignaturas"][semestre] = asignaturas_ordenadas

    def auto_seleccionar_asignatura(self, nombre_asignatura):
        """Auto-selecciona una asignatura por nombre"""
        try:
            for i in range(self.list_asignaturas.count()):
                item = self.list_asignaturas.item(i)
                if item.text() == nombre_asignatura:
                    self.list_asignaturas.setCurrentItem(item)
                    self.seleccionar_asignatura(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando asignatura: {e}", "warning")

    def auto_seleccionar_grado(self, codigo_grado):
        """Auto-selecciona un grado por código"""
        try:
            for i in range(self.list_grados.count()):
                item = self.list_grados.item(i)
                if item.text() == codigo_grado:
                    self.list_grados.setCurrentItem(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando grado: {e}", "warning")





def main():
    app = QApplication(sys.argv)

    # Aplicar tema oscuro a nivel de aplicación
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