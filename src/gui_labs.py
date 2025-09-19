import sys
import os

from PyQt6 import QtCore, QtGui, QtWidgets

# ========= MANEJO ROBUSTO DE INTERFACES =========
INTERFACES_DISPONIBLES = False
ConfigurarCalendario = None
ConfigurarHorarios = None
VerResultados = None


def cargar_interfaces():
    """Cargar interfaces extra con manejo de errores detallado"""
    global INTERFACES_DISPONIBLES, ConfigurarCalendario, ConfigurarHorarios, VerResultados

    try:
        if not os.path.exists('modules/interfaces'):
            print("📁 Directorio 'interfaces' no encontrado - solo funcionalidad básica")
            return False

        from src.modules.interfaces import ConfigurarCalendario, ConfigurarHorarios, VerResultados
        INTERFACES_DISPONIBLES = True
        print("✅ Interfaces avanzadas cargadas correctamente")
        return True

    except ImportError as e:
        print(f"⚠️ Interfaces no disponibles: {e}")
        print("ℹ️ La funcionalidad principal sigue disponible")
        return False
    except Exception as e:
        print(f"❌ Error inesperado cargando interfaces: {e}")
        return False


# Cargar interfaces al inicio
cargar_interfaces()


class Ui_MainWindow(object):
    def __init__(self):
        self.path_alumnos = None
        self.path_asignaturas = None
        self.path_laboratorios = None
        self.path_profesores = None
        self.path_restricciones = None
        self._validation_logged = False

        # Referencias a ventanas de configuración
        self.ventana_calendario = None
        self.ventana_horarios = None
        self.ventana_resultados = None

        # Guardar referencia al MainWindow
        self.main_window = None

    def setupUi(self, MainWindow):
        # Guardar referencia
        self.main_window = MainWindow

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 750)
        MainWindow.setMinimumSize(QtCore.QSize(1100, 750))
        MainWindow.setMaximumSize(QtCore.QSize(1100, 750))
        MainWindow.setWindowTitle("OPTIM by SoftVier - ETSIDI")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # ========= MENÚ SUPERIOR (solo si hay interfaces enlazadas) =========
        if INTERFACES_DISPONIBLES:
            self.setup_menu_bar(MainWindow)

        # ========= TÍTULO PRINCIPAL =========
        self.titulo_principal = QtWidgets.QLabel(self.centralwidget)
        self.titulo_principal.setGeometry(QtCore.QRect(50, 10, 1000, 35))

        titulo_base = "OPTIM by SoftVier - ETSIDI"
        if not INTERFACES_DISPONIBLES:
            titulo_base += " (Modo Básico)"

        self.titulo_principal.setText(titulo_base)
        self.titulo_principal.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titulo_principal.setStyleSheet("""
            QLabel {
                color: rgb(42,130,218);
                font-size: 18px;
                font-weight: bold;
                background-color: rgb(35,35,35);
                border: 1px solid rgb(42,130,218);
                border-radius: 5px;
                padding: 8px;
            }
        """)

        # ========= SECCIONES PRINCIPALES =========
        self.setup_credenciales_section()
        self.setup_archivos_section()
        self.setup_configuracion_section()
        self.setup_opciones_section()

        # ========= BOTONES CONFIGURACIÓN (solo si están disponibles) =========
        if INTERFACES_DISPONIBLES:
            self.setup_botones_configuracion()

        # ========= ÁREA DE LOG =========
        self.setup_area_log()

        # ========= BOTONES PRINCIPALES =========
        self.setup_botones_principales()

        # ========= BARRA DE PROGRESO =========
        self.progress_bar = QtWidgets.QProgressBar(self.centralwidget)
        self.progress_bar.setGeometry(QtCore.QRect(50, 720, 1000, 20))
        self.progress_bar.setVisible(False)

        MainWindow.setCentralWidget(self.centralwidget)

        # ========= CONEXIONES =========
        self.connect_signals()

        # ========= TEMA OSCURO =========
        self.apply_dark_theme_tfg()

        # ========= LOG INICIAL =========
        self.mostrar_log_inicial()

    def setup_menu_bar(self, MainWindow):
        """Configurar barra de menú (solo si interfaces disponibles)"""
        menubar = MainWindow.menuBar()

        # Menú Configuración
        menu_config = menubar.addMenu('⚙️ Configuración')

        action_calendario = QtGui.QAction('📅 Configurar Calendario', MainWindow)
        action_calendario.triggered.connect(self.abrir_configurar_calendario)
        menu_config.addAction(action_calendario)

        action_horarios = QtGui.QAction('⏰ Configurar Horarios', MainWindow)
        action_horarios.triggered.connect(self.abrir_configurar_horarios)
        menu_config.addAction(action_horarios)

        menu_config.addSeparator()

        action_resultados = QtGui.QAction('📊 Ver Resultados', MainWindow)
        action_resultados.triggered.connect(self.abrir_ver_resultados)
        menu_config.addAction(action_resultados)

        # Menú Ayuda
        menu_ayuda = menubar.addMenu('❓ Ayuda')
        action_acerca = QtGui.QAction('ℹ️ Acerca de OPTIM', MainWindow)
        action_acerca.triggered.connect(self.mostrar_acerca_de)
        menu_ayuda.addAction(action_acerca)

    def setup_credenciales_section(self):
        """Sección credenciales UPM"""
        self.label_credenciales = QtWidgets.QLabel(self.centralwidget)
        self.label_credenciales.setGeometry(QtCore.QRect(50, 60, 500, 25))
        self.label_credenciales.setText("Credenciales UPM (OPCIONALES - solo para web scraping)")

        self.label_email = QtWidgets.QLabel(self.centralwidget)
        self.label_email.setGeometry(QtCore.QRect(50, 95, 100, 20))
        self.label_email.setText("Email UPM:")

        self.lineEdit_email = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_email.setGeometry(QtCore.QRect(160, 95, 370, 25))
        self.lineEdit_email.setPlaceholderText("usuario@upm.es")

        self.label_password = QtWidgets.QLabel(self.centralwidget)
        self.label_password.setGeometry(QtCore.QRect(50, 135, 100, 20))
        self.label_password.setText("Contraseña:")

        self.lineEdit_password = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_password.setGeometry(QtCore.QRect(160, 135, 370, 25))
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEdit_password.setPlaceholderText("Tu contraseña UPM")

    def setup_archivos_section(self):
        """Sección archivos de datos"""
        self.label_archivos = QtWidgets.QLabel(self.centralwidget)
        self.label_archivos.setGeometry(QtCore.QRect(50, 180, 500, 25))
        self.label_archivos.setText("Seleccione los archivos con los datos del sistema")

        # Archivos obligatorios
        archivos = [
            ("alumnos", "Lista de Alumnos por Asignatura (CSV/Excel)", 215),
            ("asignaturas", "Asignaturas y Laboratorios Compatibles (CSV/Excel)", 255),
            ("laboratorios", "Laboratorios Disponibles y Capacidades (CSV/Excel)", 295),
            ("profesores", "Profesores y Disponibilidad Horaria (CSV/Excel)", 335),
            ("restricciones", "Restricciones Adicionales (Opcional)", 375)
        ]

        for nombre, descripcion, y_pos in archivos:
            # Label
            label = QtWidgets.QLabel(self.centralwidget)
            label.setGeometry(QtCore.QRect(50, y_pos, 350, 20))
            label.setText(descripcion)
            setattr(self, f'label_{nombre}', label)

            # Botón
            btn = QtWidgets.QPushButton(self.centralwidget)
            btn.setGeometry(QtCore.QRect(450, y_pos, 80, 25))
            btn.setText("Examinar")
            setattr(self, f'btn_{nombre}', btn)

    def setup_configuracion_section(self):
        """Sección parámetros"""
        self.label_config = QtWidgets.QLabel(self.centralwidget)
        self.label_config.setGeometry(QtCore.QRect(50, 420, 500, 25))
        self.label_config.setText("Configuración de parámetros")

        # Semestre
        self.label_semestre = QtWidgets.QLabel(self.centralwidget)
        self.label_semestre.setGeometry(QtCore.QRect(50, 455, 80, 20))
        self.label_semestre.setText("Semestre:")

        self.combo_semestre = QtWidgets.QComboBox(self.centralwidget)
        self.combo_semestre.setGeometry(QtCore.QRect(140, 455, 60, 25))
        self.combo_semestre.addItems(["1", "2"])

        # Capacidad
        self.label_capacidad = QtWidgets.QLabel(self.centralwidget)
        self.label_capacidad.setGeometry(QtCore.QRect(250, 455, 130, 20))
        self.label_capacidad.setText("Capacidad máxima:")

        self.spin_capacidad = QtWidgets.QSpinBox(self.centralwidget)
        self.spin_capacidad.setGeometry(QtCore.QRect(390, 455, 60, 25))
        self.spin_capacidad.setMinimum(10)
        self.spin_capacidad.setMaximum(50)
        self.spin_capacidad.setValue(24)

    def setup_opciones_section(self):
        """Sección opciones"""
        self.label_opciones = QtWidgets.QLabel(self.centralwidget)
        self.label_opciones.setGeometry(QtCore.QRect(50, 500, 500, 25))
        self.label_opciones.setText("Opciones adicionales:")

        self.check_grupos_pares = QtWidgets.QCheckBox(self.centralwidget)
        self.check_grupos_pares.setGeometry(QtCore.QRect(50, 535, 500, 20))
        self.check_grupos_pares.setText("Priorizar grupos equilibrados")
        self.check_grupos_pares.setChecked(True)

        self.check_web_scraping = QtWidgets.QCheckBox(self.centralwidget)
        self.check_web_scraping.setGeometry(QtCore.QRect(50, 560, 500, 20))
        self.check_web_scraping.setText("Web scraping automático (requiere credenciales)")

        self.check_optimizacion = QtWidgets.QCheckBox(self.centralwidget)
        self.check_optimizacion.setGeometry(QtCore.QRect(50, 585, 500, 20))
        self.check_optimizacion.setText("Optimización avanzada (más lento)")

    def setup_botones_configuracion(self):
        """Botones configuración (solo si interfaces disponibles)"""
        self.label_config_avanzada = QtWidgets.QLabel(self.centralwidget)
        self.label_config_avanzada.setGeometry(QtCore.QRect(50, 615, 500, 20))
        self.label_config_avanzada.setText("Configuración Avanzada:")
        self.label_config_avanzada.setStyleSheet("color: rgb(42,130,218); font-weight: bold;")

        self.btn_config_calendario = QtWidgets.QPushButton(self.centralwidget)
        self.btn_config_calendario.setGeometry(QtCore.QRect(50, 640, 140, 30))
        self.btn_config_calendario.setText("📅 Calendario")

        self.btn_config_horarios = QtWidgets.QPushButton(self.centralwidget)
        self.btn_config_horarios.setGeometry(QtCore.QRect(200, 640, 140, 30))
        self.btn_config_horarios.setText("⏰ Horarios")

        self.btn_ver_resultados = QtWidgets.QPushButton(self.centralwidget)
        self.btn_ver_resultados.setGeometry(QtCore.QRect(350, 640, 140, 30))
        self.btn_ver_resultados.setText("📊 Resultados")

    def setup_area_log(self):
        """Área de log"""
        y_pos = 120 if INTERFACES_DISPONIBLES else 120
        height = 450 if INTERFACES_DISPONIBLES else 520

        self.info_area = QtWidgets.QTextEdit(self.centralwidget)
        self.info_area.setGeometry(QtCore.QRect(580, y_pos, 470, height))
        self.info_area.setReadOnly(True)

    def setup_botones_principales(self):
        """Botones principales"""
        y_pos = 580 if INTERFACES_DISPONIBLES else 650

        self.ejecutar = QtWidgets.QPushButton(self.centralwidget)
        self.ejecutar.setGeometry(QtCore.QRect(650, y_pos, 180, 40))
        self.ejecutar.setText("🚀 Generar Horarios")
        self.ejecutar.setEnabled(False)

        self.btn_limpiar_log = QtWidgets.QPushButton(self.centralwidget)
        self.btn_limpiar_log.setGeometry(QtCore.QRect(850, y_pos, 100, 40))
        self.btn_limpiar_log.setText("🧹 Limpiar")

        self.btn_salir = QtWidgets.QPushButton(self.centralwidget)
        self.btn_salir.setGeometry(QtCore.QRect(960, y_pos, 90, 40))
        self.btn_salir.setText("❌ Salir")

    def connect_signals(self):
        """Conectar señales"""
        # Archivos
        for nombre in ['alumnos', 'asignaturas', 'laboratorios', 'profesores', 'restricciones']:
            btn = getattr(self, f'btn_{nombre}')
            btn.clicked.connect(lambda checked, n=nombre: self.seleccionar_archivo(n))

        # Validación
        for nombre in ['alumnos', 'asignaturas', 'laboratorios', 'profesores']:
            btn = getattr(self, f'btn_{nombre}')
            btn.clicked.connect(self.validar_ejecucion)

        # Principal
        self.ejecutar.clicked.connect(self.iniciar_programacion)
        self.btn_limpiar_log.clicked.connect(self.limpiar_log)
        self.btn_salir.clicked.connect(self.salir_aplicacion)

        # Configuración (solo si disponible)
        if INTERFACES_DISPONIBLES:
            self.btn_config_calendario.clicked.connect(self.abrir_configurar_calendario)
            self.btn_config_horarios.clicked.connect(self.abrir_configurar_horarios)
            self.btn_ver_resultados.clicked.connect(self.abrir_ver_resultados)

    def mostrar_log_inicial(self):
        """Log inicial dinámico"""
        log_inicial = f"""OPTIM - Sistema de Programación de Laboratorios v1.0
Desarrollado por SoftVier para ETSIDI

MODO: {'Completo' if INTERFACES_DISPONIBLES else 'Básico'}
{'✅ Interfaces avanzadas disponibles' if INTERFACES_DISPONIBLES else '⚠️ Solo funcionalidad básica (interfaces no disponibles)'}

INSTRUCCIONES:
1. Credenciales UPM (OPCIONALES)
2. Selecciona los 4 archivos obligatorios
3. Configura parámetros
4. Haz clic en 'Generar Horarios'

ARCHIVOS OBLIGATORIOS:
• Alumnos: Lista con DNI, nombre, asignatura
• Asignaturas: Compatibilidad con laboratorios
• Laboratorios: Capacidad y equipamiento
• Profesores: Disponibilidad horaria

{'CONFIGURACIÓN AVANZADA DISPONIBLE:' if INTERFACES_DISPONIBLES else ''}
{'• Configurar Calendario: Períodos académicos' if INTERFACES_DISPONIBLES else ''}
{'• Configurar Horarios: Franjas horarias' if INTERFACES_DISPONIBLES else ''}
{'• Ver Resultados: Análisis detallado' if INTERFACES_DISPONIBLES else ''}

Sistema listo..."""

        self.info_area.setText(log_inicial)

    # ========= MÉTODOS PRINCIPALES =========

    def seleccionar_archivo(self, tipo):
        """Seleccionar archivo"""
        fname = QtWidgets.QFileDialog.getOpenFileName(
            None, f'Seleccionar archivo de {tipo}', '', 'Archivos (*.csv *.xlsx *.xls)'
        )

        if fname[0]:
            setattr(self, f'path_{tipo}', fname[0])
            btn = getattr(self, f'btn_{tipo}')
            btn.setText("✓ Cargado")
            btn.setStyleSheet("background-color: #2ecc71; color: white;")

            filename = fname[0].split('/')[-1].split('\\')[-1]
            self.log_info(f"✓ {tipo.capitalize()} cargado: {filename}")

    def validar_ejecucion(self):
        """Validar archivos obligatorios"""
        archivos_ok = all([
            self.path_alumnos, self.path_asignaturas,
            self.path_laboratorios, self.path_profesores
        ])

        self.ejecutar.setEnabled(archivos_ok)

        if archivos_ok and not self._validation_logged:
            self.log_info("✅ Todos los archivos obligatorios cargados")
            self._validation_logged = True

    def iniciar_programacion(self):
        """Iniciar programación"""
        self.ejecutar.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_info("\n🚀 INICIANDO GENERACIÓN DE HORARIOS")

        # Simular proceso
        import time
        pasos = [
            (20, "📂 Cargando archivos..."),
            (40, "⚖️ Generando grupos equilibrados..."),
            (60, "🏢 Asignando laboratorios..."),
            (80, "📅 Resolviendo conflictos..."),
            (100, "💾 Exportando resultados...")
        ]

        for progreso, mensaje in pasos:
            self.log_info(mensaje)
            self.progress_bar.setValue(progreso)
            time.sleep(0.5)
            QtCore.QCoreApplication.processEvents()

        self.log_info("✅ ¡Horarios generados exitosamente!")
        self.progress_bar.setVisible(False)
        self.ejecutar.setEnabled(True)

    # ========= MÉTODOS DE INTERFACES (✅ CORREGIDOS) =========

    def abrir_configurar_calendario(self):
        """Abrir configuración calendario"""
        if not INTERFACES_DISPONIBLES:
            self.mostrar_mensaje("⚠️ No Disponible", "Interfaces avanzadas no cargadas")
            return

        try:
            if self.ventana_calendario is None:
                # ✅ SOLUCIÓN: Pasar self.main_window en lugar de self
                self.ventana_calendario = ConfigurarCalendario(parent=self.main_window)
            self.ventana_calendario.show()
            self.ventana_calendario.raise_()
            self.ventana_calendario.activateWindow()
            self.log_info("📅 Abriendo configuración de calendario...")
        except Exception as e:
            self.mostrar_mensaje("❌ Error", f"Error: {str(e)}")

    def abrir_configurar_horarios(self):
        """Abrir configuración horarios"""
        if not INTERFACES_DISPONIBLES:
            self.mostrar_mensaje("⚠️ No Disponible", "Interfaces avanzadas no cargadas")
            return

        try:
            if self.ventana_horarios is None:
                # ✅ SOLUCIÓN: Pasar self.main_window en lugar de self
                self.ventana_horarios = ConfigurarHorarios(parent=self.main_window)
            self.ventana_horarios.show()
            self.ventana_horarios.raise_()
            self.ventana_horarios.activateWindow()
            self.log_info("⏰ Abriendo configuración de horarios...")
        except Exception as e:
            self.mostrar_mensaje("❌ Error", f"Error: {str(e)}")

    def abrir_ver_resultados(self):
        """Abrir resultados"""
        if not INTERFACES_DISPONIBLES:
            self.mostrar_mensaje("⚠️ No Disponible", "Interfaces avanzadas no cargadas")
            return

        try:
            if self.ventana_resultados is None:
                # ✅ SOLUCIÓN: Pasar self.main_window en lugar de self
                self.ventana_resultados = VerResultados(parent=self.main_window)
            self.ventana_resultados.show()
            self.ventana_resultados.raise_()
            self.ventana_resultados.activateWindow()
            self.log_info("📊 Abriendo visualización de resultados...")
        except Exception as e:
            self.mostrar_mensaje("❌ Error", f"Error: {str(e)}")

    # ========= MÉTODOS AUXILIARES =========

    def log_info(self, mensaje):
        """Log con timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_area.append(f"[{timestamp}] {mensaje}")
        scrollbar = self.info_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def limpiar_log(self):
        """Limpiar log"""
        self.info_area.clear()
        self.mostrar_log_inicial()

    def mostrar_acerca_de(self):
        """Acerca de"""
        mensaje = f"""OPTIM by SoftVier v1.0

