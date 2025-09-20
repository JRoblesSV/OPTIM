#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Alumnos - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (Universidad)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión completa de alumnos matriculados
2. Filtros por asignatura (desde configuración global)
3. Detección automática de alumnos en múltiples asignaturas
4. Estadísticas por asignatura y experiencia previa
5. Import/Export desde CSV con validación de datos
6. Integración completa con JSON global del sistema

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
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


class GestionAlumnoDialog(QDialog):
    """Dialog para añadir/editar alumno con gestión de asignaturas"""

    def __init__(self, alumno_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        self.alumno_existente = alumno_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {"1": {}, "2": {}}
        self.grados_disponibles = self.obtener_grados_del_sistema()
        self.setWindowTitle("Editar Alumno" if alumno_existente else "Nuevo Alumno")
        self.setModal(True)
        self.resize(700, 700)
        self.setup_ui()
        self.apply_dark_theme()

        if self.alumno_existente:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 👤 DATOS PERSONALES
        datos_personales_group = QGroupBox("👤 DATOS PERSONALES")
        datos_personales_layout = QFormLayout()

        # DNI
        self.edit_dni = QLineEdit()
        self.edit_dni.setPlaceholderText("Ej: 12345678A")
        self.edit_dni.setMaxLength(9)

        # Nombre
        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Ej: Juan")

        # Apellidos
        self.edit_apellidos = QLineEdit()
        self.edit_apellidos.setPlaceholderText("Ej: García López")

        # Email
        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("Ej: juan.garcia@alumnos.upm.es")

        datos_personales_layout.addRow("🆔 DNI:", self.edit_dni)
        datos_personales_layout.addRow("👤 Nombre:", self.edit_nombre)
        datos_personales_layout.addRow("👤 Apellidos:", self.edit_apellidos)
        datos_personales_layout.addRow("📧 Email:", self.edit_email)

        datos_personales_group.setLayout(datos_personales_layout)
        layout.addWidget(datos_personales_group)

        # 🎓 DATOS ACADÉMICOS
        datos_academicos_group = QGroupBox("🎓 DATOS ACADÉMICOS")
        datos_academicos_layout = QFormLayout()

        # Número de matrícula
        self.edit_matricula = QLineEdit()
        self.edit_matricula.setPlaceholderText("Ej: 2024000123")

        # Año matrícula (campo libre, no combo limitado)
        self.edit_ano_matricula = QLineEdit()
        self.edit_ano_matricula.setPlaceholderText("Ej: 2024")
        self.edit_ano_matricula.setMaxLength(4)

        # Grupo matrícula
        grados_group = QGroupBox("🎓 GRADOS MATRICULADO")
        grados_layout = QVBoxLayout()

        if self.grados_disponibles:
            info_grados = QLabel("Selecciona los grados en los que está matriculado:")
            info_grados.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 8px;")
            grados_layout.addWidget(info_grados)

            # Diccionario para checkboxes de grados
            self.checks_grados = {}

            for grado in self.grados_disponibles:
                check_grado = QCheckBox(grado)
                check_grado.toggled.connect(self.filtrar_asignaturas_por_grados)
                self.checks_grados[grado] = check_grado
                grados_layout.addWidget(check_grado)
        else:
            no_grados_label = QLabel("⚠️ No hay grados configurados en el sistema.")
            no_grados_label.setStyleSheet("color: #ffaa00; font-style: italic; padding: 10px;")
            grados_layout.addWidget(no_grados_label)
            self.checks_grados = {}

        grados_group.setLayout(grados_layout)
        layout.addWidget(grados_group)

        datos_academicos_layout.addRow("📋 N° Matrícula:", self.edit_matricula)
        datos_academicos_layout.addRow("📅 Año Matrícula:", self.edit_ano_matricula)

        datos_academicos_group.setLayout(datos_academicos_layout)
        layout.addWidget(datos_academicos_group)

        # 📚 ASIGNATURAS MATRICULADAS
        asignaturas_group = QGroupBox("📚 ASIGNATURAS MATRICULADAS")
        asignaturas_layout = QVBoxLayout()

        if self.tiene_asignaturas_disponibles():
            info_label = QLabel("Selecciona las asignaturas matriculadas y marca si ya aprobó el laboratorio:")
            info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 8px;")
            asignaturas_layout.addWidget(info_label)

            # Diccionarios para checkboxes
            self.checks_asignaturas = {}
            self.checks_lab_aprobado = {}

            # Organizar por semestre
            asignaturas_sem1 = self.asignaturas_disponibles.get("1", {})
            asignaturas_sem2 = self.asignaturas_disponibles.get("2", {})

            if asignaturas_sem1:
                sem1_label = QLabel("📋 1º Cuatrimestre:")
                sem1_label.setStyleSheet("color: #4a9eff; font-weight: bold; margin-top: 8px;")
                asignaturas_layout.addWidget(sem1_label)

                for asignatura in sorted(asignaturas_sem1.keys()):
                    self.crear_fila_asignatura(asignatura, "1", asignaturas_layout)

            if asignaturas_sem2:
                sem2_label = QLabel("📋 2º Cuatrimestre:")
                sem2_label.setStyleSheet("color: #4a9eff; font-weight: bold; margin-top: 8px;")
                asignaturas_layout.addWidget(sem2_label)

                for asignatura in sorted(asignaturas_sem2.keys()):
                    self.crear_fila_asignatura(asignatura, "2", asignaturas_layout)
        else:
            # No hay asignaturas configuradas
            no_asig_label = QLabel("⚠️ No hay asignaturas configuradas en el sistema.\n"
                                   "Configure primero los horarios para poder matricular alumnos.")
            no_asig_label.setStyleSheet("color: #ffaa00; font-style: italic; padding: 10px;")
            no_asig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            asignaturas_layout.addWidget(no_asig_label)
            self.checks_asignaturas = {}
            self.checks_lab_aprobado = {}

        asignaturas_group.setLayout(asignaturas_layout)
        layout.addWidget(asignaturas_group)

        # 📋 EXPEDIENTES
        expedientes_group = QGroupBox("📋 EXPEDIENTES")
        expedientes_layout = QFormLayout()

        # N° Expediente Centro
        self.edit_exp_centro = QLineEdit()
        self.edit_exp_centro.setPlaceholderText("Ej: GIN-14")

        # N° Expediente Ágora
        self.edit_exp_agora = QLineEdit()
        self.edit_exp_agora.setPlaceholderText("Ej: AGR789012")

        expedientes_layout.addRow("🏫 N° Exp. Centro:", self.edit_exp_centro)
        expedientes_layout.addRow("🌐 N° Exp. Ágora:", self.edit_exp_agora)

        expedientes_group.setLayout(expedientes_layout)
        layout.addWidget(expedientes_group)

        # 📝 OBSERVACIONES
        observaciones_group = QGroupBox("📝 OBSERVACIONES")
        observaciones_layout = QVBoxLayout()

        self.edit_observaciones = QTextEdit()
        self.edit_observaciones.setMaximumHeight(80)
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

    def obtener_grados_del_sistema(self):
        """Obtener códigos de grupos disponibles desde el sistema global"""
        try:
            if self.parent() and hasattr(self.parent(), 'parent_window'):
                parent_window = self.parent().parent_window
                if parent_window and hasattr(parent_window, 'configuracion'):
                    config_asignaturas = parent_window.configuracion["configuracion"]["asignaturas"]
                    if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                        codigos_grupos = set()
                        for asig_data in config_asignaturas["datos"].values():
                            # CAMBIO: buscar en "grupos" en lugar de "grados"
                            grupos_asig = asig_data.get("grupos", [])
                            codigos_grupos.update(grupos_asig)
                        return sorted(list(codigos_grupos))
            return []
        except Exception as e:
            print(f"Error obteniendo códigos de grupos: {e}")
            return []

    def filtrar_asignaturas_por_grados(self):
        """Filtrar asignaturas disponibles según códigos de grupos seleccionados"""
        # Obtener códigos de grupos seleccionados
        grupos_seleccionados = [grupo for grupo, check in self.checks_grados.items() if check.isChecked()]

        # Limpiar asignaturas actuales
        self.limpiar_checkboxes_asignaturas()

        if not grupos_seleccionados:
            # Si no hay grupos seleccionados, no mostrar asignaturas
            return

        # Filtrar asignaturas por códigos de grupos
        asignaturas_filtradas = {"1": {}, "2": {}}

        try:
            if self.parent() and hasattr(self.parent(), 'parent_window'):
                parent_window = self.parent().parent_window
                if parent_window and hasattr(parent_window, 'configuracion'):
                    config_asignaturas = parent_window.configuracion["configuracion"]["asignaturas"]
                    if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                        for codigo, asig_data in config_asignaturas["datos"].items():
                            nombre_asig = asig_data.get("nombre", "")
                            semestre = asig_data.get("semestre", "1")
                            # buscar en "grupos"
                            grupos_asig = asig_data.get("grupos", [])

                            # Si la asignatura pertenece a algún grupo seleccionado
                            if any(grupo in grupos_asig for grupo in grupos_seleccionados):
                                asignaturas_filtradas[str(semestre)][nombre_asig] = asig_data

        except Exception as e:
            print(f"Error filtrando asignaturas por grupos: {e}")

        # Actualizar asignaturas disponibles temporalmente
        self.asignaturas_filtradas = asignaturas_filtradas

        # Recrear checkboxes de asignaturas
        self.crear_checkboxes_asignaturas(asignaturas_filtradas)

    def limpiar_checkboxes_asignaturas(self):
        """Limpiar checkboxes de asignaturas existentes"""
        # Buscar el groupbox de asignaturas y limpiar su contenido
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox) and "ASIGNATURAS MATRICULADAS" in widget.title():
                # Limpiar el layout interno
                layout_asig = widget.layout()
                if layout_asig:
                    for j in reversed(range(layout_asig.count())):
                        child = layout_asig.itemAt(j)
                        if child.widget():
                            child.widget().deleteLater()
                        elif child.layout():
                            self.clear_layout(child.layout())
    def clear_layout(self, layout):
        """Limpiar un layout recursivamente"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def crear_checkboxes_asignaturas(self, asignaturas_data):
        """Recrear checkboxes de asignaturas basado en grados seleccionados"""
        # Buscar el groupbox de asignaturas
        asignaturas_group = None
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox) and "ASIGNATURAS MATRICULADAS" in widget.title():
                asignaturas_group = widget
                break

        if not asignaturas_group:
            return

        asignaturas_layout = asignaturas_group.layout()

        # Limpiar diccionarios
        self.checks_asignaturas = {}
        self.checks_lab_aprobado = {}

        if asignaturas_data.get("1") or asignaturas_data.get("2"):
            info_label = QLabel("Selecciona las asignaturas matriculadas y marca si ya aprobó el laboratorio:")
            info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 8px;")
            asignaturas_layout.addWidget(info_label)

            # 1º Cuatrimestre
            if asignaturas_data.get("1"):
                sem1_label = QLabel("📋 1º Cuatrimestre:")
                sem1_label.setStyleSheet("color: #4a9eff; font-weight: bold; margin-top: 8px;")
                asignaturas_layout.addWidget(sem1_label)

                for asignatura in sorted(asignaturas_data["1"].keys()):
                    self.crear_fila_asignatura(asignatura, "1", asignaturas_layout)

            # 2º Cuatrimestre
            if asignaturas_data.get("2"):
                sem2_label = QLabel("📋 2º Cuatrimestre:")
                sem2_label.setStyleSheet("color: #4a9eff; font-weight: bold; margin-top: 8px;")
                asignaturas_layout.addWidget(sem2_label)

                for asignatura in sorted(asignaturas_data["2"].keys()):
                    self.crear_fila_asignatura(asignatura, "2", asignaturas_layout)
        else:
            no_asig_label = QLabel("⚠️ Selecciona primero los grados para ver las asignaturas disponibles.")
            no_asig_label.setStyleSheet("color: #ffaa00; font-style: italic; padding: 10px;")
            no_asig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            asignaturas_layout.addWidget(no_asig_label)

    def crear_fila_asignatura(self, asignatura, semestre, parent_layout):
        """Crea una fila con checkbox de asignatura + checkbox de lab aprobado"""
        fila_layout = QHBoxLayout()
        fila_layout.setContentsMargins(20, 2, 10, 2)

        # Checkbox principal de asignatura
        key_asignatura = f"{semestre}_{asignatura}"
        check_asignatura = QCheckBox(asignatura)
        check_asignatura.setMinimumWidth(200)
        self.checks_asignaturas[key_asignatura] = check_asignatura

        # Checkbox pequeño para lab aprobado
        check_lab = QCheckBox("🎓 Lab aprobado")
        check_lab.setStyleSheet("color: #90EE90; font-size: 10px;")
        check_lab.setEnabled(False)  # Inicialmente deshabilitado
        self.checks_lab_aprobado[key_asignatura] = check_lab

        # Conectar señal para habilitar/deshabilitar el checkbox de lab
        check_asignatura.toggled.connect(
            lambda checked, lab_check=check_lab: lab_check.setEnabled(checked)
        )
        check_asignatura.toggled.connect(
            lambda checked, lab_check=check_lab: lab_check.setChecked(False) if not checked else None
        )

        fila_layout.addWidget(check_asignatura)
        fila_layout.addWidget(check_lab)
        fila_layout.addStretch()

        parent_layout.addLayout(fila_layout)

    def tiene_asignaturas_disponibles(self):
        """Verificar si hay asignaturas disponibles"""
        sem1 = self.asignaturas_disponibles.get("1", {})
        sem2 = self.asignaturas_disponibles.get("2", {})
        return bool(sem1 or sem2)

    def cargar_datos_existentes(self):
        """Cargar datos del alumno existente con nueva estructura"""
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
        ano_matricula = datos.get('ano_matricula', '2024')
        self.edit_ano_matricula.setText(ano_matricula)
        grupos_matriculado = datos.get('grados_matriculado', [])

        # Marcar checkboxes de grupos
        for grupo, check in self.checks_grados.items():
            if grupo in grupos_matriculado:
                check.setChecked(True)

        # Filtrar asignaturas por grupos seleccionados ANTES de cargar asignaturas
        if grupos_matriculado:
            self.filtrar_asignaturas_por_grados()

        # Expedientes
        self.edit_exp_centro.setText(datos.get('exp_centro', ''))
        self.edit_exp_agora.setText(datos.get('exp_agora', ''))

        # Observaciones
        self.edit_observaciones.setText(datos.get('observaciones', ''))

        # Cargar asignaturas matriculadas y experiencia por asignatura
        asignaturas_matriculadas = datos.get('asignaturas_matriculadas', {})

        # Formato esperado: {"1_Fisica": {"matriculado": True, "lab_aprobado": False}, ...}
        for key, check_asig in self.checks_asignaturas.items():
            if key in asignaturas_matriculadas:
                info_asignatura = asignaturas_matriculadas[key]

                # Marcar asignatura como matriculada
                if info_asignatura.get('matriculado', False):
                    check_asig.setChecked(True)

                    # Habilitar y marcar checkbox de lab aprobado si corresponde
                    if key in self.checks_lab_aprobado:
                        self.checks_lab_aprobado[key].setEnabled(True)
                        self.checks_lab_aprobado[key].setChecked(info_asignatura.get('lab_aprobado', False))

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
            'ano_matricula': self.edit_ano_matricula.text().strip(),
            'grados_matriculado': [grupo for grupo, check in self.checks_grados.items() if check.isChecked()],

            # Asignaturas (nueva estructura)
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
        """Aplicar tema oscuro idéntico a configurar_aulas"""
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
        """)


