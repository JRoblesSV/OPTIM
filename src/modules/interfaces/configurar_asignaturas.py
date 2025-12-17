
"""
Configurar Asignaturas - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""
import math
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QListWidget,
    QListWidgetItem, QGroupBox, QMessageBox,
    QDialog, QDialogButtonBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor, QCursor


def center_window_on_screen(window, width, height) -> None:
    """Centrar ventana en la pantalla donde está el cursor"""
    try:
        # Obtener la pantalla donde está el cursor
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)

        if screen:
            screen_geometry = screen.availableGeometry()
            center_x = (screen_geometry.width() - width) // 2 + screen_geometry.x()
            center_y = (screen_geometry.height() - height) // 2 + screen_geometry.y()
            final_x = max(screen_geometry.x(), min(center_x, screen_geometry.x() + screen_geometry.width() - width))
            final_y = max(screen_geometry.y(), min(center_y, screen_geometry.y() + screen_geometry.height() - height))
            window.setGeometry(final_x, final_y, width, height)
        else:
            window.setGeometry(100, 100, width, height)
    except Exception:
        window.setGeometry(100, 100, width, height)


def dir_downloads() -> str:
    """Obtener ruta del directorio de Descargas del usuario"""
    home = Path.home()
    for name in ("Descargas", "Downloads"):
        p = home / name
        if p.exists() and p.is_dir():
            return str(p)
    return str(home)


# ========= Diálogo/Ventana Gestión Asignaturas =========
class GestionAsignaturaDialog(QDialog):
    """Dialog para añadir/editar asignatura con configuración completa"""

    # ========= INICIALIZACIÓN =========
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
        window_height = 700
        center_window_on_screen(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

        # Forzar tamaños iguales de ok/cancel
        QTimer.singleShot(50, self.configurar_botones_uniformes_ok_cancel)

        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, True)

        if self.asignatura_existente:
            self.cargar_datos_existentes()

    # ========= CONFIGURACIÓN UI =========
    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        # Datos básicos de la asignatura
        basicos_group = QGroupBox("DATOS BÁSICOS DE LA ASIGNATURA")
        basicos_layout = QFormLayout()

        self.edit_codigo = QLineEdit()
        self.edit_codigo.setPlaceholderText("FIS001, QUI200, PROG101")

        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Física I, Química Orgánica, etc.")

        self.combo_semestre = QComboBox()
        self.combo_semestre.addItems(["1º Semestre", "2º Semestre"])

        self.combo_curso = QComboBox()
        self.combo_curso.addItems(["1º Curso", "2º Curso", "3º Curso", "4º Curso", "5º Curso"])


        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Laboratorio", "Teórica"])

        self.edit_descripcion = QTextEdit()
        self.edit_descripcion.setPlaceholderText("Descripción breve de la asignatura...")
        self.edit_descripcion.setMaximumHeight(80)

        basicos_layout.addRow("Código:", self.edit_codigo)
        basicos_layout.addRow("Nombre:", self.edit_nombre)
        basicos_layout.addRow("Semestre:", self.combo_semestre)
        basicos_layout.addRow("Curso:", self.combo_curso)
        basicos_layout.addRow("Tipo:", self.combo_tipo)
        basicos_layout.addRow("Descripción:", self.edit_descripcion)

        basicos_group.setLayout(basicos_layout)
        layout.addWidget(basicos_group)

        # Gestión dinámica de grupos (como en configurar_horarios.py)
        grupos_group = QGroupBox("GRUPOS QUE CURSAN ESTA ASIGNATURA")
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
        btn_add_grupo.clicked.connect(self.add_grupo)
        grupos_header.addWidget(btn_add_grupo)

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

        # info_grupos = QLabel("💡 Tip: Gestiona los grupos dinámicamente con los botones de arriba")
        # info_grupos.setStyleSheet("color: #cccccc; font-size: 10px; font-style: italic;")
        # grupos_layout.addWidget(info_grupos)

        grupos_group.setLayout(grupos_layout)
        layout.addWidget(grupos_group)

        # Configuración de laboratorio
        # Planificación del grupo
        planificacion_group = QGroupBox("PLANIFICACIÓN DEL GRUPO")
        planificacion_layout = QVBoxLayout()

        # Configuración específica del grupo
        config_grupo_layout = QFormLayout()

        # Duración por sesión
        duracion_layout = QHBoxLayout()
        self.spin_horas_sesion = QSpinBox()
        #self.spin_horas_sesion.setRange(0, 8)
        self.spin_horas_sesion.setRange(2, 2)
        self.spin_horas_sesion.setValue(2)
        self.spin_horas_sesion.setSuffix(" h")
        self.spin_horas_sesion.setReadOnly(True)  # Solo lectura
        self.spin_horas_sesion.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # Deshabilito botones
        duracion_layout.addWidget(self.spin_horas_sesion)

        self.spin_minutos_sesion = QSpinBox()
        #self.spin_minutos_sesion.setRange(0, 45)
        self.spin_minutos_sesion.setRange(0, 0)
        #self.spin_minutos_sesion.setSingleStep(15)
        self.spin_minutos_sesion.setValue(0)
        self.spin_minutos_sesion.setSuffix(" min")
        self.spin_minutos_sesion.setReadOnly(True)  # Solo lectura
        self.spin_minutos_sesion.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)  # Deshabilito botones
        duracion_layout.addWidget(self.spin_minutos_sesion)

        duracion_layout.addWidget(QLabel("por sesión"))
        duracion_layout.addStretch()

        # Semana de inicio
        grupos_layout = QHBoxLayout()
        self.spin_semana_inicio = QSpinBox()
        # Obtener el límite de semanas del calendario
        max_semanas = self.obtener_limite_semanas_calendario()
        self.spin_semana_inicio.setRange(1, max_semanas)
        self.spin_semana_inicio.setValue(min(6, max_semanas))  # 6 o el máximo si es menor
        self.spin_semana_inicio.setSuffix("")
        grupos_layout.addWidget(self.spin_semana_inicio)
        grupos_layout.addWidget(QLabel(""))
        grupos_layout.addStretch()

        # Número de sesiones
        clases_layout = QHBoxLayout()
        self.spin_num_sesiones = QSpinBox()
        self.spin_num_sesiones.setRange(1, 15)
        self.spin_num_sesiones.setValue(3)
        clases_layout.addWidget(self.spin_num_sesiones)
        clases_layout.addWidget(QLabel("durante el semestre"))
        clases_layout.addStretch()

        # Estadísticas del grupo
        #self.label_alumnos_grupo = QLabel("Alumnos: 0 alumnos")
        #self.label_alumnos_grupo.setStyleSheet("color: #cccccc; font-size: 11px;")

        config_grupo_layout.addRow(
            self.crear_label_con_info("Duración:",
                                       "   • Duración de cada sesión de laboratorio.\n\n"
                                                "   • Actualmente serán sesiones de 2h siempre\n"),
            duracion_layout
        )

        config_grupo_layout.addRow(
            self.crear_label_con_info("Semana de inicio:",
                                      "Semana en la que comienza la asignatura\n\n"
                                               "- Ejemplo: Si empieza en la 6ª semana → poner 6\n\n"
                                               "   • El máximo se ajusta automáticamente según\n"
                                               "   • las semanas configuradas en el calendario"),
            grupos_layout
        )

        config_grupo_layout.addRow(
            self.crear_label_con_info("Número de sesiones:",
                                       "Total de sesiones de laboratorio para un grupo en el semestre\n\n"
                                                "Cuenta todas las veces que los alumnos de un solo grupo irán al laboratorio\n\n"
                                                "- Ejemplos:\n"
                                                "   • 3 prácticas de 2 sesiones cada una = 6 sesiones\n"
                                                "   • 4 prácticas de 1 sesión cada una = 4 sesiones\n"
                                                "   • Práctica mixta: 2+1+2+1 = 6 sesiones"),
            clases_layout
        )
        #config_grupo_layout.addRow("Alumnos:", con_lab_anterior)

        planificacion_layout.addLayout(config_grupo_layout)
        planificacion_group.setLayout(planificacion_layout)
        layout.addWidget(planificacion_group)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def configurar_botones_uniformes_ok_cancel(self) -> None:
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

    # ========= TEMA / ESTILO =========
    def apply_dark_theme(self) -> None:
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

            /* Botones OK/CANCEL */
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

    def get_button_style(self, color) -> str:
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

    def crear_label_con_info(self, texto_label, texto_info) -> QWidget:
        """Crear label con icono de información y tooltip"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(texto_label)
        layout.addWidget(label)

        # Botón de información
        btn_info = QPushButton("ℹ️")
        btn_info.setFixedSize(20, 20)
        btn_info.setToolTip(texto_info)
        btn_info.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #666;
                border-radius: 10px;
                font-size: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #4a9eff;
                border-color: #4a9eff;
            }
        """)
        layout.addWidget(btn_info)
        layout.addStretch()

        return container

    # ========= CARGA / DATOS EXISTENTES =========
    def cargar_datos_existentes(self) -> None:
        """Cargar datos de la asignatura existente. Utilizado al abrir."""
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
            self.combo_curso.setCurrentIndex(index)

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
                    'semana_inicio': config_lab.get('semana_inicio', 6),
                    'num_sesiones': config_lab.get('num_sesiones', 3)
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

    def get_datos_asignatura(self) -> dict:
        """Obtener datos configurados. Utilizado para guardar al dar ok."""
        # Guardar configuración del grupo actual si hay uno seleccionado
        item_actual = self.list_grupos_dialog.currentItem()
        if item_actual:
            codigo_grupo_actual = item_actual.data(Qt.ItemDataRole.UserRole)
            self.configuraciones_grupo[codigo_grupo_actual] = {
                'horas_por_sesion': self.spin_horas_sesion.value(),
                'minutos_por_sesion': self.spin_minutos_sesion.value(),
                'semana_inicio': self.spin_semana_inicio.value(),
                'num_sesiones': self.spin_num_sesiones.value()
            }

        # Generar estructura de grupos_asociados
        grupos_asociados = {}
        for codigo_grupo in self.get_grupos_seleccionados():
            config = self.configuraciones_grupo.get(codigo_grupo, {
                'horas_por_sesion': 2,
                'minutos_por_sesion': 0,
                'semana_inicio': 6,
                'num_sesiones': 3
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

    # ========= GESTIÓN DE GRUPOS ASOCIADOS (añadir, eliminar) =========
    def add_grupo(self) -> None:
        """Añadir nuevo grupo a la asignatura"""
        if not self.grupos_disponibles:
            QMessageBox.information(self, "Sin Grupos",
                                    "No hay grupos disponibles para asociar.\n"
                                    "Configure primero los grupos en el sistema.")
            return

        # Obtener grupos ya agregados
        grupos_ya_agregados = set()
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            grupos_ya_agregados.add(item.data(Qt.ItemDataRole.UserRole))

        # Crear lista de todos los grupos disponibles (sin filtrar)
        opciones_grupos = []
        for codigo, datos in self.grupos_disponibles.items():
            if codigo not in grupos_ya_agregados:
                nombre = datos.get('nombre', codigo)
                coordinador = datos.get('coordinador', 'Sin coordinador')
                opciones_grupos.append(f"{codigo} - {nombre} ({coordinador})")

        if not opciones_grupos:
            QMessageBox.information(self, "Sin Grupos",
                                    "No hay más grupos disponibles para agregar.")
            return

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

    def eliminar_grupo_seleccionado(self) -> None:
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

    def ordenar_grupos_lista(self) -> None:
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

    def get_grupos_seleccionados(self) -> list[str]:
        """Obtener lista de grupos de la lista dinámica"""
        grupos = []
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            grupos.append(item.data(Qt.ItemDataRole.UserRole))
        return sorted(grupos)

    def auto_seleccionar_grupo_dialog(self, grupo) -> None:
        """Auto-seleccionar grupo en el dialog"""
        for i in range(self.list_grupos_dialog.count()):
            item = self.list_grupos_dialog.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == grupo:
                self.list_grupos_dialog.setCurrentItem(item)
                break

    # ========= CONFIGURACIÓN DE GRUPO / LABORATORIO =========
    def grupo_seleccionado_cambio(self) -> None:
        """Cambiar configuración cuando se selecciona otro grupo"""
        item_actual = self.list_grupos_dialog.currentItem()
        if not item_actual:
            return

        # Guardar configuración del grupo anterior si existe
        if hasattr(self, 'grupo_anterior') and self.grupo_anterior and hasattr(self, 'configuraciones_grupo'):
            self.configuraciones_grupo[self.grupo_anterior] = {
                'horas_por_sesion': self.spin_horas_sesion.value(),
                'minutos_por_sesion': self.spin_minutos_sesion.value(),
                'semana_inicio': self.spin_semana_inicio.value(),
                'num_sesiones': self.spin_num_sesiones.value()
            }

        # Cargar nuevo grupo
        codigo_grupo = item_actual.data(Qt.ItemDataRole.UserRole)
        self.grupo_anterior = codigo_grupo
        self.actualizar_titulo_planificacion(codigo_grupo)
        self.cargar_configuracion_grupo(codigo_grupo)

    def guardar_configuracion_grupo(self, codigo_grupo) -> None:
        """Guardar configuración actual del grupo"""
        if not hasattr(self, 'configuraciones_grupo'):
            self.configuraciones_grupo = {}

        self.configuraciones_grupo[codigo_grupo] = {
            'horas_por_sesion': self.spin_horas_sesion.value(),
            'minutos_por_sesion': self.spin_minutos_sesion.value(),
            'semana_inicio': self.spin_semana_inicio.value(),
            'num_sesiones': self.spin_num_sesiones.value()
        }

    def cargar_configuracion_grupo(self, codigo_grupo) -> None:
        """Cargar configuración del grupo seleccionado"""
        if not hasattr(self, 'configuraciones_grupo'):
            self.configuraciones_grupo = {}

        if codigo_grupo in self.configuraciones_grupo:
            config = self.configuraciones_grupo[codigo_grupo]
            self.spin_horas_sesion.setValue(config.get('horas_por_sesion', 2))
            self.spin_minutos_sesion.setValue(config.get('minutos_por_sesion', 0))
            self.spin_semana_inicio.setValue(config.get('semana_inicio', 6))
            self.spin_num_sesiones.setValue(config.get('num_sesiones', 3))
        else:
            # Valores por defecto para grupo nuevo
            self.spin_horas_sesion.setValue(2)
            self.spin_minutos_sesion.setValue(0)
            self.spin_semana_inicio.setValue(6)
            self.spin_num_sesiones.setValue(3)

    def actualizar_titulo_planificacion(self, codigo_grupo=None) -> None:
        """Actualizar título con el grupo seleccionado"""
        for child in self.findChildren(QGroupBox):
            if "PLANIFICACIÓN" in child.title():
                if codigo_grupo:
                    child.setTitle(f"PLANIFICACIÓN LABORATORIO DEL GRUPO - {codigo_grupo}")
                else:
                    child.setTitle("PLANIFICACIÓN LABORATORIO DEL GRUPO")
                break

    # ========= CÁLCULO =========
    def calcular_grupos_posibles(self, semana_inicio, num_sesiones, total_semanas) -> tuple[int, list[str], bool, str]:
        """Calcula cuántos grupos (letras) son posibles con la configuración"""
        if semana_inicio < 1 or semana_inicio > total_semanas:
            return (0, [], False, f"Semana de inicio debe estar entre 1 y {total_semanas}")

        if num_sesiones < 1:
            return (0, [], False, "Número de sesiones debe ser mayor a 0")

        # Calcular semanas disponibles desde semana_inicio hasta el final
        semanas_disponibles = total_semanas - semana_inicio + 1

        # Verificar si la división es entera (sin resto)
        if semanas_disponibles % num_sesiones != 0:
            # Calcular divisores válidos para mostrar opciones
            divisores_validos = []
            for i in range(1, semanas_disponibles + 1):
                if semanas_disponibles % i == 0:
                    divisores_validos.append(i)

            mensaje = (
                f"⚠️ CONFIGURACIÓN INVÁLIDA\n\n"
                f"  • Tenemos [{total_semanas}] semanas, si semana de inicio [{semana_inicio}], tenemos [{semanas_disponibles}] semanas disponibles.\n"
                f"  • Con [{num_sesiones}] sesiones, NO se puede dividir equitativamente.\n\n"
                f"- Opciones válidas de sesiones: {', '.join(map(str, divisores_validos))}\n\n"
                f"💡 Ejemplo:\n"
                f"  • Si eliges [{divisores_validos[0]}] sesión(es): [{semanas_disponibles // divisores_validos[0]}] grupos\n"
                f"  • Si eliges [{divisores_validos[-1]}] sesión(es): [{semanas_disponibles // divisores_validos[-1]}] grupo(s)"
            )
            return (0, [], False, mensaje)

        # Calcular grupos posibles
        grupos_posibles = semanas_disponibles // num_sesiones

        # Generar letras (A, B, C, D, E, F...)
        letras = [chr(65 + i) for i in range(grupos_posibles)]  # 65 = 'A' en ASCII

        mensaje_ok = (
            f"- Configuración válida -\n\n"
            f"   • Grupos posibles: {grupos_posibles} ({', '.join(letras)})\n"
            f"   • Semanas disponibles: {semanas_disponibles}\n"
            f"   • Sesiones por grupo: {num_sesiones}"
        )

        return (grupos_posibles, letras, True, mensaje_ok)

    # ========= VALIDACIÓN =========
    def validar_y_aceptar(self) -> None:
        """Validar datos antes de aceptar"""
        # --- Validaciones básicas de campos ---
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

        # --- Asegurar que la config del grupo actualmente seleccionado quede guardada ---
        item_actual = self.list_grupos_dialog.currentItem()
        if item_actual:
            self.guardar_configuracion_grupo(item_actual.data(Qt.ItemDataRole.UserRole))

        # --- Validación de laboratorio para TODOS los grupos ---
        total_semanas = self.obtener_limite_semanas_calendario()

        errores: list[str] = []
        resumen_ok: list[str] = []
        primer_grupo_invalido: str | None = None

        for codigo_grupo in grupos_seleccionados:
            cfg = self.config_por_grupo(codigo_grupo)
            semana_inicio = int(cfg.get('semana_inicio', 0))
            num_sesiones = int(cfg.get('num_sesiones', 0))

            # Analizar/Validar configuración
            grupos, letras, valido, mensaje = self.calcular_grupos_posibles(
                semana_inicio, num_sesiones, total_semanas
            )

            if not valido:
                if primer_grupo_invalido is None:
                    primer_grupo_invalido = codigo_grupo
                # Mensaje resumido por grupo
                errores.append(f"====== {codigo_grupo} ======\n{mensaje}")
            else:
                resumen_ok.append(f"• {codigo_grupo}: "
                                  f"\n   - {grupos} grupo(s) disponibe(s)"
                                  f"\n   - letras que se pueden utilizar en horario: {', '.join(letras)} "
                                  f"\n   - semanas disp.: {total_semanas - semana_inicio + 1}, sesiones: {num_sesiones}")

        if errores:
            # Seleccionar el primer grupo problemático para facilitar la corrección
            if primer_grupo_invalido:
                self.auto_seleccionar_grupo_dialog(primer_grupo_invalido)

            QMessageBox.warning(
                self,
                "Configuración de Laboratorio Inválida",
                "Se han detectado problemas en la configuración de estos grupos:\n\n"
                + "\n\n".join(errores)
                + "\n\nCorrige los valores y vuelve a intentarlo."
            )
            return

        # Si son válidos, muestra un resumen y acepta
        QMessageBox.information(
            self,
            "Configuración de Laboratorio Válida",
            "Todos los grupos tienen una configuración válida:\n\n" + "\n".join(resumen_ok)
        )

        self.accept()

    def config_por_grupo(self, codigo_grupo: str) -> dict:
        """Obtener configuración del grupo con valores por defecto si no existe."""
        return self.configuraciones_grupo.get(codigo_grupo, {
            'horas_por_sesion': 2,
            'minutos_por_sesion': 0,
            'semana_inicio': 0,
            'num_sesiones': 0
        })

    # ========= OTROS =========
    def obtener_limite_semanas_calendario(self) -> int:
        """Obtener el límite de semanas desde el calendario"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'parent_window'):
                ventana_principal = self.parent_window.parent_window
                if hasattr(ventana_principal, 'configuracion'):
                    config_calendario = ventana_principal.configuracion["configuracion"].get("calendario", {})
                    if config_calendario.get("configurado") and config_calendario.get("datos"):
                        metadata = config_calendario["datos"].get("metadata", {})
                        return metadata.get("limite_semanas", 14)
            return 14
        except:
            return 14

    def hex_to_rgb(self, hex_color) -> str:
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))


