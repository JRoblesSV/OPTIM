#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Profesores - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión completa de plantilla docente del centro
2. Asignación de asignaturas por profesor con validación cruzada
3. Configuración de disponibilidad semanal personalizada
4. Gestión de fechas específicas no disponibles por calendario
5. Filtros inteligentes por asignatura y disponibilidad temporal
6. Estadísticas de cobertura docente por asignatura
7. Import/Export desde CSV con procesamiento de horarios
8. Duplicación de perfiles docentes con datos modificables
9. Detección automática de profesores duplicados
10. Sincronización con sistema de asignaturas configuradas

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QGroupBox, QFrame, QScrollArea, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QFormLayout, QSizePolicy,
    QCalendarWidget, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QPalette, QColor


def center_window_on_screen_immediate(window, width, height):
    """Centrar ventana ANTES de mostrarla - SIN PARPADEO"""
    try:
        from PyQt6.QtWidgets import QApplication

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


class GestionProfesorDialog(QDialog):
    """Dialog para añadir/editar profesor con gestión de asignaturas y disponibilidad"""

    def __init__(self, profesor_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        self.profesor_existente = profesor_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {"1": {}, "2": {}}
        self.setWindowTitle("Editar Profesor" if profesor_existente else "Nuevo Profesor")
        self.setModal(True)

        # CENTRAR INMEDIATAMENTE SIN PARPADEO
        window_width = 800
        window_height = 950
        center_window_on_screen_immediate(self, window_width, window_height)
        self.setMinimumSize(750, 800)

        self.setup_ui()
        self.apply_dark_theme()

        if self.profesor_existente:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 👤 DATOS PERSONALES
        datos_personales_group = QGroupBox("👤 DATOS PERSONALES")
        datos_personales_layout = QGridLayout()

        # Fila 1: DNI | Email
        self.edit_dni = QLineEdit()
        self.edit_dni.setPlaceholderText("Ej: 12345678A")
        self.edit_dni.setMaxLength(9)

        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("Ej: juan.garcia@upm.es")

        datos_personales_layout.addWidget(QLabel("🆔 DNI:"), 0, 0)
        datos_personales_layout.addWidget(self.edit_dni, 0, 1)
        datos_personales_layout.addWidget(QLabel("📧 Email:"), 0, 2)
        datos_personales_layout.addWidget(self.edit_email, 0, 3)

        # Fila 2: Nombre | Apellidos
        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Ej: Juan")

        self.edit_apellidos = QLineEdit()
        self.edit_apellidos.setPlaceholderText("Ej: García López")

        datos_personales_layout.addWidget(QLabel("👤 Nombre:"), 1, 0)
        datos_personales_layout.addWidget(self.edit_nombre, 1, 1)
        datos_personales_layout.addWidget(QLabel("👤 Apellidos:"), 1, 2)
        datos_personales_layout.addWidget(self.edit_apellidos, 1, 3)

        datos_personales_group.setLayout(datos_personales_layout)
        layout.addWidget(datos_personales_group)

        # 📚 ASIGNATURAS QUE PUEDE IMPARTIR
        asignaturas_group = QGroupBox("📚 ASIGNATURAS QUE PUEDE IMPARTIR")
        asignaturas_layout = QVBoxLayout()

        info_asig_label = QLabel("Selecciona las asignaturas que este profesor puede impartir:")
        info_asig_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 6px;")
        asignaturas_layout.addWidget(info_asig_label)

        # SCROLL AREA PARA ASIGNATURAS
        self.asignaturas_scroll = QScrollArea()
        self.asignaturas_scroll.setWidgetResizable(True)
        self.asignaturas_scroll.setFixedHeight(180)
        self.asignaturas_scroll.setMinimumWidth(400)
        self.asignaturas_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.asignaturas_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.asignaturas_scroll.setFrameStyle(QFrame.Shape.Box)
        self.asignaturas_scroll.setLineWidth(1)

        # Widget scrollable para asignaturas
        self.asignaturas_scroll_widget = QWidget()
        self.asignaturas_scroll_widget.setMinimumSize(380, 200)
        self.asignaturas_scroll_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # Layout del widget scrollable - VERTICAL CON HEADER + GRID
        self.asignaturas_scroll_layout = QVBoxLayout()
        self.asignaturas_scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.asignaturas_scroll_layout.setSpacing(12)

        # Configurar layout en el widget
        self.asignaturas_scroll_widget.setLayout(self.asignaturas_scroll_layout)

        # Diccionario para checkboxes de asignaturas
        self.checks_asignaturas = {}

        # Crear checkboxes de asignaturas
        self.crear_checkboxes_asignaturas()

        # Configurar scroll area
        self.asignaturas_scroll.setWidget(self.asignaturas_scroll_widget)
        asignaturas_layout.addWidget(self.asignaturas_scroll)

        asignaturas_group.setLayout(asignaturas_layout)
        layout.addWidget(asignaturas_group)

        # TABS PARA DISPONIBILIDAD Y DÍAS NO DISPONIBLES
        tabs_widget = QTabWidget()

        # TAB 1: DISPONIBILIDAD SEMANAL
        tab_disponibilidad = QWidget()
        tab_disp_layout = QVBoxLayout(tab_disponibilidad)

        disp_info_label = QLabel("Marca los días de la semana en los que el profesor está disponible:")
        disp_info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 8px;")
        tab_disp_layout.addWidget(disp_info_label)

        # Crear checkboxes para días de la semana
        self.crear_disponibilidad_semanal()
        tab_disp_layout.addWidget(self.frame_disponibilidad)

        tabs_widget.addTab(tab_disponibilidad, "📅 Disponibilidad Semanal")

        # TAB 2: DÍAS NO DISPONIBLES
        tab_no_disponibles = QWidget()
        tab_no_disp_layout = QVBoxLayout(tab_no_disponibles)

        no_disp_info_label = QLabel("Fechas específicas en las que el profesor NO estará disponible:")
        no_disp_info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 8px;")
        tab_no_disp_layout.addWidget(no_disp_info_label)

        # Layout horizontal para calendario y lista
        no_disp_horizontal = QHBoxLayout()

        # Calendario para seleccionar fechas
        self.calendario = QCalendarWidget()
        self.calendario.setMaximumSize(350, 250)
        self.calendario.clicked.connect(self.agregar_fecha_no_disponible)
        no_disp_horizontal.addWidget(self.calendario)

        # Lista de fechas no disponibles
        no_disp_derecha = QVBoxLayout()

        fechas_label = QLabel("📅 Fechas seleccionadas:")
        fechas_label.setStyleSheet("font-weight: bold; color: #4a9eff;")
        no_disp_derecha.addWidget(fechas_label)

        self.lista_fechas_no_disponibles = QListWidget()
        self.lista_fechas_no_disponibles.setMaximumHeight(180)
        no_disp_derecha.addWidget(self.lista_fechas_no_disponibles)

        # Botón para eliminar fecha seleccionada
        btn_eliminar_fecha = QPushButton("🗑️ Eliminar Fecha Seleccionada")
        btn_eliminar_fecha.clicked.connect(self.eliminar_fecha_no_disponible)
        no_disp_derecha.addWidget(btn_eliminar_fecha)

        no_disp_horizontal.addLayout(no_disp_derecha)
        tab_no_disp_layout.addLayout(no_disp_horizontal)

        tabs_widget.addTab(tab_no_disponibles, "❌ Días No Disponibles")

        layout.addWidget(tabs_widget)

        # 📝 OBSERVACIONES
        observaciones_group = QGroupBox("📝 OBSERVACIONES")
        observaciones_layout = QVBoxLayout()

        self.edit_observaciones = QTextEdit()
        self.edit_observaciones.setMaximumHeight(60)
        self.edit_observaciones.setPlaceholderText("Observaciones adicionales sobre el profesor...")
        observaciones_layout.addWidget(self.edit_observaciones)

        observaciones_group.setLayout(observaciones_layout)
        layout.addWidget(observaciones_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def crear_checkboxes_asignaturas(self):
        """Crear checkboxes para todas las asignaturas disponibles en GRID 5 COLUMNAS"""
        # Limpiar layout
        while self.asignaturas_scroll_layout.count():
            child = self.asignaturas_scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Procesar eventos pendientes
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Verificar si hay asignaturas disponibles
        sem1 = self.asignaturas_disponibles.get("1", {})
        sem2 = self.asignaturas_disponibles.get("2", {})

        if not sem1 and not sem2:
            no_asig_label = QLabel(
                "⚠️ No hay asignaturas configuradas en el sistema.\n\n💡 Configura primero las asignaturas en el sistema principal.")
            no_asig_label.setStyleSheet("""
                color: #ffaa00; 
                font-style: italic; 
                font-size: 13px;
                padding: 30px 20px; 
                text-align: center;
                background-color: rgba(255, 170, 0, 0.1);
                border: 1px dashed #ffaa00;
                border-radius: 6px;
                margin: 20px;
            """)
            no_asig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_asig_label.setWordWrap(True)
            self.asignaturas_scroll_layout.addWidget(no_asig_label)
            return

        # 1º Semestre
        if sem1:
            sem1_label = QLabel("📋 1º SEMESTRE")
            sem1_label.setStyleSheet("""
                color: #90EE90; 
                font-weight: bold; 
                font-size: 14px;
                margin: 5px 0px 8px 0px;
                padding: 8px;
                background-color: rgba(144, 238, 144, 0.15);
                border: 1px solid rgba(144, 238, 144, 0.3);
                border-radius: 6px;
                text-align: center;
            """)
            sem1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.asignaturas_scroll_layout.addWidget(sem1_label)

            # Crear GRID para 1º semestre
            self.crear_grid_asignaturas(sem1, "1")

        # 2º Semestre
        if sem2:
            # Espaciador entre semestres
            if sem1:
                espaciador = QLabel("")
                espaciador.setFixedHeight(15)
                self.asignaturas_scroll_layout.addWidget(espaciador)

            sem2_label = QLabel("📋 2º SEMESTRE")
            sem2_label.setStyleSheet("""
                color: #FFB347; 
                font-weight: bold; 
                font-size: 14px;
                margin: 5px 0px 8px 0px;
                padding: 8px;
                background-color: rgba(255, 179, 71, 0.15);
                border: 1px solid rgba(255, 179, 71, 0.3);
                border-radius: 6px;
                text-align: center;
            """)
            sem2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.asignaturas_scroll_layout.addWidget(sem2_label)

            # Crear GRID para 2º semestre
            self.crear_grid_asignaturas(sem2, "2")

        # Añadir stretch al final
        self.asignaturas_scroll_layout.addStretch()

        # Actualizar scroll
        QApplication.processEvents()

        # Forzar recálculo del tamaño del contenido
        total_height = 0
        for i in range(self.asignaturas_scroll_layout.count()):
            item = self.asignaturas_scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                widget.adjustSize()
                total_height += widget.sizeHint().height()

        # Establecer tamaño mínimo basado en contenido
        self.asignaturas_scroll_widget.setMinimumHeight(max(200, total_height + 50))

        self.asignaturas_scroll_widget.adjustSize()
        self.asignaturas_scroll.updateGeometry()

        # Procesar eventos finales
        QApplication.processEvents()

    def crear_grid_asignaturas(self, asignaturas_dict, semestre):
        """Crear grid de 5 columnas para las asignaturas de un semestre"""
        # Crear widget contenedor para el grid
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(10, 5, 10, 5)
        grid_layout.setSpacing(8)

        # Configurar 5 columnas
        COLUMNAS = 5
        asignaturas_lista = sorted(asignaturas_dict.keys())

        fila = 0
        columna = 0

        for asignatura in asignaturas_lista:
            key_asignatura = f"{semestre}_{asignatura}"
            check_asignatura = QCheckBox(asignatura)
            check_asignatura.setStyleSheet("""
                QCheckBox {
                    font-size: 11px;
                    font-weight: 500;
                    padding: 6px 8px;
                    color: #ffffff;
                    margin: 2px;
                    min-height: 18px;
                    max-width: 140px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    margin-right: 6px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #3c3c3c;
                    border: 2px solid #666666;
                    border-radius: 3px;
                }
                QCheckBox::indicator:unchecked:hover {
                    border-color: #4a9eff;
                    background-color: #4a4a4a;
                }
                QCheckBox::indicator:checked {
                    background-color: #4a9eff;
                    border: 2px solid #4a9eff;
                    border-radius: 3px;
                }
                QCheckBox:hover {
                    background-color: rgba(74, 158, 255, 0.1);
                    border-radius: 4px;
                }
            """)

            self.checks_asignaturas[key_asignatura] = check_asignatura

            # Añadir al grid
            grid_layout.addWidget(check_asignatura, fila, columna)

            # Avanzar posición
            columna += 1
            if columna >= COLUMNAS:
                columna = 0
                fila += 1

        # Configurar expansión de columnas para que se distribuyan uniformemente
        for col in range(COLUMNAS):
            grid_layout.setColumnStretch(col, 1)

        # Añadir el widget del grid al layout principal
        self.asignaturas_scroll_layout.addWidget(grid_widget)

    def crear_disponibilidad_semanal(self):
        """Crear checkboxes para disponibilidad semanal"""
        self.frame_disponibilidad = QFrame()
        self.frame_disponibilidad.setFrameStyle(QFrame.Shape.Box)
        self.frame_disponibilidad.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
            }
        """)

        layout_disponibilidad = QVBoxLayout(self.frame_disponibilidad)
        layout_disponibilidad.setSpacing(10)

        # Título
        titulo_disp = QLabel("📅 Días de trabajo:")
        titulo_disp.setStyleSheet("font-weight: bold; color: #4a9eff; font-size: 13px; margin-bottom: 8px;")
        layout_disponibilidad.addWidget(titulo_disp)

        # Días de la semana
        self.dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        self.checks_dias_trabajo = {}

        # Layout horizontal para los días
        dias_layout = QHBoxLayout()
        dias_layout.setSpacing(20)

        for dia in self.dias_semana:
            check_dia = QCheckBox(dia)
            check_dia.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px;
                    color: #ffffff;
                    min-width: 80px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    margin-right: 8px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #4a4a4a;
                    border: 2px solid #666666;
                    border-radius: 4px;
                }
                QCheckBox::indicator:unchecked:hover {
                    border-color: #4a9eff;
                    background-color: #5a5a5a;
                }
                QCheckBox::indicator:checked {
                    background-color: #4a9eff;
                    border: 2px solid #4a9eff;
                    border-radius: 4px;
                }
                QCheckBox:hover {
                    background-color: rgba(74, 158, 255, 0.1);
                    border-radius: 6px;
                }
            """)
            self.checks_dias_trabajo[dia] = check_dia
            dias_layout.addWidget(check_dia)

        layout_disponibilidad.addLayout(dias_layout)

        # Información adicional
        info_extra = QLabel("💡 El profesor podrá dar clases solo en los días marcados")
        info_extra.setStyleSheet("color: #90EE90; font-size: 14px; font-style: italic; margin-top: 3px;")
        layout_disponibilidad.addWidget(info_extra)

    def agregar_fecha_no_disponible(self, fecha):
        """Agregar fecha a la lista de no disponibles"""
        fecha_str = fecha.toString("dd/MM/yyyy")

        # Verificar si ya existe
        for i in range(self.lista_fechas_no_disponibles.count()):
            if self.lista_fechas_no_disponibles.item(i).text() == fecha_str:
                return

        # Añadir a la lista
        item = QListWidgetItem(fecha_str)
        item.setData(Qt.ItemDataRole.UserRole, fecha)
        self.lista_fechas_no_disponibles.addItem(item)

        # Ordenar lista por fecha
        self.ordenar_fechas_no_disponibles()

    def eliminar_fecha_no_disponible(self):
        """Eliminar fecha seleccionada de la lista"""
        current_item = self.lista_fechas_no_disponibles.currentItem()
        if current_item:
            row = self.lista_fechas_no_disponibles.row(current_item)
            self.lista_fechas_no_disponibles.takeItem(row)

    def ordenar_fechas_no_disponibles(self):
        """Ordenar fechas no disponibles cronológicamente"""
        fechas = []
        for i in range(self.lista_fechas_no_disponibles.count()):
            item = self.lista_fechas_no_disponibles.item(i)
            fecha = item.data(Qt.ItemDataRole.UserRole)
            fechas.append((fecha, item.text()))

        # Ordenar por fecha usando getDate() que es compatible con PyQt6
        fechas.sort(key=lambda x: x[0].getDate())  # getDate() devuelve (año, mes, día)

        # Limpiar y rellenar lista
        self.lista_fechas_no_disponibles.clear()
        for fecha, texto in fechas:
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, fecha)
            self.lista_fechas_no_disponibles.addItem(item)

    def cargar_datos_existentes(self):
        """Cargar datos del profesor existente"""
        if not self.profesor_existente:
            return

        datos = self.profesor_existente

        # Datos personales
        self.edit_dni.setText(datos.get('dni', ''))
        self.edit_nombre.setText(datos.get('nombre', ''))
        self.edit_apellidos.setText(datos.get('apellidos', ''))
        self.edit_email.setText(datos.get('email', ''))

        # Observaciones
        self.edit_observaciones.setText(datos.get('observaciones', ''))

        # Asignaturas que puede impartir
        asignaturas_imparte = datos.get('asignaturas_puede_impartir', [])
        for key, check in self.checks_asignaturas.items():
            if key in asignaturas_imparte:
                check.setChecked(True)

        # Disponibilidad semanal
        dias_trabajo = datos.get('dias_trabajo', [])
        for dia, check in self.checks_dias_trabajo.items():
            if dia in dias_trabajo:
                check.setChecked(True)

        # Fechas no disponibles
        fechas_no_disponibles = datos.get('fechas_no_disponibles', [])
        for fecha_str in fechas_no_disponibles:
            try:
                # Convertir string a QDate
                fecha_parts = fecha_str.split('/')
                if len(fecha_parts) == 3:
                    dia, mes, ano = map(int, fecha_parts)
                    fecha = QDate(ano, mes, dia)
                    self.agregar_fecha_no_disponible(fecha)
            except Exception as e:
                print(f"Error cargando fecha {fecha_str}: {e}")

    def validar_y_aceptar(self):
        """Validar datos antes de aceptar"""
        if not self.edit_dni.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El DNI es obligatorio")
            self.edit_dni.setFocus()
            return

        if not self.edit_nombre.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre es obligatorio")
            self.edit_nombre.setFocus()
            return

        if not self.edit_apellidos.text().strip():
            QMessageBox.warning(self, "Campo requerido", "Los apellidos son obligatorios")
            self.edit_apellidos.setFocus()
            return

        # Validar que al menos una asignatura esté seleccionada
        asignaturas_seleccionadas = [key for key, check in self.checks_asignaturas.items() if check.isChecked()]
        if not asignaturas_seleccionadas:
            QMessageBox.warning(self, "Asignaturas requeridas",
                                "El profesor debe poder impartir al menos una asignatura")
            return

        # Validar que tenga al menos un día de trabajo
        dias_marcados = [dia for dia, check in self.checks_dias_trabajo.items() if check.isChecked()]
        if not dias_marcados:
            QMessageBox.warning(self, "Disponibilidad requerida",
                                "El profesor debe tener al menos un día de trabajo disponible")
            return

        self.accept()

    def get_datos_profesor(self):
        """Obtener datos configurados del profesor"""
        # Obtener asignaturas que puede impartir
        asignaturas_puede_impartir = [key for key, check in self.checks_asignaturas.items() if check.isChecked()]

        # Obtener días de trabajo
        dias_trabajo = [dia for dia, check in self.checks_dias_trabajo.items() if check.isChecked()]

        # Obtener fechas no disponibles
        fechas_no_disponibles = []
        for i in range(self.lista_fechas_no_disponibles.count()):
            item = self.lista_fechas_no_disponibles.item(i)
            fechas_no_disponibles.append(item.text())

        return {
            # Datos personales
            'dni': self.edit_dni.text().strip().upper(),
            'nombre': self.edit_nombre.text().strip(),
            'apellidos': self.edit_apellidos.text().strip(),
            'email': self.edit_email.text().strip().lower(),

            # Asignaturas
            'asignaturas_puede_impartir': asignaturas_puede_impartir,

            # Disponibilidad
            'dias_trabajo': dias_trabajo,
            'fechas_no_disponibles': fechas_no_disponibles,

            # Observaciones
            'observaciones': self.edit_observaciones.toPlainText().strip(),

            # Metadatos
            'fecha_creacion': datetime.now().isoformat()
        }

    def apply_dark_theme(self):
        """Aplicar tema oscuro idéntico al sistema"""
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
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus {
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
                border: 2px solid #666666;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #4a9eff;
                background-color: #4a4a4a;
            }
            QScrollArea {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a9eff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QCalendarWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
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
            QTabWidget::pane {
                border: 1px solid #4a4a4a;
                background-color: #2b2b2b;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 8px 20px;
                margin: 2px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #5a5a5a;
            }
        """)


class ConfigurarProfesores(QMainWindow):
    """Ventana principal para configurar profesores del centro"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Profesores - OPTIM Labs")

        # CENTRAR INMEDIATAMENTE SIN PARPADEO
        window_width = 1350
        window_height = 850
        center_window_on_screen_immediate(self, window_width, window_height)
        self.setMinimumSize(1250, 800)

        # Obtener asignaturas disponibles desde el sistema global
        self.asignaturas_disponibles = self.obtener_asignaturas_del_sistema()

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("📥 Cargando configuración existente de profesores...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("📝 Iniciando configuración nueva de profesores...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.profesor_actual = None
        self.filtro_asignatura_actual = "Todas las asignaturas"

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    def obtener_asignaturas_del_sistema(self):
        """Obtener asignaturas configuradas desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                # Buscar en asignaturas
                config_asignaturas = self.parent_window.configuracion["configuracion"]["asignaturas"]

                if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                    # Transformar datos de asignaturas al formato esperado por la ventana
                    asignaturas_transformadas = {"1": {}, "2": {}}

                    for codigo, asig_data in config_asignaturas["datos"].items():
                        nombre = asig_data.get("nombre", "")
                        semestre_str = asig_data.get("semestre", "1º Semestre")

                        # Detectar semestre: "1º Semestre" -> "1", "2º Semestre" -> "2"
                        if "1º" in semestre_str or "primer" in semestre_str.lower():
                            semestre = "1"
                        elif "2º" in semestre_str or "segundo" in semestre_str.lower():
                            semestre = "2"
                        else:
                            semestre = "1"  # Por defecto

                        # Añadir asignatura al semestre correspondiente
                        if nombre:  # Solo si tiene nombre
                            asignaturas_transformadas[semestre][nombre] = asig_data

                    return asignaturas_transformadas

            return {"1": {}, "2": {}}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo asignaturas del sistema: {e}", "warning")
            return {"1": {}, "2": {}}

    def cargar_datos_iniciales(self):
        """Cargar datos existentes al inicializar"""
        try:
            # Ordenar profesores alfabéticamente
            self.ordenar_profesores_alfabeticamente()

            # Cargar lista con filtro inicial
            self.aplicar_filtro_asignatura()

            # Mostrar resumen
            total_profesores = len(self.datos_configuracion)
            if total_profesores > 0:
                self.log_mensaje(f"✅ Datos cargados: {total_profesores} profesores", "success")
                self.auto_seleccionar_primer_profesor()
            else:
                self.log_mensaje("📝 No hay profesores configurados - configuración nueva", "info")

            # Actualizar estadísticas
            self.actualizar_estadisticas()

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primer_profesor(self):
        """Auto-seleccionar primer profesor disponible"""
        try:
            if self.list_profesores.count() > 0:
                primer_item = self.list_profesores.item(0)
                if primer_item and primer_item.flags() != Qt.ItemFlag.NoItemFlags:
                    self.list_profesores.setCurrentItem(primer_item)
                    self.seleccionar_profesor(primer_item)
                    self.log_mensaje(f"🎯 Auto-seleccionado: {primer_item.text().split(' - ')[0]}", "info")
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando profesor: {e}", "warning")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("👨‍🏫 CONFIGURACIÓN DE PROFESORES")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información contextual
        info_label = QLabel(
            "📋 Gestiona la plantilla de profesores del centro. Configura qué asignaturas puede impartir cada uno y su disponibilidad.")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de profesores con filtros
        left_panel = QGroupBox("👨‍🏫 PROFESORES REGISTRADOS")
        left_layout = QVBoxLayout()

        # Filtros
        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Filtros:"))

        self.combo_filtro_asignatura = QComboBox()
        self.combo_filtro_asignatura.setMaximumWidth(180)
        filtros_layout.addWidget(self.combo_filtro_asignatura)

        self.check_solo_disponibles = QCheckBox("Solo disponibles hoy")
        self.check_solo_disponibles.setToolTip("Mostrar solo profesores disponibles en el día actual")
        filtros_layout.addWidget(self.check_solo_disponibles)

        filtros_layout.addStretch()
        left_layout.addLayout(filtros_layout)

        # Gestión de profesores
        gestion_layout = QHBoxLayout()
        gestion_layout.addWidget(QLabel("Gestión:"))
        gestion_layout.addStretch()

        # Botones de gestión
        btn_add_profesor = self.crear_boton_accion("➕", "#4CAF50", "Añadir nuevo profesor")
        btn_add_profesor.clicked.connect(self.anadir_profesor)

        btn_edit_profesor = self.crear_boton_accion("✏️", "#2196F3", "Editar profesor seleccionado")
        btn_edit_profesor.clicked.connect(self.editar_profesor_seleccionado)

        btn_delete_profesor = self.crear_boton_accion("🗑️", "#f44336", "Eliminar profesor seleccionado")
        btn_delete_profesor.clicked.connect(self.eliminar_profesor_seleccionado)

        gestion_layout.addWidget(btn_add_profesor)
        gestion_layout.addWidget(btn_edit_profesor)
        gestion_layout.addWidget(btn_delete_profesor)

        left_layout.addLayout(gestion_layout)

        # Lista de profesores
        self.list_profesores = QListWidget()
        self.list_profesores.setMaximumWidth(350)
        self.list_profesores.setMinimumHeight(400)
        left_layout.addWidget(self.list_profesores)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Detalles del profesor
        center_panel = QGroupBox("👤 DETALLES DEL PROFESOR")
        center_layout = QVBoxLayout()

        # Nombre del profesor seleccionado
        self.label_profesor_actual = QLabel("Seleccione un profesor")
        self.label_profesor_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_profesor_actual)

        # Información detallada
        self.info_profesor = QTextEdit()
        self.info_profesor.setMaximumHeight(250)
        self.info_profesor.setReadOnly(True)
        self.info_profesor.setText("ℹ️ Seleccione un profesor para ver sus detalles")
        center_layout.addWidget(self.info_profesor)

        # Estadísticas por asignatura
        stats_group = QGroupBox("📊 ESTADÍSTICAS POR ASIGNATURA")
        stats_layout = QVBoxLayout()

        # Botón para actualizar estadísticas
        self.btn_actualizar_stats = QPushButton("📈 Actualizar Estadísticas")
        self.btn_actualizar_stats.clicked.connect(self.actualizar_estadisticas)
        stats_layout.addWidget(self.btn_actualizar_stats)

        self.texto_stats = QTextEdit()
        self.texto_stats.setMaximumHeight(120)
        self.texto_stats.setReadOnly(True)
        self.texto_stats.setText("📈 Presiona 'Actualizar' para ver estadísticas")
        stats_layout.addWidget(self.texto_stats)

        stats_group.setLayout(stats_layout)
        center_layout.addWidget(stats_group)

        center_panel.setLayout(center_layout)
        content_layout.addWidget(center_panel)

        # Columna derecha - Acciones rápidas y configuración
        right_panel = QGroupBox("🔧 GESTIÓN Y CONFIGURACIÓN")
        right_layout = QVBoxLayout()

        # Acciones rápidas
        acciones_group = QGroupBox("🚀 ACCIONES RÁPIDAS")
        acciones_layout = QVBoxLayout()

        self.btn_duplicar = QPushButton("📋 Duplicar Profesor Seleccionado")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_profesor_seleccionado)
        acciones_layout.addWidget(self.btn_duplicar)

        self.btn_gestionar_disponibilidad = QPushButton("📅 Gestionar Disponibilidad")
        self.btn_gestionar_disponibilidad.setEnabled(False)
        self.btn_gestionar_disponibilidad.clicked.connect(self.gestionar_disponibilidad)
        acciones_layout.addWidget(self.btn_gestionar_disponibilidad)

        self.btn_buscar_duplicados = QPushButton("🔍 Buscar Duplicados")
        self.btn_buscar_duplicados.clicked.connect(self.buscar_duplicados)
        acciones_layout.addWidget(self.btn_buscar_duplicados)

        self.btn_sincronizar = QPushButton("🔄 Sincronizar Asignaturas")
        self.btn_sincronizar.setToolTip("Sincronizar con las asignaturas configuradas en el sistema")
        self.btn_sincronizar.clicked.connect(self.sincronizar_asignaturas)
        acciones_layout.addWidget(self.btn_sincronizar)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Importar datos
        importar_group = QGroupBox("📥 IMPORTAR DATOS")
        importar_layout = QVBoxLayout()

        self.btn_importar_csv = QPushButton("📥 Importar desde CSV")
        self.btn_importar_csv.clicked.connect(self.importar_desde_csv)
        importar_layout.addWidget(self.btn_importar_csv)

        self.btn_cargar = QPushButton("📁 Cargar Configuración")
        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Exportar datos
        exportar_group = QGroupBox("📤 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

        self.btn_exportar_csv = QPushButton("📄 Exportar a CSV")
        self.btn_exportar_csv.clicked.connect(self.exportar_a_csv)
        exportar_layout.addWidget(self.btn_exportar_csv)

        self.btn_exportar_estadisticas = QPushButton("📊 Exportar Estadísticas")
        self.btn_exportar_estadisticas.clicked.connect(self.exportar_estadisticas)
        exportar_layout.addWidget(self.btn_exportar_estadisticas)

        exportar_group.setLayout(exportar_layout)
        right_layout.addWidget(exportar_group)

        # Guardar configuración
        botones_principales_group = QGroupBox("💾 GUARDAR CONFIGURACIÓN")
        botones_layout = QVBoxLayout()

        self.btn_guardar_archivo = QPushButton("💾 Guardar en Archivo")
        self.btn_guardar_archivo.clicked.connect(self.guardar_en_archivo)
        botones_layout.addWidget(self.btn_guardar_archivo)

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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todos_profesores)
        botones_layout.addWidget(self.btn_limpiar_todo)

        botones_principales_group.setLayout(botones_layout)
        right_layout.addWidget(botones_principales_group)

        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

        # Configurar filtros
        self.configurar_filtros()

    def configurar_filtros(self):
        """Configurar opciones de filtros"""
        # Llenar combo de asignaturas
        self.combo_filtro_asignatura.clear()
        self.combo_filtro_asignatura.addItem("Todas las asignaturas")

        # Añadir asignaturas por semestre
        sem1 = self.asignaturas_disponibles.get("1", {})
        sem2 = self.asignaturas_disponibles.get("2", {})

        if sem1:
            for asignatura in sorted(sem1.keys()):
                self.combo_filtro_asignatura.addItem(f"1º - {asignatura}")

        if sem2:
            for asignatura in sorted(sem2.keys()):
                self.combo_filtro_asignatura.addItem(f"2º - {asignatura}")

    def crear_boton_accion(self, icono, color, tooltip):
        """Crear botón de acción con estilo consistente"""
        btn = QPushButton(icono)
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
                margin: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba({self.hex_to_rgb(color)}, 0.3);
                border-color: {color};
                color: {color};
            }}
            QPushButton:pressed {{
                background-color: rgba({self.hex_to_rgb(color)}, 0.5);
            }}
        """)
        btn.setToolTip(tooltip)
        return btn

    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB para estilos"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

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
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #444444;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                min-width: 60px;
            }
            QComboBox:hover {
                border-color: #4a9eff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
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
                border: 2px solid #666666;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #4a9eff;
                background-color: #4a4a4a;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def conectar_signals(self):
        """Conectar señales de la interfaz"""
        self.list_profesores.itemClicked.connect(self.seleccionar_profesor)
        self.combo_filtro_asignatura.currentTextChanged.connect(self.aplicar_filtro_asignatura)
        self.check_solo_disponibles.toggled.connect(self.aplicar_filtro_asignatura)

    def aplicar_filtro_asignatura(self):
        """Aplicar filtro por asignatura y disponibilidad"""
        filtro_texto = self.combo_filtro_asignatura.currentText()
        solo_disponibles = self.check_solo_disponibles.isChecked()

        self.filtro_asignatura_actual = filtro_texto
        self.list_profesores.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay profesores configurados")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_profesores.addItem(item)
            return

        # Filtrar profesores
        profesores_filtrados = []

        for dni, datos in self.datos_configuracion.items():
            asignaturas_imparte = datos.get('asignaturas_puede_impartir', [])

            # FILTRO POR ASIGNATURA
            incluir_por_asignatura = False

            if filtro_texto == "Todas las asignaturas":
                # Si puede impartir cualquier asignatura
                incluir_por_asignatura = bool(asignaturas_imparte)
            else:
                # Extraer semestre y asignatura del filtro "1º - Fisica"
                if " - " in filtro_texto:
                    sem, asig = filtro_texto.split(" - ", 1)
                    sem_num = sem[0]  # "1º" -> "1"
                    asig_key = f"{sem_num}_{asig}"

                    # Verificar si puede impartir esta asignatura específica
                    if asig_key in asignaturas_imparte:
                        incluir_por_asignatura = True

            # Si no pasa el filtro de asignatura, saltar
            if not incluir_por_asignatura:
                continue

            # FILTRO POR DISPONIBILIDAD (HOY)
            if solo_disponibles:
                dia_actual = datetime.now().strftime('%A')  # Ej: 'Monday'
                dias_espanol = {
                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                dia_hoy = dias_espanol.get(dia_actual, dia_actual)

                # Verificar si trabaja hoy
                dias_trabajo = datos.get('dias_trabajo', [])
                if dia_hoy not in dias_trabajo:
                    continue

                # Verificar si no está en fechas no disponibles
                fecha_hoy = datetime.now().strftime('%d/%m/%Y')
                fechas_no_disponibles = datos.get('fechas_no_disponibles', [])
                if fecha_hoy in fechas_no_disponibles:
                    continue

            # Si llegó hasta aquí, incluir en resultados
            profesores_filtrados.append((dni, datos))

        # Ordenar por apellidos + nombre
        profesores_filtrados.sort(key=lambda x: f"{x[1].get('apellidos', '')} {x[1].get('nombre', '')}")

        # Añadir a la lista
        for dni, datos in profesores_filtrados:
            nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"

            # Verificar disponibilidad hoy
            dia_actual = datetime.now().strftime('%A')
            dias_espanol = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            dia_hoy = dias_espanol.get(dia_actual, dia_actual)

            dias_trabajo = datos.get('dias_trabajo', [])
            fecha_hoy = datetime.now().strftime('%d/%m/%Y')
            fechas_no_disponibles = datos.get('fechas_no_disponibles', [])

            disponible_hoy = dia_hoy in dias_trabajo and fecha_hoy not in fechas_no_disponibles
            disponibilidad = "✅" if disponible_hoy else "⏸️"

            num_asignaturas = len(datos.get('asignaturas_puede_impartir', []))
            num_dias_trabajo = len(dias_trabajo)

            texto_item = f"{disponibilidad} {nombre_completo.strip()} [{dni}] ({num_asignaturas} asig., {num_dias_trabajo} días)"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, dni)
            self.list_profesores.addItem(item)

        # Mostrar información del filtro
        if profesores_filtrados:
            total = len(profesores_filtrados)
            contexto = "global" if filtro_texto == "Todas las asignaturas" else f"para {filtro_texto}"
            filtro_disp = " (disponibles hoy)" if solo_disponibles else ""
            self.log_mensaje(f"🔍 Filtro {contexto}{filtro_disp}: {total} profesores mostrados", "info")
        else:
            item = QListWidgetItem(f"🔍 Sin resultados para el filtro aplicado")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_profesores.addItem(item)

    def seleccionar_profesor(self, item):
        """Seleccionar profesor y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.profesor_actual = None
            self.btn_duplicar.setEnabled(False)
            self.btn_gestionar_disponibilidad.setEnabled(False)
            return

        dni = item.data(Qt.ItemDataRole.UserRole)
        if not dni or dni not in self.datos_configuracion:
            return

        self.profesor_actual = dni
        datos = self.datos_configuracion[dni]

        # Actualizar etiqueta
        nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
        self.label_profesor_actual.setText(f"👨‍🏫 {nombre_completo.strip()}")

        # Mostrar información detallada
        info = f"👨‍🏫 PROFESOR: {nombre_completo.strip()}\n\n"
        info += f"🆔 DNI: {datos.get('dni', 'No definido')}\n"
        info += f"📧 Email: {datos.get('email', 'No definido')}\n\n"

        # Mostrar asignaturas que puede impartir
        asignaturas_imparte = datos.get('asignaturas_puede_impartir', [])
        info += f"📚 ASIGNATURAS ({len(asignaturas_imparte)}):\n"
        if asignaturas_imparte:
            for asig in asignaturas_imparte:
                if '_' in asig:
                    semestre, nombre_asig = asig.split('_', 1)
                    info += f"  • {nombre_asig} ({semestre}º cuatr.)\n"
                else:
                    info += f"  • {asig}\n"
        else:
            info += "  Sin asignaturas asignadas\n"

        # Disponibilidad semanal
        dias_trabajo = datos.get('dias_trabajo', [])
        info += f"\n📅 DISPONIBILIDAD SEMANAL:\n"
        if dias_trabajo:
            info += f"  • Días de trabajo: {', '.join(dias_trabajo)}\n"
        else:
            info += "  • Sin días configurados\n"

        # Fechas no disponibles
        fechas_no_disponibles = datos.get('fechas_no_disponibles', [])
        if fechas_no_disponibles:
            info += f"  • Fechas no disponibles: {len(fechas_no_disponibles)} fechas\n"

        observaciones = datos.get('observaciones', '').strip()
        if observaciones:
            info += f"\n📝 OBSERVACIONES:\n  {observaciones}\n"

        self.info_profesor.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)
        self.btn_gestionar_disponibilidad.setEnabled(True)

    def anadir_profesor(self):
        """Añadir nuevo profesor"""
        dialog = GestionProfesorDialog(None, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_profesor()
            dni = datos['dni']

            if dni in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un profesor con el DNI '{dni}'")
                return

            # Añadir nuevo profesor
            self.datos_configuracion[dni] = datos

            # Auto-ordenar
            self.ordenar_profesores_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.auto_seleccionar_profesor(dni)
            self.marcar_cambio_realizado()

            nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
            num_asignaturas = len(datos.get('asignaturas_puede_impartir', []))
            QMessageBox.information(self, "Éxito",
                                    f"Profesor '{nombre.strip()}' añadido correctamente\n"
                                    f"Asignaturas que puede impartir: {num_asignaturas}")

    def editar_profesor_seleccionado(self):
        """Editar profesor seleccionado"""
        if not self.profesor_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un profesor para editar")
            return

        datos_originales = self.datos_configuracion[self.profesor_actual].copy()
        dialog = GestionProfesorDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_profesor()
            dni_nuevo = datos_nuevos['dni']
            dni_original = self.profesor_actual

            # Si cambió el DNI, verificar que no exista
            if dni_nuevo != dni_original and dni_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un profesor con el DNI '{dni_nuevo}'")
                return

            # Actualizar datos
            if dni_nuevo != dni_original:
                del self.datos_configuracion[dni_original]
                self.profesor_actual = dni_nuevo

            self.datos_configuracion[dni_nuevo] = datos_nuevos

            # Auto-ordenar
            self.ordenar_profesores_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.auto_seleccionar_profesor(dni_nuevo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Profesor actualizado correctamente")

    def eliminar_profesor_seleccionado(self):
        """Eliminar profesor seleccionado"""
        if not self.profesor_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un profesor para eliminar")
            return

        datos = self.datos_configuracion[self.profesor_actual]
        nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"

        respuesta = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de eliminar al profesor '{nombre.strip()}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            del self.datos_configuracion[self.profesor_actual]
            self.profesor_actual = None

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.label_profesor_actual.setText("Seleccione un profesor")
            self.info_profesor.setText("ℹ️ Seleccione un profesor para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_gestionar_disponibilidad.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Profesor eliminado correctamente")

    def duplicar_profesor_seleccionado(self):
        """Duplicar profesor seleccionado"""
        if not self.profesor_actual:
            return

        datos_originales = self.datos_configuracion[self.profesor_actual].copy()

        # Generar DNI único (simulado)
        dni_base = datos_originales['dni'][:-1]  # Sin la letra
        letra_original = datos_originales['dni'][-1]

        # Buscar letra disponible
        letras = "ABCDEFGHIJKLMNPQRSTUVWXYZ"
        dni_nuevo = datos_originales['dni']

        for letra in letras:
            if letra != letra_original:
                dni_nuevo = dni_base + letra
                if dni_nuevo not in self.datos_configuracion:
                    break

        datos_originales['dni'] = dni_nuevo
        datos_originales['nombre'] = datos_originales.get('nombre', '') + " (copia)"

        dialog = GestionProfesorDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_profesor()
            dni_final = datos_nuevos['dni']

            if dni_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un profesor con el DNI '{dni_final}'")
                return

            # Añadir profesor duplicado
            self.datos_configuracion[dni_final] = datos_nuevos

            # Auto-ordenar
            self.ordenar_profesores_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.auto_seleccionar_profesor(dni_final)
            self.marcar_cambio_realizado()

            nombre = f"{datos_nuevos.get('apellidos', '')} {datos_nuevos.get('nombre', '')}"
            QMessageBox.information(self, "Éxito", f"Profesor duplicado como '{nombre.strip()}'")

    def gestionar_disponibilidad(self):
        """Gestionar disponibilidad del profesor actual"""
        if not self.profesor_actual:
            return

        datos = self.datos_configuracion[self.profesor_actual]
        nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"

        # Por ahora mostrar un resumen, se puede expandir más tarde
        dias_trabajo = datos.get('dias_trabajo', [])
        fechas_no_disponibles = datos.get('fechas_no_disponibles', [])

        mensaje = f"Disponibilidad de {nombre.strip()}:\n\n"
        mensaje += f"Días de trabajo: {', '.join(dias_trabajo) if dias_trabajo else 'Ninguno'}\n"
        mensaje += f"Fechas no disponibles: {len(fechas_no_disponibles)}\n\n"
        mensaje += "Para modificar la disponibilidad, usa 'Editar Profesor'."

        QMessageBox.information(self, "Gestión de Disponibilidad", mensaje)

    def buscar_duplicados(self):
        """Buscar profesores duplicados por DNI o nombre completo"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay profesores para analizar")
            return

        duplicados_nombre = {}

        # Buscar duplicados por nombre completo
        for dni, datos in self.datos_configuracion.items():
            nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}".strip().lower()
            if nombre_completo in duplicados_nombre:
                duplicados_nombre[nombre_completo].append((dni, datos))
            else:
                duplicados_nombre[nombre_completo] = [(dni, datos)]

        # Filtrar solo los que tienen duplicados
        duplicados_reales = []
        for nombre, lista in duplicados_nombre.items():
            if len(lista) > 1:
                duplicados_reales.append((nombre, lista))

        if not duplicados_reales:
            QMessageBox.information(self, "Análisis Completo", "✅ No se encontraron profesores duplicados")
        else:
            mensaje = f"⚠️ Se encontraron {len(duplicados_reales)} grupos de profesores duplicados:\n\n"
            for nombre, lista in duplicados_reales[:5]:  # Mostrar solo los primeros 5
                mensaje += f"• {nombre.title()}:\n"
                for dni, datos in lista:
                    num_asig = len(datos.get('asignaturas_puede_impartir', []))
                    mensaje += f"  - DNI: {dni} ({num_asig} asignaturas)\n"
                mensaje += "\n"

            if len(duplicados_reales) > 5:
                mensaje += f"... y {len(duplicados_reales) - 5} grupos más."

            QMessageBox.warning(self, "Duplicados Encontrados", mensaje)

    def sincronizar_asignaturas(self):
        """Sincronizar asignaturas con el sistema"""
        asignaturas_nuevas = self.obtener_asignaturas_del_sistema()

        if asignaturas_nuevas == self.asignaturas_disponibles:
            QMessageBox.information(self, "Sincronización", "✅ Las asignaturas ya están sincronizadas")
            return

        self.asignaturas_disponibles = asignaturas_nuevas
        self.configurar_filtros()

        # Limpiar filtro actual
        self.combo_filtro_asignatura.setCurrentIndex(0)
        self.aplicar_filtro_asignatura()

        sem1_count = len(asignaturas_nuevas.get("1", {}))
        sem2_count = len(asignaturas_nuevas.get("2", {}))

        QMessageBox.information(self, "Sincronización Exitosa",
                                f"✅ Asignaturas sincronizadas:\n"
                                f"• 1º Semestre: {sem1_count} asignaturas\n"
                                f"• 2º Semestre: {sem2_count} asignaturas")

    def actualizar_estadisticas(self):
        """Actualizar estadísticas por asignatura"""
        if not self.datos_configuracion:
            self.texto_stats.setText("📊 No hay profesores para generar estadísticas")
            return

        # Estadísticas generales
        total_profesores = len(self.datos_configuracion)

        # Contar profesores disponibles hoy
        dia_actual = datetime.now().strftime('%A')
        dias_espanol = {
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        dia_hoy = dias_espanol.get(dia_actual, dia_actual)
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')

        disponibles_hoy = 0
        for datos in self.datos_configuracion.values():
            dias_trabajo = datos.get('dias_trabajo', [])
            fechas_no_disponibles = datos.get('fechas_no_disponibles', [])
            if dia_hoy in dias_trabajo and fecha_hoy not in fechas_no_disponibles:
                disponibles_hoy += 1

        # Estadísticas por asignatura
        stats_asignaturas = {}

        for dni, datos in self.datos_configuracion.items():
            asignaturas_imparte = datos.get('asignaturas_puede_impartir', [])

            for asig_key in asignaturas_imparte:
                if asig_key not in stats_asignaturas:
                    stats_asignaturas[asig_key] = {
                        'total_profesores': 0,
                        'disponibles_hoy': 0
                    }

                stats_asignaturas[asig_key]['total_profesores'] += 1

                # Contar si está disponible hoy
                dias_trabajo = datos.get('dias_trabajo', [])
                fechas_no_disponibles = datos.get('fechas_no_disponibles', [])
                if dia_hoy in dias_trabajo and fecha_hoy not in fechas_no_disponibles:
                    stats_asignaturas[asig_key]['disponibles_hoy'] += 1

        # Generar texto de estadísticas
        stats_texto = f"📈 ESTADÍSTICAS GENERALES:\n"
        stats_texto += f"Total profesores: {total_profesores}\n"
        stats_texto += f"Disponibles hoy ({dia_hoy}): {disponibles_hoy}\n"
        stats_texto += f"No disponibles hoy: {total_profesores - disponibles_hoy}\n\n"

        if stats_asignaturas:
            stats_texto += f"📚 POR ASIGNATURA:\n"
            for asig_key, stats in sorted(stats_asignaturas.items()):
                if '_' in asig_key:
                    sem, nombre = asig_key.split('_', 1)
                    nombre_completo = f"{nombre} ({sem}º)"
                else:
                    nombre_completo = asig_key

                total = stats['total_profesores']
                disp_hoy = stats['disponibles_hoy']

                stats_texto += f"• {nombre_completo}: {total} prof.\n"
                stats_texto += f"  - Disponibles hoy: {disp_hoy}\n"

        self.texto_stats.setText(stats_texto)

    def importar_desde_csv(self):
        """Importar profesores desde archivo CSV"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Profesores desde CSV",
            "", "Archivos CSV (*.csv);;Todos los archivos (*)"
        )

        if not archivo:
            return

        try:
            df = pd.read_csv(archivo)

            # Verificar columnas requeridas
            columnas_requeridas = ['dni', 'nombre', 'apellidos']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                QMessageBox.warning(
                    self, "Columnas Faltantes",
                    f"El archivo CSV debe contener las columnas:\n{', '.join(columnas_faltantes)}"
                )
                return

            # Importar datos
            profesores_importados = 0
            profesores_duplicados = 0

            for _, row in df.iterrows():
                dni = str(row['dni']).strip().upper()
                if not dni:
                    continue

                if dni in self.datos_configuracion:
                    profesores_duplicados += 1
                    continue

                # Procesar asignaturas si existe la columna
                asignaturas_imparte = []
                if 'asignatura' in df.columns and pd.notna(row['asignatura']):
                    asignatura = str(row['asignatura']).strip()
                    # Detectar semestre basado en asignaturas disponibles
                    for sem in ["1", "2"]:
                        if asignatura in self.asignaturas_disponibles.get(sem, {}):
                            asignaturas_imparte.append(f"{sem}_{asignatura}")
                            break

                # Procesar días de trabajo si existe la columna
                dias_trabajo = []
                if 'dias_trabajo' in df.columns and pd.notna(row['dias_trabajo']):
                    dias_str = str(row['dias_trabajo']).strip()
                    dias_trabajo = [dia.strip() for dia in dias_str.split(',') if dia.strip()]

                self.datos_configuracion[dni] = {
                    'dni': dni,
                    'nombre': str(row['nombre']).strip(),
                    'apellidos': str(row.get('apellidos', '')).strip(),
                    'email': str(row.get('email', '')).strip().lower(),
                    'asignaturas_puede_impartir': asignaturas_imparte,
                    'dias_trabajo': dias_trabajo,
                    'fechas_no_disponibles': [],
                    'observaciones': str(row.get('observaciones', '')).strip(),
                    'fecha_creacion': datetime.now().isoformat()
                }
                profesores_importados += 1

            # Auto-ordenar
            self.ordenar_profesores_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.marcar_cambio_realizado()

            mensaje = f"✅ Importación completada:\n"
            mensaje += f"• {profesores_importados} profesores importados\n"
            if profesores_duplicados > 0:
                mensaje += f"• {profesores_duplicados} profesores duplicados (omitidos)"

            QMessageBox.information(self, "Importación Exitosa", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación",
                                 f"Error al importar archivo CSV:\n{str(e)}")

    def exportar_a_csv(self):
        """Exportar profesores a archivo CSV"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay profesores para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Profesores a CSV",
            f"profesores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Archivos CSV (*.csv)"
        )

        if not archivo:
            return

        try:
            datos_export = []
            for dni, datos in self.datos_configuracion.items():
                # Expandir por asignatura (una fila por asignatura)
                asignaturas = datos.get('asignaturas_puede_impartir', [])
                if not asignaturas:
                    asignaturas = ['Sin asignatura']

                for asig_key in asignaturas:
                    # Separar semestre y asignatura
                    if '_' in asig_key:
                        sem, asignatura = asig_key.split('_', 1)
                    else:
                        sem, asignatura = '', asig_key

                    datos_export.append({
                        'dni': dni,
                        'nombre': datos.get('nombre', ''),
                        'apellidos': datos.get('apellidos', ''),
                        'email': datos.get('email', ''),
                        'asignatura': asignatura,
                        'semestre': sem,
                        'dias_trabajo': ', '.join(datos.get('dias_trabajo', [])),
                        'fechas_no_disponibles': ', '.join(datos.get('fechas_no_disponibles', [])),
                        'observaciones': datos.get('observaciones', '')
                    })

            df = pd.DataFrame(datos_export)
            df.to_csv(archivo, index=False, encoding='utf-8')

            QMessageBox.information(self, "Exportación Exitosa", f"Datos exportados a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación",
                                 f"Error al exportar datos:\n{str(e)}")

    def exportar_estadisticas(self):
        """Exportar estadísticas a archivo"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay profesores para generar estadísticas")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Estadísticas",
            f"estadisticas_profesores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            # Generar estadísticas actualizadas
            self.actualizar_estadisticas()
            contenido_stats = self.texto_stats.toPlainText()

            # Añadir información adicional
            contenido_completo = f"ESTADÍSTICAS DE PROFESORES - OPTIM Labs\n"
            contenido_completo += f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            contenido_completo += f"{'=' * 50}\n\n"
            contenido_completo += contenido_stats
            contenido_completo += f"\n\n{'=' * 50}\n"
            contenido_completo += f"Filtro aplicado: {self.filtro_asignatura_actual}\n"
            contenido_completo += f"Total configurado: {len(self.datos_configuracion)} profesores\n"

            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(contenido_completo)

            QMessageBox.information(self, "Exportación Exitosa", f"Estadísticas exportadas a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación",
                                 f"Error al exportar estadísticas:\n{str(e)}")

    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Profesores",
            "", "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "profesores" in datos_cargados:
                self.datos_configuracion = datos_cargados["profesores"]
            elif isinstance(datos_cargados, dict):
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Auto-ordenar
            self.ordenar_profesores_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.profesor_actual = None
            self.label_profesor_actual.setText("Seleccione un profesor")
            self.info_profesor.setText("ℹ️ Seleccione un profesor para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_gestionar_disponibilidad.setEnabled(False)

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def guardar_en_archivo(self):
        """Guardar configuración en archivo JSON"""
        if not self.datos_configuracion:
            QMessageBox.warning(self, "Sin Datos", "No hay profesores configurados para guardar.")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Profesores",
            f"profesores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'profesores': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_profesores': len(self.datos_configuracion),
                    'filtro_aplicado': self.filtro_asignatura_actual,
                    'generado_por': 'OPTIM Labs - Configurar Profesores'
                }
            }

            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Guardado Exitoso", f"Configuración guardada en:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Guardado", f"Error al guardar configuración:\n{str(e)}")

    def guardar_en_sistema(self):
        """Guardar configuración en el sistema principal"""
        try:
            if not self.datos_configuracion:
                QMessageBox.warning(self, "Sin Datos", "No hay profesores configurados para guardar.")
                return

            total_profesores = len(self.datos_configuracion)

            # Contar asignaturas únicas
            asignaturas_unicas = set()
            for datos in self.datos_configuracion.values():
                asignaturas_unicas.update(datos.get('asignaturas_puede_impartir', []))

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• {total_profesores} profesores configurados\n"
                f"• {len(asignaturas_unicas)} asignaturas distintas cubiertas\n\n"
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

    def limpiar_todos_profesores(self):
        """Limpiar todos los profesores configurados"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay profesores para limpiar")
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Todo",
            f"¿Está seguro de eliminar todos los profesores configurados?\n\n"
            f"Se eliminarán {len(self.datos_configuracion)} profesores.\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion.clear()
            self.profesor_actual = None

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.label_profesor_actual.setText("Seleccione un profesor")
            self.info_profesor.setText("ℹ️ Seleccione un profesor para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_gestionar_disponibilidad.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Limpieza Completada", "Todos los profesores han sido eliminados")

    def ordenar_profesores_alfabeticamente(self):
        """Reordenar profesores alfabéticamente por apellidos + nombre"""
        if not self.datos_configuracion:
            return

        # Crear lista ordenada por apellidos + nombre
        profesores_ordenados = sorted(
            self.datos_configuracion.items(),
            key=lambda x: f"{x[1].get('apellidos', '')} {x[1].get('nombre', '')}"
        )

        # Crear nuevo diccionario ordenado
        self.datos_configuracion = dict(profesores_ordenados)

    def auto_seleccionar_profesor(self, dni):
        """Auto-seleccionar profesor por DNI"""
        try:
            for i in range(self.list_profesores.count()):
                item = self.list_profesores.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == dni:
                    self.list_profesores.setCurrentItem(item)
                    self.seleccionar_profesor(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando profesor: {e}", "warning")

    def seleccionar_profesor_por_dni(self, dni):
        """Seleccionar profesor por DNI después de actualización"""
        if dni in self.datos_configuracion:
            # Buscar el item en la lista y seleccionarlo
            for i in range(self.list_profesores.count()):
                item = self.list_profesores.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == dni:
                    self.list_profesores.setCurrentItem(item)
                    self.seleccionar_profesor(item)
                    break

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
            self.log_mensaje("🔚 Cerrando configuración de profesores", "info")
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
                "profesores": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarProfesores",
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

    # Datos de ejemplo con estructura de profesores
    datos_ejemplo = {
        "12345678A": {
            "dni": "12345678A",
            "nombre": "Juan",
            "apellidos": "García López",
            "email": "juan.garcia@upm.es",
            "asignaturas_puede_impartir": ["1_Fisica I", "2_Fisica II"],
            "dias_trabajo": ["Lunes", "Martes", "Miércoles"],
            "fechas_no_disponibles": ["15/03/2025", "22/03/2025"],
            "observaciones": "Profesor titular con experiencia",
            "fecha_creacion": datetime.now().isoformat()
        },
        "23456789B": {
            "dni": "23456789B",
            "nombre": "María",
            "apellidos": "Fernández Ruiz",
            "email": "maria.fernandez@upm.es",
            "asignaturas_puede_impartir": ["1_Quimica General", "2_Quimica Organica"],
            "dias_trabajo": ["Martes", "Jueves", "Viernes"],
            "fechas_no_disponibles": ["10/04/2025"],
            "observaciones": "Profesora asociada",
            "fecha_creacion": datetime.now().isoformat()
        }
    }

    # La ventana ya se centra automáticamente en su constructor
    window = ConfigurarProfesores(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()