class ConfigurarAlumnos(QMainWindow):
    """Ventana principal para configurar alumnos matriculados"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Alumnos - OPTIM Labs")
        self.setGeometry(100, 100, 1400, 700)

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
                config_horarios = self.parent_window.configuracion["configuracion"]["horarios"]
                if config_horarios.get("configurado") and config_horarios.get("datos"):
                    return config_horarios["datos"]
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

        self.check_solo_sin_lab = QCheckBox("Solo sin lab anterior")
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

        # Nombre del alumno seleccionado
        self.label_alumno_actual = QLabel("Seleccione un alumno")
        self.label_alumno_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_alumno_actual)

        # Información detallada
        self.info_alumno = QTextEdit()
        self.info_alumno.setMaximumHeight(250)
        self.info_alumno.setReadOnly(True)
        self.info_alumno.setText("ℹ️ Seleccione un alumno para ver sus detalles")
        center_layout.addWidget(self.info_alumno)

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

        self.btn_duplicar = QPushButton("📋 Duplicar Alumno Seleccionado")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_alumno_seleccionado)
        acciones_layout.addWidget(self.btn_duplicar)

        self.btn_marcar_lab_anterior = QPushButton("🎓 Marcar sin Lab Anterior")
        self.btn_marcar_lab_anterior.setEnabled(False)
        self.btn_marcar_lab_anterior.clicked.connect(self.toggle_lab_anterior)
        acciones_layout.addWidget(self.btn_marcar_lab_anterior)

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
        """Aplicar tema oscuro idéntico a configurar_horarios"""
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
        """Aplicar filtro por asignatura y experiencia con nueva estructura - FILTRO CONTEXTUAL CORREGIDO"""
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
            grupos_matriculado = datos.get('grados_matriculado', [])
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
            self.btn_marcar_lab_anterior.setEnabled(False)
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
        info += f"📅 Año: {datos.get('fecha_matricula', 'No definido')[:4] if datos.get('fecha_matricula') else 'No definido'}\n"
        grupos_matriculado = datos.get('grados_matriculado', [])
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
        self.btn_marcar_lab_anterior.setEnabled(True)

        # Actualizar botón de experiencia
        tiene_lab_anterior = datos.get('lab_anterior', False)
        texto_boton = "🎓 Marcar sin Lab Anterior" if tiene_lab_anterior else "📝 Marcar con Lab Anterior"
        self.btn_marcar_lab_anterior.setText(texto_boton)

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
            self.btn_marcar_lab_anterior.setEnabled(False)
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
        letras = "BCDEFGHIJKLMNPQRSTUVWXYZ"
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
                                f"• 1º Cuatrimestre: {sem1_count} asignaturas\n"
                                f"• 2º Cuatrimestre: {sem2_count} asignaturas")

    def actualizar_estadisticas(self):
        """Actualizar estadísticas por asignatura con nueva estructura"""
        if not self.datos_configuracion:
            self.texto_stats.setText("📊 No hay alumnos para generar estadísticas")
            return

        # Estadísticas generales
        total_alumnos = len(self.datos_configuracion)

        # Contar alumnos con experiencia global
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
            import pandas as pd

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
            import pandas as pd

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
            self.btn_marcar_lab_anterior.setEnabled(False)

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
            self.btn_marcar_lab_anterior.setEnabled(False)
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
            "ano_matricula": "2024",
            "grados_matriculado": ["A202", "B204"],
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
            "ano_matricula": "2024",
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

    window = ConfigurarAlumnos(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()