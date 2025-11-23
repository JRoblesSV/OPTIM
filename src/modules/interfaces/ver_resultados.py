
"""
Ver Resultados - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

from __future__ import annotations
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTreeWidget, QTreeWidgetItem, QSplitter,
    QPushButton, QFileDialog, QMessageBox, QStatusBar, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet


# ========= Utilidades de Ordenación y Normalización =========
DAY_ORDER = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Miercoles": 2, "Jueves": 3, "Viernes": 4,
    "Sábado": 5, "Sabado": 5, "Domingo": 6
}


def normalize_time_range(rng: str) -> str:
    """Normaliza rangos horarios al formato HH:MM-HH:MM"""
    s = (rng or "").strip()
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$", s)
    if not m:
        return s
    h1, m1, h2, m2 = map(int, m.groups())
    return f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"


def time_start_in_minutes(franja_norm: str) -> int:
    """Extrae la hora de inicio en minutos desde medianoche de una franja horaria normalizada"""
    m = re.match(r"^(\d{2}):(\d{2})-\d{2}:\d{2}$", (franja_norm or "").strip())
    if not m:
        return 0
    h, mi = int(m.group(1)), int(m.group(2))
    return h * 60 + mi


def sort_ddmmyyyy_asc(lst: List[str]) -> List[str]:
    """Ordena lista de fechas en formato DD/MM/YYYY de forma ascendente"""
    def key_fun(s: str):
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", (s or "").strip())
        if not m:
            # tratar YYYY-MM-DD como fallback ordenable
            m2 = re.match(r"^(\d{4})-(\d{2})-(\d{2})", (s or "").strip())
            if m2:
                y, mo, d = map(int, m2.groups())
                return (y, mo, d)
            return (9999, 99, 99)
        d, mo, y = map(int, m.groups())
        return (y, mo, d)
    return sorted(lst, key=key_fun)


# ========= Formateo de Fechas =========
_ddmmyyyy_re = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_y_m_d_re    = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_d_m_y_dash  = re.compile(r"\b(\d{2})-(\d{2})-(\d{4})\b")


def any_to_ddmmyyyy(value: str) -> str:
    """Convierte cualquier formato de fecha a DD/MM/YYYY"""
    s = str(value or "").strip()
    if not s:
        return ""
    # Caso 1: ya viene DD/MM/YYYY
    m = _ddmmyyyy_re.search(s)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    # Caso 2: YYYY-MM-DD (o substring ISO 8601)
    m = _y_m_d_re.search(s)
    if m:
        y, mo, d = m.groups()
        return f"{d}/{mo}/{y}"
    # Caso 3: DD-MM-YYYY
    m = _d_m_y_dash.search(s)
    if m:
        d, mo, y = m.groups()
        return f"{d}/{mo}/{y}"
    # Caso 4: ISO con tiempo: 2025-09-15T18:43:26...
    iso = re.search(r"(\d{4}-\d{2}-\d{2})T", s)
    if iso:
        y, mo, d = iso.group(1).split("-")
        return f"{d}/{mo}/{y}"
    # Caso 5: nada reconocible, devolver original
    return s


def dates_list_any_to_ddmmyyyy(values: Any) -> str:
    """Convierte una lista de fechas a formato DD/MM/YYYY separadas por comas"""
    if isinstance(values, list):
        out = [any_to_ddmmyyyy(v) for v in values]
        return ", ".join([v for v in out if v])
    return any_to_ddmmyyyy(str(values or ""))


# ========= Utilidades de Sistema y Configuración =========
def apply_dark_palette(app: QApplication) -> None:
    """Aplica tema oscuro"""
    app.setStyle("Fusion")
    palette = QPalette()
    base = QColor(30, 30, 30)
    alt_base = QColor(45, 45, 45)
    text = QColor(220, 220, 220)
    disabled_text = QColor(127, 127, 127)
    button = QColor(53, 53, 53)
    highlight = QColor(42, 130, 218)

    palette.setColor(QPalette.ColorRole.Window, base)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, alt_base)
    palette.setColor(QPalette.ColorRole.AlternateBase, base)
    palette.setColor(QPalette.ColorRole.ToolTipBase, text)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, highlight)

    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    # Disabled
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)

    app.setPalette(palette)


def default_config_path() -> Path:
    """Obtiene la ruta por defecto al archivo de configuración configuracion_labs.json"""
    return Path(__file__).resolve().parents[2] / "configuracion_labs.json"


def load_config(path: Path) -> Dict[str, Any]:
    """Carga y parsea el archivo JSON de configuración"""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def downloads_dir() -> Path:
    """Obtiene la ruta del directorio de Descargas del usuario"""
    home = Path.home()
    for name in ("Descargas", "Downloads"):
        p = home / name
        if p.exists() and p.is_dir():
            return p
    return home


# ========= Helpers de Lógica de Datos =========
def get_group_type(al: Dict[str, Any], grupo_simple: str, grupo_doble: str) -> str:
    """Determina el tipo de grupo (simple o doble) en el que está matriculado el alumno"""
    grupos_m = al.get("grupos_matriculado", []) or []
    if grupo_simple and grupo_simple in grupos_m:
        return grupo_simple
    if grupo_doble and grupo_doble in grupos_m:
        return grupo_doble
    return grupos_m[0] if grupos_m else ""


def semesters_in_results(res: Dict[str, Any]) -> List[str]:
    """Extrae y ordena naturalmente los semestres presentes en los resultados"""
    out = [k for k in res.keys() if k.startswith("semestre_")]
    # orden natural: semestre_1, semestre_2
    def kf(k: str) -> int:
        m = re.search(r"(\d+)$", k)
        return int(m.group(1)) if m else 999
    return sorted(out, key=kf)


def like(text: str, needle: str) -> bool:
    """Realiza búsqueda insensible a mayúsculas/minúsculas (filtrado LIKE SQL)"""
    if not needle:
        return True
    return (text or "").lower().__contains__((needle or "").lower().strip())


# ========= Diálogo de Conflictos =========
class ConflictsDialog(QDialog):
    """Diálogo para visualizar detalladamente los conflictos de asignación en estructura de árbol"""
    def __init__(self, parent: QWidget, res: Dict[str, Any]):
        super().__init__(parent)
        self.setWindowTitle("Conflictos de organización")
        self.resize(1000, 520)
        layout = QVBoxLayout(self)

        # Item ordenable con clave de orden
        class SortableItem(QTableWidgetItem):
            def __init__(self, display: str, sort_key: Any = None):
                super().__init__(str(display))
                self._key = sort_key if sort_key is not None else str(display).lower()

        # Funciones auxiliares para claves de ordenación
        def semestre_key(s: str) -> tuple:
            m = re.search(r"(\d+)$", str(s))
            return (int(m.group(1)) if m else 999, str(s).lower())

        def dia_key(d: str) -> tuple:
            return (DAY_ORDER.get(str(d), 99), str(d).lower())

        def fecha_key(s: str) -> tuple:
            # admite "DD/MM/YYYY", "YYYY-MM-DD", o lista separada por comas
            txt = (s or "").split(",")[0].strip()
            ddmmyyyy = any_to_ddmmyyyy(txt)
            m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", ddmmyyyy)
            if m:
                d, mo, y = map(int, m.groups())
                return (y, mo, d)
            # fallback grande para que lo desconocido vaya al final
            return (9999, 99, 99)

        def franja_key(rng: str) -> tuple:
            norm = normalize_time_range(rng or "")
            return (time_start_in_minutes(norm), norm)

        def text_key(s: str) -> str:
            return (s or "").lower().strip()

        tabs: List[Tuple[str, List[Dict[str, Any]]]] = []
        confs = res.get("conflictos", {}) or {}
        tabs.append(("Profesores", confs.get("profesores") or []))
        tabs.append(("Aulas", confs.get("aulas") or []))

        alumnos_rows: List[Dict[str, Any]] = []
        for msg in (confs.get("alumnos") or []):
            if isinstance(msg, dict):
                alumnos_rows.append({
                    "semestre": msg.get("semestre", "-") or "-",
                    "asignatura": msg.get("asignatura", "-") or "-",
                    "grupo": msg.get("grupo", "-") or "-",
                    "dia": msg.get("dia", "-") or "-",
                    "fecha": msg.get("fecha", "-") or "-",
                    "franja": msg.get("franja", "-") or "-",
                    "detalle": msg.get("detalle", "") or "",
                    "aula": msg.get("aula", "-") or "-",
                    "profesor": msg.get("profesor", "-") or "-",
                })

        tabs.append(("Alumnos", alumnos_rows))

        for title, rows in tabs:
            label = QLabel(f" {title} ({len(rows)})")
            layout.addWidget(label)

            table = QTableWidget(self)
            headers = ["semestre", "asignatura", "grupo", "dia", "fecha", "franja", "detalle", "aula", "profesor"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            hdr = table.horizontalHeader()
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # permitir arrastrar para ancho/estrecho
            hdr.setStretchLastSection(False)  # sin estirar forzado del último
            hdr.setSectionsMovable(True)  # permite reordenar columnas

            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setSortingEnabled(False)

            for r, row in enumerate(rows):
                table.insertRow(r)

                # Normalización robusta de valores (compatibilidad con versiones anteriores)
                dia_val = row.get("dia", row.get("dia/fecha", "")) or ""

                # fecha puede venir como 'fecha', 'dia/fecha' o 'fechas' (lista)
                fecha_val = row.get("fecha")
                if fecha_val:
                    fecha_val = any_to_ddmmyyyy(str(fecha_val))
                else:
                    alt = row.get("dia/fecha")
                    if alt:
                        fecha_val = any_to_ddmmyyyy(str(alt))
                    else:
                        f_list = row.get("fechas") or []
                        fecha_val = dates_list_any_to_ddmmyyyy(f_list)

                aula_val = row.get("aula") or row.get("aula_nombre") or row.get("sala") or "—"
                prof_val = row.get("profesor") or row.get("docente") or row.get("profesor_apellidos") or "—"
                franja_val = normalize_time_range(row.get("franja", "") or "")

                # Mapa de valores y sus claves de orden
                values = {
                    "semestre": (row.get("semestre", ""), semestre_key(row.get("semestre", ""))),
                    "asignatura": (row.get("asignatura", ""), text_key(row.get("asignatura", ""))),
                    "grupo": (row.get("grupo", ""), text_key(row.get("grupo", ""))),
                    "dia": (dia_val, dia_key(dia_val)),
                    "fecha": (fecha_val, fecha_key(fecha_val)),
                    "franja": (franja_val, franja_key(franja_val)),
                    "detalle": (row.get("detalle", ""), text_key(row.get("detalle", ""))),
                    "aula": (aula_val, text_key(aula_val)),
                    "profesor": (prof_val, text_key(prof_val)),
                }

                for c, key in enumerate(headers):
                    display, skey = values[key]
                    item = SortableItem(display, skey)
                    table.setItem(r, c, item)

            # Activar orden por encabezado
            table.setSortingEnabled(True)

            layout.addWidget(table)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


# ========= Ventana Principal =========
class VerResultadosWindow(QMainWindow):
    """Ventana principal para visualizar y gestionar resultados de organización de laboratorios"""
    def __init__(self, cfg_path: Optional[Path] = None):
        super().__init__()
        self.setWindowTitle("Resultados de Organización - OPTIM")
        self.resize(1300, 800)

        self.cfg_path = cfg_path or default_config_path()
        self.cfg: Dict[str, Any] = {}
        self.res: Dict[str, Any] = {}
        self.alumnos: Dict[str, Any] = {}

        # filtros (aplican solo cuando se pulsa el botón Filtrar)
        self.filter_alumno_exp: str = ""
        self.filter_prof_apell: str = ""

        # para popup de conflictos solo una vez
        self._conflict_warned: bool = False

        self.setup_ui()
        self.load_and_render()

    # ========= CONFIGURACIÓN DE UI =========
    def setup_ui(self) -> None:
        """Construye la interfaz gráfica con controles de filtrado y vista de árbol"""
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Barra superior (filtros de semestre/asignatura + acciones)
        top1 = QHBoxLayout()
        self.cmb_semestre = QComboBox()
        self.cmb_asignatura = QComboBox()
        self.cmb_semestre.setMinimumWidth(160)
        self.cmb_asignatura.setMinimumWidth(220)

        self.btn_reload = QPushButton("Recargar")
        self.btn_export = QPushButton("Exportar PDF")
        self.btn_conflicts = QPushButton("Ver conflictos")

        top1.addWidget(QLabel("Semestre:"))
        top1.addWidget(self.cmb_semestre)
        top1.addSpacing(10)
        top1.addWidget(QLabel("Asignatura:"))
        top1.addWidget(self.cmb_asignatura)
        top1.addStretch(1)
        top1.addWidget(self.btn_conflicts)
        top1.addSpacing(8)
        top1.addWidget(self.btn_export)
        top1.addSpacing(8)
        top1.addWidget(self.btn_reload)

        # Barra de filtros textuales (alumno/profesor) + botón Filtrar
        top2 = QHBoxLayout()
        self.txt_filter_alumno = QLineEdit()
        self.txt_filter_alumno.setPlaceholderText("Alumno (expediente centro)...")
        self.txt_filter_alumno.setClearButtonEnabled(True)
        self.txt_filter_alumno.setMinimumWidth(220)

        self.txt_filter_prof = QLineEdit()
        self.txt_filter_prof.setPlaceholderText("Profesor (apellidos)...")
        self.txt_filter_prof.setClearButtonEnabled(True)
        self.txt_filter_prof.setMinimumWidth(220)

        self.btn_apply_filters = QPushButton("Filtrar")

        top2.addWidget(QLabel("Filtro:"))
        top2.addWidget(self.txt_filter_alumno)
        top2.addSpacing(10)
        top2.addWidget(self.txt_filter_prof)
        top2.addSpacing(10)
        top2.addWidget(self.btn_apply_filters)
        top2.addStretch(1)

        # Árbol resultados
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Elemento", "Detalles"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        #self.txt_params = QPlainTextEdit()
        #self.txt_params.setReadOnly(True)
        #self.txt_params.setPlaceholderText("Parámetros de organización (restricciones duras y blandas)")

        splitter.addWidget(self.tree)
        #splitter.addWidget(self.txt_params)
        #splitter.setSizes([950, 350])


        root.addLayout(top1)
        root.addLayout(top2)
        root.addWidget(splitter)

        self.setCentralWidget(central)

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)

        # Señales
        self.btn_reload.clicked.connect(self.load_and_render)
        self.cmb_semestre.currentIndexChanged.connect(self.on_semestre_changed)
        self.cmb_asignatura.currentIndexChanged.connect(self.populate_tree)
        self.btn_export.clicked.connect(self.export_pdf)
        self.btn_conflicts.clicked.connect(self.show_conflicts)
        self.btn_apply_filters.clicked.connect(self.on_apply_filters_clicked)

        # Atajos / Acciones (opcional)
        act_reload = QAction("Recargar", self)
        act_reload.setShortcut("F5")
        act_reload.triggered.connect(self.load_and_render)
        self.addAction(act_reload)

    # ========= FILTROS Y BÚSQUEDA =========
    def filter_group_and_students(self, ginfo: Dict[str, Any]) -> Tuple[bool, List[Tuple[str, Dict[str, Any]]]]:
        """Aplica filtros de semestre, asignatura y búsqueda a un grupo y sus alumnos"""
        alumnos_ids = ginfo.get("alumnos", []) or []
        profesor_txt = ginfo.get("profesor", "") or ""
        # filtro profesor (apellidos LIKE sobre el texto completo del campo profesor)
        if self.filter_prof_apell and not like(profesor_txt, self.filter_prof_apell):
            return False, []

        # filtro alumno por expediente
        out_alumnos: List[Tuple[str, Dict[str, Any]]] = []
        if self.filter_alumno_exp:
            for sid in alumnos_ids:
                al = self.alumnos.get(sid, {}) or {}
                exp = str(al.get("exp_centro", "") or "").strip()
                if like(exp, self.filter_alumno_exp):
                    out_alumnos.append((sid, al))
            if not out_alumnos:
                return False, []
        else:
            for sid in alumnos_ids:
                out_alumnos.append((sid, self.alumnos.get(sid, {}) or {}))

        return True, out_alumnos

    def on_apply_filters_clicked(self) -> None:
        """Captura los filtros textuales y recarga el árbol"""
        self.filter_alumno_exp = (self.txt_filter_alumno.text() or "").strip()
        self.filter_prof_apell = (self.txt_filter_prof.text() or "").strip()
        self.populate_tree()

    # ========= CARGA DE DATOS =========
    def load_and_render(self) -> None:
        """Carga JSON, actualiza combos y árbol, muestra conflictos detectados"""
        self.filter_alumno_exp = ""
        self.filter_prof_apell = ""
        self.txt_filter_alumno.clear()
        self.txt_filter_prof.clear()

        try:
            self.cfg = load_config(self.cfg_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el JSON:\n{self.cfg_path}\n\n{e}")
            return

        self.res = self.cfg.get("resultados_organizacion", {}) or {}
        self.alumnos = (self.cfg.get("configuracion", {})
                           .get("alumnos", {})
                           .get("datos", {}) or {})

        # Top info
        meta = self.res.get("_metadata", {})
        when = meta.get("ultima_ejecucion", "—")
        ver = meta.get("version", "—")
        self.statusBar().showMessage(f"JSON: {self.cfg_path} | Ejecutado: {when} | Motor: {ver}")

        # Parámetros
        #params = self.cfg.get("parametros_organizacion", {}) or {}
        #duras = params.get("restricciones_duras", []) or []
        #blandas = params.get("restricciones_blandas", []) or []
        #ptxt = ["Restricciones duras:"]
        #ptxt += [f"  • {x}" for x in duras]
        #ptxt += ["", "Restricciones blandas:"]
        #ptxt += [f"  • {x}" for x in blandas]
        #self.txt_params.setPlainText("\n".join(ptxt))

        # Combos
        self.populate_semestres_y_asignaturas()
        # Árbol
        self.populate_tree()

        # Popup inicial de conflictos (una vez)
        if not self._conflict_warned:
            confs = self.res.get("conflictos", {}) or {}
            c_prof = len(confs.get("profesores", []) or [])
            c_aulas = len(confs.get("aulas", []) or [])
            c_alum = len(confs.get("alumnos", []) or [])
            total = c_prof + c_aulas + c_alum
            if total > 0:
                self._conflict_warned = True
                mb = QMessageBox(self)
                mb.setIcon(QMessageBox.Icon.Warning)
                mb.setWindowTitle("Conflictos detectados")
                mb.setText(
                    f"Se han detectado {total} conflictos (Profesores: {c_prof} | Aulas: {c_aulas} | Alumnos: {c_alum}).")
                mb.setInformativeText("Revísalos para asegurar la planificación.")
                ver_btn = mb.addButton("Abrir conflictos", QMessageBox.ButtonRole.AcceptRole)
                mb.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
                mb.exec()
                if mb.clickedButton() is ver_btn:
                    self.show_conflicts()

    # ========= SEMESTRES Y ASIGNATURAS =========
    def populate_semestres_y_asignaturas(self) -> None:
        """Rellena el combo de semestres disponibles"""
        sems = semesters_in_results(self.res)
        self.cmb_semestre.blockSignals(True)
        self.cmb_asignatura.blockSignals(True)

        self.cmb_semestre.clear()
        self.cmb_semestre.addItem("Todos", userData=None)
        for s in sems:
            self.cmb_semestre.addItem(s, userData=s)

        # Asignaturas dependerán del semestre seleccionado
        self.fill_asignaturas_for_current_sem()

        self.cmb_semestre.blockSignals(False)
        self.cmb_asignatura.blockSignals(False)

    def fill_asignaturas_for_current_sem(self) -> None:
        """Rellena las asignaturas según el semestre seleccionado"""
        sel_sem = self.cmb_semestre.currentData()
        self.cmb_asignatura.clear()
        self.cmb_asignatura.addItem("Todas", userData=None)

        if sel_sem is None:
            # Cargar todas las asignaturas si no hay filtro de semestre
            seen = set()
            for s in semesters_in_results(self.res):
                for asig in (self.res.get(s) or {}).keys():
                    if asig.startswith("_"):
                        continue
                    if asig not in seen:
                        self.cmb_asignatura.addItem(asig, userData=asig)
                        seen.add(asig)
        else:
            for asig in (self.res.get(sel_sem) or {}).keys():
                if asig.startswith("_"):
                    continue
                self.cmb_asignatura.addItem(asig, userData=asig)

    def on_semestre_changed(self) -> None:
        """Actualiza asignaturas y recarga el árbol al cambiar semestre"""
        self.cmb_asignatura.blockSignals(True)
        self.fill_asignaturas_for_current_sem()
        self.cmb_asignatura.blockSignals(False)
        self.populate_tree()

    # ========= ÁRBOL DE RESULTADOS =========
    def populate_tree(self) -> None:
        """Construye árbol jerárquico de semestres → asignaturas → grupos → alumnos con filtros aplicados"""
        self.tree.clear()

        # Filtros de combos
        sel_sem = self.cmb_semestre.currentData()
        sel_asig = self.cmb_asignatura.currentData()

        def semesters_iter():
            if sel_sem is None:
                return semesters_in_results(self.res)
            return [sel_sem]

        total_grupos = 0
        total_alumnos = 0

        for sem in semesters_iter():
            sem_node = QTreeWidgetItem([f"{sem}", ""])
            self.tree.addTopLevelItem(sem_node)

            asignaturas = self.res.get(sem, {}) or {}
            # Filtrado de asignatura
            if sel_asig is not None:
                asignaturas = {k: v for k, v in asignaturas.items() if k == sel_asig}

            for asig, a_data in sorted(asignaturas.items(), key=lambda kv: kv[0]):
                if not isinstance(a_data, dict) or "grupos" not in a_data:
                    continue
                asig_node = QTreeWidgetItem([f"{asig}", ""])
                sem_node.addChild(asig_node)

                grupos = a_data.get("grupos", {}) or {}

                # Ordenar grupos por día+hora+label
                def gkey(item):
                    label, info = item
                    dia = info.get("dia", "")
                    franja = normalize_time_range(info.get("franja", "00:00-00:00"))
                    return (DAY_ORDER.get(dia, 99), time_start_in_minutes(franja), franja, label)

                for label, ginfo in sorted(grupos.items(), key=gkey):
                    pasa, alumnos_filtrados = self.filter_group_and_students(ginfo)
                    if not pasa:
                        continue

                    profesor = ginfo.get("profesor", "—")
                    aula = ginfo.get("aula", "—")
                    dia = ginfo.get("dia", "—")
                    franja = normalize_time_range(ginfo.get("franja", "—"))
                    fechas = [any_to_ddmmyyyy(f) for f in (ginfo.get("fechas", []) or [])]
                    fechas = sort_ddmmyyyy_asc(fechas)
                    capacidad = ginfo.get("capacidad", 0)
                    mixta = "Sí" if ginfo.get("mixta", False) else "No"

                    total_grupos += 1
                    total_alumnos += len(alumnos_filtrados)

                    letra = ginfo.get("letra", "")
                    det = (f"Día: {dia}  |  Franja: {franja}  |  Aula: {aula}  |  Prof: {profesor}  |  "
                           f"Mixta: {mixta}  |  Cap: {capacidad}  |  Alumnos: {len(alumnos_filtrados)}  |  "
                           f"Letra: {letra}")
                    g_node = QTreeWidgetItem([f"Grupo {label}", det])
                    asig_node.addChild(g_node)

                    # Fechas
                    f_node = QTreeWidgetItem(["Fechas", ", ".join(fechas) if fechas else "—"])
                    g_node.addChild(f_node)

                    # Alumnos
                    a_node = QTreeWidgetItem([f"Alumnos ({len(alumnos_filtrados)})", ""])
                    g_node.addChild(a_node)

                    grupo_simple = ginfo.get("grupo_simple", "")
                    grupo_doble = ginfo.get("grupo_doble", "")

                    for sid, al in alumnos_filtrados:
                        exp = str(al.get("exp_centro", "") or "").strip() or str(sid)
                        nombre = (al.get("nombre") or "").strip()
                        apell = (al.get("apellidos") or "").strip()
                        grupolab = get_group_type(al, grupo_simple, grupo_doble)
                        label_al = f"{exp} — {nombre} {apell}".strip()
                        info_al = f"Grupo: {grupolab}"
                        a_node.addChild(QTreeWidgetItem([label_al, info_al]))

            sem_node.setExpanded(True)

        self.tree.expandToDepth(2)
        confs = self.res.get("conflictos", {}) or {}
        c_prof = len(confs.get("profesores", []) or [])
        c_aulas = len(confs.get("aulas", []) or [])
        c_alum = len(confs.get("alumnos", []) or [])
        self.statusBar().showMessage(
            f"JSON: {self.cfg_path}  |  Grupos: {total_grupos}  |  Alumnos listados: {total_alumnos}  |  Conflictos -> Profesores: {c_prof}  |  Aulas: {c_aulas}  |  Alumnos: {c_alum}"
        )

    # ========= ACCIONES =========
    def show_conflicts(self) -> None:
        """Abre diálogo con conflictos detectados"""
        if not self.res:
            return
        dlg = ConflictsDialog(self, self.res)
        dlg.exec()

    def export_pdf(self) -> None:
        """Exporta resultados filtrados a PDF con tablas de alumnos"""
        # Sugerir ruta Descargas por defecto
        default_dir = str(downloads_dir())
        fname, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", str(Path(default_dir) / "resultados_organizacion.pdf"),
            "PDF (*.pdf)"
        )
        if not fname:
            return

        doc = SimpleDocTemplate(fname, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []

        # Aplicar todos los filtros activos (semestre, asignatura, alumno, profesor) al PDF
        sel_sem = self.cmb_semestre.currentData()
        sel_asig = self.cmb_asignatura.currentData()

        def semesters_iter():
            if sel_sem is None:
                return semesters_in_results(self.res)
            return [sel_sem]

        first_section = True

        for sem in semesters_iter():
            asignaturas = self.res.get(sem, {}) or {}
            if sel_asig is not None:
                asignaturas = {k: v for k, v in asignaturas.items() if k == sel_asig}

            for asig, a_data in sorted(asignaturas.items(), key=lambda kv: kv[0]):
                if not isinstance(a_data, dict) or "grupos" not in a_data:
                    continue

                grupos = a_data.get("grupos", {}) or {}

                # Orden por día + franja
                def gkey(item):
                    label, info = item
                    dia = info.get("dia", "")
                    franja = normalize_time_range(info.get("franja", "00:00-00:00"))
                    return (DAY_ORDER.get(dia, 99), time_start_in_minutes(franja), franja, label)

                any_group_printed = False

                for label, ginfo in sorted(grupos.items(), key=gkey):
                    pasa, alumnos_filtrados = self.filter_group_and_students(ginfo)
                    if not pasa:
                        continue

                    # Si hay filtro de alumno, solo imprimimos filas de esos alumnos
                    if self.filter_alumno_exp and len(alumnos_filtrados) == 0:
                        continue

                    # Encabezado de sección (una vez por sección con contenido)
                    if not any_group_printed:
                        if not first_section:
                            story.append(PageBreak())
                        story.append(Paragraph(f"<b>{sem} — {asig}</b>", styles["Title"]))
                        story.append(Spacer(1, 6))
                        first_section = False
                        any_group_printed = True

                    profesor = ginfo.get("profesor", "—")
                    aula = ginfo.get("aula", "—")
                    dia = ginfo.get("dia", "—")
                    franja = normalize_time_range(ginfo.get("franja", "—"))
                    fechas = [any_to_ddmmyyyy(f) for f in (ginfo.get("fechas", []) or [])]
                    fechas = sort_ddmmyyyy_asc(fechas)
                    grupo_simple = ginfo.get("grupo_simple", "")
                    grupo_doble = ginfo.get("grupo_doble", "")

                    story.append(Spacer(1, 4))
                    # story.append(Paragraph(f"<b>Grupo {label}</b>", styles["Heading2"]))
                    letra = ginfo.get("letra", "")
                    franja_inicio = franja.split("-")[0] if franja else ""

                    story.append(Paragraph(f"<b>Grupo {dia} {franja_inicio} {letra}</b>", styles["Heading2"]))
                    meta_line = f"Día: {dia} | Franja: {franja} | Aula: {aula} | Prof: {profesor}"

                    story.append(Paragraph(meta_line, styles["Normal"]))
                    if fechas:
                        story.append(Paragraph("Fechas: " + ", ".join(fechas), styles["Normal"]))
                    story.append(Spacer(1, 6))

                    # Tabla de alumnos (aplica filtro de alumno: solo los coincidentes)
                    data = [["Matrícula", "Nombre", "Apellidos", "Grupo"]]
                    for sid, al in alumnos_filtrados:
                        exp = str(al.get("exp_centro", "") or "").strip() or str(sid)
                        nombre = (al.get("nombre") or "").strip()
                        apell = (al.get("apellidos") or "").strip()
                        grupolab = get_group_type(al, grupo_simple, grupo_doble)
                        data.append([exp, nombre, apell, grupolab])

                    # Si no hay filas tras aplicar el filtro, omitir la tabla
                    if len(data) == 1:
                        continue

                    table = Table(data, repeatRows=1)
                    table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("TOPPADDING", (0, 1), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
                    ]))
                    story.append(table)

        if not story:
            QMessageBox.information(self, "Sin datos", "No hay datos que exportar con los filtros actuales.")
            return

        try:
            doc.build(story)
            QMessageBox.information(self, "Exportado", f"PDF generado correctamente en:\n{fname}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF:\n{e}")


# ========= main =========
def main():
    parser = argparse.ArgumentParser(description="Ver resultados de organización")
    parser.add_argument("--config", help="Ruta al configuracion_labs.json", default=None)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    apply_dark_palette(app)

    cfg_path = Path(args.config).resolve() if args.config else None
    win = VerResultadosWindow(cfg_path)
    win.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
