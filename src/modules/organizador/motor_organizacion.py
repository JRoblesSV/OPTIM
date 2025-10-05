#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planificador de laboratorios (intercalado por día+franja) — v3 (JSON-first)
Cambios clave:
- ❌ Se elimina la exportación a CSV (conflictos) y a PDF (plan).
- ✅ Todo se vuelca en /src/configuracion_labs.json:
    - "parametros_organizacion": restricciones duras y blandas aplicadas por el motor
    - "resultados_organizacion": { semestre -> asignatura -> grupos -> ... , conflictos, avisos, metadata }

Mantiene:
- Paridad DURA (todos pares; si total impar, solo 1 grupo impar).
- Asignación por FECHAS reales (no por semanas).
- Intercalado round-robin por (día, franja) entre grupos que comparten slot.
- Aulas alternativas si la preferente no está disponible.
- Respeto de fechas NO disponibles de profesores y aulas.
- Respeto de bloqueos de franja de profesores y días de trabajo.

Dependencias externas: ninguna (reportlab ya no es necesaria aquí).
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set

# ------------------------------
#   PATRONES Y ORDEN DE DÍAS
# ------------------------------
PAT_SIMPLE = re.compile(r"^[A-Z]\d{3}$")     # LNNN (p.ej. A404)
PAT_DOBLE  = re.compile(r"^[A-Z]{2}\d{3}$")  # LLNNN (p.ej. EE403)

DAY_ORDER = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Miercoles": 2, "Jueves": 3, "Viernes": 4,
    "Sábado": 5, "Sabado": 5, "Domingo": 6
}

# ------------------------------
#   MODELOS
# ------------------------------
@dataclass
class GrupoLab:
    semestre: str
    asignatura: str
    label: str              # p.ej. A404-01
    dia: str
    franja: str             # "HH:MM-HH:MM"
    aula: str               # aula preferente/actual del grupo
    profesor: str           # display "Nombre Apellidos"
    profesor_id: Optional[str]
    es_mixta: bool
    grupo_simple: str       # código LNNN
    grupo_doble: Optional[str]  # código LLNNN si aplica
    alumnos: List[str]      # IDs alumno
    capacidad: int          # capacidad del aula asignada
    fechas: List[str] = None            # ["dd/mm/yyyy", ...] (se guarda tardía→cercana)

# ------------------------------
#   UTILIDADES DE FECHAS
# ------------------------------
def ddmmyyyy_to_iso(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    if not m:
        return s
    d, mo, y = m.groups()
    return f"{y}-{mo}-{d}"

def iso_to_ddmmyyyy(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return s
    y, mo, d = m.groups()
    return f"{d}/{mo}/{y}"

def sort_ddmmyyyy_desc(lst: List[str]) -> List[str]:
    def key_fun(s: str):
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s.strip())
        if not m:
            return (0,0,0)
        d, mo, y = map(int, m.groups())
        return (y, mo, d)
    return sorted(lst, key=key_fun, reverse=True)  # tardía -> cercana

def sort_ddmmyyyy_asc(lst: List[str]) -> List[str]:
    def key_fun(s: str):
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s.strip())
        if not m:
            return (9999,99,99)
        d, mo, y = map(int, m.groups())
        return (y, mo, d)
    return sorted(lst, key=key_fun)  # cercana -> tardía

def normalize_time_range(rng: str) -> str:
    s = (rng or "").strip()
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$", s)
    if not m:
        return s
    h1, m1, h2, m2 = map(int, m.groups())
    return f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"

def time_start_minutes(franja_norm: str) -> int:
    m = re.match(r"^(\d{2}):(\d{2})-\d{2}:\d{2}$", franja_norm.strip())
    if not m:
        return 0
    h, mi = int(m.group(1)), int(m.group(2))
    return h * 60 + mi

# ------------------------------
#   LECTURA/ESCRITURA CONFIG
# ------------------------------
def load_configuration(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def save_configuration(path: Path, cfg: Dict) -> None:
    # Guardado “bonito” y sin ASCII-escape
    with path.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)

def find_default_config() -> Optional[Path]:
    # /src/configuracion_labs.json desde este archivo: .../src/modules/.../motor_organizacion.py
    p = Path(__file__).resolve().parents[2] / "configuracion_labs.json"
    return p if p.exists() else None

# ------------------------------
#   GRID HORARIOS
# ------------------------------
def _is_mixed(grupos: List[str]) -> bool:
    if not grupos:
        return False
    has_s = any(PAT_SIMPLE.match(g) for g in grupos)
    has_d = any(PAT_DOBLE.match(g) for g in grupos)
    return has_s and has_d

