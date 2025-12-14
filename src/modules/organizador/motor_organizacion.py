"""
Motor de Organización v2 - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)

ESTRUCTURA DEL MOTOR:
    FASE 1: Carga y Validación
    FASE 2: Cálculo de Fechas por Letra (solo grados simples, luego agregamos dobles/mixtos)
    FASE 3: Aula Preferente
    FASE 4: Crear Grupos de Laboratorio (aquí agregamos grados dobles/mixtos)
    FASE 5: Asignar Alumnos
    FASE 6: Asignar Profesores
    FASE 7: Programar Fechas (con búsqueda alternativas)
    FASE 8
    : Outputs
"""


from __future__ import annotations
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set

from PyQt6.QtWidgets import QMessageBox, QApplication

# ========= CONSTANTES Y PATRONES =========
# Patrones de grupos
PAT_SIMPLE = re.compile(r"^[A-Z]\d{3}$")  # Ejemplo: A404
PAT_DOBLE = re.compile(r"^[A-Z]{2}\d{3}$")  # Ejemplo: EE403

# Orden de días de la semana
DAY_ORDER = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Miercoles": 2,
    "Jueves": 3, "Viernes": 4, "Sábado": 5, "Sabado": 5, "Domingo": 6
}


# ========= MODELOS DE DATOS =========
@dataclass
class GrupoLab:
    """
    Representa un grupo de laboratorio con toda su configuración.

    Attributes:
        semestre: Semestre al que pertenece (ej: "semestre_1")
        asignatura: Código de la asignatura (ej: "SII")
        label: Identificador del grupo (ej: "A404-01")
        dia: Día de la semana (ej: "Lunes")
        franja: Rango horario (ej: "09:30-11:30")
        letra: Letra del grupo (ej: "A", "B")
        aula: Código del aula asignada
        capacidad: Capacidad del aula
        profesor: Nombre completo del profesor
        profesor_id: ID del profesor
        is_slot_mixto: Si el slot tiene grupos simples y dobles
        grupo_simple: Código del grupo simple (ej: "A404")
        grupo_doble: Código del grupo doble si aplica (ej: "EE403")
        alumnos: Lista de IDs de alumnos asignados
        fechas: Lista de fechas programadas (formato dd/mm/yyyy)
    """
    semestre: str
    asignatura: str
    label: str
    dia: str
    franja: str
    letra: str
    aula: str
    capacidad: int
    profesor: str = ""
    profesor_id: Optional[str] = None
    is_slot_mixto: bool = False
    grupo_simple: str = ""
    grupo_doble: Optional[str] = None
    alumnos: List[str] = field(default_factory=list)
    fechas: List[str] = field(default_factory=list)


@dataclass
class ErrorValidacion:
    """
    Representa un error detectado durante la validación.

    Attributes:
        fase: Fase donde se detectó el error
        tipo: Tipo de error (CRITICO, ADVERTENCIA)
        mensaje: Descripción del error
        detalle: Información adicional
    """
    fase: str
    tipo: str  # "CRITICO" o "ADVERTENCIA"
    mensaje: str
    detalle: Dict[str, Any] = field(default_factory=dict)


# ========= UTILIDADES GENERALES =========
def load_configuration(path: Path) -> Dict:
    """
    Cargar configuración desde archivo JSON.

    Args:
        path: Ruta al archivo JSON

    Returns:
        Diccionario con la configuración completa
    """
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def normalize_time_range(rng: str) -> str:
    """
    Normalizar rango horario al formato HH:MM-HH:MM.

    Args:
        rng: Rango horario en formato flexible

    Returns:
        Rango normalizado (ej: "09:30-11:30")
    """
    s = (rng or "").strip()
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$", s)
    if not m:
        return s
    h1, m1, h2, m2 = map(int, m.groups())
    return f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"


def normalizar_semestre(semestre) -> Optional[str]:
    """
    Normaliza cualquier representación de semestre a '1' o '2'.
    Acepta: 1, 2, "1", "2", "1º Semestre", "2º Semestre",
            "1 Semestre", "semestre_1", "semestre_2", "S1"/"S2", etc.
    Returns:
        String '1' o '2', o None si no se puede normalizar
    """
    if semestre is None:
        return None
    if isinstance(semestre, int):
        return '1' if semestre == 1 else ('2' if semestre == 2 else None)
    s_str = str(semestre).strip().lower()
    if "2" in s_str:
        return '2'
    if "1" in s_str:
        return '1'
    return None


# ========= FASE 1: CARGA Y VALIDACIÓN =========
class ValidadorDatos:
    """
    Clase responsable de la FASE 1: Carga y Validación de datos.

    Realiza las siguientes operaciones:
        1.1 - Carga de datos desde JSON
        1.2 - Validación de asignaturas (semana_inicio, num_sesiones, grupos_lab_posibles)
        1.3 - Validación de horarios (letras usadas vs grupos_lab_posibles)

    Attributes:
        cfg: Configuración completa cargada desde JSON
        errores: Lista de errores detectados durante la validación
        grupos_lab_posibles: Diccionario con el número de grupos posibles por asignatura
    """

    def __init__(self, config_path: Path):
        """ Inicializar el validador. """
        self.config_path = config_path
        self.cfg: Dict = {}
        self.errores: List[ErrorValidacion] = []
        self.grupos_lab_posibles: Dict[Tuple[str, str, str], int] = {}  # (semestre, asignatura, grupo) -> num_grupos

    def ejecutar(self) -> Tuple[bool, Dict, List[ErrorValidacion]]:
        """
        Ejecutar la FASE 1 completa.

        Returns:
            Tupla con:
                - bool: True si la validación fue exitosa, False si hubo errores críticos
                - Dict: Configuración cargada
                - List[ErrorValidacion]: Lista de errores detectados
        """
        print("\n" + "=" * 70)
        print("FASE 1: CARGA Y VALIDACIÓN")
        print("=" * 70)

        # 1.1 - Cargar datos
        if not self._cargar_datos():
            return False, {}, self.errores

        # 1.2 - Validar asignaturas
        if not self._validar_asignaturas():
            return False, self.cfg, self.errores

        # 1.3 - Validar horarios
        if not self._validar_horarios():
            return False, self.cfg, self.errores

        # Resumen final
        self._mostrar_resumen()

        # Si llegamos aquí, todo OK
        tiene_criticos = any(e.tipo == "CRITICO" for e in self.errores)
        return not tiene_criticos, self.cfg, self.errores

    def _cargar_datos(self) -> bool:
        """
        1.1 - Cargar datos desde JSON y verificar estructura básica.

        Returns:
            True si la carga fue exitosa, False en caso contrario
        """
        print("\n[1.1] Cargando datos desde JSON...")

        try:
            self.cfg = load_configuration(self.config_path)
            print(f"  ✓ Configuración cargada: {self.config_path}")
        except FileNotFoundError:
            self.errores.append(ErrorValidacion(
                fase="FASE_1.1",
                tipo="CRITICO",
                mensaje=f"Archivo de configuración no encontrado: {self.config_path}",
                detalle={}
            ))
            return False
        except json.JSONDecodeError as e:
            self.errores.append(ErrorValidacion(
                fase="FASE_1.1",
                tipo="CRITICO",
                mensaje=f"Error al parsear JSON: {e}",
                detalle={}
            ))
            return False

        # Verificar estructura básica
        if "configuracion" not in self.cfg:
            self.errores.append(ErrorValidacion(
                fase="FASE_1.1",
                tipo="CRITICO",
                mensaje="Falta sección 'configuracion' en el JSON",
                detalle={}
            ))
            return False

        # Verificar subsecciones requeridas
        secciones_requeridas = ["asignaturas", "horarios", "alumnos", "aulas", "profesores", "calendario"]
        configuracion = self.cfg["configuracion"]

        for seccion in secciones_requeridas:
            if seccion not in configuracion:
                self.errores.append(ErrorValidacion(
                    fase="FASE_1.1",
                    tipo="CRITICO",
                    mensaje=f"Falta sección 'configuracion.{seccion}' en el JSON",
                    detalle={}
                ))
                return False

        print(f"  ✓ Estructura JSON válida")
        print(f"  ✓ Secciones encontradas: {', '.join(secciones_requeridas)}")

        return True

    def _get_total_semanas_calendario(self) -> int:
        """
        Obtener el número total de semanas desde el calendario configurado.

        Returns:
            int: Número total de semanas definidas en el calendario o 14 por defecto.
        """
        try:
            calendario_cfg = self.cfg.get("configuracion", {}).get("calendario", {})
            semanas_total = calendario_cfg.get("datos", {}).get("metadata", {}).get("limite_semanas")
            if isinstance(semanas_total, int) and semanas_total > 0:
                return semanas_total
            # Compatibilidad con metadatos anidados
            datos = calendario_cfg.get("datos", {})
            if isinstance(datos, dict):
                meta = datos.get("metadata", {})
                if isinstance(meta, dict):
                    semanas_total = meta.get("limite_semanas")
                    if isinstance(semanas_total, int) and semanas_total > 0:
                        return semanas_total
        except Exception:
            pass
        return 14  # valor por defecto

    def _validar_asignaturas(self) -> bool:
        """
        1.2 - Validar configuración de asignaturas.

        Por cada asignatura, verifica:
            - Existe semana_inicio
            - Existe num_sesiones
            - La fórmula es válida: (12 - semana_inicio + 1) % num_sesiones == 0, saber si se puede cuadrar la config
                            según 'semana_inicio' y 'num_sesiones'
            - Calcula grupos_lab_posibles = (12 - semana_inicio + 1) / num_sesiones, saber cuantas letras por
                            franja podemos poner

        Returns:
            True si no hay errores críticos, False en caso contrario
        """
        print("\n[1.2] Validando asignaturas...")

        asignaturas_data = self.cfg["configuracion"]["asignaturas"].get("datos", {})
        total_semanas_calendario = self._get_total_semanas_calendario()

        if not asignaturas_data:
            self.errores.append(ErrorValidacion(
                fase="FASE_1.2",
                tipo="CRITICO",
                mensaje="No hay asignaturas configuradas",
                detalle={}
            ))
            return False

        num_validadas = 0
        num_total = 0

        for asig_codigo, asig_data in asignaturas_data.items():
            semestre = asig_data.get("semestre", "Desconocido")
            grupos_asociados = asig_data.get("grupos_asociados", {})

            if not grupos_asociados:
                self.errores.append(ErrorValidacion(
                    fase="FASE_1.2",
                    tipo="ADVERTENCIA",
                    mensaje=f"No hay grupos asociados en {asig_codigo}",
                    detalle={"asignatura": asig_codigo}
                ))
                continue

            for grupo_codigo, grupo_data in grupos_asociados.items():
                cfg_lab = grupo_data.get("configuracion_laboratorio", {})
                semana_inicio = cfg_lab.get("semana_inicio")
                num_sesiones = cfg_lab.get("num_sesiones")

                num_total += 1

                # Validación 1: ¿Existen los parámetros?
                if semana_inicio is None or semana_inicio < 1:
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.2",
                        tipo="CRITICO",
                        mensaje=f"Falta 'semana_inicio' en {semestre}: {asig_codigo}",
                        detalle={"semestre": semestre, "asignatura": asig_codigo, "grupo": grupo_codigo,}
                    ))
                    continue

                if num_sesiones is None or num_sesiones < 1:
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.2",
                        tipo="CRITICO",
                        mensaje=f"Falta 'num_sesiones' en {semestre}: {asig_codigo}",
                        detalle={"semestre": semestre, "asignatura": asig_codigo,"grupo": grupo_codigo,}
                    ))
                    continue

                # Validación 2: ¿Son valores válidos?
                try:
                    semana_inicio = int(semana_inicio)
                    num_sesiones = int(num_sesiones)
                except (ValueError, TypeError):
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.2",
                        tipo="CRITICO",
                        mensaje=f"Valores no numéricos en {semestre}: {asig_codigo}",
                        detalle={
                            "semestre": semestre,
                            "asignatura": asig_codigo,
                            "grupo": grupo_codigo,
                            "semana_inicio": semana_inicio,
                            "num_sesiones": num_sesiones
                        }
                    ))
                    continue

                if semana_inicio < 1 or semana_inicio > total_semanas_calendario:
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.2",
                        tipo="CRITICO",
                        mensaje=f"semana_inicio fuera de rango [1-{total_semanas_calendario}] en {semestre}: {asig_codigo}",
                        detalle={
                            "semestre": semestre,
                            "asignatura": asig_codigo,
                            "grupo": grupo_codigo,
                            "semana_inicio": semana_inicio
                        }
                    ))
                    continue

                if num_sesiones < 1:
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.2",
                        tipo="CRITICO",
                        mensaje=f"num_sesiones debe ser >= 1 en {semestre}: {asig_codigo}",
                        detalle={
                            "semestre": semestre,
                            "asignatura": asig_codigo,
                            "grupo": grupo_codigo,
                            "num_sesiones": num_sesiones
                        }
                    ))
                    continue

                # Validación 3: Fórmula de grupos posibles
                semanas_disponibles = total_semanas_calendario - semana_inicio + 1

                if semanas_disponibles % num_sesiones != 0:
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.2",
                        tipo="CRITICO",
                        mensaje=f"""Fórmula inválida en {semestre}: {asig_codigo}, ajusta correctamente el valor de 'semana_inicio' y 'num_sesiones' """,
                        detalle={
                            "semestre": semestre,
                            "asignatura": asig_codigo,
                            "grupo": grupo_codigo,
                            "semana_inicio": semana_inicio,
                            "num_sesiones": num_sesiones,
                            "semanas_disponibles": semanas_disponibles,
                            "formula": f"({semanas_disponibles}) % {num_sesiones} != 0"
                        }
                    ))
                    continue

                # Calcular grupos_lab_posibles
                grupos_lab_posibles = semanas_disponibles // num_sesiones
                self.grupos_lab_posibles[(semestre, asig_codigo, grupo_codigo)] = grupos_lab_posibles

                num_validadas += 1
                print(f"  ✓ {semestre}:{asig_codigo} → {grupo_codigo} → grupos_lab_posibles={grupos_lab_posibles} "
                      f"(semana_inicio={semana_inicio}, num_sesiones={num_sesiones})")

        print(f"\n  Resumen: {num_validadas}/{num_total} validadas")

        # Si hay errores críticos, detener
        tiene_criticos = any(e.tipo == "CRITICO" for e in self.errores if e.fase == "FASE_1.2")
        return not tiene_criticos

    def _validar_horarios(self) -> bool:
        """
        1.3 - Validar configuración de horarios.

        Por cada grupo de cada asignatura con horarios configurados:
            - Recorre franjas y días del horarios_grid
            - Extrae todas las letras usadas en horarios_grid
            - Verifica que haya grupos asignados en horarios
            - Verifica que letras_usadas <= grupos_lab_posibles
            - Si hay error, no hay horarios válidos o faltan grupos, se marca como CRITICO

        Returns:
            True si no hay errores críticos, False en caso contrario
        """
        print("\n[1.3] Validando horarios...")

        horarios_data = self.cfg["configuracion"]["horarios"].get("datos", {})

        if not horarios_data:
            self.errores.append(ErrorValidacion(
                fase="FASE_1.3",
                tipo="CRITICO",
                mensaje="No hay horarios configurados. El sistema no puede continuar sin definir horarios.",
                detalle={}
            ))
            return False

        num_validadas = 0
        num_total = 0

        # Recorrer por semestre y asignatura
        for semestre, asignaturas in horarios_data.items():
            for asig_codigo, asig_data in asignaturas.items():
                grupos_asociados = asig_data.get("grupos", {})
                horarios_grid = asig_data.get("horarios_grid", {})

                # Validar que existan tanto grupos como horarios
                if not horarios_grid or not grupos_asociados:
                    self.errores.append(ErrorValidacion(
                        fase="FASE_1.3",
                        tipo="CRITICO",
                        mensaje=f"No hay horarios o grupos definidos para {semestre}:{asig_codigo}",
                        detalle={"semestre": semestre, "asignatura": asig_codigo}
                    ))
                    continue

                # Validar cada grupo de la asignatura
                for grupo_codigo in grupos_asociados.keys():
                    num_total += 1
                    letras_usadas: Set[str] = set()
                    hay_grupos_asignados = False

                    # Recorrer horarios_grid para extraer letras y verificar asignaciones
                    for franja, dias in horarios_grid.items():
                        for dia, info in dias.items():
                            if not isinstance(info, dict):
                                continue

                            grupos = info.get("grupos", [])
                            letras = info.get("letras", [])

                            # Verificar si este grupo tiene franjas asignadas
                            if grupo_codigo in grupos:
                                hay_grupos_asignados = True

                                # Acumular todas las letras usadas en horarios
                                if letras:
                                    letras_usadas.update(letras)

                    # Error si no hay franjas asignadas para este grupo
                    if not hay_grupos_asignados:
                        self.errores.append(ErrorValidacion(
                            fase="FASE_1.3",
                            tipo="ADVERTENCIA",
                            mensaje=f"No hay franjas con grupos asignados para {semestre}:{asig_codigo}:{grupo_codigo}",
                            detalle={
                                "semestre": semestre,
                                "asignatura": asig_codigo,
                                "grupo": grupo_codigo
                            }
                        ))
                        continue

                    # Buscar grupos_lab_posibles para este grupo específico
                    # Primero intentar con formato completo, luego buscar coincidencias parciales
                    grupos_lab_posibles = self.grupos_lab_posibles.get(
                        (f"{semestre}º Semestre", asig_codigo, grupo_codigo)
                    )

                    if grupos_lab_posibles is None:
                        # Búsqueda alternativa por asignatura y grupo
                        for (sem, asig, grupo), valor in self.grupos_lab_posibles.items():
                            if asig == asig_codigo and grupo == grupo_codigo:
                                grupos_lab_posibles = valor
                                break

                    # Error si no se encontró la configuración de grupos posibles
                    if grupos_lab_posibles is None:
                        self.errores.append(ErrorValidacion(
                            fase="FASE_1.3",
                            tipo="CRITICO",
                            mensaje=f"No se encontró grupos_lab_posibles para {semestre}:{asig_codigo}:{grupo_codigo}",
                            detalle={
                                "semestre": semestre,
                                "asignatura": asig_codigo,
                                "grupo": grupo_codigo
                            }
                        ))
                        continue

                    # Validación final: letras_usadas <= grupos_lab_posibles
                    num_letras = len(letras_usadas)
                    if num_letras > grupos_lab_posibles:
                        self.errores.append(ErrorValidacion(
                            fase="FASE_1.3",
                            tipo="CRITICO",
                            mensaje=f"Demasiadas letras configuradas en {semestre}:{asig_codigo}:{grupo_codigo}",
                            detalle={
                                "semestre": semestre,
                                "asignatura": asig_codigo,
                                "grupo": grupo_codigo,
                                "letras_usadas": sorted(letras_usadas),
                                "num_letras": num_letras,
                                "grupos_lab_posibles": grupos_lab_posibles,
                                "error": f"Se usan {num_letras} letras pero solo hay {grupos_lab_posibles} grupos posibles"
                            }
                        ))
                        continue

                    # Grupo validado correctamente
                    num_validadas += 1
                    print(f"  ✓ {semestre}:{asig_codigo}:{grupo_codigo} → letras={sorted(letras_usadas)} "
                          f"({num_letras}/{grupos_lab_posibles} grupos válidos)")

        print(f"\n  Resumen: {num_validadas} grupos de laboratorio validados de {num_total}")

        # Determinar si hay errores críticos
        tiene_criticos = any(e.tipo == "CRITICO" for e in self.errores if e.fase == "FASE_1.3")
        return not tiene_criticos

    def _mostrar_resumen(self) -> None:
        """"Mostrar resumen de la validación."""
        print("\n" + "-"*70)
        print("RESUMEN FASE 1")
        print("-"*70)

        num_criticos = sum(1 for e in self.errores if e.tipo == "CRITICO")
        num_advertencias = sum(1 for e in self.errores if e.tipo == "ADVERTENCIA")

        if num_criticos == 0 and num_advertencias == 0:
            print("  ✓ VALIDACIÓN EXITOSA - Sin errores")
        else:
            if num_criticos > 0:
                print(f"  ✗ ERRORES CRÍTICOS: {num_criticos}")
            if num_advertencias > 0:
                print(f"  ⚠ ADVERTENCIAS: {num_advertencias}")

        print(f"  • Total grupos validados: {len(self.grupos_lab_posibles)}\n")


