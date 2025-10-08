#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurar Motor de Organizacion - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)


Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
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
    """
    Construye un mapeo (grupo, asignatura) -> [lista de IDs de alumnos].

    A diferencia de versiones anteriores, NO utiliza grupos_matriculado de forma genérica,
    sino que extrae el grupo específico asignado a cada asignatura desde el campo 'grupo'
    dentro de asignaturas_matriculadas.

    Estructura esperada en el JSON de alumnos:
        "asignaturas_matriculadas": {
            "SII": {
                "matriculado": true,
                "lab_aprobado": false,
                "grupo": "A408"  // Grupo específico para esta asignatura
            }
        }

    Args:
        cfg: Configuración completa del sistema (dict JSON)

    Returns:
        Diccionario con clave (codigo_grupo, codigo_asignatura) y valor lista de student IDs.
        Ejemplo: {("A408", "SII"): ["sid1", "sid2"], ("A404", "SED"): ["sid1", "sid3"]}
    """
    alumnos = cfg.get("configuracion", {}).get("alumnos", {}).get("datos", {}) or {}
    mapping: Dict[Tuple[str, str], List[str]] = {}

    for sid, al in alumnos.items():
        asigs = al.get("asignaturas_matriculadas", {}) or {}

        for asig, meta in asigs.items():
            if not isinstance(meta, dict):
                continue
            if not meta.get("matriculado", False):
                continue

            # Extraer el grupo específico asignado a esta asignatura
            grupo_asig = meta.get("grupo")
            if not grupo_asig:
                continue

            # Registrar alumno en (grupo_específico, asignatura)
            mapping.setdefault((grupo_asig, asig), []).append(sid)

    # Ordenar listas para reproducibilidad
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
    """
    Determina si un alumno es de doble grado.

    - Doble grado: alumno matriculado en al menos UN grupo con patrón LLNNN (ej: EE303, AA606)
    - Simple: alumno solo en grupos con patrón LNNN (ej: A408, A404)

    IMPORTANTE: Estar matriculado en múltiples grupos simples (A408, A404, A406) NO convierte
    al alumno en doble grado. Solo los códigos LLNNN califican como doble grado.

    Args:
        cfg: Configuración completa del sistema
        sid: ID del alumno
        g: Objeto GrupoLab (usado para contexto, no para determinar doble)

    Returns:
        True si el alumno tiene al menos un grupo LLNNN en grupos_matriculado
    """
    al = (cfg.get("configuracion", {}).get("alumnos", {}).get("datos", {}) or {}).get(sid, {})
    grupos_al = al.get("grupos_matriculado", []) or []

    # Verificar si existe al menos un código con patrón LLNNN
    return any(PAT_DOBLE.match(g) for g in grupos_al)


