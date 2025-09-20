#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Asignaturas - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión integral de asignaturas con datos académicos completos
2. Configuración dinámica de grados que cursan cada asignatura
3. Planificación automática de grupos basada en matriculaciones reales
4. Estadísticas automáticas sincronizadas con datos de alumnos
5. Configuración detallada de laboratorio y equipamiento requerido
6. Cálculo inteligente de grupos recomendados por capacidad
7. Validación de equipamiento contra aulas disponibles
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


class GestionAsignaturaDialog(QDialog):
    """Dialog para añadir/editar asignatura con configuración completa"""

    def __init__(self, asignatura_existente=None, alumnos_disponibles=None, aulas_disponibles=None, parent=None):
        super().__init__(parent)
        self.asignatura_existente = asignatura_existente
        self.alumnos_disponibles = alumnos_disponibles or {}
        self.aulas_disponibles = aulas_disponibles or {}
        self.parent_window = parent
        self.setWindowTitle("Editar Asignatura" if asignatura_existente else "Nueva Asignatura")
        self.setModal(True)

        window_width = 700
        window_height = 800
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()



        if self.asignatura_existente:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Datos básicos de la asignatura
        basicos_group = QGroupBox("📝 DATOS BÁSICOS DE LA ASIGNATURA")
        basicos_layout = QFormLayout()

        self.edit_codigo = QLineEdit()
        self.edit_codigo.setPlaceholderText("FIS001, QUI200, PROG101")

        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Física I, Química Orgánica, etc.")

        self.combo_semestre = QComboBox()
        self.combo_semestre.addItems(["1º Cuatrimestre", "2º Cuatrimestre"])

        self.combo_curso = QComboBox()
        self.combo_curso.addItems(["1º Curso", "2º Curso", "3º Curso", "4º Curso", "Master"])

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Laboratorio", "Teórica", "Práctica", "Seminario"])

        self.edit_descripcion = QTextEdit()
        self.edit_descripcion.setPlaceholderText("Descripción breve de la asignatura...")
        self.edit_descripcion.setMaximumHeight(80)

        basicos_layout.addRow("🏷️ Código:", self.edit_codigo)
        basicos_layout.addRow("📚 Nombre:", self.edit_nombre)
        basicos_layout.addRow("📅 Semestre:", self.combo_semestre)
        basicos_layout.addRow("🎓 Curso:", self.combo_curso)
        basicos_layout.addRow("📖 Tipo:", self.combo_tipo)
        basicos_layout.addRow("📝 Descripción:", self.edit_descripcion)

        basicos_group.setLayout(basicos_layout)
        layout.addWidget(basicos_group)

        # Gestión dinámica de grados (como en configurar_horarios.py)
        grados_group = QGroupBox("🎓 GRADOS QUE CURSAN ESTA ASIGNATURA")
        grados_layout = QVBoxLayout()

        # Header con botones de gestión
        grados_header = QHBoxLayout()
        grados_header.addWidget(QLabel("Grados:"))
        grados_header.addStretch()

        btn_add_grado = QPushButton("➕")
        btn_add_grado.setMinimumSize(30, 25)
        btn_add_grado.setMaximumSize(40, 40)
        btn_add_grado.setStyleSheet(self.get_button_style("#4CAF50"))
        btn_add_grado.setToolTip("Añadir nuevo grado")
        btn_add_grado.clicked.connect(self.anadir_grado)
        grados_header.addWidget(btn_add_grado)

        btn_edit_grado = QPushButton("✏️")
        btn_edit_grado.setMinimumSize(30, 25)
        btn_edit_grado.setMaximumSize(40, 40)
        btn_edit_grado.setStyleSheet(self.get_button_style("#2196F3"))
        btn_edit_grado.setToolTip("Editar grado seleccionado")
        btn_edit_grado.clicked.connect(self.editar_grado_seleccionado)
        grados_header.addWidget(btn_edit_grado)

        btn_delete_grado = QPushButton("🗑️")
        btn_delete_grado.setMinimumSize(30, 25)
        btn_delete_grado.setMaximumSize(40, 40)
        btn_delete_grado.setStyleSheet(self.get_button_style("#f44336"))
        btn_delete_grado.setToolTip("Eliminar grado seleccionado")
        btn_delete_grado.clicked.connect(self.eliminar_grado_seleccionado)
        grados_header.addWidget(btn_delete_grado)

        grados_layout.addLayout(grados_header)

        # Lista dinámica de grados
        self.list_grados_dialog = QListWidget()
        self.list_grados_dialog.setMaximumHeight(120)
        grados_layout.addWidget(self.list_grados_dialog)

        info_grados = QLabel("💡 Tip: Gestiona los grados dinámicamente con los botones de arriba")
        info_grados.setStyleSheet("color: #cccccc; font-size: 10px; font-style: italic;")
        grados_layout.addWidget(info_grados)

        grados_group.setLayout(grados_layout)
        layout.addWidget(grados_group)

        # Configuración de laboratorio
        lab_group = QGroupBox("🔬 CONFIGURACIÓN DE LABORATORIO")
        lab_layout = QFormLayout()

        # Horas por sesión
        horas_layout = QHBoxLayout()
        self.spin_horas_sesion = QSpinBox()
        self.spin_horas_sesion.setRange(1, 8)
        self.spin_horas_sesion.setValue(2)
        self.spin_horas_sesion.setSuffix(" horas")
        horas_layout.addWidget(self.spin_horas_sesion)
        horas_layout.addWidget(QLabel("por sesión de laboratorio"))
        horas_layout.addStretch()

        # Máximo estudiantes por grupo
        max_estudiantes_layout = QHBoxLayout()
        self.spin_max_estudiantes = QSpinBox()
        self.spin_max_estudiantes.setRange(5, 50)
        self.spin_max_estudiantes.setValue(20)
        self.spin_max_estudiantes.setSuffix(" estudiantes")
        max_estudiantes_layout.addWidget(self.spin_max_estudiantes)
        max_estudiantes_layout.addWidget(QLabel("máximo por grupo"))
        max_estudiantes_layout.addStretch()

        # Equipamiento requerido
        self.edit_equipamiento = QLineEdit()
        self.edit_equipamiento.setPlaceholderText("Osciloscopios, Generadores, Multímetros, etc.")

        lab_layout.addRow("⏱️ Duración:", horas_layout)
        lab_layout.addRow("👥 Capacidad:", max_estudiantes_layout)
        lab_layout.addRow("🔧 Equipamiento:", self.edit_equipamiento)

        lab_group.setLayout(lab_layout)
        layout.addWidget(lab_group)

        # Planificación
        planificacion_group = QGroupBox("📊 PLANIFICACIÓN")
        planificacion_layout = QFormLayout()

        # Número de grupos previstos
        grupos_layout = QHBoxLayout()
        self.spin_grupos_previstos = QSpinBox()
        self.spin_grupos_previstos.setRange(1, 20)
        self.spin_grupos_previstos.setValue(6)
        self.spin_grupos_previstos.setSuffix(" grupos")
        grupos_layout.addWidget(self.spin_grupos_previstos)
        grupos_layout.addWidget(QLabel("previstos inicialmente"))
        grupos_layout.addStretch()

        # Número de clases en el año
        clases_layout = QHBoxLayout()
        self.spin_clases_año = QSpinBox()
        self.spin_clases_año.setRange(1, 15)
        self.spin_clases_año.setValue(3)
        self.spin_clases_año.setSuffix(" clases")
        clases_layout.addWidget(self.spin_clases_año)
        clases_layout.addWidget(QLabel("durante el año académico"))
        clases_layout.addStretch()

        planificacion_layout.addRow("👥 Grupos:", grupos_layout)
        planificacion_layout.addRow("📅 Clases:", clases_layout)

        planificacion_group.setLayout(planificacion_layout)
        layout.addWidget(planificacion_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def cargar_datos_existentes(self):
        """Cargar datos de la asignatura existente"""
        if not self.asignatura_existente:
            return

        datos = self.asignatura_existente
        self.edit_codigo.setText(datos.get('codigo', ''))
        self.edit_nombre.setText(datos.get('nombre', ''))

        # Semestre
        semestre = datos.get('semestre', '1º Cuatrimestre')
        index = self.combo_semestre.findText(semestre)
        if index >= 0:
            self.combo_semestre.setCurrentIndex(index)

        # Curso
        curso = datos.get('curso', '1º Curso')
        index = self.combo_curso.findText(curso)
        if index >= 0:
            self.combo_curso.setCurrentIndex(index)

        # Tipo
        tipo = datos.get('tipo', 'Laboratorio')
        index = self.combo_tipo.findText(tipo)
        if index >= 0:
            self.combo_tipo.setCurrentIndex(index)

        self.edit_descripcion.setText(datos.get('descripcion', ''))

        # Grados (cargar en lista dinámica)
        grados = datos.get('grados_que_cursan', [])
        self.list_grados_dialog.clear()
        for grado in sorted(grados):
            item = QListWidgetItem(grado)
            item.setData(Qt.ItemDataRole.UserRole, grado)
            self.list_grados_dialog.addItem(item)

        # Configuración laboratorio
        config_lab = datos.get('configuracion_laboratorio', {})
        self.spin_horas_sesion.setValue(config_lab.get('horas_por_sesion', 2))
        self.spin_max_estudiantes.setValue(config_lab.get('max_estudiantes_grupo', 20))
        self.edit_equipamiento.setText(config_lab.get('equipamiento', ''))

        # Planificación
        planificacion = datos.get('planificacion', {})
        self.spin_grupos_previstos.setValue(planificacion.get('grupos_previstos', 6))
        self.spin_clases_año.setValue(planificacion.get('clases_año', 3))

    def validar_y_aceptar(self):
        """Validar datos antes de aceptar"""
        # Validar campos obligatorios
        if not self.edit_codigo.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El código de la asignatura es obligatorio")
            self.edit_codigo.setFocus()
            return

        if not self.edit_nombre.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre de la asignatura es obligatorio")
            self.edit_nombre.setFocus()
            return

        # Validar que al menos un grado esté seleccionado
        grados_seleccionados = self.get_grados_seleccionados()
        if not grados_seleccionados:
            QMessageBox.warning(self, "Grados requeridos",
                                "Debe seleccionar al menos un grado que curse esta asignatura")
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

    def anadir_grado(self):
        """Añadir nuevo grado a la asignatura"""
        grado, ok = QInputDialog.getText(self, "Nuevo Grado", "Código del grado (ej: GII, GIOI, DOBLE):")

        if ok and grado.strip():
            grado = grado.strip().upper()

            # Verificar si ya existe
            for i in range(self.list_grados_dialog.count()):
                if self.list_grados_dialog.item(i).text() == grado:
                    QMessageBox.warning(self, "Error", "Este grado ya existe en la asignatura")
                    return

            # Añadir a la lista
            item = QListWidgetItem(grado)
            item.setData(Qt.ItemDataRole.UserRole, grado)
            self.list_grados_dialog.addItem(item)

            # Ordenar alfabéticamente
            self.ordenar_grados_lista()

            # Auto-seleccionar el grado añadido
            self.auto_seleccionar_grado_dialog(grado)

    def editar_grado_seleccionado(self):
        """Editar grado seleccionado"""
        item_actual = self.list_grados_dialog.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grado para editar")
            return

        grado_original = item_actual.text()


        nuevo_grado, ok = QInputDialog.getText(
            self, "Editar Grado",
            f"Editar código del grado:",
            text=grado_original
        )

        if ok and nuevo_grado.strip():
            nuevo_grado = nuevo_grado.strip().upper()

            if nuevo_grado == grado_original:
                return

            # Verificar si ya existe
            for i in range(self.list_grados_dialog.count()):
                if self.list_grados_dialog.item(i).text() == nuevo_grado:
                    QMessageBox.warning(self, "Error", "Este grado ya existe en la asignatura")
                    return

            # Actualizar el item
            item_actual.setText(nuevo_grado)
            item_actual.setData(Qt.ItemDataRole.UserRole, nuevo_grado)

            # Ordenar alfabéticamente
            self.ordenar_grados_lista()

            # Auto-seleccionar el grado editado
            self.auto_seleccionar_grado_dialog(nuevo_grado)

    def eliminar_grado_seleccionado(self):
        """Eliminar grado seleccionado"""
        item_actual = self.list_grados_dialog.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grado para eliminar")
            return

        grado = item_actual.text()

        respuesta = QMessageBox.question(
            self, "Eliminar Grado",
            f"¿Está seguro de eliminar el grado '{grado}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            row = self.list_grados_dialog.row(item_actual)
            self.list_grados_dialog.takeItem(row)

    def ordenar_grados_lista(self):
        """Ordenar grados alfabéticamente en la lista"""
        grados = []
        for i in range(self.list_grados_dialog.count()):
            item = self.list_grados_dialog.item(i)
            grados.append(item.text())

        # Limpiar y recargar ordenado
        self.list_grados_dialog.clear()
        for grado in sorted(grados):
            item = QListWidgetItem(grado)
            item.setData(Qt.ItemDataRole.UserRole, grado)
            self.list_grados_dialog.addItem(item)

    def get_grados_seleccionados(self):
        """Obtener lista de grados de la lista dinámica"""
        grados = []
        for i in range(self.list_grados_dialog.count()):
            item = self.list_grados_dialog.item(i)
            grados.append(item.text())
        return sorted(grados)

    def auto_seleccionar_grado_dialog(self, grado):
        """Auto-seleccionar grado en el dialog"""
        for i in range(self.list_grados_dialog.count()):
            item = self.list_grados_dialog.item(i)
            if item.text() == grado:
                self.list_grados_dialog.setCurrentItem(item)
                break

    def get_datos_asignatura(self):
        """Obtener datos configurados"""
        return {
            'codigo': self.edit_codigo.text().strip().upper(),
            'nombre': self.edit_nombre.text().strip(),
            'semestre': self.combo_semestre.currentText(),
            'curso': self.combo_curso.currentText(),
            'tipo': self.combo_tipo.currentText(),
            'descripcion': self.edit_descripcion.toPlainText().strip(),
            'grados_que_cursan': self.get_grados_seleccionados(),
            'configuracion_laboratorio': {
                'horas_por_sesion': self.spin_horas_sesion.value(),
                'max_estudiantes_grupo': self.spin_max_estudiantes.value(),
                'equipamiento': self.edit_equipamiento.text().strip()
            },
            'planificacion': {
                'grupos_previstos': self.spin_grupos_previstos.value(),
                'clases_año': self.spin_clases_año.value()
            },
            'estadisticas_calculadas': {
                'total_matriculados': 0,
                'con_lab_anterior': 0,
                'sin_lab_anterior': 0,
                'grupos_recomendados': 0,
                'ultima_actualizacion': datetime.now().isoformat()
            },
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
        """)


class ConfigurarAsignaturas(QMainWindow):
    """Ventana principal para configurar asignaturas del sistema"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Asignaturas - OPTIM Labs")
        window_width = 1400
        window_height = 750
        center_window_on_screen_immediate(self, window_width, window_height)

        # Obtener datos relacionados desde el sistema global
        self.alumnos_disponibles = self.obtener_alumnos_del_sistema()
        self.aulas_disponibles = self.obtener_aulas_del_sistema()
        self.horarios_disponibles = self.obtener_horarios_del_sistema()

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("📥 Cargando configuración existente de asignaturas...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("📝 Iniciando configuración nueva de asignaturas...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.asignatura_actual = None

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

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

    def obtener_aulas_del_sistema(self):
        """Obtener aulas configuradas desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_aulas = self.parent_window.configuracion["configuracion"].get("aulas", {})
                if config_aulas.get("configurado") and config_aulas.get("datos"):
                    return config_aulas["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo aulas del sistema: {e}", "warning")
            return {}

    def cargar_datos_iniciales(self):
        """Cargar datos existentes al inicializar"""
        try:
            # Ordenar asignaturas alfabéticamente
            self.ordenar_asignaturas_alfabeticamente()

            # Cargar lista
            self.cargar_lista_asignaturas()

            # Mostrar resumen
            total_asignaturas = len(self.datos_configuracion)

            if total_asignaturas > 0:
                self.log_mensaje(
                    f"✅ Datos cargados: {total_asignaturas} asignaturas configuradas",
                    "success"
                )
                self.auto_seleccionar_primera_asignatura()
            else:
                self.log_mensaje("📝 No hay asignaturas configuradas - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primera_asignatura(self):
        """Auto-seleccionar primera asignatura disponible"""
        try:
            if self.list_asignaturas.count() > 0:
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
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("📚 CONFIGURACIÓN DE ASIGNATURAS")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información del flujo
        info_label = QLabel(
            "ℹ️ Define las asignaturas, grados que las cursan y configuración de laboratorio. Las estadísticas se actualizan desde los alumnos matriculados.")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de asignaturas
        left_panel = QGroupBox("📋 ASIGNATURAS CONFIGURADAS")
        left_layout = QVBoxLayout()

        # Header con botones de gestión
        asignaturas_header = QHBoxLayout()
        asignaturas_header.addWidget(QLabel("Asignaturas:"))
        asignaturas_header.addStretch()

        btn_add_asignatura = self.crear_boton_accion("➕", "#4CAF50", "Añadir nueva asignatura")
        btn_add_asignatura.clicked.connect(self.anadir_asignatura)

        btn_edit_asignatura = self.crear_boton_accion("✏️", "#2196F3", "Editar asignatura seleccionada")
        btn_edit_asignatura.clicked.connect(self.editar_asignatura_seleccionada)

        btn_delete_asignatura = self.crear_boton_accion("🗑️", "#f44336", "Eliminar asignatura seleccionada")
        btn_delete_asignatura.clicked.connect(self.eliminar_asignatura_seleccionada)

        asignaturas_header.addWidget(btn_add_asignatura)
        asignaturas_header.addWidget(btn_edit_asignatura)
        asignaturas_header.addWidget(btn_delete_asignatura)

        left_layout.addLayout(asignaturas_header)

        # Lista de asignaturas
        self.list_asignaturas = QListWidget()
        self.list_asignaturas.setMaximumWidth(400)
        self.list_asignaturas.setMinimumHeight(400)
        left_layout.addWidget(self.list_asignaturas)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Detalles de la asignatura
        center_panel = QGroupBox("🔍 DETALLES DE LA ASIGNATURA")
        center_layout = QVBoxLayout()
        center_layout.setSpacing(8)

        # Nombre de la asignatura seleccionada
        self.label_asignatura_actual = QLabel("Seleccione una asignatura")
        self.label_asignatura_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_asignatura_actual)

        # Información detallada
        self.info_asignatura = QTextEdit()
        self.info_asignatura.setMaximumHeight(300)
        self.info_asignatura.setReadOnly(True)
        self.info_asignatura.setText("ℹ️ Seleccione una asignatura para ver sus detalles")
        center_layout.addWidget(self.info_asignatura)

        # Estadísticas automáticas
        stats_group = QGroupBox("📊 ESTADÍSTICAS AUTOMÁTICAS")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)

        botones_stats_layout = QHBoxLayout()
        self.btn_actualizar_desde_alumnos = QPushButton("🔄 Actualizar desde Alumnos")
        self.btn_actualizar_desde_alumnos.clicked.connect(self.actualizar_estadisticas_desde_alumnos)
        botones_stats_layout.addWidget(self.btn_actualizar_desde_alumnos)

        self.btn_calcular_grupos = QPushButton("📊 Calcular Grupos Recomendados")
        self.btn_calcular_grupos.clicked.connect(self.calcular_grupos_recomendados)
        botones_stats_layout.addWidget(self.btn_calcular_grupos)

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

        self.btn_duplicar = QPushButton("📋 Duplicar Asignatura")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_asignatura_seleccionada)
        acciones_layout.addWidget(self.btn_duplicar)

        self.btn_validar_equipamiento = QPushButton("🔧 Validar Equipamiento")
        self.btn_validar_equipamiento.setEnabled(False)
        self.btn_validar_equipamiento.clicked.connect(self.validar_equipamiento_asignatura)
        acciones_layout.addWidget(self.btn_validar_equipamiento)

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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todas_asignaturas)
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
        self.list_asignaturas.itemClicked.connect(self.seleccionar_asignatura)

    def cargar_lista_asignaturas(self):
        """Cargar asignaturas en la lista visual"""
        self.list_asignaturas.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay asignaturas configuradas")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_asignaturas.addItem(item)
            return

        # Ordenar asignaturas por código
        asignaturas_ordenadas = sorted(self.datos_configuracion.items())

        for codigo, datos in asignaturas_ordenadas:
            nombre = datos.get('nombre', 'Sin nombre')
            semestre = datos.get('semestre', 'Sin semestre')
            tipo = datos.get('tipo', 'Sin tipo')

            # Mostrar grados que la cursan
            grados = datos.get('grados_que_cursan', [])
            grados_str = ', '.join(grados) if grados else 'Sin grados'

            # Estadísticas
            stats = datos.get('estadisticas_calculadas', {})
            total_matriculados = stats.get('total_matriculados', 0)
            sin_lab_anterior = stats.get('sin_lab_anterior', 0)

            # Icono según estado
            icono = "📚" if tipo == "Laboratorio" else "📖"

            texto_item = f"{icono} {codigo} - {nombre}"
            if total_matriculados > 0:
                texto_item += f" ({sin_lab_anterior}/{total_matriculados} alumnos)"
            texto_item += f"\n    {semestre} | {grados_str}"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_asignaturas.addItem(item)

    def seleccionar_asignatura(self, item):
        """Seleccionar asignatura y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.asignatura_actual = None
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_equipamiento.setEnabled(False)
            return

        codigo = item.data(Qt.ItemDataRole.UserRole)
        if not codigo or codigo not in self.datos_configuracion:
            return

        self.asignatura_actual = codigo
        datos = self.datos_configuracion[codigo]

        # Actualizar etiqueta
        nombre = datos.get('nombre', 'Sin nombre')
        self.label_asignatura_actual.setText(f"📚 {codigo} - {nombre}")

        # Mostrar información detallada
        info = f"📚 ASIGNATURA: {codigo} - {nombre}\n\n"
        info += f"📅 Semestre: {datos.get('semestre', 'No definido')}\n"
        info += f"🎓 Curso: {datos.get('curso', 'No definido')}\n"
        info += f"📖 Tipo: {datos.get('tipo', 'No definido')}\n"
        info += f"📝 Descripción: {datos.get('descripcion', 'Sin descripción')}\n\n"

        # Grados que la cursan
        grados = datos.get('grados_que_cursan', [])
        if grados:
            info += f"🎓 GRADOS QUE LA CURSAN ({len(grados)}):\n"
            for grado in grados:
                info += f"  • {grado}\n"
        else:
            info += f"🎓 GRADOS: Sin grados asignados\n"
        info += "\n"

        # Configuración laboratorio
        config_lab = datos.get('configuracion_laboratorio', {})
        info += f"🔬 CONFIGURACIÓN LABORATORIO:\n"
        info += f"• Horas por sesión: {config_lab.get('horas_por_sesion', 'No definido')}\n"
        info += f"• Máx. estudiantes/grupo: {config_lab.get('max_estudiantes_grupo', 'No definido')}\n"
        info += f"• Equipamiento: {config_lab.get('equipamiento', 'No definido')}\n\n"

        # Planificación
        planificacion = datos.get('planificacion', {})
        info += f"📊 PLANIFICACIÓN:\n"
        info += f"• Grupos previstos: {planificacion.get('grupos_previstos', 'No definido')}\n"
        info += f"• Clases en el año: {planificacion.get('clases_año', 'No definido')}\n\n"

        # Estadísticas
        stats = datos.get('estadisticas_calculadas', {})
        info += f"📈 ESTADÍSTICAS:\n"
        info += f"• Total matriculados: {stats.get('total_matriculados', 0)}\n"
        info += f"• Con lab anterior: {stats.get('con_lab_anterior', 0)} (filtrados)\n"
        info += f"• Sin lab anterior: {stats.get('sin_lab_anterior', 0)} (para scheduling)\n"
        info += f"• Grupos recomendados: {stats.get('grupos_recomendados', 0)}\n"

        ultima_actualizacion = stats.get('ultima_actualizacion', '')
        if ultima_actualizacion:
            try:
                fecha = datetime.fromisoformat(ultima_actualizacion.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
                info += f"• Última actualización: {fecha}"
            except:
                info += f"• Última actualización: {ultima_actualizacion}"

        self.info_asignatura.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)
        self.btn_validar_equipamiento.setEnabled(True)

    def anadir_asignatura(self):
        """Añadir nueva asignatura"""
        dialog = GestionAsignaturaDialog(None, self.alumnos_disponibles, self.aulas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_asignatura()
            codigo = datos['codigo']

            if codigo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe una asignatura con el código '{codigo}'")
                return

            # Añadir nueva asignatura
            self.datos_configuracion[codigo] = datos

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.auto_seleccionar_asignatura(codigo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Asignatura '{codigo} - {datos['nombre']}' añadida correctamente")

    def editar_asignatura_seleccionada(self):
        """Editar asignatura seleccionada"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para editar")
            return

        datos_originales = self.datos_configuracion[self.asignatura_actual].copy()
        dialog = GestionAsignaturaDialog(datos_originales, self.alumnos_disponibles, self.aulas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_asignatura()
            codigo_nuevo = datos_nuevos['codigo']
            codigo_original = self.asignatura_actual

            # Si cambió el código, verificar que no exista
            if codigo_nuevo != codigo_original and codigo_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe una asignatura con el código '{codigo_nuevo}'")
                return

            # Preservar estadísticas existentes
            if 'estadisticas_calculadas' in datos_originales:
                datos_nuevos['estadisticas_calculadas'] = datos_originales['estadisticas_calculadas']

            # Actualizar datos
            if codigo_nuevo != codigo_original:
                del self.datos_configuracion[codigo_original]
                self.asignatura_actual = codigo_nuevo

            self.datos_configuracion[codigo_nuevo] = datos_nuevos

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.auto_seleccionar_asignatura(codigo_nuevo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Asignatura actualizada correctamente")

    def eliminar_asignatura_seleccionada(self):
        """Eliminar asignatura seleccionada"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para eliminar")
            return

        datos = self.datos_configuracion[self.asignatura_actual]
        nombre = datos.get('nombre', 'Sin nombre')

        respuesta = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de eliminar la asignatura '{self.asignatura_actual} - {nombre}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            del self.datos_configuracion[self.asignatura_actual]
            self.asignatura_actual = None

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.label_asignatura_actual.setText("Seleccione una asignatura")
            self.info_asignatura.setText("ℹ️ Seleccione una asignatura para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_equipamiento.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Asignatura eliminada correctamente")

    def duplicar_asignatura_seleccionada(self):
        """Duplicar asignatura seleccionada"""
        if not self.asignatura_actual:
            return

        datos_originales = self.datos_configuracion[self.asignatura_actual].copy()

        # Generar código único
        codigo_base = f"{datos_originales['codigo']}_COPIA"
        contador = 1
        codigo_nuevo = codigo_base

        while codigo_nuevo in self.datos_configuracion:
            codigo_nuevo = f"{codigo_base}_{contador}"
            contador += 1

        datos_originales['codigo'] = codigo_nuevo
        datos_originales['nombre'] = f"{datos_originales['nombre']} (Copia)"

        # Limpiar estadísticas
        datos_originales['estadisticas_calculadas'] = {
            'total_matriculados': 0,
            'con_lab_anterior': 0,
            'sin_lab_anterior': 0,
            'grupos_recomendados': 0,
            'ultima_actualizacion': datetime.now().isoformat()
        }

        dialog = GestionAsignaturaDialog(datos_originales, self.alumnos_disponibles, self.aulas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_asignatura()
            codigo_final = datos_nuevos['codigo']

            if codigo_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe una asignatura con el código '{codigo_final}'")
                return

            # Añadir asignatura duplicada
            self.datos_configuracion[codigo_final] = datos_nuevos

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.auto_seleccionar_asignatura(codigo_final)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Asignatura duplicada como '{codigo_final}'")

    def actualizar_estadisticas_desde_alumnos(self):
        """Actualizar estadísticas desde datos de alumnos matriculados"""
        try:
            if not self.alumnos_disponibles:
                self.texto_stats.setText("⚠️ No hay datos de alumnos disponibles")
                return

            # Agrupar alumnos por asignatura
            estadisticas_por_asignatura = {}

            for dni, datos_alumno in self.alumnos_disponibles.items():
                codigo_asig = datos_alumno.get('codigo_asignatura', '')
                if not codigo_asig:
                    continue

                if codigo_asig not in estadisticas_por_asignatura:
                    estadisticas_por_asignatura[codigo_asig] = {
                        'total_matriculados': 0,
                        'con_lab_anterior': 0,
                        'sin_lab_anterior': 0
                    }

                estadisticas_por_asignatura[codigo_asig]['total_matriculados'] += 1

                if datos_alumno.get('lab_anterior_aprobado', False):
                    estadisticas_por_asignatura[codigo_asig]['con_lab_anterior'] += 1
                else:
                    estadisticas_por_asignatura[codigo_asig]['sin_lab_anterior'] += 1

            # Actualizar estadísticas en asignaturas configuradas
            asignaturas_actualizadas = 0
            for codigo, datos_asignatura in self.datos_configuracion.items():
                if codigo in estadisticas_por_asignatura:
                    stats = estadisticas_por_asignatura[codigo]

                    # Calcular grupos recomendados
                    max_estudiantes = datos_asignatura.get('configuracion_laboratorio', {}).get('max_estudiantes_grupo',
                                                                                                20)
                    alumnos_reales = stats['sin_lab_anterior']
                    grupos_recomendados = (
                                                      alumnos_reales + max_estudiantes - 1) // max_estudiantes if alumnos_reales > 0 else 0

                    # Actualizar estadísticas
                    self.datos_configuracion[codigo]['estadisticas_calculadas'] = {
                        'total_matriculados': stats['total_matriculados'],
                        'con_lab_anterior': stats['con_lab_anterior'],
                        'sin_lab_anterior': stats['sin_lab_anterior'],
                        'grupos_recomendados': grupos_recomendados,
                        'ultima_actualizacion': datetime.now().isoformat()
                    }
                    asignaturas_actualizadas += 1
                else:
                    # Sin alumnos matriculados
                    self.datos_configuracion[codigo]['estadisticas_calculadas'] = {
                        'total_matriculados': 0,
                        'con_lab_anterior': 0,
                        'sin_lab_anterior': 0,
                        'grupos_recomendados': 0,
                        'ultima_actualizacion': datetime.now().isoformat()
                    }

            # Mostrar resumen de la actualización
            stats_text = f"🔄 ACTUALIZACIÓN COMPLETADA:\n\n"
            stats_text += f"• {asignaturas_actualizadas} asignaturas actualizadas\n"
            stats_text += f"• {len(self.alumnos_disponibles)} alumnos procesados\n\n"

            # Mostrar estadísticas por asignatura
            for codigo, datos in self.datos_configuracion.items():
                stats = datos.get('estadisticas_calculadas', {})
                total = stats.get('total_matriculados', 0)
                sin_lab = stats.get('sin_lab_anterior', 0)
                grupos_rec = stats.get('grupos_recomendados', 0)

                stats_text += f"📚 {codigo}:\n"
                stats_text += f"  • {total} matriculados, {sin_lab} para lab\n"
                stats_text += f"  • {grupos_rec} grupos recomendados\n\n"

            self.texto_stats.setText(stats_text)

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            if self.asignatura_actual:
                self.auto_seleccionar_asignatura(self.asignatura_actual)

            self.marcar_cambio_realizado()
            self.log_mensaje(f"✅ Estadísticas actualizadas: {asignaturas_actualizadas} asignaturas", "success")

        except Exception as e:
            self.texto_stats.setText(f"❌ Error actualizando estadísticas: {e}")
            self.log_mensaje(f"⚠️ Error actualizando estadísticas: {e}", "warning")

    def calcular_grupos_recomendados(self):
        """Calcular grupos recomendados para todas las asignaturas"""
        try:
            if not self.datos_configuracion:
                QMessageBox.information(self, "Sin Datos", "No hay asignaturas configuradas")
                return

            # Calcular para cada asignatura
            for codigo, datos in self.datos_configuracion.items():
                stats = datos.get('estadisticas_calculadas', {})
                config_lab = datos.get('configuracion_laboratorio', {})

                alumnos_reales = stats.get('sin_lab_anterior', 0)
                max_estudiantes = config_lab.get('max_estudiantes_grupo', 20)

                if alumnos_reales > 0:
                    grupos_recomendados = (alumnos_reales + max_estudiantes - 1) // max_estudiantes
                else:
                    grupos_recomendados = datos.get('planificacion', {}).get('grupos_previstos', 0)

                # Actualizar
                if 'estadisticas_calculadas' not in self.datos_configuracion[codigo]:
                    self.datos_configuracion[codigo]['estadisticas_calculadas'] = {}

                self.datos_configuracion[codigo]['estadisticas_calculadas']['grupos_recomendados'] = grupos_recomendados
                self.datos_configuracion[codigo]['estadisticas_calculadas'][
                    'ultima_actualizacion'] = datetime.now().isoformat()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            if self.asignatura_actual:
                self.auto_seleccionar_asignatura(self.asignatura_actual)

            self.marcar_cambio_realizado()
            QMessageBox.information(self, "Éxito", "Grupos recomendados calculados para todas las asignaturas")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calculando grupos: {e}")

    def validar_equipamiento_asignatura(self):
        """Validar equipamiento de la asignatura contra aulas disponibles"""
        if not self.asignatura_actual:
            return

        try:
            datos_asignatura = self.datos_configuracion[self.asignatura_actual]
            equipamiento_requerido = datos_asignatura.get('configuracion_laboratorio', {}).get('equipamiento', '')

            if not equipamiento_requerido:
                QMessageBox.information(self, "Sin Equipamiento",
                                        "Esta asignatura no tiene equipamiento especificado")
                return

            if not self.aulas_disponibles:
                QMessageBox.warning(self, "Sin Aulas",
                                    "No hay datos de aulas disponibles para validar")
                return

            # Buscar aulas compatibles
            aulas_compatibles = []
            for nombre_aula, datos_aula in self.aulas_disponibles.items():
                equipamiento_aula = datos_aula.get('equipamiento', '').lower()
                equipamiento_req = equipamiento_requerido.lower()

                # Validación simple por palabras clave
                if any(palabra in equipamiento_aula for palabra in equipamiento_req.split()):
                    capacidad = datos_aula.get('capacidad', 0)
                    disponible = datos_aula.get('disponible', False)
                    aulas_compatibles.append({
                        'nombre': nombre_aula,
                        'capacidad': capacidad,
                        'disponible': disponible,
                        'equipamiento': datos_aula.get('equipamiento', '')
                    })

            # Mostrar resultados
            mensaje = f"🔧 VALIDACIÓN DE EQUIPAMIENTO\n\n"
            mensaje += f"Asignatura: {self.asignatura_actual}\n"
            mensaje += f"Equipamiento requerido: {equipamiento_requerido}\n\n"

            if aulas_compatibles:
                mensaje += f"✅ Aulas compatibles encontradas ({len(aulas_compatibles)}):\n\n"
                for aula in aulas_compatibles:
                    estado = "✅ Disponible" if aula['disponible'] else "❌ No disponible"
                    mensaje += f"• {aula['nombre']} ({aula['capacidad']} personas) - {estado}\n"
                    mensaje += f"  Equipamiento: {aula['equipamiento']}\n\n"
            else:
                mensaje += "❌ No se encontraron aulas compatibles\n\n"
                mensaje += "💡 Sugerencias:\n"
                mensaje += "• Revisar la descripción del equipamiento\n"
                mensaje += "• Configurar aulas con equipamiento compatible\n"
                mensaje += "• Contactar con administración de laboratorios"

            QMessageBox.information(self, "Validación de Equipamiento", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error validando equipamiento: {e}")

    def importar_desde_horarios(self):
        """Importar asignaturas y grados desde módulo de horarios"""
        try:
            if not self.horarios_disponibles:
                QMessageBox.information(self, "Sin Datos",
                                        "No hay datos de horarios disponibles para importar")
                return

            # Obtener asignaturas del módulo de horarios
            asignaturas_horarios = self.horarios_disponibles.get("asignaturas", {})
            if not asignaturas_horarios:
                QMessageBox.information(self, "Sin Asignaturas",
                                        "No hay asignaturas configuradas en horarios")
                return

            asignaturas_importadas = 0
            grados_importados = 0

            # Procesar ambos semestres
            for semestre, asignaturas_sem in asignaturas_horarios.items():
                for nombre_asig, datos_asig in asignaturas_sem.items():
                    # Crear código de asignatura único si no existe
                    codigo_asig = nombre_asig.upper().replace(" ", "")[:6]

                    # Verificar si ya existe
                    if codigo_asig in self.datos_configuracion:
                        continue

                    # Importar grados
                    grados = datos_asig.get("grados", [])

                    # Crear asignatura nueva
                    self.datos_configuracion[codigo_asig] = {
                        'codigo': codigo_asig,
                        'nombre': nombre_asig,
                        'semestre': f"{semestre}º Cuatrimestre",
                        'curso': "1º Curso",  # Por defecto
                        'tipo': "Laboratorio",
                        'descripcion': f"Importada desde configuración de horarios",
                        'grados_que_cursan': sorted(grados),
                        'configuracion_laboratorio': {
                            'horas_por_sesion': 2,
                            'max_estudiantes_grupo': 20,
                            'equipamiento': ''
                        },
                        'planificacion': {
                            'grupos_previstos': 6,
                            'clases_año': 3
                        },
                        'estadisticas_calculadas': {
                            'total_matriculados': 0,
                            'con_lab_anterior': 0,
                            'sin_lab_anterior': 0,
                            'grupos_recomendados': 0,
                            'ultima_actualizacion': datetime.now().isoformat()
                        },
                        'fecha_creacion': datetime.now().isoformat()
                    }
                    asignaturas_importadas += 1
                    grados_importados += len(grados)

            if asignaturas_importadas > 0:
                # Auto-ordenar
                self.ordenar_asignaturas_alfabeticamente()

                # Actualizar interfaz
                self.cargar_lista_asignaturas()
                self.marcar_cambio_realizado()

                QMessageBox.information(self, "Importación Exitosa",
                                        f"✅ Importadas {asignaturas_importadas} asignaturas "
                                        f"con {grados_importados} grados desde horarios")
            else:
                QMessageBox.information(self, "Sin Importar",
                                        "No se encontraron asignaturas nuevas para importar")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error importando desde horarios: {e}")

    def sincronizar_con_horarios(self):
        """Sincronizar datos con módulo de horarios - BIDIRECCIONAL"""
        try:
            # Preparar datos para enviar a horarios
            datos_para_horarios = {}
            for codigo, datos in self.datos_configuracion.items():
                grados = datos.get('grados_que_cursan', [])
                stats = datos.get('estadisticas_calculadas', {})

                # Convertir a formato compatible con horarios
                datos_para_horarios[datos.get('nombre', codigo)] = {
                    'codigo': codigo,
                    'grados': grados,
                    'grupos_recomendados': stats.get('grupos_recomendados', 0),
                    'alumnos_reales': stats.get('sin_lab_anterior', 0),
                    'semestre': datos.get('semestre', '1º Cuatrimestre').split('º')[0]
                }

            # Enviar datos al sistema principal para sincronización
            if self.parent_window and hasattr(self.parent_window, 'sincronizar_asignaturas_horarios'):
                resultado = self.parent_window.sincronizar_asignaturas_horarios(datos_para_horarios)
                if resultado:
                    QMessageBox.information(self, "Sincronización",
                                            f"✅ Datos sincronizados con horarios: {len(datos_para_horarios)} asignaturas")
                else:
                    QMessageBox.warning(self, "Sincronización",
                                        "⚠️ Error en la sincronización con horarios")
            else:
                # Modo independiente - mostrar datos preparados
                mensaje = f"📤 Datos preparados para sincronización:\n\n"
                for nombre, datos in datos_para_horarios.items():
                    mensaje += f"• {nombre}: {len(datos['grados'])} grados, "
                    mensaje += f"{datos['grupos_recomendados']} grupos\n"

                QMessageBox.information(self, "Sincronización Preparada", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en sincronización: {e}")

    def notificar_cambios_a_horarios(self):
        """Notificar cambios de asignaturas al módulo de horarios"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'actualizar_asignaturas_desde_config'):
                # Preparar datos en formato compatible con horarios
                datos_para_horarios = {}

                # Organizar por semestres
                for codigo, datos in self.datos_configuracion.items():
                    semestre_num = "1" if "1º" in datos.get('semestre', '1º Cuatrimestre') else "2"
                    nombre = datos.get('nombre', codigo)
                    grados = datos.get('grados_que_cursan', [])

                    if semestre_num not in datos_para_horarios:
                        datos_para_horarios[semestre_num] = {}

                    datos_para_horarios[semestre_num][nombre] = {
                        'grados': grados,
                        'codigo': codigo,
                        'horarios': {}  # Se mantendrán los horarios existentes
                    }

                # Notificar al sistema principal
                self.parent_window.actualizar_asignaturas_desde_config(datos_para_horarios)
                self.log_mensaje("📤 Cambios notificados al módulo de horarios", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error notificando cambios a horarios: {e}", "warning")

    def importar_desde_csv(self):
        """Importar asignaturas desde archivo CSV"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Asignaturas desde CSV",
            "", "Archivos CSV (*.csv);;Todos los archivos (*)"
        )

        if not archivo:
            return

        try:
            df = pd.read_csv(archivo)

            # Verificar columnas requeridas
            columnas_requeridas = ['codigo', 'nombre', 'semestre', 'tipo']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]

            if columnas_faltantes:
                QMessageBox.warning(
                    self, "Columnas Faltantes",
                    f"El archivo CSV debe contener las columnas:\n{', '.join(columnas_faltantes)}"
                )
                return

            # Importar datos
            asignaturas_importadas = 0
            asignaturas_duplicadas = 0

            for _, row in df.iterrows():
                codigo = str(row['codigo']).strip().upper()
                if not codigo:
                    continue

                if codigo in self.datos_configuracion:
                    asignaturas_duplicadas += 1
                    continue

                # Procesar grados
                grados = []
                if 'grados_que_cursan' in df.columns and pd.notna(row['grados_que_cursan']):
                    grados_text = str(row['grados_que_cursan']).strip()
                    if grados_text:
                        grados = [g.strip().upper() for g in grados_text.split(',')]

                self.datos_configuracion[codigo] = {
                    'codigo': codigo,
                    'nombre': str(row['nombre']).strip(),
                    'semestre': str(row.get('semestre', '1º Cuatrimestre')).strip(),
                    'curso': str(row.get('curso', '1º Curso')).strip(),
                    'tipo': str(row['tipo']).strip(),
                    'descripcion': str(row.get('descripcion', '')).strip(),
                    'grados_que_cursan': grados,
                    'configuracion_laboratorio': {
                        'horas_por_sesion': int(row.get('horas_por_sesion', 2)) if pd.notna(
                            row.get('horas_por_sesion')) else 2,
                        'max_estudiantes_grupo': int(row.get('max_estudiantes_grupo', 20)) if pd.notna(
                            row.get('max_estudiantes_grupo')) else 20,
                        'equipamiento': str(row.get('equipamiento', '')).strip()
                    },
                    'planificacion': {
                        'grupos_previstos': int(row.get('grupos_previstos', 6)) if pd.notna(
                            row.get('grupos_previstos')) else 6,
                        'clases_año': int(row.get('clases_año', 3)) if pd.notna(row.get('clases_año')) else 3
                    },
                    'estadisticas_calculadas': {
                        'total_matriculados': 0,
                        'con_lab_anterior': 0,
                        'sin_lab_anterior': 0,
                        'grupos_recomendados': 0,
                        'ultima_actualizacion': datetime.now().isoformat()
                    },
                    'fecha_creacion': datetime.now().isoformat()
                }
                asignaturas_importadas += 1

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.marcar_cambio_realizado()

            mensaje = f"✅ Importación completada:\n"
            mensaje += f"• {asignaturas_importadas} asignaturas importadas\n"
            if asignaturas_duplicadas > 0:
                mensaje += f"• {asignaturas_duplicadas} asignaturas duplicadas (omitidas)"

            QMessageBox.information(self, "Importación Exitosa", mensaje)

        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", f"Error al importar archivo CSV:\n{str(e)}")

    def exportar_a_csv(self):
        """Exportar asignaturas a archivo CSV"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay asignaturas para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Asignaturas a CSV",
            f"asignaturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Archivos CSV (*.csv)"
        )

        if not archivo:
            return

        try:
            datos_export = []
            for codigo, datos in self.datos_configuracion.items():
                # Convertir grados a string
                grados_str = ', '.join(datos.get('grados_que_cursan', []))

                config_lab = datos.get('configuracion_laboratorio', {})
                planificacion = datos.get('planificacion', {})
                stats = datos.get('estadisticas_calculadas', {})

                datos_export.append({
                    'codigo': codigo,
                    'nombre': datos.get('nombre', ''),
                    'semestre': datos.get('semestre', ''),
                    'curso': datos.get('curso', ''),
                    'tipo': datos.get('tipo', ''),
                    'descripcion': datos.get('descripcion', ''),
                    'grados_que_cursan': grados_str,
                    'horas_por_sesion': config_lab.get('horas_por_sesion', 2),
                    'max_estudiantes_grupo': config_lab.get('max_estudiantes_grupo', 20),
                    'equipamiento': config_lab.get('equipamiento', ''),
                    'grupos_previstos': planificacion.get('grupos_previstos', 6),
                    'clases_año': planificacion.get('clases_año', 3),
                    'total_matriculados': stats.get('total_matriculados', 0),
                    'sin_lab_anterior': stats.get('sin_lab_anterior', 0),
                    'grupos_recomendados': stats.get('grupos_recomendados', 0)
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
            f"estadisticas_asignaturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write("ESTADÍSTICAS COMPLETAS DE ASIGNATURAS - OPTIM Labs\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

                f.write(f"RESUMEN GENERAL:\n")
                f.write(f"• Total asignaturas configuradas: {len(self.datos_configuracion)}\n")

                # Estadísticas por tipo
                tipos = {}
                for datos in self.datos_configuracion.values():
                    tipo = datos.get('tipo', 'Sin tipo')
                    tipos[tipo] = tipos.get(tipo, 0) + 1

                f.write(f"• Por tipo: {', '.join(f'{k}: {v}' for k, v in tipos.items())}\n\n")

                # Detalles por asignatura
                f.write("DETALLES POR ASIGNATURA:\n")
                f.write("=" * 40 + "\n\n")

                for codigo, datos in sorted(self.datos_configuracion.items()):
                    f.write(f"📚 {codigo} - {datos.get('nombre', 'Sin nombre')}\n")
                    f.write(f"   Semestre: {datos.get('semestre', 'No definido')}\n")
                    f.write(f"   Tipo: {datos.get('tipo', 'No definido')}\n")

                    grados = datos.get('grados_que_cursan', [])
                    f.write(f"   Grados: {', '.join(grados) if grados else 'Sin grados'}\n")

                    stats = datos.get('estadisticas_calculadas', {})
                    f.write(f"   Matriculados: {stats.get('total_matriculados', 0)}\n")
                    f.write(f"   Para lab: {stats.get('sin_lab_anterior', 0)}\n")
                    f.write(f"   Grupos recomendados: {stats.get('grupos_recomendados', 0)}\n")

                    config_lab = datos.get('configuracion_laboratorio', {})
                    f.write(f"   Equipamiento: {config_lab.get('equipamiento', 'No definido')}\n\n")

            QMessageBox.information(self, "Exportación Exitosa", f"Estadísticas exportadas a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar estadísticas:\n{str(e)}")

    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Asignaturas",
            "", "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "asignaturas" in datos_cargados:
                self.datos_configuracion = datos_cargados["asignaturas"]
            elif isinstance(datos_cargados, dict):
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.asignatura_actual = None
            self.label_asignatura_actual.setText("Seleccione una asignatura")
            self.info_asignatura.setText("ℹ️ Seleccione una asignatura para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_equipamiento.setEnabled(False)

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def guardar_en_archivo(self):
        """Guardar configuración en archivo JSON"""
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Asignaturas",
            f"asignaturas_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'asignaturas': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_asignaturas': len(self.datos_configuracion),
                    'generado_por': 'OPTIM Labs - Configurar Asignaturas'
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
                QMessageBox.warning(self, "Sin Datos", "No hay asignaturas configuradas para guardar.")
                return

            total_asignaturas = len(self.datos_configuracion)
            con_alumnos = sum(1 for datos in self.datos_configuracion.values()
                              if datos.get('estadisticas_calculadas', {}).get('total_matriculados', 0) > 0)

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• {total_asignaturas} asignaturas configuradas\n"
                f"• {con_alumnos} asignaturas con alumnos matriculados\n\n"
                f"La configuración se integrará con OPTIM y la ventana se cerrará.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Enviar señal al sistema principal
                self.configuracion_actualizada.emit(self.datos_configuracion)

                # NUEVO: Notificar a horarios DESPUÉS de guardar
                self.notificar_cambios_a_horarios()

                # Marcar como guardado
                self.datos_guardados_en_sistema = True
                self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)

                # Cerrar ventana
                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar en el sistema:\n{str(e)}")

    def limpiar_todas_asignaturas(self):
        """Limpiar todas las asignaturas configuradas"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay asignaturas para limpiar")
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Todo",
            f"¿Está seguro de eliminar todas las asignaturas configuradas?\n\n"
            f"Se eliminarán {len(self.datos_configuracion)} asignaturas.\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion.clear()
            self.asignatura_actual = None

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.label_asignatura_actual.setText("Seleccione una asignatura")
            self.info_asignatura.setText("ℹ️ Seleccione una asignatura para ver sus detalles")
            self.texto_stats.setText("📈 Presiona 'Actualizar desde Alumnos' para ver estadísticas")
            self.btn_duplicar.setEnabled(False)
            self.btn_validar_equipamiento.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Limpieza Completada", "Todas las asignaturas han sido eliminadas")

    def ordenar_asignaturas_alfabeticamente(self):
        """Reordenar asignaturas alfabéticamente por código"""
        if not self.datos_configuracion:
            return

        # Crear nuevo diccionario ordenado por código
        asignaturas_ordenadas = {}
        for codigo in sorted(self.datos_configuracion.keys()):
            asignaturas_ordenadas[codigo] = self.datos_configuracion[codigo]

        self.datos_configuracion = asignaturas_ordenadas

    def auto_seleccionar_asignatura(self, codigo_asignatura):
        """Auto-seleccionar asignatura por código"""
        try:
            for i in range(self.list_asignaturas.count()):
                item = self.list_asignaturas.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == codigo_asignatura:
                    self.list_asignaturas.setCurrentItem(item)
                    self.seleccionar_asignatura(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando asignatura: {e}", "warning")

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
            self.log_mensaje("🔚 Cerrando configuración de asignaturas", "info")
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
                "asignaturas": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarAsignaturas",
                    "cambios_descartados": True
                }
            }

            self.configuracion_actualizada.emit(datos_para_sistema)
            self.datos_configuracion = datos_originales
            self.datos_guardados_en_sistema = False

            self.log_mensaje("📤 Cambios cancelados y estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cancelando cambios: {e}", "warning")

    def notificar_cambios_a_horarios(self):
        """Notificar cambios de asignaturas al módulo de horarios - IMPLEMENTACIÓN REAL"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'sincronizar_asignaturas_con_horarios'):
                # Preparar datos para horarios
                datos_para_horarios = {}

                for codigo, datos in self.datos_configuracion.items():
                    nombre = datos.get('nombre', codigo)
                    grados = datos.get('grados_que_cursan', [])

                    datos_para_horarios[nombre] = {
                        'codigo': codigo,
                        'grados': grados,
                        'horarios': {}  # Mantener horarios existentes
                    }

                # Notificar al sistema principal
                self.parent_window.sincronizar_asignaturas_con_horarios(datos_para_horarios)
                self.log_mensaje("📤 Cambios notificados al módulo de horarios", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error notificando cambios a horarios: {e}", "warning")

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
        "FIS001": {
            "codigo": "FIS001",
            "nombre": "Física I",
            "semestre": "1º Cuatrimestre",
            "curso": "1º Curso",
            "tipo": "Laboratorio",
            "descripcion": "Introducción a la física experimental",
            "grados_que_cursan": ["GII", "GIOI"],
            "configuracion_laboratorio": {
                "horas_por_sesion": 2,
                "max_estudiantes_grupo": 20,
                "equipamiento": "Osciloscopios, Generadores, Multímetros"
            },
            "planificacion": {
                "grupos_previstos": 6,
                "clases_año": 3
            },
            "estadisticas_calculadas": {
                "total_matriculados": 120,
                "con_lab_anterior": 30,
                "sin_lab_anterior": 90,
                "grupos_recomendados": 5,
                "ultima_actualizacion": datetime.now().isoformat()
            },
            "fecha_creacion": datetime.now().isoformat()
        },
        "QUI200": {
            "codigo": "QUI200",
            "nombre": "Química Orgánica",
            "semestre": "2º Cuatrimestre",
            "curso": "2º Curso",
            "tipo": "Laboratorio",
            "descripcion": "Síntesis y análisis de compuestos orgánicos",
            "grados_que_cursan": ["GIOI"],
            "configuracion_laboratorio": {
                "horas_por_sesion": 3,
                "max_estudiantes_grupo": 18,
                "equipamiento": "Campana extractora, Material químico, Balanzas"
            },
            "planificacion": {
                "grupos_previstos": 4,
                "clases_año": 2
            },
            "estadisticas_calculadas": {
                "total_matriculados": 80,
                "con_lab_anterior": 15,
                "sin_lab_anterior": 65,
                "grupos_recomendados": 4,
                "ultima_actualizacion": datetime.now().isoformat()
            },
            "fecha_creacion": datetime.now().isoformat()
        }
    }

    window = ConfigurarAsignaturas(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()