def normalize_horarios_grid(cfg: Dict) -> None:
    horarios = (cfg.get("configuracion", {}).get("horarios", {}).get("datos") or {})
    for _, asigs in (horarios or {}).items():
        for _, a_data in (asigs or {}).items():
            grid = a_data.get("horarios_grid") or {}
            for franja_k, dias in list(grid.items()):
                for dia, info in list(dias.items()):
                    if isinstance(info, list):
                        grid[franja_k][dia] = {"grupos": info, "mixta": _is_mixed(info)}
                    elif isinstance(info, dict):
                        grupos = info.get("grupos")
                        if grupos is None and "mixta" in info:
                            posibles = [k for k, v in info.items() if isinstance(v, bool)]
                            if posibles:
                                grid[franja_k][dia] = {"grupos": sorted(posibles), "mixta": _is_mixed(posibles)}
                            else:
                                grid[franja_k][dia].setdefault("grupos", [])
                                grid[franja_k][dia].setdefault("mixta", False)
                        else:
                            grid[franja_k][dia]["mixta"] = bool(info.get("mixta", _is_mixed(grupos or [])))
            a_data["horarios_grid"] = grid

def es_mixta(a_data: Dict, dia: str, franja_norm: str) -> bool:
    grid = a_data.get("horarios_grid", {}) or {}
    for franja_k, dias in grid.items():
        if normalize_time_range(franja_k) != franja_norm:
            continue
        info = dias.get(dia, {})
        if isinstance(info, dict):
            return bool(info.get("mixta"))
    return False

