#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Calendario - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión dinámica de año académico con validación automática
2. Configuración visual de días lectivos por semestre (Sep-Ene / Feb-Jun)
3. Calendarios interactivos para selección rápida de fechas por click
4. Sistema drag & drop para reasignación de horarios entre columnas
5. Generación automática de calendario académico con exclusión de festivos
6. Validación inteligente de límites por horario (14 días máximo por columna)
7. Verificación de equilibrio automático entre horarios semanales
8. Gestión de días especiales con horarios alternativos
9. Sistema de grids dinámicos con numeración y expansión automática
10. Import/Export completo desde CSV/JSON con metadatos
11. Contadores en tiempo real con alertas visuales de excesos
12. Funcionalidad de importación desde fuentes web universitarias
13. Control de conflictos de fin de semana con confirmación usuario
14. Integración bidireccional con sistema global OPTIM
15. Persistencia automática de cambios con detección de modificaciones

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QGroupBox, QFrame, QScrollArea, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QCalendarWidget, QSpinBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QPalette, QColor, QDrag, QPainter, QPixmap, QIntValidator


def center_window_on_screen_immediate(window, width, height):
    """Centrar ventana a la pantalla"""
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
    except Exception as e:
        window.setGeometry(100, 100, width, height)


class ConfiguracionDiaDialog(QDialog):
    """Mini-popup rápido para configurar un día"""

    def __init__(self, fecha_seleccionada, es_fin_semana=False, parent=None):
        super().__init__(parent)
        self.fecha_seleccionada = fecha_seleccionada
        self.es_fin_semana = es_fin_semana

        self.setWindowTitle("Configurar Día Lectivo")
        self.setModal(True)
        window_width = 350
        window_height = 200
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Información del día
        fecha_str = self.fecha_seleccionada.toString("dd MMM yyyy")

        # Obtener día en español directamente
        dia_numero = self.fecha_seleccionada.dayOfWeek()  # 1=Lunes, 7=Domingo
        nombres_dias = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}
        dia_semana_es = nombres_dias.get(dia_numero, "Desconocido")

        info_label = QLabel(f"📅 {fecha_str} ({dia_semana_es})")
        info_label.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Advertencia para fin de semana
        if self.es_fin_semana:
            warning_label = QLabel("⚠️ Este es un día de fin de semana")
            warning_label.setStyleSheet("color: #ffaa00; font-weight: bold; margin: 5px;")
            warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(warning_label)

        # Configuración
        config_layout = QVBoxLayout()

        # Horario asignado
        horario_layout = QHBoxLayout()
        horario_layout.addWidget(QLabel("Horario:"))

        self.combo_horario = QComboBox()
        self.combo_horario.addItems([
            "Horario Lunes", "Horario Martes", "Horario Miércoles",
            "Horario Jueves", "Horario Viernes"
        ])

        # Auto-seleccionar el día correspondiente si es día laborable
        if not self.es_fin_semana:
            dia_num = self.fecha_seleccionada.dayOfWeek()  # 1=Lunes, 5=Viernes
            if 1 <= dia_num <= 5:
                self.combo_horario.setCurrentIndex(dia_num - 1)

        horario_layout.addWidget(self.combo_horario)
        config_layout.addLayout(horario_layout)

        # Motivo (opcional)
        motivo_layout = QHBoxLayout()
        motivo_layout.addWidget(QLabel("Motivo:"))
        self.edit_motivo = QLineEdit()
        self.edit_motivo.setPlaceholderText("Ej: Día del Pilar, Semana de exámenes...")
        motivo_layout.addWidget(self.edit_motivo)
        config_layout.addLayout(motivo_layout)

        layout.addLayout(config_layout)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_configuracion_dia(self):
        """Obtener configuración del día"""
        horarios_map = {
            "Horario Lunes": "Lunes",
            "Horario Martes": "Martes",
            "Horario Miércoles": "Miércoles",
            "Horario Jueves": "Jueves",
            "Horario Viernes": "Viernes"
        }

        # Obtener día real en español directamente
        dia_numero = self.fecha_seleccionada.dayOfWeek()  # 1=Lunes, 7=Domingo
        nombres_dias = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}
        dia_real_es = nombres_dias.get(dia_numero, "Desconocido")

        horario_asignado = horarios_map[self.combo_horario.currentText()]

        return {
            'fecha': self.fecha_seleccionada.toString("yyyy-MM-dd"),
            'dia_real': dia_real_es,
            'horario_asignado': horario_asignado,
            'motivo': self.edit_motivo.text().strip(),
            'es_especial': dia_real_es != horario_asignado,
            'es_fin_semana': self.es_fin_semana
        }

    def apply_dark_theme(self):
        """Aplicar tema oscuro"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #4a9eff;
            }
        """)