# ========= Ventana Principal =========
class ConfigurarAsignaturasWindow(QMainWindow):
    """Ventana principal para configurar asignaturas del sistema"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    # ========= INICIALIZACIÓN =========
    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Asignaturas - OPTIM")
        window_width = 1400
        window_height = 750
        center_window_on_screen(self, window_width, window_height)

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
            "aulas_eliminadas": [],
            "asignaturas_actualizadas": []
        }

        # Estructura de datos principal
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("Cargando configuración existente de asignaturas...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("Iniciando configuración nueva de asignaturas...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.asignatura_actual = None

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    # ========= CONFIGURACIÓN UI =========
    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("CONFIGURACIÓN DE ASIGNATURAS")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Información del flujo
        info_label = QLabel("Gestiona las asignaturas, grupos que las cursan y su configuración de laboratorio.")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de asignaturas
        left_panel = QGroupBox("ASIGNATURAS CONFIGURADAS")
        left_layout = QVBoxLayout()

        # Header con botones de gestión
        asignaturas_header = QHBoxLayout()
        asignaturas_header.addWidget(QLabel("Asignaturas:"))
        asignaturas_header.addStretch()

        btn_add_asignatura = self.crear_boton_accion("➕", "#4CAF50", "Añadir nueva asignatura")
        btn_add_asignatura.clicked.connect(self.add_asignatura)

        btn_edit_asignatura = self.crear_boton_accion("✏️", "#a8af4c", "Editar asignatura seleccionada")
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
        center_panel = QGroupBox("DETALLES DE LA ASIGNATURA")
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

        # Estadísticas
        stats_group = QGroupBox("ESTADÍSTICAS")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)

        botones_stats_layout = QHBoxLayout()
        self.btn_calcular_grupos = QPushButton("Actualizar Estadísticas")
        self.btn_calcular_grupos.setMaximumWidth(200)
        self.btn_calcular_grupos.clicked.connect(self.actualizar_estadisticas)
        botones_stats_layout.addWidget(self.btn_calcular_grupos)
        botones_stats_layout.addStretch()

        stats_layout.addLayout(botones_stats_layout)

        self.texto_stats = QTextEdit()
        self.texto_stats.setMaximumHeight(150)
        self.texto_stats.setReadOnly(True)
        self.texto_stats.setText("Presiona 'Actualizar Estadísticas' para ver estadísticas")
        stats_layout.addWidget(self.texto_stats)

        stats_group.setLayout(stats_layout)
        center_layout.addWidget(stats_group)

        center_panel.setLayout(center_layout)
        content_layout.addWidget(center_panel)

        # Columna derecha - Acciones y configuración
        right_panel = QGroupBox("⚙️ GESTIÓN Y CONFIGURACIÓN")
        right_layout = QVBoxLayout()

        # Acciones rápidas
        acciones_group = QGroupBox("⚡ ACCIONES RÁPIDAS")
        acciones_layout = QVBoxLayout()

        self.btn_duplicar = QPushButton("Duplicar Asignatura Seleccionada")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_asignatura_seleccionada)
        acciones_layout.addWidget(self.btn_duplicar)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Import
        importar_group = QGroupBox("📥 IMPORTAR DATOS")
        importar_layout = QVBoxLayout()

        self.btn_cargar = QPushButton("Importar Datos")
        self.btn_cargar.setToolTip("Importar configuración desde JSON")
        self.btn_cargar.clicked.connect(self.import_config)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Export
        exportar_group = QGroupBox("💾 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

        self.btn_exportar_json = QPushButton("Exportar Datos")
        self.btn_exportar_json.setToolTip("Exportar configuración a JSON")
        self.btn_exportar_json.clicked.connect(self.export_config)
        exportar_layout.addWidget(self.btn_exportar_json)

        self.btn_exportar_estadisticas = QPushButton("Exportar Estadísticas")
        self.btn_exportar_estadisticas.setToolTip("Exportar Estadisticas en TXT")
        self.btn_exportar_estadisticas.clicked.connect(self.exportar_estadisticas)
        exportar_layout.addWidget(self.btn_exportar_estadisticas)

        exportar_group.setLayout(exportar_layout)
        right_layout.addWidget(exportar_group)

        # Botones principales
        botones_principales_group = QGroupBox("💾 GUARDAR CONFIGURACIÓN")
        botones_layout = QVBoxLayout()

        self.btn_guardar_sistema = QPushButton("Guardar en Sistema")
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

        self.btn_limpiar_todo = QPushButton("Limpiar Todo")
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

    def apply_dark_theme(self) -> None:
        """Aplicar tema oscuro con tooltips"""
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

    def crear_boton_accion(self, icono, color, tooltip) -> QPushButton:
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

    def conectar_signals(self) -> None:
        """Conectar señales de la interfaz"""
        self.list_asignaturas.itemClicked.connect(self.seleccionar_asignatura)

    # ========= OBTENCIÓN DE DATOS DEL SISTEMA =========
    def obtener_alumnos_del_sistema(self) -> dict:
        """Obtener alumnos configurados desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_alumnos = self.parent_window.configuracion["configuracion"].get("alumnos", {})
                if config_alumnos.get("configurado") and config_alumnos.get("datos"):
                    return config_alumnos["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"Error obteniendo alumnos del sistema: {e}", "warning")
            return {}

    def obtener_aulas_del_sistema(self) -> dict:
        """Obtener aulas configuradas desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_aulas = self.parent_window.configuracion["configuracion"].get("aulas", {})
                if config_aulas.get("configurado") and config_aulas.get("datos"):
                    return config_aulas["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"Error obteniendo aulas del sistema: {e}", "warning")
            return {}

    def obtener_horarios_del_sistema(self) -> dict:
        """Obtener horarios configurados desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_horarios = self.parent_window.configuracion["configuracion"].get("horarios", {})
                if config_horarios.get("configurado") and config_horarios.get("datos"):
                    return config_horarios["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"Error obteniendo horarios del sistema: {e}", "warning")
            return {}

    def obtener_grupos_del_sistema(self) -> dict:
        """Obtener grupos configurados desde el sistema global"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                config_grupos = self.parent_window.configuracion["configuracion"].get("grupos", {})
                if config_grupos.get("configurado") and config_grupos.get("datos"):
                    return config_grupos["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"Error obteniendo grupos del sistema: {e}", "warning")
            return {}

    # ========= CARGA INICIAL / ESTADO =========
    def cargar_datos_iniciales(self) -> None:
        """Cargar datos existentes al inicializar"""
        try:
            # Ordenar asignaturas alfabéticamente
            self.ordenar_asignaturas_alfabeticamente()

            # Cargar lista
            self.cargar_lista_asignaturas()

            # Mostrar resumen
            total_asignaturas = len(self.datos_configuracion)

            # Actualizar estadísticas
            #self.actualizar_estadisticas()

            if total_asignaturas > 0:
                self.log_mensaje(
                    f"Datos cargados: {total_asignaturas} asignaturas configuradas",
                    "success"
                )
                self.auto_seleccionar_primera_asignatura()
            else:
                self.log_mensaje("No hay asignaturas configuradas - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"Error cargando datos iniciales: {e}", "warning")

    def auto_seleccionar_primera_asignatura(self) -> None:
        """Auto-seleccionar primera asignatura disponible"""
        try:
            if self.list_asignaturas.count() > 0:
                primer_item = self.list_asignaturas.item(0)
                self.list_asignaturas.setCurrentItem(primer_item)
                self.seleccionar_asignatura(primer_item)
                self.log_mensaje(f"Auto-seleccionada: {primer_item.text()}", "info")
        except Exception as e:
            self.log_mensaje(f"Error auto-seleccionando asignatura: {e}", "warning")

    def cargar_lista_asignaturas(self) -> None:
        """Cargar asignaturas en la lista visual"""
        self.list_asignaturas.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("⚠️ No hay asignaturas configuradas")
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
            icono = "🔬" if tipo == "Laboratorio" else "📖"

            texto_item = f"{icono} {codigo} - {nombre}"
            if total_matriculados > 0:
                texto_item += f" ({sin_lab_anterior}/{total_matriculados} alumnos)"
            texto_item += f"\n    {semestre} | {grupos_str}"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, codigo)
            self.list_asignaturas.addItem(item)

    def ordenar_asignaturas_alfabeticamente(self) -> None:
        """Reordenar asignaturas alfabéticamente por código"""
        if not self.datos_configuracion:
            return

        # Crear nuevo diccionario ordenado por código
        asignaturas_ordenadas = {}
        for codigo in sorted(self.datos_configuracion.keys()):
            asignaturas_ordenadas[codigo] = self.datos_configuracion[codigo]

        self.datos_configuracion = asignaturas_ordenadas

    # ========= SELECCIONES =========
    def seleccionar_asignatura(self, item) -> None:
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
        self.label_asignatura_actual.setText(f"{codigo} - {nombre}")

        # Mostrar información detallada
        info = f"ASIGNATURA: {codigo} - {nombre}\n"
        info += f"  • Semestre: {datos.get('semestre', 'No definido')}\n"
        info += f"  • Curso: {datos.get('grupo', 'No definido')}\n"
        info += f"  • Tipo: {datos.get('tipo', 'No definido')}\n"
        info += f"  • Descripción: {datos.get('descripcion', 'Sin descripción')}\n\n"

        # grupos que la cursan
        grupos = datos.get('grupos_asociados', [])
        if grupos:
            info += f"GRUPOS QUE LA CURSAN ({len(grupos)}):\n"
            for grupo in grupos:
                # Buscar nombre del grupo
                nombre_grupo = grupo
                if grupo in self.grupos_disponibles:
                    nombre_grupo = self.grupos_disponibles[grupo].get('nombre', grupo)
                info += f"  • {grupo} - {nombre_grupo}\n"
        else:
            info += f"  • GRUPOS: Sin grupos asignados\n"
        info += "\n"

        # Configuración laboratorio
        info += f"CONFIGURACIÓN LABORATORIO:\n"
        if grupos:
            for codigo_grupo, datos_grupo in grupos.items():

                # Información básica del grupo
                nombre_grupo = codigo_grupo
                if codigo_grupo in self.grupos_disponibles:
                    nombre_grupo = self.grupos_disponibles[codigo_grupo].get("nombre", codigo_grupo)

                info += f"  • {codigo_grupo} - {nombre_grupo}\n"

                # Configuración del laboratorio
                cfg = datos_grupo.get("configuracion_laboratorio", {})

                horas = cfg.get("horas_por_sesion", 0)
                minutos = cfg.get("minutos_por_sesion", 0)
                semana = cfg.get("semana_inicio", "No definido")
                sesiones = cfg.get("num_sesiones", "No definido")

                info += f"      - Duración: {horas}h {minutos}min\n"
                info += f"      - Semana inicio: {semana}\n"
                info += f"      - Nº Sesiones: {sesiones}\n"

        else:
            info += "  • No hay grupos asociados\n"

        info += "\n"

        # Estadísticas
        stats = datos.get('estadisticas_calculadas', {})
        info += f"ESTADÍSTICAS:\n"
        info += f"  • Total matriculados: {stats.get('total_matriculados', 0)}\n"
        info += f"  • Con lab anterior: {stats.get('con_lab_anterior', 0)} (filtrados)\n"
        info += f"  • Sin lab anterior: {stats.get('sin_lab_anterior', 0)} (para scheduling)\n"
        info += f"  • Grupos recomendados: {stats.get('grupos_recomendados', 0)}\n"

        info += "\n"

        ultima_actualizacion = stats.get('ultima_actualizacion', '')
        if ultima_actualizacion:
            try:
                fecha = datetime.fromisoformat(ultima_actualizacion.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
                info += f"Última actualización: {fecha}"
            except:
                info += f"Última actualización: {ultima_actualizacion}"

        self.info_asignatura.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)

    def auto_seleccionar_asignatura(self, codigo_asignatura) -> None:
        """Auto-seleccionar asignatura por código"""
        try:
            for i in range(self.list_asignaturas.count()):
                item = self.list_asignaturas.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == codigo_asignatura:
                    self.list_asignaturas.setCurrentItem(item)
                    self.seleccionar_asignatura(item)
                    break
        except Exception as e:
            self.log_mensaje(f"Error auto-seleccionando asignatura: {e}", "warning")

    # ========= CRUD DE ASIGNATURAS (CON SINCRONIZACIÓN) =========
    def add_asignatura(self) -> None:
        """Añadir asignatura (con sincronización)"""
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

    def editar_asignatura_seleccionada(self) -> None:
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

            # EDICIÓN EN CASCADA: Si cambió el código, marcar para actualización pendiente
            if codigo_nuevo != codigo_original:
                # Verificar si ya está marcada
                actualizacion_existente = None
                for act in self.cambios_pendientes["asignaturas_actualizadas"]:
                    if act["codigo_original"] == codigo_original:
                        actualizacion_existente = act
                        break

                if actualizacion_existente:
                    # Actualizar el registro existente
                    actualizacion_existente["codigo_nuevo"] = codigo_nuevo
                    actualizacion_existente["datos"] = datos_nuevos
                else:
                    # Agregar nueva actualización pendiente
                    self.cambios_pendientes["asignaturas_actualizadas"].append({
                        "codigo_original": codigo_original,
                        "codigo_nuevo": codigo_nuevo,
                        "datos": datos_nuevos
                    })

            # SINCRONIZACIÓN: Aplicar cambios de grupos
            if grupos_añadidos or grupos_eliminados:
                self.sincronizar_con_grupos(codigo_nuevo, grupos_añadidos, grupos_eliminados)

            # SINCRONIZACION: franjas horarias
            if grupos_eliminados:
                self.eliminar_asignatura_de_franjas_horario(codigo_nuevo, grupos_eliminados)

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

    def duplicar_asignatura_seleccionada(self) -> None:
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

            # SINCRONIZACIÓN: Notificar grupos asociados
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

    def eliminar_asignatura_seleccionada(self) -> None:
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

            self.log_mensaje(f"Asignatura {asignatura_codigo} marcada para eliminación al guardar", "info")
            QMessageBox.information(self, "Marcada para Eliminación",
                                    f"Asignatura '{asignatura_codigo}' marcada para eliminación.\n\nLa eliminación se aplicará al guardar en el sistema.")


    # ========= SINCRONIZACIÓN =========
    def sincronizar_con_grupos(self, asignatura_codigo, grupos_nuevos, grupos_eliminados) -> None:
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
                self.log_mensaje(f"Sincronizados grupos desde asignatura {asignatura_codigo}", "info")

        except Exception as e:
            self.log_mensaje(f"Error sincronizando con grupos: {e}", "warning")

    # ========= EDITAR EN CASCADA =========
    def editar_asignatura_real_completa(self, codigo_original, codigo_nuevo) -> None:
        """Editar asignatura realmente del sistema completo en cascada"""
        try:
            if not self.parent_window:
                self.log_mensaje(f"No se puede editar {codigo_original}: sin parent_window", "warning")
                return

            # Obtener datos de la asignatura después de editar
            datos_asignatura = self.datos_configuracion.get(codigo_nuevo)
            if not datos_asignatura:
                self.log_mensaje(f"Asignatura {codigo_nuevo} no encontrada en configuración", "warning")
                return

            grupos_asociados = datos_asignatura.get('grupos_asociados', [])

            self.log_mensaje(f"Editando asignatura {codigo_original} → {codigo_nuevo} del sistema completo...", "info")

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

            self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada completamente del sistema",
                             "success")

        except Exception as e:
            self.log_mensaje(f"Error en edición completa de asignatura {codigo_original}: {e}", "error")

    def editar_asignatura_en_grupos_sistema(self, codigo_original, codigo_nuevo, grupos_asociados) -> None:
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
                        self.log_mensaje(
                            f"Asignatura {codigo_original} → {codigo_nuevo} editada en grupo {grupo_codigo}",
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
                        f"Asignatura {codigo_original} → {codigo_nuevo} editada en grupo {grupo_codigo} (referencia huérfana)",
                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["grupos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de grupos",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"Error editando asignatura en grupos: {e}", "warning")

    def editar_asignatura_en_profesores_sistema(self, codigo_original, codigo_nuevo) -> None:
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
                            f"Asignatura {codigo_original} → {codigo_nuevo} editada en profesor {nombre_profesor} ({profesor_id})",
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
                                        f"Horario bloqueado de {codigo_original} → {codigo_nuevo} editado en profesor {profesor_id}",
                                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["profesores"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de profesores",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"Error editando asignatura en profesores: {e}", "warning")

    def editar_asignatura_en_alumnos_sistema(self, codigo_original, codigo_nuevo) -> None:
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
                        f"Código de asignatura {codigo_original} → {codigo_nuevo} editado en alumno {nombre_alumno}",
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
                            f"Asignatura {codigo_original} → {codigo_nuevo} editada en matriculadas del alumno {nombre_alumno}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["alumnos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"Asignatura {codigo_original} → {codigo_nuevo} editada en {alumnos_modificados} referencias en alumnos",
                    "success")

        except Exception as e:
            self.log_mensaje(f"Error editando asignatura en alumnos: {e}", "warning")

    def editar_asignatura_en_horarios_sistema(self, codigo_original, codigo_nuevo) -> None:
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
                            f"Asignatura {asignatura_encontrada} → {codigo_nuevo} editada en semestre {semestre}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de horarios",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"Error editando asignatura en horarios: {e}", "warning")

    def editar_asignatura_en_aulas_sistema(self, codigo_original, codigo_nuevo) -> None:
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
                        self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada en aula {aula_nombre}",
                                         "info")

                # Editar ocupaciones relacionadas con la asignatura si existen
                if "ocupaciones_programadas" in aula_data:
                    for ocupacion in aula_data["ocupaciones_programadas"]:
                        if ocupacion.get("asignatura") == codigo_original:
                            ocupacion["asignatura"] = codigo_nuevo
                            cambios_realizados = True
                            self.log_mensaje(
                                f"Ocupación de {codigo_original} → {codigo_nuevo} editada en aula {aula_nombre}",
                                "info")
                        if ocupacion.get("codigo_asignatura") == codigo_original:
                            ocupacion["codigo_asignatura"] = codigo_nuevo
                            cambios_realizados = True
                            self.log_mensaje(
                                f"Código de ocupación {codigo_original} → {codigo_nuevo} editado en aula {aula_nombre}",
                                "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["aulas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de aulas", "success")

        except Exception as e:
            self.log_mensaje(f"Error editando asignatura en aulas: {e}", "warning")

    def editar_asignatura_en_asignaturas_sistema(self, codigo_original, codigo_nuevo) -> None:
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
                    self.log_mensaje(f"Asignatura {codigo_original} → {codigo_nuevo} editada en módulo de asignaturas",
                                     "info")

        except Exception as e:
            self.log_mensaje(f"Error editando asignatura en asignaturas: {e}", "warning")

    def aplicar_actualizaciones_pendientes(self) -> None:
        """Aplicar todas las actualizaciones marcadas en cascada"""
        try:
            asignaturas_actualizadas = self.cambios_pendientes["asignaturas_actualizadas"].copy()

            if not asignaturas_actualizadas:
                return

            self.log_mensaje(f"Aplicando actualización en cascada de {len(asignaturas_actualizadas)} asignaturas",
                             "info")

            # Actualizar cada asignatura marcada
            for actualizacion in asignaturas_actualizadas:
                codigo_original = actualizacion["codigo_original"]
                codigo_nuevo = actualizacion["codigo_nuevo"]
                self.editar_asignatura_real_completa(codigo_original, codigo_nuevo)

            # Limpiar lista de actualizaciones pendientes
            self.cambios_pendientes["asignaturas_actualizadas"].clear()

            self.log_mensaje(f"Actualización en cascada completada para {len(asignaturas_actualizadas)} asignaturas",
                             "success")

        except Exception as e:
            self.log_mensaje(f"Error aplicando actualizaciones pendientes: {e}", "warning")

    # ========= ELIMINAR EN CASCADA =========
    def eliminar_asignatura_de_franjas_horario(self, asignatura_codigo, grupos_eliminados, semestres=None) -> None:
        """Eliminar grupos de las franjas (horarios_grid) para una asignatura"""
        try:
            cfg = self.parent_window.configuracion.get("configuracion", {})
            mod_horarios = cfg.get("horarios", {})
            datos_hor = mod_horarios.get("datos", {})
            if not datos_hor:
                return

            # Determinar semestres a procesar
            if semestres is None:
                # Solo claves tipo str (p.ej., "1", "2")
                semestres = [s for s in datos_hor.keys() if isinstance(s, str)]

            # Normalizar el parámetro a conjunto para búsquedas O(1)
            grupos_objetivo = set(grupos_eliminados or [])
            if not grupos_objetivo:
                return

            celdas_modificadas = 0
            franjas_eliminadas_total = 0
            dias_eliminados_total = 0

            for semestre in semestres:
                sem_data = datos_hor.get(semestre)
                if not isinstance(sem_data, dict):
                    continue

                asig_data = sem_data.get(asignatura_codigo)
                if not isinstance(asig_data, dict):
                    continue

                grid = asig_data.get("horarios_grid", {})
                if not isinstance(grid, dict):
                    continue

                franjas_a_borrar = []

                for franja, dias in grid.items():
                    if not isinstance(dias, dict):
                        continue

                    dias_a_borrar = []

                    for dia, celda in dias.items():
                        # Celda esperada: {"grupos": [..], "mixta": bool}
                        if not isinstance(celda, dict):
                            continue

                        grupos = celda.get("grupos")
                        if isinstance(grupos, list):
                            # Filtrar los grupos eliminados
                            nuevos = [g for g in grupos if g not in grupos_objetivo]
                            if len(nuevos) != len(grupos):
                                celda["grupos"] = nuevos
                                celdas_modificadas += 1
                                self.log_mensaje(
                                    f"Limpiada franja {franja} / {dia} en {asignatura_codigo}: "
                                    f"eliminados {sorted(grupos_objetivo.intersection(grupos))}",
                                    "info"
                                )

                                # Si el día quedó vacío, marcar para borrar
                                if not celda["grupos"]:
                                    dias_a_borrar.append(dia)

                    # Borrar días vacíos
                    for dia in dias_a_borrar:
                        del dias[dia]
                        dias_eliminados_total += 1
                        self.log_mensaje(
                            f"Día '{dia}' eliminado de {asignatura_codigo}.{franja} (sin grupos)",
                            "info"
                        )

                    # Si la franja quedó sin días, marcar para borrar
                    if not dias:
                        franjas_a_borrar.append(franja)

                # Borrar franjas vacías
                for fr in franjas_a_borrar:
                    del grid[fr]
                    franjas_eliminadas_total += 1
                    self.log_mensaje(
                        f"Franja '{fr}' eliminada de {asignatura_codigo} (sin días)",
                        "info"
                    )

            # Registrar y fechar si hubo cambios
            if celdas_modificadas or franjas_eliminadas_total or dias_eliminados_total:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"Limpieza de franjas completada para {asignatura_codigo}: "
                    f"{celdas_modificadas} celdas actualizadas, "
                    f"{dias_eliminados_total} días y {franjas_eliminadas_total} franjas eliminadas",
                    "success"
                )

        except Exception as e:
            self.log_mensaje(f"Error eliminando grupos de franjas para {asignatura_codigo}: {e}", "warning")

    def eliminar_asignatura_real_completa(self, asignatura_codigo) -> None:
        """Eliminar asignatura realmente del sistema completo en cascada"""
        try:
            if not self.parent_window:
                self.log_mensaje(f"No se puede eliminar {asignatura_codigo}: sin parent_window", "warning")
                return

            # Obtener datos de la asignatura antes de eliminar
            datos_asignatura = self.datos_configuracion.get(asignatura_codigo)
            if not datos_asignatura:
                self.log_mensaje(f"Asignatura {asignatura_codigo} no encontrada en configuración", "warning")
                return

            grupos_asociados = datos_asignatura.get('grupos_asociados', [])

            self.log_mensaje(f"Eliminando asignatura {asignatura_codigo} del sistema completo...", "info")

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

            self.log_mensaje(f"Asignatura {asignatura_codigo} procesada para eliminación completa", "success")

        except Exception as e:
            self.log_mensaje(f"Error en eliminación completa de asignatura {asignatura_codigo}: {e}", "error")

    def eliminar_asignatura_de_grupos_sistema(self, asignatura_codigo, grupos_asociados) -> None:
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
                        self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada del grupo {grupo_codigo}", "info")

            # Buscar en TODOS los grupos por si hay referencias huérfanas
            for grupo_codigo, grupo_data in datos_grupos.items():
                asignaturas_asociadas = grupo_data.get("asignaturas_asociadas", [])
                if asignatura_codigo in asignaturas_asociadas:
                    asignaturas_asociadas.remove(asignatura_codigo)
                    grupo_data["asignaturas_asociadas"] = sorted(asignaturas_asociadas)
                    cambios_realizados = True
                    self.log_mensaje(
                        f"Asignatura {asignatura_codigo} eliminada del grupo {grupo_codigo} (referencia huérfana)",
                        "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["grupos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada del módulo de grupos", "success")

        except Exception as e:
            self.log_mensaje(f"Error eliminando asignatura de grupos: {e}", "warning")

    def eliminar_asignatura_de_profesores_sistema(self, asignatura_codigo) -> None:
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
                            f"Asignatura {asignatura_codigo} eliminada del profesor {nombre_profesor} ({profesor_id})",
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
                                    f"Horario bloqueado de {asignatura_codigo} eliminado del profesor {profesor_id}",
                                    "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["profesores"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada del módulo de profesores", "success")

        except Exception as e:
            self.log_mensaje(f"Error eliminando asignatura de profesores: {e}", "warning")

    def eliminar_asignatura_de_alumnos_sistema(self, asignatura_codigo) -> None:
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
                    self.log_mensaje(f"Código de asignatura {asignatura_codigo} eliminado del alumno {nombre_alumno}",
                                     "info")

                # Eliminar de asignaturas_matriculadas
                if "asignaturas_matriculadas" in alumno_data:
                    if asignatura_codigo in alumno_data["asignaturas_matriculadas"]:
                        del alumno_data["asignaturas_matriculadas"][asignatura_codigo]
                        cambios_realizados = True
                        alumnos_modificados += 1
                        nombre_alumno = alumno_data.get("nombre", "Desconocido")
                        self.log_mensaje(
                            f"Asignatura {asignatura_codigo} eliminada de matriculadas del alumno {nombre_alumno}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["alumnos"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(
                    f"Asignatura {asignatura_codigo} eliminada de {alumnos_modificados} referencias en alumnos",
                    "success")

        except Exception as e:
            self.log_mensaje(f"Error eliminando asignatura de alumnos: {e}", "warning")

    def eliminar_asignatura_de_horarios_sistema(self, asignatura_codigo) -> None:
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
                            f"Asignatura {asignatura_encontrada} eliminada completamente del semestre {semestre}",
                            "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["horarios"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada completamente del módulo de horarios",
                                 "success")

        except Exception as e:
            self.log_mensaje(f"Error eliminando asignatura de horarios: {e}", "warning")

    def eliminar_asignatura_de_aulas_sistema(self, asignatura_codigo) -> None:
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
                        self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada del aula {aula_nombre}", "info")

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
                        self.log_mensaje(f"Ocupaciones de {asignatura_codigo} eliminadas del aula {aula_nombre}",
                                         "info")

            if cambios_realizados:
                self.parent_window.configuracion["configuracion"]["aulas"][
                    "fecha_actualizacion"] = datetime.now().isoformat()
                self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada del módulo de aulas", "success")

        except Exception as e:
            self.log_mensaje(f"Error eliminando asignatura de aulas: {e}", "warning")

    def eliminar_asignatura_de_asignaturas_sistema(self, asignatura_codigo) -> None:
        """Eliminar asignatura del módulo de asignaturas del sistema"""
        try:
            config_asignaturas = self.parent_window.configuracion["configuracion"].get("asignaturas", {})
            if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                datos_asignaturas = config_asignaturas["datos"]
                if asignatura_codigo in datos_asignaturas:
                    del datos_asignaturas[asignatura_codigo]
                    self.parent_window.configuracion["configuracion"]["asignaturas"][
                        "fecha_actualizacion"] = datetime.now().isoformat()
                    self.log_mensaje(f"Asignatura {asignatura_codigo} eliminada del módulo de asignaturas", "info")

        except Exception as e:
            self.log_mensaje(f"Error eliminando asignatura de asignaturas: {e}", "warning")

    # ========= GUARDAR / IMPORTAR / EXPORTAR =========
    def guardar_en_sistema(self) -> None:
        """Guardar configuración en el sistema principal aplicando eliminaciones pendientes"""
        try:
            total_asignaturas = len(self.datos_configuracion)
            con_alumnos = sum(1 for datos in self.datos_configuracion.values()
                              if datos.get('estadisticas_calculadas', {}).get('total_matriculados', 0) > 0)
            asignaturas_a_eliminar = len(self.cambios_pendientes["asignaturas_eliminadas"])
            asignaturas_a_actualizar = len(self.cambios_pendientes.get("asignaturas_actualizadas", []))

            if total_asignaturas == 0 and asignaturas_a_eliminar == 0 and asignaturas_a_actualizar == 0:
                QMessageBox.warning(self, "Sin Datos", "No hay asignaturas configuradas para guardar.")
                return

            mensaje_confirmacion = f"¿Guardar configuración en el sistema y cerrar?\n\n"
            mensaje_confirmacion += f"Resumen:\n"
            mensaje_confirmacion += f"   • {total_asignaturas} asignaturas configuradas\n"
            mensaje_confirmacion += f"   • {con_alumnos} asignaturas con alumnos matriculados\n"

            if asignaturas_a_eliminar > 0:
                mensaje_confirmacion += f"   • {asignaturas_a_eliminar} asignaturas serán eliminadas en cascada\n"
            if asignaturas_a_actualizar > 0:
                mensaje_confirmacion += f"   • {asignaturas_a_actualizar} asignaturas serán actualizadas en cascada\n"

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
                if asignaturas_a_actualizar > 0:
                    self.aplicar_actualizaciones_pendientes()

                # Recalcular metadatos de horarios después de eliminar
                self.recalcular_metadatos_horarios()

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

    def import_config(self) -> None:
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Asignaturas",
            dir_downloads(), "Archivos JSON (*.json)"
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

    def export_config(self) -> None:
        """Guardar configuración en archivo JSON"""
        nombre_por_defecto = f"asignaturas_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ruta_inicial = os.path.join(dir_downloads(), nombre_por_defecto)

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Configuración de Asignaturas",
            ruta_inicial,
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
                    'generado_por': 'OPTIM - Configurar Asignaturas'
                }
            }

            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Éxito", f"Configuración guardada en:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar configuración:\n{str(e)}")

    # ========= ELIMINACIONES MASIVAS Y CONTROL =========
    def limpiar_todas_asignaturas(self) -> None:
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
        mensaje += f"IMPACTO TOTAL:\n"
        mensaje += f"   • {total_asignaturas} asignaturas serán eliminadas\n"
        mensaje += f"   • {len(grupos_afectados)} grupos serán afectados\n"
        mensaje += f"   • Todas las referencias en profesores, alumnos, horarios y aulas\n\n"
        mensaje += f"⚠️ Esta acción marcará TODAS las asignaturas para eliminación.\n"
        mensaje += f"La eliminación se aplicará al guardar en el sistema.\n\n"
        mensaje += f"Esta acción no se puede deshacer un vez guardado."

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

            self.log_mensaje(f"{asignaturas_marcadas} asignaturas marcadas para eliminación al guardar", "info")
            QMessageBox.information(self, "Marcadas para Eliminación",
                                    f"✅ {asignaturas_marcadas} asignaturas marcadas para eliminación.\n\n"
                                    f"La eliminación en cascada se aplicará al guardar en el sistema.")

    def aplicar_eliminaciones_pendientes(self) -> None:
        """Aplicar todas las eliminaciones marcadas en cascada"""
        try:
            asignaturas_eliminadas = self.cambios_pendientes["asignaturas_eliminadas"].copy()

            if not asignaturas_eliminadas:
                return

            self.log_mensaje(f"Aplicando eliminación en cascada de {len(asignaturas_eliminadas)} asignaturas...",
                             "info")

            # Eliminar cada asignatura marcada
            for asignatura_codigo in asignaturas_eliminadas:
                self.eliminar_asignatura_real_completa(asignatura_codigo)

            # Limpiar lista de eliminaciones pendientes
            self.cambios_pendientes["asignaturas_eliminadas"].clear()

            self.log_mensaje(f"Eliminación en cascada completada para {len(asignaturas_eliminadas)} asignaturas",
                             "success")

        except Exception as e:
            self.log_mensaje(f"Error aplicando eliminaciones pendientes: {e}", "warning")

    def marcar_asignatura_eliminada_en_tabla(self, asignatura_codigo) -> None:
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
            self.log_mensaje(f"Error marcando asignatura en tabla: {e}", "warning")

    def marcar_todas_asignaturas_eliminadas(self) -> None:
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
            self.log_mensaje(f"Error marcando todas las asignaturas en tabla: {e}", "warning")

    def cancelar_eliminaciones_pendientes(self) -> None:
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
                    self.texto_stats.setText("Presiona 'Recalcular Estadísticas' para ver estadísticas")
                    self.btn_duplicar.setEnabled(False)

                self.log_mensaje(f"{asignaturas_canceladas} eliminaciones de asignaturas canceladas", "info")

        except Exception as e:
            self.log_mensaje(f"Error cancelando eliminaciones: {e}", "warning")

    # ========= CAMBIOS / ESTADO VENTANA =========
    def hay_cambios_sin_guardar(self) -> bool:
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

    def marcar_cambio_realizado(self) -> None:
        """Marcar que se realizó un cambio"""
        self.datos_guardados_en_sistema = False

    def closeEvent(self, event) -> None:
        """Manejar cierre de ventana cancelando eliminaciones pendientes si es necesario"""
        if not self.hay_cambios_sin_guardar():
            self.log_mensaje("Cerrando configuración de asignaturas", "info")
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
            self.log_mensaje("Cerrando sin guardar cambios", "warning")
            event.accept()
        else:
            event.ignore()

    def cancelar_cambios_en_sistema(self) -> None:
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

            self.log_mensaje("Cambios cancelados y estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"Error cancelando cambios: {e}", "warning")

    # ========= NOTIFICACIONES A OTROS MÓDULOS =========
    def notificar_cambios_a_horarios(self) -> None:
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
                self.log_mensaje("Cambios notificados al módulo de horarios", "info")

        except Exception as e:
            self.log_mensaje(f"Error notificando cambios a horarios: {e}", "warning")

    def log_mensaje(self, mensaje, tipo="info") -> None:
        """Logging simple"""
        if self.parent_window and hasattr(self.parent_window, 'log_mensaje'):
            self.parent_window.log_mensaje(mensaje, tipo)
        else:
            iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            icono = iconos.get(tipo, "ℹ️")
            print(f"{icono} {mensaje}")

    # ========= UTILIDADES =========
    def hex_to_rgb(self, hex_color) -> str:
        """Convertir color hex a RGB"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

    # ========= ESTADÍSTICAS =========
    def actualizar_estadisticas(self) -> None:
        """Actualizar estadísticas desde datos de alumnos matriculados"""
        try:
            if not self.alumnos_disponibles:
                self.texto_stats.setText("⚠️ No hay datos de alumnos disponibles")
                return

            # Agrupar alumnos por asignatura
            estadisticas_por_asignatura = {}

            def ensure_entry(codigo: str) -> None:
                """Inicializar las entradas de diccionario antes de sumas contadores"""
                if codigo not in estadisticas_por_asignatura:
                    estadisticas_por_asignatura[codigo] = {
                        'total_matriculados': 0,
                        'con_lab_anterior': 0,
                        'sin_lab_anterior': 0
                    }
            # 1)
            for _dni, alumno in self.alumnos_disponibles.items():
                asigs = alumno.get('asignaturas_matriculadas') or {}
                if isinstance(asigs, dict):
                    for codigo_asig, info in asigs.items():
                        if not isinstance(info, dict):
                            continue
                        if not info.get('matriculado', False):
                            continue
                        ensure_entry(codigo_asig)
                        estadisticas_por_asignatura[codigo_asig]['total_matriculados'] += 1
                        if info.get('lab_aprobado', False) or info.get('lab_anterior_aprobado', False):
                            estadisticas_por_asignatura[codigo_asig]['con_lab_anterior'] += 1
                        else:
                            estadisticas_por_asignatura[codigo_asig]['sin_lab_anterior'] += 1

            # 2) Actualizar estadísticas en asignaturas configuradas
            asignaturas_actualizadas = 0
            for codigo, datos_asignatura in self.datos_configuracion.items():
                stats = estadisticas_por_asignatura.get(codigo)
                if stats:
                    self.datos_configuracion[codigo]['estadisticas_calculadas'] = {
                        'total_matriculados': stats['total_matriculados'],
                        'con_lab_anterior': stats['con_lab_anterior'],
                        'sin_lab_anterior': stats['sin_lab_anterior'],
                        'ultima_actualizacion': datetime.now().isoformat()
                    }
                    asignaturas_actualizadas += 1
                else:
                    # Sin alumnos para esta asignatura
                    self.datos_configuracion[codigo]['estadisticas_calculadas'] = {
                        'total_matriculados': 0,
                        'con_lab_anterior': 0,
                        'sin_lab_anterior': 0,
                        'ultima_actualizacion': datetime.now().isoformat()
                    }

            # 3) Mostrar resumen de la actualización
            stats_text = f"ACTUALIZACIÓN COMPLETADA:\n"
            stats_text += f"   • {asignaturas_actualizadas} asignaturas actualizadas\n"
            stats_text += f"   • {len(self.alumnos_disponibles)} alumnos procesados\n\n"

            for codigo, datos in self.datos_configuracion.items():
                s = datos.get('estadisticas_calculadas', {})
                stats_text += f"{codigo}:\n"
                stats_text += (f"   • {s.get('total_matriculados', 0)} alumnos matriculados"
                               f"   • {s.get('sin_lab_anterior', 0)} alumnos por cursar el laboratorio\n\n")

            self.texto_stats.setText(stats_text)

            # 4) Actualizar interfaz
            self.cargar_lista_asignaturas()
            if self.asignatura_actual:
                self.auto_seleccionar_asignatura(self.asignatura_actual)

            # self.marcar_cambio_realizado()
            self.log_mensaje(f"Estadísticas actualizadas: {asignaturas_actualizadas} asignaturas", "success")

        except Exception as e:
            self.texto_stats.setText(f"❌ Error actualizando estadísticas: {e}")
            self.log_mensaje(f"Error actualizando estadísticas: {e}", "warning")

    def exportar_estadisticas(self) -> None:
        """Exportar estadísticas completas a archivo"""
        nombre_txt = f"estadisticas_asignaturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ruta_inicial = os.path.join(dir_downloads(), nombre_txt)

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Estadísticas Completas",
            ruta_inicial,
            "Archivos de texto (*.txt)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write("ESTADÍSTICAS COMPLETAS DE ASIGNATURAS - OPTIM\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

                f.write(f"RESUMEN GENERAL:\n")
                f.write(f"   • Total asignaturas configuradas: {len(self.datos_configuracion)}\n")

                # Estadísticas por tipo
                tipos = {}
                for datos in self.datos_configuracion.values():
                    tipo = datos.get('tipo', 'Sin tipo')
                    tipos[tipo] = tipos.get(tipo, 0) + 1

                f.write(f"   • Por tipo: {', '.join(f'{k}: {v}' for k, v in tipos.items())}\n\n")

                # Detalles por asignatura
                f.write("DETALLES POR ASIGNATURA:\n")
                f.write("=" * 40 + "\n\n")

                for codigo, datos in sorted(self.datos_configuracion.items()):
                    f.write(f"{codigo} - {datos.get('nombre', 'Sin nombre')}\n")
                    f.write(f"   • Semestre: {datos.get('semestre', 'No definido')}\n")
                    f.write(f"   • Tipo: {datos.get('tipo', 'No definido')}\n")

                    grupos = datos.get('grupos_asociados', [])
                    f.write(f"   • Grupos: {', '.join(grupos) if grupos else 'Sin grupos'}\n")

                    stats = datos.get('estadisticas_calculadas', {})
                    f.write(f"   • Matriculados: {stats.get('total_matriculados', 0)}\n")
                    f.write(f"   • Por cursar el laboratorio: {stats.get('sin_lab_anterior', 0)}\n")
                    f.write(f"   • Grupos recomendados: {stats.get('grupos_recomendados', 0)}\n")

            QMessageBox.information(self, "Exportación Exitosa", f"Estadísticas exportadas a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar estadísticas:\n{str(e)}")

    # ========= RECALCULO METADATA HORARIOS =========
    def recalcular_metadatos_horarios(self) -> None:
        """Recalcula total_franjas y total_asignaturas en metadatos de horarios"""
        try:
            cfg = self.parent_window.configuracion.get("configuracion", {})
            horarios = cfg.get("horarios", {})
            datos_hor = horarios.get("datos", {})
            if not datos_hor:
                return

            total_asignaturas = 0
            total_franjas = 0

            for semestre in datos_hor.keys():
                asignaturas_sem = datos_hor.get(semestre, {})
                if not isinstance(asignaturas_sem, dict):
                    continue
                total_asignaturas += len(asignaturas_sem)

                for asig_data in asignaturas_sem.values():
                    grid = asig_data.get("horarios_grid", {})
                    if not isinstance(grid, dict):
                        continue
                    for dias in grid.values():
                        if not isinstance(dias, dict):
                            continue
                        for celda in dias.values():
                            grupos = celda.get("grupos", []) if isinstance(celda, dict) else celda
                            if isinstance(grupos, list) and len(grupos) > 0:
                                total_franjas += 1

            # Actualizar metadatos
            horarios["total_asignaturas"] = total_asignaturas
            horarios["total_franjas"] = total_franjas
            horarios["total"] = total_franjas
            horarios["fecha_actualizacion"] = datetime.now().isoformat()

            self.log_mensaje(
                f"Metadatos horarios recalculados: {total_asignaturas} asignaturas, {total_franjas} franjas", "info")

        except Exception as e:
            self.log_mensaje(f"Error recalculando metadatos de horarios: {e}", "warning")


# ========= main =========
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
                "semana_inicio": 6,
                "num_sesiones": 8
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
                "semana_inicio": 6,
                "num_sesiones": 8
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
                "semana_inicio": 4,
                "num_sesiones": 10
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
                "semana_inicio": 4,
                "num_sesiones": 10
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

    window = ConfigurarAsignaturasWindow(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()