# ========= FASE 2: CÁLCULO DE FECHAS POR LETRA =========
class CalculadorFechas:
    """
    Clase responsable de la FASE 2: Cálculo de fechas por letra en grados simples.

    Realiza las siguientes operaciones:
        2.1 - Obtener fechas del calendario filtradas por semana_inicio
        2.2 - Dividir fechas según num_sesiones para cada letra
        2.3 - Crear mapeo completo: (semestre, asignatura, grupo, dia, letra) -> [fechas]

    Attributes:
        cfg: Configuración completa
        grupos_lab_posibles: Diccionario con número de grupos posibles por (semestre, asig, grupo)
        mapeo_fechas: Diccionario resultante con fechas por letra
    """

    def __init__(self, cfg: Dict, grupos_lab_posibles: Dict[Tuple[str, str, str], int]):
        """Inicializar el calculador de fechas."""
        self.cfg = cfg
        self.grupos_lab_posibles = grupos_lab_posibles
        self.mapeo_fechas: Dict[Tuple[str, str, str, str, str], List[str]] = {}

    def ejecutar(self) -> Tuple[bool, Dict[Tuple[str, str, str, str, str], List[str]]]:
        """
        Ejecutar la FASE 2 completa.

        Returns:
            Tupla con:
                - bool: True si el cálculo fue exitoso
                - Dict: mapeo_fechas resultante
        """
        print("\n" + "=" * 70)
        print("FASE 2: CÁLCULO DE FECHAS POR LETRA")
        print("=" * 70)

        # 2.1 y 2.2 - Calcular fechas para cada grupo
        if not self._calcular_fechas_grupos():
            return False, {}

        # Resumen final
        self._mostrar_resumen()

        return True, self.mapeo_fechas

    def _obtener_fechas_calendario(self, dia: str, semestre: str) -> List[str]:
        """
        Obtener todas las fechas del calendario para un día y semestre específico.

        Args:
            dia: Día de la semana (ej: "Lunes", "Martes")
            semestre: Semestre (ej: "1 Semestre", "2 Semestre")

        Returns:
            Lista de fechas en formato dd/mm/yyyy ordenadas cronológicamente
        """
        calendario_datos = self.cfg.get("configuracion", {}).get("calendario", {}).get("datos", {})

        # Determinar qué clave de semestre usar
        semestre_key = "semestre_1" if "1" in semestre else "semestre_2"
        semestre_datos = calendario_datos.get(semestre_key, {})

        # Normalizar el día
        dia_normalizado = dia.strip().capitalize()
        reemplazos = {"Miercoles": "Miércoles", "Sabado": "Sábado"}
        dia_normalizado = reemplazos.get(dia_normalizado, dia_normalizado)

        # Extraer fechas donde horario_asignado coincida
        fechas = []
        for fecha_info in semestre_datos.values():
            if isinstance(fecha_info, dict):
                if fecha_info.get("horario_asignado") == dia_normalizado:
                    fecha_str = fecha_info.get("fecha", "")
                    if fecha_str:
                        # Convertir yyyy-mm-dd a dd/mm/yyyy
                        partes = fecha_str.split("-")
                        if len(partes) == 3:
                            fechas.append(f"{partes[2]}/{partes[1]}/{partes[0]}")

        return fechas

    def _filtrar_fechas_desde_semana(self, fechas: List[str], semana_inicio: int) -> List[str]:
        """
        Filtrar fechas a partir de una semana específica.

        Args:
            fechas: Lista de fechas ordenadas cronológicamente
            semana_inicio: Número de semana desde la cual comenzar (1-X)

        Returns:
            Lista de fechas filtradas desde semana_inicio
        """
        # Índice base 0: semana 1 = índice 0
        indice_inicio = semana_inicio - 1

        if indice_inicio >= len(fechas):
            return []

        return fechas[indice_inicio:]

    def _dividir_fechas_por_letras(self, fechas: List[str], num_letras: int) -> Dict[str, List[str]]:
        """
        Dividir fechas entre letras de forma intercalada.

        Ejemplo con 4 fechas y 2 letras:
            Letra A: [fecha0, fecha2] (índices pares)
            Letra B: [fecha1, fecha3] (índices impares)

        Args:
            fechas: Lista de fechas ordenadas
            num_letras: Número de letras a generar

        Returns:
            Diccionario {letra: [lista_fechas]}
        """
        resultado = {}
        letras = [chr(65 + i) for i in range(num_letras)]  # A, B, C...

        for i, letra in enumerate(letras):
            # Tomar fechas con índices: i, i+num_letras, i+2*num_letras...
            fechas_letra = fechas[i::num_letras]
            resultado[letra] = fechas_letra

        return resultado

    def _calcular_fechas_grupos(self) -> bool:
        """
        2.1 y 2.2 - Calcular fechas para todos los grupos con horarios configurados.

        Por cada grupo:
            - Obtiene días configurados en horarios_grid
            - Filtra fechas desde semana_inicio
            - Divide fechas según num_sesiones para cada letra
            - Guarda en mapeo_fechas

        Returns:
            True si el cálculo fue exitoso
        """
        print("\n[2.1-2.2] Calculando fechas por letra para cada grupo...")

        asignaturas_data = self.cfg["configuracion"]["asignaturas"].get("datos", {})
        horarios_data = self.cfg["configuracion"]["horarios"].get("datos", {})

        num_grupos_procesados = 0

        # Recorrer asignaturas para obtener configuración de laboratorio
        for asig_codigo, asig_data in asignaturas_data.items():
            semestre = asig_data.get("semestre", "Desconocido")
            grupos_asociados = asig_data.get("grupos_asociados", {})

            # Buscar horarios para esta asignatura
            horarios_asig = None
            for sem_key, asigs_horarios in horarios_data.items():
                if asig_codigo in asigs_horarios:
                    horarios_asig = asigs_horarios[asig_codigo]
                    break

            if not horarios_asig:
                continue  # Sin horarios configurados, siguiente asignatura

            horarios_grid = horarios_asig.get("horarios_grid", {})
            if not horarios_grid:
                continue

            # Procesar cada grupo de la asignatura
            for grupo_codigo in grupos_asociados.keys():
                cfg_lab = grupos_asociados[grupo_codigo].get("configuracion_laboratorio", {})
                semana_inicio = cfg_lab.get("semana_inicio")
                num_sesiones = cfg_lab.get("num_sesiones")

                # Ignorar grupos dobles (LLNNN)
                if not PAT_SIMPLE.match(grupo_codigo):
                    continue

                if semana_inicio is None or num_sesiones is None:
                    continue  # Sin configuración válida

                # Obtener grupos_lab_posibles para este grupo
                grupos_posibles = self.grupos_lab_posibles.get((semestre, asig_codigo, grupo_codigo))
                if grupos_posibles is None:
                    continue

                # Extraer días únicos donde este grupo tiene horarios
                dias_usados: Set[str] = set()
                letras_por_dia: Dict[str, Set[str]] = {}

                for franja, dias in horarios_grid.items():
                    for dia, info in dias.items():
                        if not isinstance(info, dict):
                            continue

                        grupos = info.get("grupos", [])
                        letras = info.get("letras", [])

                        # Si este grupo está en esta franja/día
                        if grupo_codigo in grupos:
                            dias_usados.add(dia)
                            if dia not in letras_por_dia:
                                letras_por_dia[dia] = set()
                            letras_por_dia[dia].update(letras)

                if not dias_usados:
                    continue  # Este grupo no tiene horarios asignados

                # Por cada día usado, calcular fechas por letra
                for dia in dias_usados:
                    # 2.1 - Obtener fechas del calendario para este día
                    fechas_calendario = self._obtener_fechas_calendario(dia, semestre)

                    if not fechas_calendario:
                        print(f"  ⚠ {semestre}:{asig_codigo}:{grupo_codigo} - Sin fechas en calendario para {dia}")
                        continue

                    # Filtrar desde semana_inicio
                    fechas_filtradas = self._filtrar_fechas_desde_semana(fechas_calendario, semana_inicio)

                    if not fechas_filtradas:
                        print(
                            f"  ⚠ {semestre}:{asig_codigo}:{grupo_codigo} - Sin fechas disponibles desde semana {semana_inicio} para {dia}")
                        continue

                    # 2.2 - Dividir fechas entre letras
                    fechas_por_letra = self._dividir_fechas_por_letras(fechas_filtradas, grupos_posibles)

                    # Obtener letras realmente usadas en este día
                    letras_usadas = letras_por_dia.get(dia, set())

                    # 2.3 - Guardar en mapeo_fechas solo las letras usadas
                    for letra in letras_usadas:
                        if letra in fechas_por_letra:
                            clave = (semestre, asig_codigo, grupo_codigo, dia, letra)
                            self.mapeo_fechas[clave] = fechas_por_letra[letra]

                            print(f"  ✓ {semestre}:{asig_codigo}:{grupo_codigo} | {dia} | Letra {letra} → "
                                  f"{len(fechas_por_letra[letra])} fechas calculadas:{fechas_por_letra[letra]}")

                num_grupos_procesados += 1

        print(f"\n  Total grupos procesados: {num_grupos_procesados}")
        print(f"  Total combinaciones (semestre, asig, grupo, dia, letra): {len(self.mapeo_fechas)}")

        return True

    def _mostrar_resumen(self) -> None:
        """Mostrar resumen del cálculo de fechas."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 2")
        print("-" * 70)

        if len(self.mapeo_fechas) == 0:
            print("  ⚠ No se calcularon fechas (posible error de configuración)\n")
        else:
            print(f"  ✓ CÁLCULO EXITOSO")
            print(f"  • Combinaciones generadas: {len(self.mapeo_fechas)}")

            # Estadísticas por letra
            letras_count = {}
            for (_, _, _, _, letra) in self.mapeo_fechas.keys():
                letras_count[letra] = letras_count.get(letra, 0) + 1

            print(f"  • Distribución por letra: {dict(sorted(letras_count.items()))}\n")


# ========= FASE 3: AULA PREFERENTE =========
class AsignadorAulaPreferente:
    """
    Clase responsable de la FASE 3: Asignación de aula preferente.

    Realiza las siguientes operaciones:
        3.1 - Por cada asignatura, buscar aulas asociadas
        3.2 - Seleccionar el aula con MAYOR capacidad
        3.3 - Crear mapeo: (semestre, asignatura) -> nombre_aula

    Attributes:
        cfg: Configuración completa
        aulas_preferentes: Diccionario resultante con aula preferente por asignatura
    """

    def __init__(self, cfg: Dict):
        """Inicializar el asignador de aulas preferentes."""
        self.cfg = cfg
        self.aulas_preferentes: Dict[Tuple[str, str], str] = {}
        self.conflictos_aulas: List[Dict] = []

    def ejecutar(self) -> tuple[bool, dict[Any, Any]] | tuple[bool, dict[tuple[str, str], str], list[dict]]:
        """
        Ejecutar la FASE 3 completa.

        Returns:
            Tupla con:
                - bool: True si la asignación fue exitosa
                - Dict: aulas_preferentes resultante
        """
        print("\n" + "=" * 70)
        print("FASE 3: AULA PREFERENTE")
        print("=" * 70)

        # 3.1, 3.2, 3.3 - Asignar aulas preferentes
        if not self._asignar_aulas_preferentes():
            return False, {}

        # Resumen final
        self._mostrar_resumen()

        return True, self.aulas_preferentes, self.conflictos_aulas

    def _obtener_aulas_por_asignatura(self, asignatura: str) -> List[Tuple[str, int]]:
        """
        Obtener todas las aulas asociadas a una asignatura.

        Args:
            asignatura: Código de la asignatura (ej: "SII")

        Returns:
            Lista de tuplas (nombre_aula, capacidad) que tienen esta asignatura
        """
        aulas_data = self.cfg.get("configuracion", {}).get("aulas", {}).get("datos", {})

        aulas_encontradas = []

        for nombre_aula, aula_info in aulas_data.items():
            # Verificar que el aula esté disponible
            if not aula_info.get("disponible", True):
                continue

            # Obtener asignaturas asociadas
            asignaturas_asociadas = aula_info.get("asignaturas_asociadas", [])

            # Si esta asignatura está en la lista
            if asignatura in asignaturas_asociadas:
                capacidad = aula_info.get("capacidad", 0)
                aulas_encontradas.append((nombre_aula, capacidad))

        return aulas_encontradas

    def _seleccionar_aula_mayor_capacidad(self, aulas: List[Tuple[str, int]]) -> Optional[str]:
        """
        Seleccionar el aula con mayor capacidad de una lista.

        Args:
            aulas: Lista de tuplas (nombre_aula, capacidad)

        Returns:
            Nombre del aula con mayor capacidad, o None si la lista está vacía
        """
        if not aulas:
            return None

        # Ordenar por capacidad (descendente) y tomar la primera
        aulas_ordenadas = sorted(aulas, key=lambda x: x[1], reverse=True)
        return aulas_ordenadas[0][0]

    def _asignar_aulas_preferentes(self) -> bool:
        """
        3.1, 3.2, 3.3 - Asignar aula preferente para cada asignatura.

        Por cada asignatura:
            - Buscar todas las aulas asociadas
            - Seleccionar la de mayor capacidad
            - Guardar en aulas_preferentes

        Returns:
            True si la asignación fue exitosa
        """
        print("\n[3.1-3.3] Asignando aulas preferentes...")

        asignaturas_data = self.cfg.get("configuracion", {}).get("asignaturas", {}).get("datos", {})

        if not asignaturas_data:
            print("  ⚠ No hay asignaturas configuradas")
            return False  # Es error crítico

        num_asignadas = 0
        num_sin_aula = 0

        # Procesar cada asignatura
        for asig_codigo, asig_data in asignaturas_data.items():
            semestre = asig_data.get("semestre", "Desconocido")

            # 3.1 - Buscar aulas asociadas a esta asignatura
            aulas_disponibles = self._obtener_aulas_por_asignatura(asig_codigo)

            if not aulas_disponibles:
                print(f"  ⚠ {semestre}:{asig_codigo} - Sin aulas asociadas")
                num_sin_aula += 1
                self.conflictos_aulas.append({
                    "semestre": semestre,
                    "asignatura": asig_codigo,
                    "grupo": "—",
                    "dia": "—",
                    "franja": "—",
                    "fecha": "—",
                    "aula": "NO ASIGNADA",
                    "profesor": "—",
                    "detalle": f"Asignatura {asig_codigo} sin aulas asociadas en configuración"
                })
                continue

            # 3.2 - Seleccionar aula con mayor capacidad
            aula_preferente = self._seleccionar_aula_mayor_capacidad(aulas_disponibles)

            if aula_preferente is None:
                print(f"  ⚠ {semestre}:{asig_codigo} - No se pudo seleccionar aula")
                num_sin_aula += 1
                continue

            # 3.3 - Guardar en mapeo
            clave = (semestre, asig_codigo)
            self.aulas_preferentes[clave] = aula_preferente

            # Obtener capacidad para el log
            capacidad = next((cap for nombre, cap in aulas_disponibles if nombre == aula_preferente), 0)

            if len(aulas_disponibles) > 1:
                print(f"  ✓ {semestre}:{asig_codigo} → {aula_preferente} (capacidad: {capacidad}) "
                      f"[{len(aulas_disponibles)} aulas disponibles]")
            else:
                print(f"  ✓ {semestre}:{asig_codigo} → {aula_preferente} (capacidad: {capacidad})")

            num_asignadas += 1

        print(f"\n  Total asignaturas con aula: {num_asignadas}")
        if num_sin_aula > 0:
            print(f"  Total asignaturas sin aula: {num_sin_aula}")

        return True

    def _mostrar_resumen(self) -> None:
        """Mostrar resumen de la asignación de aulas."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 3")
        print("-" * 70)

        if len(self.aulas_preferentes) == 0:
            print("  ⚠ No se asignaron aulas preferentes\n")
        else:
            print(f"  ✓ ASIGNACIÓN EXITOSA")
            print(f"  • Asignaturas con aula preferente: {len(self.aulas_preferentes)}")

            # Estadísticas por aula
            aulas_count = {}
            for aula in self.aulas_preferentes.values():
                aulas_count[aula] = aulas_count.get(aula, 0) + 1

            print(f"  • Distribución de uso: {dict(sorted(aulas_count.items()))}\n")


