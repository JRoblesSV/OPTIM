#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Alumnos - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión completa de alumnos matriculados por DNI
2. Sistema de cursos matriculados con validación dinámica
3. Asignaturas matriculadas con estado de laboratorio previo
4. Filtros avanzados por asignatura y experiencia previa
5. Estadísticas automáticas de matriculación por asignatura
6. Detección y gestión de alumnos duplicados
7. Import/Export desde CSV con validación de datos
8. Duplicación de registros con modificación automática
9. Sincronización bidireccional con módulo de asignaturas
10. Integración completa con sistema de configuración global

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import re
import json
import pandas as pd

from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QGroupBox, QFrame, QScrollArea, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QFormLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
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


class GestionAlumnoDialog(QDialog):
    """Dialog para añadir/editar alumno con gestión de asignaturas"""

    def __init__(self, alumno_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        self.alumno_existente = alumno_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {"1": {}, "2": {}}
        self.cursos_disponibles = self.obtener_cursos_del_sistema()
        self.setWindowTitle("Editar Alumno" if alumno_existente else "Nuevo Alumno")
        self.setModal(True)

        # Centrar sin parpadeos
        window_width = 1100
        window_height = 950
        center_window_on_screen_immediate(self, window_width, window_height)
        self.setMinimumSize(1000, 900)

        self.setup_ui()
        self.apply_dark_theme()

        if self.alumno_existente:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Estilo común para todos los CheckBox
        self.estilo_checkbox_comun = """
                QCheckBox {
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px 6px;
                    margin: 2px 0px;
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    margin-right: 8px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #3c3c3c;
                    border: 2px solid #666666;
                    border-radius: 4px;
                }
                QCheckBox::indicator:unchecked:hover {
                    border-color: #4a9eff;
                    background-color: #4a4a4a;
                }
                QCheckBox::indicator:checked {
                    background-color: #4a9eff;
                    border: 2px solid #4a9eff;
                    border-radius: 4px;
                }
                QCheckBox:hover {
                    background-color: rgba(74, 158, 255, 0.15);
                    border-radius: 4px;
                }
            """

        # 👤 DATOS PERSONALES
        datos_personales_group = QGroupBox("👤 DATOS PERSONALES")
        datos_personales_layout = QGridLayout()

        # Fila 1: DNI | Email
        self.edit_dni = QLineEdit()
        self.edit_dni.setPlaceholderText("Ej: 12345678A")
        self.edit_dni.setMaxLength(9)

        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("Ej: juan.garcia@alumnos.upm.es")

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

        # 🎓 DATOS ACADÉMICOS
        datos_academicos_group = QGroupBox("🎓 DATOS ACADÉMICOS")
        datos_academicos_layout = QGridLayout()

        # Fila 1: N° Matrícula | Año Matrícula
        self.edit_matricula = QLineEdit()
        self.edit_matricula.setPlaceholderText("Ej: 2024000123")

        datos_academicos_layout.addWidget(QLabel("📋 N° Matrícula:"), 0, 0)
        datos_academicos_layout.addWidget(self.edit_matricula, 0, 1)

        datos_academicos_group.setLayout(datos_academicos_layout)
        layout.addWidget(datos_academicos_group)

        # 🎓📚 CURSOS Y ASIGNATURAS (LADO A LADO)
        cursos_asignaturas_group = QGroupBox("🎓📚 CURSOS Y ASIGNATURAS MATRICULADAS")
        cursos_asignaturas_main_layout = QHBoxLayout()  # Layout horizontal principal
        cursos_asignaturas_main_layout.setSpacing(15)

        # COLUMNA IZQUIERDA: CURSOS MATRICULADOS
        cursos_container = QWidget()
        cursos_main_layout = QVBoxLayout(cursos_container)
        cursos_main_layout.setSpacing(8)
        cursos_main_layout.setContentsMargins(0, 0, 0, 0)

        cursos_title = QLabel("🎓 CURSOS MATRICULADOS")
        cursos_title.setStyleSheet("""
            color: #4a9eff; 
            font-weight: bold; 
            font-size: 14px; 
            margin-bottom: 8px;
            padding: 6px;
            border-bottom: 2px solid #4a9eff;
        """)
        cursos_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursos_main_layout.addWidget(cursos_title)

        if self.cursos_disponibles:
            info_cursos = QLabel("Selecciona los cursos matriculados:")
            info_cursos.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 6px;")
            cursos_main_layout.addWidget(info_cursos)

            # SCROLL AREA PARA CURSOS
            self.cursos_scroll = QScrollArea()
            self.cursos_scroll.setWidgetResizable(True)
            self.cursos_scroll.setFixedHeight(300)
            self.cursos_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.cursos_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.cursos_scroll.setFrameStyle(QFrame.Shape.Box)
            self.cursos_scroll.setLineWidth(1)

            # Widget scrollable para cursos
            self.cursos_scroll_widget = QWidget()
            self.cursos_scroll_layout = QVBoxLayout(self.cursos_scroll_widget)
            self.cursos_scroll_layout.setContentsMargins(10, 10, 10, 10)
            self.cursos_scroll_layout.setSpacing(8)
            self.cursos_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Crear checkboxes por cursos del sistema
            self.checks_cursos = {}
            for codigo, curso_data in sorted(self.cursos_disponibles.items()):
                nombre = curso_data.get("nombre", codigo)
                curso_actual = curso_data.get("curso_actual", "")

                # Mostrar: "A102 - Grado en Ingeniería en Tecnologías Industriales (1º Curso)"
                texto_completo = f"{codigo} - {nombre}"
                if curso_actual:
                    texto_completo += f" ({curso_actual})"

                check_curso = QCheckBox(texto_completo)
                check_curso.setStyleSheet(self.estilo_checkbox_comun)
                check_curso.toggled.connect(self.filtrar_asignaturas_por_cursos)
                self.checks_cursos[codigo] = check_curso  # USAR CÓDIGO COMO KEY
                self.cursos_scroll_layout.addWidget(check_curso)

            # Añadir stretch al final
            self.cursos_scroll_layout.addStretch()

            # Configurar el scroll area
            self.cursos_scroll.setWidget(self.cursos_scroll_widget)
            cursos_main_layout.addWidget(self.cursos_scroll)
        else:
            no_cursos_label = QLabel("⚠️ No hay cursos configurados en el sistema.")
            no_cursos_label.setStyleSheet("color: #ffaa00; font-style: italic; padding: 20px; font-size: 12px;")
            cursos_main_layout.addWidget(no_cursos_label)
            self.checks_cursos = {}

        # COLUMNA DERECHA: ASIGNATURAS MATRICULADAS
        asignaturas_container = QWidget()
        asignaturas_main_layout = QVBoxLayout(asignaturas_container)
        asignaturas_main_layout.setSpacing(8)
        asignaturas_main_layout.setContentsMargins(0, 0, 0, 0)

        asignaturas_title = QLabel("📚 ASIGNATURAS MATRICULADAS")
        asignaturas_title.setStyleSheet("""
            color: #4a9eff; 
            font-weight: bold; 
            font-size: 14px; 
            margin-bottom: 8px;
            padding: 6px;
            border-bottom: 2px solid #4a9eff;
        """)
        asignaturas_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        asignaturas_main_layout.addWidget(asignaturas_title)

        info_asig_label = QLabel("Selecciona asignaturas y marca si ya aprobó el lab:")
        info_asig_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 6px;")
        asignaturas_main_layout.addWidget(info_asig_label)

        # SCROLL AREA PARA ASIGNATURAS
        self.asignaturas_scroll = QScrollArea()
        self.asignaturas_scroll.setWidgetResizable(True)  # CRÍTICO
        self.asignaturas_scroll.setFixedHeight(300)
        self.asignaturas_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.asignaturas_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.asignaturas_scroll.setFrameStyle(QFrame.Shape.Box)
        self.asignaturas_scroll.setLineWidth(1)

        # WIDGET SCROLLABLE
        self.asignaturas_scroll_widget = QWidget()
        self.asignaturas_scroll_widget.setMinimumSize(200, 100)
        self.asignaturas_scroll_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )

        # LAYOUT DEL WIDGET SCROLLABLE
        self.asignaturas_scroll_layout = QVBoxLayout()
        self.asignaturas_scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.asignaturas_scroll_layout.setSpacing(6)

        # IMPORTANTE: Configurar el layout en el widget
        self.asignaturas_scroll_widget.setLayout(self.asignaturas_scroll_layout)

        # Diccionarios para checkboxes
        self.checks_asignaturas = {}
        self.checks_lab_aprobado = {}

        # INICIALIZAR CON MENSAJE
        self.mostrar_mensaje_seleccionar_cursos()

        # CONFIGURAR EL SCROLL AREA - DESPUÉS de configurar el layout
        self.asignaturas_scroll.setWidget(self.asignaturas_scroll_widget)
        asignaturas_main_layout.addWidget(self.asignaturas_scroll)

        # Añadir las dos columnas al layout principal
        cursos_asignaturas_main_layout.addWidget(cursos_container, 1)  # 50% del ancho
        cursos_asignaturas_main_layout.addWidget(asignaturas_container, 1)  # 50% del ancho

        cursos_asignaturas_group.setLayout(cursos_asignaturas_main_layout)
        layout.addWidget(cursos_asignaturas_group)

        # 📋 EXPEDIENTES
        expedientes_group = QGroupBox("📋 EXPEDIENTES")
        expedientes_layout = QGridLayout()

        self.edit_exp_centro = QLineEdit()
        self.edit_exp_centro.setPlaceholderText("Ej: GIN-14")

        self.edit_exp_agora = QLineEdit()
        self.edit_exp_agora.setPlaceholderText("Ej: AGR789012")

        expedientes_layout.addWidget(QLabel("🏫 N° Exp. Centro:"), 0, 0)
        expedientes_layout.addWidget(self.edit_exp_centro, 0, 1)
        expedientes_layout.addWidget(QLabel("🌐 N° Exp. Ágora:"), 0, 2)
        expedientes_layout.addWidget(self.edit_exp_agora, 0, 3)

        expedientes_group.setLayout(expedientes_layout)
        layout.addWidget(expedientes_group)

        # 📝 OBSERVACIONES
        observaciones_group = QGroupBox("📝 OBSERVACIONES")
        observaciones_layout = QVBoxLayout()

        self.edit_observaciones = QTextEdit()
        self.edit_observaciones.setMaximumHeight(60)
        self.edit_observaciones.setPlaceholderText("Observaciones adicionales sobre el alumno...")
        observaciones_layout.addWidget(self.edit_observaciones)

        observaciones_group.setLayout(observaciones_layout)
        layout.addWidget(observaciones_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def mostrar_mensaje_seleccionar_cursos(self):
        """Mostrar mensaje inicial para seleccionar cursos"""
        # Limpiar layout
        self.limpiar_layout_asignaturas()

        # Mensaje inicial
        mensaje_label = QLabel("⚠️ Selecciona primero los cursos para ver las asignaturas disponibles.")
        mensaje_label.setStyleSheet("""
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
        mensaje_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensaje_label.setWordWrap(True)
        self.asignaturas_scroll_layout.addWidget(mensaje_label)

        # CLAVE: Actualizar el scroll area
        self.asignaturas_scroll_widget.adjustSize()
        self.asignaturas_scroll.updateGeometry()

    def limpiar_layout_asignaturas(self):
        """Limpiar el layout de asignaturas de forma segura"""
        # Limpiar diccionarios PRIMERO
        self.checks_asignaturas.clear()
        self.checks_lab_aprobado.clear()

        # Limpiar layout de forma más robusta
        while self.asignaturas_scroll_layout.count():
            child = self.asignaturas_scroll_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)  # CRÍTICO: desconectar del padre
                widget.deleteLater()

        # IMPORTANTE: Procesar eventos pendientes para que se eliminen los widgets
        QApplication.processEvents()

        # FORZAR ACTUALIZACIÓN FINAL
        self.asignaturas_scroll_widget.updateGeometry()
        self.asignaturas_scroll.updateGeometry()

    def obtener_cursos_del_sistema(self):
        """Obtener códigos de cursos disponibles desde el sistema global"""
        try:
            if self.parent() and hasattr(self.parent(), 'parent_window'):
                parent_window = self.parent().parent_window
                if parent_window and hasattr(parent_window, 'configuracion'):
                    config_cursos = parent_window.configuracion["configuracion"]["cursos"]
                    if config_cursos.get("configurado") and config_cursos.get("datos"):
                        cursos_disponibles = {}
                        for codigo, curso_data in config_cursos["datos"].items():
                            nombre = curso_data.get("nombre", codigo)
                            cursos_disponibles[codigo] = {
                                "codigo": codigo,
                                "nombre": nombre,
                                "curso_actual": curso_data.get("curso_actual", ""),
                                "asignaturas_asociadas": curso_data.get("asignaturas_asociadas", [])
                            }
                        return cursos_disponibles
            return {}
        except Exception as e:
            print(f"Error obteniendo códigos de cursos: {e}")
            return {}

    def filtrar_asignaturas_por_cursos(self):
        """Filtrar asignaturas disponibles según cursos seleccionados"""
        # Obtener códigos de cursos seleccionados
        cursos_seleccionados = [codigo for codigo, check in self.checks_cursos.items() if check.isChecked()]

        # Guardar estado actual de asignaturas antes de limpiar
        estado_asignaturas_previo = {}
        for key, check_asig in self.checks_asignaturas.items():
            if check_asig.isChecked():
                lab_aprobado = False
                if key in self.checks_lab_aprobado and self.checks_lab_aprobado[key].isEnabled():
                    lab_aprobado = self.checks_lab_aprobado[key].isChecked()

                estado_asignaturas_previo[key] = {
                    'matriculado': True,
                    'lab_aprobado': lab_aprobado
                }

        # Limpiar asignaturas actuales
        self.limpiar_layout_asignaturas()

        if not cursos_seleccionados:
            # Si no hay cursos seleccionados, mostrar mensaje
            self.mostrar_mensaje_seleccionar_cursos()
            return

        # Obtener asignaturas desde el sistema
        asignaturas_filtradas = {"1": {}, "2": {}}

        try:
            if self.parent() and hasattr(self.parent(), 'parent_window'):
                parent_window = self.parent().parent_window
                if parent_window and hasattr(parent_window, 'configuracion'):
                    config_asignaturas = parent_window.configuracion["configuracion"]["asignaturas"]
                    if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                        for codigo_asig, asig_data in config_asignaturas["datos"].items():
                            nombre_asig = asig_data.get("nombre", codigo_asig)
                            semestre_str = asig_data.get("semestre", "1º Semestre")
                            cursos_que_cursan = asig_data.get("cursos_que_cursan", [])

                            # Detectar semestre
                            if "1º" in semestre_str or "primer" in semestre_str.lower():
                                semestre = "1"
                            elif "2º" in semestre_str or "segundo" in semestre_str.lower():
                                semestre = "2"
                            else:
                                semestre = "1"

                            # Si la asignatura es cursada por algún curso seleccionado
                            if any(curso in cursos_que_cursan for curso in cursos_seleccionados):
                                asignaturas_filtradas[semestre][codigo_asig] = {
                                    "codigo": codigo_asig,
                                    "nombre": nombre_asig,
                                    "semestre": semestre_str
                                }

        except Exception as e:
            print(f"Error filtrando asignaturas por cursos: {e}")

        # Recrear checkboxes de asignaturas
        self.crear_asignaturas_filtradas(asignaturas_filtradas)

        # Restaurar el estado previo de las asignaturas
        QApplication.processEvents()  # Asegurar que los widgets están creados

        for key, estado in estado_asignaturas_previo.items():
            if key in self.checks_asignaturas:  # Solo si la asignatura sigue disponible
                check_asig = self.checks_asignaturas[key]
                check_asig.setChecked(True)

                # Restaurar lab aprobado
                if key in self.checks_lab_aprobado:
                    lab_check = self.checks_lab_aprobado[key]
                    lab_check.setEnabled(True)
                    lab_check.setChecked(estado.get('lab_aprobado', False))

        # Forzar actualización final del scroll area
        QApplication.processEvents()
        self.asignaturas_scroll.setVisible(True)
        self.asignaturas_scroll_widget.setVisible(True)

    def crear_asignaturas_filtradas(self, asignaturas_data):
        """Crear checkboxes de asignaturas filtradas"""
        if not asignaturas_data.get("1") and not asignaturas_data.get("2"):
            # No hay asignaturas para los cursos seleccionados
            no_asig_label = QLabel("⚠️ No hay asignaturas configuradas para los cursos seleccionados.")
            no_asig_label.setStyleSheet("""
                color: #ffaa00; 
                font-style: italic; 
                font-size: 13px;
                padding: 25px; 
                text-align: center;
                background-color: rgba(255, 170, 0, 0.1);
                border: 1px dashed #ffaa00;
                border-radius: 6px;
                margin: 15px;
                min-height: 200px;
            """)
            no_asig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_asig_label.setWordWrap(True)
            self.asignaturas_scroll_layout.addWidget(no_asig_label)

            # Forzar actualización del scroll
            self.actualizar_scroll_asignaturas()
            return

        # 1º Semestre
        if asignaturas_data.get("1"):
            sem1_label = QLabel("📋 1º Semestre:")
            sem1_label.setStyleSheet("""
                color: #90EE90; 
                font-weight: bold; 
                font-size: 13px;
                margin: 10px 0px 6px 0px;
                padding: 6px;
                background-color: rgba(144, 238, 144, 0.1);
                border-radius: 4px;
            """)
            self.asignaturas_scroll_layout.addWidget(sem1_label)

            for codigo_asignatura, asig_data in sorted(asignaturas_data["1"].items()):
                nombre = asig_data.get("nombre", codigo_asignatura)
                texto_completo = f"{codigo_asignatura} - {nombre}"
                self.crear_fila_asignatura_con_texto(codigo_asignatura, texto_completo)

        # 2º Semestre
        if asignaturas_data.get("2"):
            sem2_label = QLabel("📋 2º Semestre:")
            sem2_label.setStyleSheet("""
                color: #90EE90; 
                font-weight: bold; 
                font-size: 13px;
                margin: 15px 0px 6px 0px;
                padding: 6px;
                background-color: rgba(144, 238, 144, 0.1);
                border-radius: 4px;
            """)
            self.asignaturas_scroll_layout.addWidget(sem2_label)

            for codigo_asignatura, asig_data in sorted(asignaturas_data["2"].items()):
                nombre = asig_data.get("nombre", codigo_asignatura)
                texto_completo = f"{codigo_asignatura} - {nombre}"
                self.crear_fila_asignatura_con_texto(codigo_asignatura, texto_completo)

        # IMPORTANTE: Añadir stretch al final
        self.asignaturas_scroll_layout.addStretch()

        # Forzar actualización completa del scroll
        self.actualizar_scroll_asignaturas()

    def actualizar_scroll_asignaturas(self):
        """Función para forzar actualización del scroll de asignaturas"""
        # Procesar eventos pendientes primero
        QApplication.processEvents()

        # Calcular el tamaño real del contenido
        total_height = 0
        for i in range(self.asignaturas_scroll_layout.count()):
            item = self.asignaturas_scroll_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                widget.adjustSize()
                total_height += widget.sizeHint().height()

        # Añadir márgenes y espaciado
        margins = self.asignaturas_scroll_layout.contentsMargins()
        total_height += margins.top() + margins.bottom()
        total_height += self.asignaturas_scroll_layout.spacing() * max(0, self.asignaturas_scroll_layout.count() - 1)

        # Establecer tamaño mínimo del widget basado en contenido
        self.asignaturas_scroll_widget.setMinimumHeight(max(100, total_height))

        # Forzar actualización del widget y scroll area
        self.asignaturas_scroll_widget.updateGeometry()
        self.asignaturas_scroll_widget.adjustSize()

        # Procesar eventos
        QApplication.processEvents()

        # Actualizar el scroll area
        self.asignaturas_scroll.updateGeometry()

        # Scroll al inicio
        self.asignaturas_scroll.verticalScrollBar().setValue(0)

        # Procesar eventos finales
        QApplication.processEvents()

    def crear_fila_asignatura(self, codigo_asignatura, semestre):
        """Crea una fila con checkbox de asignatura + checkbox de lab aprobado al lado"""
        fila_widget = QWidget()
        fila_widget.setStyleSheet("""
            QWidget:hover {
                background-color: rgba(74, 158, 255, 0.1);
                border-radius: 6px;
            }
        """)

        # Layout HORIZONTAL para poner asignatura y lab aprobado lado a lado
        fila_layout = QHBoxLayout(fila_widget)
        fila_layout.setContentsMargins(8, 4, 8, 4)  # Menos padding vertical
        fila_layout.setSpacing(15)  # Espacio entre asignatura y lab aprobado

        # Checkbox principal de asignatura
        key_asignatura = codigo_asignatura
        check_asignatura = QCheckBox(key_asignatura)
        check_asignatura.setStyleSheet(self.estilo_checkbox_comun + """
            QCheckBox {
                min-width: 180px;
            }
        """)
        self.checks_asignaturas[key_asignatura] = check_asignatura

        # Checkbox para lab aprobado al lado
        check_lab = QCheckBox("🎓 Lab aprobado")
        check_lab.setStyleSheet("""
            QCheckBox {
                color: #90EE90; 
                font-size: 11px;
                font-weight: 500;
                padding: 2px;
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
            QCheckBox::indicator:checked {
                background-color: #90EE90;
                border: 2px solid #90EE90;
                border-radius: 3px;
            }
            QCheckBox:disabled {
                color: #666666;
            }
        """)
        check_lab.setEnabled(False)
        self.checks_lab_aprobado[key_asignatura] = check_lab

        # Conectar señales
        check_asignatura.toggled.connect(
            lambda checked, lab_check=check_lab: lab_check.setEnabled(checked)
        )
        check_asignatura.toggled.connect(
            lambda checked, lab_check=check_lab: lab_check.setChecked(False) if not checked else None
        )

        # Añadir widgets al layout horizontal
        fila_layout.addWidget(check_asignatura)
        fila_layout.addWidget(check_lab)
        fila_layout.addStretch()  # Push a la izquierda

        # Añadir la fila al layout del scroll
        self.asignaturas_scroll_layout.addWidget(fila_widget)

    def crear_fila_asignatura_con_texto(self, codigo_asignatura, texto_mostrar):
        """Crea una fila con checkbox de asignatura + checkbox de lab aprobado"""
        fila_widget = QWidget()
        fila_widget.setStyleSheet("""
            QWidget:hover {
                background-color: rgba(74, 158, 255, 0.1);
                border-radius: 6px;
            }
        """)

        # Layout HORIZONTAL para poner asignatura y lab aprobado lado a lado
        fila_layout = QHBoxLayout(fila_widget)
        fila_layout.setContentsMargins(8, 4, 8, 4)
        fila_layout.setSpacing(15)

        # Checkbox principal de asignatura CON TEXTO COMPLETO
        key_asignatura = codigo_asignatura
        check_asignatura = QCheckBox(texto_mostrar)  # AQUÍ ESTÁ EL CAMBIO
        check_asignatura.setStyleSheet(self.estilo_checkbox_comun + """
            QCheckBox {
                min-width: 180px;
            }
        """)
        self.checks_asignaturas[key_asignatura] = check_asignatura

        # Checkbox para lab aprobado al lado
        check_lab = QCheckBox("🎓 Lab aprobado")
        check_lab.setStyleSheet("""
            QCheckBox {
                color: #90EE90; 
                font-size: 11px;
                font-weight: 500;
                padding: 2px;
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
            QCheckBox::indicator:checked {
                background-color: #90EE90;
                border: 2px solid #90EE90;
                border-radius: 3px;
            }
            QCheckBox:disabled {
                color: #666666;
            }
        """)
        check_lab.setEnabled(False)
        self.checks_lab_aprobado[key_asignatura] = check_lab

        # Conectar señales
        check_asignatura.toggled.connect(
            lambda checked, lab_check=check_lab: lab_check.setEnabled(checked)
        )
        check_asignatura.toggled.connect(
            lambda checked, lab_check=check_lab: lab_check.setChecked(False) if not checked else None
        )

        # Añadir widgets al layout horizontal
        fila_layout.addWidget(check_asignatura)
        fila_layout.addWidget(check_lab)
        fila_layout.addStretch()

        # Añadir la fila al layout del scroll
        self.asignaturas_scroll_layout.addWidget(fila_widget)

    def extraer_curso_de_curso(self, curso):
        """Extraer curso del código de curso (ej: A102 -> '1', EE309 -> '3')"""
        # Buscar patrón LLXNN donde L=letras, X=primer dígito del curso, NN=resto
        match = re.search(r'[A-Z]+(\d)', curso)
        if match:
            return match.group(1)  # Primer dígito
        return "1"  # Por defecto 1º curso

    def tiene_asignaturas_disponibles(self):
        """Verificar si hay asignaturas disponibles"""
        sem1 = self.asignaturas_disponibles.get("1", {})
        sem2 = self.asignaturas_disponibles.get("2", {})
        return bool(sem1 or sem2)

    def cargar_datos_existentes(self):
        """Cargar datos del alumno existente con nueva estructura - SCROLL FINAL"""
        if not self.alumno_existente:
            return

        datos = self.alumno_existente

        # Datos personales
        self.edit_dni.setText(datos.get('dni', ''))
        self.edit_nombre.setText(datos.get('nombre', ''))
        self.edit_apellidos.setText(datos.get('apellidos', ''))
        self.edit_email.setText(datos.get('email', ''))

        # Datos académicos
        self.edit_matricula.setText(datos.get('matricula', ''))

        # Expedientes
        self.edit_exp_centro.setText(datos.get('exp_centro', ''))
        self.edit_exp_agora.setText(datos.get('exp_agora', ''))

        # Observaciones
        self.edit_observaciones.setText(datos.get('observaciones', ''))

        # CURSOS MATRICULADOS - VERIFICAR EXISTENCIA PRIMERO
        grupos_matriculado = datos.get('cursos_matriculado', [])

        # LIMPIAR SELECCIÓN PREVIA
        for check in self.checks_cursos.values():
            check.setChecked(False)

        # MARCAR CURSOS EXISTENTES
        for grupo in grupos_matriculado:
            if grupo in self.checks_cursos:
                self.checks_cursos[grupo].setChecked(True)

        # IMPORTANTE: Filtrar asignaturas DESPUÉS de marcar cursos
        if grupos_matriculado:
            # LIMPIAR PRIMERO
            self.limpiar_layout_asignaturas()

            # FILTRAR ASIGNATURAS
            self.filtrar_asignaturas_por_cursos()

            # Procesar eventos pendientes para que se aplique el filtrado
            QApplication.processEvents()

            # CARGAR ASIGNATURAS MATRICULADAS CON KEYS CORRECTAS
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

            # VERIFICAR COMPATIBILIDAD DE KEYS
            for stored_key, info_asignatura in asignaturas_matriculadas.items():
                # Buscar la key correcta en los checkboxes actuales
                checkbox_key = None

                # Estrategia 1: Key exacta
                if stored_key in self.checks_asignaturas:
                    checkbox_key = stored_key
                else:
                    # Estrategia 2: Buscar por código de asignatura
                    for check_key in self.checks_asignaturas.keys():
                        if check_key == stored_key:
                            checkbox_key = check_key
                            break

                # Si encontramos la key, marcar el checkbox
                if checkbox_key and info_asignatura.get('matriculado', False):
                    check_asig = self.checks_asignaturas[checkbox_key]
                    check_asig.setChecked(True)

                    # Habilitar y marcar lab aprobado si corresponde
                    if checkbox_key in self.checks_lab_aprobado:
                        lab_check = self.checks_lab_aprobado[checkbox_key]
                        lab_check.setEnabled(True)
                        lab_check.setChecked(info_asignatura.get('lab_aprobado', False))

            # Actualizar scroll final
            self.actualizar_scroll_asignaturas()
        else:
            # Si no hay cursos, mostrar mensaje inicial
            self.mostrar_mensaje_seleccionar_cursos()

    def validar_y_aceptar(self):
        """Validar datos antes de aceptar con nueva estructura"""
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
                                "El alumno debe estar matriculado en al menos una asignatura")
            return

        self.accept()

    def get_datos_alumno(self):
        """Obtener datos configurados del alumno con nueva estructura"""
        # Obtener asignaturas seleccionadas con información de lab aprobado
        asignaturas_matriculadas = {}

        for key, check_asig in self.checks_asignaturas.items():
            if check_asig.isChecked():
                # Verificar si tiene lab aprobado
                lab_aprobado = False
                if key in self.checks_lab_aprobado:
                    lab_aprobado = self.checks_lab_aprobado[key].isChecked()

                asignaturas_matriculadas[key] = {
                    "matriculado": True,
                    "lab_aprobado": lab_aprobado
                }

        return {
            # Datos personales
            'dni': self.edit_dni.text().strip().upper(),
            'nombre': self.edit_nombre.text().strip(),
            'apellidos': self.edit_apellidos.text().strip(),
            'email': self.edit_email.text().strip().lower(),

            # Datos académicos
            'matricula': self.edit_matricula.text().strip(),
            'cursos_matriculado': [grupo for grupo, check in self.checks_cursos.items() if check.isChecked()],

            # Asignaturas
            'asignaturas_matriculadas': asignaturas_matriculadas,

            # Expedientes
            'exp_centro': self.edit_exp_centro.text().strip(),
            'exp_agora': self.edit_exp_agora.text().strip(),

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
        """)


# El resto de las clases permanecen igual...
class ConfigurarAlumnos(QMainWindow):
    """Ventana principal para configurar alumnos matriculados"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Alumnos - OPTIM Labs")

        # Centrar inmediatamente sin parpadeo
        window_width = 1500
        window_height = 900
        center_window_on_screen_immediate(self, window_width, window_height)
        self.setMinimumSize(1400, 850)

        # Obtener asignaturas disponibles desde el sistema global
        self.asignaturas_disponibles = self.obtener_asignaturas_del_sistema()

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("📥 Cargando configuración existente de alumnos...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("📝 Iniciando configuración nueva de alumnos...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.alumno_actual = None
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

                        # CLAVE: Usar NOMBRE como key pero incluir CÓDIGO en los datos
                        if nombre:  # Solo si tiene nombre
                            asignaturas_transformadas[semestre][nombre] = {
                                "codigo": codigo,  # INCLUIR CÓDIGO
                                "nombre": nombre,
                                "semestre": semestre_str,
                                **asig_data  # Incluir todos los datos originales
                            }

                    return asignaturas_transformadas

            return {"1": {}, "2": {}}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo asignaturas del sistema: {e}", "warning")
            return {"1": {}, "2": {}}

    def cargar_datos_iniciales(self):
        """Cargar datos existentes al inicializar"""
        try:
            # Ordenar alumnos alfabéticamente
            self.ordenar_alumnos_alfabeticamente()

            # Cargar lista con filtro inicial
            self.aplicar_filtro_asignatura()

            # Mostrar resumen
            total_alumnos = len(self.datos_configuracion)
            if total_alumnos > 0:
                self.log_mensaje(f"✅ Datos cargados: {total_alumnos} alumnos", "success")
                self.auto_seleccionar_primer_alumno()
            else:
                self.log_mensaje("📝 No hay alumnos configurados - configuración nueva", "info")

            # Actualizar estadísticas
            self.actualizar_estadisticas()

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primer_alumno(self):
        """Auto-seleccionar primer alumno disponible"""
        try:
            if self.list_alumnos.count() > 0:
                primer_item = self.list_alumnos.item(0)
                if primer_item and primer_item.flags() != Qt.ItemFlag.NoItemFlags:
                    self.list_alumnos.setCurrentItem(primer_item)
                    self.seleccionar_alumno(primer_item)
                    self.log_mensaje(f"🎯 Auto-seleccionado: {primer_item.text().split(' - ')[0]}", "info")
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando alumno: {e}", "warning")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("👥 CONFIGURACIÓN DE ALUMNOS")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información contextual
        info_label = QLabel(
            "📋 Gestiona la lista de alumnos matriculados. Los que tengan 'Lab anterior' se filtrarán automáticamente.")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de alumnos con filtros
        left_panel = QGroupBox("👥 ALUMNOS REGISTRADOS")
        left_layout = QVBoxLayout()

        # Filtros
        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(QLabel("Filtros:"))

        self.combo_filtro_asignatura = QComboBox()
        self.combo_filtro_asignatura.setMaximumWidth(200)
        filtros_layout.addWidget(self.combo_filtro_asignatura)

        self.check_solo_sin_lab = QCheckBox("Solo alumnos con laboratorio pentiende")
        self.check_solo_sin_lab.setToolTip("Mostrar solo alumnos sin experiencia previa")
        filtros_layout.addWidget(self.check_solo_sin_lab)

        filtros_layout.addStretch()
        left_layout.addLayout(filtros_layout)

        # Gestión de alumnos
        gestion_layout = QHBoxLayout()
        gestion_layout.addWidget(QLabel("Gestión:"))
        gestion_layout.addStretch()

        # Botones de gestión
        btn_add_alumno = self.crear_boton_accion("➕", "#4CAF50", "Añadir nuevo alumno")
        btn_add_alumno.clicked.connect(self.anadir_alumno)

        btn_edit_alumno = self.crear_boton_accion("✏️", "#2196F3", "Editar alumno seleccionado")
        btn_edit_alumno.clicked.connect(self.editar_alumno_seleccionado)

        btn_delete_alumno = self.crear_boton_accion("🗑️", "#f44336", "Eliminar alumno seleccionado")
        btn_delete_alumno.clicked.connect(self.eliminar_alumno_seleccionado)

        gestion_layout.addWidget(btn_add_alumno)
        gestion_layout.addWidget(btn_edit_alumno)
        gestion_layout.addWidget(btn_delete_alumno)

        left_layout.addLayout(gestion_layout)

        # Lista de alumnos
        self.list_alumnos = QListWidget()
        self.list_alumnos.setMaximumWidth(400)
        self.list_alumnos.setMinimumHeight(400)
        left_layout.addWidget(self.list_alumnos)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Detalles del alumno
        center_panel = QGroupBox("👤 DETALLES DEL ALUMNO")
        center_layout = QVBoxLayout()
        center_layout.setSpacing(10)

        # Nombre del alumno seleccionado
        self.label_alumno_actual = QLabel("Seleccione un alumno")
        self.label_alumno_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_alumno_actual)

        # Información detallada
        self.info_alumno = QTextEdit()
        self.info_alumno.setMaximumHeight(320)
        self.info_alumno.setMinimumHeight(280)
        self.info_alumno.setReadOnly(True)
        self.info_alumno.setText("ℹ️ Seleccione un alumno para ver sus detalles")
        center_layout.addWidget(self.info_alumno)

        # Estadísticas por asignatura
        stats_group = QGroupBox("📊 ESTADÍSTICAS POR ASIGNATURA")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)

        # Layout horizontal para el botón
        btn_stats_layout = QHBoxLayout()
        self.btn_actualizar_stats = QPushButton("📈 Actualizar Estadísticas")
        self.btn_actualizar_stats.setMaximumWidth(200)
        self.btn_actualizar_stats.clicked.connect(self.actualizar_estadisticas)
        btn_stats_layout.addWidget(self.btn_actualizar_stats)
        btn_stats_layout.addStretch()
        stats_layout.addLayout(btn_stats_layout)

        # Grid de estadísticas
        self.texto_stats = QTextEdit()
        self.texto_stats.setMinimumHeight(350)
        self.texto_stats.setMaximumHeight(500)
        self.texto_stats.setReadOnly(True)
        self.texto_stats.setText("📈 Presiona 'Actualizar' para ver estadísticas")
        # Mejorar fuente para mejor legibilidad
        self.texto_stats.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.3;
            }
        """)
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

        self.btn_duplicar = QPushButton("📋 Duplicar Alumno Seleccionado")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_alumno_seleccionado)
        acciones_layout.addWidget(self.btn_duplicar)

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

        self.btn_importar_alumnos = QPushButton("📥 Importar Alumnos")
        self.btn_importar_alumnos.clicked.connect(self.importar_alumnos_excel)
        importar_layout.addWidget(self.btn_importar_alumnos)

        self.btn_importar_aprobados = QPushButton("✅ Importar Alumnos Aprobados")
        self.btn_importar_aprobados.clicked.connect(self.importar_alumnos_aprobados)
        importar_layout.addWidget(self.btn_importar_aprobados)

        self.btn_cargar = QPushButton("📁 Cargar Configuración")
        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Exportar datos
        exportar_group = QGroupBox("📤 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todos_alumnos)
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
        self.list_alumnos.itemClicked.connect(self.seleccionar_alumno)
        self.combo_filtro_asignatura.currentTextChanged.connect(self.aplicar_filtro_asignatura)
        self.check_solo_sin_lab.toggled.connect(self.aplicar_filtro_asignatura)

    def aplicar_filtro_asignatura(self):
        """Aplicar filtro por asignatura y experiencia con nueva estructura"""
        filtro_texto = self.combo_filtro_asignatura.currentText()
        solo_sin_lab = self.check_solo_sin_lab.isChecked()

        self.filtro_asignatura_actual = filtro_texto
        self.list_alumnos.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay alumnos configurados")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_alumnos.addItem(item)
            return

        # Filtrar alumnos
        alumnos_filtrados = []

        for dni, datos in self.datos_configuracion.items():
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

            # FILTRO POR ASIGNATURA PRIMERO
            incluir_por_asignatura = False

            if filtro_texto == "Todas las asignaturas":
                # Si está matriculado en cualquier asignatura
                incluir_por_asignatura = bool(asignaturas_matriculadas)
            else:
                # Extraer semestre y asignatura del filtro "1º - Fisica"
                if " - " in filtro_texto:
                    sem, asig = filtro_texto.split(" - ", 1)
                    sem_num = sem[0]  # "1º" -> "1"
                    asig_key = f"{sem_num}_{asig}"

                    # Verificar si está matriculado en esta asignatura específica
                    if asig_key in asignaturas_matriculadas and asignaturas_matriculadas[asig_key].get('matriculado',
                                                                                                       False):
                        incluir_por_asignatura = True

            # Si no pasa el filtro de asignatura, saltar
            if not incluir_por_asignatura:
                continue

            # FILTRO POR EXPERIENCIA CONTEXTUAL
            if solo_sin_lab:
                if filtro_texto == "Todas las asignaturas":
                    # LÓGICA GLOBAL: Mostrar solo si tiene AL MENOS una asignatura sin lab anterior
                    tiene_alguna_sin_experiencia = any(
                        not asig_info.get('lab_aprobado', False)
                        for asig_info in asignaturas_matriculadas.values()
                        if asig_info.get('matriculado', False)
                    )
                    if not tiene_alguna_sin_experiencia:
                        continue
                else:
                    # LÓGICA ESPECÍFICA: Solo mirar la asignatura filtrada
                    sem, asig = filtro_texto.split(" - ", 1)
                    sem_num = sem[0]
                    asig_key = f"{sem_num}_{asig}"

                    # Si tiene lab aprobado EN ESTA asignatura específica, filtrarlo
                    if asig_key in asignaturas_matriculadas:
                        asig_info = asignaturas_matriculadas[asig_key]
                        if asig_info.get('lab_aprobado', False):
                            continue

            # Si llegó hasta aquí, incluir en resultados
            alumnos_filtrados.append((dni, datos))

        # Ordenar por apellidos + nombre
        alumnos_filtrados.sort(key=lambda x: f"{x[1].get('apellidos', '')} {x[1].get('nombre', '')}")

        # Añadir a la lista
        for dni, datos in alumnos_filtrados:
            nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
            grupos_matriculado = datos.get('cursos_matriculado', [])
            if grupos_matriculado:
                grupos_str = ', '.join(grupos_matriculado[:2])
                if len(grupos_matriculado) > 2:
                    grupos_str += f" +{len(grupos_matriculado) - 2}"
            else:
                grupos_str = datos.get('grupo', 'Sin grupos')

            # Verificar experiencia según contexto
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

            if filtro_texto == "Todas las asignaturas":
                # Experiencia global
                tiene_experiencia = any(
                    asig_info.get('lab_aprobado', False)
                    for asig_info in asignaturas_matriculadas.values()
                )
            else:
                # Experiencia específica de la asignatura filtrada
                sem, asig = filtro_texto.split(" - ", 1)
                sem_num = sem[0]
                asig_key = f"{sem_num}_{asig}"
                tiene_experiencia = False
                if asig_key in asignaturas_matriculadas:
                    tiene_experiencia = asignaturas_matriculadas[asig_key].get('lab_aprobado', False)

            experiencia = "🎓" if tiene_experiencia else "📝"
            num_asignaturas = len(asignaturas_matriculadas)

            texto_item = f"{experiencia} {nombre_completo.strip()} [{dni}] {grupos_str} ({num_asignaturas} asig.)"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, dni)
            self.list_alumnos.addItem(item)

        # Mostrar información del filtro
        if alumnos_filtrados:
            total = len(alumnos_filtrados)
            contexto = "global" if filtro_texto == "Todas las asignaturas" else f"para {filtro_texto}"
            filtro_lab = " (sin lab anterior)" if solo_sin_lab else ""
            self.log_mensaje(f"🔍 Filtro {contexto}{filtro_lab}: {total} alumnos mostrados", "info")
        else:
            item = QListWidgetItem(f"🔍 Sin resultados para el filtro aplicado")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_alumnos.addItem(item)

    def seleccionar_alumno(self, item):
        """Seleccionar alumno y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.alumno_actual = None
            self.btn_duplicar.setEnabled(False)
            return

        dni = item.data(Qt.ItemDataRole.UserRole)
        if not dni or dni not in self.datos_configuracion:
            return

        self.alumno_actual = dni
        datos = self.datos_configuracion[dni]

        # Actualizar etiqueta
        nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
        self.label_alumno_actual.setText(f"👤 {nombre_completo.strip()}")

        # Mostrar información detallada
        info = f"👤 ALUMNO: {nombre_completo.strip()}\n\n"
        info += f"🆔 DNI: {datos.get('dni', 'No definido')}\n"
        info += f"📧 Email: {datos.get('email', 'No definido')}\n"
        info += f"📋 Matrícula: {datos.get('expediente', 'No definido')}\n"
        grupos_matriculado = datos.get('cursos_matriculado', [])
        if grupos_matriculado:
            info += f"👥 Grupos: {', '.join(grupos_matriculado)}\n\n"
        else:
            # Compatibilidad con datos antiguos
            grupo_antiguo = datos.get('grupo', '')
            if grupo_antiguo:
                info += f"👥 Grupo (legacy): {grupo_antiguo}\n\n"
            else:
                info += f"👥 Grupos: No definido\n\n"

        # Mostrar asignaturas matriculadas
        asignaturas_matriculadas = datos.get('asignaturas_matriculadas', [])
        info += f"📚 ASIGNATURAS ({len(asignaturas_matriculadas)}):\n"
        if asignaturas_matriculadas:
            for asig in asignaturas_matriculadas:
                if '_' in asig:
                    semestre, nombre_asig = asig.split('_', 1)
                    info += f"  • {nombre_asig} ({semestre}º cuatr.)\n"
                else:
                    info += f"  • {asig}\n"
        else:
            info += "  Sin asignaturas matriculadas\n"

        # Experiencia previa
        info += f"\n🎓 EXPERIENCIA:\n"
        info += f"  • Lab anterior: {'Sí' if datos.get('lab_anterior', False) else 'No'}\n"

        observaciones = datos.get('observaciones', '').strip()
        if observaciones:
            info += f"  • Observaciones: {observaciones}\n"

        self.info_alumno.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)

    def anadir_alumno(self):
        """Añadir nuevo alumno"""
        dialog = GestionAlumnoDialog(None, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_alumno()
            dni = datos['dni']

            if dni in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un alumno con el DNI '{dni}'")
                return

            # Añadir nuevo alumno
            self.datos_configuracion[dni] = datos

            # Auto-ordenar
            self.ordenar_alumnos_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.auto_seleccionar_alumno(dni)
            self.marcar_cambio_realizado()

            nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
            num_asignaturas = len(datos.get('asignaturas_matriculadas', []))
            QMessageBox.information(self, "Éxito",
                                    f"Alumno '{nombre.strip()}' añadido correctamente\n"
                                    f"Asignaturas matriculadas: {num_asignaturas}")

    def editar_alumno_seleccionado(self):
        """Editar alumno seleccionado"""
        if not self.alumno_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un alumno para editar")
            return

        datos_originales = self.datos_configuracion[self.alumno_actual].copy()
        dialog = GestionAlumnoDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_alumno()
            dni_nuevo = datos_nuevos['dni']
            dni_original = self.alumno_actual

            # Si cambió el DNI, verificar que no exista
            if dni_nuevo != dni_original and dni_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un alumno con el DNI '{dni_nuevo}'")
                return

            # Actualizar datos
            if dni_nuevo != dni_original:
                del self.datos_configuracion[dni_original]
                self.alumno_actual = dni_nuevo

            self.datos_configuracion[dni_nuevo] = datos_nuevos

            # Auto-ordenar
            self.ordenar_alumnos_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.auto_seleccionar_alumno(dni_nuevo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Alumno actualizado correctamente")

    def eliminar_alumno_seleccionado(self):
        """Eliminar alumno seleccionado"""
        if not self.alumno_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un alumno para eliminar")
            return

        datos = self.datos_configuracion[self.alumno_actual]
        nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"

        respuesta = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de eliminar al alumno '{nombre.strip()}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            del self.datos_configuracion[self.alumno_actual]
            self.alumno_actual = None

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.label_alumno_actual.setText("Seleccione un alumno")
            self.info_alumno.setText("ℹ️ Seleccione un alumno para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Alumno eliminado correctamente")

    def duplicar_alumno_seleccionado(self):
        """Duplicar alumno seleccionado"""
        if not self.alumno_actual:
            return

        datos_originales = self.datos_configuracion[self.alumno_actual].copy()

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

        dialog = GestionAlumnoDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_alumno()
            dni_final = datos_nuevos['dni']

            if dni_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un alumno con el DNI '{dni_final}'")
                return

            # Añadir alumno duplicado
            self.datos_configuracion[dni_final] = datos_nuevos

            # Auto-ordenar
            self.ordenar_alumnos_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.auto_seleccionar_alumno(dni_final)
            self.marcar_cambio_realizado()

            nombre = f"{datos_nuevos.get('apellidos', '')} {datos_nuevos.get('nombre', '')}"
            QMessageBox.information(self, "Éxito", f"Alumno duplicado como '{nombre.strip()}'")

    def toggle_lab_anterior(self):
        """Cambiar experiencia previa del alumno actual"""
        if not self.alumno_actual:
            return

        estado_actual = self.datos_configuracion[self.alumno_actual].get('lab_anterior', False)
        nuevo_estado = not estado_actual

        self.datos_configuracion[self.alumno_actual]['lab_anterior'] = nuevo_estado

        # Actualizar interfaz
        self.aplicar_filtro_asignatura()
        self.seleccionar_alumno_por_dni(self.alumno_actual)
        self.marcar_cambio_realizado()

        datos = self.datos_configuracion[self.alumno_actual]
        nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
        estado_texto = "con experiencia" if nuevo_estado else "sin experiencia"
        QMessageBox.information(self, "Estado Actualizado",
                                f"Alumno '{nombre.strip()}' marcado como {estado_texto} previa")

    def importar_alumnos_excel(self):
        """Importar alumnos desde Excel con selector de asignatura"""
        # Verificar que hay asignaturas disponibles
        if not self.asignaturas_disponibles.get("1") and not self.asignaturas_disponibles.get("2"):
            QMessageBox.warning(self, "Sin Asignaturas",
                                "No hay asignaturas configuradas en el sistema.\n"
                                "Configure primero las asignaturas antes de importar alumnos.")
            return

        # Selector de asignatura
        selector = SelectorAsignaturaDialog(self.asignaturas_disponibles,
                                            "Importar Alumnos - Seleccionar Asignatura", self)

        if selector.exec() != QDialog.DialogCode.Accepted or not selector.asignatura_seleccionada:
            return

        asignatura_info = selector.asignatura_seleccionada

        # Seleccionar archivo Excel
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Alumnos desde Excel",
            "", "Archivos Excel (*.xlsx *.xls);;Excel Nuevo (*.xlsx);;Excel Antiguo (*.xls);;Todos los archivos (*)"
        )

        if not archivo:
            return

        try:
            # Leer Excel con pandas
            df = self._leer_excel_universal(archivo)

            # Mapeo de columnas esperadas (flexibles)
            columnas_mapeo = {
                'dni': ['DNI', 'dni', 'Dni'],
                'apellidos': ['Apellidos', 'apellidos', 'APELLIDOS'],
                'nombre': ['Nombre', 'nombre', 'NOMBRE'],
                'email': ['Email', 'email', 'EMAIL', 'E-mail', 'e-mail'],
                'grupo': ['Grupo matrícula', 'Grupo matricula', 'grupo', 'GRUPO', 'Grupo de Matricula'],
                'exp_centro': ['Nº Expediente en Centro', 'Exp Centro', 'exp_centro', 'Expediente Centro'],
                'exp_agora': ['Nº Expediente en Ágora', 'Exp Agora', 'exp_agora', 'Expediente Agora']
            }

            # Detectar columnas
            columnas_detectadas = {}
            for campo, posibles_nombres in columnas_mapeo.items():
                for nombre in posibles_nombres:
                    if nombre in df.columns:
                        columnas_detectadas[campo] = nombre
                        break

            # Verificar columnas esenciales
            esenciales = ['dni', 'apellidos', 'nombre', 'grupo']
            faltantes = [campo for campo in esenciales if campo not in columnas_detectadas]

            if faltantes:
                QMessageBox.warning(self, "Columnas Faltantes",
                                    f"No se encontraron las columnas esenciales:\n"
                                    f"{', '.join(faltantes)}\n\n"
                                    f"Columnas disponibles: {', '.join(df.columns)}")
                return

            # Obtener cursos disponibles del sistema
            cursos_disponibles = self.obtener_cursos_del_sistema()
            if not cursos_disponibles:
                QMessageBox.warning(self, "Sin Cursos",
                                    "No hay cursos configurados en el sistema.\n"
                                    "Configure primero los cursos antes de importar alumnos.")
                return

            # Procesar datos
            alumnos_importados = 0
            alumnos_actualizados = 0
            errores = []
            cursos_faltantes = set()
            asignaturas_no_asociadas = set()

            for index, row in df.iterrows():
                try:
                    # Extraer datos básicos
                    dni = str(row[columnas_detectadas['dni']]).strip().upper()
                    if not dni or dni == 'nan':
                        continue

                    apellidos = str(row[columnas_detectadas['apellidos']]).strip()
                    nombre = str(row[columnas_detectadas['nombre']]).strip()

                    if not apellidos or not nombre:
                        errores.append(f"Fila {index + 2}: Nombre o apellidos vacíos")
                        continue

                    # EXTRAER CÓDIGO DE CURSO del campo grupo
                    grupo_completo = str(row[columnas_detectadas['grupo']]).strip()
                    codigo_curso = self._extraer_codigo_curso(grupo_completo)

                    if not codigo_curso:
                        errores.append(f"Fila {index + 2}: No se pudo extraer código de curso de '{grupo_completo}'")
                        continue

                    # VALIDAR que el curso existe
                    if codigo_curso not in cursos_disponibles:
                        cursos_faltantes.add(codigo_curso)
                        errores.append(f"Fila {index + 2}: Curso '{codigo_curso}' no existe en el sistema")
                        continue

                    # VALIDAR que la asignatura está asociada al curso
                    curso_data = cursos_disponibles[codigo_curso]
                    asignaturas_del_curso = curso_data.get("asignaturas_asociadas", [])

                    # Buscar por CÓDIGO DE ASIGNATURA
                    codigo_asignatura = asignatura_info['codigo']
                    if codigo_asignatura not in asignaturas_del_curso:
                        asignaturas_no_asociadas.add(
                            f"{codigo_asignatura} ({asignatura_info['nombre']}) → {codigo_curso}")
                        errores.append(
                            f"Fila {index + 2}: Asignatura '{codigo_asignatura}' no está asociada al curso '{codigo_curso}'")
                        continue

                    # Datos opcionales
                    email = ""
                    if 'email' in columnas_detectadas:
                        email = str(row[columnas_detectadas['email']]).strip().lower()
                        if email == 'nan':
                            email = ""

                    exp_centro = ""
                    if 'exp_centro' in columnas_detectadas:
                        exp_centro = str(row[columnas_detectadas['exp_centro']]).strip()
                        if exp_centro == 'nan':
                            exp_centro = ""

                    exp_agora = ""
                    if 'exp_agora' in columnas_detectadas:
                        exp_agora = str(row[columnas_detectadas['exp_agora']]).strip()
                        if exp_agora == 'nan':
                            exp_agora = ""

                    # Preparar datos del alumno
                    if dni in self.datos_configuracion:
                        # ACTUALIZAR ALUMNO EXISTENTE - AGREGAR CURSO Y ASIGNATURA
                        alumno_datos = self.datos_configuracion[dni]
                        cambios_realizados = False

                        # Actualizar datos básicos solo si están vacíos
                        if not alumno_datos.get('apellidos'):
                            alumno_datos['apellidos'] = apellidos
                            cambios_realizados = True
                        if not alumno_datos.get('nombre'):
                            alumno_datos['nombre'] = nombre
                            cambios_realizados = True
                        if not alumno_datos.get('email') and email:
                            alumno_datos['email'] = email
                            cambios_realizados = True
                        if not alumno_datos.get('exp_centro') and exp_centro:
                            alumno_datos['exp_centro'] = exp_centro
                            cambios_realizados = True
                        if not alumno_datos.get('exp_agora') and exp_agora:
                            alumno_datos['exp_agora'] = exp_agora
                            cambios_realizados = True

                        # AGREGAR CURSO si no lo tiene
                        cursos_actuales = alumno_datos.get('cursos_matriculado', [])
                        if codigo_curso not in cursos_actuales:
                            cursos_actuales.append(codigo_curso)
                            alumno_datos['cursos_matriculado'] = cursos_actuales
                            cambios_realizados = True

                        # AGREGAR ASIGNATURA si no la tiene
                        asignaturas_actuales = alumno_datos.get('asignaturas_matriculadas', {})
                        asig_key = asignatura_info['key']

                        if asig_key not in asignaturas_actuales:
                            asignaturas_actuales[asig_key] = {
                                "matriculado": True,
                                "lab_aprobado": False
                            }
                            alumno_datos['asignaturas_matriculadas'] = asignaturas_actuales
                            cambios_realizados = True

                        if cambios_realizados:
                            alumnos_actualizados += 1

                    else:
                        # Crear NUEVO ALUMNO
                        self.datos_configuracion[dni] = {
                            'dni': dni,
                            'nombre': nombre,
                            'apellidos': apellidos,
                            'email': email,
                            'matricula': exp_centro if exp_centro else dni,
                            'cursos_matriculado': [codigo_curso],
                            'asignaturas_matriculadas': {
                                asignatura_info['key']: {
                                    "matriculado": True,
                                    "lab_aprobado": False
                                }
                            },
                            'exp_centro': exp_centro,
                            'exp_agora': exp_agora,
                            'observaciones': f"Importado desde Excel - {asignatura_info['nombre']} - Curso {codigo_curso}",
                            'fecha_creacion': datetime.now().isoformat()
                        }
                        alumnos_importados += 1

                except Exception as e:
                    errores.append(f"Fila {index + 2}: {str(e)}")

            # Auto-ordenar
            self.ordenar_alumnos_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.marcar_cambio_realizado()

            # Mostrar resultado detallado
            mensaje = f"✅ Importación completada para {asignatura_info['nombre']}:\n\n"
            mensaje += f"• {alumnos_importados} alumnos nuevos\n"
            mensaje += f"• {alumnos_actualizados} alumnos actualizados\n"

            if errores:
                mensaje += f"• {len(errores)} errores\n\n"

                # Mostrar cursos faltantes
                if cursos_faltantes:
                    mensaje += f"⚠️ CURSOS FALTANTES:\n"
                    for curso in sorted(cursos_faltantes):
                        mensaje += f"  • {curso}\n"
                    mensaje += "→ Crear en: Configurar Cursos\n\n"

                # Mostrar asignaturas no asociadas
                if asignaturas_no_asociadas:
                    mensaje += f"⚠️ ASIGNATURAS NO ASOCIADAS:\n"
                    for asoc in sorted(asignaturas_no_asociadas):
                        mensaje += f"  • {asoc}\n"
                    mensaje += "→ Editar en: Configurar Asignaturas o Configurar Cursos\n\n"

                # Mostrar algunos errores
                if errores and len(errores) <= 5:
                    mensaje += "Errores detallados:\n" + "\n".join(errores[:5])
                elif errores:
                    mensaje += f"Primeros errores:\n" + "\n".join(errores[:3]) + f"\n... y {len(errores) - 3} más"

                # Mensaje final con instrucciones
                if cursos_faltantes or asignaturas_no_asociadas:
                    mensaje += f"\n\n💡 SOLUCIÓN:\n"
                    mensaje += f"1. Ir a 'Configurar Cursos' para crear cursos faltantes\n"
                    mensaje += f"2. Ir a 'Configurar Asignaturas' para asociar asignaturas a cursos\n"
                    mensaje += f"3. Volver a importar el archivo Excel"

            QMessageBox.information(self, "Importación Completada", mensaje)

            self.log_mensaje(
                f"📥 Importados {alumnos_importados} nuevos, {alumnos_actualizados} actualizados para {asignatura_info['nombre']}",
                "success")

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación",
                                 f"Error al procesar archivo Excel:\n{str(e)}")
            self.log_mensaje(f"❌ Error importando alumnos: {e}", "error")

    def importar_alumnos_aprobados(self):
        """Importar alumnos aprobados desde Excel para desmarcar laboratorio"""
        # Verificar que hay asignaturas y alumnos
        if not self.datos_configuracion:
            QMessageBox.warning(self, "Sin Alumnos",
                                "No hay alumnos configurados en el sistema.\n"
                                "Importe primero los alumnos antes de marcar aprobados.")
            return

        if not self.asignaturas_disponibles.get("1") and not self.asignaturas_disponibles.get("2"):
            QMessageBox.warning(self, "Sin Asignaturas",
                                "No hay asignaturas configuradas en el sistema.")
            return

        # Selector de asignatura
        selector = SelectorAsignaturaDialog(self.asignaturas_disponibles,
                                            "Marcar Aprobados - Seleccionar Asignatura", self)

        if selector.exec() != QDialog.DialogCode.Accepted or not selector.asignatura_seleccionada:
            return

        asignatura_info = selector.asignatura_seleccionada

        # Seleccionar archivo Excel
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Alumnos Aprobados desde Excel",
            "", "Archivos Excel (*.xlsx *.xls);;Todos los archivos (*)"
        )

        if not archivo:
            return

        try:
            # Leer Excel
            df = self._leer_excel_universal(archivo)

            # Detectar columna de identificación (DNI o Expediente Centro)
            columna_id = None
            identificadores = []

            posibles_columnas = ['DNI', 'dni', 'Dni', 'Nº Expediente en Centro', 'Exp Centro', 'exp_centro',
                                 'Expediente Centro']

            for col_name in posibles_columnas:
                if col_name in df.columns:
                    columna_id = col_name
                    break

            if not columna_id:
                QMessageBox.warning(self, "Columna no encontrada",
                                    f"No se encontró columna de DNI o Expediente Centro.\n\n"
                                    f"Columnas disponibles: {', '.join(df.columns)}")
                return

            # Extraer identificadores
            for index, row in df.iterrows():
                identificador = str(row[columna_id]).strip().upper()
                if identificador and identificador != 'nan':
                    identificadores.append(identificador)

            if not identificadores:
                QMessageBox.warning(self, "Sin Datos", "No se encontraron identificadores válidos en el archivo")
                return

            # INICIALIZAR VARIABLES DE CONTEO AQUÍ
            alumnos_marcados = 0
            alumnos_no_encontrados = []
            alumnos_sin_asignatura = []

            # Buscar y marcar alumnos como aprobados
            for identificador in identificadores:
                alumno_encontrado = None
                dni_encontrado = None

                # Buscar por DNI directo
                if identificador in self.datos_configuracion:
                    alumno_encontrado = self.datos_configuracion[identificador]
                    dni_encontrado = identificador
                else:
                    # Buscar por expediente centro
                    for dni, datos in self.datos_configuracion.items():
                        if datos.get('exp_centro', '').strip().upper() == identificador:
                            alumno_encontrado = datos
                            dni_encontrado = dni
                            break

                if not alumno_encontrado:
                    alumnos_no_encontrados.append(identificador)
                    continue

                # Verificar si está matriculado en la asignatura
                asignaturas_matriculadas = alumno_encontrado.get('asignaturas_matriculadas', {})
                asig_key = asignatura_info['key']  # Ahora es solo el código

                if asig_key not in asignaturas_matriculadas:
                    nombre_completo = f"{alumno_encontrado.get('apellidos', '')} {alumno_encontrado.get('nombre', '')}"
                    alumnos_sin_asignatura.append(f"{nombre_completo.strip()} ({dni_encontrado})")
                    continue

                # MARCAR LABORATORIO COMO APROBADO
                if not asignaturas_matriculadas[asig_key].get('lab_aprobado', False):
                    asignaturas_matriculadas[asig_key]['lab_aprobado'] = True
                    alumnos_marcados += 1

                    # Actualizar observaciones para registrar cuándo se aprobó
                    observaciones_actuales = alumno_encontrado.get('observaciones', '')
                    fecha_aprobacion = datetime.now().strftime('%d/%m/%Y')
                    nueva_observacion = f"Lab {asignatura_info['codigo']} aprobado {fecha_aprobacion}"

                    if observaciones_actuales:
                        alumno_encontrado['observaciones'] = f"{observaciones_actuales}; {nueva_observacion}"
                    else:
                        alumno_encontrado['observaciones'] = nueva_observacion

            # Actualizar interfaz si hubo cambios
            if alumnos_marcados > 0:
                self.aplicar_filtro_asignatura()
                self.marcar_cambio_realizado()

                # Reseleccionar alumno actual si existe
                if self.alumno_actual and self.alumno_actual in self.datos_configuracion:
                    self.seleccionar_alumno_por_dni(self.alumno_actual)

            # Mostrar resultado
            mensaje = f"✅ Proceso completado para {asignatura_info['nombre']} ({asignatura_info['codigo']}):\n\n"
            mensaje += f"• {alumnos_marcados} alumnos marcados como 🎓 APROBADOS\n"
            mensaje += f"• {len(alumnos_no_encontrados)} no encontrados en el sistema\n"
            mensaje += f"• {len(alumnos_sin_asignatura)} sin matrícula en esta asignatura\n"

            if alumnos_no_encontrados and len(alumnos_no_encontrados) <= 10:
                mensaje += f"\nNo encontrados: {', '.join(alumnos_no_encontrados[:10])}"
                if len(alumnos_no_encontrados) > 10:
                    mensaje += f" y {len(alumnos_no_encontrados) - 10} más..."

            if alumnos_sin_asignatura and len(alumnos_sin_asignatura) <= 5:
                mensaje += f"\nSin matrícula: {', '.join(alumnos_sin_asignatura[:5])}"
                if len(alumnos_sin_asignatura) > 5:
                    mensaje += f" y {len(alumnos_sin_asignatura) - 5} más..."

            mensaje += f"\n\n💡 Los alumnos marcados como aprobados aparecerán con 🎓 en la lista."

            QMessageBox.information(self, "Proceso Completado", mensaje)

            self.log_mensaje(f"✅ Marcados {alumnos_marcados} alumnos como aprobados en {asignatura_info['codigo']}",
                             "success")

        except Exception as e:
            QMessageBox.critical(self, "Error de Procesamiento",
                                 f"Error al procesar archivo:\n{str(e)}")
            self.log_mensaje(f"❌ Error marcando aprobados: {e}", "error")

    def _extraer_codigo_curso(self, grupo_completo):
        """Extraer código de curso de 'Grupo de Matricula (A302)' → 'A302'"""
        import re

        # Buscar texto entre paréntesis
        match = re.search(r'\(([^)]+)\)', grupo_completo)
        if match:
            return match.group(1).strip().upper()

        # Si no hay paréntesis, intentar extraer código directamente
        # Buscar patrón de letras seguidas de números
        match = re.search(r'([A-Z]+\d+)', grupo_completo.upper())
        if match:
            return match.group(1)

        return None

    def obtener_cursos_del_sistema(self):
        """Obtener cursos disponibles desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_cursos = self.parent_window.configuracion["configuracion"]["cursos"]
                if config_cursos.get("configurado") and config_cursos.get("datos"):
                    return config_cursos["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo cursos del sistema: {e}", "warning")
            return {}

    def _leer_excel_universal(self, archivo):
        """Leer archivos Excel .xlsx y .xls con manejo automático de dependencias"""
        import os

        # Detectar extensión
        _, extension = os.path.splitext(archivo.lower())

        if extension == '.xlsx':
            # Intentar leer .xlsx con openpyxl
            try:
                return pd.read_excel(archivo, engine='openpyxl')
            except ImportError:
                # Intentar instalar openpyxl automáticamente
                try:
                    import subprocess
                    import sys
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
                    # Reintentar después de instalar
                    return pd.read_excel(archivo, engine='openpyxl')
                except:
                    raise ImportError(
                        "Para leer archivos .xlsx necesitas instalar 'openpyxl'.\n\n"
                        "Ejecuta en terminal:\n"
                        "pip install openpyxl\n\n"
                        "O desde Python:\n"
                        "import subprocess, sys\n"
                        "subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl'])"
                    )

        elif extension == '.xls':
            # Intentar leer .xls con xlrd
            try:
                return pd.read_excel(archivo, engine='xlrd')
            except ImportError:
                # Intentar instalar xlrd automáticamente
                try:
                    import subprocess
                    import sys
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "xlrd"])
                    # Reintentar después de instalar
                    return pd.read_excel(archivo, engine='xlrd')
                except:
                    raise ImportError(
                        "Para leer archivos .xls necesitas instalar 'xlrd'.\n\n"
                        "Ejecuta en terminal:\n"
                        "pip install xlrd\n\n"
                        "O desde Python:\n"
                        "import subprocess, sys\n"
                        "subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'xlrd'])"
                    )

        else:
            # Intentar lectura automática (pandas decide)
            try:
                return pd.read_excel(archivo)
            except Exception as e:
                raise ValueError(f"Formato de archivo no soportado: {extension}\n"
                                 f"Use archivos .xlsx o .xls\n\n"
                                 f"Error original: {str(e)}")

    def buscar_duplicados(self):
        """Buscar alumnos duplicados por DNI o nombre completo"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay alumnos para analizar")
            return

        duplicados_dni = {}
        duplicados_nombre = {}

        # Buscar duplicados
        for dni, datos in self.datos_configuracion.items():
            # Por DNI (ya no debería pasar, pero por si acaso)
            if dni in duplicados_dni:
                duplicados_dni[dni].append(datos)
            else:
                duplicados_dni[dni] = [datos]

            # Por nombre completo
            # nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}".strip().lower()
            # if nombre_completo in duplicados_nombre:
            #     duplicados_nombre[nombre_completo].append((dni, datos))
            # else:
            #     duplicados_nombre[nombre_completo] = [(dni, datos)]

        # Filtrar solo los que tienen duplicados
        duplicados_reales = []
        for nombre, lista in duplicados_nombre.items():
            if len(lista) > 1:
                duplicados_reales.append((nombre, lista))

        if not duplicados_reales:
            QMessageBox.information(self, "Análisis Completo", "✅ No se encontraron alumnos duplicados")
        else:
            mensaje = f"⚠️ Se encontraron {len(duplicados_reales)} grupos de alumnos duplicados:\n\n"
            for nombre, lista in duplicados_reales[:5]:  # Mostrar solo los primeros 5
                mensaje += f"• {nombre.title()}:\n"
                for dni, datos in lista:
                    grupo = datos.get('grupo', 'Sin grupo')
                    mensaje += f"  - DNI: {dni} (Grupo: {grupo})\n"
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
                                f"• 2º Semestre: {sem2_count} asignaturas\n\n"
                                f"💡 Los cursos se actualizarán automáticamente al crear/editar alumnos")

    def actualizar_estadisticas(self):
        """Actualizar estadísticas por asignatura con nueva estructura"""
        if not self.datos_configuracion:
            self.texto_stats.setText("📊 No hay alumnos para generar estadísticas")
            return

        # Estadísticas generales
        total_alumnos = len(self.datos_configuracion)

        # Contar alumnos con laboratorios aprobados global
        con_experiencia = 0
        for datos in self.datos_configuracion.values():
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})
            tiene_experiencia = any(
                asig_info.get('lab_aprobado', False)
                for asig_info in asignaturas_matriculadas.values()
            )
            if tiene_experiencia:
                con_experiencia += 1

        sin_experiencia = total_alumnos - con_experiencia

        # Estadísticas por asignatura
        stats_asignaturas = {}

        for dni, datos in self.datos_configuracion.items():
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

            for asig_key, asig_info in asignaturas_matriculadas.items():
                if asig_info.get('matriculado', False):  # Solo contar si está realmente matriculado
                    if asig_key not in stats_asignaturas:
                        stats_asignaturas[asig_key] = {
                            'total': 0,
                            'con_experiencia': 0,
                            'sin_experiencia': 0,
                            'grupos_recomendados': 0
                        }

                    stats_asignaturas[asig_key]['total'] += 1

                    # Contar experiencia específica por asignatura
                    if asig_info.get('lab_aprobado', False):
                        stats_asignaturas[asig_key]['con_experiencia'] += 1
                    else:
                        stats_asignaturas[asig_key]['sin_experiencia'] += 1

        # Calcular grupos recomendados (asumiendo 12-14 alumnos por grupo)
        for asig_key, stats in stats_asignaturas.items():
            total = stats['total']
            grupos_recomendados = max(1, (total + 13) // 14)  # Redondear hacia arriba
            stats['grupos_recomendados'] = grupos_recomendados

        # Generar texto de estadísticas
        stats_texto = f"📈 ESTADÍSTICAS GENERALES:\n"
        stats_texto += f"Total alumnos: {total_alumnos}\n"
        stats_texto += f"Con experiencia: {con_experiencia} ({con_experiencia / total_alumnos * 100:.1f}%)\n"
        stats_texto += f"Sin experiencia: {sin_experiencia} ({sin_experiencia / total_alumnos * 100:.1f}%)\n\n"

        if stats_asignaturas:
            stats_texto += f"📚 POR ASIGNATURA:\n"
            for asig_key, stats in sorted(stats_asignaturas.items()):
                if '_' in asig_key:
                    sem, nombre = asig_key.split('_', 1)
                    nombre_completo = f"{nombre} ({sem}º)"
                else:
                    nombre_completo = asig_key

                total = stats['total']
                con_exp = stats['con_experiencia']
                sin_exp = stats['sin_experiencia']
                grupos = stats['grupos_recomendados']

                stats_texto += f"• {nombre_completo}: {total} alumnos\n"
                stats_texto += f"  - Con exp.: {con_exp}, Sin exp.: {sin_exp}, Grupos: {grupos}\n"

        self.texto_stats.setText(stats_texto)

        # Actualizar configuración global si es posible
        if self.parent_window:
            try:
                # Actualizar estadísticas en la configuración de asignaturas
                config_asignaturas = self.parent_window.configuracion["configuracion"]["asignaturas"]
                if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                    for asig_key, stats in stats_asignaturas.items():
                        # Buscar asignatura en configuración global
                        for codigo, asig_data in config_asignaturas["datos"].items():
                            nombre_asig = asig_data.get("nombre", "")
                            if f"1_{nombre_asig}" == asig_key or f"2_{nombre_asig}" == asig_key:
                                # Actualizar estadísticas
                                if "estadisticas_calculadas" not in asig_data:
                                    asig_data["estadisticas_calculadas"] = {}

                                asig_data["estadisticas_calculadas"].update({
                                    'total_matriculados': stats['total'],
                                    'con_lab_anterior': stats['con_experiencia'],
                                    'sin_lab_anterior': stats['sin_experiencia'],
                                    'grupos_recomendados': stats['grupos_recomendados'],
                                    'ultima_actualizacion': datetime.now().isoformat()
                                })
                                break

                self.log_mensaje("📊 Estadísticas sincronizadas con configuración global", "success")
            except Exception as e:
                self.log_mensaje(f"⚠️ Error sincronizando estadísticas: {e}", "warning")

    def importar_desde_csv(self):
        """Importar alumnos desde archivo CSV"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Alumnos desde CSV",
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
            alumnos_importados = 0
            alumnos_duplicados = 0

            for _, row in df.iterrows():
                dni = str(row['dni']).strip().upper()
                if not dni:
                    continue

                if dni in self.datos_configuracion:
                    alumnos_duplicados += 1
                    continue

                # Procesar asignaturas matriculadas si existe la columna
                asignaturas_matriculadas = []
                if 'asignatura' in df.columns and pd.notna(row['asignatura']):
                    # Una sola asignatura por fila (formato del ejemplo)
                    asignatura = str(row['asignatura']).strip()
                    # Detectar semestre basado en asignaturas disponibles
                    for sem in ["1", "2"]:
                        if asignatura in self.asignaturas_disponibles.get(sem, {}):
                            asignaturas_matriculadas.append(f"{sem}_{asignatura}")
                            break

                self.datos_configuracion[dni] = {
                    'dni': dni,
                    'nombre': str(row['nombre']).strip(),
                    'apellidos': str(row.get('apellidos', '')).strip(),
                    'email': str(row.get('email', '')).strip().lower(),
                    'expediente': str(row.get('expediente', '')).strip(),
                    'fecha_matricula': datetime.now().strftime('%Y-%m-%d'),
                    'grupo': str(row.get('grupo', '')).strip().upper(),
                    'asignaturas_matriculadas': asignaturas_matriculadas,
                    'lab_anterior': str(row.get('lab_anterior', 'no')).lower() in ['si', 'sí', 'true', '1', 'yes'],
                    'observaciones': str(row.get('observaciones', '')).strip(),
                    'fecha_creacion': datetime.now().isoformat()
                }
                alumnos_importados += 1

            # Auto-ordenar
            self.ordenar_alumnos_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.marcar_cambio_realizado()

            mensaje = f"✅ Importación completada:\n"
            mensaje += f"• {alumnos_importados} alumnos importados\n"
            if alumnos_duplicados > 0:
                mensaje += f"• {alumnos_duplicados} alumnos duplicados (omitidos)"

            QMessageBox.information(self, "Importación Exitosa", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación",
                                 f"Error al importar archivo CSV:\n{str(e)}")

    def exportar_a_csv(self):
        """Exportar alumnos a archivo CSV"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay alumnos para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Alumnos a CSV",
            f"alumnos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Archivos CSV (*.csv)"
        )

        if not archivo:
            return

        try:
            datos_export = []
            for dni, datos in self.datos_configuracion.items():
                # Expandir por asignatura (una fila por asignatura)
                asignaturas = datos.get('asignaturas_matriculadas', [])
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
                        'expediente': datos.get('expediente', ''),
                        'grupo': datos.get('grupo', ''),
                        'fecha_matricula': datos.get('fecha_matricula', ''),
                        'asignatura': asignatura,
                        'semestre': sem,
                        'lab_anterior': 'Si' if datos.get('lab_anterior', False) else 'No',
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
            QMessageBox.information(self, "Sin Datos", "No hay alumnos para generar estadísticas")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Estadísticas",
            f"estadisticas_alumnos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            # Generar estadísticas actualizadas
            self.actualizar_estadisticas()
            contenido_stats = self.texto_stats.toPlainText()

            # Añadir información adicional
            contenido_completo = f"ESTADÍSTICAS DE ALUMNOS - OPTIM Labs\n"
            contenido_completo += f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            contenido_completo += f"{'=' * 50}\n\n"
            contenido_completo += contenido_stats
            contenido_completo += f"\n\n{'=' * 50}\n"
            contenido_completo += f"Filtro aplicado: {self.filtro_asignatura_actual}\n"
            contenido_completo += f"Total configurado: {len(self.datos_configuracion)} alumnos\n"

            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(contenido_completo)

            QMessageBox.information(self, "Exportación Exitosa", f"Estadísticas exportadas a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación",
                                 f"Error al exportar estadísticas:\n{str(e)}")

    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Alumnos",
            "", "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "alumnos" in datos_cargados:
                self.datos_configuracion = datos_cargados["alumnos"]
            elif isinstance(datos_cargados, dict):
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Auto-ordenar
            self.ordenar_alumnos_alfabeticamente()

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.alumno_actual = None
            self.label_alumno_actual.setText("Seleccione un alumno")
            self.info_alumno.setText("ℹ️ Seleccione un alumno para ver sus detalles")
            self.btn_duplicar.setEnabled(False)

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def guardar_en_archivo(self):
        """Guardar configuración en archivo JSON"""
        if not self.datos_configuracion:
            QMessageBox.warning(self, "Sin Datos", "No hay alumnos configurados para guardar.")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Alumnos",
            f"alumnos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'alumnos': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_alumnos': len(self.datos_configuracion),
                    'filtro_aplicado': self.filtro_asignatura_actual,
                    'generado_por': 'OPTIM Labs - Configurar Alumnos'
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
                QMessageBox.warning(self, "Sin Datos", "No hay alumnos configurados para guardar.")
                return

            total_alumnos = len(self.datos_configuracion)
            con_experiencia = sum(1 for datos in self.datos_configuracion.values()
                                  if datos.get('lab_anterior', False))

            # Contar asignaturas únicas
            asignaturas_unicas = set()
            for datos in self.datos_configuracion.values():
                asignaturas_unicas.update(datos.get('asignaturas_matriculadas', []))

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• {total_alumnos} alumnos configurados\n"
                f"• {con_experiencia} con experiencia previa\n"
                f"• {len(asignaturas_unicas)} asignaturas distintas\n\n"
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

    def limpiar_todos_alumnos(self):
        """Limpiar todos los alumnos configurados"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay alumnos para limpiar")
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Todo",
            f"¿Está seguro de eliminar todos los alumnos configurados?\n\n"
            f"Se eliminarán {len(self.datos_configuracion)} alumnos.\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion.clear()
            self.alumno_actual = None

            # Actualizar interfaz
            self.aplicar_filtro_asignatura()
            self.label_alumno_actual.setText("Seleccione un alumno")
            self.info_alumno.setText("ℹ️ Seleccione un alumno para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Limpieza Completada", "Todos los alumnos han sido eliminados")

    def ordenar_alumnos_alfabeticamente(self):
        """Reordenar alumnos alfabéticamente por apellidos + nombre"""
        if not self.datos_configuracion:
            return

        # Crear lista ordenada por apellidos + nombre
        alumnos_ordenados = sorted(
            self.datos_configuracion.items(),
            key=lambda x: f"{x[1].get('apellidos', '')} {x[1].get('nombre', '')}"
        )

        # Crear nuevo diccionario ordenado
        self.datos_configuracion = dict(alumnos_ordenados)

    def auto_seleccionar_alumno(self, dni):
        """Auto-seleccionar alumno por DNI"""
        try:
            for i in range(self.list_alumnos.count()):
                item = self.list_alumnos.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == dni:
                    self.list_alumnos.setCurrentItem(item)
                    self.seleccionar_alumno(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando alumno: {e}", "warning")

    def seleccionar_alumno_por_dni(self, dni):
        """Seleccionar alumno por DNI después de actualización"""
        if dni in self.datos_configuracion:
            # Buscar el item en la lista y seleccionarlo
            for i in range(self.list_alumnos.count()):
                item = self.list_alumnos.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == dni:
                    self.list_alumnos.setCurrentItem(item)
                    self.seleccionar_alumno(item)
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
            self.log_mensaje("🔚 Cerrando configuración de alumnos", "info")
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
                "alumnos": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarAlumnos",
                    "cambios_descartados": True
                }
            }

            self.configuracion_actualizada.emit(datos_para_sistema)
            self.datos_configuracion = datos_originales
            self.datos_guardados_en_sistema = False

            self.log_mensaje("📤 Cambios cancelados y estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cancelando cambios: {e}", "warning")


