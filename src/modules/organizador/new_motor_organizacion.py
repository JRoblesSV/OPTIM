
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

    def get_total_semanas_calendario(self) -> int:
        """
        Obtener el número total de semanas desde el calendario configurado.

        Returns:
            int: Número total de semanas definidas en el calendario o 14 por defecto.
        """
        try:
            calendario_cfg = self.cfg.get("configuracion", {}).get("calendario", {})
            semanas_total = calendario_cfg.get("semanas_total")
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
        total_semanas_calendario = self.get_total_semanas_calendario()

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

        print(f"  • Total grupos validados: {len(self.grupos_lab_posibles)}")
        print()


# ========= MAIN - TESTING DE FASE 1 =========
def main():
    """Función principal para testing de la FASE 1."""

    # Buscar configuración por defecto
    config_path = Path(__file__).resolve().parents[2] / "configuracion_labs.json"

    if not config_path.exists():
        print(f"ERROR: No se encontró el archivo de configuración en: {config_path}")
        print("Uso: python motor_organizacion_v2.py")
        sys.exit(1)

    # Ejecutar FASE 1
    validador = DatosValidador(config_path)
    exito, cfg, errores = validador.ejecutar()

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
    if exito:
        print("✓ FASE 1 COMPLETADA CON ÉXITO")
        print("=" * 70)
        print("\nEl sistema está listo para continuar con la FASE 2")
        sys.exit(0)
    else:
        print("✗ FASE 1 FALLÓ - Corrija los errores críticos antes de continuar")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