# ========= FASE 4: CREAR GRUPOS DE LABORATORIO =========
class CreadorGruposLab:
    """
    Clase responsable de la FASE 4: Creación de grupos de laboratorio.

    Realiza las siguientes operaciones:
        4.1 - Por cada combinación en mapeo_fechas, crear 1 o + objetos GrupoLab
        4.2 - Extraer franja horaria de horarios_grid
        4.3 - Asignar aula y capacidad de aulas_preferentes
        4.4 - Determinar si es slot_mixto
        4.5 - Generar label único (A404-01, A404-02...)
        4.6 - Agrupar por (dia, franja) para uso en FASE 7

    Attributes:
        cfg: Configuración completa
        mapeo_fechas: Diccionario con fechas por letra (de FASE 2)
        aulas_preferentes: Diccionario con aulas por asignatura (de FASE 3)
        grupos_creados: Lista de objetos GrupoLab creados
        grupos_por_slot: Diccionario agrupando grupos por (dia, franja)
    """

    def __init__(self, cfg: Dict, mapeo_fechas: Dict[Tuple[str, str, str, str, str], List[str]], aulas_preferentes: Dict[Tuple[str, str], str]):
        """Inicializar el creador de grupos."""
        self.cfg = cfg
        self.mapeo_fechas = mapeo_fechas
        self.aulas_preferentes = aulas_preferentes
        self.grupos_creados: List[GrupoLab] = []
        self.grupos_por_slot: Dict[Tuple[str, str], List[GrupoLab]] = {}
        self.contador_labels: Dict[Tuple[str, str], int] = {}
        self.conflictos_aulas: List[Dict] = []

    def ejecutar(self) -> tuple[bool, list[Any], dict[Any, Any]] | tuple[bool, list[GrupoLab], dict[tuple[str, str],
    list[GrupoLab]], list[dict]]:
        """
        Ejecutar la FASE 4 completa.

        Returns:
            Tupla con:
                - bool: True si la creación fue exitosa
                - List[GrupoLab]: Lista de grupos de laboratorio creados
                - Dict: Grupos de Laboratorio agrupados por (día, franja)
        """
        print("\n" + "=" * 70)
        print("FASE 4: CREAR GRUPOS DE LABORATORIO")
        print("=" * 70)

        # 4.1-4.6 - Crear grupos de laboratorio
        if not self._crear_grupos_laboratorio():
            return False, [], {}

        # Resumen final
        self._mostrar_resumen()

        return True, self.grupos_creados, self.grupos_por_slot, self.conflictos_aulas

    def _obtener_franjas_de_horarios_grid(self, semestre: str, asignatura: str,
                                          grupo: str, dia: str, letra: str) -> Optional[List[str]]:
        """
        Buscar las franjas horarias en horarios_grid para un grupo específico.

        Recorre el horarios_grid buscando todas las franjas donde:
            - El grupo está en la lista de grupos
            - La letra está en la lista de letras
            - El día coincide

        Args:
            semestre: Semestre (ej: "1 Semestre")
            asignatura: Código de asignatura (ej: "SII")
            grupo: Código de grupo (ej: "A404")
            dia: Día de la semana (ej: "Lunes")
            letra: Letra de grupo laboratorio asignado (ej: "A")

        Returns:
            Lista de franjas horarias normalizadas (ej: ["09:30-11:30"]) o None si no se encuentra
        """
        horarios_data = self.cfg.get("configuracion", {}).get("horarios", {}).get("datos", {})

        # Normalizar semestre de entrada
        sem_norm = normalizar_semestre(semestre)
        if sem_norm is None:
            return None

        # Buscar asignatura en el semestre correspondiente
        asig_data = None
        for sem_key, asigs in horarios_data.items():
            if sem_norm not in sem_key:
                continue
            if asignatura in asigs:
                asig_data = asigs[asignatura]
                break

        if not asig_data:
            return None

        horarios_grid = asig_data.get("horarios_grid", {})
        if not isinstance(horarios_grid, dict) or not horarios_grid:
            return None

        # Recolectar todas las franjas donde aparece este grupo con esta letra en este día
        franjas = []

        for franja_raw, dias in horarios_grid.items():
            info = dias.get(dia)
            if not isinstance(info, dict):
                continue

            # Verificar que tenga la letra asignada
            if letra not in info.get("letras", []):
                continue

            # Verificar que tenga el grupo asignado
            grupos = info.get("grupos") or []
            if grupo not in grupos:
                continue

            # Normalizar y agregar la franja
            franja_norm = normalize_time_range(franja_raw)
            franjas.append(franja_norm)

        # Ordenar cronológicamente
        # franjas = sorted(set(franjas), key=lambda x: time_start_minutes(x))

        return franjas if franjas else None

    def _determinar_slot_mixto(self, semestre: str, asignatura: str,
                               grupo: str, dia: str, franja: str) -> bool:
        """
        Determinar si un slot (día + franja) contiene grupos simples Y dobles.

        Un slot es mixto cuando en la misma franja y día conviven:
            - Grupos de grado simple (ej: A404)
            - Grupos de doble grado (ej: EE403)

        Esta información está en el campo "mixta" del horarios_grid.

        Args:
            semestre: Semestre
            asignatura: Código de asignatura
            grupo: Código de grupo
            dia: Día de la semana
            franja: Franja horaria normalizada

        Returns:
            True si el slot es mixto, False en caso contrario
        """
        horarios_data = self.cfg.get("configuracion", {}).get("horarios", {}).get("datos", {})

        # Buscar horarios para esta asignatura
        for sem_key, asigs in horarios_data.items():
            if asignatura not in asigs:
                continue

            horarios_grid = asigs[asignatura].get("horarios_grid", {})

            # Buscar la franja específica
            for franja_key, dias in horarios_grid.items():
                if normalize_time_range(franja_key) != franja:
                    continue

                if dia not in dias:
                    continue

                info = dias[dia]
                if not isinstance(info, dict):
                    continue

                # Verificar si está marcado como mixto
                return bool(info.get("mixta", False))

        return False

    def _generar_label(self, asignatura: str, grupo: str) -> str:
        """
        Generar label único para un grupo (ej: A404-01, A404-02...).

        Generar label único para un grupo dentro de una asignatura.
        Reinicia numeración al cambiar de asignatura.

        Args:
            grupo: Código de grupo base (ej: "A404")

        Returns:
            Label único con formato GRUPO-NN
        """
        clave = (asignatura, grupo)
        if clave not in self.contador_labels:
            self.contador_labels[clave] = 0
        self.contador_labels[clave] += 1
        numero = self.contador_labels[clave]
        return f"{grupo}-{numero:02d}"

    def _obtener_capacidad_aula(self, nombre_aula: str) -> int:
        """
        Obtener la capacidad de un aula desde la configuración.

        Args:
            nombre_aula: Nombre del aula

        Returns:
            Capacidad del aula, o 0 si no se encuentra
        """
        aulas_data = self.cfg.get("configuracion", {}).get("aulas", {}).get("datos", {})

        if nombre_aula in aulas_data:
            return aulas_data[nombre_aula].get("capacidad", 0)

        return 0

    # new
    def _buscar_grupo_doble_en_mixto(self, asignatura: str, dia: str, franja: str, grupo_simple: str) -> Optional[str]:
        """
        Buscar el grupo de doble grado asociado a un grupo simple en una franja mixta.

        En las franjas mixtas, conviven grupos simples (A404) y dobles (EE403).
        Esta función identifica cuál es el grupo doble que comparte la franja
        con el grupo simple especificado.

        Args:
            asignatura: Código de asignatura (ej: "SII")
            dia: Día de la semana (ej: "Lunes")
            franja: Franja horaria (ej: "09:30-11:30")
            grupo_simple: Código del grupo simple (ej: "A404")

        Returns:
            Código del grupo doble encontrado (ej: "EE403"), o None si no hay
        """
        horarios_data = self.cfg.get("configuracion", {}).get("horarios", {}).get("datos", {})

        for _, asigs in horarios_data.items():
            if asignatura not in asigs:
                continue

            horarios_grid = asigs[asignatura].get("horarios_grid", {})
            if franja not in horarios_grid:
                continue

            info = horarios_grid[franja].get(dia)
            if not isinstance(info, dict):
                continue

            # Solo consideramos franjas marcadas como mixta
            if not bool(info.get("mixta", False)):
                continue

            grupos = info.get("grupos", [])
            if grupo_simple not in grupos:
                continue

            # Devolver el primer grupo diferente al simple
            for grupo in grupos:
                if grupo != grupo_simple:
                    return grupo

        return None

    def _crear_grupos_laboratorio(self) -> bool:
        """
        4.1-4.6 - Crear todos los grupos de laboratorio.

        Por cada combinación en mapeo_fechas:
            - Extraer datos de horarios_grid
            - Obtener aula preferente y capacidad
            - Determinar si es slot mixto
            - Generar label único
            - Crear objeto GrupoLab
            - Agrupar por (dia, franja)

        Returns:
            True si la creación fue exitosa
        """
        print("\n[4.1-4.6] Creando grupos de laboratorio...")

        if not self.mapeo_fechas:
            print("  ⚠ No hay combinaciones en mapeo_fechas")
            return False  # Error crítico

        num_creados = 0
        num_sin_franja = 0
        num_sin_aula = 0

        # Recorrer combinaciones de mapeo_fechas ordenadas por semestre → asignatura → grupo → letra
        for (semestre, asignatura, grupo, dia, letra), fechas in sorted(
                self.mapeo_fechas.items(),
                key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][4])  # semestre, asignatura, grupo, letra
        ):

            # 4.2 - Obtener franja horaria desde horarios_grid
            franjas = self._obtener_franjas_de_horarios_grid(semestre, asignatura, grupo, dia, letra)

            if franjas is None:
                print(f"  ⚠ {semestre}:{asignatura}:{grupo} - No se encontró franja para {dia}")
                num_sin_franja += 1
                continue

            # Procesar cada franja encontrada (puede haber múltiples)
            for franja in franjas:
                # 4.3 - Obtener aula preferente asignada en FASE 3
                aula_preferente = self.aulas_preferentes.get((semestre, asignatura))

                if aula_preferente is None:
                    print(f"  ⚠ {semestre}:{asignatura}:{grupo} - No hay aula preferente asignada")
                    num_sin_aula += 1
                    self.conflictos_aulas.append({
                        "semestre": semestre,
                        "asignatura": asignatura,
                        "grupo": f"{grupo}-{letra}",
                        "dia": dia,
                        "franja": "—",
                        "fecha": "—",
                        "aula": "NO ASIGNADA",
                        "profesor": "—",
                        "detalle": f"Grupo {grupo} letra {letra} sin aula asignada (Fase 4 no encontró aulas)"
                    })
                    continue

                # Obtener capacidad del aula
                capacidad = self._obtener_capacidad_aula(aula_preferente)

                # 4.4 - Determinar si es slot mixto
                is_slot_mixto = self._determinar_slot_mixto(semestre, asignatura, grupo, dia, franja)

                # 4.5 - Generar label único para este grupo de laboratorio
                label = self._generar_label(asignatura, grupo)

                # Determinar tipo de grupo (simple/doble)
                grupo_simple = ""
                grupo_doble = None

                if PAT_SIMPLE.match(grupo):
                    grupo_simple = grupo

                # Si es un slot mixto, buscar el grupo doble asociado
                if is_slot_mixto:
                    grupo_doble = self._buscar_grupo_doble_en_mixto(asignatura, dia, franja, grupo_simple)

                # 4.1 - Crear objeto GrupoLab con toda la información recopilada
                grupo_lab = GrupoLab(
                    semestre=semestre,
                    asignatura=asignatura,
                    label=label,
                    dia=dia,
                    franja=franja,
                    letra=letra,
                    aula=aula_preferente,
                    capacidad=capacidad,
                    profesor="",  # Se asignará en FASE 6
                    profesor_id=None,
                    is_slot_mixto=is_slot_mixto,
                    grupo_simple=grupo_simple,
                    grupo_doble=grupo_doble,
                    alumnos=[],  # Se asignará en FASE 5
                    fechas=fechas
                )

                self.grupos_creados.append(grupo_lab)

                # 4.6 - Agrupar por (dia, franja) para facilitar la FASE 7 (intercalado de fechas)
                slot_key = (dia, franja)
                if slot_key not in self.grupos_por_slot:
                    self.grupos_por_slot[slot_key] = []
                self.grupos_por_slot[slot_key].append(grupo_lab)

                num_creados += 1

                # Log informativo ---------------------------------------------------------------------------------------------------------------------------------------------
                #dsf
                # === BLOQUE DE IMPRESIÓN AGRUPADA POR SEMESTRE Y ASIGNATURA ===
                mixto_str = f" [MIXTO con {grupo_doble}]" if is_slot_mixto else ""

                # Mostrar encabezado de semestre si cambia
                if not hasattr(self, "_ultimo_semestre") or self._ultimo_semestre != semestre:
                    print(f"\n[{semestre}]")
                    self._ultimo_semestre = semestre
                    self._ultima_asignatura = None  # reiniciar asignatura

                # Mostrar encabezado de asignatura si cambia
                if not hasattr(self, "_ultima_asignatura") or self._ultima_asignatura != asignatura:
                    print(f"  [{asignatura}]")
                    self._ultima_asignatura = asignatura

                # Mostrar grupo dentro del bloque
                print(f"    ✓ {label} | {dia} {franja} | Letra {letra} | "
                      f"{aula_preferente} (cap: {capacidad}){mixto_str}")

        print(f"\n  Total grupos creados: {num_creados}")
        if num_sin_franja > 0:
            print(f"  ⚠ Grupos sin franja: {num_sin_franja}")
        if num_sin_aula > 0:
            print(f"  ⚠ Grupos sin aula: {num_sin_aula}")

        return True

    def _mostrar_resumen(self) -> None:
        """Mostrar resumen de la creación de grupos."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 4")
        print("-" * 70)

        if len(self.grupos_creados) == 0:
            print("  ⚠ No se crearon grupos de laboratorio\n")
        else:
            print(f"  ✓ CREACIÓN EXITOSA")
            print(f"  • Grupos creados: {len(self.grupos_creados)}")
            print(f"  • Slots únicos (dia, franja): {len(self.grupos_por_slot)}")

            # Estadísticas por tipo
            grupos_simples = sum(1 for g in self.grupos_creados if g.grupo_simple and not g.grupo_doble)
            grupos_dobles = sum(1 for g in self.grupos_creados if g.grupo_doble)

            print(f"  • Grupos simples: {grupos_simples}")
            if grupos_dobles > 0:
                print(f"  • Grupos dobles: {grupos_dobles}")

            # Distribución por día
            dias_count = {}
            for grupo in self.grupos_creados:
                dias_count[grupo.dia] = dias_count.get(grupo.dia, 0) + 1

            print(
                f"  • Distribución por día: {dict(sorted(dias_count.items(), key=lambda x: DAY_ORDER.get(x[0], 99)))}\n"
            )


# ========= FASE 5: ASIGNADOR DE ALUMNOS =========
class AsignadorAlumnos:
    """
    Clase responsable de la FASE 5: Asignación de Alumnos a Grupos.

    Esta fase toma los grupos creados en la Fase 4 y asigna los alumnos
    matriculados siguiendo un algoritmo que respeta todas las restricciones
    del sistema (grupos simples/dobles, capacidades, balanceo, etc.).

    Attributes:
        cfg: Configuración completa del sistema
        grupos_creados: Lista de grupos creados en Fase 4
        avisos: Lista de advertencias generadas durante la asignación
        alumno_simple: Mapeo de alumno_id -> grupo_simple
        alumno_doble: Mapeo de alumno_id -> grupo_doble
        asignatura_actual: Código de la asignatura que se está procesando
        semestre_actual: Semestre que se está procesando
    """

    def __init__(self, cfg: Dict, grupos_creados: List[GrupoLab]):
        """
        Inicializar el asignador de alumnos.

        Args:
            cfg: Configuración completa del sistema
            grupos_creados: Lista de grupos creados en Fase 4
        """
        self.cfg = cfg
        self.grupos_creados = grupos_creados
        self.avisos: List[str] = []
        self.conflictos_alumnos: List[Dict] = []

        # Mapeos de alumnos (se construyen por asignatura)
        self.alumno_simple: Dict[str, str] = {}  # alumno_id -> grupo_simple
        self.alumno_doble: Dict[str, str] = {}  # alumno_id -> grupo_doble

        # Control de contexto actual
        self.asignatura_actual = ""
        self.semestre_actual = ""

    def ejecutar(self) -> tuple[bool, list[GrupoLab], list[str], list[dict]]:
        """
        Ejecutar la FASE 5 completa.

        Returns:
            Tupla con:
                - bool: True si la asignación fue exitosa
                - List[GrupoLab]: Lista de grupos con alumnos asignados
                - List[str]: Lista de avisos generados
        """
        print("\n" + "=" * 70)
        print("FASE 5: ASIGNACIÓN DE ALUMNOS")
        print("=" * 70)

        # Agrupar por (semestre, asignatura)
        grupos_por_asignatura: Dict[Tuple[str, str], List[GrupoLab]] = {}
        for grupo in self.grupos_creados:
            key = (grupo.semestre, grupo.asignatura)
            if key not in grupos_por_asignatura:
                grupos_por_asignatura[key] = []
            grupos_por_asignatura[key].append(grupo)

        # Procesar cada asignatura
        for (semestre, asignatura), grupos in grupos_por_asignatura.items():
            self.semestre_actual = semestre
            self.asignatura_actual = asignatura

            print(f"\n[5] Procesando {semestre} - {asignatura}...")

            # 5.1 - Construir mapeos de alumnos para esta asignatura
            self._construir_mapeos_alumnos(asignatura)

            # 5.2 - Asignar alumnos dobles
            self._asignar_alumnos_dobles(grupos)

            # 5.3 - Asignar alumnos simples
            self._asignar_alumnos_simples(grupos)

            # 5.4 - Ya se distribuyó con mínima carga

            # 5.5 - Balance de paridad
            self._balancear_paridad(grupos)

            # 5.6 - Verificar capacidad
            self._verificar_capacidad(grupos)

        # Resumen final
        self._mostrar_resumen()

        return True, self.grupos_creados, self.avisos, self.conflictos_alumnos

    def _construir_mapeos_alumnos(self, asignatura: str) -> None:
        """
        5.1 - Construir mapeos de alumnos para la asignatura actual.

        Crea dos diccionarios:
            - alumno_simple: mapea alumno_id -> grupo_simple
            - alumno_doble: mapea alumno_id -> grupo_doble

        Args:
            asignatura: Código de la asignatura
        """
        print(f"  [5.1] Construyendo mapeos de alumnos...")

        # Limpiar mapeos previos
        self.alumno_simple.clear()
        self.alumno_doble.clear()

        # Obtener datos de alumnos
        alumnos_data = self.cfg.get("configuracion", {}).get("alumnos", {}).get("datos", {}) or {}

        # Construir mapeos
        for alumno_id, alumno_data in alumnos_data.items():
            asigs_matriculadas = alumno_data.get("asignaturas_matriculadas", {}) or {}

            # Verificar si el alumno está matriculado en esta asignatura
            if asignatura not in asigs_matriculadas:
                continue

            asig_info = asigs_matriculadas[asignatura]
            if not isinstance(asig_info, dict):
                continue

            # Verificar que esté matriculado y no tenga el lab aprobado
            if not asig_info.get("matriculado", False):
                continue
            if asig_info.get("lab_aprobado", False):
                continue

            # Obtener grupo específico para esta asignatura
            grupo = asig_info.get("grupo", "")
            if not grupo:
                continue

            # Clasificar según el patrón del grupo
            if PAT_SIMPLE.match(grupo):
                self.alumno_simple[alumno_id] = grupo
            elif PAT_DOBLE.match(grupo):
                self.alumno_doble[alumno_id] = grupo

        print(f"    ✓ Alumnos simples: {len(self.alumno_simple)}")
        print(f"    ✓ Alumnos dobles: {len(self.alumno_doble)}")

    def _asignar_alumnos_dobles(self, grupos: List[GrupoLab]) -> None:
        """
        5.2 - Asignar alumnos de doble grado a los grupos.

        Los alumnos dobles tienen prioridad y solo pueden ir a slots mixtos
        o slots específicos de su grupo doble.

        Args:
            grupos: Lista de grupos de la asignatura actual
        """
        print(f"  [5.2] Asignando alumnos dobles...")

        # Identificar grupos que aceptan dobles (slots mixtos o específicos dobles)
        grupos_para_dobles = []
        for grupo in grupos:
            if grupo.is_slot_mixto or grupo.grupo_doble:
                grupos_para_dobles.append(grupo)

        if not grupos_para_dobles:
            if self.alumno_doble:
                self.avisos.append(
                    f"{self.semestre_actual}:{self.asignatura_actual} - "
                    f"No hay grupos disponibles para {len(self.alumno_doble)} alumnos dobles"
                )
            return

        # Asignar cada alumno doble
        alumnos_asignados = 0
        for alumno_id, grupo_doble in self.alumno_doble.items():
            # Buscar grupo con capacidad compatible
            mejor_grupo = None
            min_carga = float('inf')

            for grupo in grupos_para_dobles:
                # Verificar capacidad
                if len(grupo.alumnos) >= grupo.capacidad:
                    continue

                # Verificar compatibilidad del slot
                if not self._slot_permite_alumno(grupo, alumno_id):
                    continue

                # Seleccionar el grupo con menos carga
                if len(grupo.alumnos) < min_carga:
                    min_carga = len(grupo.alumnos)
                    mejor_grupo = grupo

            if mejor_grupo:
                mejor_grupo.alumnos.append(alumno_id)
                alumnos_asignados += 1
            else:
                self.avisos.append(
                    f"{self.semestre_actual}:{self.asignatura_actual} - "
                    f"Alumno {alumno_id} (doble {grupo_doble}) sin grupo compatible disponible"
                )

        print(f"    ✓ {alumnos_asignados}/{len(self.alumno_doble)} alumnos dobles asignados")

    def _asignar_alumnos_simples(self, grupos: List[GrupoLab]) -> None:
        """
        5.3 - Asignar alumnos de grado simple a los grupos.

        Distribuye los alumnos simples entre sus grupos correspondientes,
        balanceando la carga de manera uniforme.

        Args:
            grupos: Lista de grupos de la asignatura actual
        """
        print(f"  [5.3] Asignando alumnos simples...")

        # Agrupar alumnos por código de grupo simple
        alumnos_por_codigo: Dict[str, List[str]] = {}
        for alumno_id, grupo_simple in self.alumno_simple.items():
            if grupo_simple not in alumnos_por_codigo:
                alumnos_por_codigo[grupo_simple] = []
            alumnos_por_codigo[grupo_simple].append(alumno_id)

        # Procesar cada código de grupo
        total_asignados = 0
        for grupo_simple, lista_alumnos in alumnos_por_codigo.items():
            # Encontrar grupos que corresponden a este código
            grupos_codigo = [g for g in grupos if g.grupo_simple == grupo_simple]

            if not grupos_codigo:
                self.avisos.append(
                    f"{self.semestre_actual}:{self.asignatura_actual} - "
                    f"No hay grupos para código {grupo_simple}"
                )
                continue

            # Distribuir alumnos con mínima carga
            asignados = self._distribuir_alumnos_min_carga(grupos_codigo, lista_alumnos)
            total_asignados += asignados

        print(f"    ✓ {total_asignados}/{len(self.alumno_simple)} alumnos simples asignados")

    def _distribuir_alumnos_min_carga(self, grupos: List[GrupoLab], alumnos: List[str]) -> int:
        """
        5.4 - Distribuir alumnos entre grupos minimizando desbalance de carga.

        Implementa un algoritmo greedy que asigna cada alumno al grupo
        con menor número de alumnos (que tenga capacidad disponible).

        Args:
            grupos: Lista de grupos entre los que distribuir
            alumnos: Lista de IDs de alumnos a distribuir

        Returns:
            Número de alumnos asignados exitosamente
        """
        asignados = 0

        for alumno_id in alumnos:
            # Buscar grupo con menor carga y capacidad disponible
            mejor_grupo = None
            min_carga = float('inf')

            for grupo in grupos:
                # Verificar capacidad
                if len(grupo.alumnos) >= grupo.capacidad:
                    continue

                # Verificar compatibilidad del slot
                if not self._slot_permite_alumno(grupo, alumno_id):
                    continue

                # Seleccionar el grupo con menos carga
                if len(grupo.alumnos) < min_carga:
                    min_carga = len(grupo.alumnos)
                    mejor_grupo = grupo

            if mejor_grupo:
                mejor_grupo.alumnos.append(alumno_id)
                asignados += 1

        return asignados

    def _balancear_paridad(self, grupos: List[GrupoLab]) -> None:
        """
        5.5 - Balancear grupos para lograr número par de alumnos.

        Los laboratorios requieren trabajo en parejas, por lo que intentamos
        que todos los grupos tengan un número par de alumnos.

        RESTRICCIÓN CRÍTICA: Solo se mueven alumnos entre grupos del MISMO código simple.
        Por ejemplo: E403-01 ↔ E403-02 (SÍ), pero E403-01 ↔ A404-01 (NO).

        Strategy:
            1. Agrupar por código simple (ej: todos los E403-XX juntos)
            2. Si suma total de alumnos del código es impar → SIEMPRE quedará 1 grupo impar
            3. Si hay 2+ grupos impares → intentar emparejarlos moviendo alumnos
            4. Objetivo: minimizar grupos impares (idealmente solo 1 por código)

        Args:
            grupos: Lista de grupos de la asignatura actual
        """
        print(f"  [5.5] Balanceando paridad de grupos...")

        # Agrupar por código simple
        grupos_por_codigo: Dict[str, List[GrupoLab]] = {}
        for grupo in grupos:
            codigo = grupo.grupo_simple
            if codigo not in grupos_por_codigo:
                grupos_por_codigo[codigo] = []
            grupos_por_codigo[codigo].append(grupo)

        # Procesar cada código
        cambios_totales = 0
        for codigo, grupos_codigo in grupos_por_codigo.items():
            # Solo grupos con alumnos
            grupos_con_alumnos = [g for g in grupos_codigo if g.alumnos]
            if not grupos_con_alumnos:
                continue

            # Calcular total de alumnos en este código
            total_alumnos = sum(len(g.alumnos) for g in grupos_con_alumnos)

            # Si el total es impar, SIEMPRE habrá 1 grupo impar (matemática básica)
            if total_alumnos % 2 == 1:
                print(f"    • {codigo}: {total_alumnos} alumnos (impar) → mínimo 1 grupo impar inevitable")

            cambios = self._balancear_codigo(grupos_con_alumnos, codigo)
            cambios_totales += cambios

        if cambios_totales > 0:
            print(f"    ✓ {cambios_totales} movimientos realizados para balancear paridad")
        else:
            print(f"    ✓ No se requirieron movimientos (balance óptimo alcanzado)")

    def _balancear_codigo(self, grupos: List[GrupoLab], codigo: str) -> int:
        """
        Balancear paridad para un código de grupo específico.

        LÓGICA:
            - Si solo hay 1 grupo impar → NO hacer nada (no se puede balancear)
            - Si hay 2+ grupos impares → intentar mover alumnos entre ellos

        Args:
            grupos: Lista de grupos del mismo código simple
            codigo: Código del grupo simple (ej: "E403")

        Returns:
            Número de movimientos realizados
        """
        cambios = 0
        max_iteraciones = 50  # Evitar bucles infinitos

        for iteracion in range(max_iteraciones):
            # Identificar grupos impares
            grupos_impares = [g for g in grupos if len(g.alumnos) % 2 == 1]

            # Si hay 0 grupos impares → Perfecto, terminamos
            if len(grupos_impares) == 0:
                break

            # Si hay 1 grupo impar → No se puede hacer nada (inevitable si total es impar)
            if len(grupos_impares) == 1:
                # Solo mostrar mensaje en la primera iteración
                if iteracion == 0 and cambios == 0:
                    print(f"    • {codigo}: 1 grupo impar (no requiere balance)")
                break

            # Si hay 2+ grupos impares → intentar emparejarlos
            cambio_realizado = False

            for i in range(len(grupos_impares)):
                if cambio_realizado:
                    break

                src = grupos_impares[i]

                for j in range(i + 1, len(grupos_impares)):
                    dst = grupos_impares[j]

                    # Verificar capacidad del destino
                    if len(dst.alumnos) >= dst.capacidad:
                        continue

                    # Buscar alumno movible de src a dst
                    alumno_movible = None
                    for alumno_id in src.alumnos:
                        if self._slot_permite_alumno(dst, alumno_id):
                            alumno_movible = alumno_id
                            break

                    if alumno_movible:
                        # Mover alumno
                        src.alumnos.remove(alumno_movible)
                        dst.alumnos.append(alumno_movible)
                        cambios += 1
                        cambio_realizado = True
                        break

            # Si no se pudo hacer ningún movimiento, terminamos
            if not cambio_realizado:
                grupos_impares_final = [g for g in grupos if len(g.alumnos) % 2 == 1]
                if len(grupos_impares_final) > 1:
                    print(f"    • {codigo}: {len(grupos_impares_final)} grupos impares "
                          f"(no se pudo reducir más por restricciones)")
                break

        return cambios

    def _verificar_capacidad(self, grupos: List[GrupoLab]) -> None:
        """
        5.6 - Verificar capacidad y generar avisos de alumnos sin asignar.

        Compara los alumnos matriculados con los alumnos asignados
        y genera avisos si hay alumnos sin asignar por falta de capacidad.

        Args:
            grupos: Lista de grupos de la asignatura actual
        """
        # Alumnos asignados en estos grupos
        alumnos_asignados = set()
        for grupo in grupos:
            alumnos_asignados.update(grupo.alumnos)

        # Alumnos matriculados (simples + dobles)
        alumnos_matriculados = set(self.alumno_simple.keys()) | set(self.alumno_doble.keys())

        # Alumnos sin asignar
        alumnos_sin_asignar = alumnos_matriculados - alumnos_asignados

        if alumnos_sin_asignar:
            num_sin_asignar = len(alumnos_sin_asignar)
            self.avisos.append(
                f"{self.semestre_actual}:{self.asignatura_actual} - "
                f"{num_sin_asignar} alumno(s) sin asignar por capacidad insuficiente"
            )

            self.conflictos_alumnos.append({
                "semestre": self.semestre_actual,
                "asignatura": self.asignatura_actual,
                "grupo": "—",
                "dia": "—",
                "franja": "—",
                "fecha": "—",
                "aula": "—",
                "profesor": "—",
                "detalle": f"{num_sin_asignar} alumno(s) sin asignar por capacidad insuficiente"
            })

    def _slot_permite_alumno(self, grupo: GrupoLab, alumno_id: str) -> bool:
        """
        Verificar si un slot/grupo permite a un alumno específico.

        Un slot permite a un alumno si:
            - El alumno es simple y el grupo acepta su código simple, O
            - El alumno es doble y el slot es mixto o específico de dobles

        Args:
            grupo: Grupo a verificar
            alumno_id: ID del alumno

        Returns:
            True si el slot permite al alumno, False en caso contrario
        """
        # Verificar si el alumno es simple
        if alumno_id in self.alumno_simple:
            grupo_simple_alumno = self.alumno_simple[alumno_id]
            return grupo.grupo_simple == grupo_simple_alumno

        # Verificar si el alumno es doble
        if alumno_id in self.alumno_doble:
            grupo_doble_alumno = self.alumno_doble[alumno_id]
            # El slot debe ser mixto o específico del grupo doble
            return grupo.is_slot_mixto or (grupo.grupo_doble == grupo_doble_alumno)

        # El alumno no está en ningún mapeo
        return False

    def _mostrar_resumen(self) -> None:
        """Mostrar resumen de la asignación de alumnos."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 5")
        print("-" * 70)

        total_alumnos = sum(len(g.alumnos) for g in self.grupos_creados)
        grupos_con_alumnos = sum(1 for g in self.grupos_creados if g.alumnos)

        print(f"  ✓ ASIGNACIÓN COMPLETADA")
        print(f"  • Total alumnos asignados: {total_alumnos}")
        print(f"  • Grupos con alumnos: {grupos_con_alumnos}/{len(self.grupos_creados)}")

        # Estadísticas por tipo
        grupos_pares = sum(1 for g in self.grupos_creados if len(g.alumnos) % 2 == 0 and g.alumnos)
        grupos_impares = sum(1 for g in self.grupos_creados if len(g.alumnos) % 2 == 1)

        print(f"  • Grupos pares: {grupos_pares}")
        print(f"  • Grupos impares: {grupos_impares}")

        # Capacidad promedio
        if grupos_con_alumnos > 0:
            promedio = total_alumnos / grupos_con_alumnos
            print(f"  • Promedio alumnos/grupo: {promedio:.1f}")

        # Distribución de carga
        cargas = [len(g.alumnos) for g in self.grupos_creados if g.alumnos]
        if cargas:
            print(f"  • Min-Max alumnos/grupo: {min(cargas)}-{max(cargas)}")

        if self.avisos:
            print(f"\n  ⚠ Avisos generados: {len(self.avisos)}")
            for aviso in self.avisos[:5]:  # Mostrar primeros 5 avisos
                print(f"    - {aviso}")
            if len(self.avisos) > 5:
                print(f"    ... y {len(self.avisos) - 5} avisos más")


