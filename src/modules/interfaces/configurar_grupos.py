#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Grupos - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)


Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QGroupBox, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QFormLayout
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


class GestionGrupoDialog(QDialog):
    """Dialog para añadir/editar grupo con configuración completa"""

    def __init__(self, grupo_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        self.grupo_existente = grupo_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {}
        self.parent_window = parent
        self.setWindowTitle("Editar Grupo" if grupo_existente else "Nuevo Grupo")
        self.setModal(True)

        window_width = 700
        window_height = 850
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

        # Forzar tamaños iguales de ok/cancel
        QTimer.singleShot(50, self.igualar_tamanos_botones_ok_cancel)

        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)

        if self.grupo_existente:
            self.cargar_datos_existentes()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Datos básicos del grupo
        basicos_group = QGroupBox("🎓 DATOS BÁSICOS DEL GRUPO")
        basicos_layout = QFormLayout()

        self.edit_codigo = QLineEdit()
        self.edit_codigo.setPlaceholderText("A102, B102, A302, EE309...")

        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Grado en Ingeniería en Tecnologías Industriales...")

        self.combo_curso_actual = QComboBox()
        self.combo_curso_actual.addItems(["1º Curso", "2º Curso", "3º Curso", "4º Curso", "5º Curso"])

        self.edit_coordinador = QLineEdit()
        self.edit_coordinador.setPlaceholderText("Dr. García López, Dra. Martínez Ruiz...")

        self.edit_departamento = QLineEdit()
        self.edit_departamento.setPlaceholderText("Ingeniería Industrial, Ingeniería Eléctrica...")

        self.combo_horario_tipo = QComboBox()
        self.combo_horario_tipo.addItems(["Mañana", "Tarde"])

        self.check_activo = QCheckBox("Grupo activo")
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
        creditos_layout.addWidget(QLabel("créditos totales del grupo"))
        creditos_layout.addStretch()

        # Plazas disponibles
        plazas_layout = QHBoxLayout()
        self.spin_plazas = QSpinBox()
        self.spin_plazas.setRange(1, 300)
        self.spin_plazas.setValue(0)
        self.spin_plazas.setSuffix(" plazas")
        plazas_layout.addWidget(self.spin_plazas)
        plazas_layout.addWidget(QLabel("plazas disponibles"))
        plazas_layout.addStretch()

        # Estudiantes matriculados
        matriculados_layout = QHBoxLayout()
        self.spin_estudiantes_matriculados = QSpinBox()
        self.spin_estudiantes_matriculados.setRange(0, 300)
        self.spin_estudiantes_matriculados.setValue(0)
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

        #btn_edit_asignatura = QPushButton("✏️")
        #btn_edit_asignatura.setMinimumSize(30, 25)
        #btn_edit_asignatura.setMaximumSize(40, 40)
        #btn_edit_asignatura.setStyleSheet(self.get_button_style("#2196F3"))
        #btn_edit_asignatura.setToolTip("Editar asignatura seleccionada")
        #btn_edit_asignatura.clicked.connect(self.editar_asignatura_seleccionada)
        #asignaturas_header.addWidget(btn_edit_asignatura)

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
        self.edit_observaciones.setPlaceholderText("Observaciones adicionales del grupo...")
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
        """Cargar datos del grupo existente"""
        if not self.grupo_existente:
            return

        datos = self.grupo_existente
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
        self.spin_plazas.setValue(datos.get('plazas', 0))
        self.spin_estudiantes_matriculados.setValue(datos.get('estudiantes_matriculados', 0))

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
            QMessageBox.warning(self, "Campo requerido", "El código del grupo es obligatorio")
            self.edit_codigo.setFocus()
            return

        if not self.edit_nombre.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre del grupo es obligatorio")
            self.edit_nombre.setFocus()
            return

        #if not self.edit_coordinador.text().strip():
        #    QMessageBox.warning(self, "Campo requerido", "El coordinador del grupo es obligatorio")
        #    self.edit_coordinador.setFocus()
        #    return

        #if not self.edit_departamento.text().strip():
        #    QMessageBox.warning(self, "Campo requerido", "El departamento del grupo es obligatorio")
        #    self.edit_departamento.setFocus()
        #    return

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

    def anadir_asignatura(self):
        """Añadir nueva asignatura al grupo"""
        if not self.asignaturas_disponibles:
            QMessageBox.information(self, "Sin Asignaturas",
                                    "No hay asignaturas disponibles para asociar.\n"
                                    "Configure primero las asignaturas en el sistema.")
            return

        # Obtener asignaturas ya agregadas
        asignaturas_ya_agregadas = set()
        for i in range(self.list_asignaturas_dialog.count()):
            item = self.list_asignaturas_dialog.item(i)
            asignaturas_ya_agregadas.add(item.data(Qt.ItemDataRole.UserRole))

        # Crear lista de asignaturas disponibles
        asignaturas_disponibles = []
        for codigo, datos in self.asignaturas_disponibles.items():
            # Saltar si ya está agregada
            if codigo in asignaturas_ya_agregadas:
                continue

            nombre = datos.get('nombre', codigo)
            semestre = datos.get('semestre', 'Sin semestre')
            asignaturas_disponibles.append(f"{codigo} - {nombre} ({semestre})")

        # Verificar si quedan asignaturas disponibles
        if not asignaturas_disponibles:
            total_asignaturas = len(self.asignaturas_disponibles)
            asignaturas_agregadas = len(asignaturas_ya_agregadas)

            QMessageBox.information(self, "Sin Asignaturas Disponibles",
                                    f"No hay asignaturas disponibles para agregar.\n\n"
                                    f"📊 Estado actual:\n"
                                    f"• Total de asignaturas en el sistema: {total_asignaturas}\n"
                                    f"• Asignaturas ya asociadas a este grupo: {asignaturas_agregadas}\n\n"
                                    f"✅ Todas las asignaturas disponibles ya están asociadas a este grupo.")
            return

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
                    QMessageBox.warning(self, "Error", "Esta asignatura ya está asociada al grupo")
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

        # Obtener asignaturas ya agregadas
        asignaturas_ya_agregadas = set()
        for i in range(self.list_asignaturas_dialog.count()):
            item = self.list_asignaturas_dialog.item(i)
            asignaturas_ya_agregadas.add(item.data(Qt.ItemDataRole.UserRole))

        # Crear lista de asignaturas disponibles
        asignaturas_disponibles = []
        for codigo, datos in self.asignaturas_disponibles.items():
            # Saltar si ya está agregada
            if codigo in asignaturas_ya_agregadas:
                continue

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
                    QMessageBox.warning(self, "Error", "Esta asignatura ya está asociada al grupo")
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

    def get_datos_grupo(self):
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
        """Configurar estilos uniformes para botones OK/Cancel"""
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


