import sys
import json
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from datetime import datetime

# Importar el scraper del calendario
try:
    from modules.utils.obtener_datos_calendario import obtener_calendario_web

    SCRAPER_DISPONIBLE = True
except ImportError:
    print("⚠️ Módulo obtener_datos_calendario no disponible")
    SCRAPER_DISPONIBLE = False


class ConfigurarCalendario(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.datos_calendario = {
            'semestre_1': {'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [], 'viernes': []},
            'semestre_2': {'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [], 'viernes': []},
            'dias_especiales': {},
            'curso_academico': f"{datetime.now().year}-{datetime.now().year + 1}",
            'fecha_creacion': datetime.now().isoformat()
        }

        # URL desde configuración
        self.url_calendario = "https://www.etsidi.upm.es/Estudiantes/AgendaAcademica/AACalendario"
        self.cargar_url_desde_config()

        self.setupUi()

    def cargar_url_desde_config(self):
        """Cargar URL desde configuracion_labs.xml"""
        try:
            import xml.etree.ElementTree as ET
            if os.path.exists('configuracion_labs.xml'):
                tree = ET.parse('configuracion_labs.xml')
                root = tree.getroot()

                for urls in root.findall('URLs'):
                    for url in urls.findall('url_calendario'):
                        self.url_calendario = url.text
                        break
        except Exception as e:
            print(f"Error cargando URL desde config: {e}")

    def setupUi(self):
        self.setObjectName("ConfigurarCalendario")
        self.resize(1200, 700)
        self.setMinimumSize(QtCore.QSize(1200, 700))
        self.setMaximumSize(QtCore.QSize(1200, 700))
        self.setWindowTitle("OPTIM - Configurar Calendario Académico")

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # ========= TÍTULO =========
        self.titulo = QtWidgets.QLabel(self.centralwidget)
        self.titulo.setGeometry(QtCore.QRect(50, 10, 1100, 35))
        self.titulo.setText("Configuración de Calendario Académico - Días Lectivos")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titulo.setStyleSheet("""
            QLabel {
                color: rgb(42,130,218);
                font-size: 16px;
                font-weight: bold;
                background-color: rgb(35,35,35);
                border: 1px solid rgb(42,130,218);
                border-radius: 5px;
                padding: 8px;
            }
        """)

        # ========= BOTONES SUPERIORES =========
        self.setup_botones_superiores()

        # ========= PANELES DUALES DE SEMESTRES =========
        self.setup_paneles_semestres()

        # ========= CONFIGURACIÓN DÍA SELECCIONADO =========
        self.setup_configuracion_dia()

        # ========= BOTONES PRINCIPALES =========
        self.setup_botones_principales()

        # ========= ÁREA DE LOG =========
        self.setup_area_log()

        # ========= TEMA OSCURO =========
        self.apply_dark_theme()

    def setup_botones_superiores(self):
        """Botones de acción superiores"""
        # Botón Obtener de Web
        self.btn_obtener_web = QtWidgets.QPushButton(self.centralwidget)
        self.btn_obtener_web.setGeometry(QtCore.QRect(50, 60, 150, 35))
        self.btn_obtener_web.setText("🌐 Obtener de Web")
        self.btn_obtener_web.setEnabled(SCRAPER_DISPONIBLE)
        self.btn_obtener_web.clicked.connect(self.obtener_desde_web)
        self.btn_obtener_web.setStyleSheet("""
            QPushButton {
                background-color: rgb(42,130,218);
                color: white;
                border: none;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgb(35,110,190);
            }
            QPushButton:disabled {
                background-color: rgb(60,60,60);
                color: rgb(140,140,140);
            }
        """)

        # Información URL
        self.label_url = QtWidgets.QLabel(self.centralwidget)
        self.label_url.setGeometry(QtCore.QRect(220, 60, 600, 35))
        self.label_url.setText(f"📍 Fuente: {self.url_calendario}")
        self.label_url.setStyleSheet("color: rgb(180,180,180); font-size: 10px;")
        self.label_url.setWordWrap(True)

    def setup_paneles_semestres(self):
        """Paneles visuales duales para ambos semestres"""
        # Panel 1º Semestre
        self.frame_sem1 = QtWidgets.QFrame(self.centralwidget)
        self.frame_sem1.setGeometry(QtCore.QRect(50, 120, 550, 300))
        self.frame_sem1.setStyleSheet("""
            QFrame {
                background-color: rgb(35,35,35);
                border: 2px solid rgb(42,130,218);
                border-radius: 8px;
            }
        """)

        self.label_sem1 = QtWidgets.QLabel(self.frame_sem1)
        self.label_sem1.setGeometry(QtCore.QRect(10, 10, 530, 25))
        self.label_sem1.setText("📅 1º SEMESTRE (Septiembre - Enero)")
        self.label_sem1.setStyleSheet("color: rgb(42,130,218); font-weight: bold; font-size: 14px; border: none;")

        # Tabla 1º Semestre
        self.tabla_sem1 = QtWidgets.QTableWidget(self.frame_sem1)
        self.tabla_sem1.setGeometry(QtCore.QRect(10, 45, 530, 240))
        self.setup_tabla_semestre(self.tabla_sem1)

        # Panel 2º Semestre
        self.frame_sem2 = QtWidgets.QFrame(self.centralwidget)
        self.frame_sem2.setGeometry(QtCore.QRect(620, 120, 550, 300))
        self.frame_sem2.setStyleSheet("""
            QFrame {
                background-color: rgb(35,35,35);
                border: 2px solid rgb(46,204,113);
                border-radius: 8px;
            }
        """)

        self.label_sem2 = QtWidgets.QLabel(self.frame_sem2)
        self.label_sem2.setGeometry(QtCore.QRect(10, 10, 530, 25))
        self.label_sem2.setText("📅 2º SEMESTRE (Febrero - Junio)")
        self.label_sem2.setStyleSheet("color: rgb(46,204,113); font-weight: bold; font-size: 14px; border: none;")

        # Tabla 2º Semestre
        self.tabla_sem2 = QtWidgets.QTableWidget(self.frame_sem2)
        self.tabla_sem2.setGeometry(QtCore.QRect(10, 45, 530, 240))
        self.setup_tabla_semestre(self.tabla_sem2)

    def setup_tabla_semestre(self, tabla):
        """Configurar tabla de semestre"""
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'])
        tabla.setRowCount(20)  # Suficientes filas para todas las fechas

        # Configurar columnas
        for i in range(5):
            tabla.setColumnWidth(i, 100)

        # Conectar señal de selección
        tabla.cellClicked.connect(self.celda_seleccionada)

        # Estilo de tabla
        tabla.setStyleSheet("""
            QTableWidget {
                background-color: rgb(42,42,42);
                color: white;
                border: 1px solid rgb(127,127,127);
                gridline-color: rgb(127,127,127);
            }
            QTableWidget::item {
                border-bottom: 1px solid rgb(127,127,127);
                padding: 8px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: rgb(42,130,218);
            }
            QHeaderView::section {
                background-color: rgb(35,35,35);
                color: white;
                border: 1px solid rgb(127,127,127);
                padding: 8px;
                font-weight: bold;
            }
        """)

    def setup_configuracion_dia(self):
        """Panel de configuración para día seleccionado"""
        self.label_config_dia = QtWidgets.QLabel(self.centralwidget)
        self.label_config_dia.setGeometry(QtCore.QRect(50, 440, 400, 25))
        self.label_config_dia.setText("⚙️ Configurar Día Seleccionado:")
        self.label_config_dia.setStyleSheet("color: rgb(42,130,218); font-weight: bold; font-size: 12px;")

        # Información del día seleccionado
        self.info_dia_sel = QtWidgets.QLabel(self.centralwidget)
        self.info_dia_sel.setGeometry(QtCore.QRect(50, 470, 400, 20))
        self.info_dia_sel.setText("Selecciona una fecha en las tablas superiores")

        # Opciones de configuración
        self.radio_normal = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_normal.setGeometry(QtCore.QRect(50, 500, 150, 20))
        self.radio_normal.setText("Día lectivo normal")
        self.radio_normal.setChecked(True)

        self.radio_especial = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_especial.setGeometry(QtCore.QRect(50, 525, 150, 20))
        self.radio_especial.setText("Día especial:")

        # Combo tipo horario especial
        self.combo_tipo_especial = QtWidgets.QComboBox(self.centralwidget)
        self.combo_tipo_especial.setGeometry(QtCore.QRect(210, 525, 150, 25))
        tipos = ["Horario Lunes", "Horario Martes", "Horario Miércoles", "Horario Jueves", "Horario Viernes"]
        self.combo_tipo_especial.addItems(tipos)
        self.combo_tipo_especial.setEnabled(False)

        self.radio_especial.toggled.connect(lambda checked: self.combo_tipo_especial.setEnabled(checked))

        # Descripción
        self.label_desc = QtWidgets.QLabel(self.centralwidget)
        self.label_desc.setGeometry(QtCore.QRect(50, 560, 100, 20))
        self.label_desc.setText("Descripción:")

        self.line_descripcion = QtWidgets.QLineEdit(self.centralwidget)
        self.line_descripcion.setGeometry(QtCore.QRect(160, 560, 200, 25))
        self.line_descripcion.setPlaceholderText("Ej: Día del Pilar, Constitución...")

        # Botón aplicar configuración
        self.btn_aplicar_dia = QtWidgets.QPushButton(self.centralwidget)
        self.btn_aplicar_dia.setGeometry(QtCore.QRect(380, 560, 100, 25))
        self.btn_aplicar_dia.setText("✅ Aplicar")
        self.btn_aplicar_dia.clicked.connect(self.aplicar_configuracion_dia)

    def setup_area_log(self):
        """Área de log/información"""
        self.label_log = QtWidgets.QLabel(self.centralwidget)
        self.label_log.setGeometry(QtCore.QRect(500, 440, 300, 20))
        self.label_log.setText("📝 Información del Sistema:")
        self.label_log.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")

        self.log_area = QtWidgets.QTextEdit(self.centralwidget)
        self.log_area.setGeometry(QtCore.QRect(500, 470, 670, 120))
        self.log_area.setReadOnly(True)
        self.log_area.setText(
            "Sistema listo para configurar calendario académico...\n\n📍 Obtener datos automáticamente desde web o configurar manualmente\n📅 Días lectivos organizados por semestre\n⚙️ Configuración de días especiales con tipos de horario")

    def setup_botones_principales(self):
        """Botones principales de la interfaz"""
        # Guardar
        self.btn_guardar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_guardar.setGeometry(QtCore.QRect(600, 610, 120, 40))
        self.btn_guardar.setText("💾 Guardar")
        self.btn_guardar.clicked.connect(self.guardar_configuracion)

        # Cargar
        self.btn_cargar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cargar.setGeometry(QtCore.QRect(730, 610, 120, 40))
        self.btn_cargar.setText("📂 Cargar")
        self.btn_cargar.clicked.connect(self.cargar_configuracion)

        # Limpiar
        self.btn_limpiar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_limpiar.setGeometry(QtCore.QRect(860, 610, 120, 40))
        self.btn_limpiar.setText("🧹 Limpiar")
        self.btn_limpiar.clicked.connect(self.limpiar_calendarios)

        # Cerrar
        self.btn_cerrar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cerrar.setGeometry(QtCore.QRect(990, 610, 120, 40))
        self.btn_cerrar.setText("✅ Cerrar")
        self.btn_cerrar.clicked.connect(self.close)

    def obtener_desde_web(self):
        """Obtener datos automáticamente desde la web"""
        if not SCRAPER_DISPONIBLE:
            self.mostrar_mensaje("❌ Error", "Módulo de web scraping no disponible")
            return

        self.log_info("🌐 Iniciando obtención automática desde web...")
        self.btn_obtener_web.setEnabled(False)
        self.btn_obtener_web.setText("⏳ Obteniendo...")

        try:
            # Llamar al scraper
            datos, cod_error, mensaje = obtener_calendario_web(self.url_calendario, headless=True)

            if cod_error == 0:
                self.datos_calendario = datos
                self.actualizar_tablas_semestres()
                self.log_info("✅ Datos obtenidos correctamente desde web")
                self.log_info(f"📅 Curso académico: {datos.get('curso_academico', 'N/A')}")
                self.log_info(f"📊 Días especiales detectados: {len(datos.get('dias_especiales', {}))}")
                self.mostrar_mensaje("✅ Éxito", "Calendario obtenido correctamente desde la web")
            else:
                self.log_info(f"❌ Error: {mensaje}")
                self.mostrar_mensaje("❌ Error", f"Error obteniendo calendario:\n{mensaje}")

        except Exception as e:
            self.log_info(f"❌ Excepción: {str(e)}")
            self.mostrar_mensaje("❌ Error", f"Error inesperado:\n{str(e)}")

        finally:
            self.btn_obtener_web.setEnabled(True)
            self.btn_obtener_web.setText("🌐 Obtener de Web")

    def actualizar_tablas_semestres(self):
        """Actualizar las tablas con los datos cargados"""
        # Actualizar 1º Semestre
        self.poblar_tabla_semestre(self.tabla_sem1, self.datos_calendario['semestre_1'])

        # Actualizar 2º Semestre
        self.poblar_tabla_semestre(self.tabla_sem2, self.datos_calendario['semestre_2'])

    def poblar_tabla_semestre(self, tabla, datos_semestre):
        """Poblar tabla de semestre con datos"""
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']

        # Limpiar tabla
        tabla.clearContents()

        # Encontrar la fila máxima necesaria
        max_filas = max(len(datos_semestre[dia]) for dia in dias_semana)
        tabla.setRowCount(max_filas)

        # Poblar cada columna (día de la semana)
        for col, dia in enumerate(dias_semana):
            fechas = datos_semestre[dia]
            for fila, fecha in enumerate(fechas):
                item = QtWidgets.QTableWidgetItem(str(fecha))

                # Aplicar estilo especial para días con asterisco
                if '*' in str(fecha):
                    item.setBackground(QtGui.QColor(241, 196, 15))  # Amarillo para días especiales
                    item.setForeground(QtGui.QColor(0, 0, 0))  # Texto negro
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                tabla.setItem(fila, col, item)

    def celda_seleccionada(self, fila, columna):
        """Manejar selección de celda en tabla"""
        sender = self.sender()
        item = sender.item(fila, columna)

        if item and item.text():
            fecha = item.text()
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
            dia_semana = dias_semana[columna]

            # Determinar semestre
            semestre = "1º" if sender == self.tabla_sem1 else "2º"

            self.info_dia_sel.setText(f"Seleccionado: {fecha} ({dia_semana} - {semestre} Semestre)")

            # Verificar si es día especial
            if '*' in fecha:
                self.radio_especial.setChecked(True)
                if fecha in self.datos_calendario['dias_especiales']:
                    dia_config = self.datos_calendario['dias_especiales'][fecha]
                    tipo_horario = dia_config.get('tipo', 'horario_especial')
                    # Mapear tipo a índice del combo
                    tipos = ['horario_lunes', 'horario_martes', 'horario_miercoles', 'horario_jueves',
                             'horario_viernes']
                    if tipo_horario in tipos:
                        self.combo_tipo_especial.setCurrentIndex(tipos.index(tipo_horario))
                    self.line_descripcion.setText(dia_config.get('descripcion', ''))
            else:
                self.radio_normal.setChecked(True)
                self.line_descripcion.clear()

    def aplicar_configuracion_dia(self):
        """Aplicar configuración al día seleccionado"""
        # Obtener día seleccionado desde las tablas
        fecha_sel = None
        tabla_sel = None

        # Verificar cuál tabla tiene selección
        if self.tabla_sem1.currentItem():
            fecha_sel = self.tabla_sem1.currentItem().text()
            tabla_sel = self.tabla_sem1
        elif self.tabla_sem2.currentItem():
            fecha_sel = self.tabla_sem2.currentItem().text()
            tabla_sel = self.tabla_sem2

        if not fecha_sel:
            self.mostrar_mensaje("⚠️ Aviso", "Selecciona una fecha en las tablas")
            return

        # Aplicar configuración según el tipo seleccionado
        if self.radio_especial.isChecked():
            # Convertir a día especial
            fecha_nueva = fecha_sel.replace('*', '') + '*'

            tipos = ['horario_lunes', 'horario_martes', 'horario_miercoles', 'horario_jueves', 'horario_viernes']
            tipo_seleccionado = tipos[self.combo_tipo_especial.currentIndex()]

            self.datos_calendario['dias_especiales'][fecha_nueva] = {
                'tipo': tipo_seleccionado,
                'descripcion': self.line_descripcion.text()
            }

            # Actualizar tabla
            tabla_sel.currentItem().setText(fecha_nueva)
            tabla_sel.currentItem().setBackground(QtGui.QColor(241, 196, 15))
            tabla_sel.currentItem().setForeground(QtGui.QColor(0, 0, 0))

        else:
            # Día normal - quitar asterisco si lo tiene
            fecha_nueva = fecha_sel.replace('*', '')

            # Remover de días especiales si existía
            if fecha_sel in self.datos_calendario['dias_especiales']:
                del self.datos_calendario['dias_especiales'][fecha_sel]

            # Actualizar tabla
            tabla_sel.currentItem().setText(fecha_nueva)
            tabla_sel.currentItem().setBackground(QtGui.QColor(42, 42, 42))
            tabla_sel.currentItem().setForeground(QtGui.QColor(255, 255, 255))

        self.log_info(f"✅ Configuración aplicada a fecha: {fecha_nueva}")

    def guardar_configuracion(self):
        """Guardar configuración con QFileDialog"""
        nombre_default = "OPTIM_Calendario_Academico.json"

        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Guardar Configuración de Calendario',
            nombre_default,
            'Archivos JSON (*.json)'
        )

        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    json.dump(self.datos_calendario, f, indent=2, ensure_ascii=False)

                self.log_info(f"💾 Configuración guardada: {fname}")
                self.mostrar_mensaje("✅ Éxito", f"Configuración guardada en:\n{fname}")

            except Exception as e:
                self.log_info(f"❌ Error guardando: {str(e)}")
                self.mostrar_mensaje("❌ Error", f"Error guardando:\n{str(e)}")

    def cargar_configuracion(self):
        """Cargar configuración con QFileDialog"""
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Cargar Configuración de Calendario',
            '',
            'Archivos JSON (*.json)'
        )

        if fname:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    self.datos_calendario = json.load(f)

                self.actualizar_tablas_semestres()
                self.log_info(f"📂 Configuración cargada: {fname}")
                self.mostrar_mensaje("✅ Éxito", "Configuración cargada correctamente")

            except Exception as e:
                self.log_info(f"❌ Error cargando: {str(e)}")
                self.mostrar_mensaje("❌ Error", f"Error cargando:\n{str(e)}")

    def limpiar_calendarios(self):
        """Limpiar todos los datos del calendario"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirmar",
            "¿Estás seguro de que quieres limpiar todos los datos del calendario?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.datos_calendario = {
                'semestre_1': {'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [], 'viernes': []},
                'semestre_2': {'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [], 'viernes': []},
                'dias_especiales': {},
                'curso_academico': f"{datetime.now().year}-{datetime.now().year + 1}",
                'fecha_creacion': datetime.now().isoformat()
            }

            self.actualizar_tablas_semestres()
            self.log_info("🧹 Calendarios limpiados")

    def log_info(self, mensaje):
        """Añadir mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {mensaje}")

        # Auto-scroll al final
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def mostrar_mensaje(self, titulo, mensaje):
        """Mostrar mensaje al usuario"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.exec()

    def apply_dark_theme(self):
        """Aplicar tema oscuro"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgb(53,53,53);
                color: white;
            }
            QWidget {
                background-color: rgb(53,53,53);
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: white;
                font-size: 11px;
            }
            QPushButton {
                background-color: rgb(53,53,53);
                color: white;
                border: 1px solid rgb(127,127,127);
                padding: 8px;
                font-size: 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgb(66,66,66);
            }
            QComboBox, QLineEdit {
                background-color: rgb(42,42,42);
                color: white;
                border: 1px solid rgb(127,127,127);
                padding: 5px;
            }
            QComboBox::drop-down {
                background-color: rgb(53,53,53);
            }
            QComboBox QAbstractItemView {
                background-color: rgb(42,42,42);
                color: white;
                selection-background-color: rgb(42,130,218);
            }
            QTextEdit {
                background-color: rgb(42,42,42);
                color: white;
                border: 1px solid rgb(127,127,127);
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
            QRadioButton {
                color: white;
                font-size: 11px;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
                border-radius: 6px;
                border: 1px solid rgb(127,127,127);
                background-color: rgb(42,42,42);
            }
            QRadioButton::indicator:checked {
                background-color: rgb(42,130,218);
                border: 1px solid rgb(42,130,218);
            }
        """)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ConfigurarCalendario()
    window.show()
    sys.exit(app.exec())