# ========= FASE 6: ASIGNADOR DE PROFESORES =========
class AsignadorProfesores:
    """
    Clase responsable de la FASE 6: Asignación de Profesores a Grupos.

    Esta fase toma los grupos con alumnos asignados (Fase 5) y asigna
    profesores considerando disponibilidad, balance de carga y restricciones.

    Attributes:
        cfg: Configuración completa del sistema
        grupos_creados: Lista de grupos con alumnos asignados (Fase 5)
        avisos: Lista de advertencias generadas durante la asignación
        profesores_data: Datos de profesores desde configuración
        prof_carga_total: Carga total de grupos por profesor
        prof_carga_por_asig: Carga de grupos por profesor y asignatura
    """

    def __init__(self, cfg: Dict, grupos_creados: List['GrupoLab']):
        """
        Inicializar el asignador de profesores.

        Args:
            cfg: Configuración completa del sistema
            grupos_creados: Lista de grupos con alumnos (de Fase 5)
        """
        self.cfg = cfg
        self.grupos_creados = grupos_creados
        self.avisos: List[str] = []
        self.conflictos_profesores: List[Dict] = []

        # Datos de profesores
        self.profesores_data = (
            cfg.get("configuracion", {})
            .get("profesores", {})
            .get("datos", {})
        ) or {}

        # Índices de carga de trabajo
        self.prof_carga_total: Dict[str, int] = {}  # prof_id -> número total de grupos
        self.prof_carga_por_asig: Dict[Tuple[str, str], int] = {}  # (prof_id, asignatura) -> número grupos

    def ejecutar(self) -> tuple[bool, list[GrupoLab], list[str], list[dict]]:
        """
        Ejecutar la FASE 6 completa.

        Returns:
            Tupla con:
                - bool: True si la asignación fue exitosa
                - List[GrupoLab]: Lista de grupos con profesores asignados
                - List[str]: Lista de avisos generados
        """
        print("\n" + "=" * 70)
        print("FASE 6: ASIGNACIÓN DE PROFESORES")
        print("=" * 70)

        # 6.1 - Construir índices de profesores
        self._construir_indices()

        # 6.2 - Asignar profesores a todos los grupos
        self._asignar_profesores()

        # 6.3 - Ya se actualizó la carga durante la asignación

        # 6.4 - Mostrar resumen
        self._mostrar_resumen()

        return True, self.grupos_creados, self.avisos, self.conflictos_profesores

    def _construir_indices(self) -> None:
        """
        6.1 - Construir índices de profesores.

        Prepara las estructuras de datos necesarias para la asignación.
        """
        print("\n[6.1] Construyendo índices de profesores...")

        # Inicializar cargas en 0
        for prof_id in self.profesores_data.keys():
            self.prof_carga_total[prof_id] = 0
            for grupo in self.grupos_creados:
                self.prof_carga_por_asig[(prof_id, grupo.asignatura)] = 0

        print(f"    ✓ Profesores disponibles: {len(self.profesores_data)}")

    def _asignar_profesores(self) -> None:
        """
        6.2 - Asignar profesores a todos los grupos.

        Itera sobre todos los grupos y asigna el mejor profesor disponible
        usando heurísticas de mínima carga.
        """
        print("\n[6.2] Asignando profesores a grupos...")

        grupos_asignados = 0
        grupos_sin_profesor = 0

        for grupo in self.grupos_creados:
            # Buscar mejor profesor para este grupo
            profesor_id = self._pick_profesor_para_grupo(
                asignatura=grupo.asignatura,
                dia=grupo.dia,
                franja=grupo.franja
            )

            if profesor_id:
                # Asignar profesor al grupo
                grupo.profesor_id = profesor_id
                grupo.profesor = self._get_nombre_profesor(profesor_id)
                grupos_asignados += 1

                # Actualizar cargas
                self._actualizar_carga(profesor_id, grupo.asignatura)
            else:
                # No hay profesor disponible
                grupo.profesor_id = None
                grupo.profesor = "—"
                grupos_sin_profesor += 1

                # Generar aviso
                self.avisos.append(
                    f"{grupo.semestre}:{grupo.asignatura} - "
                    f"Grupo {grupo.label} sin profesor disponible para {grupo.dia} {grupo.franja}"
                )

                self.conflictos_profesores.append({
                    "semestre": grupo.semestre,
                    "asignatura": grupo.asignatura,
                    "grupo": grupo.label,
                    "dia": grupo.dia,
                    "franja": grupo.franja,
                    "fecha": "",
                    "aula": grupo.aula or "—",
                    "profesor": "SIN ASIGNAR",
                    "detalle": f"No hay profesores disponibles para {grupo.dia} {grupo.franja}"
                })

        print(f"    ✓ Grupos con profesor: {grupos_asignados}/{len(self.grupos_creados)}")
        if grupos_sin_profesor > 0:
            print(f"    ⚠ Grupos sin profesor: {grupos_sin_profesor}")

    def _pick_profesor_para_grupo(
        self,
        asignatura: str,
        dia: str,
        franja: str
    ) -> Optional[str]:
        """
        Seleccionar mejor profesor disponible para un grupo.

        Implementa heurística de mínima carga:
            1. Filtrar profesores elegibles (imparte asignatura, trabaja día, sin bloqueo)
            2. Ordenar por: carga total, carga en asignatura, nombre
            3. Seleccionar el menos cargado

        Args:
            asignatura: Código de la asignatura
            dia: Día de la semana
            franja: Franja horaria (formato HH:MM-HH:MM)

        Returns:
            ID del profesor seleccionado, o None si no hay ninguno disponible
        """
        # Normalizar franja
        franja_norm = self._normalize_time_range(franja)

        # Lista de candidatos: (carga_total, carga_asignatura, nombre, prof_id)
        candidatos = []

        # FASE 1: Filtrar profesores elegibles
        for prof_id, prof_data in self.profesores_data.items():
            # ¿Imparte la asignatura?
            if not self._prof_imparte_asignatura(prof_id, asignatura):
                continue

            # ¿Trabaja ese día?
            if not self._prof_trabaja_dia(prof_id, dia):
                continue

            # ¿Tiene bloqueada la franja?
            if self._prof_bloqueado_slot(prof_id, dia, franja_norm):
                continue

            # Es elegible → agregar a candidatos
            nombre = self._get_nombre_profesor(prof_id)
            carga_total = self.prof_carga_total.get(prof_id, 0)
            carga_asig = self.prof_carga_por_asig.get((prof_id, asignatura), 0)

            candidatos.append((carga_total, carga_asig, nombre, prof_id))

        # Si no hay candidatos, retornar None
        if not candidatos:
            return None

        # FASE 2: Seleccionar el menos cargado
        candidatos.sort()  # Ordena por: (carga_total, carga_asig, nombre, prof_id)
        profesor_id = candidatos[0][3]

        return profesor_id

    def _actualizar_carga(self, profesor_id: str, asignatura: str) -> None:
        """
        6.3 - Actualizar carga de trabajo de un profesor.

        Args:
            profesor_id: ID del profesor
            asignatura: Código de la asignatura
        """
        # Incrementar carga total
        self.prof_carga_total[profesor_id] = self.prof_carga_total.get(profesor_id, 0) + 1

        # Incrementar carga por asignatura
        key = (profesor_id, asignatura)
        self.prof_carga_por_asig[key] = self.prof_carga_por_asig.get(key, 0) + 1

    # ========= MÉTODOS DE VALIDACIÓN =========

    def _prof_imparte_asignatura(self, prof_id: str, asignatura: str) -> bool:
        """
        Verificar si un profesor imparte una asignatura.

        Args:
            prof_id: ID del profesor
            asignatura: Código de la asignatura

        Returns:
            True si el profesor imparte la asignatura
        """
        prof_data = self.profesores_data.get(prof_id, {})
        asignaturas = prof_data.get("asignaturas_imparte", []) or []
        return asignatura in asignaturas

    def _prof_trabaja_dia(self, prof_id: str, dia: str) -> bool:
        """
        Verificar si un profesor trabaja en un día específico.

        Args:
            prof_id: ID del profesor
            dia: Día de la semana

        Returns:
            True si el profesor trabaja ese día
        """
        prof_data = self.profesores_data.get(prof_id, {})
        dias_trabajo = prof_data.get("dias_trabajo", []) or []
        return dia in dias_trabajo

    def _prof_bloqueado_slot(self, prof_id: str, dia: str, franja_norm: str) -> bool:
        """
        Verificar si un profesor tiene bloqueado un slot (día + franja).

        Args:
            prof_id: ID del profesor
            dia: Día de la semana
            franja_norm: Franja normalizada (HH:MM-HH:MM)

        Returns:
            True si el profesor tiene el slot bloqueado
        """
        prof_data = self.profesores_data.get(prof_id, {})
        bloques = prof_data.get("horarios_bloqueados", {}) or {}

        # Obtener franjas bloqueadas para ese día
        franjas_dia = bloques.get(dia)

        if isinstance(franjas_dia, list):
            # Lista de franjas
            franjas_norm = [self._normalize_time_range(f) for f in franjas_dia]
        elif isinstance(franjas_dia, dict):
            # Diccionario de franjas
            franjas_norm = [self._normalize_time_range(f) for f in franjas_dia.keys()]
        else:
            franjas_norm = []

        return franja_norm in franjas_norm

    # ========= MÉTODOS AUXILIARES =========

    def _get_nombre_profesor(self, prof_id: str) -> str:
        """
        Obtener nombre completo formateado de un profesor.

        Args:
            prof_id: ID del profesor

        Returns:
            Nombre completo del profesor
        """
        prof_data = self.profesores_data.get(prof_id, {})
        nombre = (prof_data.get("nombre") or "").strip()
        apellidos = (prof_data.get("apellidos") or "").strip()

        nombre_completo = f"{nombre} {apellidos}".strip()
        return nombre_completo if nombre_completo else "—"

    def _normalize_time_range(self, rng: str) -> str:
        """
        Normalizar rango horario al formato HH:MM-HH:MM.

        Args:
            rng: Rango horario en formato flexible

        Returns:
            Rango normalizado (ej: "09:30-11:30")
        """
        s = (rng or "").strip()
        m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$", s)
        if not m:
            return s
        h1, m1, h2, m2 = map(int, m.groups())
        return f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"

    def _mostrar_resumen(self) -> None:
        """6.4 - Mostrar resumen de la asignación de profesores."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 6")
        print("-" * 70)

        grupos_con_profesor = sum(1 for g in self.grupos_creados if g.profesor_id)
        grupos_sin_profesor = len(self.grupos_creados) - grupos_con_profesor

        print(f"  ✓ ASIGNACIÓN DE PROFESORES COMPLETADA")
        print(f"  • Grupos con profesor: {grupos_con_profesor}/{len(self.grupos_creados)}")

        if grupos_sin_profesor > 0:
            print(f"  ⚠ Grupos sin profesor: {grupos_sin_profesor}")

        # Estadísticas de carga por profesor
        if self.prof_carga_total:
            cargas = list(self.prof_carga_total.values())
            cargas_filtradas = [c for c in cargas if c > 0]

            if cargas_filtradas:
                print(f"\n  DISTRIBUCIÓN DE CARGA:")
                print(f"  • Profesores activos: {len(cargas_filtradas)}/{len(self.profesores_data)}")
                print(f"  • Carga mínima: {min(cargas_filtradas)} grupos")
                print(f"  • Carga máxima: {max(cargas_filtradas)} grupos")
                print(f"  • Carga promedio: {sum(cargas_filtradas)/len(cargas_filtradas):.1f} grupos")

                # Top 5 profesores más cargados
                top_profes = sorted(
                    [(carga, prof_id) for prof_id, carga in self.prof_carga_total.items() if carga > 0],
                    reverse=True
                )[:5]

                if top_profes:
                    print(f"\n  TOP PROFESORES MÁS CARGADOS:")
                    for i, (carga, prof_id) in enumerate(top_profes, 1):
                        nombre = self._get_nombre_profesor(prof_id)
                        print(f"    {i}. {nombre}: {carga} grupos")

        if self.avisos:
            print(f"\n  ⚠ Avisos generados: {len(self.avisos)}")
            for aviso in self.avisos[:5]:  # Mostrar primeros 5 avisos
                print(f"    - {aviso}")
            if len(self.avisos) > 5:
                print(f"    ... y {len(self.avisos) - 5} avisos más")


# ========= FASE 7: PROGRAMADOR Y VALIDADOR DE FECHAS =========
class ProgramadorFechas:
    """
    Clase responsable de la FASE 7: Asignación y Validación de Fechas.

    Esta fase toma los grupos con alumnos y profesores asignados (Fases 5 y 6)
    y les asigna las fechas pre-calculadas en la Fase 2, validando que no haya
    conflictos de disponibilidad de profesores o aulas. Si detecta conflictos,
    busca fechas alternativas o cambia de aula si es necesario.

    El proceso sigue estos pasos:
        1. Asigna fechas iniciales según el mapeo de Fase 2 (letra del grupo)
        2. Valida disponibilidad de profesor y aula en cada fecha
        3. Busca fechas alternativas si hay conflictos
        4. Intenta aulas alternativas si no hay fechas disponibles
        5. Ordena las fechas cronológicamente

    Attributes:
        cfg: Configuración completa del sistema
        grupos_creados: Lista de grupos con alumnos y profesores (Fases 5 y 6)
        mapeo_fechas: Mapeo de fechas calculado en Fase 2
        conflictos_profesores: Lista de conflictos de profesores detectados
        conflictos_aulas: Lista de conflictos de aulas detectados
        prof_ocupado_fecha: Índice de ocupación de profesores por fecha
        aula_ocupada_fecha: Índice de ocupación de aulas por fecha
        profesores_data: Datos de profesores desde configuración
        aulas_data: Datos de aulas desde configuración
    """

    def __init__(
            self,
            cfg: Dict,
            grupos_creados: List['GrupoLab'],
            mapeo_fechas: Dict[Tuple[str, str, str, str, str], List[str]]
    ):
        """
        Inicializar el programador de fechas.

        Args:
            cfg: Configuración completa del sistema
            grupos_creados: Lista de grupos con alumnos y profesores
            mapeo_fechas: Mapeo de fechas de Fase 2 (semestre, asig, grupo, dia, letra) -> [fechas]
        """
        self.cfg = cfg
        self.grupos_creados = grupos_creados
        self.mapeo_fechas = mapeo_fechas

        # Listas de conflictos
        self.conflictos_profesores: List[Dict[str, Any]] = []
        self.conflictos_aulas: List[Dict[str, Any]] = []

        # Índices de ocupación por fecha (fecha_iso + franja)
        self.prof_ocupado_fecha: Dict[Tuple[str, str, str], bool] = {}  # (prof_id, fecha_iso, franja)
        self.aula_ocupada_fecha: Dict[Tuple[str, str, str], bool] = {}  # (aula, fecha_iso, franja)

        # Datos auxiliares
        self.profesores_data = (
                                   cfg.get("configuracion", {})
                                   .get("profesores", {})
                                   .get("datos", {})
                               ) or {}

        self.aulas_data = (
                              cfg.get("configuracion", {})
                              .get("aulas", {})
                              .get("datos", {})
                          ) or {}

    def ejecutar(self) -> Tuple[bool, List['GrupoLab'], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Ejecutar la FASE 7 completa.

        Returns:
            Tupla con:
                - bool: True si la programación fue exitosa
                - List[GrupoLab]: Lista de grupos con fechas asignadas
                - List[Dict]: Lista de conflictos de profesores
                - List[Dict]: Lista de conflictos de aulas
        """
        print("\n" + "=" * 70)
        print("FASE 7: ASIGNACIÓN Y VALIDACIÓN DE FECHAS")
        print("=" * 70)

        # 7.1 - Asignar fechas según mapeo de Fase 2
        self._asignar_fechas_iniciales()

        # 7.2 - Validar y resolver conflictos
        self._validar_y_resolver_conflictos()

        # 7.3 - Ordenar fechas cronológicamente
        self._ordenar_fechas()

        # 7.4 - Mostrar resumen
        self._mostrar_resumen()

        return True, self.grupos_creados, self.conflictos_profesores, self.conflictos_aulas

    def _asignar_fechas_iniciales(self) -> None:
        """
        7.1 - Asignar fechas iniciales según mapeo de Fase 2.

        Para cada grupo, busca en el mapeo la clave (semestre, asignatura,
        grupo_simple, dia, letra) y asigna las fechas correspondientes.
        """
        print("\n[7.1] Asignando fechas pre-calculadas (Fase 2) a grupos...")

        grupos_con_fechas = 0
        grupos_sin_fechas = 0

        for grupo in self.grupos_creados:
            # Construir clave para buscar en mapeo
            clave = (
                grupo.semestre,
                grupo.asignatura,
                grupo.grupo_simple,
                grupo.dia,
                grupo.letra
            )

            # Buscar fechas en el mapeo
            fechas = self.mapeo_fechas.get(clave, [])

            if fechas:
                # Asignar fechas al grupo
                grupo.fechas = list(fechas)
                grupos_con_fechas += 1
            else:
                # No hay fechas en el mapeo
                grupo.fechas = []
                grupos_sin_fechas += 1

                self.conflictos_profesores.append({
                    "semestre": grupo.semestre,
                    "asignatura": grupo.asignatura,
                    "grupo": grupo.label,
                    "dia": grupo.dia,
                    "franja": grupo.franja,
                    "fecha": "",
                    "aula": grupo.aula or "—",
                    "profesor": grupo.profesor or "—",
                    "detalle": f"Sin fechas calculadas en Fase 2 para letra {grupo.letra}"
                })

        print(f"    ✓ Grupos con fechas asignadas: {grupos_con_fechas}/{len(self.grupos_creados)}")
        if grupos_sin_fechas > 0:
            print(f"    ⚠ Grupos sin fechas: {grupos_sin_fechas}")

    def _validar_y_resolver_conflictos(self) -> None:
        """
        7.2 - Validar cada fecha asignada y resolver conflictos.

        Para cada fecha de cada grupo verifica disponibilidad de profesor y aula.
        Si hay conflicto, busca fecha alternativa o cambia de aula.
        """
        print("\n[7.2] Validando conflictos y buscando alternativas...")

        total_conflictos = 0
        conflictos_resueltos = 0
        conflictos_sin_solucion = 0
        cambios_realizados = []

        for grupo in self.grupos_creados:
            if not grupo.fechas:
                continue

            # Validar cada fecha del grupo
            fechas_validadas = []
            conflictos_grupo = 0

            for fecha_dd in grupo.fechas:
                fecha_iso = self._ddmmyyyy_to_iso(fecha_dd)

                # Verificar si esta fecha ya está ocupada o bloqueada
                if self._fecha_valida_para_grupo(grupo, fecha_dd, fecha_iso):
                    # Fecha válida, marcar como ocupada
                    fechas_validadas.append(fecha_dd)
                    self._ocupar_fecha(grupo, fecha_iso, fecha_dd)
                else:
                    total_conflictos += 1
                    conflictos_grupo += 1

                    # Conflicto, buscar alternativa
                    fecha_alternativa = self._buscar_fecha_alternativa(grupo, fecha_dd, fecha_iso)

                    if fecha_alternativa:
                        conflictos_resueltos += 1
                        fechas_validadas.append(fecha_alternativa)
                        cambios_realizados.append(f"{grupo.label}: {fecha_dd} → {fecha_alternativa} ({grupo.aula}) - {grupo.asignatura} - {grupo.franja} - {grupo.profesor} - {grupo.fechas}")
                    else:
                        conflictos_sin_solucion += 1
                        # No se encontró alternativa
                        self.conflictos_profesores.append({
                            "semestre": grupo.semestre,
                            "asignatura": grupo.asignatura,
                            "grupo": grupo.label,
                            "dia": grupo.dia,
                            "franja": grupo.franja,
                            "fecha": fecha_dd,
                            "aula": grupo.aula or "—",
                            "profesor": grupo.profesor or "—",
                            "detalle": f"Conflicto sin resolver (profesor o aula no disponible en {fecha_dd})"
                        })

            # Actualizar fechas del grupo con las validadas
            grupo.fechas = fechas_validadas

        # === LOG RESUMEN ===
        print(f"    ✓ Total conflictos detectados: {total_conflictos}")
        print(f"    ✓ Resueltos automáticamente: {conflictos_resueltos}")
        print(f"    ⚠ Sin solución: {conflictos_sin_solucion}")
        if cambios_realizados:
            print("    🔄 Ejemplos de cambios:")
            for cambio in cambios_realizados[:300]:
                print(f"       - {cambio}")

    def _fecha_valida_para_grupo(self, grupo: 'GrupoLab', fecha_dd: str, fecha_iso: str) -> bool:
        """
        Verificar si una fecha es válida para un grupo.

        Args:
            grupo: Grupo a verificar
            fecha_dd: Fecha en formato dd/mm/yyyy
            fecha_iso: Fecha en formato yyyy-mm-dd

        Returns:
            True si la fecha es válida (profesor y aula disponibles)
        """

        # Verificar profesor
        if grupo.profesor_id:
            if self._prof_fecha_no_disponible(grupo.profesor_id, fecha_dd):
                return False
            if self._prof_ocupado_en_fecha(grupo.profesor_id, fecha_iso, grupo.franja):
                return False

        # Verificar aula
        if grupo.aula and grupo.aula != "—":
            if not self._aula_disponible_en_fecha(grupo.aula, fecha_dd, fecha_iso, grupo.franja):
                return False

        # Verificar si ya hay otro grupo de laboratorio en esta franja
        if self._franja_ocupada_por_otro_grupo(grupo, fecha_iso):
            return False

        return True

    def _buscar_fecha_alternativa(
            self,
            grupo: 'GrupoLab',
            fecha_original_dd: str,
            fecha_original_iso: str
    ) -> Optional[str]:
        """
        Buscar una fecha alternativa cuando hay conflicto.

        Estrategia:
            1. Obtener pool completo de fechas para ese día
            2. Buscar primero fechas posteriores a la original
            3. Si no hay, probar anteriores (más cercanas primero)
            4. Intentar con aula alternativa si es necesario

        Args:
            grupo: Grupo con conflicto
            fecha_original_dd: Fecha original con conflicto
            fecha_original_iso: Fecha original en ISO

        Returns:
            Fecha alternativa (dd/mm/yyyy) o None
        """
        # Obtener pool de fechas para ese día
        pool = self._obtener_pool_fechas(grupo.semestre, grupo.dia)

        if not pool:
            return None

        # Índice de la fecha original dentro del pool
        try:
            idx = pool.index(fecha_original_dd)
        except ValueError:
            idx = -1

        # Ordenar prioridades: primero posteriores, luego anteriores
        fechas_reordenadas = []
        if idx != -1:
            posteriores = pool[idx + 1:]
            anteriores = pool[:idx][::-1]  # invertido para ir hacia atrás
            fechas_reordenadas = posteriores + anteriores
        else:
            fechas_reordenadas = pool  # si no se encuentra, mantener orden normal

        # Buscar fecha alternativa cercana
        for fecha_dd in fechas_reordenadas:
            # Saltar la fecha original
            #if fecha_dd == fecha_original_dd:
            #    continue

            fecha_iso = self._ddmmyyyy_to_iso(fecha_dd)

            # Verificar si es válida con aula actual
            if self._fecha_valida_para_grupo(grupo, fecha_dd, fecha_iso):
                self._ocupar_fecha(grupo, fecha_iso, fecha_dd)
                return fecha_dd

            # Si no funciona con aula actual, intentar alternativas
            aulas_alt = self._obtener_aulas_asignatura(grupo.asignatura)

            for aula_alt in aulas_alt:
                if aula_alt == grupo.aula:
                    continue

                if self._aula_disponible_en_fecha(aula_alt, fecha_dd, fecha_iso, grupo.franja):
                    # Cambiar aula y asignar fecha
                    grupo.aula = aula_alt
                    grupo.capacidad = self._get_capacidad_aula(aula_alt)
                    self._ocupar_fecha(grupo, fecha_iso, fecha_dd)
                    return fecha_dd

        return None

    def _ocupar_fecha(self, grupo: 'GrupoLab', fecha_iso: str, fecha_dd: str) -> None:
        """
        Marcar fecha como ocupada para profesor y aula.

        Args:
            grupo: Grupo al que se asigna la fecha
            fecha_iso: Fecha en formato ISO (yyyy-mm-dd)
            fecha_dd: Fecha en formato dd/mm/yyyy (no usado, mantiene firma)
        """
        # Marcar profesor como ocupado
        if grupo.profesor_id:
            self.prof_ocupado_fecha[(grupo.profesor_id, fecha_iso, grupo.franja)] = True

        # Marcar aula como ocupada
        if grupo.aula and grupo.aula != "—":
            self.aula_ocupada_fecha[(grupo.aula, fecha_iso, grupo.franja)] = True

    def _ordenar_fechas(self) -> None:
        """
        7.3 - Ordenar fechas cronológicamente para cada grupo.
        """
        print("\n[7.3] Ordenando fechas cronológicamente...")

        for grupo in self.grupos_creados:
            if grupo.fechas:
                grupo.fechas = self._sort_ddmmyyyy_asc(grupo.fechas)

        print(f"    ✓ Fechas ordenadas para {len(self.grupos_creados)} grupos")

    # ========= MÉTODOS DE VALIDACIÓN =========

    def _prof_fecha_no_disponible(self, prof_id: str, fecha_dd: str) -> bool:
        """
        Verificar si profesor tiene fecha bloqueada.

        Args:
            prof_id: ID del profesor
            fecha_dd: Fecha en formato dd/mm/yyyy

        Returns:
            True si el profesor tiene bloqueada la fecha
        """
        prof_data = self.profesores_data.get(prof_id, {})
        fechas_no_disp = [f.strip() for f in (prof_data.get("fechas_no_disponibles") or [])]
        return fecha_dd in fechas_no_disp

    def _prof_ocupado_en_fecha(self, prof_id: str, fecha_iso: str, franja: str) -> bool:
        """
        Verificar si profesor está ocupado en fecha y franja.

        Args:
            prof_id: ID del profesor
            fecha_iso: Fecha en formato yyyy-mm-dd
            franja: Franja horaria

        Returns:
            True si el profesor está ocupado
        """
        return self.prof_ocupado_fecha.get((prof_id, fecha_iso, franja), False)

    def _aula_disponible_en_fecha(self, aula: str, fecha_dd: str, fecha_iso: str, franja: str) -> bool:
        """
        Verificar si aula está disponible en fecha y franja.

        Args:
            aula: Código del aula
            fecha_dd: Fecha en formato dd/mm/yyyy
            fecha_iso: Fecha en formato yyyy-mm-dd
            franja: Franja horaria

        Returns:
            True si el aula está disponible
        """
        aula_data = self.aulas_data.get(aula, {})
        fechas_no_disp = [f.strip() for f in (aula_data.get("fechas_no_disponibles") or [])]
        if fecha_dd in fechas_no_disp:
            return False

        return not self.aula_ocupada_fecha.get((aula, fecha_iso, franja), False)

    def _franja_ocupada_por_otro_grupo(self, grupo: 'GrupoLab', fecha_iso: str) -> bool:
        """
        Verificar si ya hay otro grupo de laboratorio ocupando esta franja en la fecha.

        Args:
            grupo: Grupo que queremos asignar
            fecha_iso: Fecha en formato yyyy-mm-dd

        Returns:
            True si la franja ya está ocupada por otro grupo
        """
        # Recorrer todos los grupos ya creados
        for otro_grupo in self.grupos_creados:
            # Saltar el mismo grupo
            if otro_grupo.label == grupo.label:
                continue

            # Verificar si el otro grupo tiene esta fecha asignada
            fecha_dd = self._iso_to_ddmmyyyy(fecha_iso)
            if fecha_dd in otro_grupo.fechas:
                # Verificar si coinciden en franja horaria
                if otro_grupo.franja == grupo.franja:
                    # Solo es conflicto si comparten aula o profesor
                    if otro_grupo.aula == grupo.aula:
                        return True  # Mismo aula - conflicto
                    if otro_grupo.profesor_id == grupo.profesor_id:
                        return True  # Mismo profesor - conflicto
                    # Si no, NO hay conflicto

        return False

    # ========= MÉTODOS AUXILIARES =========

    def _obtener_pool_fechas(self, semestre: str, dia: str) -> List[str]:
        """
        Obtener pool de fechas disponibles para un día del semestre.

        Args:
            semestre: Código del semestre (ej: "semestre_1")
            dia: Día de la semana

        Returns:
            Lista de fechas en formato dd/mm/yyyy
        """
        cal = self.cfg.get("configuracion", {}).get("calendario", {}).get("datos", {}) or {}

        sem_norm=normalizar_semestre(semestre)

        key = sem_norm if sem_norm.startswith("semestre_") else f"semestre_{sem_norm}"
        semestre_datos = cal.get(key, {})

        dia_normalizado = dia.strip().capitalize()
        reemplazos = {"Miercoles": "Miércoles", "Sabado": "Sábado"}
        dia_normalizado = reemplazos.get(dia_normalizado, dia_normalizado)

        dias_filtrados = [d for d in semestre_datos.values()
                          if isinstance(d, dict) and d.get("horario_asignado") == dia_normalizado]

        dias_filtrados.sort(key=lambda d: d.get("fecha", ""))

        fechas = []
        for d in dias_filtrados:
            fecha = d.get("fecha", "")
            if re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
                fechas.append(self._iso_to_ddmmyyyy(fecha))

        return fechas

    def _obtener_aulas_asignatura(self, asignatura: str) -> List[str]:
        """
        Obtener lista de aulas disponibles para una asignatura.

        Args:
            asignatura: Código de la asignatura

        Returns:
            Lista de códigos de aulas
        """
        aulas = []

        for nombre, aula_data in self.aulas_data.items():
            if not aula_data.get("disponible", False):
                continue

            asigs = aula_data.get("asignaturas_asociadas", []) or []
            if asignatura in asigs:
                aulas.append(nombre)

        return aulas

    def _get_capacidad_aula(self, aula: str) -> int:
        """
        Obtener capacidad de un aula.

        Args:
            aula: Código del aula

        Returns:
            Capacidad del aula
        """
        try:
            return int(self.aulas_data.get(aula, {}).get("capacidad", 10000))
        except:
            return 10000

    def _ddmmyyyy_to_iso(self, fecha: str) -> str:
        """
        Convertir fecha de formato dd/mm/yyyy a yyyy-mm-dd.

        Args:
            fecha: Fecha en formato dd/mm/yyyy

        Returns:
            Fecha en formato yyyy-mm-dd
        """
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", fecha.strip())
        if not m:
            return fecha
        d, mo, y = m.groups()
        return f"{y}-{mo}-{d}"

    def _iso_to_ddmmyyyy(self, fecha: str) -> str:
        """
        Convertir fecha de formato yyyy-mm-dd a dd/mm/yyyy.

        Args:
            fecha: Fecha en formato yyyy-mm-dd

        Returns:
            Fecha en formato dd/mm/yyyy
        """
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", fecha.strip())
        if not m:
            return fecha
        y, mo, d = m.groups()
        return f"{d}/{mo}/{y}"

    def _sort_ddmmyyyy_asc(self, fechas: List[str]) -> List[str]:
        """
        Ordenar fechas de más cercana a más tardía.

        Args:
            fechas: Lista de fechas en formato dd/mm/yyyy

        Returns:
            Lista ordenada de fechas
        """

        def key_fun(s: str):
            m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s.strip())
            if not m:
                return (9999, 99, 99)
            d, mo, y = map(int, m.groups())
            return (y, mo, d)

        return sorted(fechas, key=key_fun)

    def _mostrar_resumen(self) -> None:
        """7.4 - Mostrar resumen de la programación de fechas."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 7")
        print("-" * 70)

        grupos_con_fechas = sum(1 for g in self.grupos_creados if g.fechas)
        total_fechas = sum(len(g.fechas) for g in self.grupos_creados)

        print(f"  ✓ ASIGNACIÓN Y VALIDACIÓN COMPLETADA")
        print(f"  • Grupos con fechas: {grupos_con_fechas}/{len(self.grupos_creados)}")
        print(f"  • Total sesiones programadas: {total_fechas}")

        if grupos_con_fechas > 0:
            fechas_por_grupo = [len(g.fechas) for g in self.grupos_creados if g.fechas]
            print(f"  • Sesiones por grupo (min-max): {min(fechas_por_grupo)}-{max(fechas_por_grupo)}")

        # Conflictos
        if self.conflictos_profesores:
            print(f"\n  ⚠ Conflictos detectados: {len(self.conflictos_profesores)}")
            for conf in self.conflictos_profesores[:3]:
                print(f"    - {conf['grupo']}: {conf['detalle']}")
            if len(self.conflictos_profesores) > 3:
                print(f"    ... y {len(self.conflictos_profesores) - 3} conflictos más")

        if self.conflictos_aulas:
            print(f"\n  ⚠ Conflictos aulas: {len(self.conflictos_aulas)}")


# ========= FASE 8: GENERADOR DE OUTPUT =========
class GeneradorOutputs:
    """
    Clase responsable de la FASE 8: Generación de Outputs.

    Toma los grupos programados y los convierte al formato JSON que espera
    el sistema actual, haciéndolo compatible con ver_resultados.py

    Attributes:
        cfg: Configuración completa del sistema
        grupos: Lista de grupos programados (GrupoLab)
        conflictos_profesores: Lista de conflictos de profesores detectados
        conflictos_aulas: Lista de conflictos de aulas detectados
        avisos: Lista de avisos generados durante el proceso
    """

    def __init__(
        self,
        cfg: Dict,
        grupos: List,
        conflictos_profesores: List[Dict] = None,
        conflictos_aulas: List[Dict] = None,
        conflictos_alumnos: List[Dict] = None,
        avisos: List[str] = None
    ):
        """
        Inicializar el generador de outputs.

        Args:
            cfg: Configuración completa del sistema
            grupos: Lista de objetos GrupoLab programados
            conflictos_profesores: Conflictos de profesores (opcional)
            conflictos_aulas: Conflictos de aulas (opcional)
            avisos: Lista de avisos (opcional)
        """
        self.cfg = cfg
        self.grupos = grupos
        self.conflictos_profesores = conflictos_profesores or []
        self.conflictos_aulas = conflictos_aulas or []
        self.conflictos_alumnos = conflictos_alumnos or []
        self.avisos = avisos or []

    def ejecutar(self, output_path: Path) -> Tuple[bool, Dict]:
        """
        Ejecutar la FASE 8 completa.

        Args:
            output_path: Ruta donde guardar el JSON actualizado

        Returns:
            Tupla con:
                - bool: True si se guardó correctamente
                - Dict: Configuración actualizada
        """
        print("\n" + "=" * 70)
        print("FASE 8: OUTPUTS - GENERACIÓN DE RESULTADOS")
        print("=" * 70)

        # 9.1 - Convertir grupos a formato JSON
        grupos_json = self._convertir_grupos_a_json()

        # 9.2 - Estructurar resultados_organizacion
        resultados = self._estructurar_resultados(grupos_json)

        # 9.3 - Actualizar configuración
        self._actualizar_configuracion(resultados)

        # 9.4 - Guardar archivo
        exito = self._guardar_json(output_path)

        # 9.5 - Mostrar resumen
        self._mostrar_resumen(output_path, exito)

        return exito, self.cfg

    def _convertir_grupos_a_json(self) -> List[Dict]:
        """
        9.1 - Convertir lista de GrupoLab a diccionarios JSON.

        Returns:
            Lista de grupos en formato diccionario
        """
        print("\n[9.1] Convirtiendo grupos a formato JSON...")

        grupos_json = []
        for grupo in self.grupos:
            grupo_dict = {
                'semestre': grupo.semestre,
                'asignatura': grupo.asignatura,
                'label': grupo.label,
                'profesor': grupo.profesor or "",
                'profesor_id': grupo.profesor_id or "",
                'aula': grupo.aula,
                'dia': grupo.dia,
                'franja': grupo.franja,
                'letra': grupo.letra,
                'fechas': grupo.fechas or [],
                'alumnos': list(grupo.alumnos) if grupo.alumnos else [],
                'capacidad': grupo.capacidad,
                'mixta': bool(grupo.is_slot_mixto),
                'grupo_simple': grupo.grupo_simple,
                'grupo_doble': grupo.grupo_doble or ""
            }
            grupos_json.append(grupo_dict)

        print(f"  ✓ Convertidos {len(grupos_json)} grupos a formato JSON")
        return grupos_json

    def _estructurar_resultados(self, grupos_json: List[Dict]) -> Dict:
        """
        9.2 - Estructurar resultados_organizacion según formato esperado.

        El formato es:
        {
            "datos_disponibles": true,
            "fecha_actualizacion": "ISO_TIMESTAMP",
            "conflictos": {...},
            "avisos": [...],
            "semestre_1": {
                "ASIGNATURA": {
                    "grupos": {
                        "LABEL": {...}
                    }
                }
            },
            "_metadata": {...}
        }

        Args:
            grupos_json: Lista de grupos en formato diccionario

        Returns:
            Diccionario con la estructura completa de resultados
        """
        print("\n[9.2] Estructurando resultados_organizacion...")

        resultados: Dict[str, Any] = {}

        # Metadatos básicos
        resultados["datos_disponibles"] = True
        resultados["fecha_actualizacion"] = datetime.now().isoformat()

        # Conflictos
        resultados["conflictos"] = {
            "profesores": self.conflictos_profesores,
            "aulas": self.conflictos_aulas,
            "alumnos": self.conflictos_alumnos
        }

        # Avisos
        resultados["avisos"] = self.avisos

        # Agrupar por semestre -> asignatura -> grupos
        for grupo_dict in grupos_json:
            # Normalizar clave de semestre
            sem_key = "semestre_" + normalizar_semestre(grupo_dict['semestre'])
            asignatura = grupo_dict['asignatura']
            label = grupo_dict['label']

            # Crear estructura si no existe
            if sem_key not in resultados:
                resultados[sem_key] = {}

            if asignatura not in resultados[sem_key]:
                resultados[sem_key][asignatura] = {"grupos": {}}

            # Agregar grupo (sin semestre, asignatura y label ya que están en la estructura)
            grupo_data = {
                'profesor': grupo_dict['profesor'],
                'profesor_id': grupo_dict['profesor_id'],
                'aula': grupo_dict['aula'],
                'dia': grupo_dict['dia'],
                'franja': grupo_dict['franja'],
                'fechas': grupo_dict['fechas'],
                'alumnos': grupo_dict['alumnos'],
                'capacidad': grupo_dict['capacidad'],
                'mixta': grupo_dict['mixta'],
                'grupo_simple': grupo_dict['grupo_simple'],
                'grupo_doble': grupo_dict['grupo_doble'],
                'letra': grupo_dict['letra']
            }

            resultados[sem_key][asignatura]["grupos"][label] = grupo_data

        # Metadata final
        resultados["_metadata"] = {
            "ultima_ejecucion": datetime.now().isoformat(timespec="seconds"),
            "version": "v3-json-first"
        }

        # Contar estructura
        num_semestres = len([k for k in resultados.keys() if k.startswith('semestre_')])
        num_asignaturas = sum(
            len(resultados[sem].keys())
            for sem in resultados.keys()
            if sem.startswith('semestre_')
        )

        print(f"  ✓ Estructura creada:")
        print(f"    • Semestres: {num_semestres}")
        print(f"    • Asignaturas: {num_asignaturas}")
        print(f"    • Grupos totales: {len(grupos_json)}")
        print(f"    • Conflictos profesores: {len(self.conflictos_profesores)}")
        print(f"    • Conflictos aulas: {len(self.conflictos_aulas)}")
        print(f"    • Conflictos alumnos: {len(self.conflictos_alumnos)}")
        print(f"    • Avisos: {len(self.avisos)}")

        return resultados

    def _actualizar_configuracion(self, resultados: Dict) -> None:
        """
        9.3 - Actualizar el diccionario de configuración con los resultados.

        Args:
            resultados: Diccionario con resultados_organizacion
        """
        print("\n[9.3] Actualizando configuración...")

        # Actualizar resultados_organizacion
        self.cfg["resultados_organizacion"] = resultados

        print(f"  ✓ Sección 'resultados_organizacion' actualizada")

    def _guardar_json(self, output_path: Path) -> bool:
        """
        9.4 - Guardar la configuración actualizada en archivo JSON.

        Args:
            output_path: Ruta donde guardar el archivo

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        print("\n[9.4] Guardando archivo JSON...")

        try:
            with output_path.open("w", encoding="utf-8") as fh:
                json.dump(self.cfg, fh, ensure_ascii=False, indent=2)

            # Verificar tamaño del archivo
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ Archivo guardado exitosamente")
            print(f"    • Ruta: {output_path}")
            print(f"    • Tamaño: {size_mb:.2f} MB")

            return True

        except Exception as e:
            print(f"  ✗ Error al guardar archivo: {e}")
            return False

    def _mostrar_resumen(self, output_path: Path, exito: bool) -> None:
        """9.5 - Mostrar resumen final de la fase de outputs."""
        print("\n" + "-" * 70)
        print("RESUMEN FASE 8")
        print("-" * 70)

        if exito:
            print(f"\n  ✓ GENERACIÓN DE OUTPUTS EXITOSA")
            print(f"\n  ARCHIVO GENERADO:")
            print(f"  • {output_path}")
            print(f"\n  CONTENIDO:")
            print(f"  • Grupos programados: {len(self.grupos)}")
            print(f"  • Total alumnos asignados: {sum(len(g.alumnos) for g in self.grupos if g.alumnos)}")
            print(f"  • Total sesiones: {sum(len(g.fechas) for g in self.grupos if g.fechas)}")

            if self.conflictos_profesores or self.conflictos_aulas:
                print(f"\n  CONFLICTOS REGISTRADOS:")
                if self.conflictos_profesores:
                    print(f"  • Profesores: {len(self.conflictos_profesores)}")
                if self.conflictos_aulas:
                    print(f"  • Aulas: {len(self.conflictos_aulas)}")
                if self.conflictos_alumnos:
                    print(f"  • Alumnos: {len(self.conflictos_alumnos)}")

            if self.avisos:
                print(f"\n  AVISOS REGISTRADOS:")
                print(f"  • Total avisos: {len(self.avisos)}")

            print(f"\n  COMPATIBILIDAD:")
            print(f"  ✓ Compatible con ver_resultados.py")
            print(f"  ✓ Formato JSON estándar del sistema")

        else:
            print(f"\n  ✗ ERROR AL GENERAR OUTPUTS")
            print(f"  Revise los errores anteriores")