class SelectorAsignaturaDialog(QDialog):
    """Dialog para seleccionar asignatura para importación"""

    def __init__(self, asignaturas_disponibles, titulo="Seleccionar Asignatura", parent=None):
        super().__init__(parent)
        self.asignaturas_disponibles = asignaturas_disponibles
        self.asignatura_seleccionada = None
        self.setWindowTitle(titulo)
        self.setModal(True)

        # Centrar ventana
        center_window_on_screen_immediate(self, 500, 300)

        self.setup_ui()
        self.apply_dark_theme()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Título
        titulo_label = QLabel("📚 Selecciona la asignatura:")
        titulo_label.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(titulo_label)

        # Lista de asignaturas
        self.list_asignaturas = QListWidget()
        self.list_asignaturas.setMinimumHeight(150)

        # Cargar asignaturas por semestre
        sem1 = self.asignaturas_disponibles.get("1", {})
        sem2 = self.asignaturas_disponibles.get("2", {})

        if sem1:
            # Separador 1º Semestre
            item_sep1 = QListWidgetItem("📋 1º SEMESTRE")
            item_sep1.setFlags(Qt.ItemFlag.NoItemFlags)
            item_sep1.setBackground(QColor(74, 158, 255, 30))
            self.list_asignaturas.addItem(item_sep1)

            for nombre, asig_data in sorted(sem1.items()):
                codigo = asig_data.get("codigo", nombre)  # USAR CÓDIGO
                # MOSTRAR: "FIS1 - Física I"
                item = QListWidgetItem(f"  {codigo} - {nombre}")
                item.setData(Qt.ItemDataRole.UserRole, ("1", codigo, nombre))
                self.list_asignaturas.addItem(item)

        if sem2:
            # Separador 2º Semestre
            item_sep2 = QListWidgetItem("📋 2º SEMESTRE")
            item_sep2.setFlags(Qt.ItemFlag.NoItemFlags)
            item_sep2.setBackground(QColor(74, 158, 255, 30))
            self.list_asignaturas.addItem(item_sep2)

            for nombre, asig_data in sorted(sem2.items()):
                codigo = asig_data.get("codigo", nombre)  # USAR CÓDIGO
                # MOSTRAR: "EANA - Electrónica Analógica"
                item = QListWidgetItem(f"  {codigo} - {nombre}")
                item.setData(Qt.ItemDataRole.UserRole, ("2", codigo, nombre))
                self.list_asignaturas.addItem(item)

        if not sem1 and not sem2:
            item_vacio = QListWidgetItem("⚠️ No hay asignaturas configuradas en el sistema")
            item_vacio.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_asignaturas.addItem(item_vacio)

        layout.addWidget(self.list_asignaturas)

        # Información
        info_label = QLabel("💡 Selecciona la asignatura para la cual se importarán los datos")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-top: 10px;")
        layout.addWidget(info_label)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        # Conectar doble clic
        self.list_asignaturas.itemDoubleClicked.connect(self.accept_selection)

    def accept_selection(self):
        current_item = self.list_asignaturas.currentItem()
        if not current_item or current_item.flags() == Qt.ItemFlag.NoItemFlags:
            QMessageBox.warning(self, "Selección requerida", "Debe seleccionar una asignatura")
            return

        data = current_item.data(Qt.ItemDataRole.UserRole)
        if data:
            semestre, codigo, nombre = data
            self.asignatura_seleccionada = {
                "semestre": semestre,
                "codigo": codigo,
                "nombre": nombre,
                "key": codigo
            }
            self.accept()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
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
            QLabel { color: #ffffff; }
        """)


def main():
    """Función principal para testing"""
    app = QApplication(sys.argv)

    # Aplicar tema oscuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Datos de ejemplo con estructura corregida
    datos_ejemplo = {
        "12345678A": {
            "dni": "12345678A",
            "nombre": "Juan",
            "apellidos": "García López",
            "email": "juan.garcia@alumnos.upm.es",
            "matricula": "2024000123",
            "cursos_matriculado": ["A202", "B204"],
            "asignaturas_matriculadas": {
                "1_Fisica I": {"matriculado": True, "lab_aprobado": False},
                "2_Quimica Organica": {"matriculado": True, "lab_aprobado": True}
            },
            "exp_centro": "GIN-14-123456",
            "exp_agora": "AGR123456",
            "observaciones": "Alumno destacado",
            "fecha_creacion": datetime.now().isoformat()
        },
        "23456789B": {
            "dni": "23456789B",
            "nombre": "María",
            "apellidos": "Fernández Ruiz",
            "email": "maria.fernandez@alumnos.upm.es",
            "matricula": "2024000124",
            "grupo": "B204",
            "asignaturas_matriculadas": {
                "1_Fisica I": {"matriculado": True, "lab_aprobado": True}
            },
            "exp_centro": "QUI200-124",
            "exp_agora": "AGR789012",
            "observaciones": "",
            "fecha_creacion": datetime.now().isoformat()
        }
    }

    # La ventana ya se centra automáticamente en su constructor
    window = ConfigurarAlumnos(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()