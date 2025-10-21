#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Alumnos - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import re
import json
import unicodedata
import pandas as pd
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QGroupBox, QFrame, QScrollArea, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QSizePolicy, QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor


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

def obtener_ruta_descargas():
    """Obtener la ruta de la carpeta Downloads del usuario"""

    # Intentar diferentes métodos para obtener Downloads
    try:
        # Método 1: Variable de entorno USERPROFILE (Windows)
        if os.name == 'nt':  # Windows
            downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        else:  # Linux/Mac
            downloads = os.path.join(os.path.expanduser('~'), 'Downloads')

        # Verificar que existe
        if os.path.exists(downloads):
            return downloads

        # Fallback: Desktop si Downloads no existe
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        if os.path.exists(desktop):
            return desktop

        # Último fallback: home del usuario
        return os.path.expanduser('~')

    except:
        # Si todo falla, usar directorio actual
        return os.getcwd()


class GestionAlumnoDialog(QDialog):
    """Dialog para añadir/editar alumno con gestión de asignaturas"""

    def __init__(self, alumno_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        #self.grupo_actual_seleccionado = None
        self.alumno_existente = alumno_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {"1": {}, "2": {}}
        self.grupos_disponibles = self.obtener_grupos_del_sistema()
        self.setWindowTitle("Editar Alumno" if alumno_existente else "Nuevo Alumno")
        self.setModal(True)

        # Centrar sin parpadeos
        window_width = 1100
        window_height = 950
        center_window_on_screen_immediate(self, window_width, window_height)
        self.setMinimumSize(1000, 900)

        self.setup_ui()
        self.apply_dark_theme()

        # Forzar tamaños iguales de ok/cancel
        QTimer.singleShot(50, self.igualar_tamanos_botones_ok_cancel)

        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)

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

        # 👤 Datos personales de alumno
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

        # 🎓📚 Selección de grupos y asignaturas matriculadas
        grupos_asignaturas_group = QGroupBox("🎓📚 GRUPOS Y ASIGNATURAS MATRICULADAS")
        grupos_asignaturas_main_layout = QHBoxLayout()  # Layout horizontal principal
        grupos_asignaturas_main_layout.setSpacing(15)

        # COLUMNA IZQUIERDA: GRUPOS MATRICULADOS
        grupos_container = QWidget()
        grupos_main_layout = QVBoxLayout(grupos_container)
        grupos_main_layout.setSpacing(8)
        grupos_main_layout.setContentsMargins(0, 0, 0, 0)

        grupos_title = QLabel("🎓 GRUPOS MATRICULADOS")
        grupos_title.setStyleSheet("""
            color: #4a9eff; 
            font-weight: bold; 
            font-size: 14px; 
            margin-bottom: 8px;
            padding: 6px;
            border-bottom: 2px solid #4a9eff;
        """)
        grupos_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grupos_main_layout.addWidget(grupos_title)

        if self.grupos_disponibles:
            info_grupos = QLabel("Selecciona los grupos matriculados:")
            info_grupos.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 6px;")
            grupos_main_layout.addWidget(info_grupos)

            # Área desplazable para listado de grupos
            self.grupos_scroll = QScrollArea()
            self.grupos_scroll.setWidgetResizable(True)
            self.grupos_scroll.setFixedHeight(300)
            self.grupos_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.grupos_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.grupos_scroll.setFrameStyle(QFrame.Shape.Box)
            self.grupos_scroll.setLineWidth(1)

            # Widget scrollable para grupos
            self.grupos_scroll_widget = QWidget()
            self.grupos_scroll_layout = QVBoxLayout(self.grupos_scroll_widget)
            self.grupos_scroll_layout.setContentsMargins(10, 10, 10, 10)
            self.grupos_scroll_layout.setSpacing(8)
            self.grupos_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Crear checkboxes por grupos del sistema (comportamiento radio button)
            self.checks_grupos = {}
            self.grupo_actual_seleccionado = None
            for codigo, grupo_data in sorted(self.grupos_disponibles.items()):
                nombre = grupo_data.get("nombre", codigo)
                grupo_actual = grupo_data.get("grupo_actual", "")

                # Mostrar: "A102 - Grado en Ingeniería en Tecnologías Industriales (1º Grupo)"
                texto_completo = f"{codigo} - {nombre}"
                if grupo_actual:
                    texto_completo += f" ({grupo_actual})"

                check_grupo = QCheckBox(texto_completo)
                check_grupo.setStyleSheet(self.estilo_checkbox_comun)
                check_grupo.toggled.connect(lambda checked, c=codigo: self.manejar_seleccion_unica_grupo(c, checked))
                self.checks_grupos[codigo] = check_grupo
                self.grupos_scroll_layout.addWidget(check_grupo)

            # Añadir stretch al final
            self.grupos_scroll_layout.addStretch()

            # Configurar el scroll area
            self.grupos_scroll.setWidget(self.grupos_scroll_widget)
            grupos_main_layout.addWidget(self.grupos_scroll)
        else:
            no_grupos_label = QLabel("⚠️ No hay grupos configurados en el sistema.")
            no_grupos_label.setStyleSheet("color: #ffaa00; font-style: italic; padding: 20px; font-size: 12px;")
            grupos_main_layout.addWidget(no_grupos_label)
            self.checks_grupos = {}

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

        # Contenedor desplazable
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

        # Configurar el layout en el widget
        self.asignaturas_scroll_widget.setLayout(self.asignaturas_scroll_layout)

        # Diccionarios para checkboxes
        self.checks_asignaturas = {}
        self.checks_lab_aprobado = {}

        # Inicialización con mensaje de ayuda
        self.mostrar_mensaje_seleccionar_grupos()

        # CONFIGURAR EL SCROLL AREA - DESPUÉS de configurar el layout
        self.asignaturas_scroll.setWidget(self.asignaturas_scroll_widget)
        asignaturas_main_layout.addWidget(self.asignaturas_scroll)

        # Añadir las dos columnas al layout principal
        grupos_asignaturas_main_layout.addWidget(grupos_container, 1)  # 50% del ancho
        grupos_asignaturas_main_layout.addWidget(asignaturas_container, 1)  # 50% del ancho

        grupos_asignaturas_group.setLayout(grupos_asignaturas_main_layout)
        layout.addWidget(grupos_asignaturas_group)

        # Observaciones
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

    def mostrar_mensaje_seleccionar_grupos(self):
        """Mostrar mensaje inicial para seleccionar grupos"""
        # Limpiar layout
        self.limpiar_layout_asignaturas()

        # Mensaje inicial
        mensaje_label = QLabel("⚠️ Selecciona primero los grupos para ver las asignaturas disponibles.")
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

        # Actualiza el área desplazable para reflejar cambios
        self.asignaturas_scroll_widget.adjustSize()
        self.asignaturas_scroll.updateGeometry()

    def limpiar_layout_asignaturas(self):
        """Limpiar el layout de asignaturas de forma segura"""
        # Limpiar diccionarios PRIMERO
        self.checks_asignaturas.clear()
        self.checks_lab_aprobado.clear()

        # Limpia completamente el layout (remueve y destruye widgets)
        while self.asignaturas_scroll_layout.count():
            child = self.asignaturas_scroll_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)  # CRÍTICO: desconectar del padre
                widget.deleteLater()

        # Procesar eventos pendientes para que se eliminen los widgets
        QApplication.processEvents()

        # FORZAR ACTUALIZACIÓN FINAL
        self.asignaturas_scroll_widget.updateGeometry()
        self.asignaturas_scroll.updateGeometry()

    def obtener_grupos_del_sistema(self):
        """Obtener códigos de grupos disponibles desde el sistema global"""
        try:
            if self.parent() and hasattr(self.parent(), 'parent_window'):
                parent_window = self.parent().parent_window
                if parent_window and hasattr(parent_window, 'configuracion'):
                    config_grupos = parent_window.configuracion["configuracion"]["grupos"]
                    if config_grupos.get("configurado") and config_grupos.get("datos"):
                        grupos_disponibles = {}
                        for codigo, grupo_data in config_grupos["datos"].items():
                            nombre = grupo_data.get("nombre", codigo)
                            grupos_disponibles[codigo] = {
                                "codigo": codigo,
                                "nombre": nombre,
                                "grupo_actual": grupo_data.get("grupo_actual", ""),
                                "asignaturas_asociadas": grupo_data.get("asignaturas_asociadas", [])
                            }
                        return grupos_disponibles
            return {}
        except Exception as e:
            print(f"Error obteniendo códigos de grupos: {e}")
            return {}

    def filtrar_asignaturas_por_grupos(self):
        """Filtrar asignaturas disponibles según grupos seleccionados"""
        # Obtener códigos de grupos seleccionados
        grupos_seleccionados = [codigo for codigo, check in self.checks_grupos.items() if check.isChecked()]

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

        if not grupos_seleccionados:
            # Si no hay grupos seleccionados, mostrar mensaje
            self.mostrar_mensaje_seleccionar_grupos()
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
                            grupos_asociados = asig_data.get("grupos_asociados", [])

                            # Detectar semestre
                            if "1º" in semestre_str or "primer" in semestre_str.lower():
                                semestre = "1"
                            elif "2º" in semestre_str or "segundo" in semestre_str.lower():
                                semestre = "2"
                            else:
                                semestre = "1"

                            # Si la asignatura es cursada por algún grupo seleccionado
                            if any(grupo in grupos_asociados for grupo in grupos_seleccionados):
                                asignaturas_filtradas[semestre][codigo_asig] = {
                                    "codigo": codigo_asig,
                                    "nombre": nombre_asig,
                                    "semestre": semestre_str
                                }

        except Exception as e:
            print(f"Error filtrando asignaturas por grupos: {e}")

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
        """Crear checkboxes de asignaturas filtradas para el grupo seleccionado"""
        # Obtener grupo seleccionado actual
        grupo_seleccionado = None
        for codigo, check in self.checks_grupos.items():
            if check.isChecked():
                grupo_seleccionado = codigo
                break

        if not grupo_seleccionado:
            # No hay grupo seleccionado, mostrar mensaje
            no_grupo_label = QLabel("⚠️ Selecciona un grupo para ver sus asignaturas.")
            no_grupo_label.setStyleSheet("""
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
            no_grupo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_grupo_label.setWordWrap(True)
            self.asignaturas_scroll_layout.addWidget(no_grupo_label)
            self.actualizar_scroll_asignaturas()
            return

        if not asignaturas_data.get("1") and not asignaturas_data.get("2"):
            # No hay asignaturas para el grupo seleccionado
            no_asig_label = QLabel("⚠️ No hay asignaturas configuradas para este grupo.")
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
                self.crear_fila_asignatura_con_texto(codigo_asignatura, texto_completo, grupo_seleccionado)

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
                self.crear_fila_asignatura_con_texto(codigo_asignatura, texto_completo, grupo_seleccionado)

        # Añadir stretch al final
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

    def crear_fila_asignatura_con_texto(self, codigo_asignatura, texto_mostrar, grupo_actual):
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
        check_asignatura = QCheckBox(texto_mostrar)
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

        # Conectar señales con validación de cambio de grupo
        check_asignatura.toggled.connect(
            lambda checked, asig=codigo_asignatura, grp=grupo_actual:
            self.validar_cambio_asignatura_grupo(checked, asig, grp)
        )
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

    def validar_cambio_asignatura_grupo(self, checked, codigo_asignatura, grupo_nuevo):
        """Validar si la asignatura ya está en otro grupo y confirmar cambio"""
        if not checked:
            return  # Si se desmarca, no hay validación

        # Buscar si la asignatura ya está asignada a otro grupo
        grupo_anterior = None
        for codigo_grupo, check_grupo in self.checks_grupos.items():
            if codigo_grupo == grupo_nuevo:
                continue  # Saltar el grupo actual

            # Verificar si este grupo tiene la asignatura marcada
            # Evitar actualización mientras se procesa un cambio de grupo
            if hasattr(self, 'estado_asignaturas_previo'):
                if codigo_grupo in self.estado_asignaturas_previo:
                    if codigo_asignatura in self.estado_asignaturas_previo[codigo_grupo]:
                        if self.estado_asignaturas_previo[codigo_grupo][codigo_asignatura].get('matriculado', False):
                            grupo_anterior = codigo_grupo
                            break

        if grupo_anterior:
            # La asignatura ya está en otro grupo
            nombre_asig = codigo_asignatura
            try:
                for sem in ["1", "2"]:
                    for codigo, asig_data in self.asignaturas_disponibles.get(sem, {}).items():
                        if codigo == codigo_asignatura:
                            nombre_asig = asig_data.get('nombre', codigo_asignatura)
                            break
            except:
                pass

            # Obtener nombres de grupos
            nombre_grupo_anterior = grupo_anterior
            nombre_grupo_nuevo = grupo_nuevo
            if self.grupos_disponibles:
                if grupo_anterior in self.grupos_disponibles:
                    nombre_grupo_anterior = f"{grupo_anterior} - {self.grupos_disponibles[grupo_anterior].get('nombre', grupo_anterior)}"
                if grupo_nuevo in self.grupos_disponibles:
                    nombre_grupo_nuevo = f"{grupo_nuevo} - {self.grupos_disponibles[grupo_nuevo].get('nombre', grupo_nuevo)}"

            # Preguntar al usuario
            respuesta = QMessageBox.question(
                self, "Cambio de Grupo",
                f"La asignatura '{nombre_asig}' ya está asociada al grupo:\n"
                f"  • {nombre_grupo_anterior}\n\n"
                f"¿Deseas cambiarla al grupo:\n"
                f"  • {nombre_grupo_nuevo}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.No:
                # Usuario rechazó el cambio, desmarcar el checkbox
                check_asig = self.checks_asignaturas.get(codigo_asignatura)
                if check_asig:
                    check_asig.blockSignals(True)
                    check_asig.setChecked(False)
                    check_asig.blockSignals(False)
            else:
                # Usuario aceptó el cambio, eliminar de grupo anterior
                if hasattr(self, 'estado_asignaturas_previo'):
                    if grupo_anterior in self.estado_asignaturas_previo:
                        if codigo_asignatura in self.estado_asignaturas_previo[grupo_anterior]:
                            del self.estado_asignaturas_previo[grupo_anterior][codigo_asignatura]

    def grupo_seleccionado_cambio(self):
        """Manejar cambio de selección de grupo (radio button behavior)"""
        # Guardar estado de asignaturas del grupo anterior
        grupo_anterior = getattr(self, 'grupo_actual_seleccionado', None)

        if grupo_anterior:
            # Guardar estado actual
            if not hasattr(self, 'estado_asignaturas_previo'):
                self.estado_asignaturas_previo = {}

            self.estado_asignaturas_previo[grupo_anterior] = {}
            for key, check_asig in self.checks_asignaturas.items():
                if check_asig.isChecked():
                    lab_aprobado = False
                    if key in self.checks_lab_aprobado and self.checks_lab_aprobado[key].isEnabled():
                        lab_aprobado = self.checks_lab_aprobado[key].isChecked()

                    self.estado_asignaturas_previo[grupo_anterior][key] = {
                        'matriculado': True,
                        'lab_aprobado': lab_aprobado
                    }

        # Encontrar nuevo grupo seleccionado
        nuevo_grupo = None
        for codigo, check in self.checks_grupos.items():
            if check.isChecked():
                nuevo_grupo = codigo
                break

        if not nuevo_grupo:
            # No hay grupo seleccionado, limpiar vista
            self.limpiar_layout_asignaturas()
            no_grupo_label = QLabel("⚠️ Selecciona un grupo para ver sus asignaturas.")
            no_grupo_label.setStyleSheet("""
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
            no_grupo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_grupo_label.setWordWrap(True)
            self.asignaturas_scroll_layout.addWidget(no_grupo_label)
            self.actualizar_scroll_asignaturas()
            self.grupo_actual_seleccionado = None
            return

        # Actualizar grupo actual
        self.grupo_actual_seleccionado = nuevo_grupo

        # Cargar asignaturas del nuevo grupo
        self.cargar_asignaturas_del_grupo(nuevo_grupo)

    def cargar_asignaturas_del_grupo(self, codigo_grupo):
        """Cargar y mostrar asignaturas asociadas al grupo seleccionado"""
        # Limpiar asignaturas actuales
        self.limpiar_layout_asignaturas()

        # Obtener asignaturas asociadas al grupo desde el sistema
        asignaturas_del_grupo = {"1": {}, "2": {}}

        try:
            if self.parent() and hasattr(self.parent(), 'parent_window'):
                parent_window = self.parent().parent_window
                if parent_window and hasattr(parent_window, 'configuracion'):
                    config_asignaturas = parent_window.configuracion["configuracion"]["asignaturas"]
                    if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                        for codigo_asig, asig_data in config_asignaturas["datos"].items():
                            nombre_asig = asig_data.get("nombre", codigo_asig)
                            semestre_str = asig_data.get("semestre", "1º Semestre")
                            grupos_asociados = asig_data.get("grupos_asociados", {})

                            # Verificar si este grupo está asociado a la asignatura
                            if codigo_grupo in grupos_asociados:
                                # Detectar semestre
                                if "1º" in semestre_str or "primer" in semestre_str.lower():
                                    semestre = "1"
                                elif "2º" in semestre_str or "segundo" in semestre_str.lower():
                                    semestre = "2"
                                else:
                                    semestre = "1"

                                asignaturas_del_grupo[semestre][codigo_asig] = {
                                    "codigo": codigo_asig,
                                    "nombre": nombre_asig,
                                    "semestre": semestre_str
                                }

        except Exception as e:
            print(f"Error cargando asignaturas del grupo: {e}")

        # Recrear checkboxes de asignaturas
        self.crear_asignaturas_filtradas(asignaturas_del_grupo)

        # Restaurar estado guardado de este grupo si existe
        if hasattr(self, 'estado_asignaturas_previo') and codigo_grupo in self.estado_asignaturas_previo:
            QApplication.processEvents()  # Asegurar que los widgets están creados

            for key, estado in self.estado_asignaturas_previo[codigo_grupo].items():
                if key in self.checks_asignaturas:
                    check_asig = self.checks_asignaturas[key]
                    check_asig.setChecked(True)

                    # Restaurar lab aprobado
                    if key in self.checks_lab_aprobado:
                        lab_check = self.checks_lab_aprobado[key]
                        lab_check.setEnabled(True)
                        lab_check.setChecked(estado.get('lab_aprobado', False))

        # Forzar actualización final del scroll area
        QApplication.processEvents()
        self.actualizar_scroll_asignaturas()

    def manejar_seleccion_unica_grupo(self, codigo_grupo, checked):
        """Comportamiento de radio button: solo un grupo seleccionado a la vez"""
        if checked:
            # Desmarcar todos los demás grupos
            for codigo, check in self.checks_grupos.items():
                if codigo != codigo_grupo and check.isChecked():
                    check.blockSignals(True)
                    check.setChecked(False)
                    check.blockSignals(False)

            # Manejar cambio de grupo
            self.grupo_seleccionado_cambio()

    def cargar_datos_existentes(self):
        """Cargar datos del alumno existente - SCROLL FINAL"""
        if not self.alumno_existente:
            return

        datos = self.alumno_existente

        # Datos personales
        self.edit_dni.setText(datos.get('dni', ''))
        self.edit_nombre.setText(datos.get('nombre', ''))
        self.edit_apellidos.setText(datos.get('apellidos', ''))
        self.edit_email.setText(datos.get('email', ''))

        # Expedientes
        self.edit_exp_centro.setText(datos.get('exp_centro', ''))
        self.edit_exp_agora.setText(datos.get('exp_agora', ''))

        # Observaciones
        self.edit_observaciones.setText(datos.get('observaciones', ''))

        # GRUPOS MATRICULADO - CARGAR ESTADO POR GRUPO
        grupos_matriculado = datos.get('grupos_matriculado', [])
        asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

        # Inicializar estado de asignaturas por grupo
        if not hasattr(self, 'estado_asignaturas_previo'):
            self.estado_asignaturas_previo = {}

        # Organizar asignaturas por grupo
        for asig_key, info_asignatura in asignaturas_matriculadas.items():
            if info_asignatura.get('matriculado', False):
                grupo_asig = info_asignatura.get('grupo', '')
                if grupo_asig:
                    if grupo_asig not in self.estado_asignaturas_previo:
                        self.estado_asignaturas_previo[grupo_asig] = {}

                    self.estado_asignaturas_previo[grupo_asig][asig_key] = {
                        'matriculado': True,
                        'lab_aprobado': info_asignatura.get('lab_aprobado', False)
                    }

        # LIMPIAR SELECCIÓN PREVIA
        for check in self.checks_grupos.values():
            check.setChecked(False)

        # Seleccionar el primer grupo disponible
        if grupos_matriculado:
            primer_grupo = grupos_matriculado[0]
            if primer_grupo in self.checks_grupos:
                # Bloquear señales temporalmente para evitar guardado prematuro
                self.checks_grupos[primer_grupo].blockSignals(True)
                self.checks_grupos[primer_grupo].setChecked(True)
                self.checks_grupos[primer_grupo].blockSignals(False)

                # Establecer grupo actual y cargar manualmente
                self.grupo_actual_seleccionado = primer_grupo
                self.cargar_asignaturas_del_grupo(primer_grupo)

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

    def _normalize_text(self, s: str) -> str:
        if s is None:
            return ""
        s = str(s).strip()
        # Elimina acentos y pasa a MAYÚSCULAS
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s.upper()

    def get_datos_alumno(self):
        """Obtener datos configurados del alumno con nueva estructura"""

        # CRÍTICO: Guardar estado del grupo ACTUAL antes de leer
        grupo_actual = getattr(self, 'grupo_actual_seleccionado', None)
        if grupo_actual:
            if not hasattr(self, 'estado_asignaturas_previo'):
                self.estado_asignaturas_previo = {}

            # Guardar asignaturas del grupo que estamos viendo ahora
            self.estado_asignaturas_previo[grupo_actual] = {}
            for key, check_asig in self.checks_asignaturas.items():
                if check_asig.isChecked():
                    lab_aprobado = False
                    if key in self.checks_lab_aprobado and self.checks_lab_aprobado[key].isEnabled():
                        lab_aprobado = self.checks_lab_aprobado[key].isChecked()

                    self.estado_asignaturas_previo[grupo_actual][key] = {
                        'matriculado': True,
                        'lab_aprobado': lab_aprobado
                    }

        # Obtener asignaturas seleccionadas con información de lab aprobado Y GRUPO
        asignaturas_matriculadas = {}

        # Recorrer todos los grupos guardados
        if hasattr(self, 'estado_asignaturas_previo'):
            for codigo_grupo, asignaturas_grupo in self.estado_asignaturas_previo.items():
                for key, info_asig in asignaturas_grupo.items():
                    if info_asig.get('matriculado', False):
                        asignaturas_matriculadas[key] = {
                            "matriculado": True,
                            "lab_aprobado": info_asig.get('lab_aprobado', False),
                            "grupo": codigo_grupo
                        }

        # Obtener grupos matriculados (todos los grupos con al menos una asignatura)
        grupos_matriculado = list(set(
            info['grupo'] for info in asignaturas_matriculadas.values() if 'grupo' in info
        ))

        return {
            # Datos personales
            'dni': self.edit_dni.text().strip().upper(),
            'nombre': self._normalize_text(self.edit_nombre.text()),
            'apellidos': self._normalize_text(self.edit_apellidos.text()),
            'email': self.edit_email.text().strip().lower(),

            # Grupos y asignaturas
            'grupos_matriculado': sorted(grupos_matriculado),
            'asignaturas_matriculadas': asignaturas_matriculadas,

            # Expedientes
            'exp_centro': self.edit_exp_centro.text().strip(),
            'exp_agora': self.edit_exp_agora.text().strip(),

            # Observaciones
            'observaciones': self.edit_observaciones.toPlainText().strip(),

            # Metadatos
            'fecha_creacion': datetime.now().isoformat()
        }

    def igualar_tamanos_botones_ok_cancel(self):
        """Forzar que OK y Cancel tengan exactamente el mismo tamaño"""
        try:
            button_box = self.findChild(QDialogButtonBox)
            if button_box:
                ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
                cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)

                if ok_button and cancel_button:
                    # Calcular el tamaño más grande y aplicarlo a ambos
                    width = max(ok_button.sizeHint().width(), cancel_button.sizeHint().width(), 60)
                    height = 35

                    ok_button.setFixedSize(width, height)
                    cancel_button.setFixedSize(width, height)

        except Exception as e:
            print(f"Error igualando tamaños: {e}")

    def configurar_botones_uniformes(self):
        """Configurar estilos uniformes para botones OK/Cancel """
        try:
            # Buscar el QDialogButtonBox
            button_box = self.findChild(QDialogButtonBox)
            if button_box:
                # Obtener botones específicos
                ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
                cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)

                # Estilo uniforme para los botones OK/Cancelar
                estilo_uniforme = """
                    QPushButton {
                        background-color: #4a4a4a;
                        color: #ffffff;
                        border: 1px solid #666666;
                        border-radius: 5px;
                        padding: 8px 20px;
                        font-weight: bold;
                        font-size: 12px;
                        min-width: 80px;
                        min-height: 35px;
                        margin: 2px;
                    }
                    QPushButton:hover {
                        background-color: #5a5a5a;
                        border-color: #4a9eff;
                    }
                    QPushButton:pressed {
                        background-color: #3a3a3a;
                    }
                    QPushButton:default {
                        background-color: #4a9eff;
                        border-color: #4a9eff;
                    }
                    QPushButton:default:hover {
                        background-color: #5ab7ff;
                    }
                    QPushButton:default:pressed {
                        background-color: #3a8adf;
                    }
                """

                if ok_button:
                    ok_button.setText("OK")
                    ok_button.setStyleSheet(estilo_uniforme)

                if cancel_button:
                    cancel_button.setText("Cancel")
                    cancel_button.setStyleSheet(estilo_uniforme)

        except Exception as e:
            print(f"Error configurando botones: {e}")

    def apply_dark_theme(self):
        """Aplicar tema oscuro con botones OK/Cancel uniformes"""
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
            QLineEdit, QComboBox, QSpinBox, QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
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

            /* BOTONES OK/CANCEL */
            QDialogButtonBox {
                background-color: transparent;
                border: none;
                margin-top: 10px;
            }

            QDialogButtonBox QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 90px;
                min-height: 35px;
                max-height: 35px;
                margin: 3px;
            }

            QDialogButtonBox QPushButton:hover {
                background-color: #5a5a5a;
                border-color: #4a9eff;
            }

            QDialogButtonBox QPushButton:pressed {
                background-color: #3a3a3a;
            }

            /* ANULAR DIFERENCIAS ENTRE OK Y CANCEL */
            QDialogButtonBox QPushButton:default {
                background-color: #4a4a4a;
                border-color: #666666;
            }

            QDialogButtonBox QPushButton:default:hover {
                background-color: #5a5a5a;
                border-color: #4a9eff;
            }

            QDialogButtonBox QPushButton:default:pressed {
                background-color: #3a3a3a;
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
        self.setWindowTitle("Configurar Alumnos - OPTIM")

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

                        # Se usa CÓDIGO como key
                        if nombre and codigo:  # Solo si tiene nombre y código
                            asignaturas_transformadas[semestre][codigo] = asig_data

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

        # --- Filtros (reorganizado en 2 filas) ---
        filtros_layout = QVBoxLayout()  # antes era QHBoxLayout()

        # Fila 1: Asignatura + Solo sin lab (igual que antes)
        filtros_row1 = QHBoxLayout()
        filtros_row1.addWidget(QLabel("Filtros:"))

        self.combo_filtro_asignatura = QComboBox()
        self.combo_filtro_asignatura.setMaximumWidth(200)
        filtros_row1.addWidget(self.combo_filtro_asignatura)

        self.check_solo_sin_lab = QCheckBox("Solo alumnos con laboratorio pendiente")
        self.check_solo_sin_lab.setToolTip("Mostrar solo alumnos sin experiencia previa")
        self.check_solo_sin_lab.setStyleSheet("""
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
                """)
        filtros_row1.addWidget(self.check_solo_sin_lab)
        filtros_row1.addStretch(1)

        # Fila 2: filtros
        filtros_row2 = QHBoxLayout()
        self.combo_filtro_grupo = QComboBox()
        self.combo_filtro_grupo.setMaximumWidth(180)
        filtros_row2.addWidget(self.combo_filtro_grupo)

        self.check_multi_grupo = QCheckBox("Solo alumnos con >1 grupo")
        self.check_multi_grupo.setToolTip("Mostrar solo alumnos con 2 o más grupos matriculados")
        self.check_multi_grupo.setStyleSheet(self.check_solo_sin_lab.styleSheet())
        filtros_row2.addWidget(self.check_multi_grupo)
        filtros_row2.addStretch(1)

        # Añadir filas al contenedor vertical y al panel
        filtros_layout.addLayout(filtros_row1)
        filtros_layout.addLayout(filtros_row2)
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

        self.btn_buscar_alumno = QPushButton("🔍 Buscar Alumno")
        self.btn_buscar_alumno.clicked.connect(self.buscar_alumno_dialog)
        acciones_layout.addWidget(self.btn_buscar_alumno)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Importar datos
        importar_group = QGroupBox("📥 IMPORTAR DATOS")
        importar_layout = QVBoxLayout()

        self.btn_importar_alumnos = QPushButton("📥 Importar Alumnos")
        self.btn_importar_alumnos.setToolTip("Importar Alumnos desde Excel")
        self.btn_importar_alumnos.clicked.connect(self.importar_alumnos_excel)
        importar_layout.addWidget(self.btn_importar_alumnos)

        self.btn_importar_aprobados = QPushButton("✅ Importar Alumnos Aprobados")
        self.btn_importar_aprobados.setToolTip("Importar Alumnos que han Aprobado desde Excel")
        self.btn_importar_aprobados.clicked.connect(self.importar_alumnos_aprobados)
        importar_layout.addWidget(self.btn_importar_aprobados)

        self.btn_cargar = QPushButton("📤 Importar Datos")
        self.btn_cargar.setToolTip("Importar configuración desde JSON")
        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Exportar datos
        exportar_group = QGroupBox("💾 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

        self.btn_exportar_alumnos = QPushButton("💾 Exportar Datos")
        self.btn_exportar_alumnos.setToolTip("Exportar configuración a JSON")
        self.btn_exportar_alumnos.clicked.connect(self.guardar_en_archivo)
        exportar_layout.addWidget(self.btn_exportar_alumnos)

        self.btn_exportar_estadisticas = QPushButton("📊 Exportar Estadísticas")
        self.btn_exportar_estadisticas.setToolTip("Exportar Estadisticas en TXT")
        self.btn_exportar_estadisticas.clicked.connect(self.exportar_estadisticas)
        exportar_layout.addWidget(self.btn_exportar_estadisticas)

        exportar_group.setLayout(exportar_layout)
        right_layout.addWidget(exportar_group)

        # Guardar configuración
        botones_principales_group = QGroupBox("💾 GUARDAR CONFIGURACIÓN")
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
        """Configurar opciones de filtros (asignaturas y grupos)."""
        # --- Asignaturas ---
        self.combo_filtro_asignatura.clear()
        self.combo_filtro_asignatura.addItem("Todas las asignaturas")

        sem1 = self.asignaturas_disponibles.get("1", {})
        sem2 = self.asignaturas_disponibles.get("2", {})

        if sem1:
            for codigo_asig in sorted(sem1.keys()):
                nombre_asig = sem1[codigo_asig].get('nombre', codigo_asig)
                self.combo_filtro_asignatura.addItem(f"1º - ({codigo_asig}) - {nombre_asig}")

        if sem2:
            for codigo_asig in sorted(sem2.keys()):
                nombre_asig = sem2[codigo_asig].get('nombre', codigo_asig)
                self.combo_filtro_asignatura.addItem(f"2º - ({codigo_asig}) - {nombre_asig}")

        # Filtro por grupo
        self.combo_filtro_grupo.clear()
        self.combo_filtro_grupo.addItem("Todos los grupos")

        try:
            grupos = {}
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                cfg = self.parent_window.configuracion
                grupos_cfg = cfg.get("configuracion", {}).get("grupos", {})
                if grupos_cfg.get("configurado") and grupos_cfg.get("datos"):
                    grupos = grupos_cfg["datos"]

            for codigo in sorted(grupos.keys()):
                # Mostramos solo el código (A404, A408, etc.)
                self.combo_filtro_grupo.addItem(codigo)

        except Exception as e:
            # Si algo falla, dejamos solo "Todos los grupos"
            self.combo_filtro_grupo.clear()
            self.combo_filtro_grupo.addItem("Todos los grupos")

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
        """ Tema oscuro """
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
            QLabel {
                color: #ffffff;
            }
            /* TOOLTIPS */
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

    def conectar_signals(self):
        """Conectar señales de la interfaz."""
        self.list_alumnos.itemClicked.connect(self.seleccionar_alumno)
        self.combo_filtro_asignatura.currentTextChanged.connect(self.aplicar_filtro_asignatura)
        self.check_solo_sin_lab.toggled.connect(self.aplicar_filtro_asignatura)

        # Señales de los filtros añadidos
        self.combo_filtro_grupo.currentTextChanged.connect(self.aplicar_filtro_asignatura)
        self.check_multi_grupo.toggled.connect(self.aplicar_filtro_asignatura)

    def aplicar_filtro_asignatura(self):
        """Aplicar filtros por asignatura, experiencia, grupo y multi-grupo."""
        filtro_texto = self.combo_filtro_asignatura.currentText()
        solo_sin_lab = self.check_solo_sin_lab.isChecked()

        # Leer filtros de grupo
        filtro_grupo = self.combo_filtro_grupo.currentText() if hasattr(self,
                                                                        "combo_filtro_grupo") else "Todos los grupos"
        solo_multi_grupo = self.check_multi_grupo.isChecked() if hasattr(self, "check_multi_grupo") else False

        self.filtro_asignatura_actual = filtro_texto
        self.list_alumnos.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay alumnos configurados")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_alumnos.addItem(item)
            return

        alumnos_filtrados = []

        for dni, datos in self.datos_configuracion.items():
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})
            grupos_matriculado = datos.get('grupos_matriculado', [])

            # --- 1) Filtro por asignatura (igual que antes) ---
            incluir_por_asignatura = False
            if filtro_texto == "Todas las asignaturas":
                incluir_por_asignatura = bool(asignaturas_matriculadas)
            else:
                if " - " in filtro_texto:
                    partes = filtro_texto.split(" - ")
                    if len(partes) >= 2:
                        codigo_parte = partes[1].strip()
                        if codigo_parte.startswith("(") and codigo_parte.endswith(")"):
                            codigo_asignatura = codigo_parte[1:-1]
                            if codigo_asignatura in asignaturas_matriculadas and asignaturas_matriculadas[
                                codigo_asignatura].get('matriculado', False):
                                incluir_por_asignatura = True
            if not incluir_por_asignatura:
                continue

            # --- 2) Filtro “Solo sin lab” (igual que antes, respetando global/específica) ---
            if solo_sin_lab:
                if filtro_texto == "Todas las asignaturas":
                    tiene_alguna_sin_experiencia = any(
                        not asig_info.get('lab_aprobado', False)
                        for asig_info in asignaturas_matriculadas.values()
                        if asig_info.get('matriculado', False)
                    )
                    if not tiene_alguna_sin_experiencia:
                        continue
                else:
                    partes = filtro_texto.split(" - ")
                    if len(partes) >= 2:
                        codigo_parte = partes[1].strip()
                        if codigo_parte.startswith("(") and codigo_parte.endswith(")"):
                            codigo_asignatura = codigo_parte[1:-1]
                            if codigo_asignatura in asignaturas_matriculadas:
                                if asignaturas_matriculadas[codigo_asignatura].get('lab_aprobado', False):
                                    continue

            # --- 3) Filtro por grupo seleccionado ---
            if filtro_grupo != "Todos los grupos":
                if filtro_grupo not in grupos_matriculado:
                    continue

            # --- 4) Solo alumnos con más de un grupo ---
            if solo_multi_grupo:
                if len(grupos_matriculado) < 2:
                    continue

            # Si supera todos los filtros, incluir
            alumnos_filtrados.append((dni, datos))

        # Ordenar por apellidos + nombre (como ahora)
        alumnos_filtrados.sort(key=lambda x: f"{x[1].get('apellidos', '')} {x[1].get('nombre', '')}")

        # Rellenar lista
        if alumnos_filtrados:
            for dni, datos in alumnos_filtrados:
                nombre_completo = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
                grupos_matriculado = datos.get('grupos_matriculado', [])
                if grupos_matriculado:
                    grupos_str = ', '.join(grupos_matriculado[:2])
                    if len(grupos_matriculado) > 2:
                        grupos_str += f" +{len(grupos_matriculado) - 2}"
                else:
                    # Compatibilidad legacy
                    grupos_str = datos.get('grupo', 'Sin grupos')

                # Experiencia (global o por asignatura actual) — misma lógica que ya usabas
                asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})
                if filtro_texto == "Todas las asignaturas":
                    tiene_experiencia = any(
                        asig_info.get('lab_aprobado', False)
                        for asig_info in asignaturas_matriculadas.values()
                    )
                else:
                    partes = filtro_texto.split(" - ")
                    tiene_experiencia = False
                    if len(partes) >= 2:
                        codigo_parte = partes[1].strip()
                        if codigo_parte.startswith("(") and codigo_parte.endswith(")"):
                            codigo_asignatura = codigo_parte[1:-1]
                            if codigo_asignatura in asignaturas_matriculadas:
                                tiene_experiencia = asignaturas_matriculadas[codigo_asignatura].get('lab_aprobado',
                                                                                                    False)

                experiencia = "🎓" if tiene_experiencia else "📝"
                num_asignaturas = len(asignaturas_matriculadas)

                texto_item = f"{experiencia} {nombre_completo.strip()} [{dni}] {grupos_str} ({num_asignaturas} asig.)"
                item = QListWidgetItem(texto_item)
                item.setData(Qt.ItemDataRole.UserRole, dni)
                self.list_alumnos.addItem(item)

            # Log de contexto (añadimos info del grupo/multi)
            contexto = "global" if filtro_texto == "Todas las asignaturas" else f"para {filtro_texto}"
            extras = []
            if solo_sin_lab:
                extras.append("sin lab")
            if filtro_grupo != "Todos los grupos":
                extras.append(f"grupo={filtro_grupo}")
            if solo_multi_grupo:
                extras.append(">1 grupo")
            sufijo = f" ({', '.join(extras)})" if extras else ""
            self.log_mensaje(f"🔍 Filtro {contexto}{sufijo}: {len(alumnos_filtrados)} alumnos mostrados", "info")

        else:
            item = QListWidgetItem("🔍 Sin resultados para el filtro aplicado")
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
        info += f"📋 Exp. Centro: {datos.get('exp_centro', 'No definido')}\n"
        grupos_matriculado = datos.get('grupos_matriculado', [])
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
        asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})
        info += f"📚 ASIGNATURAS ({len(asignaturas_matriculadas)}):\n"
        if asignaturas_matriculadas:
            for asig_key, asig_info in asignaturas_matriculadas.items():
                if asig_info.get('matriculado', False):
                    # Buscar el nombre de la asignatura por su código
                    codigo_asignatura = asig_key
                    nombre_asignatura = asig_key  # Por defecto, si no se encuentra

                    # Buscar en asignaturas disponibles correctamente
                    for sem in ["1", "2"]:
                        # Codigo es la clave, nombre_real está en asig_data
                        for codigo, asig_data in self.asignaturas_disponibles.get(sem, {}).items():
                            if codigo == asig_key:  # Comparar directamente las claves
                                codigo_asignatura = codigo
                                nombre_asignatura = asig_data.get('nombre', codigo)  # NOMBRE REAL
                                break
                        if nombre_asignatura != asig_key:
                            break

                    info += f"  • {codigo_asignatura} - {nombre_asignatura}\n"
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

    def _normalize_text(self, s: str) -> str:
        if s is None:
            return ""
        s = str(s).strip()
        # Elimina acentos y pasa a MAYÚSCULAS
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return s.upper()

    def importar_alumnos_excel(self):
        """Importar alumnos desde Excel con selector de asignatura (con progreso y conteo de errores)"""
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
            obtener_ruta_descargas(),
            "Archivos Excel (*.xlsx *.xls);Excel Nuevo (*.xlsx);Excel Antiguo (*.xls);Todos los archivos (*)"
        )
        if not archivo:
            return

        try:
            # Leer Excel con pandas
            df = self._leer_excel_universal(archivo)

            # Forzar columnas del DataFrame a minúsculas para facilitar detección
            def _normalizar_cabecera(col: str) -> str:
                col = str(col).strip().lower()
                # unifica nº y n°
                col = col.replace("nº", "no").replace("n°", "no")
                # quita acentos
                col = unicodedata.normalize("NFKD", col)
                col = "".join(ch for ch in col if not unicodedata.combining(ch))
                # espacios simples
                col = " ".join(col.split())
                return col

            df.columns = [_normalizar_cabecera(col) for col in df.columns]

            # Mapeo de columnas esperadas (en minúsculas)
            columnas_mapeo = {
                'dni': ['dni', 'no exp', 'no expediente', 'no expediente en centro'],
                'apellidos': ['apellidos'],
                'nombre': ['nombre'],
                'email': ['email', 'e-mail', 'correo'],
                'grupo': ['grupo matricula', 'grupo matrícula', 'grupo', 'grupo de matricula', 'grupo de matrícula'],
                'exp_centro': ['no expediente en centro', 'exp centro', 'expediente centro', 'matricula',
                               'num expediente centro'],
                'exp_agora': ['no expediente en agora', 'exp agora', 'expediente agora', 'num expediente agora']
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

            # Obtener grupos disponibles del sistema
            grupos_disponibles = self.obtener_grupos_del_sistema()
            if not grupos_disponibles:
                QMessageBox.warning(self, "Sin Grupos",
                                    "No hay grupos configurados en el sistema.\n"
                                    "Configure primero los grupos antes de importar alumnos.")
                return

            # Contadores y colecciones
            alumnos_importados = 0
            alumnos_actualizados = 0
            errores = []
            grupos_faltantes = set()
            asignaturas_no_asociadas = set()

            # Progreso
            progress = QProgressDialog("Importando alumnos…", "Cancelar", 0, len(df), self)
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.setValue(0)

            try:
                for index, row in df.iterrows():
                    try:
                        # Extraer datos básicos
                        dni = str(row[columnas_detectadas['dni']]).strip().upper()
                        if not dni or dni == 'nan':
                            errores.append(f"Fila {index + 2}: DNI vacío o inválido")
                            # Avanzar progreso y continuar
                            progress.setValue(index + 1)
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                break
                            continue

                        apellidos = self._normalize_text(row[columnas_detectadas['apellidos']])  # MARÍA→MARIA
                        nombre = self._normalize_text(row[columnas_detectadas['nombre']])
                        if not apellidos or not nombre:
                            errores.append(f"Fila {index + 2}: Nombre o apellidos vacíos")
                            progress.setValue(index + 1)
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                break
                            continue

                        # EXTRAER CÓDIGO DE GRUPO del campo grupo (tu helper actual)
                        grupo_completo = str(row[columnas_detectadas['grupo']]).strip()
                        codigo_grupo = self._extraer_codigo_grupo(grupo_completo)
                        if not codigo_grupo:
                            errores.append(
                                f"Fila {index + 2}: No se pudo extraer código de grupo de '{grupo_completo}'")
                            progress.setValue(index + 1)
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                break
                            continue

                        # VALIDAR que el grupo existe
                        if codigo_grupo not in grupos_disponibles:
                            grupos_faltantes.add(codigo_grupo)
                            errores.append(f"Fila {index + 2}: Grupo '{codigo_grupo}' no existe en el sistema")
                            progress.setValue(index + 1)
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                break
                            continue

                        # VALIDAR que la asignatura está asociada al grupo
                        grupo_data = grupos_disponibles[codigo_grupo]
                        asignaturas_del_grupo = grupo_data.get("asignaturas_asociadas", [])
                        codigo_asignatura = asignatura_info['codigo']  # tu estructura actual
                        if codigo_asignatura not in asignaturas_del_grupo:
                            asignaturas_no_asociadas.add(
                                f"{codigo_asignatura} ({asignatura_info['nombre']}) → {codigo_grupo}")
                            errores.append(
                                f"Fila {index + 2}: Asignatura '{codigo_asignatura}' no asociada al grupo '{codigo_grupo}'")
                            progress.setValue(index + 1)
                            QApplication.processEvents()
                            if progress.wasCanceled():
                                break
                            continue

                        # Datos opcionales
                        email = ""
                        if 'email' in columnas_detectadas:
                            email = str(row[columnas_detectadas['email']]).strip().lower()
                            if email == 'nan':
                                email = ""

                        exp_centro = ""
                        if 'exp_centro' in columnas_detectadas:
                            try:
                                val = row[columnas_detectadas['exp_centro']]
                                # siempre texto; limpia “.0”
                                exp_centro = str(val).strip()
                                if exp_centro.endswith(".0"):
                                    exp_centro = exp_centro[:-2]
                            except Exception:
                                exp_centro = ""

                        exp_agora = ""
                        if 'exp_agora' in columnas_detectadas:
                            try:
                                val = row[columnas_detectadas['exp_agora']]
                                exp_agora = str(val).strip()
                                if exp_agora.endswith(".0"):
                                    exp_agora = exp_agora[:-2]
                            except Exception:
                                exp_agora = ""

                        # Preparar/actualizar alumno
                        if dni in self.datos_configuracion:
                            # ACTUALIZAR ALUMNO EXISTENTE
                            alumno_datos = self.datos_configuracion[dni]
                            cambios_realizados = False

                            # Solo rellenar si están vacíos
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

                            # AGREGAR GRUPO si no lo tiene
                            grupos_actuales = alumno_datos.get('grupos_matriculado', [])
                            if codigo_grupo not in grupos_actuales:
                                grupos_actuales.append(codigo_grupo)
                                alumno_datos['grupos_matriculado'] = grupos_actuales
                                cambios_realizados = True

                            # AGREGAR ASIGNATURA si no la tiene
                            asignaturas_actuales = alumno_datos.get('asignaturas_matriculadas', {})
                            asig_key = asignatura_info['key']
                            if asig_key not in asignaturas_actuales:
                                asignaturas_actuales[asig_key] = {"matriculado": True,
                                                                  "lab_aprobado": False,
                                                                  "grupo": codigo_grupo}
                                alumno_datos['asignaturas_matriculadas'] = asignaturas_actuales
                                cambios_realizados = True

                            if cambios_realizados:
                                alumnos_actualizados += 1
                        else:
                            # NUEVO ALUMNO
                            self.datos_configuracion[dni] = {
                                'dni': dni,
                                'nombre': nombre,
                                'apellidos': apellidos,
                                'email': email,
                                'grupos_matriculado': [codigo_grupo],
                                'asignaturas_matriculadas': {
                                    asignatura_info['key']: {"matriculado": True,
                                                             "lab_aprobado": False,
                                                             "grupo": codigo_grupo}
                                },
                                'exp_centro': exp_centro,
                                'exp_agora': exp_agora,
                                'observaciones': f"Importado desde Excel - {asignatura_info['nombre']} - Grupo {codigo_grupo}",
                                'fecha_creacion': datetime.now().isoformat()
                            }
                            alumnos_importados += 1

                    except Exception as e:
                        errores.append(f"Fila {index + 2}: {str(e)}")

                    # Avanzar progreso una sola vez por fila (sin cerrar cada vuelta)
                    progress.setValue(index + 1)
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        break
            finally:
                # Cerrar la barra UNA sola vez al acabar
                progress.close()

            # Post-proceso: ordenar, refrescar UI
            self.ordenar_alumnos_alfabeticamente()
            self.aplicar_filtro_asignatura()
            self.marcar_cambio_realizado()

            # Mensaje final detallado (siempre muestra errores, aunque sean 0)
            mensaje = (f"✅ Importación completada para {asignatura_info['nombre']}:\n\n"
                       f"• {alumnos_importados} alumnos nuevos\n"
                       f"• {alumnos_actualizados} alumnos actualizados\n"
                       f"• {len(errores)} errores\n\n")

            if grupos_faltantes:
                mensaje += "⚠️ GRUPOS FALTANTES:\n" + "\n".join(f"  • {g}" for g in sorted(grupos_faltantes)) + \
                           "\n→ Crear en: Configurar Grupos\n\n"
            if asignaturas_no_asociadas:
                mensaje += "⚠️ ASIGNATURAS NO ASOCIADAS:\n" + \
                           "\n".join(f"  • {asoc}" for asoc in sorted(asignaturas_no_asociadas)) + \
                           "\n→ Editar en: Configurar Asignaturas o Configurar Grupos\n\n"

            if errores:
                # Mostrar hasta 5 errores
                if len(errores) <= 5:
                    mensaje += "Errores:\n" + "\n".join(errores[:5])
                else:
                    mensaje += "Primeros errores:\n" + "\n".join(errores[:3]) + f"\n… y {len(errores) - 3} más"

            QMessageBox.information(self, "Importación Completada", mensaje)

            self.log_mensaje(
                f"📥 Importados {alumnos_importados} nuevos, {alumnos_actualizados} actualizados para {asignatura_info['nombre']}",
                "success"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación",
                                 f"Error al procesar archivo Excel:\n{str(e)}")
            self.log_mensaje(f"❌ Error importando alumnos: {e}", "error")

    def importar_alumnos_aprobados(self):
        """Importar alumnos aprobados desde Excel para marcar 'lab_aprobado' (con doble progreso)"""
        # Verificar datos previos
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
            obtener_ruta_descargas(), "Archivos Excel (*.xlsx *.xls);Todos los archivos (*)"
        )
        if not archivo:
            return

        try:
            # Leer Excel
            df = self._leer_excel_universal(archivo)

            # Normalizar cabeceras
            def _normalizar_cabecera(col: str) -> str:
                col = str(col).strip().lower()
                col = col.replace("nº", "no").replace("n°", "no")
                col = unicodedata.normalize("NFKD", col)
                col = "".join(ch for ch in col if not unicodedata.combining(ch))
                col = " ".join(col.split())
                return col

            df.columns = [_normalizar_cabecera(c) for c in df.columns]

            # Aceptar más variantes de la columna identificadora (DNI/Expediente)
            posibles_columnas = [
                'dni', 'no exp', 'no expediente', 'no expediente en centro', 'expediente',
                'exp centro', 'expediente centro', 'num expediente centro', 'exp'
            ]
            columna_id = next((c for c in posibles_columnas if c in df.columns), None)

            for col_name in posibles_columnas:
                if col_name in df.columns:
                    columna_id = col_name
                    break

            if not columna_id:
                QMessageBox.warning(self, "Columna no encontrada",
                                    f"No se encontró columna de DNI o Expediente Centro.\n\n"
                                    f"Columnas disponibles: {', '.join(df.columns)}")
                return

            # --- FASE 1: Lectura de identificadores con progreso ---
            identificadores = []
            errores_lectura = []

            progress1 = QProgressDialog("Leyendo Excel…", "Cancelar", 0, len(df), self)
            progress1.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress1.setMinimumDuration(0)
            progress1.setAutoClose(True)
            progress1.setAutoReset(True)
            progress1.setValue(0)

            try:
                for index, row in df.iterrows():
                    try:
                        identificador = str(row[columna_id]).strip().upper()
                        if identificador and identificador != 'nan':
                            identificadores.append(identificador)
                        else:
                            errores_lectura.append(f"Fila {index + 2}: Identificador vacío/NaN")
                    except Exception as e:
                        errores_lectura.append(f"Fila {index + 2}: {str(e)}")

                    progress1.setValue(index + 1)
                    QApplication.processEvents()
                    if progress1.wasCanceled():
                        break
            finally:
                progress1.close()

            if not identificadores:
                QMessageBox.warning(self, "Sin Datos", "No se encontraron identificadores válidos en el archivo")
                return

            # --- FASE 2: Marcado de aprobados con progreso ---
            alumnos_marcados = 0
            alumnos_no_encontrados = []
            alumnos_sin_asignatura = []
            errores_marcado = []

            progress2 = QProgressDialog("Marcando aprobados…", "Cancelar", 0, len(identificadores), self)
            progress2.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress2.setMinimumDuration(0)
            progress2.setAutoClose(True)
            progress2.setAutoReset(True)
            progress2.setValue(0)

            try:
                for j, identificador in enumerate(identificadores):
                    try:
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
                            progress2.setValue(j + 1)
                            QApplication.processEvents()
                            if progress2.wasCanceled():
                                break
                            continue

                        # Verificar si está matriculado en la asignatura
                        asignaturas_matriculadas = alumno_encontrado.get('asignaturas_matriculadas', {})
                        asig_key = asignatura_info['key']  # en tu modelo actual la key es el código
                        if asig_key not in asignaturas_matriculadas:
                            nombre_completo = f"{alumno_encontrado.get('apellidos', '')} {alumno_encontrado.get('nombre', '')}"
                            alumnos_sin_asignatura.append(f"{nombre_completo.strip()} ({dni_encontrado})")
                            progress2.setValue(j + 1)
                            QApplication.processEvents()
                            if progress2.wasCanceled():
                                break
                            continue

                        # Marcar como aprobado si no lo está ya
                        if not asignaturas_matriculadas[asig_key].get('lab_aprobado', False):
                            asignaturas_matriculadas[asig_key]['lab_aprobado'] = True
                            alumnos_marcados += 1

                            # Añadir rastro en observaciones con timestamp
                            observaciones_actuales = alumno_encontrado.get('observaciones', '')
                            fecha_aprobacion = datetime.now().strftime("%Y-%m-%d %H:%M")
                            nuevo_registro = f"[{fecha_aprobacion}] Lab aprobado en {asignatura_info['nombre']}"
                            alumno_encontrado['observaciones'] = (
                                        observaciones_actuales + "\n" + nuevo_registro).strip()

                    except Exception as e:
                        errores_marcado.append(f"ID {identificador}: {str(e)}")

                    progress2.setValue(j + 1)
                    QApplication.processEvents()
                    if progress2.wasCanceled():
                        break
            finally:
                progress2.close()

            # Refrescar UI
            self.aplicar_filtro_asignatura()
            self.marcar_cambio_realizado()

            # Resumen final
            mensaje = (f"✅ Marcado de aprobados para {asignatura_info['nombre']}:\n\n"
                       f"• {alumnos_marcados} alumnos marcados como 'lab_aprobado'\n"
                       f"• {len(alumnos_no_encontrados)} identificadores no encontrados\n"
                       f"• {len(alumnos_sin_asignatura)} alumnos sin esa asignatura\n"
                       f"• {len(errores_lectura) + len(errores_marcado)} errores\n\n")

            if alumnos_no_encontrados:
                primeros = alumnos_no_encontrados[:10]
                mensaje += "No encontrados (muestra):\n" + "\n".join(f"  • {x}" for x in primeros)
                if len(alumnos_no_encontrados) > 10:
                    mensaje += f"\n… y {len(alumnos_no_encontrados) - 10} más\n\n"
                else:
                    mensaje += "\n\n"

            if alumnos_sin_asignatura:
                primeros = alumnos_sin_asignatura[:10]
                mensaje += "Sin asignatura (muestra):\n" + "\n".join(f"  • {x}" for x in primeros) + "\n\n"

            if errores_lectura or errores_marcado:
                errores = (errores_lectura[:3] + errores_marcado[:3])[:6]
                mensaje += "Errores (muestra):\n" + "\n".join(f"  • {e}" for e in errores)
                total_err = len(errores_lectura) + len(errores_marcado)
                if total_err > len(errores):
                    mensaje += f"\n… y {total_err - len(errores)} más"

            QMessageBox.information(self, "Aprobados Importados", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error en Importación de Aprobados",
                                 f"Error al procesar aprobados desde Excel:\n{str(e)}")
            self.log_mensaje(f"❌ Error importando aprobados: {e}", "error")

    def _extraer_codigo_grupo(self, grupo_completo):
        """Extraer código de grupo de 'Grupo de Matricula (A302)' → 'A302'"""
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

    def obtener_grupos_del_sistema(self):
        """Obtener grupos disponibles desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_grupos = self.parent_window.configuracion["configuracion"]["grupos"]
                if config_grupos.get("configurado") and config_grupos.get("datos"):
                    return config_grupos["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo grupos del sistema: {e}", "warning")
            return {}

    def _leer_excel_universal(self, archivo):
        """Leer archivos Excel .xlsx y .xls con manejo automático de dependencias"""
        # Detectar extensión
        _, extension = os.path.splitext(archivo.lower())

        if extension == '.xlsx':
            # Intentar leer .xlsx con openpyxl
            try:
                return pd.read_excel(archivo, engine='openpyxl')
            except ImportError:
                # Intentar instalar openpyxl automáticamente
                try:
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

    def buscar_alumno_dialog(self):
        """Mostrar diálogo para buscar alumno por DNI o nombre"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay alumnos configurados para buscar")
            return

        texto_busqueda, ok = QInputDialog.getText(
            self, "Buscar Alumno",
            "Buscar por DNI o nombre/apellidos:"
        )

        if not ok or not texto_busqueda.strip():
            return

        texto_busqueda = texto_busqueda.strip().lower()
        encontrados = []

        for dni, datos in self.datos_configuracion.items():
            # Buscar por DNI
            if texto_busqueda.upper() in dni.upper():
                encontrados.append((dni, datos))
            # Buscar por nombre completo
            elif (texto_busqueda in datos.get('nombre', '').lower() or
                  texto_busqueda in datos.get('apellidos', '').lower() or
                  texto_busqueda in f"{datos.get('apellidos', '')} {datos.get('nombre', '')}".lower()):
                encontrados.append((dni, datos))

        if not encontrados:
            QMessageBox.information(self, "Sin Resultados",
                                    f"No se encontraron alumnos que coincidan con '{texto_busqueda}'")
            return

        if len(encontrados) == 1:
            # Seleccionar directamente
            dni_encontrado = encontrados[0][0]
            self.auto_seleccionar_alumno(dni_encontrado)
            datos = encontrados[0][1]
            nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
            QMessageBox.information(self, "Alumno Encontrado",
                                    f"Alumno seleccionado: {nombre.strip()} [{dni_encontrado}]")
        else:
            # Mostrar lista de opciones
            opciones = []
            for dni, datos in encontrados:
                nombre = f"{datos.get('apellidos', '')} {datos.get('nombre', '')}"
                opciones.append(f"{nombre.strip()} [{dni}]")

            opcion, ok = QInputDialog.getItem(
                self, "Múltiples Resultados",
                f"Se encontraron {len(encontrados)} alumnos. Selecciona uno:",
                opciones, 0, False
            )

            if ok:
                # Extraer DNI de la opción seleccionada
                dni_seleccionado = opcion.split('[')[-1].rstrip(']')
                self.auto_seleccionar_alumno(dni_seleccionado)

    def actualizar_estadisticas(self):
        """Actualizar estadísticas por asignatura con desglose de grupos"""
        if not self.datos_configuracion:
            self.texto_stats.setText("📊 No hay alumnos para generar estadísticas")
            return

        # Estadísticas generales
        total_alumnos = len(self.datos_configuracion)

        # Contar alumnos con laboratorios aprobados global
        con_lab_aprobado = 0
        for datos in self.datos_configuracion.values():
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})
            tiene_aprobado = any(
                asig_info.get('lab_aprobado', False)
                for asig_info in asignaturas_matriculadas.values()
            )
            if tiene_aprobado:
                con_lab_aprobado += 1

        sin_lab_aprobado = total_alumnos - con_lab_aprobado

        # Estadísticas por asignatura (con desglose por grupo)
        stats_asignaturas = {}

        for dni, datos in self.datos_configuracion.items():
            grupos_matriculado = datos.get('grupos_matriculado', [])
            asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

            for asig_key, asig_info in asignaturas_matriculadas.items():
                if asig_info.get('matriculado', False):
                    if asig_key not in stats_asignaturas:
                        stats_asignaturas[asig_key] = {
                            'total': 0,
                            'con_lab_aprobado': 0,
                            'sin_lab_aprobado': 0,
                            'grupos_recomendados': 0,
                            'grupos': {}
                        }

                    stats_asignaturas[asig_key]['total'] += 1
                    if asig_info.get('lab_aprobado', False):
                        stats_asignaturas[asig_key]['con_lab_aprobado'] += 1
                        aprobado = True
                    else:
                        stats_asignaturas[asig_key]['sin_lab_aprobado'] += 1
                        aprobado = False

                    # Contar por grupo dentro de la asignatura
                    for grupo in grupos_matriculado:
                        if grupo not in stats_asignaturas[asig_key]['grupos']:
                            stats_asignaturas[asig_key]['grupos'][grupo] = {
                                'total': 0,
                                'con_lab_aprobado': 0,
                                'sin_lab_aprobado': 0
                            }
                        stats_asignaturas[asig_key]['grupos'][grupo]['total'] += 1
                        if aprobado:
                            stats_asignaturas[asig_key]['grupos'][grupo]['con_lab_aprobado'] += 1
                        else:
                            stats_asignaturas[asig_key]['grupos'][grupo]['sin_lab_aprobado'] += 1

        # Calcular grupos recomendados (12-14 alumnos por grupo)
        for asig_key, stats in stats_asignaturas.items():
            total = stats['total']
            grupos_recomendados = max(1, (total + 13) // 14)
            stats['grupos_recomendados'] = grupos_recomendados

        # Generar texto de estadísticas
        stats_texto = f"📈 ESTADÍSTICAS GENERALES:\n"
        stats_texto += f"Total alumnos: {total_alumnos}\n"
        stats_texto += f"Con laboratorio aprobado: {con_lab_aprobado} ({con_lab_aprobado / total_alumnos * 100:.1f}%)\n"
        stats_texto += f"Sin laboratorio aprobado: {sin_lab_aprobado} ({sin_lab_aprobado / total_alumnos * 100:.1f}%)\n\n"

        if stats_asignaturas:
            stats_texto += f"📚 POR ASIGNATURA:\n"
            for asig_key, stats in sorted(stats_asignaturas.items()):
                # Buscar nombre de asignatura por código
                codigo_asignatura = asig_key
                nombre_asignatura = asig_key
                for sem in ["1", "2"]:
                    for codigo, asig_data in self.asignaturas_disponibles.get(sem, {}).items():
                        if codigo == asig_key:
                            nombre_asignatura = asig_data.get('nombre', codigo)
                            break

                nombre_completo = f"{codigo_asignatura} - {nombre_asignatura}"
                total = stats['total']
                con_apr = stats['con_lab_aprobado']
                sin_apr = stats['sin_lab_aprobado']
                grupos = stats['grupos_recomendados']

                stats_texto += f"• {nombre_completo}: {total} alumnos\n"
                stats_texto += f"  - Con laboratorio aprobado: {con_apr}, Sin laboratorio aprobado: {sin_apr}, Grupos recomendados: {grupos}\n"

                # 👇 Desglose por grupo en esta asignatura
                if stats['grupos']:
                    stats_texto += f"  🔎 Desglose por grupos:\n"
                    for grupo, gstats in sorted(stats['grupos'].items()):
                        stats_texto += f"    · {grupo}: {gstats['total']} alumnos\n"
                        stats_texto += f"      - Con laboratorio aprobado: {gstats['con_lab_aprobado']}\n"
                        stats_texto += f"      - Sin laboratorio aprobado: {gstats['sin_lab_aprobado']}\n"

        self.texto_stats.setText(stats_texto)

        # Actualizar configuración global si es posible
        if self.parent_window:
            try:
                config_asignaturas = self.parent_window.configuracion["configuracion"]["asignaturas"]
                if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                    for asig_key, stats in stats_asignaturas.items():
                        for codigo, asig_data in config_asignaturas["datos"].items():
                            if codigo == asig_key:
                                if "estadisticas_calculadas" not in asig_data:
                                    asig_data["estadisticas_calculadas"] = {}
                                asig_data["estadisticas_calculadas"].update({
                                    'total_matriculados': stats['total'],
                                    'con_lab_aprobado': stats['con_lab_aprobado'],
                                    'sin_lab_aprobado': stats['sin_lab_aprobado'],
                                    'grupos_recomendados': stats['grupos_recomendados'],
                                    'ultima_actualizacion': datetime.now().isoformat()
                                })
                self.log_mensaje("📊 Estadísticas sincronizadas con configuración global", "success")
            except Exception as e:
                self.log_mensaje(f"⚠️ Error sincronizando estadísticas: {e}", "warning")

    def exportar_estadisticas(self):
        """Exportar estadísticas a archivo"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay alumnos para generar estadísticas")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Estadísticas",
            os.path.join(obtener_ruta_descargas(),
                         f"estadisticas_alumnos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            # Generar estadísticas actualizadas
            self.actualizar_estadisticas()
            contenido_stats = self.texto_stats.toPlainText()

            # Añadir información adicional
            contenido_completo = f"ESTADÍSTICAS DE ALUMNOS - OPTIM\n"
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
        """Cargar configuración desde archivo JSON """
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Alumnos",
            obtener_ruta_descargas(), "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # SOPORTAR NUEVA ESTRUCTURA
            if "configuracion" in datos_cargados and "alumnos" in datos_cargados["configuracion"]:
                # Estructura nueva: configuracion -> alumnos -> datos
                self.datos_configuracion = datos_cargados["configuracion"]["alumnos"].get("datos", {})
            elif "alumnos" in datos_cargados:
                # Estructura legacy: alumnos directamente
                if isinstance(datos_cargados["alumnos"], dict) and "datos" in datos_cargados["alumnos"]:
                    self.datos_configuracion = datos_cargados["alumnos"]["datos"]
                else:
                    self.datos_configuracion = datos_cargados["alumnos"]
            elif isinstance(datos_cargados, dict):
                # Formato más antiguo: diccionario directo
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
        """Guardar configuración en archivo JSON con estructura consistente"""
        if not self.datos_configuracion:
            QMessageBox.warning(self, "Sin Datos", "No hay alumnos configurados para guardar.")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Alumnos",
            os.path.join(obtener_ruta_descargas(), f"alumnos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"),
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            # ESTRUCTURA CONSISTENTE CON EL SISTEMA GLOBAL
            config_data = {
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'semestre_actual': 1  # O extraer del sistema si está disponible
                },
                'configuracion': {
                    'alumnos': {
                        'configurado': True,
                        'datos': self.datos_configuracion,
                        'total': len(self.datos_configuracion),
                        'fecha_actualizacion': datetime.now().isoformat()
                    }
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
        """Cancelar cambios restaurando estado original con estructura correcta"""
        try:
            datos_originales = json.loads(self.datos_iniciales)

            # Estructura para cancelación
            datos_para_sistema = {
                "configurado": True,
                "datos": datos_originales,
                "total": len(datos_originales),
                "fecha_actualizacion": datetime.now().isoformat(),
                "_metadata_accion": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarAlumnos",
                    "cambios_descartados": True
                }
            }

            self.configuracion_actualizada.emit(datos_para_sistema)
            self.datos_configuracion = datos_originales
            self.datos_guardados_en_sistema = False

            self.log_mensaje("🔙 Cambios cancelados y estado restaurado", "info")

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

            # codigo es la clave, nombre_real está en asig_data
            for codigo, asig_data in sorted(sem1.items()):
                nombre_real = asig_data.get("nombre", codigo)
                # MOSTRAR: "FIS1 - Física I"
                item = QListWidgetItem(f"  {codigo} - {nombre_real}")
                item.setData(Qt.ItemDataRole.UserRole, ("1", codigo, nombre_real))
                self.list_asignaturas.addItem(item)

        if sem2:
            # Separador 2º Semestre
            item_sep2 = QListWidgetItem("📋 2º SEMESTRE")
            item_sep2.setFlags(Qt.ItemFlag.NoItemFlags)
            item_sep2.setBackground(QColor(74, 158, 255, 30))
            self.list_asignaturas.addItem(item_sep2)

            # codigo es la clave, nombre_real está en asig_data
            for codigo, asig_data in sorted(sem2.items()):
                nombre_real = asig_data.get("nombre", codigo)  # NOMBRE REAL desde asig_data
                # MOSTRAR: "EANA - Electrónica Analógica"
                item = QListWidgetItem(f"  {codigo} - {nombre_real}")
                item.setData(Qt.ItemDataRole.UserRole, ("2", codigo, nombre_real))
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
            "grupos_matriculado": ["A202", "B204"],
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
            "grupos_matriculado": ["B204"],
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