# ========= CLASE DE POP-UPS =========
class PopupManager:
    """
    Utilidades para mostrar pop-ups informativos y de error.

    Si no existe un QApplication activo (ejecución en consola),
    los mensajes se muestran por terminal.
    """

    @staticmethod
    def _hay_app() -> bool:
        """Comprobar si hay un QApplication activo"""
        try:
            return QApplication.instance() is not None
        except Exception:
            return False

    @staticmethod
    def _mostrar_qmessagebox(
        icono: QMessageBox.Icon,
        titulo: str,
        mensaje: str,
        detalle: Optional[str] = None
    ) -> None:
        """Mostrar un QMessageBox con el estilo indicado"""
        box = QMessageBox()
        box.setIcon(icono)
        box.setWindowTitle(titulo)
        box.setText(mensaje)
        if detalle:
            box.setInformativeText(detalle)
        box.exec()

    @staticmethod
    def show_critical(titulo: str, mensaje: str, detalle: Optional[str] = None) -> None:
        """Mostrar un mensaje de error crítico"""
        if PopupManager._hay_app():
            PopupManager._mostrar_qmessagebox(QMessageBox.Icon.Critical, titulo, mensaje, detalle)
        else:
            # Modo consola
            print("\n" + "=" * 70)
            print(titulo)
            print("=" * 70)
            print(mensaje)
            if detalle:
                print(f"\nDetalle:\n{detalle}")
            print("=" * 70)

    @staticmethod
    def show_warning(titulo: str, mensaje: str, detalle: Optional[str] = None) -> None:
        """Mostrar una advertencia no crítica"""
        if PopupManager._hay_app():
            PopupManager._mostrar_qmessagebox(QMessageBox.Icon.Warning, titulo, mensaje, detalle)
        else:
            print("\n" + "-" * 70)
            print(f"ADVERTENCIA: {titulo}")
            print("-" * 70)
            print(mensaje)
            if detalle:
                print(f"\nDetalle:\n{detalle}")
            print("-" * 70)

    @staticmethod
    def show_info(titulo: str, mensaje: str, detalle: Optional[str] = None) -> None:
        """Mostrar un mensaje informativo"""
        if PopupManager._hay_app():
            PopupManager._mostrar_qmessagebox(QMessageBox.Icon.Information, titulo, mensaje, detalle)
        else:
            print("\n" + "-" * 70)
            print(titulo)
            print("-" * 70)
            print(mensaje)
            if detalle:
                print(f"\nDetalle:\n{detalle}")
            print("-" * 70)


