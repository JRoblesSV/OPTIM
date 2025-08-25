#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Asignaturas - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Gestión integral de asignaturas con datos académicos completos
2. Configuración dinámica de grupos que cursan cada asignatura
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


class GestionAsignaturaDialog(QDialog):
    """Dialog para añadir/editar asignatura con configuración completa"""

    def __init__(self, asignatura_existente=None, alumnos_disponibles=None, aulas_disponibles=None, grupos_disponibles=None, parent=None):
        super().__init__(parent)
        self.asignatura_existente = asignatura_existente
        self.grupos_disponibles = grupos_disponibles or {}
        self.alumnos_disponibles = alumnos_disponibles or {}
        self.aulas_disponibles = aulas_disponibles or {}
        self.parent_window = parent
        self.setWindowTitle("Editar Asignatura" if asignatura_existente else "Nueva Asignatura")
        self.setModal(True)
        self.return_curso_anterior = None
        self.flag_para_return_curso_anterior = False

        # Variables para gestión de grupos y configuración por grupo
        self.configuraciones_grupo = {}  # Cache de configuraciones por grupo

        window_width = 700
        window_height = 800
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

        # Forzar tamaños iguales de ok/cancel
        QTimer.singleShot(50, self.igualar_tamanos_botones_ok_cancel)

        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)

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
        self.combo_semestre.addItems(["1º Semestre", "2º Semestre"])

        self.combo_curso = QComboBox()
        self.combo_curso.addItems(["1º Curso", "2º Curso", "3º Curso", "4º Curso"])

        self.combo_curso.currentTextChanged.connect(self.validar_cambio_curso)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Laboratorio", "Teórica"])

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

        # Gestión dinámica de grupos (como en configurar_horarios.py)
        grupos_group = QGroupBox("🎓 GRUPOS QUE CURSAN ESTA ASIGNATURA")
        grupos_layout = QVBoxLayout()

        # Header con botones de gestión
        grupos_header = QHBoxLayout()
        grupos_header.addWidget(QLabel("Grupos:"))
        grupos_header.addStretch()

        btn_add_grupo = QPushButton("➕")
        btn_add_grupo.setMinimumSize(30, 25)
        btn_add_grupo.setMaximumSize(40, 40)
        btn_add_grupo.setStyleSheet(self.get_button_style("#4CAF50"))
        btn_add_grupo.setToolTip("Añadir nuevo grupo")
        btn_add_grupo.clicked.connect(self.anadir_grupo)
        grupos_header.addWidget(btn_add_grupo)

        #btn_edit_grupo = QPushButton("✏️")
        #btn_edit_grupo.setMinimumSize(30, 25)
        #btn_edit_grupo.setMaximumSize(40, 40)
        #btn_edit_grupo.setStyleSheet(self.get_button_style("#2196F3"))
        #btn_edit_grupo.setToolTip("Editar grupo seleccionado")
        #btn_edit_grupo.clicked.connect(self.editar_grupo_seleccionado)
        #grupos_header.addWidget(btn_edit_grupo)

        btn_delete_grupo = QPushButton("🗑️")
        btn_delete_grupo.setMinimumSize(30, 25)
        btn_delete_grupo.setMaximumSize(40, 40)
        btn_delete_grupo.setStyleSheet(self.get_button_style("#f44336"))
        btn_delete_grupo.setToolTip("Eliminar grupo seleccionado")
        btn_delete_grupo.clicked.connect(self.eliminar_grupo_seleccionado)
        grupos_header.addWidget(btn_delete_grupo)

        grupos_layout.addLayout(grupos_header)

        # Lista dinámica de grupos
        self.list_grupos_dialog = QListWidget()
        self.list_grupos_dialog.setMaximumHeight(120)
        self.list_grupos_dialog.itemSelectionChanged.connect(self.grupo_seleccionado_cambio)
        grupos_layout.addWidget(self.list_grupos_dialog)

        info_grupos = QLabel("💡 Tip: Gestiona los grupos dinámicamente con los botones de arriba")
        info_grupos.setStyleSheet("color: #cccccc; font-size: 10px; font-style: italic;")
        grupos_layout.addWidget(info_grupos)

        grupos_group.setLayout(grupos_layout)
        layout.addWidget(grupos_group)

        # Configuración de laboratorio
        # Planificación del grupo
        planificacion_group = QGroupBox("📊 PLANIFICACIÓN DEL GRUPO")
        planificacion_layout = QVBoxLayout()

        # Configuración específica del grupo
        config_grupo_layout = QFormLayout()

        # Duración por sesión
        duracion_layout = QHBoxLayout()
        self.spin_horas_sesion = QSpinBox()
        self.spin_horas_sesion.setRange(0, 8)
        self.spin_horas_sesion.setValue(2)
        self.spin_horas_sesion.setSuffix(" h")
        duracion_layout.addWidget(self.spin_horas_sesion)

        self.spin_minutos_sesion = QSpinBox()
        self.spin_minutos_sesion.setRange(0, 45)
        self.spin_minutos_sesion.setSingleStep(15)
        self.spin_minutos_sesion.setValue(0)
        self.spin_minutos_sesion.setSuffix(" min")
        duracion_layout.addWidget(self.spin_minutos_sesion)

        duracion_layout.addWidget(QLabel("por sesión"))
        duracion_layout.addStretch()

        # Número de grupos previstos
        grupos_layout = QHBoxLayout()
        self.spin_grupos_previstos = QSpinBox()
        self.spin_grupos_previstos.setRange(1, 20)
        self.spin_grupos_previstos.setValue(6)
        self.spin_grupos_previstos.setSuffix("")
        grupos_layout.addWidget(self.spin_grupos_previstos)
        grupos_layout.addWidget(QLabel(""))
        grupos_layout.addStretch()

        # Número de clases en el año
        clases_layout = QHBoxLayout()
        self.spin_clases_año = QSpinBox()
        self.spin_clases_año.setRange(1, 15)
        self.spin_clases_año.setValue(3)
        clases_layout.addWidget(self.spin_clases_año)
        clases_layout.addWidget(QLabel("durante el semestre"))
        clases_layout.addStretch()

        # Estadísticas del grupo
        #self.label_alumnos_grupo = QLabel("👨‍🎓 Alumnos: 0 alumnos")
        #self.label_alumnos_grupo.setStyleSheet("color: #cccccc; font-size: 11px;")

        config_grupo_layout.addRow("⏱️ Duración:", duracion_layout)
        config_grupo_layout.addRow("👥 Grupos de alumnos:", grupos_layout)
        config_grupo_layout.addRow("📅 Número prácticas:", clases_layout)
        #config_grupo_layout.addRow("👨‍🎓 Alumnos:", con_lab_anterior)

        planificacion_layout.addLayout(config_grupo_layout)
        planificacion_group.setLayout(planificacion_layout)
        layout.addWidget(planificacion_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def grupo_seleccionado_cambio(self):
        """Cambiar configuración cuando se selecciona otro grupo"""
        item_actual = self.list_grupos_dialog.currentItem()
        if not item_actual:
            return

        # Guardar configuración del grupo anterior si existe
        if hasattr(self, 'grupo_anterior') and self.grupo_anterior and hasattr(self, 'configuraciones_grupo'):
            self.configuraciones_grupo[self.grupo_anterior] = {
                'horas_por_sesion': self.spin_horas_sesion.value(),
                'minutos_por_sesion': self.spin_minutos_sesion.value(),
                'grupos_previstos': self.spin_grupos_previstos.value(),
                'clases_año': self.spin_clases_año.value()
            }

        # Cargar nuevo grupo
        codigo_grupo = item_actual.data(Qt.ItemDataRole.UserRole)
        self.grupo_anterior = codigo_grupo
        self.actualizar_titulo_planificacion(codigo_grupo)
        self.cargar_configuracion_grupo(codigo_grupo)

    def actualizar_titulo_planificacion(self, codigo_grupo=None):
        """Actualizar título con el grupo seleccionado"""
        for child in self.findChildren(QGroupBox):
            if "PLANIFICACIÓN" in child.title():
                if codigo_grupo:
                    child.setTitle(f"📊 PLANIFICACIÓN DEL GRUPO - {codigo_grupo}")
                else:
                    child.setTitle("📊 PLANIFICACIÓN DEL GRUPO")
                break

    def guardar_configuracion_grupo(self, codigo_grupo):
        """Guardar configuración actual del grupo"""
        if not hasattr(self, 'configuraciones_grupo'):
            self.configuraciones_grupo = {}

        self.configuraciones_grupo[codigo_grupo] = {
            'horas_por_sesion': self.spin_horas_sesion.value(),
            'minutos_por_sesion': self.spin_minutos_sesion.value(),
            'grupos_previstos': self.spin_grupos_previstos.value(),
            'clases_año': self.spin_clases_año.value()
        }

    def cargar_configuracion_grupo(self, codigo_grupo):
        """Cargar configuración del grupo seleccionado"""
        if not hasattr(self, 'configuraciones_grupo'):
            self.configuraciones_grupo = {}

        if codigo_grupo in self.configuraciones_grupo:
            config = self.configuraciones_grupo[codigo_grupo]
            self.spin_horas_sesion.setValue(config.get('horas_por_sesion', 2))
            self.spin_minutos_sesion.setValue(config.get('minutos_por_sesion', 0))
            self.spin_grupos_previstos.setValue(config.get('grupos_previstos', 6))
            self.spin_clases_año.setValue(config.get('clases_año', 3))
        else:
            # Valores por defecto para grupo nuevo
            self.spin_horas_sesion.setValue(2)
            self.spin_minutos_sesion.setValue(0)
            self.spin_grupos_previstos.setValue(6)
            self.spin_clases_año.setValue(3)

    def cargar_datos_existentes(self):
        """Cargar datos de la asignatura existente"""
        if not self.asignatura_existente:
            return

        datos = self.asignatura_existente
        self.edit_codigo.setText(datos.get('codigo', ''))
        self.edit_nombre.setText(datos.get('nombre', ''))

        # Semestre
        semestre = datos.get('semestre', '1º Semestre')
        index = self.combo_semestre.findText(semestre)
        if index >= 0:
            self.combo_semestre.setCurrentIndex(index)

        # Curso
        curso = datos.get('curso', '1º Curso')
        index = self.combo_curso.findText(curso)
        if index >= 0:
            # Desconectar temporalmente para evitar validación durante carga
            self.return_curso_anterior = curso
            self.combo_curso.currentTextChanged.disconnect()
            self.combo_curso.setCurrentIndex(index)
            self.combo_curso.currentTextChanged.connect(self.validar_cambio_curso)

        # Tipo
        tipo = datos.get('tipo', 'Laboratorio')
        index = self.combo_tipo.findText(tipo)
        if index >= 0:
            self.combo_tipo.setCurrentIndex(index)

        self.edit_descripcion.setText(datos.get('descripcion', ''))

        # Grupos (cargar en lista dinámica)
        grupos = datos.get('grupos_asociados', [])
        self.list_grupos_dialog.clear()
        for grupo in sorted(grupos):
            # Buscar nombre del grupo
            nombre_grupo = grupo
            if self.grupos_disponibles and grupo in self.grupos_disponibles:
                nombre_grupo = self.grupos_disponibles[grupo].get('nombre', grupo)

            texto_display = f"{grupo} - {nombre_grupo}"
            item = QListWidgetItem(texto_display)
            item.setData(Qt.ItemDataRole.UserRole, grupo)
            self.list_grupos_dialog.addItem(item)

        # Configuración laboratorio
        # Cargar configuraciones por grupo desde nueva estructura
        grupos_asociados = datos.get('grupos_asociados', {})
        if isinstance(grupos_asociados, dict):
            # Nueva estructura: cargar configuraciones por grupo
            for codigo_grupo, config_grupo in grupos_asociados.items():
                config_lab = config_grupo.get('configuracion_laboratorio', {})
                self.configuraciones_grupo[codigo_grupo] = {
                    'horas_por_sesion': config_lab.get('horas_por_sesion', 2),
                    'minutos_por_sesion': config_lab.get('minutos_por_sesion', 0),
                    'grupos_previstos': config_lab.get('grupos_previstos', 6),
                    'clases_año': config_lab.get('clases_año', 3)
                }

            # Seleccionar primer grupo automáticamente
            if grupos_asociados:
                primer_grupo = list(grupos_asociados.keys())[0]
                self.cargar_configuracion_grupo(primer_grupo)
                self.actualizar_titulo_planificacion(primer_grupo)

            # Auto-seleccionar primer grupo en la lista
            if self.list_grupos_dialog.count() > 0:
                primer_item = self.list_grupos_dialog.item(0)
                self.list_grupos_dialog.setCurrentItem(primer_item)

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

        # Validar que al menos un grupo esté seleccionado
        grupos_seleccionados = self.get_grupos_seleccionados()
        if not grupos_seleccionados:
            QMessageBox.warning(self, "Grupos requeridos",
                                "Debe seleccionar al menos un grupo que curse esta asignatura")
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
                    min-width: 30px;
                    min-height: 25px;
                    max-width: 40px;
                    max-height: 40px;
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

    def filtrar_grupos_por_nivel(self):
        """Filtrar grupos disponibles según el nivel de la asignatura"""
        if not self.grupos_disponibles:
            return []

        # Obtener el nivel del grupo seleccionado
        grupo_seleccionado = self.combo_curso.currentText()
        if not grupo_seleccionado:
            return []

        # Extraer el número del curso (1, 2, 3, 4)
        numero_curso = grupo_seleccionado[0]  # "1º Curso" -> "1"

        # Obtener grupos ya agregados
        grupos_ya_agregados = set()
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            grupos_ya_agregados.add(item.data(Qt.ItemDataRole.UserRole))

        # Filtrar grupos que coincidan con el patrón
        grupos_filtrados = []
        for codigo, datos in self.grupos_disponibles.items():
            # Saltar si ya está agregado
            if codigo in grupos_ya_agregados:
                continue

            # Verificar que el código tenga al menos 3 caracteres
            if len(codigo) < 3:
                continue

            # Buscar el número del grupo en las posiciones posibles
            encontrado = False

            # Verificar si es patrón L[numero]NN (1 letra + número + 2 números)
            if len(codigo) >= 3 and codigo[1] == numero_curso and codigo[1].isdigit():
                # Verificar que los últimos 2 caracteres sean números
                if codigo[2:].isdigit() and len(codigo[2:]) == 2:
                    encontrado = True

            # Verificar si es patrón LL[numero]NN (2 letras + número + 2 números)
            elif len(codigo) >= 4 and codigo[2] == numero_curso and codigo[2].isdigit():
                # Verificar que los últimos 2 caracteres sean números
                if codigo[3:].isdigit() and len(codigo[3:]) == 2:
                    encontrado = True

            if encontrado:
                nombre = datos.get('nombre', codigo)
                coordinador = datos.get('coordinador', 'Sin coordinador')
                grupos_filtrados.append((f"{codigo} - {nombre} ({coordinador})", codigo))

        return grupos_filtrados

    def filtrar_grupos_por_nivel_edicion(self, grupo_a_excluir):
        """Filtrar grupos disponibles para edición, excluyendo uno específico"""
        if not self.grupos_disponibles:
            return []

        # Obtener el nivel del grupo seleccionado
        grupo_seleccionado = self.combo_curso.currentText()
        if not grupo_seleccionado:
            return []

        # Extraer el número del curso (1, 2, 3, 4)
        numero_curso = grupo_seleccionado[0]  # "1º Curso" -> "1"

        # Obtener grupos ya agregados (excepto el que se está editando)
        grupos_ya_agregados = set()
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            codigo_item = item.data(Qt.ItemDataRole.UserRole)
            if codigo_item != grupo_a_excluir:
                grupos_ya_agregados.add(codigo_item)

        # Filtrar grupos que coincidan con el patrón
        grupos_filtrados = []
        for codigo, datos in self.grupos_disponibles.items():
            # Saltar si ya está agregado
            if codigo in grupos_ya_agregados:
                continue

            # Verificar que el código tenga al menos 3 caracteres
            if len(codigo) < 3:
                continue

            # Buscar el número del grupo en las posiciones posibles
            encontrado = False

            # Verificar si es patrón L[numero]NN (1 letra + número + 2 números)
            if len(codigo) >= 3 and codigo[1] == numero_curso and codigo[1].isdigit():
                # Verificar que los últimos 2 caracteres sean números
                if codigo[2:].isdigit() and len(codigo[2:]) == 2:
                    encontrado = True

            # Verificar si es patrón LL[numero]NN (2 letras + número + 2 números)
            elif len(codigo) >= 4 and codigo[2] == numero_curso and codigo[2].isdigit():
                # Verificar que los últimos 2 caracteres sean números
                if codigo[3:].isdigit() and len(codigo[3:]) == 2:
                    encontrado = True

            if encontrado:
                nombre = datos.get('nombre', codigo)
                coordinador = datos.get('coordinador', 'Sin coordinador')
                grupos_filtrados.append((f"{codigo} - {nombre} ({coordinador})", codigo))

        return grupos_filtrados

    def validar_cambio_curso(self):
        """Validar cambio de grupo y limpiar grupos incompatibles"""
        # Flag para return_curso_anterior
        if self.flag_para_return_curso_anterior:
            return

        # Solo validar si hay grupos agregados
        if self.list_grupos_dialog.count() == 0:
            return

        # Obtener grupos actuales
        grupos_actuales = []
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            grupos_actuales.append(item.text())

        # Obtener nivel actual
        grupo_seleccionado = self.combo_curso.currentText()
        if not grupo_seleccionado:
            return

        numero_curso = grupo_seleccionado[0]

        # Verificar grupos incompatibles
        grupos_incompatibles = []
        for codigo in grupos_actuales:
            if len(codigo) < 3:
                grupos_incompatibles.append(codigo)
                continue

            # Verificar patrones
            compatible = False

            # Patrón L[numero]NN
            if len(codigo) >= 3 and codigo[1] == numero_curso and codigo[1].isdigit():
                if codigo[2:].isdigit() and len(codigo[2:]) == 2:
                    compatible = True

            # Patrón LL[numero]NN
            elif len(codigo) >= 4 and codigo[2] == numero_curso and codigo[2].isdigit():
                if codigo[3:].isdigit() and len(codigo[3:]) == 2:
                    compatible = True

            if not compatible:
                grupos_incompatibles.append(codigo)

        # Actualizar curso_anterior cuando el cambio es exitoso (sin conflictos)
        if not grupos_incompatibles:
            self.curso_anterior = grupo_seleccionado

        # Si hay incompatibles, preguntar
        if grupos_incompatibles:
            respuesta = QMessageBox.question(
                self, "Grupos Incompatibles",
                f"Los grupos actuales no son compatibles con '{grupo_seleccionado}':\n"
                f"• {', '.join(grupos_incompatibles)}\n\n"
                f"¿Eliminar grupos incompatibles?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Eliminar grupos incompatibles
                for codigo in grupos_incompatibles:
                    for i in range(self.list_grupos_dialog.count()):
                        item = self.list_grupos_dialog.item(i)
                        if item.text() == codigo:
                            self.list_grupos_dialog.takeItem(i)
                            break
            else:
                # Usuario dijo No, restaurar curso anterior
                if self.return_curso_anterior:
                    self.flag_para_return_curso_anterior = True
                    index = self.combo_curso.findText(self.return_curso_anterior)
                    if index >= 0:
                        self.combo_curso.setCurrentIndex(index)
                    self.flag_para_return_curso_anterior = False

    def anadir_grupo(self):
        """Añadir nuevo grupo a la asignatura"""
        if not self.grupos_disponibles:
            QMessageBox.information(self, "Sin Grupos",
                                    "No hay grupos disponibles para asociar.\n"
                                    "Configure primero los grupos en el sistema.")
            return

        # Filtrar grupos según el nivel de la asignatura
        grupos_filtrados = self.filtrar_grupos_por_nivel()

        if not grupos_filtrados:
            curso_nivel = self.combo_curso.currentText()
            QMessageBox.information(self, "Sin Grupos Compatibles",
                                    f"No hay grupos disponibles para '{curso_nivel}'.\n"
                                    f"Los grupos deben seguir el patrón LL{curso_nivel[0]}NN\n"
                                    f"(ej: A{curso_nivel[0]}02, B{curso_nivel[0]}02)")
            return

        # Crear lista de opciones para el usuario
        opciones_grupos = [item[0] for item in grupos_filtrados]

        grupo, ok = QInputDialog.getItem(
            self, "Añadir Grupo",
            f"Seleccione un grupo para '{self.combo_curso.currentText()}':",
            opciones_grupos,
            0, False
        )

        if ok and grupo:
            codigo_grupo = grupo.split(' - ')[0]

            # Verificar si ya existe
            for i in range(self.list_grupos_dialog.count()):
                if self.list_grupos_dialog.item(i).data(Qt.ItemDataRole.UserRole) == codigo_grupo:
                    QMessageBox.warning(self, "Error", "Este grupo ya existe en la asignatura")
                    return

            # Buscar nombre del grupo para mostrar texto completo
            nombre_grupo = codigo_grupo
            if self.grupos_disponibles and codigo_grupo in self.grupos_disponibles:
                nombre_grupo = self.grupos_disponibles[codigo_grupo].get('nombre', codigo_grupo)

            texto_display = f"{codigo_grupo} - {nombre_grupo}"

            # Añadir a la lista
            item = QListWidgetItem(texto_display)
            item.setData(Qt.ItemDataRole.UserRole, codigo_grupo)
            self.list_grupos_dialog.addItem(item)

            # Ordenar alfabéticamente
            self.ordenar_grupos_lista()

            # Auto-seleccionar el grupo añadido
            self.auto_seleccionar_grupo_dialog(codigo_grupo)

            # Si es el primer grupo, auto-cargar su configuración
            if self.list_grupos_dialog.count() == 1:
                self.cargar_configuracion_grupo(codigo_grupo)
                self.actualizar_titulo_planificacion(codigo_grupo)

    def editar_grupo_seleccionado(self):
        """Editar grupo seleccionado"""
        item_actual = self.list_grupos_dialog.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grupo para editar")
            return

        codigo_original = item_actual.text()

        if not self.grupos_disponibles:
            QMessageBox.information(self, "Sin Grupos",
                                    "No hay grupos disponibles para cambiar.")
            return

        # Filtrar grupos según el nivel de la asignatura (excluyendo el actual)
        grupos_filtrados = self.filtrar_grupos_por_nivel_edicion(codigo_original)

        if not grupos_filtrados:
            curso_nivel = self.combo_curso.currentText()
            QMessageBox.information(self, "Sin Grupos Compatibles",
                                    f"No hay grupos disponibles para '{curso_nivel}'.\n"
                                    f"Los grupos deben seguir el patrón LL{curso_nivel[0]}NN\n"
                                    f"(ej: A{curso_nivel[0]}02, B{curso_nivel[0]}02)")
            return

        # Crear lista de opciones para el usuario
        opciones_grupos = [item[0] for item in grupos_filtrados]

        grupo, ok = QInputDialog.getItem(
            self, "Editar Grupo",
            f"Seleccione el nuevo grupo para '{self.combo_curso.currentText()}':",
            opciones_grupos,
            0, False
        )

        if ok and grupo:
            codigo_nuevo = grupo.split(' - ')[0]

            if codigo_nuevo == codigo_original:
                return

            # Verificar si ya existe
            for i in range(self.list_grupos_dialog.count()):
                if self.list_grupos_dialog.item(i).text() == codigo_nuevo:
                    QMessageBox.warning(self, "Error", "Este grupo ya existe en la asignatura")
                    return

            # Actualizar el item
            item_actual.setText(codigo_nuevo)
            item_actual.setData(Qt.ItemDataRole.UserRole, codigo_nuevo)

            # Ordenar alfabéticamente
            self.ordenar_grupos_lista()

            # Auto-seleccionar el grupo editado
            self.auto_seleccionar_grupo_dialog(codigo_nuevo)

    def eliminar_grupo_seleccionado(self):
        """Eliminar Grupo seleccionado"""
        item_actual = self.list_grupos_dialog.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grupo para eliminar")
            return

        grupo = item_actual.text()

        respuesta = QMessageBox.question(
            self, "Eliminar Grupo",
            f"¿Está seguro de eliminar el grupo '{grupo}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            row = self.list_grupos_dialog.row(item_actual)
            self.list_grupos_dialog.takeItem(row)

    def ordenar_grupos_lista(self):
        """Ordenar grupos alfabéticamente en la lista"""
        grupos_data = []
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            codigo = item.data(Qt.ItemDataRole.UserRole)
            texto = item.text()
            grupos_data.append((codigo, texto))

        # Limpiar y recargar ordenado
        self.list_grupos_dialog.clear()
        for codigo, texto in sorted(grupos_data):
            item = QListWidgetItem(texto)  # Mostrar texto completo
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_grupos_dialog.addItem(item)

    def get_grupos_seleccionados(self):
        """Obtener lista de grupos de la lista dinámica"""
        grupos = []
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            grupos.append(item.data(Qt.ItemDataRole.UserRole))
        return sorted(grupos)

    def auto_seleccionar_grupo_dialog(self, grupo):
        """Auto-seleccionar grupo en el dialog"""
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == grupo:
                self.list_grupos_dialog.setCurrentItem(item)
                break

    def get_datos_asignatura(self):
        """Obtener datos configurados"""
        # Guardar configuración del grupo actual si hay uno seleccionado
        item_actual = self.list_grupos_dialog.currentItem()
        if item_actual:
            codigo_grupo_actual = item_actual.data(Qt.ItemDataRole.UserRole)
            self.configuraciones_grupo[codigo_grupo_actual] = {
                'horas_por_sesion': self.spin_horas_sesion.value(),
                'minutos_por_sesion': self.spin_minutos_sesion.value(),
                'grupos_previstos': self.spin_grupos_previstos.value(),
                'clases_año': self.spin_clases_año.value()
            }

        # Generar estructura de grupos_asociados con configuración actual
        grupos_asociados = {}
        for codigo_grupo in self.get_grupos_seleccionados():
            config = self.configuraciones_grupo.get(codigo_grupo, {
                'horas_por_sesion': 2,
                'minutos_por_sesion': 0,
                'grupos_previstos': 6,
                'clases_año': 3
            })

            grupos_asociados[codigo_grupo] = {
                'configuracion_laboratorio': config,
                'estadisticas_calculadas': {
                    'total_matriculados': 0,
                    'con_lab_anterior': 0,
                    'sin_lab_anterior': 0,
                    'grupos_recomendados': 0,
                    'ultima_actualizacion': datetime.now().isoformat()
                }
            }

        return {
            'codigo': self.edit_codigo.text().strip().upper(),
            'nombre': self.edit_nombre.text().strip(),
            'semestre': self.combo_semestre.currentText(),
            'curso': self.combo_curso.currentText(),
            'tipo': self.combo_tipo.currentText(),
            'descripcion': self.edit_descripcion.toPlainText().strip(),
            'grupos_asociados': grupos_asociados,
            'estadisticas_calculadas': {
                'total_matriculados': 0,
                'con_lab_anterior': 0,
                'sin_lab_anterior': 0,
                'ultima_actualizacion': datetime.now().isoformat()
            },
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
        """Configurar estilos uniformes para botones OK/Cancel - SIN CAMBIAR TEXTO"""
        try:
            # Buscar el QDialogButtonBox
            button_box = self.findChild(QDialogButtonBox)
            if button_box:
                # Obtener botones específicos
                ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
                cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)

                # ✅ ESTILO UNIFORME PARA AMBOS BOTONES - MISMO COLOR DE FONDO
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
        self.grupos_disponibles = self.obtener_grupos_del_sistema()

        # Sistema de cambios pendientes para aplicar al guardar
        self.cambios_pendientes = {
            "asignaturas_eliminadas": [],
            "grupos_eliminados": [],
            "profesores_eliminados": [],
            "aulas_eliminadas": []
        }

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

    def obtener_grupos_del_sistema(self):
        """Obtener grupos configurados desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
                if config_grupos.get("configurado") and config_grupos.get("datos"):
                    return config_grupos["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"⚠️ Error obteniendo grupos del sistema: {e}", "warning")
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
            "ℹ️ Define las asignaturas, grupos que las cursan y configuración de laboratorio. Las estadísticas se actualizan desde los alumnos matriculados.")
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

        self.btn_calcular_grupos = QPushButton("📊 Recalcular Estadísticas")
        self.btn_calcular_grupos.clicked.connect(self.actualizar_estadisticas_desde_alumnos)
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
        """Aplicar tema oscuro idéntico al resto del sistema - CON TOOLTIPS"""
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
            /* TOOLTIPS CORREGIDOS */
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

            # Mostrar grupos que la cursan
            grupos = datos.get('grupos_asociados', [])
            if grupos:
                grupos_con_nombre = []
                for grupo in grupos:
                    # Buscar nombre del grupo
                    nombre_grupo = grupo
                    if grupo in self.grupos_disponibles:
                        nombre_grupo = self.grupos_disponibles[grupo].get('nombre', grupo)
                    grupos_con_nombre.append(f"{grupo} - {nombre_grupo}")
                grupos_str = ', '.join(grupos_con_nombre)
            else:
                grupos_str = 'Sin grupos'

            # Estadísticas
            stats = datos.get('estadisticas_calculadas', {})
            total_matriculados = stats.get('total_matriculados', 0)
            sin_lab_anterior = stats.get('sin_lab_anterior', 0)

            # Icono según estado
            icono = "📚" if tipo == "Laboratorio" else "📖"

            texto_item = f"{icono} {codigo} - {nombre}"
            if total_matriculados > 0:
                texto_item += f" ({sin_lab_anterior}/{total_matriculados} alumnos)"
            texto_item += f"\n    {semestre} | {grupos_str}"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_asignaturas.addItem(item)

    def seleccionar_asignatura(self, item):
        """Seleccionar asignatura y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.asignatura_actual = None
            self.btn_duplicar.setEnabled(False)
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
        info += f"🎓 Curso: {datos.get('grupo', 'No definido')}\n"
        info += f"📖 Tipo: {datos.get('tipo', 'No definido')}\n"
        info += f"📝 Descripción: {datos.get('descripcion', 'Sin descripción')}\n\n"

        # grupos que la cursan
        grupos = datos.get('grupos_asociados', [])
        if grupos:
            info += f"🎓 GRUPOS QUE LA CURSAN ({len(grupos)}):\n"
            for grupo in grupos:
                # Buscar nombre del grupo
                nombre_grupo = grupo
                if grupo in self.grupos_disponibles:
                    nombre_grupo = self.grupos_disponibles[grupo].get('nombre', grupo)
                info += f"  • {grupo} - {nombre_grupo}\n"
        else:
            info += f"🎓 GRUPOS: Sin grupos asignados\n"
        info += "\n"

        # Configuración laboratorio
        config_lab = datos.get('configuracion_laboratorio', {})
        info += f"🔬 CONFIGURACIÓN LABORATORIO:\n"
        horas = config_lab.get('horas_por_sesion', 0)
        minutos = config_lab.get('minutos_por_sesion', 0)
        info += f"• Duración: {horas}h {minutos}min por sesión\n"

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

    def sincronizar_con_grupos(self, asignatura_codigo, grupos_nuevos, grupos_eliminados):
        """Sincronizar cambios con módulo de grupos"""
        try:
            if not self.parent_window:
                return

            # Obtener configuración actual de grupos
            config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
            if not config_grupos.get("configurado") or not config_grupos.get("datos"):
                return

            datos_grupos = config_grupos["datos"]
            cambios_realizados = False

            # AÑADIR asignatura a grupos nuevos
            for grupo_codigo in grupos_nuevos:
                if grupo_codigo in datos_grupos:
                    asignaturas_actuales = datos_grupos[grupo_codigo].get("asignaturas_asociadas", [])
                    if asignatura_codigo not in asignaturas_actuales:
                        asignaturas_actuales.append(asignatura_codigo)
                        datos_grupos[grupo_codigo]["asignaturas_asociadas"] = sorted(asignaturas_actuales)
                        cambios_realizados = True

            # ELIMINAR asignatura de grupos eliminados
            for grupo_codigo in grupos_eliminados:
                if grupo_codigo in datos_grupos:
                    asignaturas_actuales = datos_grupos[grupo_codigo].get("asignaturas_asociadas", [])
                    if asignatura_codigo in asignaturas_actuales:
                        asignaturas_actuales.remove(asignatura_codigo)
                        datos_grupos[grupo_codigo]["asignaturas_asociadas"] = sorted(asignaturas_actuales)
                        cambios_realizados = True

            # Actualizar configuración si hubo cambios
            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["grupos"]["datos"] = datos_grupos
                self.parent_window.configuracion["configuracion"]["grupos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"🔄 Sincronizados grupos desde asignatura {asignatura_codigo}", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error sincronizando con grupos: {e}", "warning")

    def anadir_asignatura(self):
        """Añadir nueva asignatura - CON SINCRONIZACIÓN"""
        dialog = GestionAsignaturaDialog(None, self.alumnos_disponibles, self.aulas_disponibles, self.grupos_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_asignatura()
            codigo = datos['codigo']

            if codigo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe una asignatura con el código '{codigo}'")
                return

            # Añadir nueva asignatura
            self.datos_configuracion[codigo] = datos

            # SINCRONIZACIÓN: Notificar grupos añadidos
            grupos_nuevos = datos.get('grupos_asociados', [])
            if grupos_nuevos:
                self.sincronizar_con_grupos(codigo, grupos_nuevos, [])

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.auto_seleccionar_asignatura(codigo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Asignatura '{codigo} - {datos['nombre']}' añadida correctamente")

    def editar_asignatura_seleccionada(self):
        """Editar asignatura seleccionada - CON SINCRONIZACIÓN Y EDICIÓN EN CASCADA"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para editar")
            return

        datos_originales = self.datos_configuracion[self.asignatura_actual].copy()
        dialog = GestionAsignaturaDialog(datos_originales, self.alumnos_disponibles, self.aulas_disponibles,
                                         self.grupos_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_asignatura()
            codigo_nuevo = datos_nuevos['codigo']
            codigo_original = self.asignatura_actual

            # Si cambió el código, verificar que no exista
            if codigo_nuevo != codigo_original and codigo_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe una asignatura con el código '{codigo_nuevo}'")
                return

            # SINCRONIZACIÓN: Detectar cambios en grupos
            grupos_originales = set(datos_originales.get('grupos_asociados', []))
            grupos_nuevos = set(datos_nuevos.get('grupos_asociados', []))

            grupos_añadidos = grupos_nuevos - grupos_originales
            grupos_eliminados = grupos_originales - grupos_nuevos

            # Preservar estadísticas existentes
            if 'estadisticas_calculadas' in datos_originales:
                datos_nuevos['estadisticas_calculadas'] = datos_originales['estadisticas_calculadas']

            # Actualizar datos localmente
            if codigo_nuevo != codigo_original:
                del self.datos_configuracion[codigo_original]
                self.asignatura_actual = codigo_nuevo

            self.datos_configuracion[codigo_nuevo] = datos_nuevos

            # EDICIÓN EN CASCADA: Si cambió el código, aplicar cambios
            if codigo_nuevo != codigo_original:
                self.editar_asignatura_real_completa(codigo_original, codigo_nuevo)

            # SINCRONIZACIÓN: Aplicar cambios de grupos
            if grupos_añadidos or grupos_eliminados:
                self.sincronizar_con_grupos(codigo_nuevo, grupos_añadidos, grupos_eliminados)

            # Auto-ordenar
            self.ordenar_asignaturas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_asignaturas()
            self.auto_seleccionar_asignatura(codigo_nuevo)
            self.marcar_cambio_realizado()

            if codigo_nuevo != codigo_original:
                QMessageBox.information(self, "Éxito",
                                        f"Asignatura editada: {codigo_original} → {codigo_nuevo}\n"
                                        f"Se aplicará el cambio en cascada al guardar los datos")
            else:
                QMessageBox.information(self, "Éxito", f"Asignatura actualizada correctamente")

    def editar_asignatura_real_completa(self, codigo_original, codigo_nuevo):
        """Editar asignatura realmente del sistema completo en cascada"""
        try:
            if not self.parent_window:
                self.log_mensaje(f"⚠️ No se puede editar {codigo_original}: sin parent_window", "warning")
                return

            # Obtener datos de la asignatura después de editar
            datos_asignatura = self.datos_configuracion.get(codigo_nuevo)  # Ya actualizado localmente
            if not datos_asignatura:
                self.log_mensaje(f"⚠️ Asignatura {codigo_nuevo} no encontrada en configuración", "warning")
                return

            grupos_asociados = datos_asignatura.get('grupos_asociados', [])

            self.log_mensaje(f"✏️ Editando asignatura {codigo_original} → {codigo_nuevo} del sistema completo...", "info")

            # 1. Editar en grupos
            self.editar_asignatura_en_grupos_sistema(codigo_original, codigo_nuevo, grupos_asociados)

            # 2. Editar en profesores
            self.editar_asignatura_en_profesores_sistema(codigo_original, codigo_nuevo)

            # 3. Editar en alumnos
            self.editar_asignatura_en_alumnos_sistema(codigo_original, codigo_nuevo)

            # 4. Editar en horarios
            self.editar_asignatura_en_horarios_sistema(codigo_original, codigo_nuevo)

            # 5. Editar en aulas
            self.editar_asignatura_en_aulas_sistema(codigo_original, codigo_nuevo)

            # 6. Editar en configuración de asignaturas del sistema
            self.editar_asignatura_en_asignaturas_sistema(codigo_original, codigo_nuevo)

            self.log_mensaje(f"✅ Asignatura {codigo_original} → {codigo_nuevo} editada completamente del sistema",
                             "success")

        except Exception as e:
            self.log_mensaje(f"❌ Error en edición completa de asignatura {codigo_original}: {e}", "error")

    def editar_asignatura_en_grupos_sistema(self, codigo_original, codigo_nuevo, grupos_asociados):
        """Editar código de asignatura en el sistema de grupos"""
        try:
            config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
            if not config_grupos.get("configurado") or not config_grupos.get("datos"):
                return

            datos_grupos = config_grupos["datos"]
            cambios_realizados = False

            # Procesar todos los grupos que cursan esta asignatura
            for grupo_codigo in grupos_asociados:
                if grupo_codigo in datos_grupos:
                    asignaturas_asociadas = datos_grupos[grupo_codigo].get("asignaturas_asociadas", [])
                    if codigo_original in asignaturas_asociadas:
                        # Reemplazar código antiguo por nuevo
                        indice = asignaturas_asociadas.index(codigo_original)
                        asignaturas_asociadas[indice] = codigo_nuevo
                        datos_grupos[grupo_codigo]["asignaturas_asociadas"] = sorted(asignaturas_asociadas)
                        cambios_realizados = True
                        self.log_mensaje(f"🔄 Asignatura {codigo_original} → {codigo_nuevo} editada en grupo {grupo_codigo}",
                                         "info")

            # Buscar en TODOS los grupos por si hay referencias huérfanas
            for grupo_codigo, grupo_data in datos_grupos.items():
                asignaturas_asociadas = grupo_data.get("asignaturas_asociadas", [])
                if codigo_original in asignaturas_asociadas:
                    # Reemplazar código antiguo por nuevo
                    indice = asignaturas_asociadas.index(codigo_original)
                    asignaturas_asociadas[indice] = codigo_nuevo
                    grupo_data["asignaturas_asociadas"] = sorted(asignaturas_asociadas)
                    cambios_realizados = True
                    self.log_mensaje(
                        f"🔄 Asignatura {codigo_original} → {codigo_nuevo} editada en grupo {grupo_codigo} (referencia huérfana)",
                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["grupos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de grupos", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando asignatura en grupos: {e}", "warning")


    def editar_asignatura_en_profesores_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de asignatura en el sistema de profesores"""
        try:
            config_profesores = self.parent_window.configuracion["configuracion"].get("profesores", {})
            if not config_profesores.get("configurado") or not config_profesores.get("datos"):
                return

            datos_profesores = config_profesores["datos"]
            cambios_realizados = False

            for profesor_id, profesor_data in datos_profesores.items():
                # Editar en asignaturas_imparte
                if "asignaturas_imparte" in profesor_data:
                    asignaturas_imparte = profesor_data["asignaturas_imparte"]
                    if codigo_original in asignaturas_imparte:
                        # Reemplazar código antiguo por nuevo
                        indice = asignaturas_imparte.index(codigo_original)
                        asignaturas_imparte[indice] = codigo_nuevo
                        profesor_data["asignaturas_imparte"] = asignaturas_imparte
                        cambios_realizados = True
                        nombre_profesor = profesor_data.get("nombre", "Desconocido")
                        self.log_mensaje(
                            f"🔄 Asignatura {codigo_original} → {codigo_nuevo} editada en profesor {nombre_profesor} ({profesor_id})",
                            "info")

                # Editar en horarios_bloqueados si hay referencias específicas a la asignatura
                if "horarios_bloqueados" in profesor_data:
                    horarios_bloqueados = profesor_data["horarios_bloqueados"]
                    for dia, bloqueados in horarios_bloqueados.items():
                        if isinstance(bloqueados, dict):
                            for horario, motivo in bloqueados.items():
                                if isinstance(motivo, str) and codigo_original.lower() in motivo.lower():
                                    # Reemplazar en el motivo
                                    nuevo_motivo = motivo.replace(codigo_original, codigo_nuevo)
                                    bloqueados[horario] = nuevo_motivo
                                    cambios_realizados = True
                                    self.log_mensaje(
                                        f"🔄 Horario bloqueado de {codigo_original} → {codigo_nuevo} editado en profesor {profesor_id}",
                                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["profesores"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de profesores",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando asignatura en profesores: {e}", "warning")


    def editar_asignatura_en_alumnos_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de asignatura en el sistema de alumnos"""
        try:
            config_alumnos = self.parent_window.configuracion["configuracion"].get("alumnos", {})
            if not config_alumnos.get("configurado") or not config_alumnos.get("datos"):
                return

            datos_alumnos = config_alumnos["datos"]
            cambios_realizados = False
            alumnos_modificados = 0

            for alumno_codigo, alumno_data in datos_alumnos.items():
                # Editar codigo_asignatura si coincide
                if alumno_data.get("codigo_asignatura") == codigo_original:
                    alumno_data["codigo_asignatura"] = codigo_nuevo
                    cambios_realizados = True
                    alumnos_modificados += 1
                    nombre_alumno = alumno_data.get("nombre", "Desconocido")
                    self.log_mensaje(
                        f"🔄 Código de asignatura {codigo_original} → {codigo_nuevo} editado en alumno {nombre_alumno}",
                        "info")

                # Editar en asignaturas_matriculadas
                if "asignaturas_matriculadas" in alumno_data:
                    if codigo_original in alumno_data["asignaturas_matriculadas"]:
                        # Mover datos del código antiguo al nuevo
                        datos_asignatura = alumno_data["asignaturas_matriculadas"][codigo_original]
                        del alumno_data["asignaturas_matriculadas"][codigo_original]
                        alumno_data["asignaturas_matriculadas"][codigo_nuevo] = datos_asignatura
                        cambios_realizados = True
                        alumnos_modificados += 1
                        nombre_alumno = alumno_data.get("nombre", "Desconocido")
                        self.log_mensaje(
                            f"🔄 Asignatura {codigo_original} → {codigo_nuevo} editada en matriculadas del alumno {nombre_alumno}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["alumnos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"✅ Asignatura {codigo_original} → {codigo_nuevo} editada en {alumnos_modificados} referencias en alumnos",
                    "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando asignatura en alumnos: {e}", "warning")


    def editar_asignatura_en_horarios_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de asignatura en el sistema de horarios"""
        try:
            config_horarios = self.parent_window.configuracion["configuracion"].get("horarios", {})
            if not config_horarios.get("configurado") or not config_horarios.get("datos"):
                return

            datos_horarios = config_horarios["datos"]
            cambios_realizados = False

            # Buscar en ambos semestres
            for semestre in ["1", "2"]:
                if semestre in datos_horarios:
                    asignaturas_semestre = datos_horarios[semestre]

                    # Buscar la asignatura por código o nombre
                    asignatura_encontrada = None
                    datos_asignatura = None

                    # Buscar directamente por código
                    if codigo_original in asignaturas_semestre:
                        asignatura_encontrada = codigo_original
                        datos_asignatura = asignaturas_semestre[codigo_original]
                    else:
                        # Buscar por nombre de asignatura (usar datos actuales)
                        nombre_asignatura_original = self.datos_configuracion.get(codigo_nuevo, {}).get('nombre', '')
                        if nombre_asignatura_original and nombre_asignatura_original in asignaturas_semestre:
                            asignatura_encontrada = nombre_asignatura_original
                            datos_asignatura = asignaturas_semestre[nombre_asignatura_original]

                    # Editar asignatura si se encontró
                    if asignatura_encontrada and datos_asignatura:
                        # Eliminar con clave antigua
                        del asignaturas_semestre[asignatura_encontrada]

                        # Agregar con clave nueva (usar el nuevo código como clave)
                        asignaturas_semestre[codigo_nuevo] = datos_asignatura
                        cambios_realizados = True
                        self.log_mensaje(
                            f"🔄 Asignatura {asignatura_encontrada} → {codigo_nuevo} editada en semestre {semestre}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de horarios",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando asignatura en horarios: {e}", "warning")


    def editar_asignatura_en_aulas_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de asignatura en el sistema de aulas"""
        try:
            config_aulas = self.parent_window.configuracion["configuracion"].get("aulas", {})
            if not config_aulas.get("configurado") or not config_aulas.get("datos"):
                return

            datos_aulas = config_aulas["datos"]
            cambios_realizados = False

            for aula_nombre, aula_data in datos_aulas.items():
                # Editar en asignaturas_asociadas
                if "asignaturas_asociadas" in aula_data:
                    asignaturas_asociadas = aula_data["asignaturas_asociadas"]
                    if codigo_original in asignaturas_asociadas:
                        # Reemplazar código antiguo por nuevo
                        indice = asignaturas_asociadas.index(codigo_original)
                        asignaturas_asociadas[indice] = codigo_nuevo
                        aula_data["asignaturas_asociadas"] = asignaturas_asociadas
                        cambios_realizados = True
                        self.log_mensaje(f"🔄 Asignatura {codigo_original} → {codigo_nuevo} editada en aula {aula_nombre}",
                                         "info")

                # Editar ocupaciones relacionadas con la asignatura si existen
                if "ocupaciones_programadas" in aula_data:
                    for ocupacion in aula_data["ocupaciones_programadas"]:
                        if ocupacion.get("asignatura") == codigo_original:
                            ocupacion["asignatura"] = codigo_nuevo
                            cambios_realizados = True
                            self.log_mensaje(
                                f"🔄 Ocupación de {codigo_original} → {codigo_nuevo} editada en aula {aula_nombre}",
                                "info")
                        if ocupacion.get("codigo_asignatura") == codigo_original:
                            ocupacion["codigo_asignatura"] = codigo_nuevo
                            cambios_realizados = True
                            self.log_mensaje(
                                f"🔄 Código de ocupación {codigo_original} → {codigo_nuevo} editado en aula {aula_nombre}",
                                "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["aulas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de aulas", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando asignatura en aulas: {e}", "warning")


    def editar_asignatura_en_asignaturas_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de asignatura en el módulo de asignaturas del sistema"""
        try:
            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                datos_asignaturas = config_asignaturas["datos"]
                if codigo_original in datos_asignaturas and codigo_original != codigo_nuevo:
                    # Mover datos del código antiguo al nuevo
                    datos_asignaturas[codigo_nuevo] = datos_asignaturas[codigo_original]
                    del datos_asignaturas[codigo_original]

                    # Actualizar el código interno del objeto también
                    datos_asignaturas[codigo_nuevo]["codigo"] = codigo_nuevo

                    self.parent_window.configuracion["configuracion"]["asignaturas"][
                        "fecha_actualizacion"] = datetime.now().isoformat()
                    self.log_mensaje(f"🔄 Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de asignaturas",
                                     "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando asignatura en asignaturas: {e}", "warning")

    def eliminar_asignatura_seleccionada(self):
        """Marcar asignatura seleccionada para eliminación en cascada al guardar"""
        if not self.asignatura_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione una asignatura para eliminar")
            return

        datos = self.datos_configuracion[self.asignatura_actual]
        nombre = datos.get('nombre', 'Sin nombre')
        grupos_asociados = datos.get('grupos_asociados', [])

        mensaje = f"¿Está seguro de eliminar la asignatura '{self.asignatura_actual} - {nombre}'?\n\n"
        if grupos_asociados:
            mensaje += f"ADVERTENCIA: Esta asignatura está asociada a {len(grupos_asociados)} grupos.\n"
            mensaje += f"Se eliminará automáticamente de:\n"
            mensaje += f"  • Todos los grupos asociados ({', '.join(grupos_asociados)})\n"
            mensaje += f"  • Todos los profesores que la imparten\n"
            mensaje += f"  • Todos los alumnos matriculados\n"
            mensaje += f"  • Todos los horarios programados\n"
            mensaje += f"  • Todas las aulas con ocupaciones\n\n"
        mensaje += "La eliminación se aplicará al guardar en el sistema."

        # Confirmar eliminación
        respuesta = QMessageBox.question(self, "Confirmar Eliminación",
                                         mensaje,
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if respuesta == QMessageBox.StandardButton.Yes:
            asignatura_codigo = self.asignatura_actual

            # Marcar para eliminación en cascada
            if asignatura_codigo not in self.cambios_pendientes["asignaturas_eliminadas"]:
                self.cambios_pendientes["asignaturas_eliminadas"].append(asignatura_codigo)

            # Marcar visualmente como eliminada en la tabla
            self.marcar_asignatura_eliminada_en_tabla(asignatura_codigo)

            # Deshabilitar selección de la asignatura eliminada
            self.asignatura_actual = None
            self.label_asignatura_actual.setText("Asignatura marcada para eliminación")
            self.info_asignatura.setText("⚠️ Esta asignatura será eliminada al guardar en el sistema")
            self.btn_duplicar.setEnabled(False)
            self.marcar_cambio_realizado()

            self.log_mensaje(f"📝 Asignatura {asignatura_codigo} marcada para eliminación al guardar", "info")
            QMessageBox.information(self, "Marcada para Eliminación",
                                    f"Asignatura '{asignatura_codigo}' marcada para eliminación.\n\nLa eliminación se aplicará al guardar en el sistema.")

    def aplicar_eliminaciones_pendientes(self):
        """Aplicar todas las eliminaciones marcadas en cascada"""
        try:
            asignaturas_eliminadas = self.cambios_pendientes["asignaturas_eliminadas"].copy()

            if not asignaturas_eliminadas:
                return

            self.log_mensaje(f"🗑️ Aplicando eliminación en cascada de {len(asignaturas_eliminadas)} asignaturas...",
                             "info")

            # Eliminar cada asignatura marcada
            for asignatura_codigo in asignaturas_eliminadas:
                self.eliminar_asignatura_real_completa(asignatura_codigo)

            # Limpiar lista de eliminaciones pendientes
            self.cambios_pendientes["asignaturas_eliminadas"].clear()

            self.log_mensaje(f"✅ Eliminación en cascada completada para {len(asignaturas_eliminadas)} asignaturas",
                             "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error aplicando eliminaciones pendientes: {e}", "warning")

    def eliminar_asignatura_real_completa(self, asignatura_codigo):
        """Eliminar asignatura realmente del sistema completo en cascada"""
        try:
            if not self.parent_window:
                self.log_mensaje(f"⚠️ No se puede eliminar {asignatura_codigo}: sin parent_window", "warning")
                return

            # Obtener datos de la asignatura antes de eliminar
            datos_asignatura = self.datos_configuracion.get(asignatura_codigo)
            if not datos_asignatura:
                self.log_mensaje(f"⚠️ Asignatura {asignatura_codigo} no encontrada en configuración", "warning")
                return

            grupos_asociados = datos_asignatura.get('grupos_asociados', [])

            self.log_mensaje(f"🗑️ Eliminando asignatura {asignatura_codigo} del sistema completo...", "info")

            # 1. Eliminar de grupos: Pasar grupos_asociados
            self.eliminar_asignatura_de_grupos_sistema(asignatura_codigo, grupos_asociados)

            # 2. Eliminar de profesores
            self.eliminar_asignatura_de_profesores_sistema(asignatura_codigo)

            # 3. Eliminar de alumnos
            self.eliminar_asignatura_de_alumnos_sistema(asignatura_codigo)

            # 4. Eliminar de horarios
            self.eliminar_asignatura_de_horarios_sistema(asignatura_codigo)

            # 5. Eliminar de aulas
            self.eliminar_asignatura_de_aulas_sistema(asignatura_codigo)

            # 6. Eliminar de configuración de asignaturas del sistema
            self.eliminar_asignatura_de_asignaturas_sistema(asignatura_codigo)

            # 7. Eliminar de la configuración local
            if asignatura_codigo in self.datos_configuracion:
                del self.datos_configuracion[asignatura_codigo]

            self.log_mensaje(f"✅ Asignatura {asignatura_codigo} procesada para eliminación completa", "success")

        except Exception as e:
            self.log_mensaje(f"❌ Error en eliminación completa de asignatura {asignatura_codigo}: {e}", "error")

    def eliminar_asignatura_de_grupos_sistema(self, asignatura_codigo, grupos_asociados):
        """Eliminar asignatura del sistema de grupos"""
        try:
            config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
            if not config_grupos.get("configurado") or not config_grupos.get("datos"):
                return

            datos_grupos = config_grupos["datos"]
            cambios_realizados = False

            # Procesar todos los grupos que cursaban esta asignatura
            for grupo_codigo in grupos_asociados:
                if grupo_codigo in datos_grupos:
                    # CORREGIDO: Buscar en asignaturas_asociadas
                    asignaturas_asociadas = datos_grupos[grupo_codigo].get("asignaturas_asociadas", [])
                    if asignatura_codigo in asignaturas_asociadas:
                        asignaturas_asociadas.remove(asignatura_codigo)
                        datos_grupos[grupo_codigo]["asignaturas_asociadas"] = sorted(asignaturas_asociadas)
                        cambios_realizados = True
                        self.log_mensaje(f"🔄 Asignatura {asignatura_codigo} eliminada del grupo {grupo_codigo}", "info")

            # Buscar en TODOS los grupos por si hay referencias huérfanas
            for grupo_codigo, grupo_data in datos_grupos.items():
                asignaturas_asociadas = grupo_data.get("asignaturas_asociadas", [])
                if asignatura_codigo in asignaturas_asociadas:
                    asignaturas_asociadas.remove(asignatura_codigo)
                    grupo_data["asignaturas_asociadas"] = sorted(asignaturas_asociadas)
                    cambios_realizados = True
                    self.log_mensaje(
                        f"🔄 Asignatura {asignatura_codigo} eliminada del grupo {grupo_codigo} (referencia huérfana)",
                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["grupos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {asignatura_codigo} eliminada del módulo de grupos", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando asignatura de grupos: {e}", "warning")

    def eliminar_asignatura_de_profesores_sistema(self, asignatura_codigo):
        """Eliminar asignatura del sistema de profesores"""
        try:
            config_profesores = self.parent_window.configuracion["configuracion"].get("profesores", {})
            if not config_profesores.get("configurado") or not config_profesores.get("datos"):
                return

            datos_profesores = config_profesores["datos"]
            cambios_realizados = False

            for profesor_id, profesor_data in datos_profesores.items():
                # Buscar en asignaturas_imparte
                if "asignaturas_imparte" in profesor_data:
                    asignaturas_imparte = profesor_data["asignaturas_imparte"]
                    if asignatura_codigo in asignaturas_imparte:
                        asignaturas_imparte.remove(asignatura_codigo)
                        profesor_data["asignaturas_imparte"] = asignaturas_imparte
                        cambios_realizados = True
                        nombre_profesor = profesor_data.get("nombre", "Desconocido")
                        self.log_mensaje(
                            f"🔄 Asignatura {asignatura_codigo} eliminada del profesor {nombre_profesor} ({profesor_id})",
                            "info")

                # Eliminar de horarios_bloqueados si hay referencias específicas a la asignatura
                if "horarios_bloqueados" in profesor_data:
                    horarios_bloqueados = profesor_data["horarios_bloqueados"]
                    for dia, bloqueados in horarios_bloqueados.items():
                        if isinstance(bloqueados, dict):
                            bloqueados_a_eliminar = []
                            for horario, motivo in bloqueados.items():
                                if isinstance(motivo, str) and asignatura_codigo.lower() in motivo.lower():
                                    bloqueados_a_eliminar.append(horario)

                            for horario in bloqueados_a_eliminar:
                                del bloqueados[horario]
                                cambios_realizados = True
                                self.log_mensaje(
                                    f"🔄 Horario bloqueado de {asignatura_codigo} eliminado del profesor {profesor_id}",
                                    "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["profesores"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {asignatura_codigo} eliminada del módulo de profesores", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando asignatura de profesores: {e}", "warning")

    def eliminar_asignatura_de_alumnos_sistema(self, asignatura_codigo):
        """Eliminar asignatura del sistema de alumnos"""
        try:
            config_alumnos = self.parent_window.configuracion["configuracion"].get("alumnos", {})
            if not config_alumnos.get("configurado") or not config_alumnos.get("datos"):
                return

            datos_alumnos = config_alumnos["datos"]
            cambios_realizados = False
            alumnos_modificados = 0

            for alumno_codigo, alumno_data in datos_alumnos.items():
                # Eliminar de codigo_asignatura si coincide
                if alumno_data.get("codigo_asignatura") == asignatura_codigo:
                    alumno_data["codigo_asignatura"] = ""
                    cambios_realizados = True
                    alumnos_modificados += 1
                    nombre_alumno = alumno_data.get("nombre", "Desconocido")
                    self.log_mensaje(f"🔄 Código de asignatura {asignatura_codigo} eliminado del alumno {nombre_alumno}",
                                     "info")

                # Eliminar de asignaturas_matriculadas
                if "asignaturas_matriculadas" in alumno_data:
                    if asignatura_codigo in alumno_data["asignaturas_matriculadas"]:
                        del alumno_data["asignaturas_matriculadas"][asignatura_codigo]
                        cambios_realizados = True
                        alumnos_modificados += 1
                        nombre_alumno = alumno_data.get("nombre", "Desconocido")
                        self.log_mensaje(
                            f"🔄 Asignatura {asignatura_codigo} eliminada de matriculadas del alumno {nombre_alumno}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["alumnos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"✅ Asignatura {asignatura_codigo} eliminada de {alumnos_modificados} referencias en alumnos",
                    "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando asignatura de alumnos: {e}", "warning")

    def eliminar_asignatura_de_horarios_sistema(self, asignatura_codigo):
        """Eliminar asignatura del sistema de horarios con limpieza completa"""
        try:
            config_horarios = self.parent_window.configuracion["configuracion"].get("horarios", {})
            if not config_horarios.get("configurado") or not config_horarios.get("datos"):
                return

            datos_horarios = config_horarios["datos"]
            cambios_realizados = False

            # Buscar en ambos semestres
            for semestre in ["1", "2"]:
                if semestre in datos_horarios:
                    asignaturas_semestre = datos_horarios[semestre]

                    # Buscar la asignatura por código o nombre
                    asignatura_encontrada = None

                    # Buscar directamente por código
                    if asignatura_codigo in asignaturas_semestre:
                        asignatura_encontrada = asignatura_codigo
                    else:
                        # Buscar por nombre de asignatura
                        nombre_asignatura = self.datos_configuracion.get(asignatura_codigo, {}).get('nombre', '')
                        if nombre_asignatura and nombre_asignatura in asignaturas_semestre:
                            asignatura_encontrada = nombre_asignatura

                    # Eliminar asignatura completa si se encontró
                    if asignatura_encontrada:
                        del asignaturas_semestre[asignatura_encontrada]
                        cambios_realizados = True
                        self.log_mensaje(
                            f"🗑️ Asignatura {asignatura_encontrada} eliminada completamente del semestre {semestre}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {asignatura_codigo} eliminada completamente del módulo de horarios",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando asignatura de horarios: {e}", "warning")

    def eliminar_asignatura_de_aulas_sistema(self, asignatura_codigo):
        """Eliminar asignatura del sistema de aulas"""
        try:
            config_aulas = self.parent_window.configuracion["configuracion"].get("aulas", {})
            if not config_aulas.get("configurado") or not config_aulas.get("datos"):
                return

            datos_aulas = config_aulas["datos"]
            cambios_realizados = False

            for aula_nombre, aula_data in datos_aulas.items():
                # Buscar en asignaturas_asociadas
                if "asignaturas_asociadas" in aula_data:
                    asignaturas_asociadas = aula_data["asignaturas_asociadas"]
                    if asignatura_codigo in asignaturas_asociadas:
                        asignaturas_asociadas.remove(asignatura_codigo)
                        aula_data["asignaturas_asociadas"] = asignaturas_asociadas
                        cambios_realizados = True
                        self.log_mensaje(f"🔄 Asignatura {asignatura_codigo} eliminada del aula {aula_nombre}", "info")

                # Eliminar ocupaciones relacionadas con la asignatura si existen
                if "ocupaciones_programadas" in aula_data:
                    ocupaciones_originales = len(aula_data["ocupaciones_programadas"])
                    aula_data["ocupaciones_programadas"] = [
                        ocup for ocup in aula_data["ocupaciones_programadas"]
                        if ocup.get("asignatura") != asignatura_codigo and ocup.get(
                            "codigo_asignatura") != asignatura_codigo
                    ]
                    if len(aula_data["ocupaciones_programadas"]) < ocupaciones_originales:
                        cambios_realizados = True
                        self.log_mensaje(f"🔄 Ocupaciones de {asignatura_codigo} eliminadas del aula {aula_nombre}",
                                         "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["aulas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Asignatura {asignatura_codigo} eliminada del módulo de aulas", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando asignatura de aulas: {e}", "warning")

    def eliminar_asignatura_de_asignaturas_sistema(self, asignatura_codigo):
        """Eliminar asignatura del módulo de asignaturas del sistema"""
        try:
            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                datos_asignaturas = config_asignaturas["datos"]
                if asignatura_codigo in datos_asignaturas:
                    del datos_asignaturas[asignatura_codigo]
                    self.parent_window.configuracion["configuracion"]["asignaturas"][
                        "fecha_actualizacion"] = datetime.now().isoformat()
                    self.log_mensaje(f"🗑️ Asignatura {asignatura_codigo} eliminada del módulo de asignaturas", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando asignatura de asignaturas: {e}", "warning")

    def marcar_asignatura_eliminada_en_tabla(self, asignatura_codigo):
        """Marcar asignatura como eliminada visualmente en la tabla"""
        try:
            for row in range(self.list_asignaturas.count()):
                item = self.list_asignaturas.item(row)
                if item and item.data(Qt.ItemDataRole.UserRole) == asignatura_codigo:
                    # Obtener texto actual y modificarlo
                    texto_actual = item.text()
                    if not texto_actual.startswith("🗑️"):
                        texto_eliminado = f"🗑️ {texto_actual} (ELIMINADA)"
                        item.setText(texto_eliminado)

                    # Cambiar estilo visual
                    item.setBackground(QColor(220, 220, 220))  # Gris claro
                    item.setForeground(QColor(100, 100, 100))  # Texto gris

                    # Deshabilitar selección
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    break

        except Exception as e:
            self.log_mensaje(f"⚠️ Error marcando asignatura en tabla: {e}", "warning")

    def duplicar_asignatura_seleccionada(self):
        """Duplicar asignatura seleccionada con sincronización"""
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

        dialog = GestionAsignaturaDialog(datos_originales, self.alumnos_disponibles, self.aulas_disponibles,
                                         self.grupos_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_asignatura()
            codigo_final = datos_nuevos['codigo']

            if codigo_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe una asignatura con el código '{codigo_final}'")
                return

            # Añadir asignatura duplicada
            self.datos_configuracion[codigo_final] = datos_nuevos

            # SINCRONIZACIÓN: Notificar grupos asociados (NUEVO)
            grupos_asociados = datos_nuevos.get('grupos_asociados', [])
            if grupos_asociados:
                self.sincronizar_con_grupos(codigo_final, grupos_asociados, [])

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

                    # Calcular grupos recomendados (basándose en planificación)
                    alumnos_reales = stats['sin_lab_anterior']
                    grupos_recomendados = datos_asignatura.get('planificacion', {}).get('grupos_previstos',
                                                                                        0) if alumnos_reales > 0 else 0
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

    def importar_desde_horarios(self):
        """Importar asignaturas y grupos desde módulo de horarios"""
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
            grupos_importados = 0

            # Procesar ambos semestres
            for semestre, asignaturas_sem in asignaturas_horarios.items():
                for nombre_asig, datos_asig in asignaturas_sem.items():
                    # Crear código de asignatura único si no existe
                    codigo_asig = nombre_asig.upper().replace(" ", "")[:6]

                    # Verificar si ya existe
                    if codigo_asig in self.datos_configuracion:
                        continue

                    # Importar grupos
                    grupos = datos_asig.get("grupos", [])

                    # Crear asignatura nueva
                    self.datos_configuracion[codigo_asig] = {
                        'codigo': codigo_asig,
                        'nombre': nombre_asig,
                        'semestre': f"{semestre}º Semestre",
                        'curso': "1º Curso",  # Por defecto
                        'tipo': "Laboratorio",
                        'descripcion': f"Importada desde configuración de horarios",
                        'grupos_asociados': sorted(grupos),
                        'configuracion_laboratorio': {
                            'horas_por_sesion': 2,
                            'minutos_por_sesion': 0,
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
                    grupos_importados += len(grupos)

            if asignaturas_importadas > 0:
                # Auto-ordenar
                self.ordenar_asignaturas_alfabeticamente()

                # Actualizar interfaz
                self.cargar_lista_asignaturas()
                self.marcar_cambio_realizado()

                QMessageBox.information(self, "Importación Exitosa",
                                        f"✅ Importadas {asignaturas_importadas} asignaturas "
                                        f"con {grupos_importados} grupos desde horarios")
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
                grupos = datos.get('grupos_asociados', [])
                stats = datos.get('estadisticas_calculadas', {})

                # Convertir a formato compatible con horarios
                datos_para_horarios[datos.get('nombre', codigo)] = {
                    'codigo': codigo,
                    'grupos': grupos,
                    'grupos_recomendados': stats.get('grupos_recomendados', 0),
                    'alumnos_reales': stats.get('sin_lab_anterior', 0),
                    'semestre': datos.get('semestre', '1º Semestre').split('º')[0]
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
                    mensaje += f"• {nombre}: {len(datos['grupos'])} grupos, "
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
                    semestre_num = "1" if "1º" in datos.get('semestre', '1º Semestre') else "2"
                    nombre = datos.get('nombre', codigo)
                    grupos = datos.get('grupos_asociados', [])

                    if semestre_num not in datos_para_horarios:
                        datos_para_horarios[semestre_num] = {}

                    datos_para_horarios[semestre_num][nombre] = {
                        'grupos': grupos,
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

                # Procesar grupos
                grupos = []
                if 'grupos_asociados' in df.columns and pd.notna(row['grupos_asociados']):
                    grupos_text = str(row['grupos_asociados']).strip()
                    if grupos_text:
                        grupos = [g.strip().upper() for g in grupos_text.split(',')]

                self.datos_configuracion[codigo] = {
                    'codigo': codigo,
                    'nombre': str(row['nombre']).strip(),
                    'semestre': str(row.get('semestre', '1º Semestre')).strip(),
                    'curso': str(row.get('curso', '1º Curso')).strip(),
                    'tipo': str(row['tipo']).strip(),
                    'descripcion': str(row.get('descripcion', '')).strip(),
                    'grupos_asociados': grupos,
                    'configuracion_laboratorio': {
                        'horas_por_sesion': int(row.get('horas_por_sesion', 2)) if pd.notna(row.get('horas_por_sesion')) else 2,
                        'minutos_por_sesion': int(row.get('minutos_por_sesion', 0)) if pd.notna(row.get('minutos_por_sesion')) else 0,
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
                # Convertir grupos a string
                grupos_str = ', '.join(datos.get('grupos_asociados', []))

                config_lab = datos.get('configuracion_laboratorio', {})
                stats = datos.get('estadisticas_calculadas', {})

                datos_export.append({
                    'codigo': codigo,
                    'nombre': datos.get('nombre', ''),
                    'semestre': datos.get('semestre', ''),
                    'curso': datos.get('curso', ''),
                    'tipo': datos.get('tipo', ''),
                    'descripcion': datos.get('descripcion', ''),
                    'grupos_asociados': grupos_str,
                    'horas_por_sesion': config_lab.get('horas_por_sesion', 2),
                    'minutos_por_sesion': config_lab.get('minutos_por_sesion', 0),
                    'grupos_previstos': config_lab.get('grupos_previstos', 6),
                    'clases_año': config_lab.get('clases_año', 3),
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

                    grupos = datos.get('grupos_asociados', [])
                    f.write(f"   Grupos: {', '.join(grupos) if grupos else 'Sin grupos'}\n")

                    stats = datos.get('estadisticas_calculadas', {})
                    f.write(f"   Matriculados: {stats.get('total_matriculados', 0)}\n")
                    f.write(f"   Para lab: {stats.get('sin_lab_anterior', 0)}\n")
                    f.write(f"   Grupos recomendados: {stats.get('grupos_recomendados', 0)}\n")

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
        """Guardar configuración en el sistema principal aplicando eliminaciones pendientes"""
        try:
            total_asignaturas = len(self.datos_configuracion)
            con_alumnos = sum(1 for datos in self.datos_configuracion.values()
                              if datos.get('estadisticas_calculadas', {}).get('total_matriculados', 0) > 0)
            asignaturas_a_eliminar = len(self.cambios_pendientes["asignaturas_eliminadas"])

            if total_asignaturas == 0 and asignaturas_a_eliminar == 0:
                QMessageBox.warning(self, "Sin Datos", "No hay asignaturas configuradas para guardar.")
                return

            mensaje_confirmacion = f"¿Guardar configuración en el sistema y cerrar?\n\n"
            mensaje_confirmacion += f"📊 Resumen:\n"
            mensaje_confirmacion += f"• {total_asignaturas} asignaturas configuradas\n"
            mensaje_confirmacion += f"• {con_alumnos} asignaturas con alumnos matriculados\n"

            if asignaturas_a_eliminar > 0:
                mensaje_confirmacion += f"• {asignaturas_a_eliminar} asignaturas serán eliminadas en cascada\n"

            mensaje_confirmacion += f"\nLa configuración se integrará con OPTIM y la ventana se cerrará."

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                mensaje_confirmacion,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Aplicar eliminaciones pendientes antes de guardar
                if asignaturas_a_eliminar > 0:
                    self.aplicar_eliminaciones_pendientes()

                # Enviar señal al sistema principal
                self.configuracion_actualizada.emit(self.datos_configuracion)

                # Notificar a horarios DESPUÉS de guardar
                self.notificar_cambios_a_horarios()

                # Marcar como guardado
                self.datos_guardados_en_sistema = True
                self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)

                # Cerrar ventana
                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar en el sistema:\n{str(e)}")

    def limpiar_todas_asignaturas(self):
        """Marcar todas las asignaturas para eliminación en cascada al guardar"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay asignaturas para limpiar")
            return

        # Calcular estadísticas para mostrar en el diálogo
        total_asignaturas = len(self.datos_configuracion)

        # Contar grupos afectados
        grupos_afectados = set()
        for datos in self.datos_configuracion.values():
            grupos_asociados = datos.get('grupos_asociados', [])
            grupos_afectados.update(grupos_asociados)

        mensaje = f"¿Está seguro de eliminar TODAS las asignaturas configuradas?\n\n"
        mensaje += f"📊 IMPACTO TOTAL:\n"
        mensaje += f"• {total_asignaturas} asignaturas serán eliminadas\n"
        mensaje += f"• {len(grupos_afectados)} grupos serán afectados\n"
        mensaje += f"• Todas las referencias en profesores, alumnos, horarios y aulas\n\n"
        mensaje += f"⚠️ Esta acción marcará TODAS las asignaturas para eliminación.\n"
        mensaje += f"La eliminación se aplicará al guardar en el sistema.\n\n"
        mensaje += f"Esta acción no se puede deshacer."

        respuesta = QMessageBox.question(
            self, "Limpiar Todas las Asignaturas",
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            # Marcar TODAS las asignaturas para eliminación
            asignaturas_marcadas = 0
            for asignatura_codigo in list(self.datos_configuracion.keys()):
                if asignatura_codigo not in self.cambios_pendientes["asignaturas_eliminadas"]:
                    self.cambios_pendientes["asignaturas_eliminadas"].append(asignatura_codigo)
                    asignaturas_marcadas += 1

            # Marcar visualmente TODAS las asignaturas como eliminadas
            self.marcar_todas_asignaturas_eliminadas()

            # Deshabilitar selección
            self.asignatura_actual = None
            self.label_asignatura_actual.setText("Todas las asignaturas marcadas para eliminación")
            self.info_asignatura.setText("⚠️ TODAS las asignaturas serán eliminadas al guardar en el sistema")
            self.texto_stats.setText("⚠️ TODAS las asignaturas marcadas para eliminación en cascada")
            self.btn_duplicar.setEnabled(False)
            self.marcar_cambio_realizado()

            self.log_mensaje(f"📝 {asignaturas_marcadas} asignaturas marcadas para eliminación al guardar", "info")
            QMessageBox.information(self, "Marcadas para Eliminación",
                                    f"✅ {asignaturas_marcadas} asignaturas marcadas para eliminación.\n\n"
                                    f"La eliminación en cascada se aplicará al guardar en el sistema.")

    def marcar_todas_asignaturas_eliminadas(self):
        """Marcar visualmente todas las asignaturas como eliminadas"""
        try:
            for row in range(self.list_asignaturas.count()):
                item = self.list_asignaturas.item(row)
                if item and item.flags() != Qt.ItemFlag.NoItemFlags:  # Si no está ya deshabilitado
                    # Obtener texto actual y modificarlo
                    texto_actual = item.text()
                    if not texto_actual.startswith("🗑️"):
                        texto_eliminado = f"🗑️ {texto_actual} (ELIMINADA)"
                        item.setText(texto_eliminado)

                    # Cambiar estilo visual
                    item.setBackground(QColor(220, 220, 220))  # Gris claro
                    item.setForeground(QColor(100, 100, 100))  # Texto gris

                    # Deshabilitar selección
                    item.setFlags(Qt.ItemFlag.NoItemFlags)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error marcando todas las asignaturas en tabla: {e}", "warning")

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

        # Verificar eliminaciones pendientes
        hay_eliminaciones = len(self.cambios_pendientes["asignaturas_eliminadas"]) > 0

        if (hay_cambios or hay_eliminaciones) and not self.datos_guardados_en_sistema:
            return True

        if self.datos_guardados_en_sistema and (hay_cambios or hay_eliminaciones):
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
        """Manejar cierre de ventana cancelando eliminaciones pendientes si es necesario"""
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
            # Cancelar eliminaciones pendientes y restaurar vista
            self.cancelar_eliminaciones_pendientes()
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

    def cancelar_eliminaciones_pendientes(self):
        """Cancelar eliminaciones marcadas y restaurar vista"""
        try:
            asignaturas_canceladas = len(self.cambios_pendientes["asignaturas_eliminadas"])

            if asignaturas_canceladas > 0:
                self.cambios_pendientes["asignaturas_eliminadas"].clear()

                # Recargar tabla para quitar marcas visuales
                self.cargar_lista_asignaturas()

                # Restaurar interfaz si se había limpiado todo
                if asignaturas_canceladas == len(self.datos_configuracion) or asignaturas_canceladas > 1:
                    self.label_asignatura_actual.setText("Seleccione una asignatura")
                    self.info_asignatura.setText("ℹ️ Seleccione una asignatura para ver sus detalles")
                    self.texto_stats.setText("📈 Presiona 'Actualizar desde Alumnos' para ver estadísticas")
                    self.btn_duplicar.setEnabled(False)

                self.log_mensaje(f"↩️ {asignaturas_canceladas} eliminaciones de asignaturas canceladas", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cancelando eliminaciones: {e}", "warning")

    def notificar_cambios_a_horarios(self):
        """Notificar cambios de asignaturas al módulo de horarios - IMPLEMENTACIÓN REAL"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'sincronizar_asignaturas_con_horarios'):
                # Preparar datos para horarios
                datos_para_horarios = {}

                for codigo, datos in self.datos_configuracion.items():
                    nombre = datos.get('nombre', codigo)
                    grupos = datos.get('grupos_asociados', [])

                    datos_para_horarios[nombre] = {
                        'codigo': codigo,
                        'grupos': grupos,
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
        "SEI": {
          "codigo": "SEI",
          "nombre": "Sistemas Electronicos Industriales",
          "semestre": "2º Semestre",
          "curso": "3º Curso",
          "tipo": "Laboratorio",
          "descripcion": "",
          "grupos_asociados": {
            "A302": {
              "configuracion_laboratorio": {
                "horas_por_sesion": 2,
                "minutos_por_sesion": 0,
                "grupos_previstos": 6,
                "clases_año": 8
              },
              "estadisticas_calculadas": {
                "total_matriculados": 0,
                "con_lab_anterior": 0,
                "sin_lab_anterior": 0,
                "grupos_recomendados": 0,
                "ultima_actualizacion": "2025-07-13T15:23:00.651797"
              }
            },
            "EE303": {
              "configuracion_laboratorio": {
                "horas_por_sesion": 2,
                "minutos_por_sesion": 0,
                "grupos_previstos": 6,
                "clases_año": 8
              },
              "estadisticas_calculadas": {
                "total_matriculados": 0,
                "con_lab_anterior": 0,
                "sin_lab_anterior": 0,
                "grupos_recomendados": 0,
                "ultima_actualizacion": "2025-07-13T15:23:00.651797"
              }
            }
          },
          "estadisticas_calculadas": {
            "total_matriculados": 0,
            "con_lab_anterior": 0,
            "sin_lab_anterior": 0,
            "ultima_actualizacion": "2025-07-13T15:23:00.651797"
          },
          "fecha_creacion": "2025-07-14T18:38:45.061223"
        },
        "SII": {
          "codigo": "SII",
          "nombre": "Sistemas Informaticos Industriales",
          "semestre": "2º Semestre",
          "curso": "3º Curso",
          "tipo": "Laboratorio",
          "descripcion": "",
          "grupos_asociados": {
            "A302": {
              "configuracion_laboratorio": {
                "horas_por_sesion": 2,
                "minutos_por_sesion": 0,
                "grupos_previstos": 4,
                "clases_año": 10
              },
              "estadisticas_calculadas": {
                "total_matriculados": 0,
                "con_lab_anterior": 0,
                "sin_lab_anterior": 0,
                "grupos_recomendados": 0,
                "ultima_actualizacion": "2025-07-13T15:22:51.472035"
              }
            },
            "EE303": {
              "configuracion_laboratorio": {
                "horas_por_sesion": 2,
                "minutos_por_sesion": 0,
                "grupos_previstos": 4,
                "clases_año": 10
              },
              "estadisticas_calculadas": {
                "total_matriculados": 0,
                "con_lab_anterior": 0,
                "sin_lab_anterior": 0,
                "grupos_recomendados": 0,
                "ultima_actualizacion": "2025-07-13T15:22:51.472035"
              }
            }
          },
          "estadisticas_calculadas": {
            "total_matriculados": 0,
            "con_lab_anterior": 0,
            "sin_lab_anterior": 0,
            "ultima_actualizacion": "2025-07-13T15:22:51.472035"
          },
          "fecha_creacion": "2025-07-14T17:54:43.734029"
        }
    }

    window = ConfigurarAsignaturas(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()