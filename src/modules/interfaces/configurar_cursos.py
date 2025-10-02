#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Cursos - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión integral de cursos académicos con datos completos
2. Configuración dinámica de asignaturas asociadas por curso
3. Planificación automática de plazas y coordinación académica
4. Estadísticas automáticas sincronizadas con datos de alumnos
5. Configuración detallada de departamentos y coordinadores
6. Cálculo inteligente de ocupación y ratio estudiante/plaza
7. Validación de asignaturas contra configuración de horarios
8. Sincronización bidireccional con módulos de horarios y alumnos
9. Import/Export desde CSV con preservación de relaciones
10. Integración completa con sistema de configuración global

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QGroupBox, QFrame, QScrollArea, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
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


class GestionCursoDialog(QDialog):
    """Dialog para añadir/editar curso con configuración completa"""

    def __init__(self, curso_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        self.curso_existente = curso_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {}
        self.parent_window = parent
        self.setWindowTitle("Editar Curso" if curso_existente else "Nuevo Curso")
        self.setModal(True)

        window_width = 700
        window_height = 850
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

        if self.curso_existente:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Datos básicos del curso
        basicos_group = QGroupBox("🎓 DATOS BÁSICOS DEL CURSO")
        basicos_layout = QFormLayout()

        self.edit_codigo = QLineEdit()
        self.edit_codigo.setPlaceholderText("A102, B102, A302, EE309...")

        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Grado en Ingeniería en Tecnologías Industriales...")

        self.combo_curso_actual = QComboBox()
        self.combo_curso_actual.addItems(["1º Curso", "2º Curso", "3º Curso", "4º Curso"])

        self.edit_coordinador = QLineEdit()
        self.edit_coordinador.setPlaceholderText("Dr. García López, Dra. Martínez Ruiz...")

        self.edit_departamento = QLineEdit()
        self.edit_departamento.setPlaceholderText("Ingeniería Industrial, Ingeniería Eléctrica...")

        self.combo_horario_tipo = QComboBox()
        self.combo_horario_tipo.addItems(["Mañana", "Tarde"])

        self.check_activo = QCheckBox("Curso activo")
        self.check_activo.setChecked(True)

        basicos_layout.addRow("🏷️ Código:", self.edit_codigo)
        basicos_layout.addRow("📚 Nombre:", self.edit_nombre)
        basicos_layout.addRow("🎯 Curso Actual:", self.combo_curso_actual)
        basicos_layout.addRow("👨‍🏫 Coordinador:", self.edit_coordinador)
        basicos_layout.addRow("🏢 Departamento:", self.edit_departamento)
        basicos_layout.addRow("🕐 Horario:", self.combo_horario_tipo)
        basicos_layout.addRow("✅ Estado:", self.check_activo)

        basicos_group.setLayout(basicos_layout)
        layout.addWidget(basicos_group)

        # Configuración académica
        academica_group = QGroupBox("📊 CONFIGURACIÓN ACADÉMICA")
        academica_layout = QFormLayout()

        # Créditos totales
        creditos_layout = QHBoxLayout()
        self.spin_creditos_totales = QSpinBox()
        self.spin_creditos_totales.setRange(60, 480)
        self.spin_creditos_totales.setValue(240)
        self.spin_creditos_totales.setSuffix(" ECTS")
        creditos_layout.addWidget(self.spin_creditos_totales)
        creditos_layout.addWidget(QLabel("créditos totales del curso"))
        creditos_layout.addStretch()

        # Plazas disponibles
        plazas_layout = QHBoxLayout()
        self.spin_plazas = QSpinBox()
        self.spin_plazas.setRange(1, 300)
        self.spin_plazas.setValue(120)
        self.spin_plazas.setSuffix(" plazas")
        plazas_layout.addWidget(self.spin_plazas)
        plazas_layout.addWidget(QLabel("plazas disponibles"))
        plazas_layout.addStretch()

        # Estudiantes matriculados
        matriculados_layout = QHBoxLayout()
        self.spin_estudiantes_matriculados = QSpinBox()
        self.spin_estudiantes_matriculados.setRange(0, 300)
        self.spin_estudiantes_matriculados.setValue(95)
        self.spin_estudiantes_matriculados.setSuffix(" estudiantes")
        matriculados_layout.addWidget(self.spin_estudiantes_matriculados)
        matriculados_layout.addWidget(QLabel("estudiantes matriculados"))
        matriculados_layout.addStretch()

        academica_layout.addRow("📋 Créditos:", creditos_layout)
        academica_layout.addRow("🪑 Plazas:", plazas_layout)
        academica_layout.addRow("👥 Matriculados:", matriculados_layout)

        academica_group.setLayout(academica_layout)
        layout.addWidget(academica_group)

        # Gestión dinámica de asignaturas asociadas
        asignaturas_group = QGroupBox("📚 ASIGNATURAS ASOCIADAS")
        asignaturas_layout = QVBoxLayout()

        # Header con botones de gestión
        asignaturas_header = QHBoxLayout()
        asignaturas_header.addWidget(QLabel("Asignaturas:"))
        asignaturas_header.addStretch()

        btn_add_asignatura = QPushButton("➕")
        btn_add_asignatura.setMinimumSize(30, 25)
        btn_add_asignatura.setMaximumSize(40, 40)
        btn_add_asignatura.setStyleSheet(self.get_button_style("#4CAF50"))
        btn_add_asignatura.setToolTip("Añadir nueva asignatura")
        btn_add_asignatura.clicked.connect(self.anadir_asignatura)
        asignaturas_header.addWidget(btn_add_asignatura)

        btn_edit_asignatura = QPushButton("✏️")
        btn_edit_asignatura.setMinimumSize(30, 25)
        btn_edit_asignatura.setMaximumSize(40, 40)
        btn_edit_asignatura.setStyleSheet(self.get_button_style("#2196F3"))
        btn_edit_asignatura.setToolTip("Editar asignatura seleccionada")
        btn_edit_asignatura.clicked.connect(self.editar_asignatura_seleccionada)
        asignaturas_header.addWidget(btn_edit_asignatura)

        btn_delete_asignatura = QPushButton("🗑️")
        btn_delete_asignatura.setMinimumSize(30, 25)
        btn_delete_asignatura.setMaximumSize(40, 40)
        btn_delete_asignatura.setStyleSheet(self.get_button_style("#f44336"))
        btn_delete_asignatura.setToolTip("Eliminar asignatura seleccionada")
        btn_delete_asignatura.clicked.connect(self.eliminar_asignatura_seleccionada)
        asignaturas_header.addWidget(btn_delete_asignatura)

        asignaturas_layout.addLayout(asignaturas_header)

        # Lista dinámica de asignaturas
        self.list_asignaturas_dialog = QListWidget()
        self.list_asignaturas_dialog.setMaximumHeight(120)
        asignaturas_layout.addWidget(self.list_asignaturas_dialog)

        info_asignaturas = QLabel("💡 Tip: Gestiona las asignaturas dinámicamente con los botones de arriba")
        info_asignaturas.setStyleSheet("color: #cccccc; font-size: 10px; font-style: italic;")
        asignaturas_layout.addWidget(info_asignaturas)

        asignaturas_group.setLayout(asignaturas_layout)
        layout.addWidget(asignaturas_group)

        # Observaciones
        observaciones_group = QGroupBox("📝 OBSERVACIONES")
        observaciones_layout = QVBoxLayout()

        self.edit_observaciones = QTextEdit()
        self.edit_observaciones.setPlaceholderText("Observaciones adicionales del curso...")
        self.edit_observaciones.setMaximumHeight(80)
        observaciones_layout.addWidget(self.edit_observaciones)

        observaciones_group.setLayout(observaciones_layout)
        layout.addWidget(observaciones_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def cargar_datos_existentes(self):
        """Cargar datos del curso existente"""
        if not self.curso_existente:
            return

        datos = self.curso_existente
        self.edit_codigo.setText(datos.get('codigo', ''))
        self.edit_nombre.setText(datos.get('nombre', ''))

        # Curso actual
        curso_actual = datos.get('curso_actual', '1º Curso')
        index = self.combo_curso_actual.findText(curso_actual)
        if index >= 0:
            self.combo_curso_actual.setCurrentIndex(index)

        self.edit_coordinador.setText(datos.get('coordinador', ''))
        self.edit_departamento.setText(datos.get('departamento', ''))

        # Horario tipo
        horario_tipo = datos.get('horario_tipo', 'Mañana')
        index = self.combo_horario_tipo.findText(horario_tipo)
        if index >= 0:
            self.combo_horario_tipo.setCurrentIndex(index)

        self.check_activo.setChecked(datos.get('activo', True))

        # Configuración académica
        self.spin_creditos_totales.setValue(datos.get('creditos_totales', 240))
        self.spin_plazas.setValue(datos.get('plazas', 120))
        self.spin_estudiantes_matriculados.setValue(datos.get('estudiantes_matriculados', 95))

        # Asignaturas asociadas (cargar en lista dinámica)
        asignaturas = datos.get('asignaturas_asociadas', [])
        self.list_asignaturas_dialog.clear()
        for asignatura in sorted(asignaturas):
            # Buscar nombre de la asignatura
            nombre_asignatura = asignatura
            if self.asignaturas_disponibles and asignatura in self.asignaturas_disponibles:
                nombre_asignatura = self.asignaturas_disponibles[asignatura].get('nombre', asignatura)

            texto_display = f"{asignatura} - {nombre_asignatura}"
            item = QListWidgetItem(texto_display)
            item.setData(Qt.ItemDataRole.UserRole, asignatura)
            self.list_asignaturas_dialog.addItem(item)

        self.edit_observaciones.setText(datos.get('observaciones', ''))

    def validar_y_aceptar(self):
        """Validar datos antes de aceptar"""
        # Validar campos obligatorios
        if not self.edit_codigo.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El código del curso es obligatorio")
            self.edit_codigo.setFocus()
            return

        if not self.edit_nombre.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre del curso es obligatorio")
            self.edit_nombre.setFocus()
            return

        if not self.edit_coordinador.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El coordinador del curso es obligatorio")
            self.edit_coordinador.setFocus()
            return

        if not self.edit_departamento.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El departamento del curso es obligatorio")
            self.edit_departamento.setFocus()
            return

        # Validar coherencia de datos
        plazas = self.spin_plazas.value()
        matriculados = self.spin_estudiantes_matriculados.value()

        if matriculados > plazas:
            respuesta = QMessageBox.question(
                self, "Advertencia",
                f"Los estudiantes matriculados ({matriculados}) superan las plazas disponibles ({plazas}).\n\n"
                f"¿Continuar guardando?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.No:
                return

        self.accept()

    def get_button_style(self, color):
        """Generar estilo para botones de acción"""
        return f"""
            QPushButton {{
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #666;
                border-radius: 4px;
                background-color: #444;
                color: {color};
                padding: 2px;
                margin: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba({self.hex_to_rgb(color)}, 0.3);
                border-color: {color};
            }}
            QPushButton:pressed {{
                background-color: rgba({self.hex_to_rgb(color)}, 0.5);
            }}
        """

    def hex_to_rgb(self, hex_color):
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

    def anadir_asignatura(self):
        """Añadir nueva asignatura al curso"""
        if not self.asignaturas_disponibles:
            QMessageBox.information(self, "Sin Asignaturas",
                                    "No hay asignaturas disponibles para asociar.\n"
                                    "Configure primero las asignaturas en el sistema.")
            return

        # Crear lista de asignaturas disponibles
        asignaturas_disponibles = []
        for codigo, datos in self.asignaturas_disponibles.items():
            nombre = datos.get('nombre', codigo)
            semestre = datos.get('semestre', 'Sin semestre')
            asignaturas_disponibles.append(f"{codigo} - {nombre} ({semestre})")

        asignatura, ok = QInputDialog.getItem(
            self, "Añadir Asignatura",
            "Seleccione una asignatura para asociar:",
            asignaturas_disponibles,
            0, False
        )

        if ok and asignatura:
            codigo_asignatura = asignatura.split(' - ')[0]

            # Verificar si ya existe
            for i in range(self.list_asignaturas_dialog.count()):
                item = self.list_asignaturas_dialog.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == codigo_asignatura:
                    QMessageBox.warning(self, "Error", "Esta asignatura ya está asociada al curso")
                    return

            # Añadir a la lista
            item = QListWidgetItem(asignatura)
            item.setData(Qt.ItemDataRole.UserRole, codigo_asignatura)
            self.list_asignaturas_dialog.addItem(item)

            # Ordenar alfabéticamente
            self.ordenar_asignaturas_lista()

            # Auto-seleccionar la asignatura añadida
            self.auto_seleccionar_asignatura_dialog(codigo_asignatura)

    def editar_asignatura_seleccionada(self):
        """Editar asignatura seleccionada"""
        item_actual = self.list_asignaturas_dialog.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para editar")
            return

        codigo_original = item_actual.data(Qt.ItemDataRole.UserRole)

        if not self.asignaturas_disponibles:
            QMessageBox.information(self, "Sin Asignaturas",
                                    "No hay asignaturas disponibles para cambiar.")
            return

        # Crear lista de asignaturas disponibles
        asignaturas_disponibles = []
        for codigo, datos in self.asignaturas_disponibles.items():
            nombre = datos.get('nombre', codigo)
            semestre = datos.get('semestre', 'Sin semestre')
            asignaturas_disponibles.append(f"{codigo} - {nombre} ({semestre})")

        asignatura, ok = QInputDialog.getItem(
            self, "Editar Asignatura",
            "Seleccione la nueva asignatura:",
            asignaturas_disponibles,
            0, False
        )

        if ok and asignatura:
            codigo_nuevo = asignatura.split(' - ')[0]

            if codigo_nuevo == codigo_original:
                return

            # Verificar si ya existe
            for i in range(self.list_asignaturas_dialog.count()):
                item = self.list_asignaturas_dialog.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == codigo_nuevo:
                    QMessageBox.warning(self, "Error", "Esta asignatura ya está asociada al curso")
                    return

            # Actualizar el item
            item_actual.setText(asignatura)
            item_actual.setData(Qt.ItemDataRole.UserRole, codigo_nuevo)

            # Ordenar alfabéticamente
            self.ordenar_asignaturas_lista()

            # Auto-seleccionar la asignatura editada
            self.auto_seleccionar_asignatura_dialog(codigo_nuevo)

    def eliminar_asignatura_seleccionada(self):
        """Eliminar asignatura seleccionada"""
        item_actual = self.list_asignaturas_dialog.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para eliminar")
            return

        asignatura = item_actual.text()

        respuesta = QMessageBox.question(
            self, "Eliminar Asignatura",
            f"¿Está seguro de eliminar la asignatura '{asignatura}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            row = self.list_asignaturas_dialog.row(item_actual)
            self.list_asignaturas_dialog.takeItem(row)

    def ordenar_asignaturas_lista(self):
        """Ordenar asignaturas alfabéticamente en la lista"""
        asignaturas = []
        for i in range(self.list_asignaturas_dialog.count()):
            item = self.list_asignaturas_dialog.item(i)
            asignaturas.append((item.text(), item.data(Qt.ItemDataRole.UserRole)))

        # Limpiar y recargar ordenado
        self.list_asignaturas_dialog.clear()
        for texto, codigo in sorted(asignaturas):
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_asignaturas_dialog.addItem(item)

    def get_asignaturas_seleccionadas(self):
        """Obtener lista de asignaturas de la lista dinámica"""
        asignaturas = []
        for i in range(self.list_asignaturas_dialog.count()):
            item = self.list_asignaturas_dialog.item(i)
            asignaturas.append(item.data(Qt.ItemDataRole.UserRole))
        return sorted(asignaturas)

    def auto_seleccionar_asignatura_dialog(self, codigo):
        """Auto-seleccionar asignatura en el dialog"""
        for i in range(self.list_asignaturas_dialog.count()):
            item = self.list_asignaturas_dialog.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == codigo:
                self.list_asignaturas_dialog.setCurrentItem(item)
                break

    def get_datos_curso(self):
        """Obtener datos configurados"""
        return {
            'codigo': self.edit_codigo.text().strip().upper(),
            'nombre': self.edit_nombre.text().strip(),
            'curso_actual': self.combo_curso_actual.currentText(),
            'coordinador': self.edit_coordinador.text().strip(),
            'departamento': self.edit_departamento.text().strip(),
            'creditos_totales': self.spin_creditos_totales.value(),
            'plazas': self.spin_plazas.value(),
            'estudiantes_matriculados': self.spin_estudiantes_matriculados.value(),
            'horario_tipo': self.combo_horario_tipo.currentText(),
            'observaciones': self.edit_observaciones.toPlainText().strip(),
            'fecha_creacion': datetime.now().isoformat(),
            'activo': self.check_activo.isChecked(),
            'asignaturas_asociadas': self.get_asignaturas_seleccionadas()
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
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
        """)


class ConfigurarCursos(QMainWindow):
    """Ventana principal para configurar cursos del sistema"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Cursos - OPTIM Labs")
        window_width = 1400
        window_height = 750
        center_window_on_screen_immediate(self, window_width, window_height)

        # Obtener datos relacionados desde el sistema global
        self.asignaturas_disponibles = self.obtener_asignaturas_del_sistema()
        self.alumnos_disponibles = self.obtener_alumnos_del_sistema()
        self.horarios_disponibles = self.obtener_horarios_del_sistema()

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("📥 Cargando configuración existente de cursos...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("📝 Iniciando configuración nueva de cursos...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.curso_actual = None

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    def obtener_asignaturas_del_sistema(self):
        """Obtener asignaturas configuradas desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
                if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                    return config_asignaturas["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo asignaturas del sistema: {e}", "warning")
            return {}

    def obtener_alumnos_del_sistema(self):
        """Obtener alumnos configurados desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_alumnos = self.parent_window.configuracion["configuracion"].get("alumnos", {})
                if config_alumnos.get("configurado") and config_alumnos.get("datos"):
                    return config_alumnos["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo alumnos del sistema: {e}", "warning")
            return {}

    def obtener_horarios_del_sistema(self):
        """Obtener horarios configurados desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_horarios = self.parent_window.configuracion["configuracion"].get("horarios", {})
                if config_horarios.get("configurado") and config_horarios.get("datos"):
                    return config_horarios["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo horarios del sistema: {e}", "warning")
            return {}

    def cargar_datos_iniciales(self):
        """Cargar datos existentes al inicializar"""
        try:
            # Ordenar cursos alfabéticamente
            self.ordenar_cursos_alfabeticamente()

            # Cargar lista
            self.cargar_lista_cursos()

            # Mostrar resumen
            total_cursos = len(self.datos_configuracion)

            if total_cursos > 0:
                self.log_mensaje(
                    f"✅ Datos cargados: {total_cursos} cursos configurados",
                    "success"
                )
                self.auto_seleccionar_primer_curso()
            else:
                self.log_mensaje("📝 No hay cursos configurados - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primer_curso(self):
        """Auto-seleccionar primer curso disponible"""
        try:
            if self.list_cursos.count() > 0:
                primer_item = self.list_cursos.item(0)
                self.list_cursos.setCurrentItem(primer_item)
                self.seleccionar_curso(primer_item)
                self.log_mensaje(f"🎯 Auto-seleccionado: {primer_item.text()}", "info")
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando curso: {e}", "warning")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("🎓 CONFIGURACIÓN DE CURSOS")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información del flujo
        info_label = QLabel(
            "ℹ️ Define los cursos académicos, coordinadores y asignaturas asociadas. Las estadísticas se actualizan desde los alumnos matriculados.")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de cursos
        left_panel = QGroupBox("📋 CURSOS CONFIGURADOS")
        left_layout = QVBoxLayout()

        # Header con botones de gestión
        cursos_header = QHBoxLayout()
        cursos_header.addWidget(QLabel("Cursos:"))
        cursos_header.addStretch()

        btn_add_curso = self.crear_boton_accion("➕", "#4CAF50", "Añadir nuevo curso")
        btn_add_curso.clicked.connect(self.anadir_curso)

        btn_edit_curso = self.crear_boton_accion("✏️", "#2196F3", "Editar curso seleccionado")
        btn_edit_curso.clicked.connect(self.editar_curso_seleccionado)

        btn_delete_curso = self.crear_boton_accion("🗑️", "#f44336", "Eliminar curso seleccionado")
        btn_delete_curso.clicked.connect(self.eliminar_curso_seleccionado)

        cursos_header.addWidget(btn_add_curso)
        cursos_header.addWidget(btn_edit_curso)
        cursos_header.addWidget(btn_delete_curso)

        left_layout.addLayout(cursos_header)

        # Lista de cursos
        self.list_cursos = QListWidget()
        self.list_cursos.setMaximumWidth(400)
        self.list_cursos.setMinimumHeight(400)
        left_layout.addWidget(self.list_cursos)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Detalles del curso
        center_panel = QGroupBox("🔍 DETALLES DEL CURSO")
        center_layout = QVBoxLayout()
        center_layout.setSpacing(8)

        # Nombre del curso seleccionado
        self.label_curso_actual = QLabel("Seleccione un curso")
        self.label_curso_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_curso_actual)

        # Información detallada
        self.info_curso = QTextEdit()
        self.info_curso.setMaximumHeight(300)
        self.info_curso.setReadOnly(True)
        self.info_curso.setText("ℹ️ Seleccione un curso para ver sus detalles")
        center_layout.addWidget(self.info_curso)

        # Estadísticas automáticas
        stats_group = QGroupBox("📊 ESTADÍSTICAS AUTOMÁTICAS")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)

        botones_stats_layout = QHBoxLayout()
        self.btn_actualizar_desde_alumnos = QPushButton("🔄 Actualizar desde Alumnos")
        self.btn_actualizar_desde_alumnos.clicked.connect(self.actualizar_estadisticas_desde_alumnos)
        botones_stats_layout.addWidget(self.btn_actualizar_desde_alumnos)

        self.btn_calcular_ocupacion = QPushButton("📈 Calcular Ocupación")
        self.btn_calcular_ocupacion.clicked.connect(self.calcular_ocupacion_cursos)
        botones_stats_layout.addWidget(self.btn_calcular_ocupacion)

        stats_layout.addLayout(botones_stats_layout)

        self.texto_stats = QTextEdit()
        self.texto_stats.setMaximumHeight(150)
        self.texto_stats.setReadOnly(True)
        self.texto_stats.setText("📈 Presiona 'Actualizar desde Alumnos' para ver estadísticas")
        stats_layout.addWidget(self.texto_stats)

        stats_group.setLayout(stats_layout)
        center_layout.addWidget(stats_group)

        center_panel.setLayout(center_layout)
        content_layout.addWidget(center_panel)

        # Columna derecha - Acciones y configuración
        right_panel = QGroupBox("⚙️ GESTIÓN Y CONFIGURACIÓN")
        right_layout = QVBoxLayout()

        # Acciones rápidas
        acciones_group = QGroupBox("🚀 ACCIONES RÁPIDAS")
        acciones_layout = QVBoxLayout()

        self.btn_duplicar = QPushButton("📋 Duplicar Curso")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_curso_seleccionado)
        acciones_layout.addWidget(self.btn_duplicar)

        self.btn_validar_asignaturas = QPushButton("🔍 Validar Asignaturas")
        self.btn_validar_asignaturas.setEnabled(False)
        self.btn_validar_asignaturas.clicked.connect(self.validar_asignaturas_curso)
        acciones_layout.addWidget(self.btn_validar_asignaturas)

        self.btn_sincronizar_horarios = QPushButton("📅 Sincronizar con Horarios")
        self.btn_sincronizar_horarios.clicked.connect(self.sincronizar_con_horarios)
        acciones_layout.addWidget(self.btn_sincronizar_horarios)

        self.btn_importar_desde_horarios = QPushButton("⬅️ Importar desde Horarios")
        self.btn_importar_desde_horarios.clicked.connect(self.importar_desde_horarios)
        acciones_layout.addWidget(self.btn_importar_desde_horarios)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Import
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

        # Export
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

        # Botones principales
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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todos_cursos)
        botones_layout.addWidget(self.btn_limpiar_todo)

        botones_principales_group.setLayout(botones_layout)
        right_layout.addWidget(botones_principales_group)

        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

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
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

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
        """)

    def conectar_signals(self):
        """Conectar señales de la interfaz"""
        self.list_cursos.itemClicked.connect(self.seleccionar_curso)

    def cargar_lista_cursos(self):
        """Cargar cursos en la lista visual"""
        self.list_cursos.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay cursos configurados")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_cursos.addItem(item)
            return

        # Ordenar cursos por código
        cursos_ordenados = sorted(self.datos_configuracion.items())

        for codigo, datos in cursos_ordenados:
            nombre = datos.get('nombre', 'Sin nombre')
            curso_actual = datos.get('curso_actual', 'Sin curso')
            coordinador = datos.get('coordinador', 'Sin coordinador')

            # Mostrar estado activo
            activo = datos.get('activo', True)
            estado_icono = "✅" if activo else "❌"

            # Estadísticas
            plazas = datos.get('plazas', 0)
            matriculados = datos.get('estudiantes_matriculados', 0)
            asignaturas = datos.get('asignaturas_asociadas', [])

            texto_item = f"{estado_icono} {codigo} - {nombre}"
            texto_item += f"\n    {curso_actual} | {coordinador}"
            texto_item += f"\n    {matriculados}/{plazas} estudiantes | {len(asignaturas)} asignaturas"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_cursos.addItem(item)

    def seleccionar_curso(self, item):
        """Seleccionar curso y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.curso_actual = None
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_asignaturas.setEnabled(False)
            return

        codigo = item.data(Qt.ItemDataRole.UserRole)
        if not codigo or codigo not in self.datos_configuracion:
            return

        self.curso_actual = codigo
        datos = self.datos_configuracion[codigo]

        # Actualizar etiqueta
        nombre = datos.get('nombre', 'Sin nombre')
        self.label_curso_actual.setText(f"🎓 {codigo} - {nombre}")

        # Mostrar información detallada
        info = f"🎓 CURSO: {codigo} - {nombre}\n\n"
        info += f"📚 Curso Actual: {datos.get('curso_actual', 'No definido')}\n"
        info += f"👨‍🏫 Coordinador: {datos.get('coordinador', 'No definido')}\n"
        info += f"🏢 Departamento: {datos.get('departamento', 'No definido')}\n"
        info += f"🕐 Horario: {datos.get('horario_tipo', 'No definido')}\n"
        info += f"✅ Estado: {'Activo' if datos.get('activo', True) else 'Inactivo'}\n\n"

        # Configuración académica
        info += f"📊 CONFIGURACIÓN ACADÉMICA:\n"
        info += f"• Créditos totales: {datos.get('creditos_totales', 'No definido')} ECTS\n"
        info += f"• Plazas disponibles: {datos.get('plazas', 'No definido')}\n"
        info += f"• Estudiantes matriculados: {datos.get('estudiantes_matriculados', 'No definido')}\n"

        # Calcular ocupación
        plazas = datos.get('plazas', 0)
        matriculados = datos.get('estudiantes_matriculados', 0)
        if plazas > 0:
            ocupacion = (matriculados / plazas) * 100
            info += f"• Ocupación: {ocupacion:.1f}%\n"
        info += "\n"

        # Asignaturas asociadas
        asignaturas = datos.get('asignaturas_asociadas', [])
        if asignaturas:
            info += f"📚 ASIGNATURAS ASOCIADAS ({len(asignaturas)}):\n"
            for asignatura in asignaturas:
                # Buscar nombre de la asignatura
                nombre_asignatura = asignatura
                if asignatura in self.asignaturas_disponibles:
                    nombre_asignatura = self.asignaturas_disponibles[asignatura].get('nombre', asignatura)
                info += f"  • {asignatura} - {nombre_asignatura}\n"
        else:
            info += f"📚 ASIGNATURAS: Sin asignaturas asociadas\n"
        info += "\n"

        # Observaciones
        observaciones = datos.get('observaciones', '')
        if observaciones:
            info += f"📝 OBSERVACIONES:\n{observaciones}\n\n"

        # Fechas
        fecha_creacion = datos.get('fecha_creacion', '')
        if fecha_creacion:
            try:
                fecha = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
                info += f"📅 Creado: {fecha}"
            except:
                info += f"📅 Creado: {fecha_creacion}"

        self.info_curso.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)
        self.btn_validar_asignaturas.setEnabled(True)

    def sincronizar_con_asignaturas(self, curso_codigo, asignaturas_nuevas, asignaturas_eliminadas):
        """Sincronizar cambios con módulo de asignaturas"""
        try:
            if not self.parent_window:
                return

            # Obtener configuración actual de asignaturas
            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if not config_asignaturas.get("configurado") or not config_asignaturas.get("datos"):
                return

            datos_asignaturas = config_asignaturas["datos"]
            cambios_realizados = False

            # AÑADIR curso a asignaturas nuevas
            for asignatura_codigo in asignaturas_nuevas:
                if asignatura_codigo in datos_asignaturas:
                    cursos_actuales = datos_asignaturas[asignatura_codigo].get("cursos_que_cursan", [])
                    if curso_codigo not in cursos_actuales:
                        cursos_actuales.append(curso_codigo)
                        datos_asignaturas[asignatura_codigo]["cursos_que_cursan"] = sorted(cursos_actuales)
                        cambios_realizados = True

            # ELIMINAR curso de asignaturas eliminadas
            for asignatura_codigo in asignaturas_eliminadas:
                if asignatura_codigo in datos_asignaturas:
                    cursos_actuales = datos_asignaturas[asignatura_codigo].get("cursos_que_cursan", [])
                    if curso_codigo in cursos_actuales:
                        cursos_actuales.remove(curso_codigo)
                        datos_asignaturas[asignatura_codigo]["cursos_que_cursan"] = sorted(cursos_actuales)
                        cambios_realizados = True

            # Actualizar configuración si hubo cambios
            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["asignaturas"]["datos"] = datos_asignaturas
                self.parent_window.configuracion["configuracion"]["asignaturas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"🔄 Sincronizadas asignaturas desde curso {curso_codigo}", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error sincronizando con asignaturas: {e}", "warning")

    def anadir_curso(self):
        """Añadir nuevo curso - CON SINCRONIZACIÓN"""
        dialog = GestionCursoDialog(None, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_curso()
            codigo = datos['codigo']

            if codigo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un curso con el código '{codigo}'")
                return

            # Añadir nuevo curso
            self.datos_configuracion[codigo] = datos

            # SINCRONIZACIÓN: Notificar asignaturas añadidas
            asignaturas_nuevas = datos.get('asignaturas_asociadas', [])
            if asignaturas_nuevas:
                self.sincronizar_con_asignaturas(codigo, asignaturas_nuevas, [])

            # Auto-ordenar
            self.ordenar_cursos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.auto_seleccionar_curso(codigo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Curso '{codigo} - {datos['nombre']}' añadido correctamente")

    def editar_curso_seleccionado(self):
        """Editar curso seleccionado - CON SINCRONIZACIÓN"""
        if not self.curso_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un curso para editar")
            return

        datos_originales = self.datos_configuracion[self.curso_actual].copy()
        dialog = GestionCursoDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_curso()
            codigo_nuevo = datos_nuevos['codigo']
            codigo_original = self.curso_actual

            # Si cambió el código, verificar que no exista
            if codigo_nuevo != codigo_original and codigo_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un curso con el código '{codigo_nuevo}'")
                return

            # SINCRONIZACIÓN: Detectar cambios en asignaturas
            asignaturas_originales = set(datos_originales.get('asignaturas_asociadas', []))
            asignaturas_nuevas = set(datos_nuevos.get('asignaturas_asociadas', []))

            asignaturas_añadidas = asignaturas_nuevas - asignaturas_originales
            asignaturas_eliminadas = asignaturas_originales - asignaturas_nuevas

            # Actualizar datos
            if codigo_nuevo != codigo_original:
                del self.datos_configuracion[codigo_original]
                self.curso_actual = codigo_nuevo

            self.datos_configuracion[codigo_nuevo] = datos_nuevos

            # SINCRONIZACIÓN: Aplicar cambios
            if asignaturas_añadidas or asignaturas_eliminadas:
                self.sincronizar_con_asignaturas(codigo_nuevo, asignaturas_añadidas, asignaturas_eliminadas)

            # Auto-ordenar
            self.ordenar_cursos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.auto_seleccionar_curso(codigo_nuevo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Curso actualizado correctamente")

    def eliminar_curso_seleccionado(self):
        """Eliminar curso seleccionado - CON SINCRONIZACIÓN"""
        if not self.curso_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un curso para eliminar")
            return

        datos = self.datos_configuracion[self.curso_actual]
        nombre = datos.get('nombre', 'Sin nombre')
        asignaturas_asociadas = datos.get('asignaturas_asociadas', [])

        mensaje = f"¿Está seguro de eliminar el curso '{self.curso_actual} - {nombre}'?\n\n"
        if asignaturas_asociadas:
            mensaje += f"ADVERTENCIA: Este curso tiene {len(asignaturas_asociadas)} asignaturas asociadas.\n"
        mensaje += "Esta acción no se puede deshacer."

        # Confirmar eliminación
        respuesta = QMessageBox.question(self, "Confirmar Eliminación",
                                         f"¿Está seguro de eliminar el curso '{self.curso_actual}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if respuesta == QMessageBox.StandardButton.Yes:
            # SINCRONIZACIÓN: Eliminar curso de todas las asignaturas
            if asignaturas_asociadas:
                self.sincronizar_con_asignaturas(self.curso_actual, [], asignaturas_asociadas)

            # Eliminar curso
            del self.datos_configuracion[self.curso_actual]
            self.curso_actual = None

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.label_curso_actual.setText("Seleccione un curso")
            self.info_curso.setText("ℹ️ Seleccione un curso para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_asignaturas.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Curso eliminado correctamente")

    def duplicar_curso_seleccionado(self):
        """Duplicar curso seleccionado"""
        if not self.curso_actual:
            return

        datos_originales = self.datos_configuracion[self.curso_actual].copy()

        # Generar código único
        codigo_base = f"{datos_originales['codigo']}_COPIA"
        contador = 1
        codigo_nuevo = codigo_base

        while codigo_nuevo in self.datos_configuracion:
            codigo_nuevo = f"{codigo_base}_{contador}"
            contador += 1

        datos_originales['codigo'] = codigo_nuevo
        datos_originales['nombre'] = f"{datos_originales['nombre']} (Copia)"
        datos_originales['estudiantes_matriculados'] = 0  # Resetear matriculados
        datos_originales['fecha_creacion'] = datetime.now().isoformat()

        dialog = GestionCursoDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_curso()
            codigo_final = datos_nuevos['codigo']

            if codigo_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un curso con el código '{codigo_final}'")
                return

            # Añadir curso duplicado
            self.datos_configuracion[codigo_final] = datos_nuevos

            # Auto-ordenar
            self.ordenar_cursos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.auto_seleccionar_curso(codigo_final)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Curso duplicado como '{codigo_final}'")

    def actualizar_estadisticas_desde_alumnos(self):
        """Actualizar estadísticas desde datos de alumnos matriculados"""
        try:
            if not self.alumnos_disponibles:
                self.texto_stats.setText("⚠️ No hay datos de alumnos disponibles")
                return

            # Agrupar alumnos por curso
            estadisticas_por_curso = {}

            for dni, datos_alumno in self.alumnos_disponibles.items():
                grupo = datos_alumno.get('grupo', '')
                if not grupo:
                    continue

                # Extraer códigos de curso del grupo (ej: "A102, A104" -> ["A102", "A104"])
                codigos_curso = [g.strip() for g in grupo.split(',') if g.strip()]

                for codigo_curso in codigos_curso:
                    if codigo_curso not in estadisticas_por_curso:
                        estadisticas_por_curso[codigo_curso] = {
                            'estudiantes_reales': 0,
                            'asignaturas_matriculadas': set()
                        }

                    estadisticas_por_curso[codigo_curso]['estudiantes_reales'] += 1

                    # Recopilar asignaturas
                    asignaturas_matriculadas = datos_alumno.get('asignaturas_matriculadas', {})
                    for asignatura in asignaturas_matriculadas.keys():
                        estadisticas_por_curso[codigo_curso]['asignaturas_matriculadas'].add(asignatura)

            # Actualizar estadísticas en cursos configurados
            cursos_actualizados = 0
            for codigo, datos_curso in self.datos_configuracion.items():
                if codigo in estadisticas_por_curso:
                    stats = estadisticas_por_curso[codigo]

                    # Actualizar estudiantes matriculados
                    self.datos_configuracion[codigo]['estudiantes_matriculados'] = stats['estudiantes_reales']
                    cursos_actualizados += 1

            # Mostrar resumen de la actualización
            stats_text = f"🔄 ACTUALIZACIÓN COMPLETADA:\n\n"
            stats_text += f"• {cursos_actualizados} cursos actualizados\n"
            stats_text += f"• {len(self.alumnos_disponibles)} alumnos procesados\n\n"

            # Mostrar estadísticas por curso
            for codigo, datos in self.datos_configuracion.items():
                matriculados = datos.get('estudiantes_matriculados', 0)
                plazas = datos.get('plazas', 0)
                ocupacion = (matriculados / plazas * 100) if plazas > 0 else 0
                asignaturas = len(datos.get('asignaturas_asociadas', []))

                stats_text += f"🎓 {codigo}:\n"
                stats_text += f"  • {matriculados}/{plazas} estudiantes ({ocupacion:.1f}%)\n"
                stats_text += f"  • {asignaturas} asignaturas asociadas\n\n"

            self.texto_stats.setText(stats_text)

            # Actualizar interfaz
            self.cargar_lista_cursos()
            if self.curso_actual:
                self.auto_seleccionar_curso(self.curso_actual)

            self.marcar_cambio_realizado()
            self.log_mensaje(f"✅ Estadísticas actualizadas: {cursos_actualizados} cursos", "success")

        except Exception as e:
            self.texto_stats.setText(f"❌ Error actualizando estadísticas: {e}")
            self.log_mensaje(f"⚠️ Error actualizando estadísticas: {e}", "warning")

    def calcular_ocupacion_cursos(self):
        """Calcular ocupación para todos los cursos"""
        try:
            if not self.datos_configuracion:
                QMessageBox.information(self, "Sin Datos", "No hay cursos configurados")
                return

            stats_text = "📊 OCUPACIÓN DE CURSOS:\n\n"

            total_plazas = 0
            total_matriculados = 0
            cursos_completos = 0
            cursos_vacios = 0

            for codigo, datos in self.datos_configuracion.items():
                plazas = datos.get('plazas', 0)
                matriculados = datos.get('estudiantes_matriculados', 0)

                if plazas > 0:
                    ocupacion = (matriculados / plazas) * 100

                    if ocupacion >= 90:
                        estado = "🔴 COMPLETO"
                        cursos_completos += 1
                    elif ocupacion >= 70:
                        estado = "🟡 ALTO"
                    elif ocupacion >= 40:
                        estado = "🟢 MEDIO"
                    elif ocupacion > 0:
                        estado = "🔵 BAJO"
                    else:
                        estado = "⚪ VACÍO"
                        cursos_vacios += 1

                    stats_text += f"🎓 {codigo}: {matriculados}/{plazas} ({ocupacion:.1f}%) {estado}\n"

                    total_plazas += plazas
                    total_matriculados += matriculados
                else:
                    stats_text += f"🎓 {codigo}: Sin plazas definidas\n"

            # Resumen global
            if total_plazas > 0:
                ocupacion_global = (total_matriculados / total_plazas) * 100
                stats_text += f"\n📊 RESUMEN GLOBAL:\n"
                stats_text += f"• Total: {total_matriculados}/{total_plazas} ({ocupacion_global:.1f}%)\n"
                stats_text += f"• Cursos completos: {cursos_completos}\n"
                stats_text += f"• Cursos vacíos: {cursos_vacios}\n"

            self.texto_stats.setText(stats_text)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calculando ocupación: {e}")

    def validar_asignaturas_curso(self):
        """Validar asignaturas del curso contra configuración de horarios"""
        if not self.curso_actual:
            return

        try:
            datos_curso = self.datos_configuracion[self.curso_actual]
            asignaturas_curso = datos_curso.get('asignaturas_asociadas', [])

            if not asignaturas_curso:
                QMessageBox.information(self, "Sin Asignaturas",
                                        "Este curso no tiene asignaturas asociadas")
                return

            if not self.horarios_disponibles:
                QMessageBox.warning(self, "Sin Horarios",
                                    "No hay datos de horarios disponibles para validar")
                return

            # Buscar asignaturas en horarios
            asignaturas_en_horarios = set()
            for semestre, asignaturas_sem in self.horarios_disponibles.items():
                if isinstance(asignaturas_sem, dict):
                    for nombre_asig, datos_asig in asignaturas_sem.items():
                        cursos_asig = datos_asig.get('cursos', [])
                        if self.curso_actual in cursos_asig:
                            asignaturas_en_horarios.add(nombre_asig)

            # Mostrar resultados
            mensaje = f"🔍 VALIDACIÓN DE ASIGNATURAS\n\n"
            mensaje += f"Curso: {self.curso_actual}\n"
            mensaje += f"Asignaturas asociadas: {len(asignaturas_curso)}\n\n"

            if asignaturas_en_horarios:
                mensaje += f"✅ Asignaturas encontradas en horarios ({len(asignaturas_en_horarios)}):\n"
                for asignatura in sorted(asignaturas_en_horarios):
                    mensaje += f"  • {asignatura}\n"
            else:
                mensaje += "❌ No se encontraron asignaturas en horarios\n"

            mensaje += f"\n💡 Sugerencias:\n"
            mensaje += f"• Verificar que las asignaturas estén configuradas en horarios\n"
            mensaje += f"• Sincronizar datos entre módulos\n"
            mensaje += f"• Revisar códigos de asignaturas"

            QMessageBox.information(self, "Validación de Asignaturas", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error validando asignaturas: {e}")

    def importar_desde_horarios(self):
        """Importar cursos desde módulo de horarios"""
        try:
            if not self.horarios_disponibles:
                QMessageBox.information(self, "Sin Datos",
                                        "No hay datos de horarios disponibles para importar")
                return

            cursos_importados = 0
            cursos_encontrados = set()

            # Procesar ambos semestres
            for semestre, asignaturas_sem in self.horarios_disponibles.items():
                if isinstance(asignaturas_sem, dict):
                    for nombre_asig, datos_asig in asignaturas_sem.items():
                        cursos_asig = datos_asig.get('cursos', [])
                        for curso in cursos_asig:
                            cursos_encontrados.add(curso)

            # Crear cursos que no existan
            for codigo_curso in cursos_encontrados:
                if codigo_curso not in self.datos_configuracion:
                    # Inferir datos del curso
                    nombre_curso = f"Curso {codigo_curso}"
                    curso_actual = "1º Curso"

                    # Intentar inferir el curso basado en el código
                    if codigo_curso.endswith('02'):
                        curso_actual = "1º Curso"
                    elif codigo_curso.endswith('03'):
                        curso_actual = "2º Curso"
                    elif codigo_curso.endswith('04'):
                        curso_actual = "3º Curso"

                    self.datos_configuracion[codigo_curso] = {
                        'codigo': codigo_curso,
                        'nombre': nombre_curso,
                        'curso_actual': curso_actual,
                        'coordinador': 'Por definir',
                        'departamento': 'Por definir',
                        'creditos_totales': 240,
                        'plazas': 100,
                        'estudiantes_matriculados': 0,
                        'horario_tipo': 'Mañana',
                        'observaciones': 'Importado desde configuración de horarios',
                        'fecha_creacion': datetime.now().isoformat(),
                        'activo': True,
                        'asignaturas_asociadas': []
                    }
                    cursos_importados += 1

            if cursos_importados > 0:
                # Auto-ordenar
                self.ordenar_cursos_alfabeticamente()

                # Actualizar interfaz
                self.cargar_lista_cursos()
                self.marcar_cambio_realizado()

                QMessageBox.information(self, "Importación Exitosa",
                                        f"✅ Importados {cursos_importados} cursos desde horarios")
            else:
                QMessageBox.information(self, "Sin Importar",
                                        "No se encontraron cursos nuevos para importar")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importando desde horarios: {e}")

    def sincronizar_con_horarios(self):
        """Sincronizar datos con módulo de horarios"""
        try:
            # Preparar datos para enviar a horarios
            datos_para_horarios = {}
            for codigo, datos in self.datos_configuracion.items():
                asignaturas = datos.get('asignaturas_asociadas', [])

                datos_para_horarios[codigo] = {
                    'nombre': datos.get('nombre', codigo),
                    'asignaturas': asignaturas,
                    'coordinador': datos.get('coordinador', ''),
                    'activo': datos.get('activo', True)
                }

            # Enviar datos al sistema principal para sincronización
            if self.parent_window and hasattr(self.parent_window, 'sincronizar_cursos_horarios'):
                resultado = self.parent_window.sincronizar_cursos_horarios(datos_para_horarios)
                if resultado:
                    QMessageBox.information(self, "Sincronización",
                                            f"✅ Datos sincronizados con horarios: {len(datos_para_horarios)} cursos")
                else:
                    QMessageBox.warning(self, "Sincronización",
                                        "⚠️ Error en la sincronización con horarios")
            else:
                # Modo independiente - mostrar datos preparados
                mensaje = f"📤 Datos preparados para sincronización:\n\n"
                for codigo, datos in datos_para_horarios.items():
                    mensaje += f"• {codigo}: {datos['nombre']}, "
                    mensaje += f"{len(datos['asignaturas'])} asignaturas\n"

                QMessageBox.information(self, "Sincronización Preparada", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en sincronización: {e}")

    def importar_desde_csv(self):
        """Importar cursos desde archivo CSV"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Cursos desde CSV",
            "", "Archivos CSV (*.csv);;Todos los archivos (*)"
        )

        if not archivo:
            return

        try:
            df = pd.read_csv(archivo)

            # Verificar columnas requeridas
            columnas_requeridas = ['codigo', 'nombre', 'coordinador', 'departamento']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                QMessageBox.warning(
                    self, "Columnas Faltantes",
                    f"El archivo CSV debe contener las columnas:\n{', '.join(columnas_faltantes)}"
                )
                return

            # Importar datos
            cursos_importados = 0
            cursos_duplicados = 0

            for _, row in df.iterrows():
                codigo = str(row['codigo']).strip().upper()
                if not codigo:
                    continue

                if codigo in self.datos_configuracion:
                    cursos_duplicados += 1
                    continue

                # Procesar asignaturas asociadas
                asignaturas = []
                if 'asignaturas_asociadas' in df.columns and pd.notna(row['asignaturas_asociadas']):
                    asignaturas_text = str(row['asignaturas_asociadas']).strip()
                    if asignaturas_text:
                        asignaturas = [g.strip() for g in asignaturas_text.split(',')]

                self.datos_configuracion[codigo] = {
                    'codigo': codigo,
                    'nombre': str(row['nombre']).strip(),
                    'curso_actual': str(row.get('curso_actual', '1º Curso')).strip(),
                    'coordinador': str(row['coordinador']).strip(),
                    'departamento': str(row['departamento']).strip(),
                    'creditos_totales': int(row.get('creditos_totales', 240)) if pd.notna(
                        row.get('creditos_totales')) else 240,
                    'plazas': int(row.get('plazas', 100)) if pd.notna(row.get('plazas')) else 100,
                    'estudiantes_matriculados': int(row.get('estudiantes_matriculados', 0)) if pd.notna(
                        row.get('estudiantes_matriculados')) else 0,
                    'horario_tipo': str(row.get('horario_tipo', 'Mañana')).strip(),
                    'observaciones': str(row.get('observaciones', '')).strip(),
                    'fecha_creacion': datetime.now().isoformat(),
                    'activo': bool(row.get('activo', True)) if pd.notna(row.get('activo')) else True,
                    'asignaturas_asociadas': asignaturas
                }
                cursos_importados += 1

            # Auto-ordenar
            self.ordenar_cursos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.marcar_cambio_realizado()

            mensaje = f"✅ Importación completada:\n"
            mensaje += f"• {cursos_importados} cursos importados\n"
            if cursos_duplicados > 0:
                mensaje += f"• {cursos_duplicados} cursos duplicados (omitidos)"

            QMessageBox.information(self, "Importación Exitosa", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", f"Error al importar archivo CSV:\n{str(e)}")

    def exportar_a_csv(self):
        """Exportar cursos a archivo CSV"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay cursos para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Cursos a CSV",
            f"cursos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Archivos CSV (*.csv)"
        )

        if not archivo:
            return

        try:
            datos_export = []
            for codigo, datos in self.datos_configuracion.items():
                # Convertir asignaturas a string
                asignaturas_str = ', '.join(datos.get('asignaturas_asociadas', []))

                datos_export.append({
                    'codigo': codigo,
                    'nombre': datos.get('nombre', ''),
                    'curso_actual': datos.get('curso_actual', ''),
                    'coordinador': datos.get('coordinador', ''),
                    'departamento': datos.get('departamento', ''),
                    'creditos_totales': datos.get('creditos_totales', 240),
                    'plazas': datos.get('plazas', 100),
                    'estudiantes_matriculados': datos.get('estudiantes_matriculados', 0),
                    'horario_tipo': datos.get('horario_tipo', 'Mañana'),
                    'observaciones': datos.get('observaciones', ''),
                    'activo': datos.get('activo', True),
                    'asignaturas_asociadas': asignaturas_str
                })

            df = pd.DataFrame(datos_export)
            df.to_csv(archivo, index=False, encoding='utf-8')

            QMessageBox.information(self, "Exportación Exitosa", f"Datos exportados a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar datos:\n{str(e)}")

    def exportar_estadisticas(self):
        """Exportar estadísticas completas a archivo"""
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Estadísticas Completas",
            f"estadisticas_cursos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write("ESTADÍSTICAS COMPLETAS DE CURSOS - OPTIM Labs\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

                f.write(f"RESUMEN GENERAL:\n")
                f.write(f"• Total cursos configurados: {len(self.datos_configuracion)}\n")

                # Estadísticas por tipo de horario
                horarios = {}
                for datos in self.datos_configuracion.values():
                    horario = datos.get('horario_tipo', 'Sin horario')
                    horarios[horario] = horarios.get(horario, 0) + 1

                f.write(f"• Por horario: {', '.join(f'{k}: {v}' for k, v in horarios.items())}\n")

                # Estadísticas generales
                total_plazas = sum(datos.get('plazas', 0) for datos in self.datos_configuracion.values())
                total_matriculados = sum(
                    datos.get('estudiantes_matriculados', 0) for datos in self.datos_configuracion.values())
                ocupacion_global = (total_matriculados / total_plazas * 100) if total_plazas > 0 else 0

                f.write(f"• Total plazas: {total_plazas}\n")
                f.write(f"• Total matriculados: {total_matriculados}\n")
                f.write(f"• Ocupación global: {ocupacion_global:.1f}%\n\n")

                # Detalles por curso
                f.write("DETALLES POR CURSO:\n")
                f.write("=" * 40 + "\n\n")

                for codigo, datos in sorted(self.datos_configuracion.items()):
                    f.write(f"🎓 {codigo} - {datos.get('nombre', 'Sin nombre')}\n")
                    f.write(f"   Coordinador: {datos.get('coordinador', 'No definido')}\n")
                    f.write(f"   Departamento: {datos.get('departamento', 'No definido')}\n")
                    f.write(f"   Curso: {datos.get('curso_actual', 'No definido')}\n")

                    plazas = datos.get('plazas', 0)
                    matriculados = datos.get('estudiantes_matriculados', 0)
                    ocupacion = (matriculados / plazas * 100) if plazas > 0 else 0
                    f.write(f"   Ocupación: {matriculados}/{plazas} ({ocupacion:.1f}%)\n")

                    asignaturas = datos.get('asignaturas_asociadas', [])
                    f.write(f"   Asignaturas: {len(asignaturas)} asociadas\n")
                    for asignatura in asignaturas:
                        f.write(f"     • {asignatura}\n")

                    f.write(f"   Estado: {'Activo' if datos.get('activo', True) else 'Inactivo'}\n\n")

            QMessageBox.information(self, "Exportación Exitosa", f"Estadísticas exportadas a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar estadísticas:\n{str(e)}")

    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Cursos",
            "", "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "cursos" in datos_cargados:
                self.datos_configuracion = datos_cargados["cursos"]
            elif isinstance(datos_cargados, dict):
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Auto-ordenar
            self.ordenar_cursos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.curso_actual = None
            self.label_curso_actual.setText("Seleccione un curso")
            self.info_curso.setText("ℹ️ Seleccione un curso para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_asignaturas.setEnabled(False)

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def guardar_en_archivo(self):
        """Guardar configuración en archivo JSON"""
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Cursos",
            f"cursos_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'cursos': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_cursos': len(self.datos_configuracion),
                    'generado_por': 'OPTIM Labs - Configurar Cursos'
                }
            }

            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Éxito", f"Configuración guardada en:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar configuración:\n{str(e)}")

    def guardar_en_sistema(self):
        """Guardar configuración en el sistema principal"""
        try:
            if not self.datos_configuracion:
                QMessageBox.warning(self, "Sin Datos", "No hay cursos configurados para guardar.")
                return

            total_cursos = len(self.datos_configuracion)
            cursos_activos = sum(1 for datos in self.datos_configuracion.values() if datos.get('activo', True))

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• {total_cursos} cursos configurados\n"
                f"• {cursos_activos} cursos activos\n\n"
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

    def limpiar_todos_cursos(self):
        """Limpiar todos los cursos configurados"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay cursos para limpiar")
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Todo",
            f"¿Está seguro de eliminar todos los cursos configurados?\n\n"
            f"Se eliminarán {len(self.datos_configuracion)} cursos.\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion.clear()
            self.curso_actual = None

            # Actualizar interfaz
            self.cargar_lista_cursos()
            self.label_curso_actual.setText("Seleccione un curso")
            self.info_curso.setText("ℹ️ Seleccione un curso para ver sus detalles")
            self.texto_stats.setText("📈 Presiona 'Actualizar desde Alumnos' para ver estadísticas")
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_asignaturas.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Limpieza Completada", "Todos los cursos han sido eliminados")

    def ordenar_cursos_alfabeticamente(self):
        """Reordenar cursos alfabéticamente por código"""
        if not self.datos_configuracion:
            return

        # Crear nuevo diccionario ordenado por código
        cursos_ordenados = {}
        for codigo in sorted(self.datos_configuracion.keys()):
            cursos_ordenados[codigo] = self.datos_configuracion[codigo]

        self.datos_configuracion = cursos_ordenados

    def auto_seleccionar_curso(self, codigo_curso):
        """Auto-seleccionar curso por código"""
        try:
            for i in range(self.list_cursos.count()):
                item = self.list_cursos.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == codigo_curso:
                    self.list_cursos.setCurrentItem(item)
                    self.seleccionar_curso(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando curso: {e}", "warning")

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
            self.log_mensaje("🔚 Cerrando configuración de cursos", "info")
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
                "cursos": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarCursos",
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

    # Datos de ejemplo
    datos_ejemplo = {
        "A102": {
            "codigo": "A102",
            "nombre": "Grado en Ingeniería en Tecnologías Industriales",
            "curso_actual": "1º Curso",
            "coordinador": "Dr. García López",
            "departamento": "Ingeniería Industrial",
            "creditos_totales": 240,
            "plazas": 120,
            "estudiantes_matriculados": 95,
            "horario_tipo": "Mañana",
            "observaciones": "Curso de nueva implantación",
            "fecha_creacion": datetime.now().isoformat(),
            "activo": True,
            "asignaturas_asociadas": ["FIS1", "MAT1", "QUI1"]
        },
        "B102": {
            "codigo": "B102",
            "nombre": "Grado en Ingeniería Eléctrica",
            "curso_actual": "1º Curso",
            "coordinador": "Dra. Martínez Ruiz",
            "departamento": "Ingeniería Eléctrica",
            "creditos_totales": 240,
            "plazas": 80,
            "estudiantes_matriculados": 76,
            "horario_tipo": "Mañana",
            "observaciones": "",
            "fecha_creacion": datetime.now().isoformat(),
            "activo": True,
            "asignaturas_asociadas": ["FIS1", "MAT1", "ELE1"]
        },
        "A302": {
            "codigo": "A302",
            "nombre": "Grado en Ingeniería Electrónica Industrial",
            "curso_actual": "3º Curso",
            "coordinador": "Dr. Fernández Castro",
            "departamento": "Ingeniería Electrónica",
            "creditos_totales": 240,
            "plazas": 60,
            "estudiantes_matriculados": 54,
            "horario_tipo": "Tarde",
            "observaciones": "Curso con alta demanda",
            "fecha_creacion": datetime.now().isoformat(),
            "activo": True,
            "asignaturas_asociadas": ["EANA", "EDIG", "PROG3"]
        }
    }

    window = ConfigurarCursos(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()