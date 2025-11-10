"""
Motor de Organización v2 - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)

ESTRUCTURA DEL MOTOR:
    FASE 1: Carga y Validación
    FASE 2: Cálculo de Fechas por Letra
    FASE 3: Aula Preferente
    FASE 4: Crear Grupos de Laboratorio
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


# ========= CONSTANTES Y PATRONES (REUTILIZADO DEL MOTOR ANTERIOR) =========
# Patrones de grupos
PAT_SIMPLE = re.compile(r"^[A-Z]\d{3}$")  # Ejemplo: A404
PAT_DOBLE = re.compile(r"^[A-Z]{2}\d{3}$")  # Ejemplo: EE403

# Orden de días de la semana
DAY_ORDER = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Miercoles": 2,
    "Jueves": 3, "Viernes": 4, "Sábado": 5, "Sabado": 5, "Domingo": 6
}


# ========= MODELOS DE DATOS (REUTILIZADO Y MEJORADO) =========
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


# ========= UTILIDADES GENERALES (REUTILIZADO DEL MOTOR ANTERIOR) =========
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
class DatosValidador:
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
    Clase responsable de la FASE 2: Cálculo de fechas por letra.

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


# ========= MAIN - TESTING DE FASE 2/9 =========
def main():
    """Función principal para testing de las FASES 1 y 2."""

    # Buscar configuración por defecto
    config_path = Path(__file__).resolve().parents[2] / "configuracion_labs.json"

    if not config_path.exists():
        print(f"ERROR: No se encontró el archivo de configuración en: {config_path}")
        sys.exit(1)

    # ===== FASE 1 =====
    validador = DatosValidador(config_path)
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

    # Resultado final
    print("\n" + "=" * 70)
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

    # ===== RESULTADO FINAL =====
    print("\n" + "=" * 70)
    print("✓ FASES 1 Y 2 COMPLETADAS CON ÉXITO")
    print("=" * 70)
    print(f"\n  • Grupos validados: {len(validador.grupos_lab_posibles)}")
    print(f"  • Combinaciones de fechas: {len(mapeo_fechas)}")
    print("\nEl sistema está listo para continuar con la FASE 3")
    sys.exit(0)


if __name__ == "__main__":
    main()
