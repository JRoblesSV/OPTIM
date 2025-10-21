#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar GUI - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

import sys
import os
import json
import copy
import re as _re
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore, QtGui, QtWidgets


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
    def _downloads_dir(self) -> str:
        """Ruta a la carpeta Descargas del usuario (multiplataforma)."""
        home = os.path.expanduser("~")
        ruta = os.path.join(home, "Downloads")
        try:
            os.makedirs(ruta, exist_ok=True)
        except Exception:
            pass
        return ruta

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
        self.log_mensaje("🔄 OPTIM iniciado correctamente", "info")

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

        # Barra de progreso para organización de laboratorios
        self.setup_progress_bar()

        # Aplicar tema visual del sistema
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
            ("grupos", "🎓 Grupos", 20),
            ("asignaturas", "📚 Asignaturas", 180),
            ("profesores", "👨‍🏫 Profesores", 340),
            ("alumnos", "👥 Alumnos", 500),
            ("aulas", "🏢 Aulas", 660),
            ("calendario", "📆 Calendario", 820),
            ("horarios", "📅 Horarios", 980)
        ]

        self.labels_estado = {}
        for key, texto, x_pos in estados:
            # Label título
            label_titulo = QtWidgets.QLabel(self.frame_estado)
            label_titulo.setGeometry(QtCore.QRect(x_pos, 10, 130, 20))
            label_titulo.setText(texto)
            label_titulo.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")

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
            ("btn_grupos", "🎓 GRUPOS\nGrados y titulaciones", 50, 20),
            ("btn_asignaturas", "📋 ASIGNATURAS\nLímites y grupos", 300, 20),
            ("btn_profesores", "👨‍🏫 PROFESORES\nDisponibilidad horaria", 550, 20),
            ("btn_alumnos", "👥 ALUMNOS\nMatrículas por asignatura", 800, 20)
        ]

        # Segunda fila de botones
        botones_fila2 = [
            ("btn_aulas", "🏢 AULAS\nLaboratorios disponibles", 50, 100),
            ("btn_calendario", "📅 CALENDARIO\nConfigurar semestre", 300, 100),
            ("btn_horarios", "⏰ HORARIOS\nFranjas por asignatura", 550, 100),
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
            ("btn_exportar", "💾 EXPORTAR\nCONFIGURACIÓN", 300, 15, 220, False),
            ("btn_importar", "📥 IMPORTAR\nCONFIGURACIÓN", 550, 15, 220, False),
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
        self.botones_config["btn_grupos"].clicked.connect(self.abrir_configurar_grupos)
        self.botones_config["btn_asignaturas"].clicked.connect(self.abrir_configurar_asignaturas)
        self.botones_config["btn_profesores"].clicked.connect(self.abrir_configurar_profesores)
        self.botones_config["btn_alumnos"].clicked.connect(self.abrir_configurar_alumnos)

        self.botones_config["btn_calendario"].clicked.connect(self.abrir_configurar_calendario)
        self.botones_config["btn_horarios"].clicked.connect(self.abrir_configurar_horarios)
        self.botones_config["btn_aulas"].clicked.connect(self.abrir_configurar_aulas)
        self.botones_config["btn_parametros"].clicked.connect(self.abrir_configurar_parametros)

        # Botones principales
        self.botones_principales["btn_organizar"].clicked.connect(self._ejecutar_motor_organizacion)
        self.botones_principales["btn_exportar"].clicked.connect(self.exportar_configuracion)
        self.botones_principales["btn_importar"].clicked.connect(self.importar_configuracion)
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

        # Configuración por defecto del sistema
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
                "grupos": {"configurado": False, "datos": {}, "total": 0}
            },
            # Sección de resultados de organización
            "resultados_organizacion": {
                "datos_disponibles": False,
                "fecha_actualizacion": None
            }
        }

    def actualizar_estado_visual(self):
        """Actualizar indicadores visuales de configuración"""
        configuraciones = {
            "grupos": self.configuracion["configuracion"]["grupos"],
            "asignaturas": self.configuracion["configuracion"]["asignaturas"],
            "profesores": self.configuracion["configuracion"]["profesores"],
            "alumnos": self.configuracion["configuracion"]["alumnos"],
            "calendario": self.configuracion["configuracion"]["calendario"],
            "horarios": self.configuracion["configuracion"]["horarios"],
            "aulas": self.configuracion["configuracion"]["aulas"],
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
                    elif key == "horarios":
                        # Caso especial para horarios - mostrar franjas
                        total_franjas = config.get("total", 0)
                        total_asignaturas = config.get("total_asignaturas", 0)
                        self.labels_estado[key].setText(f"✅ {total_franjas} franjas\n{total_asignaturas} asignaturas")
                    elif key == "calendario":
                        # Caso especial para calendario - mostrar días
                        total_dias = config.get("total", 0)
                        self.labels_estado[key].setText(f"✅ {total_dias} días lectivos\nconfigurados")
                    elif key == "aulas":
                        # Caso especial para aulas - mostrar laboratorios
                        total_aulas = config.get("total_aulas", config.get("total", 0))
                        self.labels_estado[key].setText(f"✅ {total_aulas} laboratorios\nconfigurados")
                    else:
                        # Otros casos (grupos, asignaturas, profesores, alumnos)
                        total = config.get("total", 0)
                        elementos_texto = {
                            "grupos": "grupos",
                            "asignaturas": "asignaturas",
                            "profesores": "profesores",
                            "alumnos": "alumnos"
                        }
                        texto_elemento = elementos_texto.get(key, "elementos")
                        self.labels_estado[key].setText(f"✅ {total} {texto_elemento}\nconfigurados")

                    self.labels_estado[key].setStyleSheet("font-size: 11px; color: rgb(100,200,100);")
                else:
                    self.labels_estado[key].setText("❌ Sin configurar")
                    self.labels_estado[key].setStyleSheet("font-size: 11px; color: rgb(220,220,220);")

        # Actualizar resumen
        self.actualizar_resumen_configuracion()

        # Verificar si se puede organizar
        configuraciones_obligatorias = ["grupos", "asignaturas", "profesores", "alumnos", "horarios", "aulas", "calendario"]
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

                # Tooltips según disponibilidad
                if hay_resultados:
                    self.botones_secundarios["btn_resultados"].setToolTip("Abrir resultados de la última ejecución.")
                else:
                    self.botones_secundarios["btn_resultados"].setToolTip("Ejecute la organización primero.")

        if todo_configurado:
            self.log_mensaje("🎯 Sistema listo para organizar laboratorios", "success")
        else:
            faltantes = [key for key in configuraciones_obligatorias if
                         not configuraciones[key].get("configurado", False)]
            self.log_mensaje(f"⚠️ Faltan configurar: {', '.join(faltantes)}", "warning")

    def actualizar_resumen_configuracion(self):
        """Actualizar texto de resumen de configuración"""
        config = self.configuracion["configuracion"]
        # Aviso de claves desconocidas para depuración (no bloqueante)
        claves_conocidas = {"grupos","asignaturas","profesores","alumnos","aulas","horarios","calendario"}
        for k in list(config.keys()):
            if k not in claves_conocidas:
                self.log_mensaje(f"Clave desconocida en configuración: {k} (ignorada)", "warning")
        resultados = self.configuracion.get("resultados_organizacion", {})

        resumen = "📋 CONFIGURACIÓN ACTUAL DEL SISTEMA\n"
        resumen += "=" * 80 + "\n\n"

        # Configuraciones básicas
        resumen += "📚 DATOS ACADÉMICOS:\n"
        resumen += f"  • Grupos: {config['grupos'].get('total', 0)} configurados\n"
        resumen += f"  • Asignaturas: {config['asignaturas'].get('total', 0)} configuradas\n"
        resumen += f"  • Profesores: {config['profesores'].get('total', 0)} configurados\n"
        resumen += f"  • Alumnos: {config['alumnos'].get('total', 0)} configurados\n"

        resumen += "\n🏢 INFRAESTRUCTURA:\n"
        resumen += f"  • Aulas/Laboratorios: {config['aulas'].get('total_aulas', 0)} configuradas\n"
        resumen += f"  • Horarios: {'✅ Configurado' if config['horarios'].get('configurado') else '❌ Sin configurar'}\n"
        resumen += f"  • Calendario: {'✅ Configurado' if config['calendario'].get('configurado') else '❌ Sin configurar'}\n"

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

    def get_estado_grupos(self):
        """Obtener estado de configuración de grupos"""
        grupos = self.configuracion["configuracion"].get("grupos", {})
        if grupos.get("configurado", False) and grupos.get("total", 0) > 0:
            return ("✅", f"{grupos['total']} grupos", "rgb(100,255,100)")
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
        # Alias simple a la versión principal
        return self.actualizar_resumen_configuracion()
        config = self.configuracion["configuracion"]
        resumen = []

        # Sección horarios
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
            ("grupos", "GRUPOS", 50),
            ("asignaturas", "ASIGNATURAS", 200),
            ("profesores", "PROFESORES", 350),
            ("alumnos", "ALUMNOS", 500),
            ("calendario", "CALENDARIO", 650),
            ("horarios", "HORARIOS", 800),
            ("aulas", "AULAS", 950),
            ("parametros", "PARÁMETROS", 1100),
            ("resultados", "RESULTADOS", 1250)
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

        # Normalización de estilo
        mensaje = str(mensaje).strip()
        if not mensaje.endswith((".", "…", "!", "?")):
            mensaje = mensaje + "."
        def _cap_first_alpha(m):
            return m.group(1) + m.group(2).upper()
        mensaje = _re.sub(r"^([^A-Za-zÁÉÍÓÚÑáéíóúñ]*)([A-Za-zÁÉÍÓÚÑáéíóúñ])", _cap_first_alpha, mensaje, count=1)

        mensaje_completo = f"{timestamp} - {icono} {mensaje}"
        self.texto_log.append(mensaje_completo)

        # Auto-scroll al final
        scrollbar = self.texto_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ========= ACTUALIZACION DE CONFIGURACION =========
    def actualizar_configuracion_grupos(self, grupos_data):
        """Actualizar configuración de grupos en el sistema principal"""
        try:
            # Verificar si es una cancelación de cambios
            if isinstance(grupos_data, dict) and "metadata" in grupos_data:
                metadata = grupos_data["metadata"]
                if metadata.get("accion") == "CANCELAR_CAMBIOS":
                    # Restaurar datos originales desde metadata
                    datos_grupos = grupos_data.get("grupos", {})
                    self.log_mensaje("🔄 Restaurando configuración original de grupos", "warning")
                else:
                    # Datos normales con metadata
                    datos_grupos = grupos_data.get("grupos", grupos_data)
            else:
                # CASO NORMAL: Datos directos de grupos SIN metadata
                datos_grupos = grupos_data

            # Validar datos recibidos del módulo
            self.log_mensaje(f"📥 Recibiendo datos de grupos: {len(datos_grupos)} elementos", "info")

            # Actualizar configuración interna
            if "grupos" not in self.configuracion["configuracion"]:
                self.configuracion["configuracion"]["grupos"] = {}

            grupos_config = self.configuracion["configuracion"]["grupos"]

            grupos_config["configurado"] = True if datos_grupos else False
            grupos_config["datos"] = datos_grupos
            grupos_config["total"] = len(datos_grupos)
            grupos_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Persistir configuración en archivo JSON
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            total = len(datos_grupos)
            if isinstance(grupos_data, dict) and grupos_data.get("metadata", {}).get("accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de grupos restaurada: {total} grupos",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de grupos actualizada: {total} grupos guardados en JSON",
                    "success"
                )

            # Actualizar estado visual
            self.actualizar_estado_visual()

        except Exception as e:
            error_msg = f"Error al actualizar configuración de grupos: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def actualizar_configuracion_calendario(self, calendario_data):
        """Actualizar configuración de calendario en el sistema principal"""
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
            calendario_config["total"] = total_dias
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
            asignaturas_data = datos_horarios.get("asignaturas", {})
            metadata = datos_horarios.get("metadata", {})

            if not asignaturas_data:
                self.log_mensaje("⚠️ No se recibieron datos de horarios para guardar", "warning")
                return

            # Totales desde metadata…
            total_franjas = metadata.get("total_franjas", 0)
            total_asignaturas = metadata.get("total_asignaturas", 0)

            # …y fallback robusto si vienen en 0 o faltan
            if not total_franjas or not total_asignaturas:
                def _contar(asigs):
                    tf = 0
                    for _, asig_data in asigs.items():
                        grid = asig_data.get("horarios_grid", {})
                        for _, dias in grid.items():
                            for _, entry in dias.items():
                                grupos = entry.get("grupos", []) if isinstance(entry, dict) else entry
                                if isinstance(grupos, list) and grupos:
                                    tf += 1
                    return tf

                # Recalcular
                total_asignaturas = sum(len(a) for a in asignaturas_data.values())
                total_franjas = sum(_contar(asignaturas_data.get(sem, {})) for sem in asignaturas_data.keys())

                # Inyectar los totales corregidos
                metadata["total_asignaturas"] = total_asignaturas
                metadata["total_franjas"] = total_franjas

            # Persistir en config
            self.configuracion["configuracion"]["horarios"] = {
                "configurado": True,
                "datos": asignaturas_data,
                "archivo": "horarios_integrados.json",
                "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                "semestre_actual": datos_horarios.get("semestre_actual", "2"),
                "total_asignaturas": total_asignaturas,
                "total_franjas": total_franjas,
                "total": total_franjas
            }

            self.configuracion["metadata"]["timestamp"] = datetime.now().isoformat()
            self.guardar_configuracion()
            self.actualizar_estado_visual()

            semestre = datos_horarios.get("semestre_actual", "?")
            self.log_mensaje(
                f"✅ Horarios integrados: S{semestre}, {total_asignaturas} asignaturas, {total_franjas} franjas",
                "success"
            )

        except Exception as e:
            error_msg = f"Error integrando horarios: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error de Integración",
                f"{error_msg}\n\nPor favor, intenta guardar manualmente."
            )

    def actualizar_configuracion_aulas(self, aulas_data):
        """Actualizar configuración de aulas en el sistema principal"""
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

            # Calculo total aulas configuradas
            total_aulas_calculado = 0
            if isinstance(datos_aulas, dict):
                total_aulas_calculado = len(datos_aulas)
            elif isinstance(datos_aulas, list):
                total_aulas_calculado = len(datos_aulas)
            else:
                total_aulas_calculado = 0

            # Actualizar configuración interna
            aulas_config = self.configuracion["configuracion"]["aulas"]

            aulas_config["configurado"] = True if total_aulas_calculado > 0 else False
            aulas_config["datos"] = datos_aulas
            aulas_config["total_aulas"] = total_aulas_calculado
            aulas_config["total"] = total_aulas_calculado
            aulas_config["fecha_actualizacion"] = datetime.now().isoformat()

            # Guardar configuración
            self.guardar_configuracion()

            # Log apropiado según el tipo de actualización
            if isinstance(aulas_data, dict) and aulas_data.get("metadata", {}).get("accion") == "CANCELAR_CAMBIOS":
                self.log_mensaje(
                    f"🔄 Configuración de aulas restaurada: {total_aulas_calculado} laboratorios",
                    "warning"
                )
            else:
                self.log_mensaje(
                    f"✅ Configuración de aulas actualizada: {total_aulas_calculado} laboratorios guardados",
                    "success"
                )

            # Actualizar estado visual
            self.actualizar_estado_visual()

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
    def abrir_configurar_grupos(self):
        """Abrir ventana de configuración de grupos - Estilo idéntico a asignaturas"""
        try:
            from modules.interfaces.configurar_grupos import ConfigurarGrupos
            GRUPOS_DISPONIBLE = True
        except ImportError as e:
            print(f"⚠️ Módulo configurar_grupos no disponible: {e}")
            GRUPOS_DISPONIBLE = False

        if not GRUPOS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_grupos.py no está disponible.\n"
                "Verifica que esté en la misma carpeta que gui_labs.py"
            )
            return

        self.log_mensaje("🎓 Abriendo configuración de grupos...", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_grupos') and self.ventana_grupos:
                self.ventana_grupos.close()

            # PREPARAR DATOS EXISTENTES PARA PASAR A LA VENTANA
            datos_existentes = None
            grupos_config = self.configuracion["configuracion"].get("grupos", {})

            if grupos_config.get("configurado") and grupos_config.get("datos"):
                datos_existentes = grupos_config["datos"].copy()
                total_grupos = grupos_config.get("total", 0)
                self.log_mensaje(
                    f"📥 Cargando configuración existente: {total_grupos} grupos configurados",
                    "info"
                )
            else:
                self.log_mensaje("📝 Abriendo configuración nueva de grupos", "info")

            # Crear ventana con datos existentes (o None si no hay)
            self.ventana_grupos = ConfigurarGrupos(
                parent=self,
                datos_existentes=datos_existentes
            )

            # Conectar señal para recibir configuración actualizada
            self.ventana_grupos.configuracion_actualizada.connect(self.actualizar_configuracion_grupos)

            self.ventana_grupos.show()

            if datos_existentes:
                self.log_mensaje("✅ Ventana de grupos abierta con datos existentes", "success")
            else:
                self.log_mensaje("✅ Ventana de grupos abierta (configuración nueva)", "success")

        except Exception as e:
            error_msg = f"Error al abrir configuración de grupos: {str(e)}"
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
                    "semestre_actual": horarios_config.get("semestre_actual", "1"),
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
                datos_existentes=datos_existentes  # Transferir configuración existente
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
                datos_existentes=datos_existentes  # Transferir configuración existente
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
        """Abrir ventana para visualizar restricciones duras y blandas (solo lectura)."""

        try:
            from modules.interfaces.configurar_parametros import ConfigurarParametrosWindow
            CONFIGURAR_PARAMETROS_DISPONIBLE = True
        except ImportError:
            CONFIGURAR_PARAMETROS_DISPONIBLE = False

        if not CONFIGURAR_PARAMETROS_DISPONIBLE:
            QtWidgets.QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo configurar_parametros.py no está disponible.\n"
                "Verifica que esté en modules/interfaces/configurar_parametros.py"
            )
            return

        try:
            if hasattr(self, "ventana_parametros") and self.ventana_parametros:
                self.ventana_parametros.close()

            self.ventana_parametros = ConfigurarParametrosWindow(cfg_path=Path(self.config_file))
            self.ventana_parametros.show()
            self.log_mensaje("📖 Ventana de parámetros abierta (solo lectura)", "info")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           f"No se pudo abrir la visualización de parámetros:\n{e}")

    def abrir_ver_resultados(self):
        """Abrir ventana de visualización de resultados (lee el JSON directamente)."""
        # 1) Importar la ventana nueva
        try:
            from modules.interfaces.ver_resultados import VerResultadosWindow
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

        # 2) Comprobar si hay resultados marcados en el JSON
        resultados_disponibles = self.configuracion.get("resultados_organizacion", {}).get("datos_disponibles", False)

        if not resultados_disponibles:
            mensaje_sin_datos = (
                "📊 No hay resultados disponibles aún.\n\n"
                "Primero ejecuta la organización y después vuelve a abrir esta ventana.\n"
                "¿Quieres abrir la ventana con datos de ejemplo?"
            )
            reply = QtWidgets.QMessageBox.question(
                self, "Sin Resultados Disponibles", mensaje_sin_datos,
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                self.log_mensaje("ℹ️ Visualización de resultados cancelada - sin datos", "info")
                return
            self.log_mensaje("📝 Abriendo resultados con datos simulados (sin datos reales)", "info")

        self.log_mensaje("📊 Abriendo visualización de resultados.", "info")

        try:
            # Cerrar ventana anterior si existe
            if hasattr(self, 'ventana_resultados') and self.ventana_resultados:
                self.ventana_resultados.close()

            # Crear y mostrar la ventana (le pasamos la ruta del JSON por si cambia)
            self.ventana_resultados = VerResultadosWindow(cfg_path=Path(self.config_file))
            self.ventana_resultados.show()

            if resultados_disponibles:
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

    def _ejecutar_motor_organizacion(self):
        """Ejecuta el motor que vuelca resultados en el JSON."""
        try:
            # 1) Importar el motor
            try:
                from modules.organizador.motor_organizacion import run as ejecutar_motor
                MOTOR_DISPONIBLE = True
            except ImportError as e:
                self.log_mensaje(f"❌ Motor de organización no disponible: {e}", "error")
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    "El módulo motor_organizacion.py no está disponible.\n"
                    "Verifica que esté en modules/organizador/motor_organizacion.py"
                )
                return

            # 2) Verificación de configuración previa (tu método ya existe)
            if not self._verificar_configuracion_completa():
                return

            self.log_mensaje("🚀 Ejecutando motor de organización (JSON)...", "info")

            # 3) Deshabilitar interfaz y mostrar progreso indeterminado
            self._deshabilitar_interfaz_organizacion()
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # indeterminado

            # 4) Ejecutar el motor (bloqueante). Le pasamos la ruta del JSON.
            ejecutar_motor(self.config_file)

            # 5) Ocultar barra y restaurar interfaz
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setVisible(False)
            self._restaurar_interfaz_organizacion()

            # 6) Recargar config desde disco, refrescar estado y ofrecer abrir resultados
            self.configuracion = self.cargar_configuracion()
            self.actualizar_estado_visual()
            self.actualizar_resumen_configuracion()
            self.log_mensaje("✅ Organización completada y guardada en el JSON", "success")

            # Preguntar si quiere ver los resultados
            # self.abrir_ver_resultados()
            reply = QtWidgets.QMessageBox.question(
                self, "Organización Completada",
                "🎉 ¡Organización completada exitosamente!\n\n"
                "¿Quieres ver los resultados ahora?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )

            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.abrir_ver_resultados()

        except Exception as e:
            # Recuperación en caso de error
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setVisible(False)
            self._restaurar_interfaz_organizacion()

            error_msg = f"Error ejecutando motor de organización: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error de Ejecución",
                f"{error_msg}\n\nDetalles técnicos:\n{type(e).__name__}: {e}"
            )

    def _verificar_configuracion_completa(self) -> bool:
        """
        Verifica si la configuración básica está completa antes de ejecutar el motor.
        Comprueba los apartados imprescindibles: grupos, asignaturas, profesores, alumnos,
        aulas, calendario y horarios.

        Los parámetros de organización no se validan aquí, ya que se generan automáticamente
        en el motor como texto explicativo.
        """
        faltantes = []

        cfg = self.configuracion.get("configuracion", {})

        if not cfg.get("grupos", {}).get("datos"):
            faltantes.append("Grupos")
        if not cfg.get("asignaturas", {}).get("datos"):
            faltantes.append("Asignaturas")
        if not cfg.get("profesores", {}).get("datos"):
            faltantes.append("Profesores")
        if not cfg.get("alumnos", {}).get("datos"):
            faltantes.append("Alumnos")
        if not cfg.get("aulas", {}).get("datos"):
            faltantes.append("Aulas")
        if not cfg.get("calendario", {}).get("datos"):
            faltantes.append("Calendario")
        if not cfg.get("horarios", {}).get("datos"):
            faltantes.append("Horarios")

        if faltantes:
            mensaje = "No se puede iniciar la organización. Faltan configurar:\n\n"
            for f in faltantes:
                mensaje += f"• {f}\n"
            mensaje += "\nPor favor, completa todas las configuraciones antes de continuar."
            QtWidgets.QMessageBox.warning(self, "Configuración incompleta", mensaje)
            return False

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
    • Revisar que haya suficientes regrupos disponibles

    ¿Quieres revisar la configuración?
        """

        reply = QtWidgets.QMessageBox.question(
            self, "Error en Organización", mensaje_completo,
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # Abrir configuración de parámetros para revisar
            self.abrir_configurar_parametros()

    def exportar_configuracion(self):
        """Exportar configuración actual a archivo JSON"""
        try:
            # 1. VERIFICACIÓN DE DATOS PARA EXPORTAR
            # Verificar si existe al menos una configuración válida
            configuraciones_validas = 0
            for seccion_key, seccion_data in self.configuracion.get("configuracion", {}).items():
                if isinstance(seccion_data, dict) and seccion_data.get("configurado", False):
                    configuraciones_validas += 1

            # Si no hay configuraciones válidas, informar al usuario
            if configuraciones_validas == 0:
                QtWidgets.QMessageBox.information(
                    self, "Sin Datos para Exportar",
                    "❌ No hay configuraciones válidas para exportar.\n\n"
                    "Para exportar, necesitas configurar al menos uno de estos módulos:\n"
                    "• Grupos y asignaturas\n"
                    "• Profesores y alumnos\n"
                    "• Aulas y horarios\n"
                    "• Parámetros de organización\n\n"
                    "💡 Configura algún módulo y vuelve a intentar."
                )
                self.log_mensaje("⚠️ Exportación cancelada - sin configuraciones válidas", "warning")
                return

            # 2. DIÁLOGO PARA SELECCIONAR ARCHIVO DE DESTINO
            # Generar nombre sugerido con timestamp
            timestamp_archivo = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_sugerido = f"configuracion_optim_{timestamp_archivo}.json"

            archivo_destino, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "💾 Exportar Configuración OPTIM",
                os.path.join(self._downloads_dir(), nombre_sugerido),
                "Archivos JSON (*.json);;Todos los archivos (*.*)"
            )

            # Si el usuario cancela la selección, salir silenciosamente
            if not archivo_destino:
                self.log_mensaje("ℹ️ Exportación cancelada por el usuario", "info")
                return

            # 3. PREPARAR DATOS DE EXPORTACIÓN CON METADATA COMPLETA
            # Hacer copia profunda de la configuración actual
            datos_export = copy.deepcopy(self.configuracion)

            # Asegurar que existe la sección metadata
            if "metadata" not in datos_export:
                datos_export["metadata"] = {}

            # Añadir información de exportación
            datos_export["metadata"].update({
                "exportado_en": datetime.now().isoformat(),
                "version_optim": "1.0",
                "tipo_archivo": "configuracion_completa_optim",
                "archivo_origen": self.config_file,
                "usuario_exportacion": os.getenv('USERNAME', 'unknown')
            })

            # 4. CALCULAR ESTADÍSTICAS DETALLADAS PARA METADATA
            configuracion_stats = datos_export.get("configuracion", {})

            estadisticas_export = {
                "total_modulos_configurados": configuraciones_validas,
                "modulos_detalle": {
                    "grupos": configuracion_stats.get("grupos", {}).get("total", 0),
                    "asignaturas": configuracion_stats.get("asignaturas", {}).get("total", 0),
                    "profesores": configuracion_stats.get("profesores", {}).get("total", 0),
                    "alumnos": configuracion_stats.get("alumnos", {}).get("total", 0),
                    "aulas": configuracion_stats.get("aulas", {}).get("total_aulas", 0),
                    "horarios_configurado": configuracion_stats.get("horarios", {}).get("configurado", False),
                    "calendario_configurado": configuracion_stats.get("calendario", {}).get("configurado", False)
                },
                "resultados_disponibles": datos_export.get("resultados_organizacion", {}).get("datos_disponibles",
                                                                                              False)
            }

            # Añadir estadísticas a metadata
            datos_export["metadata"]["estadisticas_exportacion"] = estadisticas_export

            # 5. GUARDAR ARCHIVO JSON CON FORMATO LEGIBLE
            with open(archivo_destino, 'w', encoding='utf-8') as archivo_json:
                json.dump(datos_export, archivo_json, indent=2, ensure_ascii=False)

            # 6. LOGGING DE CONFIRMACIÓN
            nombre_archivo = os.path.basename(archivo_destino)
            self.log_mensaje(f"📤 Configuración exportada exitosamente a '{nombre_archivo}'", "success")

            # 7. MOSTRAR RESUMEN DETALLADO AL USUARIO
            stats = estadisticas_export
            modulos_detalle = stats["modulos_detalle"]

            mensaje_exito = f"""
        ✅ EXPORTACIÓN COMPLETADA EXITOSAMENTE

        📊 RESUMEN DE DATOS EXPORTADOS:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        📚 CONFIGURACIONES ACADÉMICAS:
           • Grupos: {modulos_detalle['grupos']} configurados
           • Asignaturas: {modulos_detalle['asignaturas']} configuradas  
           • Profesores: {modulos_detalle['profesores']} configurados
           • Alumnos: {modulos_detalle['alumnos']} configurados

        🏢 INFRAESTRUCTURA Y HORARIOS:
           • Aulas: {modulos_detalle['aulas']} configuradas
           • Horarios: {'✅ Configurado' if modulos_detalle['horarios_configurado'] else '❌ Sin configurar'}
           • Calendario: {'✅ Configurado' if modulos_detalle['calendario_configurado'] else '❌ Sin configurar'}

        📊 RESULTADOS:
           • Datos disponibles: {'✅ Sí' if stats['resultados_disponibles'] else '❌ No'}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        📁 Archivo guardado: {nombre_archivo}
        📂 Ubicación: {os.path.dirname(archivo_destino)}
        📅 Fecha exportación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

        💡 Este archivo puede ser importado en cualquier instalación de OPTIM.
                """

            QtWidgets.QMessageBox.information(
                self,
                "🎉 Exportación Exitosa",
                mensaje_exito
            )

        except PermissionError:
            # Error específico de permisos
            error_msg = "Sin permisos de escritura en la ubicación seleccionada"
            self.log_mensaje(f"❌ Error de permisos: {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self,
                "❌ Error de Permisos",
                f"{error_msg}\n\n"
                "Soluciones:\n"
                "• Selecciona una ubicación diferente\n"
                "• Ejecuta el programa como administrador\n"
                "• Verifica que la carpeta no esté protegida"
            )

        except FileNotFoundError:
            # Error de ruta no válida
            error_msg = "La ruta seleccionada no es válida o no existe"
            self.log_mensaje(f"❌ Error de ruta: {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self,
                "❌ Error de Ruta",
                f"{error_msg}\n\n"
                "Verifica que la carpeta de destino existe y es accesible."
            )

        except (TypeError, ValueError) as json_error:
            # Error específico de JSON
            error_msg = f"Error al serializar datos a JSON: {str(json_error)}"
            self.log_mensaje(f"❌ Error JSON: {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self,
                "❌ Error de Formato",
                f"{error_msg}\n\n"
                "Los datos contienen elementos que no se pueden convertir a JSON.\n"
                "Contacta con soporte técnico."
            )

        except Exception as e:
            # Error genérico con información detallada
            error_msg = f"Error inesperado durante la exportación: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self,
                "❌ Error de Exportación",
                f"{error_msg}\n\n"
                f"Tipo de error: {type(e).__name__}\n"
                f"Detalles técnicos: {e}\n\n"
                "Si el problema persiste, contacta con soporte técnico."
            )

    def importar_configuracion(self):
        """Importar configuración desde archivo JSON"""
        try:
            # Advertencia sobre sobrescritura
            if any(config.get("configurado", False) for config in self.configuracion["configuracion"].values()):
                respuesta = QtWidgets.QMessageBox.question(
                    self, "Confirmar Importación",
                    "⚠️ Hay configuraciones existentes que se sobrescribirán.\n\n"
                    "¿Continuar con la importación?\n\n"
                    "💡 Tip: Exporta la configuración actual antes de importar.",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
                )

                if respuesta == QtWidgets.QMessageBox.StandardButton.No:
                    return

            # Diálogo para seleccionar archivo
            archivo, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Importar Configuración OPTIM",
                self._downloads_dir(), "Archivos JSON (*.json);;Todos los archivos (*)"
            )

            if not archivo:
                return

            # Cargar y validar archivo
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_importados = json.load(f)

            # Validar estructura del archivo
            if not isinstance(datos_importados, dict):
                raise ValueError("El archivo no contiene una configuración válida")

            # Verificar que es un archivo de configuración OPTIM
            if "configuracion" not in datos_importados:
                raise ValueError("El archivo no es una configuración OPTIM válida")

            # Respaldar configuración actual
            configuracion_backup = self.configuracion.copy()

            try:
                # Importar configuración manteniendo estructura
                self.configuracion = datos_importados

                # Asegurar que metadata existe
                if "metadata" not in self.configuracion:
                    self.configuracion["metadata"] = {
                        "version": "1.0",
                        "timestamp": datetime.now().isoformat()
                    }

                # Actualizar timestamp de importación
                self.configuracion["metadata"]["importado_en"] = datetime.now().isoformat()
                self.configuracion["metadata"]["importado_desde"] = os.path.basename(archivo)

                # Guardar configuración importada
                self.guardar_configuracion()

                # Actualizar interfaz
                self.actualizar_estado_visual()

                # Estadísticas de importación
                stats_import = datos_importados.get("metadata", {}).get("estadisticas", {})
                modulos_importados = sum(
                    1 for config in self.configuracion["configuracion"].values() if config.get("configurado", False))

                self.log_mensaje(f"📥 Configuración importada desde {os.path.basename(archivo)}", "success")

                # Mostrar resumen de importación
                mensaje_resumen = f"✅ Configuración importada exitosamente\n\n"
                mensaje_resumen += f"📊 Resumen importado:\n"
                mensaje_resumen += f"• {modulos_importados} módulos configurados\n"

                if stats_import:
                    mensaje_resumen += f"• {stats_import.get('total_profesores', 0)} profesores\n"
                    mensaje_resumen += f"• {stats_import.get('total_alumnos', 0)} alumnos\n"
                    mensaje_resumen += f"• {stats_import.get('total_aulas', 0)} aulas\n"

                mensaje_resumen += f"\n📁 Desde: {os.path.basename(archivo)}\n\n"
                mensaje_resumen += "🔄 El sistema ha sido actualizado con la nueva configuración."

                QtWidgets.QMessageBox.information(self, "Importación Exitosa", mensaje_resumen)

            except Exception as e_inner:
                # Restaurar backup en caso de error
                self.configuracion = configuracion_backup
                raise e_inner

        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                "El archivo seleccionado no existe o no se puede acceder."
            )
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                "El archivo seleccionado no es un JSON válido."
            )
        except Exception as e:
            error_msg = f"Error al importar configuración: {str(e)}"
            self.log_mensaje(f"❌ {error_msg}", "error")
            QtWidgets.QMessageBox.critical(
                self, "Error de Importación",
                f"{error_msg}\n\nVerifica que el archivo sea una configuración OPTIM válida."
            )

    def guardar_configuracion(self):
        """Guardar configuración actual"""
        try:
            self.configuracion["metadata"]["timestamp"] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configuracion, f, indent=2, ensure_ascii=False)
            self.log_mensaje(f"✅ Configuración guardada en {self.config_file}", "success")
        except Exception as e:
            self.log_mensaje(f"❌ Error guardando configuración: {e}", "error")

    def reset_configuracion(self):
        """Reset completo de configuración"""
        reply = QtWidgets.QMessageBox.question(
            self, "Reset Configuración",
            "¿Estás seguro de que quieres resetear toda la configuración?\n\n"
            "Se eliminarán todos los datos configurados y se volverá al estado inicial.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                # Eliminar archivo de configuración si existe
                if os.path.exists(self.config_file):
                    os.remove(self.config_file)

                # Regenerar configuración por defecto
                self.configuracion = self.cargar_configuracion()

                # Cerrar todas las ventanas abiertas
                if hasattr(self, 'ventana_horarios') and self.ventana_horarios:
                    self.ventana_horarios.close()
                    self.ventana_horarios = None
                if hasattr(self, 'ventana_calendario') and self.ventana_calendario:
                    self.ventana_calendario.close()
                    self.ventana_calendario = None
                if hasattr(self, 'ventana_alumnos') and self.ventana_alumnos:
                    self.ventana_alumnos.close()
                    self.ventana_alumnos = None
                if hasattr(self, 'ventana_profesores') and self.ventana_profesores:
                    self.ventana_profesores.close()
                    self.ventana_profesores = None
                if hasattr(self, 'ventana_aulas') and self.ventana_aulas:
                    self.ventana_aulas.close()
                    self.ventana_aulas = None
                if hasattr(self, 'ventana_resultados') and self.ventana_resultados:
                    self.ventana_resultados.close()
                    self.ventana_resultados = None

                # Forzar actualización completa de la interfaz
                self.actualizar_estado_visual()
                self.actualizar_resumen_configuracion()

                # Log de confirmación
                self.log_mensaje("🔄 Configuración reseteada completamente - sistema reiniciado", "success")

                # Mensaje de confirmación
                QtWidgets.QMessageBox.information(
                    self, "Reset Completado",
                    "✅ Configuración reseteada correctamente.\n\nTodas las ventanas han sido cerradas y el sistema vuelve al estado inicial."
                )

            except Exception as e:
                self.log_mensaje(f"❌ Error durante reset: {e}", "error")
                QtWidgets.QMessageBox.critical(
                    self, "Error de Reset",
                    f"Error durante el reset:\n{str(e)}\n\nIntenta cerrar manualmente las ventanas abiertas."
                )

    def mostrar_ayuda(self):
        """Mostrar ayuda y soporte"""
        QtWidgets.QMessageBox.information(
            self, "Ayuda - OPTIM",
            "OPTIM - Sistema de Programación de Laboratorios\n\n"
            "Flujo recomendado:\n"
            "1️⃣ Configurar Grupos\n"
            "2️⃣ Configurar Asignaturas\n"
            "3️⃣ Configurar Profesores\n"
            "4️⃣ Configurar Alumnos matriculados\n"
            "7️⃣ Configurar Aulas/Laboratorios\n"
            "5️⃣ Configurar Calendario semestral\n"
            "6️⃣ Organizar Horarios por asignatura\n\n"
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
    app.setApplicationName("OPTIM by SoftVier")
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