
"""
Configurar Aulas - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QListWidget,
    QGroupBox, QScrollArea, QMessageBox,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QLineEdit, QInputDialog, QTextEdit, QFormLayout, QListWidgetItem,
    QTabWidget, QCalendarWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QPalette, QColor


def center_window_on_screen(window, width, height) -> None:
    """Centra la ventana en la pantalla"""
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


# ========= Diálogo Gestión Aulas =========
class GestionAulaDialog(QDialog):
    """Dialog para añadir/editar aula con gestión de asignaturas asociadas y días no disponibles"""

    # ========= INICIALIZACIÓN =========
    def __init__(self, aula_existente=None, asignaturas_disponibles=None, parent=None):
        super().__init__(parent)
        self.aula_existente = aula_existente
        self.asignaturas_disponibles = asignaturas_disponibles or {}
        self.setWindowTitle("Editar Laboratorio" if aula_existente else "Nuevo Laboratorio")
        self.setModal(True)
        window_width = 700
        window_height = 650
        self.setMinimumHeight(450)
        center_window_on_screen(self, window_width, window_height)

        self.setup_ui()
        self.apply_dark_theme()

        self.configurar_botones_uniformes()

        if self.aula_existente:
            self.cargar_datos_existentes()

    # ========= CONFIGURACIÓN DE UI =========
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Datos básicos del laboratorio
        datos_group = QGroupBox("🏢 DATOS BÁSICOS DEL LABORATORIO")
        datos_layout = QFormLayout()

        # Nombre
        self.edit_nombre = QLineEdit()
        self.edit_nombre.setPlaceholderText("Ej: Lab_Fisica_A")

        # Capacidad con unidad externa
        capacidad_layout = QHBoxLayout()
        self.spin_capacidad = QSpinBox()
        self.spin_capacidad.setRange(1, 200)
        self.spin_capacidad.setValue(24)
        self.spin_capacidad.setMinimumWidth(80)
        capacidad_layout.addWidget(self.spin_capacidad)
        capacidad_layout.addWidget(QLabel("alumnos"))
        capacidad_layout.addStretch()

        # Equipamiento
        self.edit_equipamiento = QLineEdit()
        self.edit_equipamiento.setPlaceholderText("Ej: Osciloscopios + Generadores")

        # Edificio
        self.edit_edificio = QLineEdit()
        self.edit_edificio.setPlaceholderText("Ej: Edificio A")

        # Planta
        self.edit_planta = QLineEdit()
        self.edit_planta.setPlaceholderText("Ej: Planta 1")

        # Disponibilidad - Checkbox con estilo consistente
        self.check_disponible = QCheckBox("Laboratorio disponible para uso")
        self.check_disponible.setChecked(True)
        self.check_disponible.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 8px;
                margin: 2px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
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

        # Añadir campos al formulario
        datos_layout.addRow("🏷️ Nombre:", self.edit_nombre)
        datos_layout.addRow("👥 Capacidad:", capacidad_layout)
        datos_layout.addRow("🔧 Equipamiento:", self.edit_equipamiento)
        datos_layout.addRow("🏢 Edificio:", self.edit_edificio)
        datos_layout.addRow("📍 Planta:", self.edit_planta)
        datos_layout.addRow("", self.check_disponible)

        datos_group.setLayout(datos_layout)
        layout.addWidget(datos_group)

        # ================== TABS PRINCIPALES: ASIGNATURAS Y DÍAS NO DISPONIBLES ==================
        tabs_widget = QTabWidget()

        # ================== TAB 1: ASIGNATURAS ASOCIADAS ==================
        tab_asignaturas = QWidget()
        tab_asignaturas_layout = QVBoxLayout(tab_asignaturas)
        tab_asignaturas_layout.setSpacing(15)

        if self.asignaturas_disponibles:
            info_label = QLabel("Selecciona las asignaturas que pueden cursarse en este laboratorio:")
            info_label.setStyleSheet("color: #cccccc; font-size: 11px; margin-bottom: 5px;")
            tab_asignaturas_layout.addWidget(info_label)

            # Crear checkboxes para cada asignatura disponible
            self.checks_asignaturas = {}

            # Scroll area para asignaturas
            scroll_asignaturas = QScrollArea()
            scroll_asignaturas.setWidgetResizable(True)
            scroll_asignaturas.setMinimumHeight(300)
            scroll_asignaturas.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)

            # Organizar por semestre basado en la configuración de asignaturas
            asignaturas_por_semestre = {"1º Semestre": [], "2º Semestre": []}

            for codigo, asig_data in self.asignaturas_disponibles.items():
                semestre = asig_data.get('semestre', '1º Semestre')
                if semestre in asignaturas_por_semestre:
                    asignaturas_por_semestre[semestre].append((codigo, asig_data))
                else:
                    asignaturas_por_semestre["1º Semestre"].append((codigo, asig_data))

            # 1º Semestre
            if asignaturas_por_semestre["1º Semestre"]:
                sem1_label = QLabel("📋 1º SEMESTRE:")
                sem1_label.setStyleSheet("color: #90EE90; font-weight: bold; margin-top: 8px; font-size: 13px;")
                scroll_layout.addWidget(sem1_label)

                for codigo, asig_data in sorted(asignaturas_por_semestre["1º Semestre"],
                                                key=lambda x: x[1].get('nombre', x[0])):
                    nombre = asig_data.get('nombre', codigo)
                    curso = asig_data.get('curso', '')
                    texto_checkbox = f"{codigo} - {nombre}"
                    if curso:
                        texto_checkbox += f" - {curso}"

                    check = QCheckBox(texto_checkbox)
                    check.setStyleSheet("""
                        QCheckBox {
                            color: #ffffff;
                            font-size: 11px;
                            font-weight: 500;
                            padding: 6px 8px;
                            margin: 2px;
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
                    self.checks_asignaturas[codigo] = check
                    scroll_layout.addWidget(check)

            # 2º Semestre
            if asignaturas_por_semestre["2º Semestre"]:
                # Espaciador
                if asignaturas_por_semestre["1º Semestre"]:
                    espaciador = QLabel("")
                    espaciador.setFixedHeight(10)
                    scroll_layout.addWidget(espaciador)

                sem2_label = QLabel("📋 2º SEMESTRE:")
                sem2_label.setStyleSheet("color: #FFB347; font-weight: bold; margin-top: 8px; font-size: 13px;")
                scroll_layout.addWidget(sem2_label)

                for codigo, asig_data in sorted(asignaturas_por_semestre["2º Semestre"],
                                                key=lambda x: x[1].get('nombre', x[0])):
                    nombre = asig_data.get('nombre', codigo)
                    curso = asig_data.get('curso', '')
                    texto_checkbox = f"{codigo} - {nombre}"
                    if curso:
                        texto_checkbox += f" - {curso}"

                    check = QCheckBox(texto_checkbox)
                    check.setStyleSheet("""
                        QCheckBox {
                            color: #ffffff;
                            font-size: 11px;
                            font-weight: 500;
                            padding: 6px 8px;
                            margin: 2px;
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
                    self.checks_asignaturas[codigo] = check
                    scroll_layout.addWidget(check)

            scroll_layout.addStretch()
            scroll_asignaturas.setWidget(scroll_widget)
            tab_asignaturas_layout.addWidget(scroll_asignaturas)

        else:
            # No hay asignaturas configuradas
            no_asig_label = QLabel("⚠️ No hay asignaturas configuradas en el sistema.\n"
                                   "Configure primero las asignaturas para poder asociarlas.")
            no_asig_label.setStyleSheet("color: #ffaa00; font-style: italic; padding: 20px; font-size: 13px;")
            no_asig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tab_asignaturas_layout.addWidget(no_asig_label)
            self.checks_asignaturas = {}

        # ================== TAB 2: DÍAS NO DISPONIBLES ==================
        tab_no_disponibles = QWidget()
        tab_no_disp_layout = QVBoxLayout(tab_no_disponibles)
        tab_no_disp_layout.setContentsMargins(15, 20, 15, 15)
        tab_no_disp_layout.setSpacing(15)

        no_disp_info_label = QLabel("📅 Fechas NO disponibles (obras, mantenimiento, etc.):")
        no_disp_info_label.setStyleSheet("color: #cccccc; font-size: 12px; margin-bottom: 8px;")
        no_disp_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tab_no_disp_layout.addWidget(no_disp_info_label)

        # Layout horizontal para calendario y lista lado a lado
        no_disp_horizontal = QHBoxLayout()
        no_disp_horizontal.setSpacing(20)

        # Calendario para seleccionar fechas
        self.calendario = QCalendarWidget()
        self.calendario.setMaximumSize(400, 280)
        self.calendario.setMinimumWidth(300)
        self.calendario.clicked.connect(self.agregar_fecha_no_disponible)

        # Lista de fechas no disponibles a la derecha
        no_disp_derecha = QVBoxLayout()
        no_disp_derecha.setSpacing(10)

        # Título para la lista
        lista_titulo = QLabel("📋 Fechas bloqueadas:")
        lista_titulo.setStyleSheet("font-weight: bold; color: #ffffff; margin-bottom: 5px;")
        no_disp_derecha.addWidget(lista_titulo)

        self.lista_fechas_no_disponibles = QListWidget()
        self.lista_fechas_no_disponibles.setMaximumHeight(200)
        self.lista_fechas_no_disponibles.setMinimumWidth(180)
        no_disp_derecha.addWidget(self.lista_fechas_no_disponibles)

        # Botones de gestión
        botones_fechas = QHBoxLayout()
        botones_fechas.setSpacing(8)

        btn_eliminar_fecha = QPushButton("🗑️ Eliminar")
        btn_limpiar_fechas = QPushButton("🧹 Limpiar Todo")
        btn_eliminar_fecha.clicked.connect(self.eliminar_fecha_no_disponible)
        btn_limpiar_fechas.clicked.connect(self.limpiar_todas_fechas)

        botones_fechas.addWidget(btn_eliminar_fecha)
        botones_fechas.addWidget(btn_limpiar_fechas)
        no_disp_derecha.addLayout(botones_fechas)

        # Widget contenedor derecho
        no_disp_derecha_widget = QWidget()
        no_disp_derecha_widget.setLayout(no_disp_derecha)

        # Agregar al layout horizontal
        no_disp_horizontal.addStretch(1)
        no_disp_horizontal.addWidget(self.calendario)

        # Espaciador central
        espaciador_central = QSpacerItem(50, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        no_disp_horizontal.addItem(espaciador_central)

        no_disp_horizontal.addWidget(no_disp_derecha_widget)
        no_disp_horizontal.addStretch(1)

        tab_no_disp_layout.addLayout(no_disp_horizontal)
        tab_no_disp_layout.addStretch()

        # ================== AÑADIR TABS AL WIDGET PRINCIPAL ==================
        tabs_widget.addTab(tab_asignaturas, "📚 Asignaturas Asociadas")
        tabs_widget.addTab(tab_no_disponibles, "❌ Días No Disponibles")

        layout.addWidget(tabs_widget)

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validar_y_aceptar)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

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

            /* Unificar estilo entre Aceptar y Cancelar */
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

    def configurar_botones_uniformes(self) -> None:
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

    # ========= MANEJO DE FECHAS NO DISPONIBLES =========
    def agregar_fecha_no_disponible(self, fecha) -> None:
        """Añadir la fecha a la lista de no disponibles"""
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

    def eliminar_fecha_no_disponible(self) -> None:
        """Eliminar fecha seleccionada de la lista"""
        current_item = self.lista_fechas_no_disponibles.currentItem()
        if current_item:
            row = self.lista_fechas_no_disponibles.row(current_item)
            self.lista_fechas_no_disponibles.takeItem(row)

    def limpiar_todas_fechas(self) -> None:
        """Limpiar todas las fechas no disponibles"""
        if self.lista_fechas_no_disponibles.count() == 0:
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Fechas",
            f"¿Eliminar todas las {self.lista_fechas_no_disponibles.count()} fechas no disponibles?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.lista_fechas_no_disponibles.clear()

    def ordenar_fechas_no_disponibles(self) -> None:
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

    # ========= CARGA DE DATOS =========
    def cargar_datos_existentes(self) -> None:
        """Cargar datos del aula existente"""
        if not self.aula_existente:
            return

        datos = self.aula_existente
        self.edit_nombre.setText(datos.get('nombre', ''))
        self.spin_capacidad.setValue(datos.get('capacidad', 24))
        self.edit_equipamiento.setText(datos.get('equipamiento', ''))
        self.edit_edificio.setText(datos.get('edificio', ''))
        self.edit_planta.setText(datos.get('planta', ''))
        self.check_disponible.setChecked(datos.get('disponible', True))

        # Cargar asignaturas asociadas
        asignaturas_asociadas = datos.get('asignaturas_asociadas', [])
        for codigo, check in self.checks_asignaturas.items():
            if codigo in asignaturas_asociadas:
                check.setChecked(True)

        # Cargar fechas no disponibles
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

    def get_datos_aula(self) -> dict:
        """Obtener datos configurados incluyendo asignaturas asociadas y fechas no disponibles"""
        # Obtener asignaturas seleccionadas
        asignaturas_seleccionadas = []
        for codigo, check in self.checks_asignaturas.items():
            if check.isChecked():
                asignaturas_seleccionadas.append(codigo)

        # Obtener fechas no disponibles
        fechas_no_disponibles = []
        for i in range(self.lista_fechas_no_disponibles.count()):
            item = self.lista_fechas_no_disponibles.item(i)
            fechas_no_disponibles.append(item.text())

        return {
            'nombre': self.edit_nombre.text().strip(),
            'capacidad': self.spin_capacidad.value(),
            'equipamiento': self.edit_equipamiento.text().strip(),
            'edificio': self.edit_edificio.text().strip(),
            'planta': self.edit_planta.text().strip(),
            'disponible': self.check_disponible.isChecked(),
            'asignaturas_asociadas': asignaturas_seleccionadas,
            'fechas_no_disponibles': fechas_no_disponibles
        }

    # ========= VALIDAR DATOS =========
    def validar_y_aceptar(self) -> None:
        """Validar datos antes de aceptar"""
        if not self.edit_nombre.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre del laboratorio es obligatorio")
            self.edit_nombre.setFocus()
            return

        #if not self.edit_equipamiento.text().strip():
        #    QMessageBox.warning(self, "Campo requerido", "El equipamiento es obligatorio")
        #    self.edit_equipamiento.setFocus()
        #    return

        self.accept()


# ========= Ventana Principal =========
class ConfigurarAulasWindow(QMainWindow):
    """Ventana principal para configurar aulas/laboratorios con integración global"""

    # Señal para comunicar cambios al sistema principal
    configuracion_actualizada = pyqtSignal(dict)

    # ========= INICIALIZACIÓN =========
    def __init__(self, parent=None, datos_existentes=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Configurar Aulas - OPTIM")
        window_width = 1200
        window_height = 650
        center_window_on_screen(self, window_width, window_height)

        # Obtener asignaturas disponibles desde el sistema global
        self.asignaturas_disponibles = self.get_asignaturas_del_sistema()

        # Estructura de datos principal (integrada con sistema global)
        if datos_existentes:
            self.datos_configuracion = datos_existentes.copy()
            self.log_mensaje("Cargando configuración existente de aulas...", "info")
        else:
            self.datos_configuracion = {}
            self.log_mensaje("Iniciando configuración nueva de aulas...", "info")

        # Variables para rastrear cambios
        self.datos_iniciales = json.dumps(self.datos_configuracion, sort_keys=True)
        self.datos_guardados_en_sistema = datos_existentes is not None
        self.aula_actual = None

        self.setup_ui()
        self.apply_dark_theme()
        self.conectar_signals()
        self.cargar_datos_iniciales()

    # ========= CONFIGURACIÓN DE UI =========
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("CONFIGURACIÓN DE AULAS Y LABORATORIOS")
        titulo.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Contenido principal en tres columnas
        content_layout = QHBoxLayout()

        # Columna izquierda - Lista de aulas
        left_panel = QGroupBox("📋 AULAS CONFIGURADAS")
        left_layout = QVBoxLayout()

        # Header con botones de gestión
        aulas_header = QHBoxLayout()
        aulas_header.addWidget(QLabel("Laboratorios:"))
        aulas_header.addStretch()

        # Botones de gestión con el mismo estilo
        btn_add_aula = self.crear_boton_accion("➕", "#4CAF50", "Añadir nueva aula")
        btn_add_aula.clicked.connect(self.add_aula)

        btn_edit_aula = self.crear_boton_accion("✏️", "#2196F3", "Editar aula seleccionada")
        btn_edit_aula.clicked.connect(self.editar_aula_seleccionada)

        btn_delete_aula = self.crear_boton_accion("🗑️", "#f44336", "Eliminar aula seleccionada")
        btn_delete_aula.clicked.connect(self.eliminar_aula_seleccionada)

        aulas_header.addWidget(btn_add_aula)
        aulas_header.addWidget(btn_edit_aula)
        aulas_header.addWidget(btn_delete_aula)

        left_layout.addLayout(aulas_header)

        # Lista de aulas
        self.list_aulas = QListWidget()
        self.list_aulas.setMaximumWidth(350)
        self.list_aulas.setMinimumHeight(350)
        left_layout.addWidget(self.list_aulas)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)

        # Columna central - Detalles del aula
        center_panel = QGroupBox("🔍 DETALLES DEL LABORATORIO")
        center_layout = QVBoxLayout()
        center_layout.setSpacing(8)

        # Nombre del aula seleccionada
        self.label_aula_actual = QLabel("Seleccione un laboratorio")
        self.label_aula_actual.setStyleSheet("color: #4a9eff; font-weight: bold; font-size: 14px;")
        center_layout.addWidget(self.label_aula_actual)

        # Información detallada
        self.info_aula = QTextEdit()
        self.info_aula.setMaximumHeight(200)
        self.info_aula.setReadOnly(True)
        self.info_aula.setText("ℹ️ Seleccione un laboratorio para ver sus detalles")
        center_layout.addWidget(self.info_aula)

        # Estadísticas simplificadas
        stats_group = QGroupBox("📊 ESTADÍSTICAS")
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(5)

        self.texto_stats = QTextEdit()
        self.texto_stats.setMaximumHeight(120)
        self.texto_stats.setReadOnly(True)
        self.texto_stats.setText("📈 Seleccione datos para ver estadísticas")
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

        self.btn_duplicar = QPushButton("Duplicar Aula Seleccionada")
        self.btn_duplicar.setEnabled(False)
        self.btn_duplicar.clicked.connect(self.duplicar_aula_seleccionada)
        acciones_layout.addWidget(self.btn_duplicar)

        self.btn_toggle_disponible = QPushButton("Cambiar Disponibilidad")
        self.btn_toggle_disponible.setEnabled(False)
        self.btn_toggle_disponible.clicked.connect(self.toggle_disponibilidad_aula)
        acciones_layout.addWidget(self.btn_toggle_disponible)

        self.btn_buscar_aula = QPushButton("🔍 Buscar Aula")
        self.btn_buscar_aula.clicked.connect(self.buscar_aula_dialog)
        acciones_layout.addWidget(self.btn_buscar_aula)

        acciones_group.setLayout(acciones_layout)
        right_layout.addWidget(acciones_group)

        # Importar
        importar_group = QGroupBox("📥 IMPORTAR DATOS")
        importar_layout = QVBoxLayout()

        self.btn_cargar = QPushButton("Importar Datos")
        self.btn_cargar.setToolTip("Importar configuración desde JSON")
        self.btn_cargar.clicked.connect(self.import_config)
        importar_layout.addWidget(self.btn_cargar)

        importar_group.setLayout(importar_layout)
        right_layout.addWidget(importar_group)

        # Exportar
        exportar_group = QGroupBox("💾 EXPORTAR DATOS")
        exportar_layout = QVBoxLayout()

        self.btn_exportar_aulas = QPushButton("Exportar Datos")
        self.btn_exportar_aulas.setToolTip("Exportar configuración a JSON")
        self.btn_exportar_aulas.clicked.connect(self.export_config)
        exportar_layout.addWidget(self.btn_exportar_aulas)

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
        self.btn_limpiar_todo.clicked.connect(self.limpiar_todas_aulas)
        botones_layout.addWidget(self.btn_limpiar_todo)

        botones_principales_group.setLayout(botones_layout)
        right_layout.addWidget(botones_principales_group)

        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        content_layout.addWidget(right_panel)

        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

    def ordenar_aulas_alfabeticamente(self) -> None:
        """Reordenar aulas alfabéticamente"""
        if not self.datos_configuracion:
            return

        # Crear nuevo diccionario ordenado
        aulas_ordenadas = {}
        for nombre in sorted(self.datos_configuracion.keys()):
            aulas_ordenadas[nombre] = self.datos_configuracion[nombre]

        self.datos_configuracion = aulas_ordenadas

    def auto_seleccionar_aula(self, nombre_aula) -> None:
        """Auto-seleccionar aula por nombre"""
        try:
            for i in range(self.list_aulas.count()):
                item = self.list_aulas.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == nombre_aula:
                    self.list_aulas.setCurrentItem(item)
                    self.seleccionar_aula(item)
                    break
        except Exception as e:
            self.log_mensaje(f"Error auto-seleccionando aula: {e}", "warning")

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

    def hex_to_rgb(self, hex_color) -> str:
        """Convertir color hex a RGB para estilos"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))

    def apply_dark_theme(self) -> None:
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

    # ========= CONEXIÓN DE SEÑALES =========
    def conectar_signals(self) -> None:
        """Conectar señales de la interfaz"""
        self.list_aulas.itemClicked.connect(self.seleccionar_aula)

    # ========= GESTIÓN DE AULAS =========
    def add_aula(self) -> None:
        """Añadir nueva aula con selección de asignaturas"""
        dialog = GestionAulaDialog(None, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.get_datos_aula()
            nombre = datos['nombre']

            if nombre in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un laboratorio con el nombre '{nombre}'")
                return

            # Añadir nueva aula
            self.datos_configuracion[nombre] = datos

            # Auto-ordenar
            self.ordenar_aulas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_aulas()
            self.auto_seleccionar_aula(nombre)
            self.marcar_cambio_realizado()

            num_asignaturas = len(datos.get('asignaturas_asociadas', []))
            num_fechas_bloqueadas = len(datos.get('fechas_no_disponibles', []))
            QMessageBox.information(self, "Éxito",
                                    f"Laboratorio '{nombre}' añadido correctamente\n"
                                    f"Asignaturas asociadas: {num_asignaturas}\n"
                                    f"Fechas bloqueadas: {num_fechas_bloqueadas}")

    def editar_aula_seleccionada(self) -> None:
        """Editar aula seleccionada"""
        if not self.aula_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un laboratorio para editar")
            return

        datos_originales = self.datos_configuracion[self.aula_actual].copy()
        dialog = GestionAulaDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_aula()
            nombre_nuevo = datos_nuevos['nombre']
            nombre_original = self.aula_actual

            # Si cambió el nombre, verificar que no exista
            if nombre_nuevo != nombre_original and nombre_nuevo in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un laboratorio con el nombre '{nombre_nuevo}'")
                return

            # Actualizar datos
            if nombre_nuevo != nombre_original:
                del self.datos_configuracion[nombre_original]
                self.aula_actual = nombre_nuevo

            self.datos_configuracion[nombre_nuevo] = datos_nuevos

            # Auto-ordenar
            self.ordenar_aulas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_aulas()
            self.auto_seleccionar_aula(nombre_nuevo)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Laboratorio actualizado correctamente")

    def eliminar_aula_seleccionada(self) -> None:
        """Eliminar aula seleccionada"""
        if not self.aula_actual:
            QMessageBox.warning(self, "Advertencia", "Seleccione un laboratorio para eliminar")
            return

        respuesta = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de eliminar el laboratorio '{self.aula_actual}'?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            del self.datos_configuracion[self.aula_actual]
            self.aula_actual = None

            # Actualizar interfaz
            self.cargar_lista_aulas()
            self.label_aula_actual.setText("Seleccione un laboratorio")
            self.info_aula.setText("ℹ️ Seleccione un laboratorio para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_toggle_disponible.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", "Laboratorio eliminado correctamente")

    def limpiar_todas_aulas(self) -> None:
        """Limpiar todas las aulas configuradas"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay laboratorios para limpiar")
            return

        respuesta = QMessageBox.question(
            self, "Limpiar Todo",
            f"¿Está seguro de eliminar todos los laboratorios configurados?\n\n"
            f"Se eliminarán {len(self.datos_configuracion)} laboratorios.\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.datos_configuracion.clear()
            self.aula_actual = None

            # Actualizar interfaz
            self.cargar_lista_aulas()
            self.label_aula_actual.setText("Seleccione un laboratorio")
            self.info_aula.setText("ℹ️ Seleccione un laboratorio para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_toggle_disponible.setEnabled(False)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Limpieza Completada", "Todos los laboratorios han sido eliminados")

    def duplicar_aula_seleccionada(self) -> None:
        """Duplicar aula seleccionada"""
        if not self.aula_actual:
            return

        datos_originales = self.datos_configuracion[self.aula_actual].copy()

        # Generar nombre único
        nombre_base = f"{datos_originales['nombre']}_copia"
        contador = 1
        nombre_nuevo = nombre_base

        while nombre_nuevo in self.datos_configuracion:
            nombre_nuevo = f"{nombre_base}_{contador}"
            contador += 1

        datos_originales['nombre'] = nombre_nuevo

        dialog = GestionAulaDialog(datos_originales, self.asignaturas_disponibles, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos_nuevos = dialog.get_datos_aula()
            nombre_final = datos_nuevos['nombre']

            if nombre_final in self.datos_configuracion:
                QMessageBox.warning(self, "Error", f"Ya existe un laboratorio con el nombre '{nombre_final}'")
                return

            # Añadir aula duplicada
            self.datos_configuracion[nombre_final] = datos_nuevos

            # Auto-ordenar
            self.ordenar_aulas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_aulas()
            self.auto_seleccionar_aula(nombre_final)
            self.marcar_cambio_realizado()

            QMessageBox.information(self, "Éxito", f"Laboratorio duplicado como '{nombre_final}'")

    def toggle_disponibilidad_aula(self) -> None:
        """Cambiar disponibilidad del aula actual"""
        if not self.aula_actual:
            return

        estado_actual = self.datos_configuracion[self.aula_actual].get('disponible', True)
        nuevo_estado = not estado_actual

        self.datos_configuracion[self.aula_actual]['disponible'] = nuevo_estado

        # Actualizar interfaz
        self.cargar_lista_aulas()
        self.auto_seleccionar_aula(self.aula_actual)
        self.marcar_cambio_realizado()

        estado_texto = "disponible" if nuevo_estado else "no disponible"
        QMessageBox.information(self, "Estado Actualizado",
                                f"Laboratorio '{self.aula_actual}' marcado como {estado_texto}")

    def buscar_aula_dialog(self) -> None:
        """Mostrar diálogo para buscar aula por nombre o equipamiento"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay laboratorios configurados para buscar")
            return

        texto_busqueda, ok = QInputDialog.getText(
            self, "Buscar Laboratorio",
            "Buscar por nombre, equipamiento o edificio:"
        )

        if not ok or not texto_busqueda.strip():
            return

        texto_busqueda = texto_busqueda.strip().lower()
        encontrados = []

        for nombre, datos in self.datos_configuracion.items():
            # Buscar por nombre
            if texto_busqueda in nombre.lower():
                encontrados.append((nombre, datos))
            # Buscar por equipamiento
            elif texto_busqueda in datos.get('equipamiento', '').lower():
                encontrados.append((nombre, datos))
            # Buscar por edificio
            elif texto_busqueda in datos.get('edificio', '').lower():
                encontrados.append((nombre, datos))

        if not encontrados:
            QMessageBox.information(self, "Sin Resultados",
                                    f"No se encontraron laboratorios que coincidan con '{texto_busqueda}'")
            return

        if len(encontrados) == 1:
            # Seleccionar directamente
            nombre_encontrado = encontrados[0][0]
            self.auto_seleccionar_aula(nombre_encontrado)
            QMessageBox.information(self, "Laboratorio Encontrado",
                                    f"Laboratorio seleccionado: {nombre_encontrado}")
        else:
            # Mostrar lista de opciones
            opciones = []
            for nombre, datos in encontrados:
                equipamiento = datos.get('equipamiento', 'Sin equipamiento')
                edificio = datos.get('edificio', 'Sin edificio')
                opciones.append(f"{nombre} - {equipamiento} ({edificio})")

            opcion, ok = QInputDialog.getItem(
                self, "Múltiples Resultados",
                f"Se encontraron {len(encontrados)} laboratorios. Selecciona uno:",
                opciones, 0, False
            )

            if ok:
                # Extraer nombre del laboratorio de la opción seleccionada
                nombre_seleccionado = opcion.split(' - ')[0]
                self.auto_seleccionar_aula(nombre_seleccionado)

    # ========= IMPORTAR / EXPORTAR =========
    def export_config(self) -> None:
        """Exportar aulas a archivo JSON"""
        if not self.datos_configuracion:
            QMessageBox.information(self, "Sin Datos", "No hay laboratorios para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Exportar Laboratorios a JSON",
            os.path.join(dir_downloads(), f"laboratorios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"),
            "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            config_data = {
                'laboratorios': self.datos_configuracion,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'total_laboratorios': len(self.datos_configuracion),
                    'total_asociaciones': sum(len(datos.get('asignaturas_asociadas', []))
                                              for datos in self.datos_configuracion.values()),
                    'total_fechas_bloqueadas': sum(len(datos.get('fechas_no_disponibles', []))
                                                   for datos in self.datos_configuracion.values()),
                    'generado_por': 'OPTIM - Configurar Aulas'
                }
            }

            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "Exportación Exitosa", f"Datos exportados a:\n{archivo}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error al exportar datos:\n{str(e)}")

    def import_config(self) -> None:
        """Cargar configuración desde archivo JSON"""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Cargar Configuración de Aulas",
            dir_downloads(), "Archivos JSON (*.json)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cargados = json.load(f)

            # Validar estructura
            if "laboratorios" in datos_cargados:
                self.datos_configuracion = datos_cargados["laboratorios"]
            elif isinstance(datos_cargados, dict):
                self.datos_configuracion = datos_cargados
            else:
                raise ValueError("Formato de archivo JSON inválido")

            # Auto-ordenar
            self.ordenar_aulas_alfabeticamente()

            # Actualizar interfaz
            self.cargar_lista_aulas()
            self.aula_actual = None
            self.label_aula_actual.setText("Seleccione un laboratorio")
            self.info_aula.setText("ℹ️ Seleccione un laboratorio para ver sus detalles")
            self.btn_duplicar.setEnabled(False)
            self.btn_toggle_disponible.setEnabled(False)

            QMessageBox.information(self, "Éxito", "Configuración cargada correctamente")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar configuración:\n{str(e)}")

    # ========= GUARDAR EN SISTEMA =========
    def guardar_en_sistema(self) -> None:
        """Guardar configuración en el sistema principal"""
        try:
            if not self.datos_configuracion:
                QMessageBox.warning(self, "Sin Datos", "No hay laboratorios configurados para guardar.")
                return

            total_aulas = len(self.datos_configuracion)
            disponibles = sum(1 for datos in self.datos_configuracion.values()
                              if datos.get('disponible', True))
            total_asociaciones = sum(len(datos.get('asignaturas_asociadas', []))
                                     for datos in self.datos_configuracion.values())
            total_fechas_bloqueadas = sum(len(datos.get('fechas_no_disponibles', []))
                                          for datos in self.datos_configuracion.values())

            respuesta = QMessageBox.question(
                self, "Guardar y Cerrar",
                f"¿Guardar configuración en el sistema y cerrar?\n\n"
                f"📊 Resumen:\n"
                f"• {total_aulas} laboratorios configurados\n"
                f"• {disponibles} laboratorios disponibles\n"
                f"• {total_asociaciones} asignaturas asociadas\n"
                f"• {total_fechas_bloqueadas} fechas bloqueadas\n\n"
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

    # ========= CARGAR DATOS =========
    def get_asignaturas_del_sistema(self) -> dict:
        """Obtener asignaturas configuradas desde el sistema global - Sincronizado con asignaturas"""
        try:
            if self.parent_window and hasattr(self.parent_window, 'configuracion'):
                # Obtener de configuracion["asignaturas"] en lugar de horarios
                config_asignaturas = self.parent_window.configuracion["configuracion"]["asignaturas"]
                if config_asignaturas.get("configurado") and config_asignaturas.get("datos"):
                    return config_asignaturas["datos"]
            return {}
        except Exception as e:
            self.log_mensaje(f"Error obteniendo asignaturas del sistema: {e}", "warning")
            return {}

    def cargar_datos_iniciales(self) -> None:
        """Cargar datos existentes al inicializar"""
        try:
            # Ordenar aulas alfabéticamente
            self.ordenar_aulas_alfabeticamente()

            # Cargar lista
            self.cargar_lista_aulas()

            # Mostrar resumen
            total_aulas = len(self.datos_configuracion)
            disponibles = sum(1 for datos in self.datos_configuracion.values()
                              if datos.get('disponible', True))

            if total_aulas > 0:
                self.log_mensaje(
                    f"Datos cargados: {total_aulas} aulas ({disponibles} disponibles)",
                    "success"
                )
                self.auto_seleccionar_primera_aula()
            else:
                self.log_mensaje("No hay aulas configuradas - configuración nueva", "info")

        except Exception as e:
            self.log_mensaje(f"Error cargando datos iniciales: {e}", "warning")

    def cargar_lista_aulas(self) -> None:
        """Cargar aulas en la lista visual"""
        self.list_aulas.clear()

        if not self.datos_configuracion:
            item = QListWidgetItem("📭 No hay aulas configuradas")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_aulas.addItem(item)
            return

        # Ordenar aulas por nombre
        aulas_ordenadas = sorted(self.datos_configuracion.items())

        for nombre, datos in aulas_ordenadas:
            disponible_icon = "✅" if datos.get('disponible', True) else "❌"
            capacidad = datos.get('capacidad', 0)
            edificio = datos.get('edificio', 'Sin edificio')

            # Mostrar número de asignaturas asociadas
            num_asignaturas = len(datos.get('asignaturas_asociadas', []))
            asig_info = f"({num_asignaturas} asig.)" if num_asignaturas > 0 else "(sin asig.)"

            # Mostrar fechas no disponibles
            num_fechas_bloqueadas = len(datos.get('fechas_no_disponibles', []))
            fechas_info = f"({num_fechas_bloqueadas} fechas bloq.)" if num_fechas_bloqueadas > 0 else ""

            texto_item = f"{disponible_icon} {nombre} ({capacidad}p) - {edificio} {asig_info} {fechas_info}"

            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, nombre)
            self.list_aulas.addItem(item)

        # Actualizar estadísticas
        self.actualizar_estadisticas()

    # ========= SELECCIÓNAR AUTOMÁTICAMENTE ========
    def seleccionar_aula(self, item) -> None:
        """Seleccionar aula y mostrar detalles"""
        if not item or item.flags() == Qt.ItemFlag.NoItemFlags:
            self.aula_actual = None
            self.btn_duplicar.setEnabled(False)
            self.btn_toggle_disponible.setEnabled(False)
            return

        nombre = item.data(Qt.ItemDataRole.UserRole)
        if not nombre or nombre not in self.datos_configuracion:
            return

        self.aula_actual = nombre
        datos = self.datos_configuracion[nombre]

        # Actualizar etiqueta
        self.label_aula_actual.setText(f"{nombre}")

        # Mostrar información detallada con asignaturas asociadas y fechas no disponibles
        info = f"🏷️ LABORATORIO: {nombre}\n\n"
        info += f"👥 Capacidad: {datos.get('capacidad', 'No definida')} personas\n"
        info += f"🔧 Equipamiento: {datos.get('equipamiento', 'No definido')}\n"
        info += f"🏢 Edificio: {datos.get('edificio', 'No definido')}\n"
        info += f"📍 Planta: {datos.get('planta', 'No definida')}\n"
        info += f"✅ Disponible: {'Sí' if datos.get('disponible', True) else 'No'}\n\n"

        # Mostrar asignaturas asociadas
        asignaturas_asociadas = datos.get('asignaturas_asociadas', [])
        if asignaturas_asociadas:
            info += f"📚 ASIGNATURAS ({len(asignaturas_asociadas)}):\n"
            for codigo_asig in asignaturas_asociadas:
                # Buscar el nombre de la asignatura
                if codigo_asig in self.asignaturas_disponibles:
                    asig_data = self.asignaturas_disponibles[codigo_asig]
                    nombre_asig = asig_data.get('nombre', codigo_asig)
                    semestre = asig_data.get('semestre', '')
                    info += f"  • {codigo_asig} - {nombre_asig} ({semestre})\n"
                else:
                    info += f"  • {codigo_asig}\n"
        else:
            info += f"📚 ASIGNATURAS: Sin asignaturas asociadas\n"

        # Mostrar fechas no disponibles
        fechas_no_disponibles = datos.get('fechas_no_disponibles', [])
        if fechas_no_disponibles:
            info += f"\n❌ DÍAS NO DISPONIBLES ({len(fechas_no_disponibles)}):\n"
            # Mostrar solo las primeras 5 fechas para no saturar
            fechas_mostrar = fechas_no_disponibles[:5]
            for fecha in fechas_mostrar:
                info += f"  • {fecha}\n"
            if len(fechas_no_disponibles) > 5:
                info += f"  ... y {len(fechas_no_disponibles) - 5} fechas más\n"
        else:
            info += f"\n❌ DÍAS NO DISPONIBLES: Ninguno\n"

        self.info_aula.setText(info)

        # Habilitar botones
        self.btn_duplicar.setEnabled(True)
        self.btn_toggle_disponible.setEnabled(True)

        # Actualizar botón de disponibilidad
        estado_actual = "Marcar como No Disponible" if datos.get('disponible', True) else "Marcar como Disponible"
        self.btn_toggle_disponible.setText(f"{estado_actual}")

    def auto_seleccionar_primera_aula(self) -> None:
        """Auto-seleccionar primera aula disponible"""
        try:
            if self.list_aulas.count() > 0:
                primer_item = self.list_aulas.item(0)
                self.list_aulas.setCurrentItem(primer_item)
                self.seleccionar_aula(primer_item)
                self.log_mensaje(f"Auto-seleccionada: {primer_item.text()}", "info")
        except Exception as e:
            self.log_mensaje(f"Error auto-seleccionando aula: {e}", "warning")

    # ========= ESTADÍSTICAS =========
    def actualizar_estadisticas(self) -> None:
        """Actualizar estadísticas simplificadas"""
        total = len(self.datos_configuracion)
        if total == 0:
            self.texto_stats.setText("📊 No hay aulas configuradas")
            return

        disponibles = sum(1 for datos in self.datos_configuracion.values()
                          if datos.get('disponible', True))

        # Capacidades
        capacidades = [datos.get('capacidad', 0) for datos in self.datos_configuracion.values()]
        cap_total = sum(capacidades)

        # Edificios únicos
        edificios = set(datos.get('edificio', 'Sin edificio')
                        for datos in self.datos_configuracion.values())

        # Asignaturas totales asociadas
        total_asociaciones = sum(len(datos.get('asignaturas_asociadas', []))
                                 for datos in self.datos_configuracion.values())

        # Fechas bloqueadas totales
        total_fechas_bloqueadas = sum(len(datos.get('fechas_no_disponibles', []))
                                      for datos in self.datos_configuracion.values())

        # Estadísticas
        stats = f"📈 RESUMEN: {total} aulas, {disponibles} disponibles\n"
        stats += f"👥 CAPACIDAD: {cap_total} total"
        if capacidades:
            stats += f" ({min(capacidades)}-{max(capacidades)})\n"
        else:
            stats += "\n"
        stats += f"🏗️ UBICACIONES: {len(edificios)} edificios\n"
        stats += f"📚 ASOCIACIONES: {total_asociaciones} asignaturas vinculadas\n"
        stats += f"❌ FECHAS BLOQUEADAS: {total_fechas_bloqueadas} días"

        self.texto_stats.setText(stats)

    # ========= LOGS =========
    def log_mensaje(self, mensaje, tipo="info") -> None:
        """Logging simple"""
        if self.parent_window and hasattr(self.parent_window, 'log_mensaje'):
            self.parent_window.log_mensaje(mensaje, tipo)
        else:
            iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            icono = iconos.get(tipo, "ℹ️")
            print(f"{icono} {mensaje}")

    # ========= GESTIÓN DEL CAMBIO =========
    def hay_cambios_sin_guardar(self) -> bool:
        """Detectar si hay cambios sin guardar"""
        datos_actuales = json.dumps(self.datos_configuracion, sort_keys=True)
        hay_cambios = datos_actuales != self.datos_iniciales

        if hay_cambios and not self.datos_guardados_en_sistema:
            return True

        if self.datos_guardados_en_sistema and hay_cambios:
            return True

        return False

    def marcar_cambio_realizado(self) -> None:
        """Marcar que se realizó un cambio"""
        self.datos_guardados_en_sistema = False

    def closeEvent(self, event) -> None:
        """Manejar cierre de ventana"""
        if not self.hay_cambios_sin_guardar():
            self.log_mensaje("Cerrando configuración de aulas", "info")
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
            self.log_mensaje("Cerrando sin guardar cambios", "warning")
            event.accept()
        else:
            event.ignore()

    def cancelar_cambios_en_sistema(self) -> None:
        """Cancelar cambios restaurando estado original"""
        try:
            datos_originales = json.loads(self.datos_iniciales)

            datos_para_sistema = {
                "laboratorios": datos_originales,
                "metadata": {
                    "accion": "CANCELAR_CAMBIOS",
                    "timestamp": datetime.now().isoformat(),
                    "origen": "ConfigurarAulas",
                    "cambios_descartados": True
                }
            }

            self.configuracion_actualizada.emit(datos_para_sistema)
            self.datos_configuracion = datos_originales
            self.datos_guardados_en_sistema = False

            self.log_mensaje("Cambios cancelados y estado restaurado", "info")

        except Exception as e:
            self.log_mensaje(f"Error cancelando cambios: {e}", "warning")


def main():
    """Función principal para testing"""
    app = QApplication(sys.argv)

    # Aplicar tema oscuro
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Datos de ejemplo con asignaturas asociadas y fechas no disponibles
    datos_ejemplo = {
        "Lab_Fisica_A": {
            "nombre": "Lab_Fisica_A",
            "capacidad": 20,
            "equipamiento": "Equipos de medición básicos",
            "edificio": "Edificio A",
            "planta": "Planta 1",
            "disponible": True,
            "asignaturas_asociadas": ["FIS1", "QUI1"],  # Códigos reales del JSON
            "fechas_no_disponibles": ["15/03/2025", "22/03/2025", "01/04/2025"]
        },
        "Lab_Electronica_C": {
            "nombre": "Lab_Electronica_C",
            "capacidad": 18,
            "equipamiento": "Analizadores, Osciloscopios, Microcontroladores",
            "edificio": "Edificio C",
            "planta": "Planta 3",
            "disponible": True,
            "asignaturas_asociadas": ["EANA", "EDIG"],  # Códigos reales del JSON
            "fechas_no_disponibles": ["10/04/2025"]
        }
    }

    window = ConfigurarAulasWindow(datos_existentes=datos_ejemplo)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()