Modo: {'Completo' if INTERFACES_DISPONIBLES else 'Básico'}
Stack: Python + PyQt6 + Pandas

Desarrollado para ETSIDI (2025)"""

        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Acerca de OPTIM")
        msg_box.setText(mensaje)
        msg_box.exec()

    def mostrar_mensaje(self, titulo, mensaje):
        """Mostrar mensaje"""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.exec()

    def salir_aplicacion(self):
        """Salir"""
        reply = QtWidgets.QMessageBox.question(
            None, 'Salir', '¿Salir de OPTIM?',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            QtWidgets.QApplication.quit()

    def apply_dark_theme_tfg(self):
        """Tema oscuro"""
        self.centralwidget.setStyleSheet("""
            QWidget {
                background-color: rgb(53,53,53);
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel { color: white; font-size: 13px; }
            QPushButton {
                background-color: rgb(53,53,53);
                color: white;
                border: 1px solid rgb(127,127,127);
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: rgb(66,66,66); }
            QPushButton:disabled { background-color: rgb(60,60,60); color: rgb(140,140,140); }
            QLineEdit, QComboBox, QSpinBox {
                background-color: rgb(42,42,42);
                color: white;
                border: 1px solid rgb(127,127,127);
                padding: 5px;
            }
            QTextEdit {
                background-color: rgb(42,42,42);
                color: white;
                border: 1px solid rgb(127,127,127);
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QCheckBox { color: white; font-size: 13px; }
            QProgressBar {
                background-color: rgb(42,42,42);
                border: 1px solid rgb(127,127,127);
                text-align: center;
                color: white;
            }
            QProgressBar::chunk { background-color: rgb(42,130,218); }
            QMenuBar {
                background-color: rgb(53,53,53);
                color: white;
                border-bottom: 1px solid rgb(127,127,127);
            }
            QMenuBar::item { background-color: transparent; padding: 8px 12px; }
            QMenuBar::item:selected { background-color: rgb(42,130,218); }
            QMenu {
                background-color: rgb(42,42,42);
                color: white;
                border: 1px solid rgb(127,127,127);
            }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background-color: rgb(42,130,218); }
        """)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("OPTIM by SoftVier - ETSIDI")
    app.setStyle('Fusion')

    # Paleta oscura
    paleta = QtGui.QPalette()
    paleta.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
    paleta.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(42, 42, 42))
    paleta.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(66, 66, 66))
    paleta.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
    paleta.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
    paleta.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(255, 255, 255))
    app.setPalette(paleta)

    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())