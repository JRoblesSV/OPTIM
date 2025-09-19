import sys
import json
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from datetime import datetime, time


class ConfigurarHorarios(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config_path = "config/horarios_sistema.json"

        # Datos del sistema
        self.laboratorios = {}  # {nombre: {capacidad: 24, equipamiento: "..."}}
        self.cursos = {}  # {codigo: {descripcion: "...", es_doble: bool, comparte_con: "..."}}
        self.asignaciones = {}  # {id: {curso: "M204", laboratorio: "Lab_A", dia: "Lunes", inicio: "08:00", fin: "10:00"}}

        self.setupUi()
        self.cargar_configuracion()

    def setupUi(self):
        self.setObjectName("ConfigurarHorarios")
        self.resize(1600, 900)
        self.setMinimumSize(QtCore.QSize(1600, 900))
        self.setWindowTitle("OPTIM - Configurar Horarios de Laboratorios")

        # Centrar ventana en pantalla
        self.center_window()

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # ========= TÍTULO =========
        self.titulo = QtWidgets.QLabel(self.centralwidget)
        self.titulo.setGeometry(QtCore.QRect(50, 20, 1500, 40))
        self.titulo.setText("Configuración de Horarios de Laboratorios por Curso")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titulo.setStyleSheet("""
            QLabel {
                color: rgb(42,130,218);
                font-size: 18px;
                font-weight: bold;
                background-color: rgb(35,35,35);
                border: 1px solid rgb(42,130,218);
                border-radius: 5px;
                padding: 10px;
            }
        """)

        # ========= PANEL IZQUIERDO - RECURSOS =========
        self.setup_panel_recursos()

        # ========= PANEL CENTRO - ASIGNACIÓN =========
        self.setup_panel_asignacion()

        # ========= PANEL DERECHO - CALENDARIO =========
        self.setup_panel_calendario()

        # ========= BOTONES PRINCIPALES =========
        self.setup_botones()

        # ========= APLICAR TEMA OSCURO =========
        self.apply_dark_theme()

    def center_window(self):
        """Centrar ventana en la pantalla"""
        # Obtener información de la pantalla
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Calcular posición para centrar
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        # Mover la ventana al centro
        self.move(x, y)

    def setup_panel_recursos(self):
        """Panel izquierdo - Gestión de laboratorios y cursos"""

        # ===== LABORATORIOS ===== (Alineado con ASIGNAR HORARIO)
        self.label_labs = QtWidgets.QLabel(self.centralwidget)
        self.label_labs.setGeometry(QtCore.QRect(20, 80, 350, 25))  # Misma altura que ASIGNAR HORARIO
        self.label_labs.setText("🏢 LABORATORIOS DISPONIBLES")
        self.label_labs.setStyleSheet("color: rgb(42,130,218); font-weight: bold; font-size: 14px;")

        self.lista_laboratorios = QtWidgets.QListWidget(self.centralwidget)
        self.lista_laboratorios.setGeometry(QtCore.QRect(20, 115, 350, 140))  # Más alta para acomodar botones
        self.lista_laboratorios.currentRowChanged.connect(self.seleccionar_laboratorio)

        # Botones laboratorios (ALINEADOS con botones de asignar/limpiar)
        self.btn_nuevo_lab = QtWidgets.QPushButton(self.centralwidget)
        self.btn_nuevo_lab.setGeometry(QtCore.QRect(20, 265, 100, 30))  # y=265 para alinear
        self.btn_nuevo_lab.setText("➕ Nuevo")
        self.btn_nuevo_lab.clicked.connect(self.nuevo_laboratorio)

        self.btn_editar_lab = QtWidgets.QPushButton(self.centralwidget)
        self.btn_editar_lab.setGeometry(QtCore.QRect(130, 265, 100, 30))  # y=265 para alinear
        self.btn_editar_lab.setText("✏️ Editar")
        self.btn_editar_lab.clicked.connect(self.editar_laboratorio)

        self.btn_eliminar_lab = QtWidgets.QPushButton(self.centralwidget)
        self.btn_eliminar_lab.setGeometry(QtCore.QRect(240, 265, 130, 30))  # y=265 para alinear
        self.btn_eliminar_lab.setText("🗑️ Eliminar")
        self.btn_eliminar_lab.clicked.connect(self.eliminar_laboratorio)

        # ===== CURSOS ===== (Alineado con ASIGNACIONES ACTUALES)
        self.label_cursos = QtWidgets.QLabel(self.centralwidget)
        self.label_cursos.setGeometry(QtCore.QRect(20, 310, 350, 25))  # Movido hacia abajo
        self.label_cursos.setText("👥 CURSOS DEL SISTEMA")
        self.label_cursos.setStyleSheet("color: rgb(42,130,218); font-weight: bold; font-size: 14px;")

        self.lista_cursos = QtWidgets.QListWidget(self.centralwidget)
        self.lista_cursos.setGeometry(QtCore.QRect(20, 345, 350, 120))  # Movido hacia abajo
        self.lista_cursos.currentRowChanged.connect(self.seleccionar_curso)

        # Botones cursos
        self.btn_nuevo_curso = QtWidgets.QPushButton(self.centralwidget)
        self.btn_nuevo_curso.setGeometry(QtCore.QRect(20, 475, 100, 30))
        self.btn_nuevo_curso.setText("➕ Nuevo")
        self.btn_nuevo_curso.clicked.connect(self.nuevo_curso)

        self.btn_editar_curso = QtWidgets.QPushButton(self.centralwidget)
        self.btn_editar_curso.setGeometry(QtCore.QRect(130, 475, 100, 30))
        self.btn_editar_curso.setText("✏️ Editar")
        self.btn_editar_curso.clicked.connect(self.editar_curso)

        self.btn_eliminar_curso = QtWidgets.QPushButton(self.centralwidget)
        self.btn_eliminar_curso.setGeometry(QtCore.QRect(240, 475, 130, 30))
        self.btn_eliminar_curso.setText("🗑️ Eliminar")
        self.btn_eliminar_curso.clicked.connect(self.eliminar_curso)

        # ===== INFORMACIÓN DEL RECURSO SELECCIONADO =====
        self.info_recurso = QtWidgets.QTextEdit(self.centralwidget)
        self.info_recurso.setGeometry(QtCore.QRect(20, 520, 350, 190))  # Expandido hasta casi los botones
        self.info_recurso.setReadOnly(True)
        self.info_recurso.setPlaceholderText("Selecciona un laboratorio o curso para ver detalles...")

    def setup_panel_asignacion(self):
        """Panel central - Asignación de horarios"""

        self.label_asignacion = QtWidgets.QLabel(self.centralwidget)
        self.label_asignacion.setGeometry(QtCore.QRect(400, 80, 550, 25))
        self.label_asignacion.setText("🎯 ASIGNAR HORARIO DE LABORATORIO")
        self.label_asignacion.setStyleSheet("color: rgb(42,130,218); font-weight: bold; font-size: 14px;")

        # Formulario de asignación
        self.setup_formulario_asignacion()

        # Lista de asignaciones existentes (ALINEADA con CURSOS DEL SISTEMA)
        self.label_asignaciones = QtWidgets.QLabel(self.centralwidget)
        self.label_asignaciones.setGeometry(QtCore.QRect(400, 310, 550, 25))  # Alineada con cursos y=310
        self.label_asignaciones.setText("📋 ASIGNACIONES ACTUALES")
        self.label_asignaciones.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")

        self.tabla_asignaciones = QtWidgets.QTableWidget(self.centralwidget)
        self.tabla_asignaciones.setGeometry(QtCore.QRect(400, 345, 550, 370))  # Ajustada para nueva posición
        self.tabla_asignaciones.setColumnCount(6)
        self.tabla_asignaciones.setHorizontalHeaderLabels(['Curso', 'Laboratorio', 'Día', 'Inicio', 'Fin', 'Acción'])

        # Ajustar anchos de columna
        self.tabla_asignaciones.setColumnWidth(0, 70)  # Curso
        self.tabla_asignaciones.setColumnWidth(1, 140)  # Laboratorio
        self.tabla_asignaciones.setColumnWidth(2, 80)  # Día
        self.tabla_asignaciones.setColumnWidth(3, 60)  # Inicio
        self.tabla_asignaciones.setColumnWidth(4, 60)  # Fin
        self.tabla_asignaciones.setColumnWidth(5, 80)  # Acción

    def setup_formulario_asignacion(self):
        """Formulario para crear nueva asignación"""
        y_base = 115

        # Curso
        self.label_form_curso = QtWidgets.QLabel(self.centralwidget)
        self.label_form_curso.setGeometry(QtCore.QRect(400, y_base, 120, 25))
        self.label_form_curso.setText("Curso:")

        self.combo_form_curso = QtWidgets.QComboBox(self.centralwidget)
        self.combo_form_curso.setGeometry(QtCore.QRect(530, y_base, 140, 30))
        self.combo_form_curso.currentTextChanged.connect(self.validar_turno_curso)

        # Laboratorio
        self.label_form_lab = QtWidgets.QLabel(self.centralwidget)
        self.label_form_lab.setGeometry(QtCore.QRect(400, y_base + 45, 120, 25))
        self.label_form_lab.setText("Laboratorio:")

        self.combo_form_lab = QtWidgets.QComboBox(self.centralwidget)
        self.combo_form_lab.setGeometry(QtCore.QRect(530, y_base + 45, 140, 30))

        # Día
        self.label_form_dia = QtWidgets.QLabel(self.centralwidget)
        self.label_form_dia.setGeometry(QtCore.QRect(400, y_base + 90, 120, 25))
        self.label_form_dia.setText("Día:")

        self.combo_form_dia = QtWidgets.QComboBox(self.centralwidget)
        self.combo_form_dia.setGeometry(QtCore.QRect(530, y_base + 90, 140, 30))
        self.combo_form_dia.addItems(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'])

        # Hora inicio
        self.label_form_inicio = QtWidgets.QLabel(self.centralwidget)
        self.label_form_inicio.setGeometry(QtCore.QRect(690, y_base, 100, 25))
        self.label_form_inicio.setText("Hora Inicio:")

        self.time_form_inicio = QtWidgets.QTimeEdit(self.centralwidget)
        self.time_form_inicio.setGeometry(QtCore.QRect(800, y_base, 100, 30))
        self.time_form_inicio.setDisplayFormat("HH:mm")
        self.time_form_inicio.setTime(QtCore.QTime(8, 0))

        # Hora fin
        self.label_form_fin = QtWidgets.QLabel(self.centralwidget)
        self.label_form_fin.setGeometry(QtCore.QRect(690, y_base + 45, 100, 25))
        self.label_form_fin.setText("Hora Fin:")

        self.time_form_fin = QtWidgets.QTimeEdit(self.centralwidget)
        self.time_form_fin.setGeometry(QtCore.QRect(800, y_base + 45, 100, 30))
        self.time_form_fin.setDisplayFormat("HH:mm")
        self.time_form_fin.setTime(QtCore.QTime(10, 0))

        # Advertencia turno
        self.label_turno_info = QtWidgets.QLabel(self.centralwidget)
        self.label_turno_info.setGeometry(QtCore.QRect(690, y_base + 90, 210, 50))
        self.label_turno_info.setText("")
        self.label_turno_info.setWordWrap(True)
        self.label_turno_info.setStyleSheet("color: orange; font-size: 12px; font-weight: bold;")

        # Botones CENTRADOS en la sección
        self.btn_asignar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_asignar.setGeometry(QtCore.QRect(540, y_base + 150, 130, 35))  # Centrado: x=540
        self.btn_asignar.setText("➕ Asignar")
        self.btn_asignar.clicked.connect(self.crear_asignacion)

        self.btn_limpiar_form = QtWidgets.QPushButton(self.centralwidget)
        self.btn_limpiar_form.setGeometry(QtCore.QRect(680, y_base + 150, 130, 35))  # Centrado: x=680
        self.btn_limpiar_form.setText("🧹 Limpiar")
        self.btn_limpiar_form.clicked.connect(self.limpiar_formulario)

        # Detección automática doble grado (CENTRADA)
        self.label_doble_info = QtWidgets.QLabel(self.centralwidget)
        self.label_doble_info.setGeometry(QtCore.QRect(475, y_base + 195, 400, 45))  # Centrada en la sección
        self.label_doble_info.setText("")
        self.label_doble_info.setWordWrap(True)
        self.label_doble_info.setStyleSheet("color: rgb(46,204,113); font-size: 12px; font-weight: bold;")

    def setup_panel_calendario(self):
        """Panel derecho - Vista calendario semanal"""

        self.label_calendario = QtWidgets.QLabel(self.centralwidget)
        self.label_calendario.setGeometry(QtCore.QRect(980, 80, 590, 25))
        self.label_calendario.setText("📅 CALENDARIO SEMANAL DE LABORATORIOS")
        self.label_calendario.setStyleSheet("color: rgb(42,130,218); font-weight: bold; font-size: 14px;")

        # Tabs por día (AJUSTADO para nueva distribución)
        self.tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_widget.setGeometry(QtCore.QRect(980, 115, 590, 600))  # Mantenemos altura máxima

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        self.tabs_dias = {}

        for dia in dias:
            tab = QtWidgets.QWidget()
            self.tab_widget.addTab(tab, dia)

            # Área de texto para cada día
            texto_dia = QtWidgets.QTextEdit(tab)
            texto_dia.setGeometry(QtCore.QRect(10, 10, 570, 560))
            texto_dia.setReadOnly(True)
            texto_dia.setStyleSheet("""
                QTextEdit {
                    background-color: rgb(35,35,35);
                    color: white;
                    border: 1px solid rgb(127,127,127);
                    font-family: 'Consolas', monospace;
                    font-size: 12px;
                }
            """)

            self.tabs_dias[dia] = texto_dia

    def setup_botones(self):
        """Botones principales"""
        self.btn_guardar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_guardar.setGeometry(QtCore.QRect(600, 730, 140, 45))
        self.btn_guardar.setText("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar_configuracion)

        self.btn_cargar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cargar.setGeometry(QtCore.QRect(750, 730, 140, 45))
        self.btn_cargar.setText("📂 Cargar")
        self.btn_cargar.clicked.connect(lambda: self.cargar_configuracion(mostrar_mensaje=True))

        self.btn_exportar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_exportar.setGeometry(QtCore.QRect(900, 730, 140, 45))
        self.btn_exportar.setText("📤 Exportar")
        self.btn_exportar.clicked.connect(self.exportar_horarios)

        self.btn_cerrar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cerrar.setGeometry(QtCore.QRect(1050, 730, 140, 45))
        self.btn_cerrar.setText("✅ Cerrar")
        self.btn_cerrar.clicked.connect(self.close)

    # ========= MÉTODOS DE GESTIÓN DE LABORATORIOS =========

    def nuevo_laboratorio(self):
        """Crear nuevo laboratorio"""
        dialog = DialogoLaboratorio(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            datos = dialog.get_datos()
            self.laboratorios[datos['nombre']] = {
                'capacidad': datos['capacidad'],
                'equipamiento': datos['equipamiento'],
                'edificio': datos['edificio']
            }
            self.actualizar_lista_laboratorios()
            self.actualizar_combos()

    def editar_laboratorio(self):
        """Editar laboratorio seleccionado"""
        item = self.lista_laboratorios.currentItem()
        if item is None:
            self.mostrar_mensaje("⚠️ Aviso", "Selecciona un laboratorio para editar")
            return

        nombre = item.text().split(' (')[0]
        datos_actuales = self.laboratorios[nombre]

        dialog = DialogoLaboratorio(self, datos_actuales, nombre)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            nuevos_datos = dialog.get_datos()

            # Si cambió el nombre, actualizar clave
            if nuevos_datos['nombre'] != nombre:
                del self.laboratorios[nombre]
                self.laboratorios[nuevos_datos['nombre']] = {
                    'capacidad': nuevos_datos['capacidad'],
                    'equipamiento': nuevos_datos['equipamiento'],
                    'edificio': nuevos_datos['edificio']
                }
            else:
                self.laboratorios[nombre].update({
                    'capacidad': nuevos_datos['capacidad'],
                    'equipamiento': nuevos_datos['equipamiento'],
                    'edificio': nuevos_datos['edificio']
                })

            self.actualizar_lista_laboratorios()
            self.actualizar_combos()

    def eliminar_laboratorio(self):
        """Eliminar laboratorio seleccionado"""
        item = self.lista_laboratorios.currentItem()
        if item is None:
            self.mostrar_mensaje("⚠️ Aviso", "Selecciona un laboratorio para eliminar")
            return

        nombre = item.text().split(' (')[0]

        reply = QtWidgets.QMessageBox.question(
            self, "Confirmar", f"¿Eliminar laboratorio '{nombre}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            del self.laboratorios[nombre]
            self.actualizar_lista_laboratorios()
            self.actualizar_combos()

    # ========= MÉTODOS DE GESTIÓN DE CURSOS =========

    def nuevo_curso(self):
        """Crear nuevo curso"""
        dialog = DialogoCurso(self, self.cursos)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            datos = dialog.get_datos()
            self.cursos[datos['codigo']] = {
                'descripcion': datos['descripcion'],
                'es_doble_grado': datos['es_doble_grado'],
                'comparte_con': datos['comparte_con']
            }
            self.actualizar_lista_cursos()
            self.actualizar_combos()

    def editar_curso(self):
        """Editar curso seleccionado"""
        item = self.lista_cursos.currentItem()
        if item is None:
            self.mostrar_mensaje("⚠️ Aviso", "Selecciona un curso para editar")
            return

        codigo = item.text().split(' -')[0]
        datos_actuales = self.cursos[codigo]

        dialog = DialogoCurso(self, self.cursos, datos_actuales, codigo)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            nuevos_datos = dialog.get_datos()

            if nuevos_datos['codigo'] != codigo:
                del self.cursos[codigo]
                self.cursos[nuevos_datos['codigo']] = {
                    'descripcion': nuevos_datos['descripcion'],
                    'es_doble_grado': nuevos_datos['es_doble_grado'],
                    'comparte_con': nuevos_datos['comparte_con']
                }
            else:
                self.cursos[codigo].update({
                    'descripcion': nuevos_datos['descripcion'],
                    'es_doble_grado': nuevos_datos['es_doble_grado'],
                    'comparte_con': nuevos_datos['comparte_con']
                })

            self.actualizar_lista_cursos()
            self.actualizar_combos()

    def eliminar_curso(self):
        """Eliminar curso seleccionado"""
        item = self.lista_cursos.currentItem()
        if item is None:
            self.mostrar_mensaje("⚠️ Aviso", "Selecciona un curso para eliminar")
            return

        codigo = item.text().split(' -')[0]

        reply = QtWidgets.QMessageBox.question(
            self, "Confirmar", f"¿Eliminar curso '{codigo}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            del self.cursos[codigo]
            self.actualizar_lista_cursos()
            self.actualizar_combos()

    # ========= MÉTODOS DE ASIGNACIÓN =========

    def validar_turno_curso(self, codigo_curso):
        """Validar y mostrar info del turno según código de curso"""
        if not codigo_curso:
            self.label_turno_info.setText("")
            return

        try:
            # Extraer número de turno (últimos 2 dígitos)
            numero_turno = int(codigo_curso[-2:])

            if numero_turno < 5:
                turno_teoria = "MAÑANA"
                turno_labs = "TARDE (15:00-20:00)"
                color = "orange"
            else:
                turno_teoria = "TARDE"
                turno_labs = "MAÑANA (8:00-14:00)"
                color = "lightblue"

            info = f"Teoría: {turno_teoria}\nLabs: {turno_labs}"
            self.label_turno_info.setText(info)
            self.label_turno_info.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")

        except (ValueError, IndexError):
            self.label_turno_info.setText("Código de curso inválido")
            self.label_turno_info.setStyleSheet("color: red; font-size: 10px;")

    def crear_asignacion(self):
        """Crear nueva asignación de horario"""
        curso = self.combo_form_curso.currentText()
        laboratorio = self.combo_form_lab.currentText()
        dia = self.combo_form_dia.currentText()
        inicio = self.time_form_inicio.time().toString("HH:mm")
        fin = self.time_form_fin.time().toString("HH:mm")

        if not all([curso, laboratorio, dia]):
            self.mostrar_mensaje("⚠️ Aviso", "Completa todos los campos")
            return

        if inicio >= fin:
            self.mostrar_mensaje("❌ Error", "La hora de inicio debe ser anterior a la hora de fin")
            return

        # Verificar conflictos
        if self.verificar_conflictos(curso, laboratorio, dia, inicio, fin):
            return

        # Crear ID único
        asignacion_id = f"{curso}_{laboratorio}_{dia}_{inicio}"

        self.asignaciones[asignacion_id] = {
            'curso': curso,
            'laboratorio': laboratorio,
            'dia': dia,
            'inicio': inicio,
            'fin': fin
        }

        self.actualizar_tabla_asignaciones()
        self.actualizar_calendario()
        self.limpiar_formulario()

        # Verificar dobles grados
        self.verificar_dobles_grados(curso, laboratorio, dia, inicio, fin)

    def verificar_conflictos(self, curso, laboratorio, dia, inicio, fin):
        """Verificar conflictos de horario"""
        for asignacion in self.asignaciones.values():
            if (asignacion['laboratorio'] == laboratorio and
                    asignacion['dia'] == dia):

                # Verificar solapamiento de horarios
                inicio_existente = asignacion['inicio']
                fin_existente = asignacion['fin']

                if not (fin <= inicio_existente or inicio >= fin_existente):
                    self.mostrar_mensaje("❌ Conflicto",
                                         f"Laboratorio {laboratorio} ya ocupado el {dia} de {inicio_existente} a {fin_existente}")
                    return True
        return False

    def verificar_dobles_grados(self, curso_asignado, laboratorio, dia, inicio, fin):
        """Verificar si hay cursos de doble grado que deberían compartir este laboratorio"""
        cursos_que_comparten = []

        for codigo, datos in self.cursos.items():
            if (datos['es_doble_grado'] and
                    datos['comparte_con'] == curso_asignado and
                    codigo != curso_asignado):
                cursos_que_comparten.append(codigo)

        if cursos_que_comparten:
            cursos_str = ", ".join(cursos_que_comparten)
            mensaje = f"💡 Cursos de doble grado detectados: {cursos_str}\n"
            mensaje += f"Pueden compartir laboratorio {laboratorio} el {dia}"
            self.label_doble_info.setText(mensaje)
        else:
            self.label_doble_info.setText("")

    def eliminar_asignacion(self, asignacion_id):
        """Eliminar asignación"""
        if asignacion_id in self.asignaciones:
            del self.asignaciones[asignacion_id]
            self.actualizar_tabla_asignaciones()
            self.actualizar_calendario()

    def limpiar_formulario(self):
        """Limpiar formulario de asignación"""
        self.combo_form_curso.setCurrentIndex(-1)
        self.combo_form_lab.setCurrentIndex(-1)
        self.combo_form_dia.setCurrentIndex(0)
        self.time_form_inicio.setTime(QtCore.QTime(8, 0))
        self.time_form_fin.setTime(QtCore.QTime(10, 0))
        self.label_turno_info.setText("")
        self.label_doble_info.setText("")

    # ========= MÉTODOS DE ACTUALIZACIÓN =========

    def actualizar_lista_laboratorios(self):
        """Actualizar lista de laboratorios"""
        self.lista_laboratorios.clear()
        for nombre, datos in self.laboratorios.items():
            texto = f"{nombre} (Cap: {datos['capacidad']})"
            self.lista_laboratorios.addItem(texto)

    def actualizar_lista_cursos(self):
        """Actualizar lista de cursos"""
        self.lista_cursos.clear()
        for codigo, datos in self.cursos.items():
            doble = " [DOBLE]" if datos['es_doble_grado'] else ""
            texto = f"{codigo} - {datos['descripcion']}{doble}"
            self.lista_cursos.addItem(texto)

    def actualizar_combos(self):
        """Actualizar combos del formulario"""
        # Cursos
        self.combo_form_curso.clear()
        self.combo_form_curso.addItems(list(self.cursos.keys()))

        # Laboratorios
        self.combo_form_lab.clear()
        self.combo_form_lab.addItems(list(self.laboratorios.keys()))

    def actualizar_tabla_asignaciones(self):
        """Actualizar tabla de asignaciones"""
        self.tabla_asignaciones.setRowCount(len(self.asignaciones))

        for row, (asignacion_id, datos) in enumerate(self.asignaciones.items()):
            self.tabla_asignaciones.setItem(row, 0, QtWidgets.QTableWidgetItem(datos['curso']))
            self.tabla_asignaciones.setItem(row, 1, QtWidgets.QTableWidgetItem(datos['laboratorio']))
            self.tabla_asignaciones.setItem(row, 2, QtWidgets.QTableWidgetItem(datos['dia']))
            self.tabla_asignaciones.setItem(row, 3, QtWidgets.QTableWidgetItem(datos['inicio']))
            self.tabla_asignaciones.setItem(row, 4, QtWidgets.QTableWidgetItem(datos['fin']))

            # Botón eliminar
            btn_eliminar = QtWidgets.QPushButton("🗑️")
            btn_eliminar.clicked.connect(lambda checked, aid=asignacion_id: self.eliminar_asignacion(aid))
            self.tabla_asignaciones.setCellWidget(row, 5, btn_eliminar)

    def actualizar_calendario(self):
        """Actualizar vista calendario"""
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

        for dia in dias:
            asignaciones_dia = [a for a in self.asignaciones.values() if a['dia'] == dia]
            asignaciones_dia.sort(key=lambda x: x['inicio'])

            texto = f"📅 {dia.upper()}\n"
            texto += "=" * 30 + "\n\n"

            if not asignaciones_dia:
                texto += "Sin laboratorios programados\n"
            else:
                for asig in asignaciones_dia:
                    curso_info = ""
                    if asig['curso'] in self.cursos:
                        curso_data = self.cursos[asig['curso']]
                        if curso_data['es_doble_grado']:
                            curso_info = f" [DOBLE con {curso_data['comparte_con']}]"

                    texto += f"⏰ {asig['inicio']}-{asig['fin']}\n"
                    texto += f"🏢 {asig['laboratorio']}\n"
                    texto += f"👥 {asig['curso']}{curso_info}\n\n"

            self.tabs_dias[dia].setText(texto)

    def seleccionar_laboratorio(self, row):
        """Mostrar información del laboratorio seleccionado"""
        if row == -1:
            return

        item = self.lista_laboratorios.item(row)
        nombre = item.text().split(' (')[0]
        datos = self.laboratorios[nombre]

        info = f"🏢 LABORATORIO: {nombre}\n\n"
        info += f"👥 Capacidad: {datos['capacidad']} alumnos\n"
        info += f"🔧 Equipamiento: {datos['equipamiento']}\n"
        info += f"🏗️ Edificio: {datos['edificio']}\n\n"

        # Contar asignaciones
        asignaciones_lab = [a for a in self.asignaciones.values() if a['laboratorio'] == nombre]
        info += f"📅 Horarios asignados: {len(asignaciones_lab)}\n"

        self.info_recurso.setText(info)

    def seleccionar_curso(self, row):
        """Mostrar información del curso seleccionado"""
        if row == -1:
            return

        item = self.lista_cursos.item(row)
        codigo = item.text().split(' -')[0]
        datos = self.cursos[codigo]

        info = f"👥 CURSO: {codigo}\n\n"
        info += f"📝 Descripción: {datos['descripcion']}\n"
        info += f"🎓 Doble grado: {'Sí' if datos['es_doble_grado'] else 'No'}\n"

        if datos['es_doble_grado']:
            info += f"🔗 Comparte con: {datos['comparte_con']}\n"

        # Analizar código
        try:
            numero_turno = int(codigo[-2:])
            turno_teoria = "MAÑANA" if numero_turno < 5 else "TARDE"
            turno_labs = "TARDE" if numero_turno < 5 else "MAÑANA"
            info += f"\n⏰ Teoría: {turno_teoria}\n"
            info += f"🔬 Laboratorios: {turno_labs}\n"
        except:
            pass

        # Contar asignaciones
        asignaciones_curso = [a for a in self.asignaciones.values() if a['curso'] == codigo]
        info += f"\n📅 Laboratorios asignados: {len(asignaciones_curso)}\n"

        self.info_recurso.setText(info)

    # ========= MÉTODOS DE PERSISTENCIA =========

    def guardar_configuracion(self):
        """Guardar configuración"""
        try:
            os.makedirs("config", exist_ok=True)

            config_data = {
                'laboratorios': self.laboratorios,
                'cursos': self.cursos,
                'asignaciones': self.asignaciones,
                'fecha_guardado': datetime.now().isoformat()
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.mostrar_mensaje("✅ Éxito", f"Configuración guardada en:\n{self.config_path}")

        except Exception as e:
            self.mostrar_mensaje("❌ Error", f"Error guardando:\n{str(e)}")

    def cargar_configuracion(self, mostrar_mensaje=False):
        """Cargar configuración"""
        try:
            if not os.path.exists(self.config_path):
                self.cargar_datos_ejemplo()
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            self.laboratorios = config_data.get('laboratorios', {})
            self.cursos = config_data.get('cursos', {})
            self.asignaciones = config_data.get('asignaciones', {})

            self.actualizar_lista_laboratorios()
            self.actualizar_lista_cursos()
            self.actualizar_combos()
            self.actualizar_tabla_asignaciones()
            self.actualizar_calendario()

            if mostrar_mensaje:
                self.mostrar_mensaje("✅ Éxito", "Configuración cargada correctamente")

        except Exception as e:
            self.mostrar_mensaje("❌ Error", f"Error cargando:\n{str(e)}")
            self.cargar_datos_ejemplo()

    def cargar_datos_ejemplo(self):
        """Cargar datos de ejemplo"""
        self.laboratorios = {
            'Lab_Fisica_A': {'capacidad': 24, 'equipamiento': 'Equipos medición básicos', 'edificio': 'Edificio A'},
            'Lab_Fisica_B': {'capacidad': 20, 'equipamiento': 'Equipos medición avanzados', 'edificio': 'Edificio A'},
            'Lab_Quimica_A': {'capacidad': 18, 'equipamiento': 'Campana extractora', 'edificio': 'Edificio B'},
            'Lab_Expresion_Grafica': {'capacidad': 30, 'equipamiento': 'Ordenadores + CAD', 'edificio': 'Edificio C'}
        }

        self.cursos = {
            'M204': {'descripcion': 'Mecánica 2º Mañana', 'es_doble_grado': False, 'comparte_con': ''},
            'M206': {'descripcion': 'Mecánica 2º Tarde', 'es_doble_grado': False, 'comparte_con': ''},
            'E104': {'descripcion': 'Electrónica 1º Mañana', 'es_doble_grado': False, 'comparte_con': ''},
            'EE204': {'descripcion': 'Doble Electr. 2º Mañana', 'es_doble_grado': True, 'comparte_con': 'E204'}
        }

        self.asignaciones = {}

        self.actualizar_lista_laboratorios()
        self.actualizar_lista_cursos()
        self.actualizar_combos()
        self.actualizar_calendario()

    def exportar_horarios(self):
        """Exportar horarios a Excel"""
        try:
            import pandas as pd

            # Convertir asignaciones a DataFrame
            data = []
            for asignacion in self.asignaciones.values():
                data.append([
                    asignacion['curso'],
                    asignacion['laboratorio'],
                    asignacion['dia'],
                    asignacion['inicio'],
                    asignacion['fin']
                ])

            df = pd.DataFrame(data, columns=['Curso', 'Laboratorio', 'Día', 'Hora_Inicio', 'Hora_Fin'])

            filename = f"horarios_laboratorios_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            df.to_excel(filename, index=False)

            self.mostrar_mensaje("✅ Éxito", f"Horarios exportados a:\n{filename}")

        except ImportError:
            self.mostrar_mensaje("❌ Error", "Pandas no está instalado.\nNo se puede exportar a Excel.")
        except Exception as e:
            self.mostrar_mensaje("❌ Error", f"Error exportando:\n{str(e)}")

    def mostrar_mensaje(self, titulo, mensaje):
        """Mostrar mensaje"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.exec()

    def apply_dark_theme(self):
        """Aplicar tema oscuro"""
        self.setStyleSheet("""
            QMainWindow { background-color: rgb(53,53,53); color: white; }
            QWidget { 
                background-color: rgb(53,53,53); 
                color: white; 
                font-family: 'Segoe UI', Arial, sans-serif; 
                font-size: 12px;
            }
            QLabel { color: white; font-size: 13px; }
            QPushButton { 
                background-color: rgb(53,53,53); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px; 
                font-size: 12px; 
                border-radius: 3px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgb(66,66,66); }
            QListWidget { 
                background-color: rgb(42,42,42); 
                color: white; 
                border: 1px solid rgb(127,127,127);
                selection-background-color: rgb(42,130,218);
                font-size: 12px;
            }
            QTableWidget { 
                background-color: rgb(42,42,42); 
                color: white; 
                border: 1px solid rgb(127,127,127);
                gridline-color: rgb(127,127,127);
                font-size: 12px;
            }
            QTableWidget::item { 
                border-bottom: 1px solid rgb(127,127,127); 
                padding: 8px; 
            }
            QTableWidget::item:selected { background-color: rgb(42,130,218); }
            QHeaderView::section { 
                background-color: rgb(35,35,35); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QTextEdit { 
                background-color: rgb(42,42,42); 
                color: white; 
                border: 1px solid rgb(127,127,127);
                font-family: 'Consolas', monospace; 
                font-size: 12px; 
            }
            QComboBox, QTimeEdit { 
                background-color: rgb(42,42,42); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px;
                font-size: 12px;
            }
            QComboBox::drop-down { background-color: rgb(53,53,53); }
            QComboBox QAbstractItemView { 
                background-color: rgb(42,42,42); 
                color: white; 
                selection-background-color: rgb(42,130,218);
                font-size: 12px;
            }
            QTabWidget::pane { 
                border: 1px solid rgb(127,127,127); 
                background-color: rgb(42,42,42); 
            }
            QTabBar::tab { 
                background-color: rgb(53,53,53); 
                color: white; 
                border: 1px solid rgb(127,127,127);
                padding: 10px 20px; 
                margin-right: 2px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected { 
                background-color: rgb(42,130,218); 
                color: white; 
            }
            QTabBar::tab:hover { background-color: rgb(66,66,66); }
        """)


# ========= DIÁLOGOS AUXILIARES =========

class DialogoLaboratorio(QtWidgets.QDialog):
    """Diálogo para crear/editar laboratorio"""

    def __init__(self, parent=None, datos=None, nombre_actual=""):
        super().__init__(parent)
        self.datos_actuales = datos or {}
        self.nombre_actual = nombre_actual
        self.setupUi()
        if datos:
            self.cargar_datos()

    def setupUi(self):
        self.setWindowTitle("Configurar Laboratorio")
        self.setModal(True)
        self.resize(450, 350)

        # Aplicar tema oscuro al diálogo
        self.setStyleSheet("""
            QDialog { 
                background-color: rgb(53,53,53); 
                color: white; 
                font-size: 12px;
            }
            QLabel { 
                color: white; 
                font-size: 13px; 
                font-weight: bold; 
            }
            QLineEdit, QSpinBox, QTextEdit { 
                background-color: rgb(42,42,42); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px;
                font-size: 12px;
            }
            QPushButton { 
                background-color: rgb(53,53,53); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px; 
                font-size: 12px; 
            }
            QPushButton:hover { background-color: rgb(66,66,66); }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)

        # Nombre
        layout.addWidget(QtWidgets.QLabel("Nombre del Laboratorio:"))
        self.line_nombre = QtWidgets.QLineEdit()
        self.line_nombre.setMinimumHeight(30)
        layout.addWidget(self.line_nombre)

        # Capacidad
        layout.addWidget(QtWidgets.QLabel("Capacidad (número de alumnos):"))
        self.spin_capacidad = QtWidgets.QSpinBox()
        self.spin_capacidad.setMinimumHeight(30)
        self.spin_capacidad.setMinimum(1)
        self.spin_capacidad.setMaximum(100)
        self.spin_capacidad.setValue(24)
        layout.addWidget(self.spin_capacidad)

        # Equipamiento
        layout.addWidget(QtWidgets.QLabel("Equipamiento disponible:"))
        self.text_equipamiento = QtWidgets.QTextEdit()
        self.text_equipamiento.setMaximumHeight(100)
        layout.addWidget(self.text_equipamiento)

        # Edificio
        layout.addWidget(QtWidgets.QLabel("Edificio/Ubicación:"))
        self.line_edificio = QtWidgets.QLineEdit()
        self.line_edificio.setMinimumHeight(30)
        layout.addWidget(self.line_edificio)

        # Botones
        botones = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def cargar_datos(self):
        """Cargar datos existentes"""
        self.line_nombre.setText(self.nombre_actual)
        self.spin_capacidad.setValue(self.datos_actuales.get('capacidad', 24))
        self.text_equipamiento.setText(self.datos_actuales.get('equipamiento', ''))
        self.line_edificio.setText(self.datos_actuales.get('edificio', ''))

    def get_datos(self):
        """Obtener datos del formulario"""
        return {
            'nombre': self.line_nombre.text().strip(),
            'capacidad': self.spin_capacidad.value(),
            'equipamiento': self.text_equipamiento.toPlainText().strip(),
            'edificio': self.line_edificio.text().strip()
        }


class DialogoCurso(QtWidgets.QDialog):
    """Diálogo para crear/editar curso"""

    def __init__(self, parent=None, cursos_existentes=None, datos=None, codigo_actual=""):
        super().__init__(parent)
        self.cursos_existentes = cursos_existentes or {}
        self.datos_actuales = datos or {}
        self.codigo_actual = codigo_actual
        self.setupUi()
        if datos:
            self.cargar_datos()

    def setupUi(self):
        self.setWindowTitle("Configurar Curso")
        self.setModal(True)
        self.resize(500, 400)

        # Aplicar tema oscuro al diálogo
        self.setStyleSheet("""
            QDialog { 
                background-color: rgb(53,53,53); 
                color: white; 
                font-size: 12px;
            }
            QLabel { 
                color: white; 
                font-size: 13px; 
                font-weight: bold; 
            }
            QLineEdit, QComboBox { 
                background-color: rgb(42,42,42); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px;
                font-size: 12px;
            }
            QCheckBox { 
                color: white; 
                font-size: 12px; 
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: rgb(42,42,42);
                border: 1px solid rgb(127,127,127);
            }
            QCheckBox::indicator:checked {
                background-color: rgb(42,130,218);
                border: 1px solid rgb(42,130,218);
            }
            QPushButton { 
                background-color: rgb(53,53,53); 
                color: white; 
                border: 1px solid rgb(127,127,127); 
                padding: 8px; 
                font-size: 12px; 
            }
            QPushButton:hover { background-color: rgb(66,66,66); }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)

        # Código
        layout.addWidget(QtWidgets.QLabel("Código del Curso (ej: M204, EE206):"))
        self.line_codigo = QtWidgets.QLineEdit()
        self.line_codigo.setMinimumHeight(30)
        self.line_codigo.textChanged.connect(self.validar_codigo)
        layout.addWidget(self.line_codigo)

        self.label_codigo_info = QtWidgets.QLabel("")
        self.label_codigo_info.setStyleSheet("color: orange; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.label_codigo_info)

        # Descripción
        layout.addWidget(QtWidgets.QLabel("Descripción del Curso:"))
        self.line_descripcion = QtWidgets.QLineEdit()
        self.line_descripcion.setMinimumHeight(30)
        layout.addWidget(self.line_descripcion)

        # Es doble grado
        self.check_doble = QtWidgets.QCheckBox("Es un curso de doble grado")
        self.check_doble.toggled.connect(self.toggle_doble_grado)
        layout.addWidget(self.check_doble)

        # Comparte con
        self.label_comparte = QtWidgets.QLabel("Comparte laboratorio con:")
        self.combo_comparte = QtWidgets.QComboBox()
        self.combo_comparte.setMinimumHeight(30)
        layout.addWidget(self.label_comparte)
        layout.addWidget(self.combo_comparte)

        # Inicialmente ocultar
        self.label_comparte.setVisible(False)
        self.combo_comparte.setVisible(False)

        # Botones
        botones = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def validar_codigo(self, codigo):
        """Validar código de curso"""
        if not codigo:
            self.label_codigo_info.setText("")
            return

        try:
            if len(codigo) >= 3:
                numero_turno = int(codigo[-2:])
                if numero_turno < 5:
                    info = "Teoría: MAÑANA → Labs: TARDE"
                else:
                    info = "Teoría: TARDE → Labs: MAÑANA"
                self.label_codigo_info.setText(info)
            else:
                self.label_codigo_info.setText("Código incompleto")
        except ValueError:
            self.label_codigo_info.setText("Formato inválido")

    def toggle_doble_grado(self, checked):
        """Mostrar/ocultar opciones de doble grado"""
        self.label_comparte.setVisible(checked)
        self.combo_comparte.setVisible(checked)

        if checked:
            # Actualizar lista de cursos disponibles
            self.combo_comparte.clear()
            cursos_disponibles = [c for c in self.cursos_existentes.keys() if c != self.codigo_actual]
            self.combo_comparte.addItems(cursos_disponibles)

    def cargar_datos(self):
        """Cargar datos existentes"""
        self.line_codigo.setText(self.codigo_actual)
        self.line_descripcion.setText(self.datos_actuales.get('descripcion', ''))
        self.check_doble.setChecked(self.datos_actuales.get('es_doble_grado', False))

        if self.datos_actuales.get('es_doble_grado', False):
            comparte_con = self.datos_actuales.get('comparte_con', '')
            if comparte_con:
                index = self.combo_comparte.findText(comparte_con)
                if index >= 0:
                    self.combo_comparte.setCurrentIndex(index)

    def get_datos(self):
        """Obtener datos del formulario"""
        return {
            'codigo': self.line_codigo.text().strip(),
            'descripcion': self.line_descripcion.text().strip(),
            'es_doble_grado': self.check_doble.isChecked(),
            'comparte_con': self.combo_comparte.currentText() if self.check_doble.isChecked() else ''
        }


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ConfigurarHorarios()
    window.show()
    sys.exit(app.exec())