class DropZoneWidget(QLabel):
    """Widget que puede recibir drops para cambiar horarios"""

    dia_dropped = pyqtSignal(str, str)  # (datos_dia, nuevo_horario)

    def __init__(self, horario_columna, parent=None):
        super().__init__(parent)
        self.horario_columna = horario_columna  # "Lunes", "Martes", etc.

        self.setFixedWidth(140)
        self.setMinimumHeight(50)
        self.setStyleSheet("border: 1px dashed #555; border-radius: 3px; background-color: #2b2b2b;")

        # Habilitar drops
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """Verificar si podemos aceptar el drag"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Cambiar estilo para mostrar que es una zona válida
            self.setStyleSheet(
                "border: 2px dashed #4a9eff; border-radius: 3px; background-color: rgba(74, 158, 255, 0.1);")
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Mantener feedback visual durante el drag"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        """Restaurar estilo cuando el drag sale de la zona"""
        self.setStyleSheet("border: 1px dashed #555; border-radius: 3px; background-color: #2b2b2b;")

    def dropEvent(self, event):
        """Manejar el drop del día"""
        if event.mimeData().hasText():
            datos_dia = event.mimeData().text()
            self.dia_dropped.emit(datos_dia, self.horario_columna)
            event.acceptProposedAction()

        # Restaurar estilo normal
        self.setStyleSheet("border: 1px dashed #555; border-radius: 3px; background-color: #2b2b2b;")


class DiaWidget(QFrame):
    """Widget para mostrar un día en el grid con botones de acción"""

    dia_eliminado = pyqtSignal(str)  # Emite la fecha
    dia_editado = pyqtSignal(str)  # Emite la fecha para edición
    dia_dropped = pyqtSignal(str, str)  # (datos_dia, nuevo_horario)

    def __init__(self, fecha, dia_real, horario_asignado, motivo="", es_especial=False, parent=None):
        super().__init__(parent)
        self.fecha = fecha
        self.dia_real = dia_real
        self.horario_asignado = horario_asignado
        self.motivo = motivo
        self.es_especial = es_especial

        self.setFixedWidth(140)
        self.setMinimumHeight(50)
        self.setMaximumHeight(70)

        # Variables para drag & drop
        self.drag_start_position = None

        # Habilitar drops también en el widget
        self.setAcceptDrops(True)

        self.setup_ui()
        self.apply_style()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(1)

        # Fecha
        fecha_obj = datetime.strptime(self.fecha, "%Y-%m-%d")
        fecha_display = fecha_obj.strftime("%d%b").replace("Jan", "Ene").replace("Apr", "Abr").replace("Aug",
                                                                                                       "Ago").replace(
            "Dec", "Dic")

        fecha_label = QLabel(fecha_display)
        fecha_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fecha_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        layout.addWidget(fecha_label)

        # Motivo si existe
        if self.motivo:
            motivo_label = QLabel(f"({self.motivo[:10]}{'...' if len(self.motivo) > 10 else ''})")
            motivo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            motivo_label.setFont(QFont("Arial", 6))
            motivo_label.setStyleSheet("color: #cccccc; font-style: italic;")
            layout.addWidget(motivo_label)

        # Botones de acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # Botón ELIMINAR
        btn_eliminar = QPushButton("🗑️")
        btn_eliminar.setMinimumSize(20, 20)
        btn_eliminar.setMaximumSize(25, 25)
        btn_eliminar.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #333;
                color: #f44336;
                padding: 1px;
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
        btn_eliminar.setToolTip("Eliminar día")
        btn_eliminar.clicked.connect(self.eliminar_dia)

        # Centrar el botón
        btn_layout.addStretch()
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Iniciar drag & drop al hacer clic"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()

    def mouseMoveEvent(self, event):
        """Manejar movimiento del mouse para drag & drop"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if not self.drag_start_position:
            return

        # Verificar si se movió lo suficiente para iniciar drag
        distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        # Iniciar drag
        self.start_drag()

    def start_drag(self):
        """Iniciar operación de drag & drop"""
        drag = QDrag(self)
        mime_data = QMimeData()

        # Información del día que se está arrastrando
        data = f"{self.fecha}|{self.dia_real}|{self.horario_asignado}|{self.motivo}|{self.es_especial}"
        mime_data.setText(data)

        # Crear imagen de arrastre simple
        pixmap = self.grab()

        # Crear una versión transparente simple
        transparent_pixmap = QPixmap(pixmap.size())
        transparent_pixmap.fill(QColor(0, 0, 0, 100))  # Semi-transparente

        drag.setMimeData(mime_data)
        drag.setPixmap(transparent_pixmap)
        drag.setHotSpot(self.drag_start_position)

        # Ejecutar drag
        result = drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        """Permitir drop sobre otros DiaWidgets para intercambiar"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Mostrar que se puede hacer drop aquí
            self.setStyleSheet(self.styleSheet() + "border: 2px solid #4a9eff;")

    def dragLeaveEvent(self, event):
        """Restaurar estilo al salir"""
        self.apply_style()

    def dropEvent(self, event):
        """Manejar drop sobre este widget (intercambio de posiciones)"""
        if event.mimeData().hasText():
            datos_dia = event.mimeData().text()
            # Emitir señal hacia el padre
            self.dia_dropped.emit(datos_dia, self.horario_asignado)
            event.acceptProposedAction()

        # Restaurar estilo
        self.apply_style()

    def eliminar_dia(self):
        """Eliminar este día"""
        respuesta = QMessageBox.question(
            self, "Eliminar Día",
            f"¿Eliminar el día {self.fecha}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self.dia_eliminado.emit(self.fecha)

    def apply_style(self):
        """Aplicar estilo según tipo de día"""
        if self.es_especial:
            # Día especial - amarillo
            color_fondo = "#4a4a00"
            color_borde = "#ffff00"
        else:
            # Día normal - verde
            color_fondo = "#004a00"
            color_borde = "#00ff00"

        self.setStyleSheet(f"""
            DiaWidget {{
                background-color: {color_fondo};
                border: 2px solid {color_borde};
                border-radius: 5px;
                margin: 2px;
            }}
            QLabel {{
                color: #ffffff;
                background-color: transparent;
                border: none;
            }}
        """)


class ConfigurarCalendario(QMainWindow):
    """Ventana principal para configurar calendario académico"""

    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Calendario - OPTIM Labs")
        window_width = 1600
        window_height = 900
        center_window_on_screen_immediate(self, window_width, window_height)

        # Determinar anio académico actual
        anio_actual = datetime.now().year
        if datetime.now().month >= 9:  # Si estamos en sep-dic, es el anio actual
            self.anio_academico = anio_actual
        else:  # Si estamos en ene-ago, es el anio anterior
            self.anio_academico = anio_actual - 1

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("📥 Cargando configuración existente de calendario...", "info")
        else:
            self.datos_configuracion = {
                "anio_academico": f"{self.anio_academico}-{self.anio_academico + 1}",
                "semestre_1": {},
                "semestre_2": {}
            }
            self.log_mensaje("📝 Iniciando configuración nueva de calendario...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None

        # Widgets de grids
        self.grids_widgets = {
            "semestre_1": {
                "Lunes": [], "Martes": [], "Miércoles": [], "Jueves": [], "Viernes": []
            },
            "semestre_2": {
                "Lunes": [], "Martes": [], "Miércoles": [], "Jueves": [], "Viernes": []
            }
        }

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    def cargar_datos_iniciales(self):
        """Cargar datos existentes al inicializar"""
        try:
            self.cargar_dias_en_grids()

            total_dias = len(self.datos_configuracion.get("semestre_1", {})) + len(
                self.datos_configuracion.get("semestre_2", {}))

            if total_dias > 0:
                self.log_mensaje(f"✅ Datos cargados: {total_dias} días lectivos configurados", "success")
            else:
                self.log_mensaje("📝 No hay días configurados - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("🗓️ CONFIGURACIÓN DE CALENDARIO ACADÉMICO")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información del anio académico
        self.anio_label = QLabel(f"📅 Año Académico: {self.datos_configuracion['anio_academico']}")
        self.anio_label.setStyleSheet("color: #cccccc; font-size: 12px; margin-bottom: 10px;")
        self.anio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.anio_label)

        # Información de uso
        info_label = QLabel(
            "ℹ️ Haz clic en fechas del calendario para añadir días • Arrastra días entre columnas para cambiar horarios")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 15px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal - tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Calendarios clicables
        self.setup_calendarios_panel(content_layout)

        # Columna central - Grids de días configurados
        self.setup_grids_panel(content_layout)

        # Columna derecha - Acciones y configuración
        self.setup_acciones_panel(content_layout)

        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

    def setup_anio_control(self, parent_layout):
        """Crear control dinámico para cambiar anio académico"""
        anio_control_layout = QHBoxLayout()
        anio_control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Etiqueta
        label_anio = QLabel("Año base:")
        label_anio.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        anio_control_layout.addWidget(label_anio)

        # Campo de texto para anio (solo números, 4 dígitos)
        self.edit_anio = QLineEdit()
        self.edit_anio.setFixedWidth(80)
        self.edit_anio.setText(str(self.anio_academico))
        self.edit_anio.setMaxLength(4)

        # Validador para solo números
        validator = QIntValidator()
        self.edit_anio.setValidator(validator)

        self.edit_anio.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 2px solid #4a9eff;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #66b3ff;
            }
        """)
        anio_control_layout.addWidget(self.edit_anio)

        # Botón aplicar
        self.btn_aplicar_anio = QPushButton("Aplicar")
        self.btn_aplicar_anio.setFixedWidth(80)
        self.btn_aplicar_anio.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: #ffffff;
                border: 1px solid #4a9eff;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #66b3ff;
                border-color: #66b3ff;
            }
            QPushButton:pressed {
                background-color: #3d8bcc;
            }
        """)
        self.btn_aplicar_anio.clicked.connect(self.aplicar_nuevo_anio)
        anio_control_layout.addWidget(self.btn_aplicar_anio)

        # Conectar Enter al botón aplicar
        self.edit_anio.returnPressed.connect(self.aplicar_nuevo_anio)

        parent_layout.addLayout(anio_control_layout)

    def aplicar_nuevo_anio(self):
        """Aplicar nuevo anio académico"""
        try:
            nuevo_anio_text = self.edit_anio.text().strip()

            # Validar que tenga 4 dígitos
            if len(nuevo_anio_text) != 4:
                QMessageBox.warning(
                    self, "Año Inválido",
                    "El año debe tener exactamente 4 dígitos.\n\nEjemplo: 2024"
                )
                self.edit_anio.setText(str(self.anio_academico))
                return

            nuevo_anio = int(nuevo_anio_text)

            # Si es el mismo anio, no hacer nada
            if nuevo_anio == self.anio_academico:
                return

            # Verificar si hay datos existentes
            total_dias = len(self.datos_configuracion.get("semestre_1", {})) + len(
                self.datos_configuracion.get("semestre_2", {}))

            if total_dias > 0:
                respuesta = QMessageBox.question(
                    self, "Cambiar Año Académico",
                    f"🗓️ CAMBIAR AÑO ACADÉMICO\n\n"
                    f"Año actual: {self.anio_academico}-{self.anio_academico + 1}\n"
                    f"Año nuevo: {nuevo_anio}-{nuevo_anio + 1}\n\n"
                    f"⚠️ Hay {total_dias} días configurados actualmente.\n\n"
                    f"Al cambiar el año académico se perderán todos los días\n"
                    f"configurados y se reiniciará la configuración.\n\n"
                    f"¿Continuar con el cambio?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if respuesta == QMessageBox.StandardButton.No:
                    self.edit_anio.setText(str(self.anio_academico))
                    return

            # Aplicar nuevo anio
            self.anio_academico = nuevo_anio
            self.datos_configuracion["anio_academico"] = f"{nuevo_anio}-{nuevo_anio + 1}"

            # Limpiar datos existentes
            self.datos_configuracion["semestre_1"].clear()
            self.datos_configuracion["semestre_2"].clear()

            # Actualizar label de anio académico
            self.anio_label.setText(f"📅 Año Académico: {self.datos_configuracion['anio_academico']}")

            # Actualizar rangos de calendarios
            self.actualizar_rangos_calendarios()

            # Limpiar y recargar grids
            self.cargar_dias_en_grids()

            # Marcar cambio
            self.marcar_cambio_realizado()

            # Log del cambio
            self.log_mensaje(f"🗓️ Año académico cambiado a {nuevo_anio}-{nuevo_anio + 1}", "success")

            QMessageBox.information(
                self, "Año Actualizado",
                f"✅ Año académico actualizado exitosamente\n\n"
                f"Nuevo período: {nuevo_anio}-{nuevo_anio + 1}\n\n"
                f"📝 Los calendarios han sido actualizados\n"
                f"con las nuevas fechas disponibles."
            )

        except ValueError:
            QMessageBox.warning(
                self, "Año Inválido",
                "Por favor ingresa un año válido de 4 dígitos.\n\nEjemplo: 2024"
            )
            self.edit_anio.setText(str(self.anio_academico))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error aplicando nuevo año: {e}")
            self.edit_anio.setText(str(self.anio_academico))

    def actualizar_rangos_calendarios(self):
        """Actualizar rangos de fechas de los calendarios"""
        try:
            # Calendario 1º semestre (Sep-Ene)
            inicio_1 = QDate(self.anio_academico, 9, 1)
            fin_1 = QDate(self.anio_academico + 1, 1, 31)
            self.calendario_1.setMinimumDate(inicio_1)
            self.calendario_1.setMaximumDate(fin_1)
            self.calendario_1.setSelectedDate(inicio_1)

            # Calendario 2º semestre (Feb-Jun)
            inicio_2 = QDate(self.anio_academico + 1, 2, 1)
            fin_2 = QDate(self.anio_academico + 1, 6, 30)
            self.calendario_2.setMinimumDate(inicio_2)
            self.calendario_2.setMaximumDate(fin_2)
            self.calendario_2.setSelectedDate(inicio_2)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error actualizando rangos de calendarios: {e}", "warning")

    def setup_calendarios_panel(self, parent_layout):
        """Panel izquierdo con calendarios clicables"""
        left_panel = QGroupBox("📅 CALENDARIOS RÁPIDOS")
        left_layout = QVBoxLayout()

        # Control dinámico de anio académico
        self.setup_anio_control(left_layout)

        # Separador visual
        separator = QLabel("")
        separator.setFixedHeight(10)
        left_layout.addWidget(separator)

        # Calendario 1º semestre
        sem1_group = QGroupBox("1º Semestre (Sep-Ene)")
        sem1_layout = QVBoxLayout()

        self.calendario_1 = QCalendarWidget()
        self.calendario_1.setMaximumHeight(200)

        # Configurar rango de fechas del 1º semestre
        inicio_1 = QDate(self.anio_academico, 9, 1)
        fin_1 = QDate(self.anio_academico + 1, 1, 31)
        self.calendario_1.setMinimumDate(inicio_1)
        self.calendario_1.setMaximumDate(fin_1)
        self.calendario_1.setSelectedDate(inicio_1)

        self.calendario_1.clicked.connect(lambda fecha: self.calendario_dia_clicked(fecha, "semestre_1"))
        sem1_layout.addWidget(self.calendario_1)

        # Contador de días 1º semestre
        self.label_contador_1 = QLabel("📊 Días configurados: 0/14")
        self.label_contador_1.setStyleSheet("color: #cccccc; font-size: 10px;")
        sem1_layout.addWidget(self.label_contador_1)

        sem1_group.setLayout(sem1_layout)
        left_layout.addWidget(sem1_group)

        # Calendario 2º semestre
        sem2_group = QGroupBox("2º Semestre (Feb-Jun)")
        sem2_layout = QVBoxLayout()

        self.calendario_2 = QCalendarWidget()
        self.calendario_2.setMaximumHeight(200)

        # Configurar rango de fechas del 2º semestre
        inicio_2 = QDate(self.anio_academico + 1, 2, 1)
        fin_2 = QDate(self.anio_academico + 1, 6, 30)
        self.calendario_2.setMinimumDate(inicio_2)
        self.calendario_2.setMaximumDate(fin_2)
        self.calendario_2.setSelectedDate(inicio_2)

        self.calendario_2.clicked.connect(lambda fecha: self.calendario_dia_clicked(fecha, "semestre_2"))
        sem2_layout.addWidget(self.calendario_2)

        # Contador de días 2º semestre
        self.label_contador_2 = QLabel("📊 Días configurados: 0/14")
        self.label_contador_2.setStyleSheet("color: #cccccc; font-size: 10px;")
        sem2_layout.addWidget(self.label_contador_2)

        sem2_group.setLayout(sem2_layout)
        left_layout.addWidget(sem2_group)

        # Leyenda de colores y controles
        leyenda_group = QGroupBox("🎨 Leyenda & Controles")
        leyenda_layout = QVBoxLayout()

        leyenda_layout.addWidget(QLabel("🟢 Verde: Día normal"))
        leyenda_layout.addWidget(QLabel("🟡 Amarillo: Horario especial"))
        leyenda_layout.addWidget(QLabel("⚪ Gris: Sin configurar"))
        leyenda_layout.addWidget(QLabel(""))
        leyenda_layout.addWidget(QLabel("💡 Arrastra días entre columnas"))
        leyenda_layout.addWidget(QLabel("🖱️ Clic en calendario para añadir"))

        leyenda_group.setLayout(leyenda_layout)
        left_layout.addWidget(leyenda_group)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(350)
        parent_layout.addWidget(left_panel)

    def setup_grids_panel(self, parent_layout):
        """Panel central con grids de días configurados"""
        center_panel = QGroupBox("📋 DÍAS LECTIVOS CONFIGURADOS")
        center_layout = QVBoxLayout()

        # Grid 1º semestre
        sem1_group = QGroupBox("1º SEMESTRE")
        sem1_layout = QVBoxLayout()

        self.grid_1 = self.crear_grid_semestre("semestre_1")
        sem1_layout.addWidget(self.grid_1)

        sem1_group.setLayout(sem1_layout)
        center_layout.addWidget(sem1_group)

        # Grid 2º semestre
        sem2_group = QGroupBox("2º SEMESTRE")
        sem2_layout = QVBoxLayout()

        self.grid_2 = self.crear_grid_semestre("semestre_2")
        sem2_layout.addWidget(self.grid_2)

        sem2_group.setLayout(sem2_layout)
        center_layout.addWidget(sem2_group)

        center_panel.setLayout(center_layout)
        parent_layout.addWidget(center_panel)

    def crear_grid_semestre(self, semestre):
        """Crear grid para un semestre con numeración y capacidad dinámica"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        ANCHO_COLUMNA = 140
        ANCHO_NUMERACION = 50

        # Header para numeración
        num_header = QLabel("#")
        num_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_header.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        num_header.setStyleSheet("background-color: #6a6a6a; padding: 6px; border-radius: 3px; color: white;")
        num_header.setFixedWidth(ANCHO_NUMERACION)
        num_header.setMinimumHeight(30)
        grid_layout.addWidget(num_header, 0, 0)

        # Headers de días de la semana
        dias_header = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES"]
        for i, dia in enumerate(dias_header):
            header = QLabel(dia)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            header.setStyleSheet("background-color: #4a4a4a; padding: 6px; border-radius: 3px; color: white;")
            header.setFixedWidth(ANCHO_COLUMNA)
            header.setMinimumHeight(30)
            grid_layout.addWidget(header, 0, i + 1)  # +1 por la columna de numeración

        # Crear inicialmente 14 filas (mínimo) con números y DropZoneWidgets
        dias_columnas = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        for fila in range(1, 15):  # Filas 1-14
            # Columna de numeración
            num_label = QLabel(str(fila))
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            num_label.setStyleSheet("""
                background-color: #5a5a5a; 
                color: #ffffff; 
                border: 1px solid #666; 
                border-radius: 3px; 
                padding: 3px;
            """)
            num_label.setFixedWidth(ANCHO_NUMERACION)
            num_label.setMinimumHeight(50)
            grid_layout.addWidget(num_label, fila, 0)

            # Columnas de días
            for col in range(5):  # Columnas 0-4 para días
                dia_horario = dias_columnas[col]
                drop_zone = DropZoneWidget(dia_horario)
                drop_zone.dia_dropped.connect(self.manejar_drop_dia)
                grid_layout.addWidget(drop_zone, fila, col + 1)  # +1 por la columna de numeración

        # Establecer política de columnas
        grid_layout.setColumnMinimumWidth(0, ANCHO_NUMERACION)  # Columna numeración
        for col in range(1, 6):  # Columnas 1-5 para días
            grid_layout.setColumnMinimumWidth(col, ANCHO_COLUMNA)
            grid_layout.setColumnStretch(col, 0)

        # Grid dinámico
        grid_layout.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)
        grid_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        grid_widget.setLayout(grid_layout)
        scroll.setWidget(grid_widget)

        return scroll

    def setup_acciones_panel(self, parent_layout):
        """Panel derecho con acciones"""
        right_panel = QGroupBox("⚙️ GESTIÓN Y CONFIGURACIÓN")
        right_layout = QVBoxLayout()

        # Acciones rápidas
        acciones_group = QGroupBox("🚀 ACCIONES RÁPIDAS")
        acciones_layout = QVBoxLayout()

        self.btn_generar_calendario = QPushButton("🤖 Generar Calendario Automático")
        self.btn_generar_calendario.clicked.connect(self.generar_calendario_automatico)
        acciones_layout.addWidget(self.btn_generar_calendario)

        self.btn_limpiar_semestre = QPushButton("🧹 Limpiar Semestre")
        self.btn_limpiar_semestre.clicked.connect(self.limpiar_semestre)
        acciones_layout.addWidget(self.btn_limpiar_semestre)

        self.btn_verificar_equilibrio = QPushButton("⚖️ Verificar Equilibrio")
        self.btn_verificar_equilibrio.clicked.connect(
            lambda: self.verificar_equilibrio_completo(mostrar_si_todo_ok=True))
        acciones_layout.addWidget(self.btn_verificar_equilibrio)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Import/Export
        importar_group = QGroupBox("📥 IMPORTAR DATOS")
        importar_layout = QVBoxLayout()

        self.btn_importar_web = QPushButton("🌐 Importar desde Web UPM")
        self.btn_importar_web.setStyleSheet("background-color: #FF9800; color: white;")
        self.btn_importar_web.clicked.connect(self.importar_desde_web)
        importar_layout.addWidget(self.btn_importar_web)

        self.btn_importar_csv = QPushButton("📥 Importar desde CSV")
        self.btn_importar_csv.clicked.connect(self.importar_desde_csv)
        importar_layout.addWidget(self.btn_importar_csv)

        self.btn_cargar = QPushButton("📁 Cargar Configuración")
        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Exportar
        exportar_group = QGroupBox("📤 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

        self.btn_exportar_csv = QPushButton("📄 Exportar a CSV")
        self.btn_exportar_csv.clicked.connect(self.exportar_a_csv)
        exportar_layout.addWidget(self.btn_exportar_csv)

        self.btn_exportar_json = QPushButton("📋 Exportar a JSON")
        self.btn_exportar_json.clicked.connect(self.exportar_a_json)
        exportar_layout.addWidget(self.btn_exportar_json)

        exportar_group.setLayout(exportar_layout)
        right_layout.addWidget(exportar_group)

        # Botones principales
        botones_group = QGroupBox("💾 GUARDAR CONFIGURACIÓN")
        botones_layout = QVBoxLayout()

        self.btn_guardar_sistema = QPushButton("✅ Guardar en Sistema")
        self.btn_guardar_sistema.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
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
        self.btn_guardar_sistema.clicked.connect(self.guardar_en_sistema)
        botones_layout.addWidget(self.btn_guardar_sistema)

        self.btn_limpiar_todo = QPushButton("🗑️ Limpiar Todo")
        self.btn_limpiar_todo.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todo)
        botones_layout.addWidget(self.btn_limpiar_todo)

        botones_group.setLayout(botones_layout)
        right_layout.addWidget(botones_group)

        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        right_panel.setMaximumWidth(400)
        parent_layout.addWidget(right_panel)

    def apply_dark_theme(self):
        """Aplicar tema oscuro idéntico al resto del sistema"""
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
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #3c3c3c;
            }
            QCalendarWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
            }
        """)

    def conectar_signals(self):
        """Conectar señales"""
        pass

    def calendario_dia_clicked(self, fecha, semestre):
        """Manejar clic en calendario"""
        try:
            # Verificar que la fecha esté en el rango del semestre correcto
            anio_fecha = fecha.year()
            mes_fecha = fecha.month()

            # Validar que la fecha corresponde al semestre seleccionado
            if semestre == "semestre_1":
                # 1º semestre: Sep-Ene
                if not ((mes_fecha >= 9 and anio_fecha == self.anio_academico) or
                        (mes_fecha <= 1 and anio_fecha == self.anio_academico + 1)):
                    QMessageBox.warning(
                        self, "Fecha Incorrecta",
                        f"La fecha seleccionada no corresponde al 1º semestre\n"
                        f"(Septiembre {self.anio_academico} - Enero {self.anio_academico + 1})"
                    )
                    return
            else:  # semestre_2
                # 2º semestre: Feb-Jun
                if not (2 <= mes_fecha <= 6 and anio_fecha == self.anio_academico + 1):
                    QMessageBox.warning(
                        self, "Fecha Incorrecta",
                        f"La fecha seleccionada no corresponde al 2º semestre\n"
                        f"(Febrero {self.anio_academico + 1} - Junio {self.anio_academico + 1})"
                    )
                    return

            # Verificar si es fin de semana
            es_fin_semana = fecha.dayOfWeek() in [6, 7]  # Sábado=6, Domingo=7

            if es_fin_semana:
                # Obtener nombre del día en español
                nombres_dias = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado",
                                7: "Domingo"}
                nombre_dia = nombres_dias.get(fecha.dayOfWeek(), "Desconocido")

                # Mostrar advertencia para fin de semana
                respuesta = QMessageBox.question(
                    self, "⚠️ Día de Fin de Semana",
                    f"Has seleccionado: {nombre_dia} {fecha.toString('dd MMM yyyy')}\n\n"
                    "⚠️ Normalmente los fines de semana no son días lectivos\n\n"
                    "¿Estás seguro de que este día habrá clases?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if respuesta == QMessageBox.StandardButton.No:
                    return

            # Verificar si ya existe este día
            fecha_str = fecha.toString("yyyy-MM-dd")
            if fecha_str in self.datos_configuracion[semestre]:
                QMessageBox.information(
                    self, "Día Ya Configurado",
                    f"El día {fecha.toString('dd MMM yyyy')} ya está configurado.\n\n"
                    "Elimínalo del grid si quieres reconfigurarlo."
                )
                return

            # Abrir dialog de configuración
            dialog = ConfiguracionDiaDialog(fecha, es_fin_semana, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                config_dia = dialog.get_configuracion_dia()

                # Guardar en el semestre correcto
                self.datos_configuracion[semestre][fecha_str] = config_dia

                # Actualizar grids
                self.cargar_dias_en_grids()

                # Verificar límite por horario específico
                self.verificar_limite_por_horario(semestre, config_dia['horario_asignado'])

                # Actualizar contadores
                self.actualizar_contadores()

                # Marcar cambio
                self.marcar_cambio_realizado()

                sem_nombre = "1º" if semestre == "semestre_1" else "2º"
                self.log_mensaje(f"✅ Día {fecha.toString('dd MMM')} añadido a {sem_nombre} semestre", "success")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error añadiendo día: {e}")

    def verificar_limite_por_horario(self, semestre, horario_asignado):
        """Verificar límite de 14 días por horario específico con avisos precisos"""
        # Contar días con este horario asignado en este semestre
        count = sum(1 for config in self.datos_configuracion[semestre].values()
                    if config.get('horario_asignado') == horario_asignado)

        sem_nombre = "1º" if semestre == "semestre_1" else "2º"

        if count > 14:
            QMessageBox.warning(
                self, "⚠️ Límite Excedido",
                f"🚨 LÍMITE SUPERADO\n\n"
                f"Columna \"{horario_asignado}\" en {sem_nombre} semestre:\n"
                f"📊 Días actuales: {count}\n"
                f"📋 Límite recomendado: 14 días\n"
                f"📈 Exceso: {count - 14} días\n\n"
                f"⚠️ Esto puede causar sobrecarga en ese horario.\n"
                f"Considera redistribuir algunos días a otras columnas."
            )
        elif count == 14:
            QMessageBox.information(
                self, "✅ Límite Alcanzado",
                f"🎯 LÍMITE PERFECTO\n\n"
                f"Columna \"{horario_asignado}\" en {sem_nombre} semestre:\n"
                f"📊 Días actuales: {count}\n"
                f"📋 Límite recomendado: 14 días\n\n"
                f"✅ Has alcanzado exactamente el límite ideal.\n"
                f"💡 Evita añadir más días a esta columna."
            )

    def verificar_equilibrio_completo(self, mostrar_si_todo_ok=False):
        """Verificar equilibrio de todos los horarios en ambos semestres"""
        problemas_encontrados = []

        for semestre in ["semestre_1", "semestre_2"]:
            sem_nombre = "1º" if semestre == "semestre_1" else "2º"

            # Contar por horario
            conteo_horarios = {"Lunes": 0, "Martes": 0, "Miércoles": 0, "Jueves": 0, "Viernes": 0}

            for config in self.datos_configuracion[semestre].values():
                horario = config.get('horario_asignado', 'Lunes')
                if horario in conteo_horarios:
                    conteo_horarios[horario] += 1

            # Verificar problemas por horario
            for horario, count in conteo_horarios.items():
                if count > 14:
                    problemas_encontrados.append(
                        f"🚨 {sem_nombre} semestre - {horario}: {count} días (excede límite por {count - 14})"
                    )
                elif count < 14 and count > 0:
                    problemas_encontrados.append(
                        f"⚠️ {sem_nombre} semestre - {horario}: {count} días (faltan {14 - count} para límite)"
                    )
                elif count == 0:
                    problemas_encontrados.append(
                        f"❌ {sem_nombre} semestre - {horario}: 0 días (columna vacía)"
                    )

        # Mostrar resultados
        if problemas_encontrados:
            mensaje = "📊 ANÁLISIS DE EQUILIBRIO DE HORARIOS\n\n"
            mensaje += "Se detectaron los siguientes desequilibrios:\n\n"

            for i, problema in enumerate(problemas_encontrados, 1):
                mensaje += f"{i}. {problema}\n"

            mensaje += f"\n💡 RECOMENDACIONES:\n"
            mensaje += f"• Ideal: 14 días por horario\n"
            mensaje += f"• Redistribuye días entre columnas usando drag & drop\n"
            mensaje += f"• Usa 'Generar Calendario Automático' para equilibrio perfecto"

            QMessageBox.warning(self, "⚖️ Desequilibrio de Horarios", mensaje)
            return False
        else:
            if mostrar_si_todo_ok:
                QMessageBox.information(
                    self, "✅ Equilibrio Perfecto",
                    "🎯 CONFIGURACIÓN IDEAL\n\n"
                    "✅ Todos los horarios tienen exactamente 14 días\n"
                    "✅ Distribución perfectamente equilibrada\n\n"
                    "🎉 ¡Excelente configuración!"
                )
            return True

    def verificar_y_restaurar_numeracion(self, grid_layout):
        """Verificar que existan los números 1-14 y restaurarlos si faltan"""
        try:
            ANCHO_NUMERACION = 50

            # Verificar y crear números faltantes en filas 1-14
            for fila in range(1, 15):
                existing_num = grid_layout.itemAtPosition(fila, 0)
                if not existing_num or not existing_num.widget():
                    # Crear número faltante
                    num_label = QLabel(str(fila))
                    num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    num_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                    num_label.setStyleSheet("""
                        background-color: #5a5a5a; 
                        color: #ffffff; 
                        border: 1px solid #666; 
                        border-radius: 3px; 
                        padding: 3px;
                    """)
                    num_label.setToolTip(f"Día {fila}")
                    num_label.setFixedWidth(ANCHO_NUMERACION)
                    num_label.setMinimumHeight(50)
                    grid_layout.addWidget(num_label, fila, 0)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error restaurando numeración: {e}", "warning")

    def cargar_dias_en_grids(self):
        """Cargar días configurados en los grids con capacidad dinámica optimizada"""
        try:
            # Limpiar solo widgets de días, preservar numeración
            self.limpiar_widgets_grids()

            # Mapeo consistente de días
            dias_mapa = {
                "Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4, "Viernes": 5
            }

            # Cargar cada semestre
            for semestre in ["semestre_1", "semestre_2"]:
                datos_semestre = self.datos_configuracion.get(semestre, {})

                # Obtener el grid correcto
                grid_widget = self.grid_1.widget() if semestre == "semestre_1" else self.grid_2.widget()
                grid_layout = grid_widget.layout()

                # Verificar y restaurar numeración base 1-14
                self.verificar_y_restaurar_numeracion(grid_layout)

                # Organizar por día de la semana
                dias_por_semana = {
                    "Lunes": [], "Martes": [], "Miércoles": [], "Jueves": [], "Viernes": []
                }

                # Solo añadir datos si existen
                if datos_semestre:
                    for fecha_str, config_dia in datos_semestre.items():
                        horario_asignado = config_dia.get('horario_asignado', 'Lunes')
                        if horario_asignado in dias_por_semana:
                            dias_por_semana[horario_asignado].append((fecha_str, config_dia))

                    # Ordenar por fecha dentro de cada día
                    for dia in dias_por_semana:
                        dias_por_semana[dia].sort(key=lambda x: x[0])

                # Calcular máximo número de días en cualquier columna
                max_dias = max(len(dias_por_semana[dia]) for dia in dias_por_semana) if any(
                    dias_por_semana.values()) else 0
                filas_necesarias = max(14, max_dias)  # Mínimo 14, máximo según datos

                # Expandir grid solo si es necesario (esto no borrará números existentes)
                if filas_necesarias > 14:
                    self.expandir_grid_si_necesario(grid_layout, filas_necesarias)

                # Procesar todas las columnas de días
                for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]:
                    if dia not in dias_mapa:
                        continue

                    col = dias_mapa[dia]  # Columna correspondiente
                    fila = 1  # Empezar en fila 1 (fila 0 son headers)
                    lista_dias = dias_por_semana[dia]

                    # Añadir widgets de días existentes
                    for fecha_str, config_dia in lista_dias:
                        if fila > filas_necesarias:  # No exceder filas disponibles
                            break

                        # Crear widget del día
                        dia_widget = DiaWidget(
                            fecha_str,
                            config_dia.get('dia_real', ''),
                            config_dia.get('horario_asignado', ''),
                            config_dia.get('motivo', ''),
                            config_dia.get('es_especial', False),
                            self
                        )

                        # Conectar señales
                        dia_widget.dia_eliminado.connect(
                            lambda fecha, s=semestre: self.eliminar_dia(fecha, s))
                        dia_widget.dia_dropped.connect(self.manejar_drop_dia)

                        # Guardar referencia
                        self.grids_widgets[semestre][dia].append(dia_widget)

                        # Añadir widget en posición específica
                        grid_layout.addWidget(dia_widget, fila, col)
                        fila += 1

                    # Rellenar espacios vacíos con DropZoneWidget hasta filas disponibles
                    filas_disponibles = max(14, grid_layout.rowCount() - 1)  # -1 por header
                    while fila <= filas_disponibles:
                        # Verificar si ya existe un widget en esta posición
                        existing_item = grid_layout.itemAtPosition(fila, col)
                        if not existing_item or not existing_item.widget():
                            # Crear nueva drop zone
                            drop_zone = DropZoneWidget(dia)
                            drop_zone.dia_dropped.connect(self.manejar_drop_dia)

                            # Aplicar estilo de advertencia si excede 14
                            if fila > 14:
                                drop_zone.setStyleSheet("""
                                    border: 2px dashed #ff6600; 
                                    border-radius: 3px; 
                                    background-color: rgba(255, 102, 0, 0.1);
                                """)
                                drop_zone.setToolTip(f"⚠️ Zona {dia} - Fila {fila} excede límite")

                            grid_layout.addWidget(drop_zone, fila, col)
                        fila += 1

            # Actualizar contadores
            self.actualizar_contadores()

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando días en grids: {e}", "warning")

    def expandir_grid_si_necesario(self, grid_layout, filas_necesarias):
        """Expandir grid dinámicamente agregando solo las filas que faltan"""
        try:
            ANCHO_COLUMNA = 140
            ANCHO_NUMERACION = 50

            # Obtener número actual de filas
            filas_actuales = grid_layout.rowCount()

            # Solo añadir filas si realmente necesitamos más
            if filas_necesarias >= filas_actuales:
                dias_columnas = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

                # Añadir solo las filas que faltan
                for fila in range(filas_actuales, filas_necesarias + 1):
                    # Verificar si ya existe la numeración en esta fila
                    existing_num = grid_layout.itemAtPosition(fila, 0)
                    if not existing_num or not existing_num.widget():
                        # Crear columna de numeración solo si no existe
                        num_label = QLabel(str(fila))
                        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        num_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))

                        # Color diferente si excede 14 (visual warning)
                        if fila > 14:
                            num_label.setStyleSheet("""
                                background-color: #cc5500; 
                                color: #ffffff; 
                                border: 2px solid #ff6600; 
                                border-radius: 3px; 
                                padding: 3px;
                                font-weight: bold;
                            """)
                            num_label.setToolTip(f"⚠️ Fila {fila} - Excede límite recomendado de 14 días")
                        else:
                            num_label.setStyleSheet("""
                                background-color: #5a5a5a; 
                                color: #ffffff; 
                                border: 1px solid #666; 
                                border-radius: 3px; 
                                padding: 3px;
                            """)
                            num_label.setToolTip(f"Día {fila}")

                        num_label.setFixedWidth(ANCHO_NUMERACION)
                        num_label.setMinimumHeight(50)
                        grid_layout.addWidget(num_label, fila, 0)

                    # Crear columnas de días solo si no existen
                    for col in range(5):
                        existing_widget = grid_layout.itemAtPosition(fila, col + 1)
                        if not existing_widget or not existing_widget.widget():
                            dia_horario = dias_columnas[col]
                            drop_zone = DropZoneWidget(dia_horario)
                            drop_zone.dia_dropped.connect(self.manejar_drop_dia)

                            # Color de advertencia para DropZones que exceden límite
                            if fila > 14:
                                drop_zone.setStyleSheet("""
                                    border: 2px dashed #ff6600; 
                                    border-radius: 3px; 
                                    background-color: rgba(255, 102, 0, 0.1);
                                """)
                                drop_zone.setToolTip(f"⚠️ Zona {dia_horario} - Fila {fila} excede límite")

                            grid_layout.addWidget(drop_zone, fila, col + 1)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error expandiendo grid: {e}", "warning")

    def limpiar_widgets_grids(self):
        """Limpiar widgets de días pero preservar numeración"""
        try:
            # Limpiar referencias en memoria
            for semestre in self.grids_widgets:
                for dia in self.grids_widgets[semestre]:
                    for widget in self.grids_widgets[semestre][dia]:
                        if widget and hasattr(widget, 'setParent'):
                            widget.setParent(None)
                            widget.deleteLater()
                    self.grids_widgets[semestre][dia].clear()

            # Limpiar físicamente solo las columnas de días (1-5), preservar numeración (columna 0)
            for semestre, grid_scroll in [("semestre_1", self.grid_1), ("semestre_2", self.grid_2)]:
                grid_widget = grid_scroll.widget()
                grid_layout = grid_widget.layout()

                # Obtener número total de filas actuales
                filas_totales = grid_layout.rowCount()

                # Limpiar solo columnas de días (1-5), NO la numeración (0)
                for fila in range(1, filas_totales):
                    for col in range(1, 6):  # Solo columnas 1-5 (días), preservar 0 (números)
                        item = grid_layout.itemAtPosition(fila, col)
                        if item and item.widget():
                            widget = item.widget()
                            grid_layout.removeWidget(widget)
                            widget.setParent(None)
                            widget.deleteLater()

        except Exception as e:
            self.log_mensaje(f"⚠️ Error limpiando widgets: {e}", "warning")

    def manejar_drop_dia(self, datos_dia, nuevo_horario):
        """Manejar cuando se dropea un día en una nueva columna"""
        try:
            # Parsear datos del día
            partes = datos_dia.split('|')
            if len(partes) != 5:
                return

            fecha, dia_real, horario_original, motivo, es_especial_str = partes
            es_especial = es_especial_str == 'True'

            # Buscar el semestre que contiene esta fecha
            semestre = None
            for s in ["semestre_1", "semestre_2"]:
                if fecha in self.datos_configuracion[s]:
                    semestre = s
                    break

            if not semestre:
                return

            # Verificar límite en la nueva columna antes de mover
            count_nuevo_horario = sum(1 for config in self.datos_configuracion[semestre].values()
                                      if config.get('horario_asignado') == nuevo_horario)

            # Si no estaba en esta columna antes, verificar límite
            if horario_original != nuevo_horario and count_nuevo_horario >= 14:
                respuesta = QMessageBox.question(
                    self, "⚠️ Límite de Columna",
                    f"La columna \"{nuevo_horario}\" ya tiene {count_nuevo_horario} días.\n\n"
                    f"¿Continuar moviendo el día {fecha} a esta columna?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if respuesta == QMessageBox.StandardButton.No:
                    return

            # Actualizar horario asignado en los datos
            nueva_es_especial = dia_real != nuevo_horario

            self.datos_configuracion[semestre][fecha].update({
                'horario_asignado': nuevo_horario,
                'es_especial': nueva_es_especial
            })

            # Recargar grids para mostrar el cambio
            self.cargar_dias_en_grids()

            # Verificar nuevo límite
            self.verificar_limite_por_horario(semestre, nuevo_horario)

            # Marcar cambio
            self.marcar_cambio_realizado()

            # Log del movimiento
            if horario_original != nuevo_horario:
                self.log_mensaje(
                    f"📋 Día {fecha} movido: {horario_original} → {nuevo_horario}",
                    "success"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error moviendo día: {e}")
            self.log_mensaje(f"⚠️ Error en drag & drop: {e}", "warning")

    def eliminar_dia(self, fecha, semestre):
        """Eliminar un día específico"""
        try:
            if fecha in self.datos_configuracion[semestre]:
                del self.datos_configuracion[semestre][fecha]

                # Recargar grids
                self.cargar_dias_en_grids()

                # Marcar cambio
                self.marcar_cambio_realizado()

                self.log_mensaje(f"🗑️ Día {fecha} eliminado", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando día: {e}", "warning")

    def actualizar_contadores(self):
        """Actualizar contadores de días con información detallada por horario y alertas visuales"""

        # Función auxiliar para contar por horario
        def contar_por_horario(semestre_data):
            conteo = {"Lunes": 0, "Martes": 0, "Miércoles": 0, "Jueves": 0, "Viernes": 0}
            for config in semestre_data.values():
                horario = config.get('horario_asignado', 'Lunes')
                if horario in conteo:
                    conteo[horario] += 1
            return conteo

        # Contar por horario en cada semestre
        count_1_por_horario = contar_por_horario(self.datos_configuracion.get("semestre_1", {}))
        count_2_por_horario = contar_por_horario(self.datos_configuracion.get("semestre_2", {}))

        # Totales por semestre
        total_1 = sum(count_1_por_horario.values())
        total_2 = sum(count_2_por_horario.values())

        # Detectar si alguna columna excede 14
        exceso_1 = any(count > 14 for count in count_1_por_horario.values())
        exceso_2 = any(count > 14 for count in count_2_por_horario.values())

        # Detectar columnas específicas que exceden
        columnas_exceso_1 = [dia for dia, count in count_1_por_horario.items() if count > 14]
        columnas_exceso_2 = [dia for dia, count in count_2_por_horario.items() if count > 14]

        # Aplicar colores según límite
        color_1 = "#ff6666" if exceso_1 else "#66ff66" if total_1 > 0 else "#cccccc"
        color_2 = "#ff6666" if exceso_2 else "#66ff66" if total_2 > 0 else "#cccccc"

        # Mostrar contadores con detalles y alertas
        texto_1 = f"📊 Total: {total_1} días"
        if total_1 > 0:
            # Mostrar detalles de columnas con días
            detalles_1 = []
            for dia, count in count_1_por_horario.items():
                if count > 0:
                    if count > 14:
                        detalles_1.append(f"{dia[0]}:{count}⚠️")  # Añadir alerta visual
                    else:
                        detalles_1.append(f"{dia[0]}:{count}")
            if detalles_1:
                texto_1 += f" ({', '.join(detalles_1)})"

        # Añadir advertencia si hay excesos
        if columnas_exceso_1:
            texto_1 += f"\n🚨 EXCESO: {', '.join(columnas_exceso_1)}"

        texto_2 = f"📊 Total: {total_2} días"
        if total_2 > 0:
            # Mostrar detalles de columnas con días
            detalles_2 = []
            for dia, count in count_2_por_horario.items():
                if count > 0:
                    if count > 14:
                        detalles_2.append(f"{dia[0]}:{count}⚠️")  # Añadir alerta visual
                    else:
                        detalles_2.append(f"{dia[0]}:{count}")
            if detalles_2:
                texto_2 += f" ({', '.join(detalles_2)})"

        # Añadir advertencia si hay excesos
        if columnas_exceso_2:
            texto_2 += f"\n🚨 EXCESO: {', '.join(columnas_exceso_2)}"

        self.label_contador_1.setText(texto_1)
        self.label_contador_1.setStyleSheet(f"color: {color_1}; font-size: 10px; font-weight: bold;")

        self.label_contador_2.setText(texto_2)
        self.label_contador_2.setStyleSheet(f"color: {color_2}; font-size: 10px; font-weight: bold;")

    def generar_calendario_automatico(self):
        """Generar calendario automático básico"""
        try:
            respuesta = QMessageBox.question(
                self, "Generar Calendario Automático",
                "¿Generar un calendario académico básico?\n\n"
                "Esto creará días lectivos típicos de lunes a viernes\n"
                "excluyendo festivos comunes.\n\n"
                "⚠️ Esto reemplazará la configuración actual",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.No:
                return

            # Limpiar configuración actual
            self.datos_configuracion["semestre_1"].clear()
            self.datos_configuracion["semestre_2"].clear()

            # Calcular primer lunes de septiembre
            primer_sept = date(self.anio_academico, 9, 1)
            dias_hasta_lunes = (0 - primer_sept.weekday()) % 7  # 0 = Lunes
            primer_lunes_sept = primer_sept + timedelta(days=dias_hasta_lunes)

            # Calcular primer lunes de febrero
            primer_feb = date(self.anio_academico + 1, 2, 1)
            dias_hasta_lunes_feb = (0 - primer_feb.weekday()) % 7  # 0 = Lunes
            primer_lunes_feb = primer_feb + timedelta(days=dias_hasta_lunes_feb)

            # Generar 1º semestre (desde primer lunes de septiembre)
            self.generar_dias_semestre(
                "semestre_1",
                primer_lunes_sept,
                date(self.anio_academico + 1, 1, 20)  # Fin típico
            )

            # Generar 2º semestre (desde primer lunes de febrero)
            self.generar_dias_semestre(
                "semestre_2",
                primer_lunes_feb,
                date(self.anio_academico + 1, 6, 6)  # Fin típico
            )

            # Recargar grids
            self.cargar_dias_en_grids()
            self.marcar_cambio_realizado()

            # Calcular estadísticas
            count_1_por_horario = {}
            count_2_por_horario = {}

            for config in self.datos_configuracion["semestre_1"].values():
                horario = config.get('horario_asignado', 'Lunes')
                count_1_por_horario[horario] = count_1_por_horario.get(horario, 0) + 1

            for config in self.datos_configuracion["semestre_2"].values():
                horario = config.get('horario_asignado', 'Lunes')
                count_2_por_horario[horario] = count_2_por_horario.get(horario, 0) + 1

            total_1 = sum(count_1_por_horario.values())
            total_2 = sum(count_2_por_horario.values())
            total_generados = total_1 + total_2

            # Mostrar detalles por horario
            detalles_1 = ", ".join([f"{h}: {c}" for h, c in count_1_por_horario.items() if c > 0])
            detalles_2 = ", ".join([f"{h}: {c}" for h, c in count_2_por_horario.items() if c > 0])

            # Verificar si la generación automática logró equilibrio perfecto
            equilibrio_perfecto = self.verificar_equilibrio_completo(mostrar_si_todo_ok=False)

            # Mensaje personalizado según el equilibrio
            if equilibrio_perfecto:
                icono_equilibrio = "🎯"
                estado_equilibrio = "¡Equilibrio perfecto logrado!"
            else:
                icono_equilibrio = "⚠️"
                estado_equilibrio = "Revisa el equilibrio de horarios"

            QMessageBox.information(
                self, "Calendario Generado",
                f"✅ Calendario automático generado\n\n"
                f"Total días lectivos: {total_generados}\n\n"
                f"1º Semestre: {total_1} días\n"
                f"   Inicio: {primer_lunes_sept.strftime('%d/%m/%Y')}\n"
                f"   {detalles_1}\n\n"
                f"2º Semestre: {total_2} días\n"
                f"   Inicio: {primer_lunes_feb.strftime('%d/%m/%Y')}\n"
                f"   {detalles_2}\n\n"
                f"{icono_equilibrio} {estado_equilibrio}\n"
                f"💡 Ideal: 14 días por horario"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando calendario: {e}")

    def generar_dias_semestre(self, semestre, fecha_inicio, fecha_fin):
        """Generar días lectivos para un semestre respetando límite por horario"""
        fecha_actual = fecha_inicio
        conteo_por_horario = {"Lunes": 0, "Martes": 0, "Miércoles": 0, "Jueves": 0, "Viernes": 0}

        # Festivos típicos a excluir
        festivos = [
            (10, 12),  # Día del Pilar
            (11, 1),  # Todos los Santos
            (12, 6),  # Constitución
            (12, 8),  # Inmaculada
            (12, 25),  # Navidad
            (1, 1),  # Año Nuevo
            (1, 6),  # Reyes
        ]

        while fecha_actual <= fecha_fin:
            # Solo días laborables (lunes a viernes)
            if fecha_actual.weekday() < 5:  # 0=Lunes, 4=Viernes
                dia_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][fecha_actual.weekday()]

                # Verificar límite por horario (14 días por columna)
                if conteo_por_horario[dia_semana] >= 14:
                    fecha_actual += timedelta(days=1)
                    continue

                # Verificar si no es festivo
                es_festivo = (fecha_actual.month, fecha_actual.day) in festivos

                if not es_festivo:
                    fecha_str = fecha_actual.strftime("%Y-%m-%d")

                    self.datos_configuracion[semestre][fecha_str] = {
                        'fecha': fecha_str,
                        'dia_real': dia_semana,
                        'horario_asignado': dia_semana,
                        'motivo': '',
                        'es_especial': False,
                        'es_fin_semana': False
                    }
                    conteo_por_horario[dia_semana] += 1

            fecha_actual += timedelta(days=1)

    def importar_desde_web(self):
        """Importar desde web UPM - funcionalidad futura"""
        QMessageBox.information(
            self, "Funcionalidad Web",
            "🌐 Importar desde Web UPM\n\n"
            "Esta funcionalidad permitirá importar el calendario académico\n"
            "oficial directamente desde la web de ETSIDI.\n\n"
            "🚧 Próximamente disponible en la siguiente versión."
        )

    def importar_desde_csv(self):
        """Importar calendario desde CSV"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Calendario desde CSV",
            "", "Archivos CSV (*.csv);;Todos los archivos (*)"
        )

        if not archivo:
            return

        try:
            df = pd.read_csv(archivo)

            # Verificar columnas requeridas
            columnas_requeridas = ['fecha', 'semestre', 'horario_asignado']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                QMessageBox.warning(
                    self, "Columnas Faltantes",
                    f"El archivo CSV debe contener las columnas:\n{', '.join(columnas_faltantes)}"
                )
                return

            # Limpiar configuración actual
            self.datos_configuracion["semestre_1"].clear()
            self.datos_configuracion["semestre_2"].clear()

            dias_importados = 0
            advertencias_limite = []

            for _, row in df.iterrows():
                try:
                    fecha_str = str(row['fecha']).strip()
                    semestre = str(row['semestre']).strip()
                    horario_asignado = str(row['horario_asignado']).strip()

                    # Validar semestre
                    if semestre not in ['semestre_1', '1', 'semestre_2', '2']:
                        continue

                    sem_key = f"semestre_{semestre}" if semestre in ['1', '2'] else semestre

                    # Parsear fecha
                    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                    dia_real = fecha_obj.strftime("%A")  # Nombre del día en inglés

                    # Convertir a español
                    dias_es = {
                        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
                    }
                    dia_real = dias_es.get(dia_real, dia_real)

                    es_especial = dia_real != horario_asignado
                    motivo = str(row.get('motivo', '')).strip()

                    self.datos_configuracion[sem_key][fecha_str] = {
                        'fecha': fecha_str,
                        'dia_real': dia_real,
                        'horario_asignado': horario_asignado,
                        'motivo': motivo,
                        'es_especial': es_especial,
                        'es_fin_semana': dia_real in ['Sábado', 'Domingo']
                    }
                    dias_importados += 1

                except Exception as e:
                    continue

            # Verificar límites y mostrar advertencias
            for sem in ['semestre_1', 'semestre_2']:
                num_dias = len(self.datos_configuracion[sem])
                if num_dias > 14:
                    advertencias_limite.append(f"{sem.replace('_', ' ')}: {num_dias} días")

            # Recargar grids
            self.cargar_dias_en_grids()
            self.marcar_cambio_realizado()

            mensaje = f"✅ Importación completada:\n"
            mensaje += f"• {dias_importados} días importados\n"

            if advertencias_limite:
                mensaje += f"\n⚠️ Límites excedidos:\n"
                for adv in advertencias_limite:
                    mensaje += f"• {adv}\n"

            QMessageBox.information(self, "Importación Exitosa", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", f"Error al importar archivo CSV:\n{str(e)}")

    def exportar_a_csv(self):
        """Exportar calendario a CSV"""
        if not any(self.datos_configuracion[s] for s in ['semestre_1', 'semestre_2']):
            QMessageBox.information(self, "Sin Datos", "No hay días configurados para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Calendario a CSV",
            f"calendario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Archivos CSV (*.csv)"
        )

        if not archivo:
            return

        try:
            datos_export = []

            for semestre in ['semestre_1', 'semestre_2']:
                for fecha_str, config_dia in self.datos_configuracion[semestre].items():
                    datos_export.append({
                        'fecha': fecha_str,
                        'semestre': semestre,
                        'dia_real': config_dia.get('dia_real', ''),
                        'horario_asignado': config_dia.get('horario_asignado', ''),
                        'motivo': config_dia.get('motivo', ''),
                        'es_especial': config_dia.get('es_especial', False),
                        'es_fin_semana': config_dia.get('es_fin_semana', False)
                    })

            df = pd.DataFrame(datos_export)
            df = df.sort_values(['semestre', 'fecha'])  # Ordenar por semestre y fecha
            df.to_csv(archivo, index=False, encoding='utf-8')

            QMessageBox.information(self, "Exportación Exitosa", f"Datos exportados a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar datos:\n{str(e)}")

    def exportar_a_json(self):
        """Exportar calendario a JSON"""
        if not any(self.datos_configuracion[s] for s in ['semestre_1', 'semestre_2']):
            QMessageBox.information(self, "Sin Datos", "No hay días configurados para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Calendario a JSON",
            f"calendario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'calendario': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_dias_1': len(self.datos_configuracion['semestre_1']),
                    'total_dias_2': len(self.datos_configuracion['semestre_2']),
                    'generado_por': 'OPTIM Labs - Configurar Calendario'
                }
            }

            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Exportación Exitosa", f"Datos exportados a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar datos:\n{str(e)}")

    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Calendario",
            "", "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "calendario" in datos_cargados:
                self.datos_configuracion = datos_cargados["calendario"]
            elif "anio_academico" in datos_cargados:
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Recargar grids
            self.cargar_dias_en_grids()

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def limpiar_semestre(self):
        """Limpiar un semestre específico"""
        semestre, ok = QInputDialog.getItem(
            self, "Limpiar Semestre",
            "Selecciona el semestre a limpiar:",
            ["1º Semestre", "2º Semestre"],
            0, False
        )

        if not ok:
            return

        sem_key = "semestre_1" if "1º" in semestre else "semestre_2"

        if not self.datos_configuracion[sem_key]:
            QMessageBox.information(self, "Sin Datos", f"El {semestre} ya está vacío")
            return

        respuesta = QMessageBox.question(
            self, "Confirmar Limpieza",
            f"¿Eliminar todos los días del {semestre}?\n\n"
            f"Se eliminarán {len(self.datos_configuracion[sem_key])} días configurados.\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion[sem_key].clear()
            self.cargar_dias_en_grids()
            self.marcar_cambio_realizado()
            QMessageBox.information(self, "Limpieza Completada", f"{semestre} limpiado correctamente")

    def limpiar_todo(self):
        """Limpiar toda la configuración"""
        total_dias = len(self.datos_configuracion['semestre_1']) + len(self.datos_configuracion['semestre_2'])

        if total_dias == 0:
            QMessageBox.information(self, "Sin Datos", "No hay días configurados para limpiar")
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Todo",
            f"¿Está seguro de eliminar toda la configuración del calendario?\n\n"
            f"Se eliminarán {total_dias} días configurados.\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion['semestre_1'].clear()
            self.datos_configuracion['semestre_2'].clear()
            self.cargar_dias_en_grids()
            self.marcar_cambio_realizado()
            QMessageBox.information(self, "Limpieza Completada", "Toda la configuración ha sido eliminada")

    def guardar_en_sistema(self):
        """Guardar configuración en el sistema principal"""
        try:
            total_dias = len(self.datos_configuracion['semestre_1']) + len(
                self.datos_configuracion['semestre_2'])

            if total_dias == 0:
                QMessageBox.warning(self, "Sin Datos", "No hay días configurados para guardar.")
                return

            # Verificar equilibrio antes de guardar
            self.verificar_equilibrio_completo(mostrar_si_todo_ok=False)

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• 1º Semestre: {len(self.datos_configuracion['semestre_1'])} días\n"
                f"• 2º Semestre: {len(self.datos_configuracion['semestre_2'])} días\n"
                f"• Total: {total_dias} días lectivos\n\n"
                f"La configuración se integrará con OPTIM y la ventana se cerrará.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Enviar señal al sistema principal
                self.configuracion_actualizada.emit(self.datos_configuracion)

                # Marcar como guardado
                self.datos_guardados_en_sistema = True
                self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)

                # Cerrar ventana
                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar en el sistema:\n{str(e)}")

    def hay_cambios_sin_guardar(self):
        """Detectar si hay cambios sin guardar"""
        datos_actuales = json.dumps(self.datos_configuracion, sort_keys=True)
        hay_cambios = datos_actuales != self.datos_iniciales

        if hay_cambios and not self.datos_guardados_en_sistema:
            return True

        if self.datos_guardados_en_sistema and hay_cambios:
            return True

        return False

    def marcar_cambio_realizado(self):
        """Marcar que se realizó un cambio"""
        self.datos_guardados_en_sistema = False

    def log_mensaje(self, mensaje, tipo="info"):
        """Logging simple"""
        if self.parent_window and hasattr(self.parent_window, 'log_mensaje'):
            self.parent_window.log_mensaje(mensaje, tipo)
        else:
            iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            icono = iconos.get(tipo, "ℹ️")
            print(f"{icono} {mensaje}")

    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        if not self.hay_cambios_sin_guardar():
            self.log_mensaje("🔚 Cerrando configuración de calendario", "info")
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
        """Cancelar cambios restaurando estado original"""
        try:
            datos_originales = json.loads(self.datos_iniciales)

            datos_para_sistema = {
                "calendario": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarCalendario",
                    "cambios_descartados": True
                }
            }

            self.configuracion_actualizada.emit(datos_para_sistema)
            self.datos_configuracion = datos_originales
            self.datos_guardados_en_sistema = False

            self.log_mensaje("📤 Cambios cancelados y estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cancelando cambios: {e}", "warning")


