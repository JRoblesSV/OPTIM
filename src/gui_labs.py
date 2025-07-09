#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar GUI - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

FUNCIONALIDADES IMPLEMENTADAS:
1. Interfaz principal unificada del sistema OPTIM
2. Panel de estado visual con indicadores de configuración
3. Gestión centralizada de todos los módulos del sistema
4. Resumen automático de configuración actual
5. Sistema de logging de actividad con timestamps
6. Navegación inteligente entre ventanas de configuración
7. Guardado y carga de configuración global en JSON
8. Validación de completitud antes de ejecutar organización
9. Sistema de reset selectivo y completo
10. Integración de todos los subsistemas con comunicación bidireccional

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer


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


class OptimLabsGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_file = "configuracion_labs.json"

        # Ventanas de configuración (se abren bajo demanda)
        self.ventana_horarios = None
        self.ventana_calendario = None
        self.ventana_alumnos = None
        self.ventana_profesores = None
        self.ventana_aulas = None
        self.ventana_resultados = None

        self.setupUi()
        self.conectar_signals()

        # Carga configuracion antes del UI
        self.configuracion = self.cargar_configuracion()

        self.actualizar_estado_visual()
        self.log_mensaje("🔄 OPTIM Labs iniciado correctamente", "info")

    def setupUi(self):
        """Configurar interfaz principal"""
        self.setObjectName("OptimLabsGUI")
        self.setMinimumSize(QtCore.QSize(1200, 940))
        window_width = 1200
        window_height = 920
        center_window_on_screen_immediate(self, window_width, window_height)

        self.setWindowTitle("OPTIM by SoftVier - ETSIDI")

        # Widget central
        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # Configurar componentes
        self.setup_titulo()
        self.setup_panel_estado()
        self.setup_botones_configuracion()
        self.setup_resumen_configuracion()
        self.setup_botones_principales()
        self.setup_botones_secundarios()
        self.setup_area_log()

        # Progres Bar para organizados de laboratorios
        self.setup_progress_bar()

        # Aplicar tema oscuro del TFG
        self.aplicar_tema_oscuro()

    def setup_titulo(self):
        """Título principal con información del proyecto"""
        self.titulo = QtWidgets.QLabel(self.centralwidget)
        self.titulo.setGeometry(QtCore.QRect(50, 10, 1100, 45))
        self.titulo.setText("🎯 OPTIM by SoftVier - Sistema de Programación de Laboratorios ETSIDI")
        self.titulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titulo.setStyleSheet("""
            QLabel {
                color: rgb(42,130,218);
                font-size: 16px;
                font-weight: bold;
                background-color: rgb(35,35,35);
                border: 2px solid rgb(42,130,218);
                border-radius: 8px;
                padding: 10px;
            }
        """)

    def setup_panel_estado(self):
        """Panel de estado general con indicadores visuales"""
        # Frame contenedor
        self.frame_estado = QtWidgets.QFrame(self.centralwidget)
        self.frame_estado.setGeometry(QtCore.QRect(50, 70, 1100, 80))
        self.frame_estado.setFrameStyle(QtWidgets.QFrame.Shape.Box)

        # Labels de estado
        estados = [
            ("asignaturas", "📚 Asignaturas", 20),
            ("profesores", "👨‍🏫 Profesores", 180),
            ("alumnos", "👥 Alumnos", 340),
            ("aulas", "🏢 Aulas", 500),
            ("calendario", "📆 Calendario", 660),
            ("horarios", "📅 Horarios", 820),
            ("global", "🎯 Estado", 980)
        ]

        self.labels_estado = {}
        for key, texto, x_pos in estados:
            # Label título
            label_titulo = QtWidgets.QLabel(self.frame_estado)
            label_titulo.setGeometry(QtCore.QRect(x_pos, 10, 150, 20))
            label_titulo.setText(texto)
            label_titulo.setStyleSheet("font-weight: bold; font-size: 12px;")

            # Label estado
            label_estado = QtWidgets.QLabel(self.frame_estado)
            label_estado.setGeometry(QtCore.QRect(x_pos, 35, 150, 35))
            label_estado.setText("❌ Sin configurar")
            label_estado.setStyleSheet("font-size: 11px; color: rgb(220,220,220);")

            self.labels_estado[key] = label_estado

    def setup_botones_configuracion(self):
        """Botones para acceder a cada configuración"""
        # Frame contenedor
        self.frame_botones = QtWidgets.QFrame(self.centralwidget)
        self.frame_botones.setGeometry(QtCore.QRect(50, 170, 1100, 180))

        # Primera fila de botones
        botones_fila1 = [
            ("btn_cursos", "🎓 CURSOS\nGrados y titulaciones", 50, 20),
            ("btn_asignaturas", "📋 ASIGNATURAS\nLímites y grupos", 300, 20),
            ("btn_profesores", "👨‍🏫 PROFESORES\nDisponibilidad horaria", 550, 20),
            ("btn_alumnos", "👥 ALUMNOS\nMatrículas por asignatura", 800, 20)
        ]

        # Segunda fila de botones
        botones_fila2 = [
            ("btn_calendario", "📅 CALENDARIO\nConfigurar semestre", 50, 100),
            ("btn_horarios", "⏰ HORARIOS\nFranjas por asignatura", 300, 100),
            ("btn_aulas", "🏢 AULAS\nLaboratorios disponibles", 550, 100),
            ("btn_parametros", "🎯 PARÁMETROS\nPesos optimización", 800, 100)
        ]

        self.botones_config = {}
        for botones_fila in [botones_fila1, botones_fila2]:
            for key, texto, x, y in botones_fila:
                btn = QtWidgets.QPushButton(self.frame_botones)
                btn.setGeometry(QtCore.QRect(x, y, 220, 65))
                btn.setText(texto)
                btn.setStyleSheet(self.estilo_boton_configuracion())
                self.botones_config[key] = btn

    def setup_resumen_configuracion(self):
        """Área de resumen de configuración actual"""
        # Label título
        self.label_resumen_titulo = QtWidgets.QLabel(self.centralwidget)
        self.label_resumen_titulo.setGeometry(QtCore.QRect(50, 370, 1100, 25))
        self.label_resumen_titulo.setText("📋 RESUMEN DE CONFIGURACIÓN ACTUAL")
        self.label_resumen_titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: rgb(42,130,218);")

        # Área de texto para resumen
        self.texto_resumen = QtWidgets.QTextEdit(self.centralwidget)
        self.texto_resumen.setGeometry(QtCore.QRect(50, 400, 1100, 120))
        self.texto_resumen.setReadOnly(True)
        self.texto_resumen.setStyleSheet("""
            QTextEdit {
                background-color: rgb(42,42,42);
                color: rgb(220,220,220);
                border: 1px solid rgb(127,127,127);
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)

    def setup_botones_principales(self):
        """Botones principales de acción"""
        # Frame contenedor
        self.frame_acciones = QtWidgets.QFrame(self.centralwidget)
        self.frame_acciones.setGeometry(QtCore.QRect(50, 540, 1100, 80))

        # Botones principales
        botones_principales = [
            ("btn_organizar", "✨ ORGANIZAR\nLABORATORIOS", 50, 15, 220, True),
            ("btn_guardar", "💾 GUARDAR\nCONFIGURACIÓN", 300, 15, 220, False),
            ("btn_cargar", "📂 CARGAR\nCONFIGURACIÓN", 550, 15, 220, False),
            ("btn_reset", "🔄 RESET\nTODO", 800, 15, 220, False),
        ]

        self.botones_principales = {}
        for key, texto, x, y, width, es_principal in botones_principales:
            btn = QtWidgets.QPushButton(self.frame_acciones)
            btn.setGeometry(QtCore.QRect(x, y, width, 50))
            btn.setText(texto)

            if es_principal:
                btn.setStyleSheet(self.estilo_boton_principal())
                btn.setEnabled(False)  # Deshabilitado hasta tener configuración completa
            else:
                btn.setStyleSheet(self.estilo_boton_secundario())

            self.botones_principales[key] = btn

    def setup_botones_secundarios(self):
        """Botones secundarios en la parte inferior derecha"""
        # Frame contenedor
        self.frame_secundarios = QtWidgets.QFrame(self.centralwidget)
        self.frame_secundarios.setGeometry(QtCore.QRect(50, 840, 1100, 80))

        # Botones alineados a la derecha
        botones_secundarios = [
            ("btn_resultados", "📊 RESULTADOS\nVer última ejecución", 550, 15, 220),
            ("btn_ayuda", "❓ AYUDA\nY SOPORTE", 800, 15, 220)
        ]

        self.botones_secundarios = {}
        for key, texto, x, y, width in botones_secundarios:
            btn = QtWidgets.QPushButton(self.frame_secundarios)
            btn.setGeometry(QtCore.QRect(x, y, width, 50))
            btn.setText(texto)
            btn.setStyleSheet(self.estilo_boton_secundario())
            self.botones_secundarios[key] = btn


    def setup_area_log(self):
        """Área de log de actividad"""
        # Label título
        self.label_log_titulo = QtWidgets.QLabel(self.centralwidget)
        self.label_log_titulo.setGeometry(QtCore.QRect(50, 640, 1100, 25))
        self.label_log_titulo.setText("📝 LOG DE ACTIVIDAD")
        self.label_log_titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: rgb(42,130,218);")

        # Área de texto para log
        self.texto_log = QtWidgets.QTextEdit(self.centralwidget)
        self.texto_log.setGeometry(QtCore.QRect(50, 670, 1100, 150))
        self.texto_log.setReadOnly(True)
        self.texto_log.setStyleSheet("""
            QTextEdit {
                background-color: rgb(35,35,35);
                color: rgb(200,200,200);
                border: 1px solid rgb(127,127,127);
                font-family: 'Consolas', monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)

    def setup_progress_bar(self):
        """Configurar barra de progreso para organización"""
        self.progress_bar = QtWidgets.QProgressBar(self.centralwidget)
        self.progress_bar.setGeometry(QtCore.QRect(50, 830, 1100, 25))
        self.progress_bar.setVisible(False)  # Oculto inicialmente
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgb(42,42,42);
                border: 1px solid rgb(127,127,127);
                border-radius: 5px;
                text-align: center;
                color: white;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: rgb(42,130,218);
                border-radius: 3px;
            }
        """)

    def conectar_signals(self):
        """Conectar señales de botones"""
        # Botones de configuración
        self.botones_config["btn_cursos"].clicked.connect(self.abrir_configurar_cursos)
        self.botones_config["btn_asignaturas"].clicked.connect(self.abrir_configurar_asignaturas)
        self.botones_config["btn_profesores"].clicked.connect(self.abrir_configurar_profesores)
        self.botones_config["btn_alumnos"].clicked.connect(self.abrir_configurar_alumnos)

        self.botones_config["btn_calendario"].clicked.connect(self.abrir_configurar_calendario)
        self.botones_config["btn_horarios"].clicked.connect(self.abrir_configurar_horarios)
        self.botones_config["btn_aulas"].clicked.connect(self.abrir_configurar_aulas)
        self.botones_config["btn_parametros"].clicked.connect(self.abrir_configurar_parametros)

        # Botones principales
        self.botones_principales["btn_organizar"].clicked.connect(self.iniciar_organizacion)
        self.botones_principales["btn_guardar"].clicked.connect(self.guardar_configuracion)
        self.botones_principales["btn_cargar"].clicked.connect(self.cargar_configuracion_archivo)
        self.botones_principales["btn_reset"].clicked.connect(self.reset_configuracion)

        # Botones secundarios
        self.botones_secundarios["btn_resultados"].clicked.connect(self.abrir_ver_resultados)
        self.botones_secundarios["btn_ayuda"].clicked.connect(self.mostrar_ayuda)

    def cargar_configuracion(self):
        """Cargar configuración desde archivo JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.log_mensaje(f"✅ Configuración cargada desde {self.config_file}", "info")
                return config
            except Exception as e:
                self.log_mensaje(f"❌ Error cargando configuración: {e}", "error")

        # Configuración por defecto ACTUALIZADA CON RESULTADOS
        return {
            "metadata": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "semestre_actual": 1
            },
            "configuracion": {
                "horarios": {"configurado": False, "datos": {}, "archivo": ""},
                "calendario": {"configurado": False, "datos": {}, "semanas_total": 0},
                "aulas": {
                    "configurado": False,
                    "datos": {},
                    "total_aulas": 0,
                    "fecha_actualizacion": None
                },
                "profesores": {"configurado": False, "datos": {}, "total": 0},
                "alumnos": {"configurado": False, "datos": {}, "total": 0},
                "asignaturas": {"configurado": False, "datos": {}, "total": 0},
                "cursos": {"configurado": False, "datos": {}, "total": 0}
            },
            "parametros_organizacion": {
                "configurado": False,
                "fecha_actualizacion": None,
                "parametros_booleanos": {
                    "preferir_grupos_pares": True,
                    "priorizar_horas_tempranas": True,
                    "aplicar_prioridad_doble_grado": True,
                    "permitir_intercambio_automatico": True,
                    "aplicar_restricciones_duras": True,
                    "generar_reportes_detallados": True,
                    "optimizar_utilizacion_aulas": True,
                    "equilibrar_carga_profesores": True
                },
                "pesos_optimizacion": {
                    "peso_equilibrio_grupos": 25,
                    "peso_grupos_pares": 20,
                    "peso_horas_tempranas": 40,
                    "peso_doble_grado": 30,
                    "peso_conflictos_alumnos": 15,
                    "peso_utilizacion_aulas": 25,
                    "peso_distribucion_profesores": 20,
                    "peso_compatibilidad_asignaturas": 30
                },
                "configuraciones_adicionales": {
                    "diferencia_maxima_grupos": 1,
                    "utilizacion_aula_optima": 85,
                    "max_horas_profesor_dia": 6,
                    "min_descanso_entre_clases": 30,
                    "preferencia_aulas_especificas": 70,
                    "factor_penalizacion_conflictos": 100
                }
            },
            # Añadir seccion de resultados
            "resultados_organizacion": {
                "datos_disponibles": False,
                "fecha_actualizacion": None,
                "ultima_ejecucion": {},
                "resumen": {
                    "total_grupos": 0,
                    "grupos_asignados": 0,
                    "conflictos_detectados": 0,
                    "porcentaje_exito": 0
                },
                "historial_ejecuciones": []
            }
        }

    def actualizar_estado_visual(self):
        """Actualizar indicadores visuales de configuración"""
        configuraciones = {
            "cursos": self.configuracion["configuracion"]["cursos"],
            "asignaturas": self.configuracion["configuracion"]["asignaturas"],
            "profesores": self.configuracion["configuracion"]["profesores"],
            "alumnos": self.configuracion["configuracion"]["alumnos"],
            "calendario": self.configuracion["configuracion"]["calendario"],
            "horarios": self.configuracion["configuracion"]["horarios"],
            "aulas": self.configuracion["configuracion"]["aulas"],
            "parametros": self.configuracion["parametros_organizacion"],
            "resultados": self.configuracion.get("resultados_organizacion", {})
        }

        # Actualizar cada label de estado
        for key, config in configuraciones.items():
            if key in self.labels_estado:
                if key == "resultados":
                    # Caso especial para resultados
                    if config.get("datos_disponibles", False):
                        resumen = config.get("resumen", {})
                        exito = resumen.get("porcentaje_exito", 0)
                        self.labels_estado[key].setText(f"✅ {exito:.0f}% éxito\nÚltima organización")
                        self.labels_estado[key].setStyleSheet("font-size: 11px; color: rgb(100,200,100);")
                    else:
                        self.labels_estado[key].setText("❌ Sin ejecutar\nEjecutar organización")
                        self.labels_estado[key].setStyleSheet("font-size: 11px; color: rgb(200,150,0);")

                elif config.get("configurado", False):
                    if key == "parametros":
                        # Caso especial para parámetros
                        total_parametros = (
                                len(config.get("parametros_booleanos", {})) +
                                len(config.get("pesos_optimizacion", {})) +
                                len(config.get("configuraciones_adicionales", {}))
                        )
                        self.labels_estado[key].setText(f"✅ {total_parametros} parámetros\nconfigurados")
                    else:
                        # Otros casos
                        total = config.get("total", 0) or config.get("total_aulas", 0) or config.get("semanas_total", 0)
                        self.labels_estado[key].setText(f"✅ {total} elementos\nconfigurados")

                    self.labels_estado[key].setStyleSheet("font-size: 11px; color: rgb(100,200,100);")
                else:
                    self.labels_estado[key].setText("❌ Sin configurar")
                    self.labels_estado[key].setStyleSheet("font-size: 11px; color: rgb(220,220,220);")

        # Actualizar resumen
        self.actualizar_resumen_configuracion()

        # Verificar si se puede organizar
        configuraciones_obligatorias = ["cursos", "asignaturas", "profesores", "alumnos", "horarios", "aulas",
                                        "parametros"]
        todo_configurado = all(configuraciones[key].get("configurado", False) for key in configuraciones_obligatorias)

        # Habilitar/deshabilitar botón principal
        self.botones_principales["btn_organizar"].setEnabled(todo_configurado)

        # Manejo boton resultados
        hay_resultados = configuraciones["resultados"].get("datos_disponibles", False)

        if "btn_resultados" in self.botones_secundarios:
            # Siempre habilitar el botón de resultados
            self.botones_secundarios["btn_resultados"].setEnabled(True)

            # Cambiar texto según disponibilidad
            if hay_resultados:
                self.botones_secundarios["btn_resultados"].setText("📊 RESULTADOS\nVer última ejecución")
                self.botones_secundarios["btn_resultados"].setStyleSheet("""
                    QPushButton {
                        background-color: rgb(30,150,30);
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        font-size: 11px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: rgb(40,160,40);
                    }
                """)
            else:
                self.botones_secundarios["btn_resultados"].setText("📊 RESULTADOS\nEjecutar organización")
                self.botones_secundarios["btn_resultados"].setStyleSheet("""
                    QPushButton {
                        background-color: rgb(150,100,0);
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        font-size: 11px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: rgb(160,110,0);
                    }
                """)

        if todo_configurado:
            self.log_mensaje("🎯 Sistema listo para organizar laboratorios", "success")
        else:
            faltantes = [key for key in configuraciones_obligatorias if
                         not configuraciones[key].get("configurado", False)]
            self.log_mensaje(f"⚠️ Faltan configurar: {', '.join(faltantes)}", "warning")

    def actualizar_resumen_configuracion(self):
        """Actualizar texto de resumen de configuración"""
        config = self.configuracion["configuracion"]
        parametros = self.configuracion["parametros_organizacion"]
        resultados = self.configuracion.get("resultados_organizacion", {})

        resumen = "📋 CONFIGURACIÓN ACTUAL DEL SISTEMA\n"
        resumen += "=" * 80 + "\n\n"

        # Configuraciones básicas
        resumen += "📚 DATOS ACADÉMICOS:\n"
        resumen += f"  • Cursos: {config['cursos'].get('total', 0)} configurados\n"
        resumen += f"  • Asignaturas: {config['asignaturas'].get('total', 0)} configuradas\n"
        resumen += f"  • Profesores: {config['profesores'].get('total', 0)} configurados\n"
        resumen += f"  • Alumnos: {config['alumnos'].get('total', 0)} configurados\n"

        resumen += "\n🏢 INFRAESTRUCTURA:\n"
        resumen += f"  • Aulas/Laboratorios: {config['aulas'].get('total_aulas', 0)} configuradas\n"
        resumen += f"  • Horarios: {'✅ Configurado' if config['horarios'].get('configurado') else '❌ Sin configurar'}\n"
        resumen += f"  • Calendario: {'✅ Configurado' if config['calendario'].get('configurado') else '❌ Sin configurar'}\n"

        # Parámetros de optimización
        resumen += "\n🎯 PARÁMETROS DE OPTIMIZACIÓN:\n"
        if parametros.get("configurado", False):
            resumen += f"  • Parámetros booleanos: {len(parametros.get('parametros_booleanos', {}))} configurados\n"
            resumen += f"  • Pesos de optimización: {len(parametros.get('pesos_optimizacion', {}))} configurados\n"
            resumen += f"  • Configuraciones adicionales: {len(parametros.get('configuraciones_adicionales', {}))} configuradas\n"

            # Mostrar algunos parámetros clave
            pesos = parametros.get("pesos_optimizacion", {})
            if pesos:
                resumen += f"  • Peso horas tempranas: {pesos.get('peso_horas_tempranas', 0)}%\n"
                resumen += f"  • Peso equilibrio grupos: {pesos.get('peso_equilibrio_grupos', 0)}%\n"
        else:
            resumen += "  • ❌ Parámetros sin configurar\n"

        # Seccion de resultados
        resumen += "\n📊 RESULTADOS DE ORGANIZACIÓN:\n"
        if resultados.get("datos_disponibles", False):
            resumen_datos = resultados.get("resumen", {})
            fecha_actualizacion = resultados.get("fecha_actualizacion", "")

            resumen += f"  • ✅ Datos disponibles\n"
            resumen += f"  • Total grupos: {resumen_datos.get('total_grupos', 0)}\n"
            resumen += f"  • Grupos asignados: {resumen_datos.get('grupos_asignados', 0)}\n"
            resumen += f"  • Éxito: {resumen_datos.get('porcentaje_exito', 0):.1f}%\n"
            resumen += f"  • Conflictos: {resumen_datos.get('conflictos_detectados', 0)}\n"

            if fecha_actualizacion:
                try:
                    fecha_obj = datetime.fromisoformat(fecha_actualizacion.replace('Z', '+00:00'))
                    fecha_formateada = fecha_obj.strftime('%d/%m/%Y %H:%M')
                    resumen += f"  • Última ejecución: {fecha_formateada}\n"
                except:
                    resumen += f"  • Última ejecución: {fecha_actualizacion[:19]}\n"
        else:
            resumen += "  • ❌ Sin resultados disponibles\n"

        resumen += f"\n🕒 Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"

        self.texto_resumen.setPlainText(resumen)

    def get_estado_cursos(self):
        """Obtener estado de configuración de cursos"""
        cursos = self.configuracion["configuracion"].get("cursos", {})
        if cursos.get("configurado", False) and cursos.get("total", 0) > 0:
            return ("✅", f"{cursos['total']} cursos", "rgb(100,255,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def get_estado_horarios(self):
        """Obtener estado de configuración de horarios"""
        horarios = self.configuracion["configuracion"]["horarios"]
        if horarios["configurado"] and horarios.get("datos"):
            total_asig = horarios.get("total_asignaturas", 0)
            total_franjas = horarios.get("total_franjas", 0)
            semestre = horarios.get("semestre_actual", "?")

            if total_asig > 0:
                return ("✅", f"S{semestre}: {total_asig} asig, {total_franjas} franjas", "rgb(100,255,100)")
            else:
                return ("⚠️", "Configurado sin datos", "rgb(255,200,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def get_estado_calendario(self):
        """Obtener estado de configuración de calendario"""
        calendario = self.configuracion["configuracion"]["calendario"]
        if calendario["configurado"]:
            dias_1 = calendario.get("dias_semestre_1", 0)
            dias_2 = calendario.get("dias_semestre_2", 0)
            total_dias = dias_1 + dias_2

            if total_dias > 0:
                return ("✅", f"{total_dias} días ({dias_1}+{dias_2})", "rgb(100,255,100)")
            else:
                return ("⚠️", "Configurado sin días", "rgb(255,200,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def get_estado_aulas(self):
        """Obtener estado de configuración de aulas"""
        aulas = self.configuracion["configuracion"]["aulas"]
        if aulas["configurado"] and aulas.get("total_aulas", 0) > 0:
            return ("✅", f"{aulas['total_aulas']} aulas", "rgb(100,255,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def get_estado_profesores(self):
        """Obtener estado de configuración de profesores"""
        profesores = self.configuracion["configuracion"]["profesores"]
        if profesores["configurado"] and profesores["total"] > 0:
            return ("✅", f"{profesores['total']} profesores", "rgb(100,255,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def get_estado_alumnos(self):
        """Obtener estado de configuración de alumnos"""
        alumnos = self.configuracion["configuracion"]["alumnos"]
        if alumnos["configurado"] and alumnos["total"] > 0:
            return ("✅", f"{alumnos['total']} alumnos", "rgb(100,255,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def get_estado_asignaturas(self):
        """Obtener estado de configuración de asignaturas"""
        asignaturas = self.configuracion["configuracion"]["asignaturas"]
        if asignaturas["configurado"] and asignaturas.get("total", 0) > 0:
            return ("✅", f"{asignaturas['total']} asignaturas", "rgb(100,255,100)")
        return ("❌", "Sin configurar", "rgb(255,100,100)")

    def actualizar_resumen(self):
        """Actualizar área de resumen"""
        config = self.configuracion["configuracion"]
        resumen = []

        # Sección horarios mejorado
        if config["horarios"]["configurado"]:
            horarios_info = config["horarios"]
            total_asig = horarios_info.get("total_asignaturas", 0)
            total_franjas = horarios_info.get("total_franjas", 0)
            semestre = horarios_info.get("semestre_actual", "?")
            timestamp = horarios_info.get("timestamp", "")

            if timestamp:
                fecha = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
            else:
                fecha = "Fecha desconocida"

            resumen.append(f"✅ HORARIOS: Semestre {semestre} - {total_asig} asignaturas, {total_franjas} franjas")
            resumen.append(f"   📅 Última actualización: {fecha}")

            # Mostrar detalles por semestre si hay datos
            datos_horarios = horarios_info.get("datos", {})
            if datos_horarios:
                for semestre_num, asignaturas in datos_horarios.items():
                    if asignaturas:  # Solo mostrar semestres con datos
                        franjas_sem = sum(
                            sum(len(horarios_dia) for horarios_dia in asig_data.get("horarios", {}).values())
                            for asig_data in asignaturas.values()
                        )
                        resumen.append(
                            f"   • Semestre {semestre_num}: {len(asignaturas)} asignaturas, {franjas_sem} franjas")
        else:
            resumen.append("❌ HORARIOS: Sin configurar")

        resumen.append("")

        # Resto de configuraciones (igual que antes)
        secciones = [
            ("CALENDARIO", "calendario"),
            ("AULAS", "aulas"),
            ("PROFESORES", "profesores"),
            ("ALUMNOS", "alumnos")
        ]

        for nombre, key in secciones:
            if config[key]["configurado"]:
                if key == "aulas":
                    total = config[key].get("total_aulas", 0)
                else:
                    total = config[key].get("total", 0)
                resumen.append(f"✅ {nombre}: {total} elementos configurados")
            else:
                resumen.append(f"❌ {nombre}: Sin configurar")

        self.texto_resumen.setPlainText("\n".join(resumen))

    def setup_estado_visual(self):
        """Configurar indicadores visuales de estado"""
        # Frame contenedor
        self.frame_estado = QtWidgets.QFrame(self.centralwidget)
        self.frame_estado.setGeometry(QtCore.QRect(50, 80, 1100, 80))

        # Títulos y estados
        configuraciones = [
            ("cursos", "CURSOS", 50),
            ("asignaturas", "ASIGNATURAS", 200),
            ("profesores", "PROFESORES", 350),
            ("alumnos", "ALUMNOS", 500),
            ("calendario", "CALENDARIO", 650),
            ("horarios", "HORARIOS", 800),
            ("aulas", "AULAS", 950),
            ("parametros", "PARÁMETROS", 1100),
            ("resultados", "RESULTADOS", 1250)  # ← AÑADIR RESULTADOS
        ]

        self.labels_estado = {}
        for key, texto, x_pos in configuraciones:
            # Label título
            label_titulo = QtWidgets.QLabel(self.frame_estado)
            label_titulo.setGeometry(QtCore.QRect(x_pos, 10, 150, 20))
            label_titulo.setText(texto)
            label_titulo.setStyleSheet("font-weight: bold; font-size: 12px;")

            # Label estado
            label_estado = QtWidgets.QLabel(self.frame_estado)
            label_estado.setGeometry(QtCore.QRect(x_pos, 35, 150, 35))
            label_estado.setText("❌ Sin configurar")
            label_estado.setStyleSheet("font-size: 11px; color: rgb(220,220,220);")

            self.labels_estado[key] = label_estado

    def log_mensaje(self, mensaje, tipo="info"):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
        icono = iconos.get(tipo, "ℹ️")

        mensaje_completo = f"{timestamp} - {icono} {mensaje}"
        self.texto_log.append(mensaje_completo)

        # Auto-scroll al final
        scrollbar = self.texto_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ========= ACTUALIZACION DE CONFIGURACION =========
    def actualizar_configuracion_cursos(self, cursos_data):
        """Actualizar configuración de cursos en el sistema principal"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(cursos_data, dict) and "metadata" in cursos_data:
                metadata = cursos_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    datos_cursos = cursos_data.get("cursos", {})
                    self.log_mensaje("🔄 Restaurando configuración original de cursos", "warning")
                else:
                    # Datos normales con metadata
                    datos_cursos = cursos_data.get("cursos", cursos_data)
            else:
                # CASO NORMAL: Datos directos de cursos SIN metadata
                datos_cursos = cursos_data

            # DEBUG: Verificar qué datos estamos recibiendo
            self.log_mensaje(f"📥 Recibiendo datos de cursos: {len(datos_cursos)} elementos", "info")

            # Actualizar configuración interna
            if "cursos" not in self.configuracion["configuracion"]:
                self.configuracion["configuracion"]["cursos"] = {}

            cursos_config = self.configuracion["configuracion"]["cursos"]

            cursos_config["configurado"] = True if datos_cursos else False
            cursos_config["datos"] = datos_cursos
            cursos_config["total"] = len(datos_cursos)
            cursos_config["fecha_actualizacion"] = datetime.now().isoformat()

            # IMPORTANTE: Guardar configuración en JSON
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            total = len(datos_cursos)
            if isinstance(cursos_data, dict) and cursos_data.get("metadata", {}).get("accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de cursos restaurada: {total} cursos",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de cursos actualizada: {total} cursos guardados en JSON",
                    "success"
                )

            # Actualizar estado visual
            self.actualizar_estado_visual()

        except Exception as e:
            error_msg = f"Error al actualizar configuración de cursos: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_calendario(self, calendario_data):
        """Actualizar configuración de calendario en el sistema principal - Estilo idéntico a horarios"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(calendario_data, dict) and "metadata" in calendario_data:
                metadata = calendario_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    if "calendario" in calendario_data:
                        datos_calendario = calendario_data["calendario"]
                    else:
                        datos_calendario = {}
                    self.log_mensaje("🔄 Restaurando configuración original de calendario", "warning")
                else:
                    # Datos normales con metadata
                    datos_calendario = calendario_data.get("calendario", calendario_data)
            else:
                # Datos directos sin metadata
                datos_calendario = calendario_data

            # Calcular estadísticas
            dias_1 = len(datos_calendario.get("semestre_1", {}))
            dias_2 = len(datos_calendario.get("semestre_2", {}))
            total_dias = dias_1 + dias_2
            semanas_estimadas = total_dias // 5 if total_dias > 0 else 0

            # Actualizar configuración interna
            calendario_config = self.configuracion["configuracion"]["calendario"]

            calendario_config["configurado"] = True if total_dias > 0 else False
            calendario_config["datos"] = datos_calendario
            calendario_config["semanas_total"] = semanas_estimadas
            calendario_config["dias_semestre_1"] = dias_1
            calendario_config["dias_semestre_2"] = dias_2
            calendario_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Guardar configuración
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            if isinstance(calendario_data, dict) and calendario_data.get("metadata", {}).get(
                    "accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de calendario restaurada: {total_dias} días lectivos",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de calendario actualizada: {total_dias} días lectivos guardados ({dias_1}+{dias_2})",
                    "success"
                )

            # Actualizar estado visual
            self.actualizar_estado_visual()

        except Exception as e:
            error_msg = f"Error al actualizar configuración de calendario: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_horarios(self, datos_horarios):
        """Actualizar configuración cuando se completen los horarios"""
        try:
            # Extraer datos del diccionario recibido
            asignaturas_data = datos_horarios.get("asignaturas", {})
            metadata = datos_horarios.get("metadata", {})

            # Verificar que realmente hay datos nuevos
            if not asignaturas_data:
                self.log_mensaje("⚠️ No se recibieron datos de horarios para guardar", "warning")
                return

            # Actualizar configuración principal
            self.configuracion["configuracion"]["horarios"] = {
                "configurado": True,
                "datos": asignaturas_data,
                "archivo": "horarios_integrados.json",
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "semestre_actual": datos_horarios.get("semestre_actual", "2"),
                "total_asignaturas": metadata.get("total_asignaturas", 0),
                "total_franjas": metadata.get("total_franjas", 0)
            }

            # Actualizar metadata general
            self.configuracion["metadata"]["timestamp"] = datetime.now().isoformat()

            # Guardar automáticamente la configuración principal
            self.guardar_configuracion()

            # Actualizar interfaz visual
            self.actualizar_estado_visual()

            # SOLO LOG - SIN DIÁLOGOS MOLESTOS
            total_asignaturas = metadata.get("total_asignaturas", 0)
            total_franjas = metadata.get("total_franjas", 0)
            semestre = datos_horarios.get("semestre_actual", "?")

            self.log_mensaje(
                f"✅ Horarios integrados silenciosamente: S{semestre}, {total_asignaturas} asignaturas, {total_franjas} franjas",
                "success"
            )


        except Exception as e:
            error_msg = f"Error integrando horarios: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            # Solo mostrar error si realmente hay un problema
            QtWidgets.QMessageBox.critical(
                self, "Error de Integración",
                f"{error_msg}\n\nPor favor, intenta guardar manualmente."
            )

    def actualizar_configuracion_aulas(self, aulas_data):
        """Actualizar configuración de aulas en el sistema principal - Estilo idéntico a horarios"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(aulas_data, dict) and "metadata" in aulas_data:
                metadata = aulas_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    if "laboratorios" in aulas_data:
                        datos_aulas = aulas_data["laboratorios"]
                    else:
                        datos_aulas = {}

                    self.log_mensaje("🔄 Restaurando configuración original de aulas", "warning")
                else:
                    # Datos normales con metadata
                    datos_aulas = aulas_data.get("laboratorios", aulas_data)
            else:
                # Datos directos sin metadata
                datos_aulas = aulas_data

            # Actualizar configuración interna
            aulas_config = self.configuracion["configuracion"]["aulas"]

            aulas_config["configurado"] = True if datos_aulas else False
            aulas_config["datos"] = datos_aulas
            aulas_config["total_aulas"] = len(datos_aulas)
            aulas_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Guardar configuración
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            total = len(datos_aulas)
            if isinstance(aulas_data, dict) and aulas_data.get("metadata", {}).get("accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de aulas restaurada: {total} laboratorios",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de aulas actualizada: {total} laboratorios guardados",
                    "success"
                )

            # Actualizar estado de botón si existe
            if hasattr(self, 'btn_configurar_aulas'):
                if total > 0:
                    self.btn_configurar_aulas.setText(f"🏢 Aulas ({total})")
                else:
                    self.btn_configurar_aulas.setText("🏢 Configurar Aulas")

        except Exception as e:
            error_msg = f"Error al actualizar configuración de aulas: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_profesores(self, profesores_data):
        """Actualizar configuración de profesores en el sistema principal - Estilo idéntico a alumnos"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(profesores_data, dict) and "metadata" in profesores_data:
                metadata = profesores_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    if "profesores" in profesores_data:
                        datos_profesores = profesores_data["profesores"]
                    else:
                        datos_profesores = {}

                    self.log_mensaje("🔄 Restaurando configuración original de profesores", "warning")
                else:
                    # Datos normales con metadata
                    datos_profesores = profesores_data.get("profesores", profesores_data)
            else:
                # Datos directos sin metadata
                datos_profesores = profesores_data

            # Actualizar configuración interna
            profesores_config = self.configuracion["configuracion"]["profesores"]

            profesores_config["configurado"] = True if datos_profesores else False
            profesores_config["datos"] = datos_profesores
            profesores_config["total"] = len(datos_profesores)
            profesores_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Guardar configuración
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            total = len(datos_profesores)
            if isinstance(profesores_data, dict) and profesores_data.get("metadata", {}).get(
                    "accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de profesores restaurada: {total} profesores",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de profesores actualizada: {total} profesores guardados",
                    "success"
                )

            # Actualizar estado visual
            self.actualizar_estado_visual()

        except Exception as e:
            error_msg = f"Error al actualizar configuración de profesores: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_alumnos(self, alumnos_data):
        """Actualizar configuración de alumnos en el sistema principal - Estilo idéntico a horarios"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(alumnos_data, dict) and "metadata" in alumnos_data:
                metadata = alumnos_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    if "alumnos" in alumnos_data:
                        datos_alumnos = alumnos_data["alumnos"]
                    else:
                        datos_alumnos = {}

                    self.log_mensaje("🔄 Restaurando configuración original de alumnos", "warning")
                else:
                    # Datos normales con metadata
                    datos_alumnos = alumnos_data.get("alumnos", alumnos_data)
            else:
                # Datos directos sin metadata
                datos_alumnos = alumnos_data

            # Actualizar configuración interna
            alumnos_config = self.configuracion["configuracion"]["alumnos"]

            alumnos_config["configurado"] = True if datos_alumnos else False
            alumnos_config["datos"] = datos_alumnos
            alumnos_config["total"] = len(datos_alumnos)
            alumnos_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Guardar configuración
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            total = len(datos_alumnos)
            if isinstance(alumnos_data, dict) and alumnos_data.get("metadata", {}).get("accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de alumnos restaurada: {total} alumnos",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de alumnos actualizada: {total} alumnos guardados",
                    "success"
                )

            # Actualizar estado visual
            self.actualizar_estado_visual()

        except Exception as e:
            error_msg = f"Error al actualizar configuración de alumnos: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_asignaturas(self, asignaturas_data):
        """Actualizar configuración de asignaturas en el sistema principal"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(asignaturas_data, dict) and "metadata" in asignaturas_data:
                metadata = asignaturas_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    datos_asignaturas = asignaturas_data.get("asignaturas", {})
                    self.log_mensaje("🔄 Restaurando configuración original de asignaturas", "warning")
                else:
                    # Datos normales con metadata - extraer las asignaturas
                    datos_asignaturas = asignaturas_data.get("asignaturas", asignaturas_data)
            else:
                # CASO NORMAL: Datos directos de asignaturas SIN metadata
                datos_asignaturas = asignaturas_data

            # DEBUG: Verificar qué datos estamos recibiendo
            self.log_mensaje(f"📥 Recibiendo datos de asignaturas: {len(datos_asignaturas)} elementos", "info")

            # Actualizar configuración interna
            asignaturas_config = self.configuracion["configuracion"]["asignaturas"]

            asignaturas_config["configurado"] = True if datos_asignaturas else False
            asignaturas_config["datos"] = datos_asignaturas
            asignaturas_config["total"] = len(datos_asignaturas)
            asignaturas_config["fecha_actualizacion"] = datetime.now().isoformat()

            # IMPORTANTE: Guardar configuración en JSON
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            total = len(datos_asignaturas)
            if isinstance(asignaturas_data, dict) and asignaturas_data.get("metadata", {}).get(
                    "accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de asignaturas restaurada: {total} asignaturas",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de asignaturas actualizada: {total} asignaturas guardadas en JSON",
                    "success"
                )

            # Después de actualizar, sincronizar con horarios
            self.sincronizar_asignaturas_con_horarios()

            # Actualizar estado visual
            self.actualizar_estado_visual()

        except Exception as e:
            error_msg = f"Error al actualizar configuración de asignaturas: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def sincronizar_asignaturas_con_horarios(self, datos_asignaturas=None):
        """Sincronizar asignaturas con horarios"""
        try:
            # Si horarios está abierto, recargar datos
            if hasattr(self, 'ventana_horarios') and self.ventana_horarios:
                self.ventana_horarios.recargar_asignaturas_desde_sistema()
                self.log_mensaje("🔄 Horarios sincronizado con asignaturas", "info")

            # Si se pasaron datos específicos, se podrían procesar aquí
            if datos_asignaturas:
                self.log_mensaje(f"📤 Sincronizando {len(datos_asignaturas)} asignaturas con horarios", "info")

        except Exception as e:
            self.log_mensaje(f"⚠️ Error en sincronización: {e}", "warning")

    def actualizar_configuracion_parametros(self, parametros_data):
        """Actualizar configuración de parámetros en el sistema principal"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(parametros_data, dict) and "metadata" in parametros_data:
                metadata = parametros_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    datos_parametros = parametros_data.get("parametros", {})
                    self.log_mensaje("🔄 Restaurando configuración original de parámetros", "warning")
                else:
                    # Datos normales con metadata
                    datos_parametros = parametros_data.get("parametros", parametros_data)
            else:
                # CASO NORMAL: Datos directos de parámetros SIN metadata
                datos_parametros = parametros_data

            # DEBUG: Verificar qué datos estamos recibiendo
            total_parametros = (
                    len(datos_parametros.get("parametros_booleanos", {})) +
                    len(datos_parametros.get("pesos_optimizacion", {})) +
                    len(datos_parametros.get("configuraciones_adicionales", {}))
            )
            self.log_mensaje(f"📥 Recibiendo datos de parámetros: {total_parametros} elementos", "info")

            # Actualizar configuración interna
            if "parametros_organizacion" not in self.configuracion:
                self.configuracion["parametros_organizacion"] = {}

            parametros_config = self.configuracion["parametros_organizacion"]

            # Actualizar cada sección de parámetros
            parametros_config["parametros_booleanos"] = datos_parametros.get("parametros_booleanos", {})
            parametros_config["pesos_optimizacion"] = datos_parametros.get("pesos_optimizacion", {})
            parametros_config["configuraciones_adicionales"] = datos_parametros.get("configuraciones_adicionales", {})

            # Marcar como configurado
            parametros_config["configurado"] = True
            parametros_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Actualizar estado visual
            self.actualizar_estado_visual()

            # Guardar automáticamente
            self.guardar_configuracion()

            # Log de confirmación
            self.log_mensaje(f"✅ Configuración de parámetros actualizada: {total_parametros} parámetros guardados",
                             "success")

            # Opcional: Sincronizar con otras ventanas si es necesario
            # self.sincronizar_parametros_con_otras_ventanas(datos_parametros)

        except Exception as e:
            error_msg = f"Error al actualizar configuración de parámetros: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error de configuración",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_resultados(self, resultados_data):
        """Actualizar configuración de resultados en el sistema principal"""
        try:
            # Verificar si es una actualización de datos
            if isinstance(resultados_data, dict):
                # DEBUG: Verificar qué datos estamos recibiendo
                total_horarios = len(resultados_data.get("horarios", []))
                total_problemas = len(resultados_data.get("problemas", []))
                self.log_mensaje(
                    f"📥 Recibiendo actualización de resultados: {total_horarios} horarios, {total_problemas} problemas",
                    "info")

                # Actualizar configuración interna
                if "resultados_organizacion" not in self.configuracion:
                    self.configuracion["resultados_organizacion"] = {}

                resultados_config = self.configuracion["resultados_organizacion"]

                # Guardar los datos de resultados
                resultados_config["datos_disponibles"] = True
                resultados_config["ultima_ejecucion"] = resultados_data
                resultados_config["fecha_actualizacion"] = datetime.now().isoformat()

                # Estadísticas resumidas para el estado visual
                estadisticas = resultados_data.get("estadisticas", {})
                resultados_config["resumen"] = {
                    "total_grupos": estadisticas.get("total_grupos", 0),
                    "grupos_asignados": estadisticas.get("grupos_asignados", 0),
                    "conflictos_detectados": estadisticas.get("conflictos_detectados", 0),
                    "porcentaje_exito": (estadisticas.get("grupos_asignados", 0) / max(
                        estadisticas.get("total_grupos", 1), 1)) * 100
                }

                # Actualizar estado visual
                self.actualizar_estado_visual()

                # Guardar automáticamente
                self.guardar_configuracion()

                # Log de confirmación
                porcentaje_exito = resultados_config["resumen"]["porcentaje_exito"]
                self.log_mensaje(f"✅ Resultados actualizados: {porcentaje_exito:.1f}% de éxito en organización",
                                 "success")

            else:
                self.log_mensaje("⚠️ Datos de resultados inválidos recibidos", "warning")

        except Exception as e:
            error_msg = f"Error al actualizar resultados: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error de actualización",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def guardar_resultados_organizacion(self, datos_resultados):
        """Guardar resultados de organización en el sistema"""
        try:
            self.log_mensaje("💾 Guardando resultados de organización...", "info")

            # Actualizar configuración con los resultados
            if "resultados_organizacion" not in self.configuracion:
                self.configuracion["resultados_organizacion"] = {}

            resultados_config = self.configuracion["resultados_organizacion"]

            # Guardar los datos completos
            resultados_config["datos_disponibles"] = True
            resultados_config["ultima_ejecucion"] = datos_resultados
            resultados_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Estadísticas resumidas para el estado visual
            estadisticas = datos_resultados.get("estadisticas", {})
            resultados_config["resumen"] = {
                "total_grupos": estadisticas.get("total_grupos", 0),
                "grupos_asignados": estadisticas.get("grupos_asignados", 0),
                "conflictos_detectados": estadisticas.get("conflictos_detectados", 0),
                "porcentaje_exito": estadisticas.get("porcentaje_exito", 0)
            }

            # Guardar en historial (mantener últimas 5 ejecuciones)
            if "historial_ejecuciones" not in resultados_config:
                resultados_config["historial_ejecuciones"] = []

            historial = resultados_config["historial_ejecuciones"]
            historial.append({
                "timestamp": datetime.now().isoformat(),
                "resumen": resultados_config["resumen"].copy(),
                "total_horarios": len(datos_resultados.get("horarios", [])),
                "total_problemas": len(datos_resultados.get("problemas", []))
            })

            # Mantener solo últimas 5 ejecuciones
            if len(historial) > 5:
                historial.pop(0)

            # Actualizar estado visual
            self.actualizar_estado_visual()

            # Guardar automáticamente
            self.guardar_configuracion()

            porcentaje_exito = resultados_config["resumen"]["porcentaje_exito"]
            self.log_mensaje(f"✅ Resultados guardados: {porcentaje_exito:.1f}% de éxito", "success")

            return True

        except Exception as e:
            self.log_mensaje(f"❌ Error guardando resultados: {e}", "error")
            return False

    # ========= MÉTODOS DE NAVEGACIÓN =========
    def abrir_configurar_cursos(self):
        """Abrir ventana de configuración de cursos - Estilo idéntico a asignaturas"""
        try:
            from modules.interfaces.configurar_cursos import ConfigurarCursos
            CURSOS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configurar_cursos no disponible: {e}")
            CURSOS_DISPONIBLE = False

        if not CURSOS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_cursos.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("🎓 Abriendo configuración de cursos...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_cursos') and self.ventana_cursos:
                self.ventana_cursos.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            cursos_config = self.configuracion["configuracion"].get("cursos", {})

            if cursos_config.get("configurado") and cursos_config.get("datos"):
                datos_existentes = cursos_config["datos"].copy()
                total_cursos = cursos_config.get("total", 0)
                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_cursos} cursos configurados",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de cursos", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_cursos = ConfigurarCursos(
                parent=self,
                datos_existentes=datos_existentes
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_cursos.configuracion_actualizada.connect(self.actualizar_configuracion_cursos)

            self.ventana_cursos.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de cursos abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de cursos abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de cursos: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_calendario(self):
        """Abrir ventana de configuración de calendario - Estilo idéntico a horarios"""
        try:
            from modules.interfaces.configurar_calendario import ConfigurarCalendario
            CALENDARIO_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configurar_calendario no disponible: {e}")
            CALENDARIO_DISPONIBLE = False

        if not CALENDARIO_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_calendario.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("📅 Abriendo configuración de calendario...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_calendario') and self.ventana_calendario:
                self.ventana_calendario.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            calendario_config = self.configuracion["configuracion"]["calendario"]

            if calendario_config["configurado"] and calendario_config.get("datos"):
                datos_existentes = calendario_config["datos"].copy()
                semanas = calendario_config.get("semanas_total", 0)
                self.log_mensaje(
                    f"📥 Cargando configuración existente: {semanas} semanas configuradas",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de calendario", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_calendario = ConfigurarCalendario(
                parent=self,
                datos_existentes=datos_existentes
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_calendario.configuracion_actualizada.connect(self.actualizar_configuracion_calendario)

            self.ventana_calendario.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de calendario abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de calendario abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de calendario: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_horarios(self):
        """Abrir ventana de configuración de horarios"""
        try:
            from modules.interfaces.configurar_horarios import ConfigurarHorarios
            HORARIOS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configurar_horarios no disponible: {e}")
            HORARIOS_DISPONIBLE = False

        if not HORARIOS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_horarios.py no está disponible.\n"
                "Verifica que esté en modules/interfaces/"
            )
            return

        self.log_mensaje("⏰ Abriendo configuración de horarios...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_horarios') and self.ventana_horarios:
                self.ventana_horarios.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            horarios_config = self.configuracion["configuracion"]["horarios"]

            if horarios_config["configurado"] and horarios_config.get("datos"):
                # Hay datos guardados, prepararlos para la ventana
                datos_existentes = {
                    "semestre_actual": horarios_config.get("semestre_actual", "2"),
                    "asignaturas": horarios_config["datos"]
                }

                total_asig = horarios_config.get("total_asignaturas", 0)
                total_franjas = horarios_config.get("total_franjas", 0)

                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_asig} asignaturas, {total_franjas} franjas",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de horarios", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_horarios = ConfigurarHorarios(
                parent=self,
                datos_existentes=datos_existentes  # ← PASAR DATOS EXISTENTES
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_horarios.configuracion_actualizada.connect(self.actualizar_configuracion_horarios)

            self.ventana_horarios.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de horarios abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de horarios abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de horarios: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_aulas(self):
        """Abrir ventana de configuración de aulas/laboratorios - Estilo idéntico a horarios"""
        # Verificar si el módulo está disponible
        try:
            from modules.interfaces.configurar_aulas import ConfigurarAulas
            AULAS_DISPONIBLE = True
        except ImportError:
            AULAS_DISPONIBLE = False

        if not AULAS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_aulas.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("🏢 Abriendo configuración de aulas...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_aulas') and self.ventana_aulas:
                self.ventana_aulas.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            aulas_config = self.configuracion["configuracion"]["aulas"]

            if aulas_config["configurado"] and aulas_config.get("datos"):
                # Hay datos guardados, prepararlos para la ventana
                datos_existentes = aulas_config["datos"].copy()

                total_aulas = aulas_config.get("total_aulas", 0)

                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_aulas} aulas configuradas",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de aulas", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_aulas = ConfigurarAulas(
                parent=self,
                datos_existentes=datos_existentes  # ← PASAR DATOS EXISTENTES
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_aulas.configuracion_actualizada.connect(self.actualizar_configuracion_aulas)

            self.ventana_aulas.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de aulas abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de aulas abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de aulas: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_profesores(self):
        """Abrir ventana de configuración de profesores - Estilo idéntico a alumnos"""
        try:
            from modules.interfaces.configuracion_profesores import ConfigurarProfesores
            PROFESORES_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configuracion_profesores no disponible: {e}")
            PROFESORES_DISPONIBLE = False

        if not PROFESORES_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configuracion_profesores.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("👨‍🏫 Abriendo configuración de profesores...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_profesores') and self.ventana_profesores:
                self.ventana_profesores.close()

            # PREPARAR DATOS EXISTENTES
            datos_existentes = None
            profesores_config = self.configuracion["configuracion"]["profesores"]

            if profesores_config["configurado"] and profesores_config.get("datos"):
                datos_existentes = profesores_config["datos"].copy()
                total_profesores = profesores_config.get("total", 0)
                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_profesores} profesores configurados",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de profesores", "info")

            # Crear ventana
            self.ventana_profesores = ConfigurarProfesores(
                parent=self,
                datos_existentes=datos_existentes
            )

            # Conectar señal
            self.ventana_profesores.configuracion_actualizada.connect(self.actualizar_configuracion_profesores)

            self.ventana_profesores.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de profesores abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de profesores abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de profesores: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_alumnos(self):
        """Abrir ventana de configuración de alumnos - Estilo idéntico a horarios"""
        try:
            from modules.interfaces.configuracion_alumnos import ConfigurarAlumnos
            ALUMNOS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configuracion_alumnos no disponible: {e}")
            ALUMNOS_DISPONIBLE = False

        if not ALUMNOS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configuracion_alumnos.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("👥 Abriendo configuración de alumnos...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_alumnos') and self.ventana_alumnos:
                self.ventana_alumnos.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            alumnos_config = self.configuracion["configuracion"]["alumnos"]

            if alumnos_config["configurado"] and alumnos_config.get("datos"):
                datos_existentes = alumnos_config["datos"].copy()
                total_alumnos = alumnos_config.get("total", 0)
                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_alumnos} alumnos configurados",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de alumnos", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_alumnos = ConfigurarAlumnos(
                parent=self,
                datos_existentes=datos_existentes
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_alumnos.configuracion_actualizada.connect(self.actualizar_configuracion_alumnos)

            self.ventana_alumnos.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de alumnos abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de alumnos abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de alumnos: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_asignaturas(self):
        """Abrir ventana de configuración de asignaturas - Estilo idéntico a horarios"""
        try:
            from modules.interfaces.configurar_asignaturas import ConfigurarAsignaturas
            ASIGNATURAS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configuracion_asignaturas no disponible: {e}")
            ASIGNATURAS_DISPONIBLE = False

        if not ASIGNATURAS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configuracion_asignaturas.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("📋 Abriendo configuración de asignaturas...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_asignaturas') and self.ventana_asignaturas:
                self.ventana_asignaturas.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            asignaturas_config = self.configuracion["configuracion"]["asignaturas"]

            if asignaturas_config["configurado"] and asignaturas_config.get("datos"):
                datos_existentes = asignaturas_config["datos"].copy()
                total_asignaturas = asignaturas_config.get("total", 0)
                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_asignaturas} asignaturas configuradas",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de asignaturas", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_asignaturas = ConfigurarAsignaturas(
                parent=self,
                datos_existentes=datos_existentes
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_asignaturas.configuracion_actualizada.connect(self.actualizar_configuracion_asignaturas)

            self.ventana_asignaturas.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de asignaturas abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de asignaturas abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de asignaturas: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_configurar_parametros(self):
        """Abrir ventana de configuración de parámetros - Estilo idéntico a otras ventanas"""
        # Verificar si el módulo está disponible
        try:
            from modules.interfaces.configurar_parametros import ConfigurarParametros
            PARAMETROS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configurar_parametros no disponible: {e}")
            PARAMETROS_DISPONIBLE = False

        if not PARAMETROS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_parametros.py no está disponible.\n"
                "Verifica que esté en modules/interfaces/configurar_parametros.py"
            )
            return

        self.log_mensaje("🎯 Abriendo configuración de parámetros...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_parametros') and self.ventana_parametros:
                self.ventana_parametros.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            parametros_config = self.configuracion.get("parametros_organizacion", {})

            if parametros_config:
                # Hay datos guardados, prepararlos para la ventana
                datos_existentes = {
                    "parametros_booleanos": parametros_config.get("parametros_booleanos", {}),
                    "pesos_optimizacion": parametros_config.get("pesos_optimizacion", {}),
                    "configuraciones_adicionales": parametros_config.get("configuraciones_adicionales", {})
                }

                total_parametros = (
                        len(datos_existentes["parametros_booleanos"]) +
                        len(datos_existentes["pesos_optimizacion"]) +
                        len(datos_existentes["configuraciones_adicionales"])
                )

                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_parametros} parámetros configurados",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de parámetros", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_parametros = ConfigurarParametros(
                parent=self,
                datos_existentes=datos_existentes  # ← PASAR DATOS EXISTENTES
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_parametros.configuracion_actualizada.connect(self.actualizar_configuracion_parametros)

            self.ventana_parametros.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de parámetros abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de parámetros abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de parámetros: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def abrir_ver_resultados(self):
        """Abrir ventana de visualización de resultados - CON MENSAJE MEJORADO"""
        # Verificar si el módulo está disponible
        try:
            from modules.interfaces.ver_resultados import VerResultados
            RESULTADOS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo ver_resultados no disponible: {e}")
            RESULTADOS_DISPONIBLE = False

        if not RESULTADOS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo ver_resultados.py no está disponible.\n"
                "Verifica que esté en modules/interfaces/ver_resultados.py"
            )
            return

        # Verificar si hay resultados disponibles
        resultados_disponibles = self.configuracion.get("resultados_organizacion", {}).get("datos_disponibles", False)

        if not resultados_disponibles:
            # MENSAJE MEJORADO CUANDO NO HAY DATOS
            mensaje_sin_datos = """
    📊 No hay resultados disponibles

    Para ver los resultados de organización, primero debes:

    1️⃣ Completar todas las configuraciones necesarias:
       • Cursos y asignaturas
       • Profesores y alumnos  
       • Aulas y horarios
       • Parámetros de organización

    2️⃣ Hacer clic en el botón azul "✨ ORGANIZAR LABORATORIOS"

    3️⃣ Esperar a que se complete el proceso

    Una vez completada la organización, podrás visualizar:
    • Horarios generados por laboratorio
    • Asignaciones por profesor
    • Grupos de alumnos
    • Estadísticas de calidad
    • Problemas detectados

    ¿Quieres ver la ventana con datos de ejemplo?
            """

            reply = QtWidgets.QMessageBox.question(
                self, "Sin Resultados Disponibles", mensaje_sin_datos,
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )

            if reply == QtWidgets.QMessageBox.StandardButton.No:
                self.log_mensaje("ℹ️ Visualización de resultados cancelada - sin datos", "info")
                return

            self.log_mensaje("📝 Abriendo resultados con datos simulados (sin datos reales)", "info")

        self.log_mensaje("📊 Abriendo visualización de resultados...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_resultados') and self.ventana_resultados:
                self.ventana_resultados.close()

            # PREPARAR DATOS DE RESULTADOS PARA PASAR A LA VENTANA
            datos_resultados = None

            if resultados_disponibles:
                resultados_config = self.configuracion["resultados_organizacion"]
                datos_resultados = resultados_config.get("ultima_ejecucion", {})

                timestamp = datos_resultados.get("timestamp", "fecha desconocida")
                total_horarios = len(datos_resultados.get("horarios", []))

                self.log_mensaje(
                    f"📥 Cargando resultados reales: {total_horarios} horarios generados ({timestamp})",
                    "success"
                )

            # Crear ventana con datos existentes (o None para usar simulados)
            self.ventana_resultados = VerResultados(
                parent=self,
                datos_resultados=datos_resultados
            )

            # Conectar señal para recibir actualizaciones
            self.ventana_resultados.resultados_actualizados.connect(self.actualizar_configuracion_resultados)

            self.ventana_resultados.show()

            if datos_resultados:
                self.log_mensaje("✅ Ventana de resultados abierta con datos reales", "success")
            else:
                self.log_mensaje("✅ Ventana de resultados abierta con datos simulados", "info")

        except Exception as e:
            error_msg = f"Error al abrir visualización de resultados: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    # ========= MÉTODOS DE ACCIÓN =========
    def iniciar_organizacion(self):
        """Iniciar proceso de organización de laboratorios"""
        self.log_mensaje("✨ Iniciando organización de laboratorios...", "info")

        # Verificar que todos los datos necesarios estén configurados
        if not self._verificar_configuracion_completa():
            return

        # Mostrar diálogo de confirmación
        reply = QtWidgets.QMessageBox.question(
            self, "Confirmar Organización",
            "¿Estás seguro de que quieres iniciar la organización de laboratorios?\n\n"
            "Este proceso puede tardar varios minutos y generará nuevos horarios.\n"
            "Los resultados anteriores se sobrescribirán.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.No:
            self.log_mensaje("❌ Organización cancelada por el usuario", "warning")
            return

        try:
            # Deshabilitar interfaz durante el proceso
            self._deshabilitar_interfaz_organizacion()

            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Iniciando organización... %p%")

            # Importar y ejecutar motor de organización
            from modules.organizador.motor_organizacion import ejecutar_organizacion

            # Preparar callback de progreso
            def actualizar_progreso(valor):
                self.progress_bar.setValue(valor)
                if valor <= 5:
                    self.progress_bar.setFormat("Validando datos... %p%")
                elif valor <= 15:
                    self.progress_bar.setFormat("Generando grupos... %p%")
                elif valor <= 30:
                    self.progress_bar.setFormat("Asignando recursos... %p%")
                elif valor <= 50:
                    self.progress_bar.setFormat("Resolviendo conflictos... %p%")
                elif valor <= 70:
                    self.progress_bar.setFormat("Optimizando... %p%")
                elif valor <= 90:
                    self.progress_bar.setFormat("Generando estadísticas... %p%")
                else:
                    self.progress_bar.setFormat("Completando... %p%")

                # Procesar eventos para mantener la UI responsive
                QtWidgets.QApplication.processEvents()

            # Ejecutar organización
            self.log_mensaje("🚀 Ejecutando motor de organización...", "info")
            resultado = ejecutar_organizacion(self.configuracion, actualizar_progreso)

            # Procesar resultados
            if resultado["exito"]:
                self._procesar_resultados_exitosos(resultado["resultados"])
            else:
                self._procesar_resultados_fallidos(resultado["mensaje"])


        except ImportError as e:

            error_msg = f"Error: No se pudo importar el motor de organización.\n\nVerifica que motor_organizacion.py esté en la misma carpeta.\n\nError técnico: {e}"

            self.log_mensaje(f"❌ {error_msg}", "error")

            QtWidgets.QMessageBox.critical(self, "Error de Importación", error_msg)

        except Exception as e:
            error_msg = f"Error inesperado durante la organización: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(self, "Error de Organización", error_msg)

        finally:
            # Restaurar interfaz
            self._restaurar_interfaz_organizacion()
            self.progress_bar.setVisible(False)

    def _verificar_configuracion_completa(self):
        """Verificar que toda la configuración necesaria esté completa"""
        configuraciones_requeridas = {
            "cursos": "Configuración de cursos",
            "asignaturas": "Configuración de asignaturas",
            "profesores": "Configuración de profesores",
            "alumnos": "Configuración de alumnos",
            "horarios": "Configuración de horarios",
            "aulas": "Configuración de aulas",
            "parametros": "Parámetros de organización"
        }

        faltantes = []

        # Verificar configuraciones básicas
        for key, nombre in configuraciones_requeridas.items():
            if key == "parametros":
                config_section = self.configuracion.get("parametros_organizacion", {})
            else:
                config_section = self.configuracion["configuracion"].get(key, {})

            if not config_section.get("configurado", False):
                faltantes.append(nombre)

        if faltantes:
            mensaje = "No se puede iniciar la organización. Faltan configurar:\n\n"
            mensaje += "\n".join([f"• {item}" for item in faltantes])
            mensaje += "\n\nPor favor, completa todas las configuraciones antes de continuar."

            QtWidgets.QMessageBox.warning(self, "Configuración Incompleta", mensaje)
            self.log_mensaje(f"⚠️ Configuración incompleta: {', '.join(faltantes)}", "warning")
            return False

        # Verificar que haya datos suficientes
        if len(self.configuracion["configuracion"]["alumnos"].get("datos", {})) == 0:
            QtWidgets.QMessageBox.warning(self, "Sin Datos", "No hay alumnos configurados en el sistema.")
            return False

        if len(self.configuracion["configuracion"]["profesores"].get("datos", {})) == 0:
            QtWidgets.QMessageBox.warning(self, "Sin Datos", "No hay profesores configurados en el sistema.")
            return False

        if len(self.configuracion["configuracion"]["aulas"].get("datos", {})) == 0:
            QtWidgets.QMessageBox.warning(self, "Sin Datos", "No hay aulas configuradas en el sistema.")
            return False

        self.log_mensaje("✅ Configuración completa verificada", "success")
        return True

    def _deshabilitar_interfaz_organizacion(self):
        """Deshabilitar interfaz durante organización"""
        # Deshabilitar botones principales
        for btn in self.botones_principales.values():
            btn.setEnabled(False)

        # Deshabilitar botones de configuración
        for btn in self.botones_config.values():
            btn.setEnabled(False)

        # Cambiar texto del botón de organizar
        self.botones_principales["btn_organizar"].setText("⏳ ORGANIZANDO...")
        self.botones_principales["btn_organizar"].setStyleSheet("""
            QPushButton {
                background-color: rgb(200,100,0);
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
        """)

    def _restaurar_interfaz_organizacion(self):
        """Restaurar interfaz después de organización"""
        # Restaurar botones principales
        for btn in self.botones_principales.values():
            btn.setEnabled(True)

        # Restaurar botones de configuración
        for btn in self.botones_config.values():
            btn.setEnabled(True)

        # Restaurar texto del botón de organizar
        self.botones_principales["btn_organizar"].setText("✨ ORGANIZAR\nLABORATORIOS")
        self.botones_principales["btn_organizar"].setStyleSheet(self.estilo_boton_principal())

    def _procesar_resultados_exitosos(self, resultados):
        """Procesar resultados exitosos de organización"""
        self.log_mensaje("✅ Organización completada exitosamente", "success")

        # Guardar resultados en configuración
        self.guardar_resultados_organizacion(resultados)

        # Mostrar estadísticas resumidas
        estadisticas = resultados.get("estadisticas", {})
        mensaje_exito = f"""
    🎉 ¡ORGANIZACIÓN COMPLETADA!

    📊 RESULTADOS:
    • Total de grupos: {estadisticas.get('total_grupos', 0)}
    • Grupos asignados: {estadisticas.get('grupos_asignados', 0)}
    • Porcentaje de éxito: {estadisticas.get('porcentaje_exito', 0):.1f}%
    • Conflictos detectados: {estadisticas.get('conflictos_detectados', 0)}

    🏢 RECURSOS UTILIZADOS:
    • Aulas utilizadas: {estadisticas.get('aulas_utilizadas', 0)}
    • Profesores participantes: {estadisticas.get('profesores_participantes', 0)}
    • Utilización promedio: {estadisticas.get('utilizacion_promedio_aulas', 0):.1f}%

    📋 CALIDAD:
    • Grupos equilibrados: {estadisticas.get('grupos_equilibrados', 0)}
    • Horas tempranas: {estadisticas.get('horas_tempranas_utilizadas', 0):.1f}%

    ¿Quieres ver los resultados detallados?
        """

        # Mostrar diálogo con opción de ver resultados
        reply = QtWidgets.QMessageBox.question(
            self, "Organización Completada", mensaje_exito,
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # Abrir ventana de resultados automáticamente
            self.abrir_ver_resultados()

    def _procesar_resultados_fallidos(self, mensaje_error):
        """Procesar resultados fallidos de organización"""
        self.log_mensaje(f"❌ Organización fallida: {mensaje_error}", "error")

        mensaje_completo = f"""
    ❌ Error en la Organización

    La organización de laboratorios no pudo completarse debido al siguiente problema:

    {mensaje_error}

    POSIBLES SOLUCIONES:
    • Verificar que todos los datos estén correctamente configurados
    • Revisar la compatibilidad entre asignaturas y aulas
    • Confirmar disponibilidad de profesores
    • Ajustar parámetros de organización
    • Revisar que haya suficientes recursos disponibles

    ¿Quieres revisar la configuración?
        """

        reply = QtWidgets.QMessageBox.question(
            self, "Error en Organización", mensaje_completo,
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # Abrir configuración de parámetros para revisar
            self.abrir_configurar_parametros()

    def guardar_configuracion(self):
        """Guardar configuración actual"""
        try:
            self.configuracion["metadata"]["timestamp"] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configuracion, f, indent=2, ensure_ascii=False)
            self.log_mensaje(f"✅ Configuración guardada en {self.config_file}", "success")
        except Exception as e:
            self.log_mensaje(f"❌ Error guardando configuración: {e}", "error")

    def cargar_configuracion_archivo(self):
        """Cargar configuración desde archivo"""
        archivo, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Cargar Configuración", "", "JSON Files (*.json)"
        )
        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    self.configuracion = json.load(f)
                self.actualizar_estado_visual()
                self.log_mensaje(f"✅ Configuración cargada desde {archivo}", "success")
            except Exception as e:
                self.log_mensaje(f"❌ Error cargando configuración: {e}", "error")

    def reset_configuracion(self):
        """Reset completo de configuración"""
        reply = QtWidgets.QMessageBox.question(
            self, "Reset Configuración",
            "¿Estás seguro de que quieres resetear toda la configuración?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.configuracion = self.cargar_configuracion()
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            self.actualizar_estado_visual()
            self.log_mensaje("🔄 Configuración reseteada completamente", "warning")

    def mostrar_ayuda(self):
        """Mostrar ayuda y soporte"""
        QtWidgets.QMessageBox.information(
            self, "Ayuda - OPTIM Labs",
            "OPTIM - Sistema de Programación de Laboratorios\n\n"
            "Flujo recomendado:\n"
            "1️⃣ Configurar Calendario semestral\n"
            "2️⃣ Configurar Horarios por asignatura\n"
            "3️⃣ Configurar Aulas/Laboratorios\n"
            "4️⃣ Configurar Profesores\n"
            "5️⃣ Configurar Alumnos matriculados\n"
            "6️⃣ Organizar Laboratorios\n\n"
            "Desarrollado por SoftVier para ETSIDI (UPM)"
        )

    # ========= ESTILOS =========
    def estilo_boton_configuracion(self):
        return """
            QPushButton {
                background-color: rgb(53,53,53);
                color: white;
                border: 2px solid rgb(127,127,127);
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgb(66,66,66);
                border-color: rgb(42,130,218);
            }
            QPushButton:pressed {
                background-color: rgb(42,130,218);
            }
        """

    def estilo_boton_principal(self):
        return """
            QPushButton {
                background-color: rgb(42,130,218);
                color: white;
                border: 2px solid rgb(42,130,218);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(50,140,228);
            }
            QPushButton:pressed {
                background-color: rgb(35,120,200);
            }
            QPushButton:disabled {
                background-color: rgb(80,80,80);
                border-color: rgb(100,100,100);
                color: rgb(150,150,150);
            }
        """

    def estilo_boton_secundario(self):
        return """
            QPushButton {
                background-color: rgb(53,53,53);
                color: white;
                border: 1px solid rgb(127,127,127);
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(66,66,66);
                border-color: rgb(42,130,218);
            }
        """

    def aplicar_tema_oscuro(self):
        """Aplicar tema oscuro idéntico al sistema"""
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
            QFrame {
                background-color: rgb(42,42,42);
                border: 1px solid rgb(127,127,127);
                border-radius: 6px;
            }
            QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
                border: none;
            }
        """)


def main():
    """Función principal"""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("OPTIM Labs by SoftVier")
    app.setStyle('Fusion')

    # Aplicar paleta de colores oscura
    paleta = QtGui.QPalette()
    paleta.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(53, 53, 53))
    paleta.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(42, 42, 42))
    paleta.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(66, 66, 66))
    paleta.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(53, 53, 53))
    paleta.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(255, 255, 255))
    paleta.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 0, 0))
    paleta.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
    paleta.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
    paleta.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(255, 255, 255))
    app.setPalette(paleta)

    # Crear y mostrar ventana principal
    window = OptimLabsGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()