def get_config_path() -> Path:
    """Devuelve ruta de configuracion_labs.json de forma compatible para .exe y para desarrollar"""
    if getattr(sys, "frozen", False):
        # Ejecutándose como .exe - está junto al ejecutable
        base_dir = Path(sys.executable).parent
    else:
        # Ejecutándose desde código fuente - motor_organizacion.py está en /src/modules/organizador
        base_dir = Path(__file__).resolve().parents[2]

    return base_dir / "configuracion_labs.json"


# ========= MAIN - TESTING DE FASE 8/8 =========
def main():
    """
    Función principal para ejecución completa del Motor de Organización.

    Ejecuta las 8 fases del sistema:
        FASE 1: Carga y Validación
        FASE 2: Cálculo de Fechas por Letra
        FASE 3: Aula Preferente
        FASE 4: Crear Grupos de Laboratorio
        FASE 5: Asignar Alumnos
        FASE 6: Asignar Profesores
        FASE 7: Programar Fechas
        FASE 8: Outputs (Generación JSON)
    """

    # Buscar configuración por defecto
    config_path = get_config_path()

    if not config_path.exists():
        print(f"ERROR: No se encontró el archivo de configuración en: {config_path}")
        PopupManager.show_critical(
            "❌ Error",
            "No se encuentra el archivo de configuración configuracion_labs.json.\n\n"
            f"Revisa que el archivo exista en la ruta esperada: {config_path}."
        )
        return

    # ===== FASE 1: CARGA Y VALIDACIÓN =====
    validador = ValidadorDatos(config_path)
    exito_fase1, cfg, errores = validador.ejecutar()

    # Mostrar errores detallados si los hay
    if errores:
        print("\n" + "=" * 70)
        print("ERRORES DETECTADOS")
        print("=" * 70)

        for i, error in enumerate(errores, 1):
            print(f"\n[{i}] {error.fase} - {error.tipo}")
            print(f"    {error.mensaje}")
            if error.detalle:
                print(f"    Detalle: {error.detalle}")

    # Si FASE 1 falla, detener
    if not exito_fase1:
        print("\n" + "=" * 70)
        print("✗ FASE 1 FALLÓ - Corrija los errores críticos antes de continuar")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 1",
            "La Fase 1 (Carga y Validación de Datos) no se ha podido completar.\n\n"
            "Esta fase verifica que el archivo de configuración contiene toda "
            "la información necesaria para continuar con el proceso. "
            "Los fallos más habituales son:\n\n"
            " • Faltan secciones obligatorias en el archivo JSON.\n"
            " • Alguna asignatura no tiene parámetros básicos definidos.\n"
            " • Grupos, horarios o aulas están incompletos o mal configurados.\n"
            " • Revisar si es compatible el número de sesiones en Asignaturas y el número de letras en Horarios.\n"
            " • Valores vacíos o inconsistentes (semana_inicio, num_sesiones, letras de grupos...) revisa calendario.\n\n"
            "Revisa el panel de errores y corrige las configuraciones indicadas."
        )
        return

    # ===== FASE 2: CÁLCULO DE FECHAS =====
    calculador = CalculadorFechas(cfg, validador.grupos_lab_posibles)
    exito_fase2, mapeo_fechas = calculador.ejecutar()

    # Si FASE 2 falla, detener
    if not exito_fase2:
        print("\n" + "=" * 70)
        print("✗ FASE 2 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 2",
            "La Fase 2 (Cálculo de fechas) no ha podido completarse.\n\n"
            "Esto suele ocurrir cuando:\n"
            " • No se definió correctamente la semana de inicio.\n"
            " • El número de sesiones no coincide con la duración del semestre.\n"
            " • Hay huecos en el calendario o semanas fuera de rango.\n\n"
            "Revisa la configuración del calendario en el módulo correspondiente."
        )
        return

    # ===== FASE 3: AULA PREFERENTE =====
    asignador_aulas = AsignadorAulaPreferente(cfg)
    exito_fase3, aulas_preferentes, conflictos_aulas_fase3 = asignador_aulas.ejecutar()

    # Si FASE 3 falla, detener
    if not exito_fase3:
        print("\n" + "=" * 70)
        print("✗ FASE 3 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 3",
            "La Fase 3 (Asignación de Aula Preferente) ha fallado.\n\n"
            "Generalmente ocurre cuando:\n"
            " • No existen aulas registradas en el sistema.\n"
            " • La asignatura no tiene definida un aula válida.\n"
            " • La capacidad del aula es insuficiente.\n\n"
            "Revisa la configuración de Aulas y las Asignaturas afectadas."
        )
        return

    # ===== FASE 4: CREAR GRUPOS =====
    creador_grupos = CreadorGruposLab(cfg, mapeo_fechas, aulas_preferentes)
    exito_fase4, grupos_creados, grupos_por_slot, conflictos_aulas_fase4 = creador_grupos.ejecutar()

    # Si FASE 4 falla, detener
    if not exito_fase4:
        print("\n" + "=" * 70)
        print("✗ FASE 4 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 4",
            "La Fase 4 (Creación de Grupos de laboratorio) no se ha completado.\n\n"
            "Posibles causas:\n"
            " • La asignatura no tiene configurados los grupos correctamente.\n"
            " • El horario tiene grupos con demasiadas letras o inconsistencias.\n\n"
            "Revisa el módulo 'Grupos' y 'Horarios' para corregir la configuración."
        )
        return

    # ===== FASE 5: ASIGNAR ALUMNOS =====
    asignador_alumnos = AsignadorAlumnos(cfg, grupos_creados)
    exito_fase5, grupos_con_alumnos, avisos_fase5, conflictos_alumnos_fase5 = asignador_alumnos.ejecutar()

    # Si FASE 5 falla, detener
    if not exito_fase5:
        print("\n" + "=" * 70)
        print("✗ FASE 5 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 5",
            "La Fase 5 (Asignación de alumnos) no pudo realizarse.\n\n"
            "Esto suele deberse a:\n"
            " • Alumnos matriculados en asignaturas sin grupos configurados.\n"
            " • Grupos saturados que no admiten más alumnos.\n"
            " • Datos incompletos en la matrícula de alumnos.\n"
            " • Existen alumnos sin información completa o con datos incorrectos.\n\n"
            "Revisa el módulo 'Alumnos' y asegúrate de que los grupos tienen capacidad."
        )
        return

    # ===== FASE 6: ASIGNAR PROFESORES =====
    asignador_profesores = AsignadorProfesores(cfg, grupos_con_alumnos)
    exito_fase6, grupos_con_profesores, avisos_fase6, conflictos_prof_fase6 = asignador_profesores.ejecutar()

    # Si FASE 6 falla, detener
    if not exito_fase6:
        print("\n" + "=" * 70)
        print("✗ FASE 6 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 6",
            "La Fase 6 (Asignación de profesores) ha fallado.\n\n"
            "Causas frecuentes:\n"
            " • Profesores sin disponibilidad compatible con los grupos.\n"
            " • Falta de profesores asignados a ciertas asignaturas.\n"
            " • Conflictos entre múltiples grupos asignados al mismo profesor.\n\n"
            "Revisa el módulo 'Profesores' y asegúrate de que todos tienen horarios válidos."
        )
        return

    # ===== FASE 7: PROGRAMAR FECHAS =====
    # IMPORTANTE: Pasar mapeo_fechas de Fase 2
    programador_fechas = ProgramadorFechas(cfg, grupos_con_profesores, mapeo_fechas)
    exito_fase7, grupos_con_fechas, conflictos_profes_fase7, conflictos_aulas_fase7 = programador_fechas.ejecutar()

    # Si FASE 7 falla, detener
    if not exito_fase7:
        print("\n" + "=" * 70)
        print("✗ FASE 7 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 7",
            "La Fase 7 (Programación de Fechas del laboratorio) no pudo completarse.\n\n"
            "Suele producirse cuando:\n"
            " • Existen conflictos de disponibilidad entre profesores y grupos.\n"
            " • No hay aulas libres para algunas sesiones.\n"
            " • Las fechas generadas no encajan en el calendario configurado.\n"
            " • Hay grupos que quedaron sin sesión/fecha asignada.\n\n"
            "Revisa conflictos de profesores, aulas y disponibilidad del calendario."
        )
        return

    # ===== FASE 8: OUTPUTS (GENERACIÓN JSON) =====
    # Combinar todos los avisos de las fases anteriores
    avisos_totales = avisos_fase5 + avisos_fase6

    # Combinar Conflictos de Todas las Fases
    conflictos_aulas_totales = conflictos_aulas_fase3 + conflictos_aulas_fase4 + conflictos_aulas_fase7
    conflictos_profesores_totales = conflictos_prof_fase6 + conflictos_profes_fase7
    conflictos_alumnos_totales = conflictos_alumnos_fase5

    # Crear generador de outputs
    generador = GeneradorOutputs(
        cfg=cfg,
        grupos=grupos_con_fechas,
        conflictos_profesores=conflictos_profesores_totales,
        conflictos_aulas=conflictos_aulas_totales,
        conflictos_alumnos=conflictos_alumnos_totales,
        avisos=avisos_totales
    )

    # Ejecutar generación y guardar
    exito_fase8, cfg_actualizada = generador.ejecutar(config_path)

    if not exito_fase8:
        print("\n" + "=" * 70)
        print("✗ FASE 8 FALLÓ")
        print("=" * 70)
        PopupManager.show_critical(
            "❌ Error en Fase 8",
            "La Fase 8 (Generación del archivo final) ha fallado.\n\n"
            "Esto puede deberse a:\n"
            " • Falta de permisos para guardar el archivo.\n"
            " • La ruta de destino no es válida o está bloqueada.\n"
            " • El JSON resultante es inconsistente.\n"
            " • El archivo está siendo usado por otro programa.\n\n"
            "Revisa la ruta de guardado y asegúrate de que el archivo no está bloqueado."
        )
        return

    # ===== RESULTADO FINAL =====
    print("\n" + "=" * 70)
    print("✓ TODAS LAS FASES COMPLETADAS CON ÉXITO")
    print("=" * 70)

    print(f"\n  ESTADÍSTICAS FINALES:")
    print(f"  {'─' * 66}")
    print(f"\n  • Grupos validados: {len(validador.grupos_lab_posibles)}")
    print(f"  • Combinaciones de fechas: {len(mapeo_fechas)}")
    print(f"  • Aulas preferentes asignadas: {len(aulas_preferentes)}")
    print(f"  • Grupos de laboratorio creados: {len(grupos_creados)}")
    print(f"  • Slots únicos (dia, franja): {len(grupos_por_slot)}")
    print(f"  • Total alumnos asignados: {sum(len(g.alumnos) for g in grupos_con_alumnos)}")
    print(f"  • Grupos con profesor: {sum(1 for g in grupos_con_profesores if g.profesor_id)}/{len(grupos_con_profesores)}")
    print(f"  • Grupos con fechas: {sum(1 for g in grupos_con_fechas if g.fechas)}/{len(grupos_con_fechas)}")
    print(f"  • Total sesiones programadas: {sum(len(g.fechas) for g in grupos_con_fechas)}")

    # Mostrar avisos y conflictos si existen
    if avisos_totales:
        print(f"\n  AVISOS:")
        print(f"  {'─' * 66}")
        print(f"  ⚠ Total avisos: {len(avisos_totales)}")

    if conflictos_profes_fase7 or conflictos_aulas_fase7:
        print(f"\n  CONFLICTOS:")
        print(f"  {'─' * 66}")
        if conflictos_profes_fase7:
            print(f"  ⚠ Conflictos de profesores: {len(conflictos_profes_fase7)}")
        if conflictos_aulas_fase7:
            print(f"  ⚠ Conflictos de aulas: {len(conflictos_aulas_fase7)}")

    print(f"\n  ARCHIVO ACTUALIZADO:")
    print(f"  {'─' * 66}")
    print(f"  {config_path}")
    print(f"  ✓ Sección 'resultados_organizacion' actualizada")
    print(f"  ✓ Compatible con ver_resultados.py")

    print("\n" + "=" * 70)
    print("El sistema ha completado la organización de laboratorios")
    print("Puedes visualizar los resultados con ver_resultados.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