class ConfigurarGrupos(QMainWindow):
    """Ventana principal para configurar grupos del sistema"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Grupos - OPTIM")
        window_width = 1400
        window_height = 750
        center_window_on_screen_immediate(self, window_width, window_height)

        # Obtener datos relacionados desde el sistema global
        self.asignaturas_disponibles = self.obtener_asignaturas_del_sistema()
        self.alumnos_disponibles = self.obtener_alumnos_del_sistema()
        self.horarios_disponibles = self.obtener_horarios_del_sistema()

        # Sistema de cambios pendientes para eliminación en cascada
        self.cambios_pendientes = {
            "grupos_eliminados": [],
            "profesores_eliminados": [],
            "aulas_eliminadas": [],
            "asignaturas_eliminadas": []
        }

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("📥 Cargando configuración existente de grupos...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("📝 Iniciando configuración nueva de grupos...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.grupo_actual = None

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
            # Ordenar grupos alfabéticamente
            self.ordenar_grupos_alfabeticamente()

            # Cargar lista
            self.cargar_lista_grupos()

            # Mostrar resumen
            total_grupos = len(self.datos_configuracion)

            if total_grupos > 0:
                self.log_mensaje(
                    f"✅ Datos cargados: {total_grupos} grupos configurados",
                    "success"
                )
                self.auto_seleccionar_primer_grupo()
            else:
                self.log_mensaje("📝 No hay grupos configurados - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primer_grupo(self):
        """Auto-seleccionar primer grupo disponible"""
        try:
            if self.list_grupos.count() > 0:
                primer_item = self.list_grupos.item(0)
                self.list_grupos.setCurrentItem(primer_item)
                self.seleccionar_grupo(primer_item)
                self.log_mensaje(f"🎯 Auto-seleccionado: {primer_item.text()}", "info")
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando grupo: {e}", "warning")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("🎓 CONFIGURACIÓN DE GRUPOS")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información del flujo
        info_label = QLabel(
            "ℹ️ Define los grupos académicos, coordinadores y asignaturas asociadas. Las estadísticas se actualizan desde los alumnos matriculados.")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de grupos
        left_panel = QGroupBox("📋 GRUPOS CONFIGURADOS")
        left_layout = QVBoxLayout()

        # Header con botones de gestión
        grupos_header = QHBoxLayout()
        grupos_header.addWidget(QLabel("Grupos:"))
        grupos_header.addStretch()

        btn_add_grupo = self.crear_boton_accion("➕", "#4CAF50", "Añadir nuevo grupo")
        btn_add_grupo.clicked.connect(self.anadir_grupo)

        btn_edit_grupo = self.crear_boton_accion("✏️", "#2196F3", "Editar grupo seleccionado")
        btn_edit_grupo.clicked.connect(self.editar_grupo_seleccionado)

        btn_delete_grupo = self.crear_boton_accion("🗑️", "#f44336", "Eliminar grupo seleccionado")
        btn_delete_grupo.clicked.connect(self.eliminar_grupo_seleccionado)

        grupos_header.addWidget(btn_add_grupo)
        grupos_header.addWidget(btn_edit_grupo)
        grupos_header.addWidget(btn_delete_grupo)

        left_layout.addLayout(grupos_header)

        # Lista de grupos
        self.list_grupos = QListWidget()
        self.list_grupos.setMaximumWidth(400)
        self.list_grupos.setMinimumHeight(400)
        left_layout.addWidget(self.list_grupos)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Detalles del grupo
        center_panel = QGroupBox("🔍 DETALLES DEL GRUPO")
        center_layout = QVBoxLayout()
        center_layout.setSpacing(8)

        # Nombre del grupo seleccionado
        self.label_grupo_actual = QLabel("Seleccione un grupo")
        self.label_grupo_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_grupo_actual)

        # Información detallada
        self.info_grupo = QTextEdit()
        self.info_grupo.setMaximumHeight(300)
        self.info_grupo.setReadOnly(True)
        self.info_grupo.setText("ℹ️ Seleccione un grupo para ver sus detalles")
        center_layout.addWidget(self.info_grupo)

        # Estadísticas automáticas
        stats_group = QGroupBox("📊 ESTADÍSTICAS AUTOMÁTICAS")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)

        botones_stats_layout = QHBoxLayout()
        self.btn_actualizar_desde_alumnos = QPushButton("🔄 Actualizar desde Alumnos")
        self.btn_actualizar_desde_alumnos.clicked.connect(self.actualizar_estadisticas_desde_alumnos)
        botones_stats_layout.addWidget(self.btn_actualizar_desde_alumnos)

        self.btn_calcular_ocupacion = QPushButton("📈 Calcular Ocupación")
        self.btn_calcular_ocupacion.clicked.connect(self.calcular_ocupacion_grupos)
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

        self.btn_duplicar = QPushButton("📋 Duplicar Grupo Seleccionado")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_grupo_seleccionado)
        acciones_layout.addWidget(self.btn_duplicar)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Import
        importar_group = QGroupBox("📥 IMPORTAR DATOS")
        importar_layout = QVBoxLayout()

        self.btn_cargar = QPushButton("📤 Importar Datos")
        self.btn_cargar.setToolTip("Importar configuración desde JSON")
        self.btn_cargar.clicked.connect(self.cargar_configuracion)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Export
        exportar_group = QGroupBox("💾 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

        self.btn_exportar_datos = QPushButton("💾 Exportar Datos")
        self.btn_exportar_datos.setToolTip("Exportar configuración a JSON")
        self.btn_exportar_datos.clicked.connect(self.guardar_en_archivo)
        exportar_layout.addWidget(self.btn_exportar_datos)

        self.btn_exportar_estadisticas = QPushButton("📊 Exportar Estadísticas")
        self.btn_exportar_datos.setToolTip("Exportar Estadisticas en TXT")
        self.btn_exportar_estadisticas.clicked.connect(self.exportar_estadisticas)
        exportar_layout.addWidget(self.btn_exportar_estadisticas)

        exportar_group.setLayout(exportar_layout)
        right_layout.addWidget(exportar_group)

        # Botones principales
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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todos_grupos)
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
        """Conectar señales de la interfaz"""
        self.list_grupos.itemClicked.connect(self.seleccionar_grupo)

    def cargar_lista_grupos(self):
        """Cargar grupos en la lista visual"""
        self.list_grupos.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay grupos configurados")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_grupos.addItem(item)
            return

        # Ordenar grupos por código
        grupos_ordenados = sorted(self.datos_configuracion.items())

        for codigo, datos in grupos_ordenados:
            nombre = datos.get('nombre', 'Sin nombre')
            grupo_actual = datos.get('grupo_actual', 'Sin grupo')
            coordinador = datos.get('coordinador', 'Sin coordinador')

            # Mostrar estado activo
            activo = datos.get('activo', True)
            estado_icono = "✅" if activo else "❌"

            # Estadísticas
            plazas = datos.get('plazas', 0)
            matriculados = datos.get('estudiantes_matriculados', 0)
            asignaturas = datos.get('asignaturas_asociadas', [])

            texto_item = f"{estado_icono} {codigo} - {nombre}"
            texto_item += f"\n    {grupo_actual} | {coordinador}"
            texto_item += f"\n    {matriculados}/{plazas} estudiantes | {len(asignaturas)} asignaturas"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_grupos.addItem(item)

    def seleccionar_grupo(self, item):
        """Seleccionar grupo y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.grupo_actual = None
            self.btn_duplicar.setEnabled(False)
            return

        codigo = item.data(Qt.ItemDataRole.UserRole)
        if not codigo or codigo not in self.datos_configuracion:
            return

        self.grupo_actual = codigo
        datos = self.datos_configuracion[codigo]

        # Actualizar etiqueta
        nombre = datos.get('nombre', 'Sin nombre')
        self.label_grupo_actual.setText(f"🎓 {codigo} - {nombre}")

        # Mostrar información detallada
        info = f"🎓 GRUPO: {codigo} - {nombre}\n\n"
        info += f"📚 Grupo Actual: {datos.get('grupo_actual', 'No definido')}\n"
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

        self.info_grupo.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)

    def sincronizar_con_asignaturas(self, grupo_codigo, asignaturas_nuevas, asignaturas_eliminadas):
        """Sincroniza altas/bajas del grupo con el módulo de asignaturas.

        Notas:
          - `grupos_asociados` es un diccionario cuyas claves son códigos de grupo.
          - Altas: se crea/actualiza la clave `grupo_codigo` con un dict (vacío si no aplica).
          - Bajas: se elimina la clave `grupo_codigo` si existe.
        """
        try:
            if not self.parent_window:
                return

            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if not config_asignaturas.get("configurado") or not config_asignaturas.get("datos"):
                return

            datos_asignaturas = config_asignaturas["datos"]
            cambios_realizados = False

            # Altas: garantizar clave en dict grupos_asociados
            for asignatura_codigo in asignaturas_nuevas:
                if asignatura_codigo in datos_asignaturas:
                    ga = datos_asignaturas[asignatura_codigo].get("grupos_asociados")
                    if not isinstance(ga, dict):
                        ga = {}
                    if grupo_codigo not in ga:
                        ga[grupo_codigo] = ga.get(grupo_codigo, {})  # payload vacío/sin estructura específica
                        datos_asignaturas[asignatura_codigo]["grupos_asociados"] = ga
                        cambios_realizados = True

            # Bajas: eliminar clave del dict
            for asignatura_codigo in asignaturas_eliminadas:
                if asignatura_codigo in datos_asignaturas:
                    ga = datos_asignaturas[asignatura_codigo].get("grupos_asociados")
                    if isinstance(ga, dict) and grupo_codigo in ga:
                        ga.pop(grupo_codigo, None)
                        datos_asignaturas[asignatura_codigo]["grupos_asociados"] = ga
                        cambios_realizados = True

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["asignaturas"]["datos"] = datos_asignaturas
                self.parent_window.configuracion["configuracion"]["asignaturas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"🔄 Sincronizado grupo {grupo_codigo} con módulo de asignaturas", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error sincronizando con asignaturas: {e}", "warning")

    def anadir_grupo(self):
        """Añadir nuevo grupo - CON SINCRONIZACIÓN"""
        dialog = GestionGrupoDialog(None, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_grupo()
            codigo = datos['codigo']

            if codigo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un grupo con el código '{codigo}'")
                return

            # Añadir nuevo grupo
            self.datos_configuracion[codigo] = datos

            # SINCRONIZACIÓN: Notificar asignaturas añadidas
            asignaturas_nuevas = datos.get('asignaturas_asociadas', [])
            if asignaturas_nuevas:
                self.sincronizar_con_asignaturas(codigo, asignaturas_nuevas, [])

            # Auto-ordenar
            self.ordenar_grupos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_grupos()
            self.auto_seleccionar_grupo(codigo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Grupo '{codigo} - {datos['nombre']}' añadido correctamente")

    def editar_grupo_seleccionado(self):
        """Editar grupo seleccionado - CON SINCRONIZACIÓN Y EDICIÓN EN CASCADA"""
        if not self.grupo_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grupo para editar")
            return

        datos_originales = self.datos_configuracion[self.grupo_actual].copy()
        dialog = GestionGrupoDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_grupo()
            codigo_nuevo = datos_nuevos['codigo']
            codigo_original = self.grupo_actual

            # Si cambió el código, verificar que no exista
            if codigo_nuevo != codigo_original and codigo_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un grupo con el código '{codigo_nuevo}'")
                return

            # SINCRONIZACIÓN: Detectar cambios en asignaturas
            asignaturas_originales = set(datos_originales.get('asignaturas_asociadas', []))
            asignaturas_nuevas = set(datos_nuevos.get('asignaturas_asociadas', []))

            asignaturas_añadidas = asignaturas_nuevas - asignaturas_originales
            asignaturas_eliminadas = asignaturas_originales - asignaturas_nuevas

            # Actualizar datos localmente
            if codigo_nuevo != codigo_original:
                del self.datos_configuracion[codigo_original]
                self.grupo_actual = codigo_nuevo

            self.datos_configuracion[codigo_nuevo] = datos_nuevos

            # EDICIÓN EN CASCADA: Si cambió el código, aplicar cambios
            if codigo_nuevo != codigo_original:
                self.editar_grupo_real_completo(codigo_original, codigo_nuevo)

            # SINCRONIZACIÓN: Aplicar cambios de asignaturas
            if asignaturas_añadidas or asignaturas_eliminadas:
                self.sincronizar_con_asignaturas(codigo_nuevo, asignaturas_añadidas, asignaturas_eliminadas)

            # Auto-ordenar
            self.ordenar_grupos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_grupos()
            self.auto_seleccionar_grupo(codigo_nuevo)
            self.marcar_cambio_realizado()

            if codigo_nuevo != codigo_original:
                QMessageBox.information(self, "Éxito",
                                        f"Grupo editado: {codigo_original} → {codigo_nuevo}\n"
                                        f"Se aplicará el cambio en cascada al guardar los datos")
            else:
                QMessageBox.information(self, "Éxito", "Grupo actualizado correctamente")

    def editar_grupo_real_completo(self, codigo_original, codigo_nuevo):
        """Editar grupo realmente del sistema completo en cascada"""
        try:
            if not self.parent_window:
                self.log_mensaje(f"⚠️ No se puede editar {codigo_original}: sin parent_window", "warning")
                return

            # Obtener datos del grupo antes de editar
            datos_grupo = self.datos_configuracion.get(codigo_nuevo)  # Ya actualizado localmente
            if not datos_grupo:
                self.log_mensaje(f"⚠️ Grupo {codigo_nuevo} no encontrado en configuración", "warning")
                return

            asignaturas_asociadas = datos_grupo.get('asignaturas_asociadas', [])

            self.log_mensaje(f"✏️ Editando grupo {codigo_original} → {codigo_nuevo} del sistema completo...", "info")

            # 1. Editar en asignaturas
            if asignaturas_asociadas:
                self.editar_grupo_en_asignaturas_sistema(codigo_original, codigo_nuevo, asignaturas_asociadas)

            # 2. Editar en alumnos
            self.editar_grupo_en_alumnos_sistema(codigo_original, codigo_nuevo)

            # 3. Editar en horarios
            self.editar_grupo_en_horarios_sistema(codigo_original, codigo_nuevo)
            self.editar_grupo_en_franjas_horario(codigo_original, codigo_nuevo, asignaturas_asociadas)

            # 4. Editar en configuración de grupos del sistema
            self.editar_grupo_en_grupos_sistema(codigo_original, codigo_nuevo)

            self.log_mensaje(f"✅ Grupo {codigo_original} → {codigo_nuevo} editado completamente del sistema", "success")

        except Exception as e:
            self.log_mensaje(f"❌ Error en edición completa de grupo {codigo_original}: {e}", "error")

    def editar_grupo_en_asignaturas_sistema(self, codigo_original, codigo_nuevo, asignaturas_asociadas):
        """Renombra el código de grupo en el módulo de asignaturas.

        Criterios:
          - `grupos_asociados` es dict -> renombrar clave `codigo_original` a `codigo_nuevo`.
          - Se conserva el payload asociado a la clave (dict existente o se crea vacío).
        """
        try:
            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if not config_asignaturas.get("configurado") or not config_asignaturas.get("datos"):
                return

            datos_asignaturas = config_asignaturas["datos"]
            cambios_realizados = False

            for asignatura_codigo in asignaturas_asociadas:
                if asignatura_codigo in datos_asignaturas:
                    ga = datos_asignaturas[asignatura_codigo].get("grupos_asociados")
                    if isinstance(ga, dict) and codigo_original in ga:
                        payload = ga.pop(codigo_original)
                        # Si por diseño no hay payload estructurado, garantizamos dict vacío
                        if not isinstance(payload, dict):
                            payload = {}
                        ga[codigo_nuevo] = payload
                        datos_asignaturas[asignatura_codigo]["grupos_asociados"] = ga
                        cambios_realizados = True

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["asignaturas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"🔄 Grupo {codigo_original} → {codigo_nuevo} renombrado en módulo de asignaturas",
                                 "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando grupo en asignaturas: {e}", "warning")

    def editar_grupo_en_alumnos_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de grupo en el sistema de alumnos"""
        try:
            config_alumnos = self.parent_window.configuracion["configuracion"].get("alumnos", {})
            if not config_alumnos.get("configurado") or not config_alumnos.get("datos"):
                return

            datos_alumnos = config_alumnos["datos"]
            cambios_realizados_grupos_matriculado = False
            cambios_realizados_asignaturas_matriculadas = False

            for alumno_codigo, alumno_data in datos_alumnos.items():
                # 1. Actualizar grupos_matriculado
                grupos_matriculados = alumno_data.get("grupos_matriculado", [])
                if codigo_original in grupos_matriculados:
                    # Reemplazar código antiguo por nuevo
                    indice = grupos_matriculados.index(codigo_original)
                    grupos_matriculados[indice] = codigo_nuevo
                    alumno_data["grupos_matriculado"] = grupos_matriculados
                    cambios_realizados_grupos_matriculado = True

                # 2. Actualizar campo 'grupo' dentro de cada asignatura
                asignaturas_matriculadas = alumno_data.get("asignaturas_matriculadas", {})
                for asig_codigo, asig_info in asignaturas_matriculadas.items():
                    if isinstance(asig_info, dict):
                        grupo_asig = asig_info.get("grupo")
                        if grupo_asig == codigo_original:
                            asig_info["grupo"] = codigo_nuevo
                            cambios_realizados_asignaturas_matriculadas = True

            if cambios_realizados_grupos_matriculado and cambios_realizados_asignaturas_matriculadas:
                self.parent_window.configuracion["configuracion"]["alumnos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"🔄 Grupo {codigo_original} → {codigo_nuevo} editado en módulo de alumnos", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando grupo en alumnos: {e}", "warning")

    def editar_grupo_en_horarios_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de grupo en el sistema de horarios"""
        try:
            config_horarios = self.parent_window.configuracion["configuracion"].get("horarios", {})
            if not config_horarios.get("configurado") or not config_horarios.get("datos"):
                return

            datos_horarios = config_horarios["datos"]
            cambios_realizados = False

            for semestre in ["1", "2"]:
                if semestre in datos_horarios:
                    asignaturas_semestre = datos_horarios[semestre]
                    for asignatura_codigo, asignatura_data in asignaturas_semestre.items():

                        # Editar en grupos principales
                        grupos = asignatura_data.get("grupos", [])
                        if codigo_original in grupos:
                            indice = grupos.index(codigo_original)
                            grupos[indice] = codigo_nuevo
                            asignatura_data["grupos"] = grupos
                            cambios_realizados = True
                            self.log_mensaje(
                                f"🔄 Grupo {codigo_original} → {codigo_nuevo} editado en {asignatura_codigo}.grupos",
                                "info")

                        # Editar en horarios_grid
                        horarios_grid = asignatura_data.get("horarios_grid", {})

                        for franja, dias_data in horarios_grid.items():
                            # Procesar cada día de la franja
                            for dia, lista_grupos in dias_data.items():
                                if isinstance(lista_grupos, list) and codigo_original in lista_grupos:
                                    # Reemplazar código antiguo por nuevo
                                    indice = lista_grupos.index(codigo_original)
                                    lista_grupos[indice] = codigo_nuevo
                                    cambios_realizados = True
                                    self.log_mensaje(
                                        f"🔄 Grupo {codigo_original} → {codigo_nuevo} editado en {asignatura_codigo}.{franja}.{dia}",
                                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Grupo {codigo_original} → {codigo_nuevo} editado en módulo de horarios", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando grupo en horarios: {e}", "warning")

    def editar_grupo_en_franjas_horario(self, codigo_original, codigo_nuevo, asignaturas_asociadas=None,
                                        semestres=None):
        """Renombra el código de grupo en todas las franjas del horarios_grid.

        Parámetros:
            codigo_original (str): código de grupo actual en las franjas (p. ej., "A408").
            codigo_nuevo (str): nuevo código de grupo a aplicar (p. ej., "A409").
            asignaturas_asociadas (list[str] | None): limitar la actualización a estas asignaturas.
                Si None, se intentará aplicar a todas las asignaturas presentes en los horarios.
            semestres (list[str] | None): limitar a semestres concretos (p. ej., ["1", "2"]).
                Si None, se detectan automáticamente a partir de la configuración.

        Comportamiento:
            - Recorre horarios_grid de cada asignatura/semestre y reemplaza codigo_original por codigo_nuevo
              en todas las listas de grupos por franja y día.
            - No crea nuevas franjas ni altera el orden de las listas, únicamente sustituye el literal del grupo.
        """
        try:
            cfg = self.parent_window.configuracion.get("configuracion", {})
            horarios = cfg.get("horarios", {})
            datos_hor = horarios.get("datos", {})
            if not datos_hor:
                return

            # Determinar semestres a procesar
            if semestres is None:
                semestres = [s for s in datos_hor.keys() if isinstance(s, str)]
            # Normalizar listado de asignaturas a procesar por semestre
            cambios = 0

            for semestre in semestres:
                sem_data = datos_hor.get(semestre, {})
                if not sem_data:
                    continue

                # Si no se limitaron asignaturas, tomar todas las del semestre
                asignaturas_objetivo = asignaturas_asociadas or list(sem_data.keys())

                for asig in asignaturas_objetivo:
                    asig_data = sem_data.get(asig)
                    if not asig_data:
                        continue

                    grid = asig_data.get("horarios_grid", {})
                    if not isinstance(grid, dict):
                        continue

                    # Estructura esperada: horarios_grid[franja][dia]["grupos"] -> list[str]
                    for franja, dias in grid.items():
                        if not isinstance(dias, dict):
                            continue
                        for dia, celda in dias.items():
                            if not isinstance(celda, dict):
                                continue
                            grupos = celda.get("grupos")
                            if isinstance(grupos, list) and codigo_original in grupos:
                                # Reemplazo in-place manteniendo orden
                                celda["grupos"] = [codigo_nuevo if g == codigo_original else g for g in grupos]
                                cambios += 1

            if cambios > 0:
                # Fecha de actualización de horarios
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"Actualizadas {cambios} celdas en franjas de horario: {codigo_original} → {codigo_nuevo}",
                    "info"
                )

        except Exception as e:
            self.log_mensaje(f"Error actualizando franjas de horario (renombrar {codigo_original}→{codigo_nuevo}): {e}",
                             "warning")

    def editar_grupo_en_grupos_sistema(self, codigo_original, codigo_nuevo):
        """Editar código de grupo en el sistema de grupos"""
        try:
            config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
            if config_grupos.get("configurado") and config_grupos.get("datos"):
                datos_grupos = config_grupos["datos"]
                if codigo_original in datos_grupos and codigo_original != codigo_nuevo:
                    # Mover datos del código antiguo al nuevo
                    datos_grupos[codigo_nuevo] = datos_grupos[codigo_original]
                    del datos_grupos[codigo_original]

                    # Actualizar el código interno del objeto también
                    datos_grupos[codigo_nuevo]["codigo"] = codigo_nuevo

                    self.parent_window.configuracion["configuracion"]["grupos"][
                        "fecha_actualizacion"] = datetime.now().isoformat()
                    self.log_mensaje(f"🔄 Grupo {codigo_original} → {codigo_nuevo} editado en módulo de grupos", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error editando grupo en grupos: {e}", "warning")

    def eliminar_grupo_seleccionado(self):
        """Marcar grupo seleccionado para eliminación en cascada al guardar"""
        if not self.grupo_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un grupo para eliminar")
            return

        datos = self.datos_configuracion[self.grupo_actual]
        nombre = datos.get('nombre', 'Sin nombre')
        asignaturas_asociadas = datos.get('asignaturas_asociadas', [])

        mensaje = f"¿Está seguro de eliminar el grupo '{self.grupo_actual} - {nombre}'?\n\n"
        if asignaturas_asociadas:
            mensaje += f"ADVERTENCIA: Este grupo tiene {len(asignaturas_asociadas)} asignaturas asociadas.\n"
            mensaje += f"Se eliminará automáticamente de:\n"
            mensaje += f"  • Todas las asignaturas asociadas\n"
            mensaje += f"  • Todos los alumnos matriculados\n"
            mensaje += f"  • Todos los horarios programados\n\n"
        mensaje += "La eliminación se aplicará al guardar en el sistema."

        # Confirmar eliminación
        respuesta = QMessageBox.question(self, "Confirmar Eliminación",
                                         mensaje,
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if respuesta == QMessageBox.StandardButton.Yes:
            grupo_codigo = self.grupo_actual

            # Marcar para eliminación en cascada
            if grupo_codigo not in self.cambios_pendientes["grupos_eliminados"]:
                self.cambios_pendientes["grupos_eliminados"].append(grupo_codigo)

            # Marcar visualmente como eliminado en la tabla
            self.marcar_grupo_eliminado_en_tabla(grupo_codigo)

            # Deshabilitar selección del grupo eliminado
            self.grupo_actual = None
            self.label_grupo_actual.setText("Grupo marcado para eliminación")
            self.info_grupo.setText("⚠️ Este grupo será eliminado al guardar en el sistema")
            self.btn_duplicar.setEnabled(False)
            self.marcar_cambio_realizado()

            self.log_mensaje(f"📝 Grupo {grupo_codigo} marcado para eliminación al guardar", "info")
            QMessageBox.information(self, "Marcado para Eliminación",
                                    f"Grupo '{grupo_codigo}' marcado para eliminación.\n\nLa eliminación se aplicará al guardar en el sistema.")

    def marcar_grupo_eliminado_en_tabla(self, grupo_codigo):
        """Marcar grupo como eliminado visualmente en la tabla"""
        try:
            for row in range(self.list_grupos.count()):
                item = self.list_grupos.item(row)
                if item and item.data(Qt.ItemDataRole.UserRole) == grupo_codigo:
                    # Obtener texto actual y modificarlo
                    texto_actual = item.text()
                    if not texto_actual.startswith("🗑️"):
                        texto_eliminado = f"🗑️ {texto_actual} (ELIMINADO)"
                        item.setText(texto_eliminado)

                    # Cambiar estilo visual
                    item.setBackground(QColor(220, 220, 220))  # Gris claro
                    item.setForeground(QColor(100, 100, 100))  # Texto gris

                    # Deshabilitar selección
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    break

        except Exception as e:
            self.log_mensaje(f"⚠️ Error marcando grupo en tabla: {e}", "warning")

    def eliminar_grupo_real_completo(self, grupo_codigo):
        """Eliminar grupo realmente del sistema completo en cascada"""
        try:
            if not self.parent_window:
                self.log_mensaje(f"⚠️ No se puede eliminar {grupo_codigo}: sin parent_window", "warning")
                return

            # Obtener datos del grupo antes de eliminar
            datos_grupo = self.datos_configuracion.get(grupo_codigo)
            if not datos_grupo:
                self.log_mensaje(f"⚠️ Grupo {grupo_codigo} no encontrado en configuración", "warning")
                return

            asignaturas_asociadas = datos_grupo.get('asignaturas_asociadas', [])

            self.log_mensaje(f"🗑️ Eliminando grupo {grupo_codigo} del sistema completo...", "info")

            # 1. Eliminar de asignaturas
            if asignaturas_asociadas:
                self.eliminar_grupo_de_asignaturas_sistema(grupo_codigo, asignaturas_asociadas)

            # 2. Eliminar de alumnos
            self.eliminar_grupo_de_alumnos_sistema(grupo_codigo)

            # 3. Eliminar de horarios
            self.eliminar_grupo_de_horarios_sistema(grupo_codigo)
            self.eliminar_grupo_de_franjas_horario(grupo_codigo, asignaturas_asociadas)

            # 5. Eliminar de configuración de grupos
            self.eliminar_grupo_de_grupos_sistema(grupo_codigo)

            # 6. Eliminar de la configuración local
            if grupo_codigo in self.datos_configuracion:
                del self.datos_configuracion[grupo_codigo]

            self.log_mensaje(f"✅ Grupo {grupo_codigo} eliminado completamente del sistema", "success")

        except Exception as e:
            self.log_mensaje(f"❌ Error en eliminación completa de grupo {grupo_codigo}: {e}", "error")

    def eliminar_grupo_de_asignaturas_sistema(self, grupo_codigo, asignaturas_asociadas):
        """Elimina el grupo de todas las asignaturas indicadas.

        Detalle:
          - `grupos_asociados` es dict -> se elimina la clave `grupo_codigo` si existe.
          - No ordena ni transforma: respeta la estructura actual del diccionario.
        """
        try:
            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if not config_asignaturas.get("configurado") or not config_asignaturas.get("datos"):
                return

            datos_asignaturas = config_asignaturas["datos"]
            cambios_realizados = False

            for asignatura_codigo in asignaturas_asociadas:
                if asignatura_codigo in datos_asignaturas:
                    ga = datos_asignaturas[asignatura_codigo].get("grupos_asociados")
                    if isinstance(ga, dict) and grupo_codigo in ga:
                        ga.pop(grupo_codigo, None)
                        datos_asignaturas[asignatura_codigo]["grupos_asociados"] = ga
                        cambios_realizados = True

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["asignaturas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"🔄 Grupo {grupo_codigo} eliminado del módulo de asignaturas", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando grupo de asignaturas: {e}", "warning")

    def eliminar_grupo_de_alumnos_sistema(self, grupo_codigo):
        """
        Elimina el grupo del sistema de alumnos y limpia asignaturas huérfanas.

        Cambios aplicados:
        1. Elimina el grupo de grupos_matriculado
        2. Elimina COMPLETAMENTE cualquier asignatura cuyo campo 'grupo' coincida con
           el grupo eliminado (no tiene sentido tener asignaturas sin grupo)

        Ejemplo:
            Si se elimina A408 y un alumno tiene:
                "asignaturas_matriculadas": {
                    "SII": {"grupo": "A408", "matriculado": true},
                    "SED": {"grupo": "A404", "matriculado": true}
                }
            Resultado:
                "asignaturas_matriculadas": {
                    "SED": {"grupo": "A404", "matriculado": true}
                }
            (SII se elimina porque su grupo A408 ya no existe)
        """
        try:
            config_alumnos = self.parent_window.configuracion["configuracion"].get("alumnos", {})
            if not config_alumnos.get("configurado") or not config_alumnos.get("datos"):
                return

            datos_alumnos = config_alumnos["datos"]
            cambios_realizados = 0
            asignaturas_eliminadas_total = 0

            for alumno_codigo, alumno_data in datos_alumnos.items():
                # 1. Eliminar de grupos_matriculado
                grupos_matriculados = alumno_data.get("grupos_matriculado", [])
                if grupo_codigo in grupos_matriculados:
                    grupos_matriculados.remove(grupo_codigo)
                    alumno_data["grupos_matriculado"] = grupos_matriculados
                    cambios_realizados += 1

                # 2. Eliminar asignaturas que tengan este grupo asignado
                asignaturas_matriculadas = alumno_data.get("asignaturas_matriculadas", {})
                asignaturas_a_eliminar = []

                for asig_codigo, asig_info in asignaturas_matriculadas.items():
                    if isinstance(asig_info, dict):
                        grupo_asig = asig_info.get("grupo")
                        if grupo_asig == grupo_codigo:
                            asignaturas_a_eliminar.append(asig_codigo)

                # Eliminar las asignaturas identificadas
                for asig_codigo in asignaturas_a_eliminar:
                    del asignaturas_matriculadas[asig_codigo]
                    asignaturas_eliminadas_total += 1

            if cambios_realizados > 0 or asignaturas_eliminadas_total > 0:
                self.parent_window.configuracion["configuracion"]["alumnos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"🔄 Grupo {grupo_codigo} eliminado: {cambios_realizados} alumnos actualizados, "
                    f"{asignaturas_eliminadas_total} asignaturas eliminadas",
                    "info"
                )

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando grupo de alumnos: {e}", "warning")

    def eliminar_grupo_de_horarios_sistema(self, grupo_codigo):
        """Eliminar grupo del sistema de horarios con limpieza completa de estructuras"""
        try:
            config_horarios = self.parent_window.configuracion["configuracion"].get("horarios", {})
            if not config_horarios.get("configurado") or not config_horarios.get("datos"):
                return

            datos_horarios = config_horarios["datos"]
            cambios_realizados = False

            for semestre in ["1", "2"]:
                if semestre in datos_horarios:
                    asignaturas_semestre = datos_horarios[semestre]
                    for asignatura_codigo, asignatura_data in asignaturas_semestre.items():

                        # 1. Eliminar de grupos principales (dict de grupos)
                        grupos_dict = asignatura_data.get("grupos", {})
                        if isinstance(grupos_dict, dict) and grupo_codigo in grupos_dict:
                            del grupos_dict[grupo_codigo]
                            asignatura_data["grupos"] = grupos_dict
                            cambios_realizados = True
                            self.log_mensaje(f"🗑️ Grupo {grupo_codigo} eliminado de {asignatura_codigo}.grupos (dict)",
                                             "info")

                        # 2. Eliminar de horarios_grid con limpieza automática
                        horarios_grid = asignatura_data.get("horarios_grid", {})
                        franjas_a_eliminar = []

                        for franja, dias_data in horarios_grid.items():
                            dias_a_eliminar = []

                            # Procesar cada día de la franja
                            for dia, celda in dias_data.items():
                                if isinstance(celda, dict):
                                    grupos = celda.get("grupos", [])
                                    if isinstance(grupos, list) and grupo_codigo in grupos:
                                        grupos.remove(grupo_codigo)
                                        celda["grupos"] = grupos
                                        cambios_realizados = True
                                        self.log_mensaje(
                                            f"🔄 Grupo {grupo_codigo} eliminado de {asignatura_codigo}.{franja}.{dia}",
                                            "info")

                                        # Si la lista del día quedó vacía, marcar día para eliminar
                                        if len(grupos) == 0:
                                            dias_a_eliminar.append(dia)

                            # Eliminar días que quedaron vacíos
                            for dia in dias_a_eliminar:
                                del dias_data[dia]
                                self.log_mensaje(
                                    f"🗑️ Día {dia} eliminado de {asignatura_codigo}.{franja} (quedó vacío)", "info")

                            # Si la franja quedó sin días, marcar franja para eliminar
                            if len(dias_data) == 0:
                                franjas_a_eliminar.append(franja)

                        # Eliminar franjas que quedaron vacías
                        for franja in franjas_a_eliminar:
                            del horarios_grid[franja]
                            self.log_mensaje(f"🗑️ Franja {franja} eliminada de {asignatura_codigo} (quedó vacía)",
                                             "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"✅ Grupo {grupo_codigo} eliminado del módulo de horarios con limpieza automática",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando grupo de horarios: {e}", "warning")

    def eliminar_grupo_de_franjas_horario(self, grupo_codigo, asignaturas_asociadas=None, semestres=None):
        """Elimina el código de grupo de todas las franjas del horarios_grid.

        Parámetros:
            grupo_codigo (str): código de grupo a eliminar de las franjas (p. ej., "EE403").
            asignaturas_asociadas (list[str] | None): limitar la limpieza a estas asignaturas.
                Si None, se intentará aplicar a todas las asignaturas presentes en los horarios.
            semestres (list[str] | None): limitar a semestres concretos (p. ej., ["1", "2"]).
                Si None, se detectan automáticamente a partir de la configuración.

        Comportamiento:
            - Recorre horarios_grid y elimina todas las apariciones de `grupo_codigo` en las listas de grupos.
            - Si una lista queda vacía, se mantiene vacía (no se borran franjas ni días).
        """
        try:
            cfg = self.parent_window.configuracion.get("configuracion", {})
            horarios = cfg.get("horarios", {})
            datos_hor = horarios.get("datos", {})
            if not datos_hor:
                return

            # Determinar semestres a procesar
            if semestres is None:
                semestres = [s for s in datos_hor.keys() if isinstance(s, str)]

            cambios = 0

            for semestre in semestres:
                sem_data = datos_hor.get(semestre, {})
                if not sem_data:
                    continue

                # Si no se limitaron asignaturas, tomar todas las del semestre
                asignaturas_objetivo = asignaturas_asociadas or list(sem_data.keys())

                for asig in asignaturas_objetivo:
                    asig_data = sem_data.get(asig)
                    if not asig_data:
                        continue

                    grid = asig_data.get("horarios_grid", {})
                    if not isinstance(grid, dict):
                        continue

                    for franja, dias in grid.items():
                        if not isinstance(dias, dict):
                            continue
                        for dia, celda in dias.items():
                            if not isinstance(celda, dict):
                                continue
                            grupos = celda.get("grupos")
                            if isinstance(grupos, list) and grupo_codigo in grupos:
                                celda["grupos"] = [g for g in grupos if g != grupo_codigo]
                                cambios += 1

            if cambios > 0:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"Eliminadas {cambios} apariciones de {grupo_codigo} en franjas de horario",
                    "info"
                )

        except Exception as e:
            self.log_mensaje(f"Error limpiando franjas de horario (eliminar {grupo_codigo}): {e}", "warning")

    def eliminar_grupo_de_grupos_sistema(self, grupo_codigo):
        """Eliminar grupo del sistema de grupos"""
        try:
            config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
            if config_grupos.get("configurado") and config_grupos.get("datos"):
                datos_grupos = config_grupos["datos"]
                if grupo_codigo in datos_grupos:
                    del datos_grupos[grupo_codigo]
                    self.parent_window.configuracion["configuracion"]["grupos"][
                        "fecha_actualizacion"] = datetime.now().isoformat()
                    self.log_mensaje(f"🗑️ Grupo {grupo_codigo} eliminado del módulo de grupos", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error eliminando grupo de grupos: {e}", "warning")

    def _actualizar_estadisticas_horarios(self):
        """Recalcular estadísticas de horarios después de modificaciones"""
        try:
            config_horarios = self.parent_window.configuracion["configuracion"]["horarios"]
            datos_horarios = config_horarios.get("datos", {})

            total_asignaturas = 0
            total_franjas = 0

            for semestre, asignaturas in datos_horarios.items():
                if isinstance(asignaturas, dict):
                    total_asignaturas += len(asignaturas)
                    for asignatura_data in asignaturas.values():
                        horarios_grid = asignatura_data.get("horarios_grid", {})
                        total_franjas += len(horarios_grid)

            # Actualizar estadísticas
            config_horarios["total_asignaturas"] = total_asignaturas
            config_horarios["total_franjas"] = total_franjas

            self.log_mensaje(f"📊 Estadísticas actualizadas: {total_asignaturas} asignaturas, {total_franjas} franjas",
                             "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error actualizando estadísticas de horarios: {e}", "warning")

    def duplicar_grupo_seleccionado(self):
        """Duplicar grupo seleccionado - CON SINCRONIZACIÓN"""
        if not self.grupo_actual:
            return

        datos_originales = self.datos_configuracion[self.grupo_actual].copy()

        # Generar código único
        codigo_base = f"{datos_originales['codigo']}_COPIA"
        contador = 1
        codigo_nuevo = codigo_base

        while codigo_nuevo in self.datos_configuracion:
            codigo_nuevo = f"{codigo_base}_{contador}"
            contador += 1

        datos_originales['codigo'] = codigo_nuevo
        datos_originales['nombre'] = f"{datos_originales['nombre']} (Copia)"
        # datos_originales['estudiantes_matriculados'] = 0  # Resetear matriculados
        datos_originales['fecha_creacion'] = datetime.now().isoformat()

        dialog = GestionGrupoDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_grupo()
            codigo_final = datos_nuevos['codigo']

            if codigo_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un grupo con el código '{codigo_final}'")
                return

            # Añadir grupo duplicado
            self.datos_configuracion[codigo_final] = datos_nuevos

            # ✅ SINCRONIZACIÓN: Notificar asignaturas añadidas del grupo duplicado
            asignaturas_nuevas = datos_nuevos.get('asignaturas_asociadas', [])
            if asignaturas_nuevas:
                self.sincronizar_con_asignaturas(codigo_final, asignaturas_nuevas, [])

            # Auto-ordenar
            self.ordenar_grupos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_grupos()
            self.auto_seleccionar_grupo(codigo_final)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Grupo duplicado como '{codigo_final}' con sincronización completa")

    def actualizar_estadisticas_desde_alumnos(self):
        """Actualizar estadísticas desde datos de alumnos matriculados"""
        try:
            if not self.alumnos_disponibles:
                self.texto_stats.setText("⚠️ No hay datos de alumnos disponibles")
                return

            # Agrupar alumnos por grupo
            estadisticas_por_grupo = {}

            for dni, datos_alumno in self.alumnos_disponibles.items():
                grupo = datos_alumno.get('grupo', '')
                if not grupo:
                    continue

                # Extraer códigos de grupo del grupo (ej: "A102, A104" -> ["A102", "A104"])
                codigos_grupo = [g.strip() for g in grupo.split(',') if g.strip()]

                for codigo_grupo in codigos_grupo:
                    if codigo_grupo not in estadisticas_por_grupo:
                        estadisticas_por_grupo[codigo_grupo] = {
                            'estudiantes_reales': 0,
                            'asignaturas_matriculadas': set()
                        }

                    estadisticas_por_grupo[codigo_grupo]['estudiantes_reales'] += 1

                    # Recopilar asignaturas
                    asignaturas_matriculadas = datos_alumno.get('asignaturas_matriculadas', {})
                    for asignatura in asignaturas_matriculadas.keys():
                        estadisticas_por_grupo[codigo_grupo]['asignaturas_matriculadas'].add(asignatura)

            # Actualizar estadísticas en grupos configurados
            grupos_actualizados = 0
            for codigo, datos_grupo in self.datos_configuracion.items():
                if codigo in estadisticas_por_grupo:
                    stats = estadisticas_por_grupo[codigo]

                    # Actualizar estudiantes matriculados
                    self.datos_configuracion[codigo]['estudiantes_matriculados'] = stats['estudiantes_reales']
                    grupos_actualizados += 1

            # Mostrar resumen de la actualización
            stats_text = f"🔄 ACTUALIZACIÓN COMPLETADA:\n\n"
            stats_text += f"• {grupos_actualizados} grupos actualizados\n"
            stats_text += f"• {len(self.alumnos_disponibles)} alumnos procesados\n\n"

            # Mostrar estadísticas por grupo
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
            self.cargar_lista_grupos()
            if self.grupo_actual:
                self.auto_seleccionar_grupo(self.grupo_actual)

            self.marcar_cambio_realizado()
            self.log_mensaje(f"✅ Estadísticas actualizadas: {grupos_actualizados} grupos", "success")

        except Exception as e:
            self.texto_stats.setText(f"❌ Error actualizando estadísticas: {e}")
            self.log_mensaje(f"⚠️ Error actualizando estadísticas: {e}", "warning")

    def calcular_ocupacion_grupos(self):
        """Calcular ocupación para todos los grupos"""
        try:
            if not self.datos_configuracion:
                QMessageBox.information(self, "Sin Datos", "No hay grupos configurados")
                return

            stats_text = "📊 OCUPACIÓN DE GRUPOS:\n\n"

            total_plazas = 0
            total_matriculados = 0
            grupos_completos = 0
            grupos_vacios = 0

            for codigo, datos in self.datos_configuracion.items():
                plazas = datos.get('plazas', 0)
                matriculados = datos.get('estudiantes_matriculados', 0)

                if plazas > 0:
                    ocupacion = (matriculados / plazas) * 100

                    if ocupacion >= 90:
                        estado = "🔴 COMPLETO"
                        grupos_completos += 1
                    elif ocupacion >= 70:
                        estado = "🟡 ALTO"
                    elif ocupacion >= 40:
                        estado = "🟢 MEDIO"
                    elif ocupacion > 0:
                        estado = "🔵 BAJO"
                    else:
                        estado = "⚪ VACÍO"
                        grupos_vacios += 1

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
                stats_text += f"• Grupos completos: {grupos_completos}\n"
                stats_text += f"• Grupos vacíos: {grupos_vacios}\n"

            self.texto_stats.setText(stats_text)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calculando ocupación: {e}")

    def exportar_estadisticas(self):
        """Exportar estadísticas completas a archivo"""
        ruta_inicial = obtener_ruta_descargas()
        nombre_archivo = f"estadisticas_grupos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ruta_completa = os.path.join(ruta_inicial, nombre_archivo)

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Estadísticas Completas",
            ruta_completa,  # Cambiar de solo nombre a ruta completa
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write("ESTADÍSTICAS COMPLETAS DE GRUPOS - OPTIM\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

                f.write(f"RESUMEN GENERAL:\n")
                f.write(f"• Total grupos configurados: {len(self.datos_configuracion)}\n")

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

                # Detalles por grupo
                f.write("DETALLES POR GRUPO:\n")
                f.write("=" * 40 + "\n\n")

                for codigo, datos in sorted(self.datos_configuracion.items()):
                    f.write(f"🎓 {codigo} - {datos.get('nombre', 'Sin nombre')}\n")
                    f.write(f"   Coordinador: {datos.get('coordinador', 'No definido')}\n")
                    f.write(f"   Departamento: {datos.get('departamento', 'No definido')}\n")
                    f.write(f"   Grupo: {datos.get('grupo_actual', 'No definido')}\n")

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
            self, "Cargar Configuración de Grupos",
            obtener_ruta_descargas(), "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "grupos" in datos_cargados:
                self.datos_configuracion = datos_cargados["grupos"]
            elif isinstance(datos_cargados, dict):
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Auto-ordenar
            self.ordenar_grupos_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_grupos()
            self.grupo_actual = None
            self.label_grupo_actual.setText("Seleccione un grupo")
            self.info_grupo.setText("ℹ️ Seleccione un grupo para ver sus detalles")
            self.btn_duplicar.setEnabled(False)

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    def guardar_en_archivo(self):
        """Guardar configuración en archivo JSON"""
        ruta_inicial = obtener_ruta_descargas()
        nombre_archivo = f"grupos_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ruta_completa = os.path.join(ruta_inicial, nombre_archivo)

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Grupos",
            ruta_completa,  # Cambiar de solo nombre a ruta completa
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'grupos': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_grupos': len(self.datos_configuracion),
                    'generado_por': 'OPTIM - Configurar Grupos'
                }
            }

            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Éxito", f"Configuración guardada en:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar configuración:\n{str(e)}")

    def guardar_en_sistema(self):
        """Guardar configuración en el sistema principal aplicando eliminaciones y actualizaciones pendientes"""
        try:
            total_grupos = len(self.datos_configuracion)
            grupos_activos = sum(1 for datos in self.datos_configuracion.values() if datos.get('activo', True))
            grupos_a_eliminar = len(self.cambios_pendientes["grupos_eliminados"])
            grupos_a_actualizar = len(self.cambios_pendientes.get("grupos_actualizados", []))

            if total_grupos == 0 and grupos_a_eliminar == 0 and grupos_a_actualizar == 0:
                QMessageBox.warning(self, "Sin Datos", "No hay grupos configurados para guardar.")
                return

            mensaje_confirmacion = f"¿Guardar configuración en el sistema y cerrar?\n\n"
            mensaje_confirmacion += f"📊 Resumen:\n"
            mensaje_confirmacion += f"• {total_grupos} grupos configurados\n"
            mensaje_confirmacion += f"• {grupos_activos} grupos activos\n"

            if grupos_a_eliminar > 0:
                if grupos_a_eliminar == len(self.datos_configuracion) + grupos_a_eliminar:  # Si son todos
                    mensaje_confirmacion += f"• TODOS los grupos ({grupos_a_eliminar}) serán eliminados en cascada\n"
                else:
                    mensaje_confirmacion += f"• {grupos_a_eliminar} grupos serán eliminados en cascada\n"

            if grupos_a_actualizar > 0:
                mensaje_confirmacion += f"• {grupos_a_actualizar} grupos serán actualizados en cascada\n"

            mensaje_confirmacion += f"\nLa configuración se integrará con OPTIM y la ventana se cerrará."

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                mensaje_confirmacion,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Aplicar eliminaciones y actualizaciones pendientes antes de guardar
                total_cambios = grupos_a_eliminar + grupos_a_actualizar
                if total_cambios > 0:
                    self.aplicar_eliminaciones_pendientes()

                # Enviar señal al sistema principal
                self.configuracion_actualizada.emit(self.datos_configuracion)

                # Marcar como guardado
                self.datos_guardados_en_sistema = True
                self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)

                # Cerrar ventana
                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar en el sistema:\n{str(e)}")

    def aplicar_eliminaciones_pendientes(self):
        """Aplicar todas las eliminaciones marcadas en cascada"""
        try:
            grupos_eliminados = self.cambios_pendientes["grupos_eliminados"].copy()

            if not grupos_eliminados:
                return

            self.log_mensaje(f"🗑️ Aplicando eliminación en cascada de {len(grupos_eliminados)} grupos...", "info")

            # Eliminar cada grupo marcado
            for grupo_codigo in grupos_eliminados:
                self.eliminar_grupo_real_completo(grupo_codigo)

            # Limpiar lista de eliminaciones pendientes
            self.cambios_pendientes["grupos_eliminados"].clear()

            self.log_mensaje(f"✅ Eliminación en cascada completada para {len(grupos_eliminados)} grupos", "success")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error aplicando eliminaciones pendientes: {e}", "warning")

    def limpiar_todos_grupos(self):
        """Marcar todos los grupos para eliminación en cascada al guardar"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay grupos para limpiar")
            return

        # Calcular estadísticas para mostrar en el diálogo
        total_grupos = len(self.datos_configuracion)

        # Contar asignaturas afectadas y estadísticas
        asignaturas_afectadas = set()
        total_estudiantes = 0

        for datos in self.datos_configuracion.values():
            asignaturas_asociadas = datos.get('asignaturas_asociadas', [])
            asignaturas_afectadas.update(asignaturas_asociadas)
            total_estudiantes += datos.get('estudiantes_matriculados', 0)

        mensaje = f"¿Está seguro de eliminar TODOS los grupos configurados?\n\n"
        mensaje += f"📊 IMPACTO TOTAL:\n"
        mensaje += f"• {total_grupos} grupos serán eliminados\n"
        mensaje += f"• {len(asignaturas_afectadas)} asignaturas serán afectadas\n"
        mensaje += f"• {total_estudiantes} estudiantes matriculados afectados\n"
        mensaje += f"• Todas las referencias en profesores, alumnos, horarios y aulas\n\n"
        mensaje += f"⚠️ Esta acción marcará TODOS los grupos para eliminación.\n"
        mensaje += f"La eliminación se aplicará al guardar en el sistema.\n\n"
        mensaje += f"Esta acción no se puede deshacer."

        respuesta = QMessageBox.question(
            self, "Limpiar Todos los Grupos",
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            # Marcar TODOS los grupos para eliminación
            grupos_marcados = 0
            for grupo_codigo in list(self.datos_configuracion.keys()):
                if grupo_codigo not in self.cambios_pendientes["grupos_eliminados"]:
                    self.cambios_pendientes["grupos_eliminados"].append(grupo_codigo)
                    grupos_marcados += 1

            # Marcar visualmente TODOS los grupos como eliminados
            self.marcar_todos_grupos_eliminados()

            # Deshabilitar selección
            self.grupo_actual = None
            self.label_grupo_actual.setText("Todos los grupos marcados para eliminación")
            self.info_grupo.setText("⚠️ TODOS los grupos serán eliminados al guardar en el sistema")
            self.texto_stats.setText("⚠️ TODOS los grupos marcados para eliminación en cascada")
            self.btn_duplicar.setEnabled(False)
            self.marcar_cambio_realizado()

            self.log_mensaje(f"📝 {grupos_marcados} grupos marcados para eliminación al guardar", "info")
            QMessageBox.information(self, "Marcados para Eliminación",
                                    f"✅ {grupos_marcados} grupos marcados para eliminación.\n\n"
                                    f"La eliminación en cascada se aplicará al guardar en el sistema.")

    def marcar_todos_grupos_eliminados(self):
        """Marcar visualmente todos los grupos como eliminados"""
        try:
            for row in range(self.list_grupos.count()):
                item = self.list_grupos.item(row)
                if item and item.flags() != Qt.ItemFlag.NoItemFlags:  # Si no está ya deshabilitado
                    # Obtener texto actual y modificarlo
                    texto_actual = item.text()
                    if not texto_actual.startswith("🗑️"):
                        texto_eliminado = f"🗑️ {texto_actual} (ELIMINADO)"
                        item.setText(texto_eliminado)

                    # Cambiar estilo visual
                    item.setBackground(QColor(220, 220, 220))  # Gris claro
                    item.setForeground(QColor(100, 100, 100))  # Texto gris

                    # Deshabilitar selección
                    item.setFlags(Qt.ItemFlag.NoItemFlags)

        except Exception as e:
            self.log_mensaje(f"⚠️ Error marcando todos los grupos en tabla: {e}", "warning")

    def ordenar_grupos_alfabeticamente(self):
        """Reordenar grupos alfabéticamente por código"""
        if not self.datos_configuracion:
            return

        # Crear nuevo diccionario ordenado por código
        grupos_ordenados = {}
        for codigo in sorted(self.datos_configuracion.keys()):
            grupos_ordenados[codigo] = self.datos_configuracion[codigo]

        self.datos_configuracion = grupos_ordenados

    def auto_seleccionar_grupo(self, codigo_grupo):
        """Auto-seleccionar grupo por código"""
        try:
            for i in range(self.list_grupos.count()):
                item = self.list_grupos.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == codigo_grupo:
                    self.list_grupos.setCurrentItem(item)
                    self.seleccionar_grupo(item)
                    break
        except Exception as e:
            self.log_mensaje(f"⚠️ Error auto-seleccionando grupo: {e}", "warning")

    def hay_cambios_sin_guardar(self):
        """Detectar si hay cambios sin guardar"""
        datos_actuales = json.dumps(self.datos_configuracion, sort_keys=True)
        hay_cambios = datos_actuales != self.datos_iniciales

        # Verificar eliminaciones pendientes
        hay_eliminaciones = len(self.cambios_pendientes["grupos_eliminados"]) > 0

        # Verificar actualizaciones pendientes
        hay_actualizaciones = len(self.cambios_pendientes.get("grupos_actualizados", [])) > 0

        if (hay_cambios or hay_eliminaciones or hay_actualizaciones) and not self.datos_guardados_en_sistema:
            return True

        if self.datos_guardados_en_sistema and (hay_cambios or hay_eliminaciones or hay_actualizaciones):
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
            self.log_mensaje("🔚 Cerrando configuración de grupos", "info")
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
                "grupos": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarGrupos",
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
        """Cancelar eliminaciones y actualizaciones marcadas y restaurar vista"""
        try:
            grupos_eliminados = len(self.cambios_pendientes["grupos_eliminados"])
            grupos_actualizados = len(self.cambios_pendientes.get("grupos_actualizados", []))

            if grupos_eliminados > 0 or grupos_actualizados > 0:
                # Restaurar códigos originales para grupos actualizados
                for actualizacion in self.cambios_pendientes.get("grupos_actualizados", []):
                    codigo_original = actualizacion["codigo_original"]
                    codigo_nuevo = actualizacion["codigo_nuevo"]

                    # Si se creó una entrada temporal con el nuevo código, eliminarla
                    if codigo_nuevo in self.datos_configuracion and codigo_original != codigo_nuevo:
                        del self.datos_configuracion[codigo_nuevo]

                # Limpiar listas
                self.cambios_pendientes["grupos_eliminados"].clear()
                if "grupos_actualizados" in self.cambios_pendientes:
                    self.cambios_pendientes["grupos_actualizados"].clear()

                # Recargar tabla para quitar marcas visuales
                self.cargar_lista_grupos()

                # Restaurar interfaz si se había limpiado todo
                if grupos_eliminados > 1:  # Si eran múltiples eliminaciones (limpiar todo)
                    self.label_grupo_actual.setText("Seleccione un grupo")
                    self.info_grupo.setText("ℹ️ Seleccione un grupo para ver sus detalles")
                    self.texto_stats.setText("📈 Presiona 'Actualizar desde Alumnos' para ver estadísticas")
                    self.btn_duplicar.setEnabled(False)

                total_cancelados = grupos_eliminados + grupos_actualizados
                self.log_mensaje(
                    f"↩️ {total_cancelados} cambios cancelados ({grupos_eliminados} eliminaciones, {grupos_actualizados} actualizaciones)",
                    "info")

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
            "grupo_actual": "1º Grupo",
            "coordinador": "Dr. García López",
            "departamento": "Ingeniería Industrial",
            "creditos_totales": 240,
            "plazas": 120,
            "estudiantes_matriculados": 95,
            "horario_tipo": "Mañana",
            "observaciones": "Grupo de nueva implantación",
            "fecha_creacion": datetime.now().isoformat(),
            "activo": True,
            "asignaturas_asociadas": ["FIS1", "MAT1", "QUI1"]
        },
        "B102": {
            "codigo": "B102",
            "nombre": "Grado en Ingeniería Eléctrica",
            "grupo_actual": "1º Grupo",
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
            "grupo_actual": "3º Grupo",
            "coordinador": "Dr. Fernández Castro",
            "departamento": "Ingeniería Electrónica",
            "creditos_totales": 240,
            "plazas": 60,
            "estudiantes_matriculados": 54,
            "horario_tipo": "Tarde",
            "observaciones": "Grupo con alta demanda",
            "fecha_creacion": datetime.now().isoformat(),
            "activo": True,
            "asignaturas_asociadas": ["EANA", "EDIG", "PROG3"]
        }
    }

    window = ConfigurarGrupos(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()