def slots_de_grupo(a_data: Dict, grupo_simple: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    grid = a_data.get("horarios_grid", {}) or {}
    for franja_k, dias in grid.items():
        franja_norm = normalize_time_range(franja_k)
        for dia, info in dias.items():
            grupos = []
            if isinstance(info, dict):
                grupos = info.get("grupos") or []
            if grupo_simple in grupos:
                out.append((dia, franja_norm))
    out = sorted(set(out), key=lambda t: (DAY_ORDER.get(t[0], 99), time_start_minutes(t[1]), t[1]))
    return out

# ------------------------------
#   ALUMNOS
# ------------------------------
def student_map_by_group_subject(cfg: Dict) -> Dict[Tuple[str, str], List[str]]:
    alumnos = cfg.get("configuracion", {}).get("alumnos", {}).get("datos", {}) or {}
    mapping: Dict[Tuple[str, str], List[str]] = {}
    for sid, al in alumnos.items():
        grupos = al.get("grupos_matriculado", []) or []
        asigs  = al.get("asignaturas_matriculadas", {}) or {}
        for asig, meta in asigs.items():
            if not (isinstance(meta, dict) and meta.get("matriculado")):
                continue
            for g in grupos:
                mapping.setdefault((g, asig), []).append(sid)
    for k in mapping:
        mapping[k].sort()
    return mapping

def nombre_profesor_display(p: Dict) -> str:
    n = (p.get("nombre") or "").strip()
    a = (p.get("apellidos") or "").strip()
    out = f"{n} {a}".strip()
    return out or "—"

def capacidad_de_aula(cfg: Dict, aula: str) -> int:
    try:
        return int(cfg["configuracion"]["aulas"]["datos"][aula]["capacidad"])
    except Exception:
        return 10_000

# ------------------------------
#   SCHEDULER (por FECHA real)
# ------------------------------
class Scheduler:
    """
    Ocupaciones por FECHA real. La clave de slot es "YYYY-MM-DD__HH:MM-HH:MM".
    """
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.profs: Dict[str, Dict] = (cfg.get("configuracion", {})
                                     .get("profesores", {})
                                     .get("datos", {}) or {})
        self.aulas: Dict[str, Dict] = (cfg.get("configuracion", {})
                                     .get("aulas", {})
                                     .get("datos", {}) or {})

        # Ocupaciones por FECHA
        self.prof_busy_date: Dict[str, Set[str]] = {}   # prof_id -> {slot_date,...}
        self.aula_busy_date: Dict[str, Set[str]] = {}   # aula    -> {slot_date,...}

        # Cargas para heurísticas
        self.prof_load_total: Dict[str, int] = {}       # prof_id -> nº GRUPOS (no sesiones)
        self.prof_load_by_asig: Dict[Tuple[str, str], int] = {}  # (prof_id, asig) -> nº GRUPOS

        self.primary_room_by_asig: Dict[str, Optional[str]] = {}

    def slot_key_date(self, iso_date: str, franja_norm: str) -> str:
        return f"{iso_date}__{franja_norm}"

    # -------- Profes --------
    def _prof_imparte_asig(self, pid: str, asig: str) -> bool:
        p = self.profs.get(pid) or {}
        return asig in (p.get("asignaturas_imparte") or [])

    def _prof_trabaja_dia(self, pid: str, dia: str) -> bool:
        p = self.profs.get(pid) or {}
        return dia in (p.get("dias_trabajo") or [])

    def _prof_bloqueado_slot(self, pid: str, dia: str, franja_norm: str) -> bool:
        p = self.profs.get(pid) or {}
        bloques = p.get("horarios_bloqueados") or {}
        franjas_en_dia = bloques.get(dia)
        if isinstance(franjas_en_dia, list):
            franjas = [normalize_time_range(x) for x in franjas_en_dia]
        elif isinstance(franjas_en_dia, dict):
            franjas = [normalize_time_range(x) for x in franjas_en_dia.keys()]
        else:
            franjas = []
        return franja_norm in franjas

    def _prof_fecha_no_disponible(self, pid: str, ddmmyyyy: str) -> bool:
        p = self.profs.get(pid) or {}
        lst = [x.strip() for x in (p.get("fechas_no_disponibles") or [])]
        return ddmmyyyy in lst

    def pick_profesor_para_grupo(self, asig: str, dia: str, franja_norm: str) -> Optional[str]:
        cand = []
        for pid in self.profs.keys():
            if not self._prof_imparte_asig(pid, asig):
                continue
            if not self._prof_trabaja_dia(pid, dia):
                continue
            if self._prof_bloqueado_slot(pid, dia, franja_norm):
                continue
            name = nombre_profesor_display(self.profs[pid])
            cand.append((self.prof_load_total.get(pid, 0),
                         self.prof_load_by_asig.get((pid, asig), 0),
                         name, pid))
        if not cand:
            return None
        cand.sort()
        pid = cand[0][3]
        # aumentamos carga a nivel "grupo"
        self.prof_load_total[pid] = self.prof_load_total.get(pid, 0) + 1
        self.prof_load_by_asig[(pid, asig)] = self.prof_load_by_asig.get((pid, asig), 0) + 1
        return pid

    def prof_libre_en_fecha(self, pid: str, iso_date: str, franja_norm: str) -> bool:
        slot = self.slot_key_date(iso_date, franja_norm)
        return slot not in self.prof_busy_date.get(pid, set())

    def ocupar_prof_en_fecha(self, pid: str, iso_date: str, franja_norm: str) -> None:
        slot = self.slot_key_date(iso_date, franja_norm)
        self.prof_busy_date.setdefault(pid, set()).add(slot)

    # -------- Aulas --------
    def _ensure_primary_room(self, asig: str) -> Optional[str]:
        if asig in self.primary_room_by_asig:
            return self.primary_room_by_asig[asig]
        cand = []
        for nombre, a in self.aulas.items():
            if not a.get("disponible", False):
                continue
            if asig not in (a.get("asignaturas_asociadas") or []):
                continue
            cap = int(a.get("capacidad") or 0)
            cand.append((cap, nombre))
        cand.sort(reverse=True)
        self.primary_room_by_asig[asig] = cand[0][1] if cand else None
        return self.primary_room_by_asig[asig]

    def _aulas_de_asignatura(self, asig: str) -> List[str]:
        out = []
        for nombre, a in self.aulas.items():
            if not a.get("disponible", False):
                continue
            if asig in (a.get("asignaturas_asociadas") or []):
                out.append(nombre)
        principal = self._ensure_primary_room(asig)
        if principal in out:
            out.remove(principal)
            out.insert(0, principal)
        return out

    def _aula_fecha_no_disponible(self, aula: str, ddmmyyyy: str) -> bool:
        a = self.aulas.get(aula) or {}
        lst = [x.strip() for x in (a.get("fechas_no_disponibles") or [])]
        return ddmmyyyy in lst

    def aula_libre_en_fecha(self, aula: str, iso_date: str, franja_norm: str) -> bool:
        slot = self.slot_key_date(iso_date, franja_norm)
        return slot not in self.aula_busy_date.get(aula, set())

    def ocupar_aula_en_fecha(self, aula: str, iso_date: str, franja_norm: str) -> None:
        slot = self.slot_key_date(iso_date, franja_norm)
        self.aula_busy_date.setdefault(aula, set()).add(slot)

# ------------------------------
#   FECHAS CALENDARIO
# ------------------------------
def fechas_pool_para_dia(cfg: Dict, semestre: str, dia: str) -> List[str]:
    """
    Todas las fechas del semestre para 'dia' en formato dd/mm/yyyy,
    ordenadas de tardía -> cercana.
    """
    cal = (cfg.get("configuracion", {}).get("calendario", {}).get("datos") or {})
    key = f"semestre_{semestre}"
    dias = list((cal.get(key) or {}).values())
    dias = [d for d in dias if (d.get("horario_asignado") == dia)]
    dias.sort(key=lambda d: d.get("fecha", ""), reverse=True)  # tardía -> cercana
    out = [iso_to_ddmmyyyy(d.get("fecha", "")) if re.match(r"^\d{4}-\d{2}-\d{2}$", (d.get("fecha") or "")) else (d.get("fecha") or "") for d in dias]
    return [x for x in out if x]

# ------------------------------
#   PARIDAD
# ------------------------------
def es_alumno_doble_para_asig(cfg: Dict, sid: str, g: GrupoLab) -> bool:
    al = (cfg.get("configuracion", {}).get("alumnos", {}).get("datos", {}) or {}).get(sid, {})
    grupos = al.get("grupos_matriculado", []) or []
    return bool(g.grupo_doble and g.grupo_doble in grupos)

def paridad_dura_balance(cfg: Dict, grupos: List[GrupoLab], asignatura: str) -> List[str]:
    avisos: List[str] = []
    total = sum(len(g.alumnos) for g in grupos)
    permit_impares = 1 if (total % 2 == 1) else 0

    def candidato_desde(src: GrupoLab, dst: GrupoLab) -> Optional[str]:
        if len(dst.alumnos) >= dst.capacidad:
            return None
        for sid in src.alumnos:
            if es_alumno_doble_para_asig(cfg, sid, src) and not dst.es_mixta:
                continue
            return sid
        return None

    def odd_indices() -> List[int]:
        return [i for i, g in enumerate(grupos) if (len(g.alumnos) % 2 == 1)]

    odds = odd_indices()
    if len(odds) <= permit_impares:
        return avisos

    changed = True
    while len(odds) > permit_impares and changed:
        changed = False
        odds = odd_indices()
        for i in range(len(odds)):
            if len(odds) <= permit_impares:
                break
            for j in range(i + 1, len(odds)):
                a, b = grupos[odds[i]], grupos[odds[j]]
                sid = candidato_desde(b, a)
                if sid is not None:
                    b.alumnos.remove(sid); a.alumnos.append(sid)
                    changed = True; break
                sid = candidato_desde(a, b)
                if sid is not None:
                    a.alumnos.remove(sid); b.alumnos.append(sid)
                    changed = True; break
            if changed: break

    odds = odd_indices()
    if len(odds) > permit_impares:
        avisos.append("No fue posible paridad total por capacidad/mixto; quedan grupos impares adicionales.")
    return avisos

# ------------------------------
#   AGRUPACIÓN Y SCHED APP
# ------------------------------
def grupos_asociados_codes(asig_entry: Dict) -> Tuple[Optional[str], Optional[str]]:
    grupos = (asig_entry.get("grupos_asociados") or {})
    gs = None; gd = None
    for k in grupos.keys():
        if PAT_SIMPLE.match(k): gs = k
        elif PAT_DOBLE.match(k): gd = k
    return gs, gd

def grupos_previstos(asig_entry: Dict, code: Optional[str], default: int = 0) -> int:
    if not code: return 0
    data = (asig_entry.get("grupos_asociados") or {}).get(code, {}) or {}
    return int((data.get("configuracion_laboratorio") or {}).get("grupos_previstos", default))

def clases_por_grupo(asig_entry: Dict, code: Optional[str], default: int = 1) -> int:
    if not code: return default
    data = (asig_entry.get("grupos_asociados") or {}).get(code, {}) or {}
    return int((data.get("configuracion_laboratorio") or {}).get("clases_año", default))

def crear_slots_equilibrados(a_data: Dict, grupo_simple: str, n_simple: int) -> List[Tuple[str, str]]:
    base = slots_de_grupo(a_data, grupo_simple)
    if not base or n_simple <= 0:
        return []
    out: List[Tuple[str, str]] = []
    i = 0
    for _ in range(n_simple):
        out.append(base[i % len(base)])
        i += 1
    return out

def elegir_slots_mixtos(a_data: Dict, grupos_slots: List[Tuple[str, str]], k_doble: int) -> List[int]:
    mixtos_idx = [i for i, (dia, franja) in enumerate(grupos_slots) if es_mixta(a_data, dia, franja)]
    if k_doble <= 0: return []
    if len(mixtos_idx) <= k_doble: return mixtos_idx
    step = max(1, len(mixtos_idx) // k_doble)
    chosen = []; pick = 0
    while len(chosen) < k_doble and pick < len(mixtos_idx):
        chosen.append(mixtos_idx[pick]); pick += step
    i = 0
    while len(chosen) < k_doble and i < len(mixtos_idx):
        if mixtos_idx[i] not in chosen:
            chosen.append(mixtos_idx[i])
        i += 1
    return sorted(chosen)

# --- ASIGNACIÓN DE ALUMNOS ---
def asignar_alumnos_min_carga_por_grupo(
    grupos: List[GrupoLab],
    alumnos_simple: List[str],
    alumnos_doble: List[str],
    reserved_double_idxs: List[int],
) -> None:
    def grupo_menos_cargado(indices: List[int]) -> int:
        return min(indices, key=lambda i: (len(grupos[i].alumnos), i))
    # dobles
    vivos = [i for i in reserved_double_idxs]
    while alumnos_doble and vivos:
        gi = grupo_menos_cargado(vivos)
        if len(grupos[gi].alumnos) < grupos[gi].capacidad:
            grupos[gi].alumnos.append(alumnos_doble.pop(0))
        else:
            vivos.remove(gi)
    # simples
    vivos = [i for i in range(len(grupos))]
    while alumnos_simple and vivos:
        gi = grupo_menos_cargado(vivos)
        if len(grupos[gi].alumnos) < grupos[gi].capacidad:
            grupos[gi].alumnos.append(alumnos_simple.pop(0))
        else:
            vivos.remove(gi)

# ------------------------------
#   PROGRAMACIÓN POR FECHA (intercalado)
# ------------------------------
def _intentar_asignar_en_pool(
    cfg: Dict,
    scheduler: Scheduler,
    g: GrupoLab,
    pool: List[str],         # dd/mm/yyyy (tardía->cercana)
    start_idx: int,
    aulas_alt: List[str],
    conflictos_profes: List[Dict[str, Any]],
) -> Optional[Tuple[int, str]]:
    """
    Intenta asignar una fecha empezando en start_idx y moviéndose a fechas más cercanas.
    - Respeta no-disponibles del profesor y aula.
    - Si el aula preferente no está libre o está marcada no disponible, intenta alternativas.
    Devuelve (idx_elegido, dd/mm/yyyy) o None.
    """
    franja = g.franja
    asig = g.asignatura

    # Intentaremos desde start_idx hacia delante (fechas más cercanas)
    last_tried_dd: Optional[str] = None

    for idx in range(start_idx, len(pool)):
        dd = pool[idx]                              # dd/mm/yyyy candidata
        last_tried_dd = dd
        iso = ddmmyyyy_to_iso(dd)

        # Profesor: si existe asignado al grupo, respetar disponibilidad por fecha/franja
        if g.profesor_id:
            if scheduler._prof_fecha_no_disponible(g.profesor_id, dd):
                continue
            if not scheduler.prof_libre_en_fecha(g.profesor_id, iso, franja):
                continue

        # Aula preferente: no disponible por fecha o ya ocupada
        preferente_ok = False
        if g.aula and g.aula != "—":
            if (not scheduler._aula_fecha_no_disponible(g.aula, dd)) and \
               scheduler.aula_libre_en_fecha(g.aula, iso, franja):
                preferente_ok = True

        if preferente_ok:
            # ocupar preferente
            if g.profesor_id:
                scheduler.ocupar_prof_en_fecha(g.profesor_id, iso, franja)
            scheduler.ocupar_aula_en_fecha(g.aula, iso, franja)
            return (idx, dd)

        # Si no, probar alternativas de aula
        for aula_alt in aulas_alt:
            if scheduler._aula_fecha_no_disponible(aula_alt, dd):
                continue
            if scheduler.aula_libre_en_fecha(aula_alt, iso, franja):
                g.aula = aula_alt
                g.capacidad = capacidad_de_aula(cfg, g.aula)
                if g.profesor_id:
                    scheduler.ocupar_prof_en_fecha(g.profesor_id, iso, franja)
                scheduler.ocupar_aula_en_fecha(g.aula, iso, franja)
                return (idx, dd)

    # No encontrado en fechas cercanas: anotar conflicto con referencia de fecha candidata
    conflictos_profes.append({
        "semestre": g.semestre,
        "asignatura": asig,
        "grupo": g.label,
        "dia": g.dia,
        "franja": g.franja,
        "fecha": last_tried_dd or "",  # si hubo al menos una candidata
        "fechas": pool[start_idx:] if start_idx < len(pool) else [],  # candidatas probadas desde el inicio
        "aula": g.aula or "—",
        "profesor": g.profesor or "—",
        "detalle": "Sin hueco válido (prof/aula) en fechas cercanas"
    })
    return None


def programar_bloque_intercalado(
    cfg: Dict,
    scheduler: Scheduler,
    grupos: List[GrupoLab],          # todos comparten (día, franja)
    asig_entry: Dict,
    conflictos_profes: List[Dict[str, Any]],
    conflictos_aulas: List[Dict[str, Any]],
) -> None:
    """
    Reparte fechas intercaladas (round-robin) entre 'grupos' que comparten (día, franja).
    Evita reutilizar la misma fecha dentro del bloque.
    """
    if not grupos:
        return

    semestre = grupos[0].semestre
    asig = grupos[0].asignatura
    dia = grupos[0].dia
    franja = grupos[0].franja

    # Pool de fechas (tardía -> cercana)
    pool = fechas_pool_para_dia(cfg, semestre, dia)
    if not pool:
        for g in grupos:
            conflictos_profes.append({
                "semestre": semestre,
                "asignatura": asig,
                "grupo": g.label,
                "dia": dia,
                "franja": franja,
                "fecha": "",          # no hay calendario para ese día
                "fechas": [],
                "aula": g.aula or "—",
                "profesor": g.profesor or "—",
                "detalle": "Sin calendario para ese día"
            })
            g.fechas = []
        return

    # Nº de prácticas por grupo (se asume igual para todos por ser mismo simple)
    clases = clases_por_grupo(asig_entry, grupos[0].grupo_simple, default=1)

    # Aulas disponibles asociadas a la asignatura (preferente va primera)
    aulas_lista = scheduler._aulas_de_asignatura(asig)

    # Estado: fechas usadas dentro del bloque para no repetir día entre grupos
    fechas_usadas_bloque: Set[str] = set()

    # reset del contenedor de fechas en cada grupo
    for g in grupos:
        g.fechas = []

    m = len(grupos)
    # Rondas: j = ocurrencia (0..clases-1); r = índice de grupo en el bloque
    for j in range(clases):
        for r, g in enumerate(grupos):
            start = r + j * m
            if start >= len(pool):
                # No hay suficientes fechas para cubrir todas las ocurrencias
                conflictos_profes.append({
                    "semestre": g.semestre,
                    "asignatura": asig,
                    "grupo": g.label,
                    "dia": dia,
                    "franja": franja,
                    "fecha": "",            # no hay una concreta
                    "fechas": pool,         # mostramos el pool disponible (insuficiente)
                    "aula": g.aula or "—",
                    "profesor": g.profesor or "—",
                    "detalle": "Sin suficientes fechas para intercalado"
                })
                continue

            # Asegurar profesor/aula a nivel de grupo si faltan
            if not g.profesor_id:
                pid = scheduler.pick_profesor_para_grupo(asig, dia, franja)
                if pid is None:
                    conflictos_profes.append({
                        "semestre": g.semestre,
                        "asignatura": asig,
                        "grupo": g.label,
                        "dia": dia,
                        "franja": franja,
                        "fecha": pool[start],               # primera candidata de esta ocurrencia
                        "fechas": pool[start:],
                        "aula": g.aula or "—",
                        "profesor": "—",
                        "detalle": "Sin profesor elegible (imparte/día/bloqueo)"
                    })
                    g.profesor = "—"
                    g.profesor_id = None
                else:
                    g.profesor_id = pid
                    g.profesor = nombre_profesor_display(scheduler.profs[pid])

            if not g.aula or g.aula == "—":
                principal = scheduler._ensure_primary_room(asig)
                g.aula = principal if principal else "—"
                g.capacidad = capacidad_de_aula(cfg, g.aula) if g.aula != "—" else 10_000

            # Lista de aulas alternativas (excluye la actual del grupo)
            aulas_alt = [a for a in aulas_lista if a != g.aula]

            # Intentar asignar fecha empezando en 'start', saltando las fechas ya usadas por el bloque
            idx = start
            asignada = False
            while idx < len(pool):
                if pool[idx] in fechas_usadas_bloque:
                    idx += 1
                    continue
                res = _intentar_asignar_en_pool(cfg, scheduler, g, pool, idx, aulas_alt, conflictos_profes)
                if res is not None:
                    idx_elegida, dd = res
                    # Reservar fecha para no reutilizarla en el bloque
                    fechas_usadas_bloque.add(dd)
                    g.fechas.append(dd)
                    asignada = True
                    break
                else:
                    # Si _intentar_asignar_en_pool no consiguió asignar en 'idx', probamos la siguiente fecha
                    idx += 1

            if not asignada:
                # No se pudo asignar esta ocurrencia
                fecha_candidata = pool[idx] if idx < len(pool) else (pool[start] if start < len(pool) else "")
                conflictos_profes.append({
                    "semestre": g.semestre,
                    "asignatura": g.asignatura,
                    "grupo": g.label,
                    "dia": dia,
                    "franja": franja,
                    "fecha": fecha_candidata,
                    "fechas": pool[start:] if start < len(pool) else [],
                    "aula": g.aula or "—",
                    "profesor": g.profesor or "—",
                    "detalle": "No se pudo asignar fecha para esta ocurrencia (intercalado)"
                })

    # Guardamos fechas internas en orden tardía -> cercana (útil para ajustes internos)
    for g in grupos:
        g.fechas = sort_ddmmyyyy_desc(g.fechas or [])


# ------------------------------
#   PLANIFICACIÓN DE UNA ASIGNATURA
# ------------------------------
def planificar_asignatura(
    cfg: Dict,
    scheduler: Scheduler,
    semestre: str,
    asig: str,
    conflict_profs: List[Dict[str, Any]],
    conflict_aulas: List[Dict[str, Any]],
) -> Tuple[List[GrupoLab], List[str]]:
    normalize_horarios_grid(cfg)
    horarios = cfg["configuracion"]["horarios"]["datos"][semestre]
    a_data = horarios[asig]
    asig_entry = cfg["configuracion"]["asignaturas"]["datos"].get(asig, {})

    gs, gd = grupos_asociados_codes(asig_entry)
    if not gs:
        return [], [f"- {semestre}:{asig} → sin grupo simple LNNN en grupos_asociados"]

    n_simple = grupos_previstos(asig_entry, gs, default=0)
    n_doble  = grupos_previstos(asig_entry, gd, default=0)

    # Alumnos
    smap = student_map_by_group_subject(cfg)
    alumnos_s = list(smap.get((gs, asig), []))
    alumnos_d = list(smap.get((gd, asig), [])) if gd else []

    # 1) Slots de grupos (por día y franja)
    grupos_slots = crear_slots_equilibrados(a_data, gs, n_simple)
    # 2) Elegir qué índices serán mixtos (para dobles)
    reserved_double = elegir_slots_mixtos(a_data, grupos_slots, n_doble)

    grupos_creados: List[GrupoLab] = []
    avisos: List[str] = []
    contador = 1

    # 3) Crear grupos (profesor/aula asignados a nivel de grupo; ocupación por fecha más tarde)
    for i, (dia, franja_norm) in enumerate(grupos_slots):
        pid = scheduler.pick_profesor_para_grupo(asig, dia, franja_norm)
        if pid is None:
            prof_display = "—"
            avisos.append(f"- {semestre}:{asig} {gs}-{contador:02d} → sin profesor elegible en {dia} {franja_norm}")
        else:
            prof_display = nombre_profesor_display(scheduler.profs[pid])

        aula = scheduler._ensure_primary_room(asig) or "—"
        cap = capacidad_de_aula(cfg, aula) if aula != "—" else 10_000

        g = GrupoLab(
            semestre=semestre, asignatura=asig, label=f"{gs}-{contador:02d}",
            dia=dia, franja=franja_norm, aula=aula, profesor=prof_display,
            profesor_id=pid, es_mixta=(i in reserved_double) or es_mixta(a_data, dia, franja_norm),
            grupo_simple=gs, grupo_doble=gd, alumnos=[], capacidad=cap, fechas=[]
        )
        grupos_creados.append(g)
        contador += 1

    # 4) Reparto de alumnos por capacidad
    asignar_alumnos_min_carga_por_grupo(grupos_creados, alumnos_s, alumnos_d, reserved_double)

    # 5) Paridad DURA
    avisos += paridad_dura_balance(cfg, grupos_creados, asig)

    # 6) Programación por FECHA con INTERCALADO por (día, franja)
    # Agrupar grupos por (día, franja) para repartir fechas en rondas
    grupos_por_slot: Dict[Tuple[str, str], List[GrupoLab]] = {}
    for g in grupos_creados:
        grupos_por_slot.setdefault((g.dia, g.franja), []).append(g)

    for (dia, franja), glist in grupos_por_slot.items():
        programar_bloque_intercalado(cfg, scheduler, glist, asig_entry,
                                     conflict_profs, conflict_aulas)

    return grupos_creados, avisos

# ------------------------------
#   CONSTRUCCIÓN DE RESULTADOS JSON
# ------------------------------
def sem_key(sem: str) -> str:
    """Normaliza la clave de semestre a 'semestre_1' / 'semestre_2'."""
    return sem if sem.startswith("semestre_") else f"semestre_{sem}"

def grupo_to_json(g: GrupoLab) -> Dict[str, Any]:
    return {
        "profesor": g.profesor,
        "profesor_id": g.profesor_id or "",
        "aula": g.aula,
        "dia": g.dia,
        "franja": g.franja,
        "fechas": g.fechas or [],
        "alumnos": list(g.alumnos),
        "capacidad": g.capacidad,
        "mixta": bool(g.es_mixta),
        "grupo_simple": g.grupo_simple,
        "grupo_doble": g.grupo_doble or ""
    }

def merge_resultados_into_cfg(cfg: Dict,
                              grupos: List[GrupoLab],
                              conflictos_profes: List[Dict[str, Any]],
                              conflictos_aulas: List[Dict[str, Any]],
                              avisos: List[str]) -> None:
    """
    Inserta/actualiza en cfg:
      - parametros_organizacion
      - resultados_organizacion: { semestre -> asignatura -> grupos -> ... , conflictos, avisos, metadata }
    """
    #cfg["parametros_organizacion"] = build_parametros_organizacion()

    res = cfg.get("resultados_organizacion") or {}

    res["datos_disponibles"] = True
    res["fecha_actualizacion"] = datetime.now().isoformat()

    # Estructura base
    res.setdefault("conflictos", {})
    res["conflictos"]["profesores"] = conflictos_profes or []
    res["conflictos"]["aulas"] = conflictos_aulas or []
    res["avisos"] = avisos or []

    # Agrupar por semestre->asignatura
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for g in grupos:
        skey = sem_key(g.semestre)
        res.setdefault(skey, {})
        res[skey].setdefault(g.asignatura, {})
        res[skey][g.asignatura].setdefault("grupos", {})
        res[skey][g.asignatura]["grupos"][g.label] = grupo_to_json(g)
        index[(skey, g.asignatura)] = res[skey][g.asignatura]

    # Metadatos
    meta = res.setdefault("_metadata", {})
    meta["ultima_ejecucion"] = datetime.now().isoformat(timespec="seconds")
    meta["version"] = "v3-json-first"
    cfg["resultados_organizacion"] = res

# ------------------------------
#   RUN
# ------------------------------
def run(config_path: Optional[str] = None) -> None:
    # 1) Cargar configuración
    if not config_path:
        p = find_default_config()
        if not p:
            print("ERROR: especifica --config ruta_al_json")
            sys.exit(1)
        config_path = str(p)
    cfg_path = Path(config_path)
    cfg = load_configuration(cfg_path)

    # 2) Preparar scheduler por fecha
    scheduler = Scheduler(cfg)

    # 3) Recorrer semestres y asignaturas
    conflictos_profes: List[Dict[str, Any]] = []
    conflictos_aulas:  List[Dict[str, Any]] = []
    grupos_total: List[GrupoLab] = []
    avisos_globales: List[str] = []

    horarios = (cfg.get("configuracion", {}).get("horarios", {}).get("datos") or {})
    for semestre, asigs in horarios.items():
        for asig in asigs.keys():
            grupos, avisos = planificar_asignatura(cfg, scheduler, semestre, asig,
                                                   conflictos_profes, conflictos_aulas)
            grupos_total.extend(grupos)
            avisos_globales.extend(avisos)

    # 4) Volcar todo al JSON
    merge_resultados_into_cfg(cfg, grupos_total, conflictos_profes, conflictos_aulas, avisos_globales)
    save_configuration(cfg_path, cfg)

    # 5) Mensaje final en consola
    print("[OK] Planificación completada y guardada en JSON.")
    print(f"     Archivo: {cfg_path}")
    if avisos_globales:
        print(f"     Avisos: {len(avisos_globales)}")
    print(f"     Conflictos -> Profesores: {len(conflictos_profes)} | Aulas: {len(conflictos_aulas)}")
    print("     Secciones actualizadas: parametros_organizacion, resultados_organizacion")

# ------------------------------
#   CLI
# ------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Planificador de laboratorios por FECHA (intercalado) con volcado a JSON")
    ap.add_argument("--config", type=str, help="Ruta al JSON de configuración", required=False)
    args = ap.parse_args()
    run(args.config)