def paridad_dura_balance(
    cfg: Dict,
    grupos_creados: List[GrupoLab],
    asig: str,
) -> List[str]:
    """
    Equilibrio de paridad por CÓDIGO SIMPLE (p. ej., A408, A404), respetando:
      - Elegibilidad de franja: un alumno solo puede moverse a (día, franja) si su(s) código(s) están declarados en el grid.
      - Capacidad de grupo destino.
      - No se mezclan códigos: cada código se equilibra dentro de sus propios grupos.
    Objetivo: dejar como mucho 1 grupo impar por cada código.

    Devuelve lista de avisos si no se puede completar el equilibrio.
    """
    avisos: List[str] = []
    if not grupos_creados:
        return avisos

    # --- Contexto de datos necesarios ---
    semestre = grupos_creados[0].semestre
    horarios = cfg["configuracion"]["horarios"]["datos"][semestre]
    a_data = horarios[asig]

    # --- Helpers robustos a '09:30-11:30' vs '9:30-11:30' y esquema [franja][dia] / [dia][franja] ---
    def _norm_franja_key(s: str) -> str:
        if not isinstance(s, str):
            return s
        s = s.strip()
        if "-" not in s:
            return s

        def _norm_hhmm(t: str) -> str:
            t = t.strip()
            if ":" not in t:
                return t
            hh, mm = t.split(":", 1)
            try:
                hh_n = str(int(hh))  # quita ceros a la izquierda
            except ValueError:
                hh_n = hh
            return f"{hh_n}:{mm}"

        ini, fin = s.split("-", 1)
        return f"{_norm_hhmm(ini)}-{_norm_hhmm(fin)}"

    def _slot_node(a_data_local: dict, dia: str, franja_norm: str) -> Dict[str, Any]:
        hg = a_data_local.get("horarios_grid", {})
        key_raw = franja_norm or ""
        key_norm = _norm_franja_key(key_raw)

        # Forma 1: horarios_grid[franja][dia]
        if isinstance(hg.get(key_raw), dict) and isinstance(hg[key_raw].get(dia), dict):
            return hg[key_raw][dia]
        if isinstance(hg.get(key_norm), dict) and isinstance(hg[key_norm].get(dia), dict):
            return hg[key_norm][dia]

        # Forma 2: horarios_grid[dia][franja]
        if isinstance(hg.get(dia), dict):
            if isinstance(hg[dia].get(key_raw), dict):
                return hg[dia][key_raw]
            if isinstance(hg[dia].get(key_norm), dict):
                return hg[dia][key_norm]

        return {}

    def _slot_grupos(a_data_local: dict, dia: str, franja_norm: str) -> List[str]:
        node = _slot_node(a_data_local, dia, franja_norm)
        return list(node.get("grupos") or [])

    def _slot_permite(a_data_local: dict, dia: str, franja_norm: str, code: str) -> bool:
        return code in _slot_grupos(a_data_local, dia, franja_norm)

    def _slot_permite_estudiante(
        a_data_local: dict,
        dia: str,
        franja_norm: str,
        grupo_simple: str,
        grupo_doble: Optional[str],
    ) -> bool:
        if grupo_doble:
            return (_slot_permite(a_data_local, dia, franja_norm, grupo_doble)
                    or _slot_permite(a_data_local, dia, franja_norm, grupo_simple))
        return _slot_permite(a_data_local, dia, franja_norm, grupo_simple)

    # --- Índices alumno → (simple, doble) para esta asignatura ---
    smap = student_map_by_group_subject(cfg)
    alumno_simple: Dict[str, str] = {}
    alumno_doble: Dict[str, str] = {}
    # recolectamos desde TODOS los códigos presentes en grupos_creados
    codigos_presentes = sorted(set(g.grupo_simple for g in grupos_creados))
    # simples:
    for gs in codigos_presentes:
        for sid in smap.get((gs, asig), []):
            alumno_simple[sid] = gs
    # dobles: buscar cualquier LLNNN que esté vinculado a esta asignatura en el cfg
    asig_entry = cfg["configuracion"]["asignaturas"]["datos"].get(asig, {})
    _, dobles = grupos_asociados_codes(asig_entry)
    for gd in dobles:
        for sid in smap.get((gd, asig), []):
            alumno_doble[sid] = gd

    # --- Agrupar grupos por código simple ---
    grupos_idx_por_codigo: Dict[str, List[int]] = {}
    for i, g in enumerate(grupos_creados):
        grupos_idx_por_codigo.setdefault(g.grupo_simple, []).append(i)

    # --- Para cada código, intentar reducir impares moviendo alumnos elegibles ---
    for gs, idxs in grupos_idx_por_codigo.items():
        if not idxs:
            continue

        # Solo grupos de este código
        impares = [i for i in idxs if (len(grupos_creados[i].alumnos) % 2) == 1]

        # Intentamos emparejar impares de dos en dos.
        # Movimiento de un alumno de src -> dst (ambos impares) hará que ambos pasen a par,
        # si (y solo si) el alumno es elegible en el slot destino y hay capacidad.
        changed = True
        while len(impares) >= 2 and changed:
            changed = False
            # probamos todas las combinaciones (greedy)
            tried_pairs = set()
            for s_pos in range(len(impares)):
                src_idx = impares[s_pos]
                for d_pos in range(s_pos + 1, len(impares)):
                    dst_idx = impares[d_pos]
                    if (src_idx, dst_idx) in tried_pairs:
                        continue
                    tried_pairs.add((src_idx, dst_idx))

                    src = grupos_creados[src_idx]
                    dst = grupos_creados[dst_idx]

                    if len(dst.alumnos) >= dst.capacidad:
                        continue  # sin hueco

                    # buscamos un alumno en src elegible para el slot de dst
                    sid_movable = None
                    for sid in src.alumnos:
                        gs_al = alumno_simple.get(sid)  # debería ser gs
                        gd_al = alumno_doble.get(sid)
                        if _slot_permite_estudiante(a_data, dst.dia, dst.franja, gs_al or gs, gd_al):
                            sid_movable = sid
                            break

                    if sid_movable is None:
                        continue

                    # mover
                    src.alumnos.remove(sid_movable)
                    dst.alumnos.append(sid_movable)

                    # actualizar lista de impares: src y dst cambian de paridad
                    # (ambos eran impares, tras mover quedan pares)
                    impares = [i for i in idxs if (len(grupos_creados[i].alumnos) % 2) == 1]
                    changed = True
                    break  # re-evaluar impares
                if changed:
                    break

        # Si quedan >1 impares, no hemos podido resolver del todo
        if len(impares) > 1:
            avisos.append(
                f"- Paridad no resuelta en {gs}: quedan {len(impares)} grupos impares "
                f"por restricciones de elegibilidad/capacidad."
            )
        elif len(impares) == 0:
            # Perfecto (0 impares)
            pass
        else:
            # 1 impar (tolerado)
            pass

    return avisos


