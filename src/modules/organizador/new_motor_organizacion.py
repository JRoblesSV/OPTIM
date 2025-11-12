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
    FASE 8: Validaciones Finales
    FASE 9: Outputs
"""


from __future__ import annotations
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set


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


def save_configuration(path: Path, cfg: Dict) -> None:
    """
    Guardar configuración en archivo JSON.

    Args:
        path: Ruta donde guardar el archivo
        cfg: Diccionario con la configuración
    """
    with path.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)


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
                        (f"{semestre} Semestre", asig_codigo, grupo_codigo)
                    )

                    if grupos_lab_posibles is None:
                        # Búsqueda alternativa por asignatura y grupo (sin semestre exacto)
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

    def ejecutar(self) -> Tuple[bool, Dict[Tuple[str, str], str]]:
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

        return True, self.aulas_preferentes

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
        self.contador_labels: Dict[str, int] = {}  # Para generar labels únicos

    def ejecutar(self) -> Tuple[bool, List[GrupoLab], Dict[Tuple[str, str], List[GrupoLab]]]:
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

        return True, self.grupos_creados, self.grupos_por_slot

    def _normalizar_semestre(self, semestre) -> Optional[str]:
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
        sem_norm = self._normalizar_semestre(semestre)
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

    def _generar_label(self, grupo: str) -> str:
        """
        Generar label único para un grupo (ej: A404-01, A404-02...).

        Utiliza un contador interno por código de grupo para generar
        identificadores únicos secuenciales.

        Args:
            grupo: Código de grupo base (ej: "A404")

        Returns:
            Label único con formato GRUPO-NN
        """
        if grupo not in self.contador_labels:
            self.contador_labels[grupo] = 0

        self.contador_labels[grupo] += 1
        numero = self.contador_labels[grupo]

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

        # Recorrer cada combinación en mapeo_fechas (ordenado por letra)
        for (semestre, asignatura, grupo, dia, letra), fechas in sorted(self.mapeo_fechas.items(), key=lambda x: x[0][-1]):

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
                    continue

                # Obtener capacidad del aula
                capacidad = self._obtener_capacidad_aula(aula_preferente)

                # 4.4 - Determinar si es slot mixto
                is_slot_mixto = self._determinar_slot_mixto(semestre, asignatura, grupo, dia, franja)

                # 4.5 - Generar label único para este grupo de laboratorio
                label = self._generar_label(grupo)

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

                # Log informativo
                mixto_str = f" [MIXTO con {grupo_doble}]" if is_slot_mixto else ""
                print(f"  ✓ {label} | {semestre}:{asignatura} | {dia} {franja} | Letra {letra} | "
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


# ========= MAIN - TESTING DE FASE 4/9 =========
def main():
    """Función principal para testing de las FASES 1, 2 y 3."""

    # Buscar configuración por defecto
    config_path = Path(__file__).resolve().parents[2] / "configuracion_labs.json"

    if not config_path.exists():
        print(f"ERROR: No se encontró el archivo de configuración en: {config_path}")
        sys.exit(1)

    # ===== FASE 1 =====
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
        sys.exit(1)

    # ===== FASE 2 =====
    calculador = CalculadorFechas(cfg, validador.grupos_lab_posibles)
    exito_fase2, mapeo_fechas = calculador.ejecutar()

    # Si FASE 2 falla, detener
    if not exito_fase2:
        print("\n" + "=" * 70)
        print("✗ FASE 2 FALLÓ")
        print("=" * 70)
        sys.exit(1)

    # ===== FASE 3 =====
    asignador_aulas = AsignadorAulaPreferente(cfg)
    exito_fase3, aulas_preferentes = asignador_aulas.ejecutar()

    # Si FASE 3 falla, detener
    if not exito_fase3:
        print("\n" + "=" * 70)
        print("✗ FASE 3 FALLÓ")
        print("=" * 70)
        sys.exit(1)

    # ===== FASE 4 =====
    creador_grupos = CreadorGruposLab(cfg, mapeo_fechas, aulas_preferentes)
    exito_fase4, grupos_creados, grupos_por_slot = creador_grupos.ejecutar()

    # Si FASE 4 falla, detener
    if not exito_fase4:
        print("\n" + "=" * 70)
        print("✗ FASE 4 FALLÓ")
        print("=" * 70)
        sys.exit(1)

    # ===== RESULTADO FINAL =====
    print("\n" + "=" * 70)
    print("✓ FASES 1, 2, 3 Y 4 COMPLETADAS CON ÉXITO")
    print("=" * 70)
    print(f"\n  • Grupos validados: {len(validador.grupos_lab_posibles)}")
    print(f"  • Combinaciones de fechas: {len(mapeo_fechas)}")
    print(f"  • Aulas preferentes asignadas: {len(aulas_preferentes)}")
    print(f"  • Grupos de laboratorio creados: {len(grupos_creados)}")
    print(f"  • Slots únicos (dia, franja): {len(grupos_por_slot)}")
    print("\nEl sistema está listo para continuar con la FASE 5")
    sys.exit(0)


if __name__ == "__main__":
    main()