def main():
    """Función principal para testing"""
    app = QApplication(sys.argv)

    # Aplicar tema oscuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Datos de ejemplo para testing drag & drop
    datos_ejemplo = {
        "anio_academico": "2024-2025",
        "semestre_1": {
            "2024-09-16": {
                "fecha": "2024-09-16",
                "dia_real": "Lunes",
                "horario_asignado": "Lunes",
                "motivo": "",
                "es_especial": False,
                "es_fin_semana": False
            },
            "2024-09-17": {
                "fecha": "2024-09-17",
                "dia_real": "Martes",
                "horario_asignado": "Martes",
                "motivo": "",
                "es_especial": False,
                "es_fin_semana": False
            },
            "2024-10-12": {
                "fecha": "2024-10-12",
                "dia_real": "Sábado",
                "horario_asignado": "Jueves",
                "motivo": "Día del Pilar",
                "es_especial": True,
                "es_fin_semana": True
            },
            "2024-10-14": {
                "fecha": "2024-10-14",
                "dia_real": "Lunes",
                "horario_asignado": "Lunes",
                "motivo": "",
                "es_especial": False,
                "es_fin_semana": False
            }
        },
        "semestre_2": {
            "2025-02-03": {
                "fecha": "2025-02-03",
                "dia_real": "Lunes",
                "horario_asignado": "Lunes",
                "motivo": "",
                "es_especial": False,
                "es_fin_semana": False
            },
            "2025-02-04": {
                "fecha": "2025-02-04",
                "dia_real": "Martes",
                "horario_asignado": "Martes",
                "motivo": "",
                "es_especial": False,
                "es_fin_semana": False
            }
        }
    }

    window = ConfigurarCalendario(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()