# ------------------------------
#   AGRUPACIÓN Y SCHED APP
# ------------------------------
def grupos_asociados_codes(asig_entry: Dict) -> Tuple[List[str], List[str]]:
    """
    Devuelve dos listas: códigos simples (LNNN) y dobles (LLNNN).
    """
    simples: List[str] = []
    dobles: List[str]  = []
    grupos = (asig_entry.get("grupos_asociados") or {})
    for k in grupos.keys():
        if PAT_SIMPLE.match(k):
            simples.append(k)
        elif PAT_DOBLE.match(k):
            dobles.append(k)
    # orden estable para reproducibilidad
    return sorted(simples), sorted(dobles)

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

def _avisos_capacidad_insuficiente(
    cfg: Dict,
    semestre: str,
    asig: str,
    grupos_creados: List["GrupoLab"],
    simples: List[str],
    dobles: List[str],
    smap: Dict[Tuple[str, str], List[str]],
) -> List[Dict[str, Any]]:
    """
    Genera avisos de capacidad como CONFLICTOS ESTRUCTURADOS (dict), listos para
    mostrarse en la tabla 'Alumnos' de la UI con las mismas columnas que
    Profesores/Aulas. Los campos no aplicables se rellenan con "-".
    """
    conflictos: List[Dict[str, Any]] = []

    # Alumnos realmente asignados
    asignados: Set[str] = set()
    for g in grupos_creados:
        for sid in (g.alumnos or []):
            asignados.add(sid)

    def add_conf(codigo: str, etiqueta: str) -> None:
        # alumnos matriculados en (codigo, asig)
        matriculados = set(smap.get((codigo, asig), []))
        faltan = len(matriculados - asignados)
        if faltan > 0:
            conflictos.append({
                "semestre": f"semestre_{semestre}" if not str(semestre).startswith("semestre_") else str(semestre),
                "asignatura": asig,
                "grupo": codigo,          # p.ej. A408 o EE403
                "dia": "-", "fecha": "-", "franja": "-",
                "aula": "-", "profesor": "-",
                "detalle": (
                    f"Capacidad insuficiente: faltan {faltan} alumno(s) del {etiqueta} {codigo} por ubicar. "
                    f"Incrementa nº de laboratorios previstos, la capacidad del aula o revisa las franjas horarias."
                )
            })

    # Detalle por cada simple y doble
    for gs in simples:
        add_conf(gs, "grupo")
    for gd in dobles:
        add_conf(gd, "grupo doble")

    # Resumen global de la asignatura
    total_faltan = 0
    for codigo in simples + dobles:
        total_faltan += len(set(smap.get((codigo, asig), [])) - asignados)
    if total_faltan > 0:
        conflictos.append({
            "semestre": f"semestre_{semestre}" if not str(semestre).startswith("semestre_") else str(semestre),
            "asignatura": asig,
            "grupo": "[RESUMEN]",
            "dia": "-", "fecha": "-", "franja": "-",
            "aula": "-", "profesor": "-",
            "detalle": (
                f"Faltan {total_faltan} alumno(s) por ubicar en total. "
                f"Revisa grupos_previstos y capacidad de aulas."
            )
        })

    return conflictos




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
    """
    Planifica los laboratorios de una asignatura respetando la asignación específica
    grupo-asignatura de cada alumno.

    Flujo:
    - Crea grupos para cada código simple (LNNN) con slots equilibrados
    - Reserva grupos 'mixta' donde el grid lo declara (para dobles)
    - Reparte alumnos dobles PRIMERO en grupos mixta compatibles
    - Reparte alumnos simples en SUS grupos específicos de la asignatura
    - Aplica paridad dura
    - Programa fechas con intercalado por (día, franja)

    Args:
        cfg: Configuración completa
        scheduler: Gestor de ocupaciones por fecha
        semestre: "1" o "2"
        asig: Código de asignatura
        conflict_profs: Lista acumulativa de conflictos de profesores
        conflict_aulas: Lista acumulativa de conflictos de aulas

    Returns:
        Tupla (grupos_creados, avisos) donde:
        - grupos_creados: Lista de objetos GrupoLab con alumnos asignados y fechas
        - avisos: Lista de mensajes de advertencia
    """
    normalize_horarios_grid(cfg)
    horarios = cfg["configuracion"]["horarios"]["datos"][semestre]
    a_data = horarios[asig]
    asig_entry = cfg["configuracion"]["asignaturas"]["datos"].get(asig, {})

    simples, dobles = grupos_asociados_codes(asig_entry)
    if not simples:
        return [], [f"- {semestre}:{asig} → sin grupos simples LNNN en grupos_asociados"]

    # Mapeo: usa grupo específico de cada asignatura
    smap = student_map_by_group_subject(cfg)

    # Helpers de elegibilidad por slot
    def _norm_franja_key(s: str) -> str:
        if not isinstance(s, str):
            return s
        s = s.strip()
        if "-" not in s:
            return s

        def _norm_hhmm(t: str) -> str:
            t = t.strip()
            if ":" not in t:
                return t
            hh, mm = t.split(":", 1)
            try:
                hh_n = str(int(hh))
            except ValueError:
                hh_n = hh
            return f"{hh_n}:{mm}"

        ini, fin = s.split("-", 1)
        return f"{_norm_hhmm(ini)}-{_norm_hhmm(fin)}"

    def _slot_node(a_data_local: dict, dia: str, franja_norm: str) -> Dict[str, Any]:
        hg = a_data_local.get("horarios_grid", {})
        key_raw = franja_norm or ""
        key_norm = _norm_franja_key(key_raw)
        if isinstance(hg.get(key_raw), dict) and isinstance(hg[key_raw].get(dia), dict):
            return hg[key_raw][dia]
        if isinstance(hg.get(key_norm), dict) and isinstance(hg[key_norm].get(dia), dict):
            return hg[key_norm][dia]
        if isinstance(hg.get(dia), dict):
            if isinstance(hg[dia].get(key_raw), dict):
                return hg[dia][key_raw]
            if isinstance(hg[dia].get(key_norm), dict):
                return hg[dia][key_norm]
        return {}

    def _slot_grupos(a_data_local: dict, dia: str, franja_norm: str) -> List[str]:
        node = _slot_node(a_data_local, dia, franja_norm)
        return list(node.get("grupos") or [])

    def _slot_permite(a_data_local: dict, dia: str, franja_norm: str, code: str) -> bool:
        return code in _slot_grupos(a_data_local, dia, franja_norm)

    def _slot_permite_estudiante(a_data_local: dict, dia: str, franja_norm: str,
                                 grupo_simple: str, grupo_doble: Optional[str]) -> bool:
        if grupo_doble:
            return (_slot_permite(a_data_local, dia, franja_norm, grupo_doble) or
                    _slot_permite(a_data_local, dia, franja_norm, grupo_simple))
        return _slot_permite(a_data_local, dia, franja_norm, grupo_simple)

    total_dobles_previstos = sum(grupos_previstos(asig_entry, gd, default=0) for gd in dobles)
    grupos_creados: List[GrupoLab] = []
    avisos: List[str] = []

    # 1) Crear grupos para cada código simple
    mixtos_por_reservar = total_dobles_previstos
    for gs in simples:
        n_simple = grupos_previstos(asig_entry, gs, default=0)
        if n_simple <= 0:
            continue

        grupos_slots = crear_slots_equilibrados(a_data, gs, n_simple)
        if not grupos_slots:
            avisos.append(f"- {semestre}:{asig} {gs} → sin slots en horarios_grid")
            continue

        mixtos_candidatos = [i for i, (dia, franja) in enumerate(grupos_slots) if es_mixta(a_data, dia, franja)]
        k_a_reservar = min(mixtos_por_reservar, len(mixtos_candidatos))
        if k_a_reservar > 0:
            step = max(1, len(mixtos_candidatos) // k_a_reservar)
            reserved_idx_local = sorted({mixtos_candidatos[i] for i in range(0, len(mixtos_candidatos), step)})[
                                 :k_a_reservar]
        else:
            reserved_idx_local = []

        mixtos_por_reservar -= len(reserved_idx_local)

        contador = 1
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
                profesor_id=pid, es_mixta=(i in reserved_idx_local),
                grupo_simple=gs, grupo_doble=None,
                alumnos=[], capacidad=cap, fechas=[]
            )
            grupos_creados.append(g)
            contador += 1

    # 2) Asignación de alumnos
    reserved_double_global = [i for i, g in enumerate(grupos_creados) if g.es_mixta]

    # Índices inversos: alumno → grupo asignado para ESTA asignatura
    # Clave: ahora usamos el grupo específico de asignaturas_matriculadas[asig]["grupo"]
    alumnos_data = cfg.get("configuracion", {}).get("alumnos", {}).get("datos", {}) or {}
    alumno_simple: Dict[str, str] = {}
    alumno_doble: Dict[str, str] = {}

    for sid, al in alumnos_data.items():
        asigs_mat = al.get("asignaturas_matriculadas", {}) or {}

        # Grupo específico para esta asignatura
        if asig in asigs_mat and isinstance(asigs_mat[asig], dict):
            grupo_especifico = asigs_mat[asig].get("grupo")
            if grupo_especifico:
                # Determinar si es simple o doble según el PATRÓN del grupo específico
                if PAT_SIMPLE.match(grupo_especifico):
                    alumno_simple[sid] = grupo_especifico
                elif PAT_DOBLE.match(grupo_especifico):
                    alumno_doble[sid] = grupo_especifico

    alumnos_dobles_all: List[str] = sorted(set(alumno_doble.keys()))

    # 2A) Reparto de dobles en grupos mixta
    for sid in alumnos_dobles_all:
        gs = alumno_simple.get(sid)
        gd = alumno_doble.get(sid)

        candidatos_idx = []
        for idx in reserved_double_global:
            g = grupos_creados[idx]
            if _slot_permite_estudiante(a_data, g.dia, g.franja, gs or "", gd):
                if len(g.alumnos) < g.capacidad:
                    candidatos_idx.append(idx)

        if not candidatos_idx:
            avisos.append(
                f"- {semestre}:{asig} → alumno {sid} doble {gd}"
                f"{f'/{gs}' if gs else ''} sin slot mixta compatible o sin capacidad"
            )
            continue

        mejor_idx = min(candidatos_idx, key=lambda i: len(grupos_creados[i].alumnos))
        grupos_creados[mejor_idx].alumnos.append(sid)

    # 2B) Reparto de simples: cada código a SUS grupos de la asignatura
    for gs in simples:
        # Alumnos cuyo grupo ESPECÍFICO para esta asignatura es 'gs'
        alumnos_s_local = [sid for sid, grupo_asig in alumno_simple.items() if grupo_asig == gs]
        if not alumnos_s_local:
            continue

        idx_local = [i for i, g in enumerate(grupos_creados) if g.grupo_simple == gs]
        idx_local_elig = [i for i in idx_local if
                          _slot_permite(a_data, grupos_creados[i].dia, grupos_creados[i].franja, gs)]
        sub_grupos = [grupos_creados[i] for i in idx_local_elig]

        if not sub_grupos:
            avisos.append(f"- {semestre}:{asig} {gs} → no hay grupos con franjas que declaren {gs}")
            continue

        asignar_alumnos_min_carga_por_grupo(
            grupos=sub_grupos,
            alumnos_simple=alumnos_s_local,
            alumnos_doble=[],
            reserved_double_idxs=[],
        )

    # 3) Paridad dura
    avisos += paridad_dura_balance(cfg, grupos_creados, asig)

    # 4) Programación por fecha
    grupos_por_slot: Dict[Tuple[str, str], List[GrupoLab]] = {}
    for g in grupos_creados:
        grupos_por_slot.setdefault((g.dia, g.franja), []).append(g)

    for (dia, franja), glist in grupos_por_slot.items():
        programar_bloque_intercalado(
            cfg, scheduler, glist, asig_entry, conflict_profs, conflict_aulas
        )

    # 5) Avisos de capacidad
    avisos += _avisos_capacidad_insuficiente(
        cfg=cfg, semestre=semestre, asig=asig,
        grupos_creados=grupos_creados,
        simples=simples, dobles=dobles, smap=smap,
    )

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
                              avisos: List[Any]) -> None:
    """
    Reconstruye resultados_organizacion y mueve los avisos de capacidad a
    conflictos.alumnos. Admite dicts y strings (formato heredado).
    """

    res: Dict[str, Any] = {}
    res["datos_disponibles"] = True
    res["fecha_actualizacion"] = datetime.now().isoformat()

    # Separar conflictos de alumnos (dict actual; string heredado con prefijo)
    conflictos_alumnos: List[Dict[str, Any]] = []
    otros_avisos: List[str] = []

    for m in avisos or []:
        if isinstance(m, dict):
            # Ya viene estructurado
            conflictos_alumnos.append(m)
        elif isinstance(m, str) and m.startswith("[CAPACIDAD_ALUMNOS]"):
            # Compatibilidad con entradas en texto plano
            txt = m.replace("[CAPACIDAD_ALUMNOS]", "").strip()
            conflictos_alumnos.append({
                "semestre": "-", "asignatura": "-", "grupo": "[LEGACY]",
                "dia": "-", "fecha": "-", "franja": "-",
                "aula": "-", "profesor": "-",
                "detalle": txt
            })
        else:
            # Aviso normal, no es de alumnos
            otros_avisos.append(str(m))

    res["conflictos"] = {
        "profesores": conflictos_profes or [],
        "aulas": conflictos_aulas or [],
        "alumnos": conflictos_alumnos or []
    }
    res["avisos"] = otros_avisos

    # Cuerpo: semestre -> asignatura -> grupos
    def sem_key(sem: str) -> str:
        return sem if str(sem).startswith("semestre_") else f"semestre_{sem}"

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

    for g in grupos:
        skey = sem_key(g.semestre)
        if skey not in res:
            res[skey] = {}
        if g.asignatura not in res[skey]:
            res[skey][g.asignatura] = {"grupos": {}}
        res[skey][g.asignatura]["grupos"][g.label] = grupo_to_json(g)

    res["_metadata"] = {
        "ultima_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "version": "v3-json-first"
    }

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
