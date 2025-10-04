#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración de Parámetros - OPTIM - Sistema de Programación Automática de Laboratorios
Desarrollado por SoftVier para ETSIDI (UPM)

MÓDULO: Definición de restricciones y parámetros del sistema de organización
FUNCIONALIDAD: Configuración centralizada de todas las reglas y prioridades
TEMA: Oscuro profesional | Precisión técnica | Simplicidad funcional

Stack: Python + Configuración declarativa
"""


# ====================================================================
# RESTRICCIONES DURAS DEL SISTEMA (OBLIGATORIAS - NO NEGOCIABLES)
# ====================================================================

class RestriccionesDuras:
    """
    Restricciones que NUNCA pueden violarse - El sistema debe fallar antes que incumplirlas

    Características:
    - Violación = Error crítico del sistema
    - No tienen pesos configurables (siempre peso máximo)
    - Validación obligatoria antes de cualquier asignación
    - Causan rechazo automático de configuraciones inválidas
    """

    # ══════════════════════════════════════════════════════════════
    # RESTRICCIONES TEMPORALES ABSOLUTAS
    # ══════════════════════════════════════════════════════════════

    PROFESOR_UBICUIDAD_PROHIBIDA = {
        "descripcion": "Un profesor no puede estar en múltiples aulas simultáneamente",
        "alcance": "Conflictos temporales por profesor",
        "validacion": "Por slot temporal exacto (día + hora_inicio + hora_fin)",
        "consecuencia_violacion": "Conflicto físico imposible de resolver"
    }

    AULA_OCUPACION_EXCLUSIVA = {
        "descripcion": "Un aula no puede albergar múltiples asignaturas simultáneamente",
        "alcance": "Conflictos temporales por aula",
        "validacion": "Por slot temporal exacto (día + hora_inicio + hora_fin)",
        "consecuencia_violacion": "Solapamiento físico de grupos"
    }

    # ══════════════════════════════════════════════════════════════
    # RESTRICCIONES DE CAPACIDAD FÍSICA
    # ══════════════════════════════════════════════════════════════

    CAPACIDAD_AULA_ABSOLUTA = {
        "descripcion": "Número de alumnos por grupo no puede exceder capacidad del aula",
        "alcance": "Límites físicos de infraestructura",
        "validacion": "num_alumnos <= capacidad_aula para cada asignación",
        "consecuencia_violacion": "Imposibilidad física de acomodar alumnos"
    }

    # ══════════════════════════════════════════════════════════════
    # RESTRICCIONES DE DISPONIBILIDAD OBLIGATORIA
    # ══════════════════════════════════════════════════════════════

    DISPONIBILIDAD_PROFESOR_CALENDARIO = {
        "descripcion": "Respetar días de trabajo y horarios no bloqueados de profesores",
        "alcance": "Calendario personal de cada profesor",
        "validacion": "día in dias_trabajo AND horario not in horarios_bloqueados",
        "consecuencia_violacion": "Asignación a profesor no disponible"
    }

    DISPONIBILIDAD_PROFESOR_FECHAS = {
        "descripcion": "Respetar fechas específicas no disponibles de profesores",
        "alcance": "Fechas puntuales de indisponibilidad",
        "validacion": "fecha_especifica not in fechas_no_disponibles",
        "consecuencia_violacion": "Conflicto con agenda personal/institucional"
    }

    DISPONIBILIDAD_AULA_GENERAL = {
        "descripcion": "Solo usar aulas marcadas como disponibles",
        "alcance": "Estado operativo de infraestructura",
        "validacion": "aula.disponible == True",
        "consecuencia_violacion": "Uso de aula fuera de servicio"
    }

    DISPONIBILIDAD_AULA_FECHAS = {
        "descripcion": "Respetar fechas específicas no disponibles de aulas",
        "alcance": "Mantenimientos, reservas especiales, etc.",
        "validacion": "fecha_especifica not in fechas_no_disponibles",
        "consecuencia_violacion": "Conflicto con calendario de mantenimiento"
    }

    # ══════════════════════════════════════════════════════════════
    # RESTRICCIONES DE COMPATIBILIDAD ACADÉMICA
    # ══════════════════════════════════════════════════════════════

    COMPATIBILIDAD_ASIGNATURA_AULA = {
        "descripcion": "Solo usar aulas relacionadas/compatibles con la asignatura",
        "alcance": "Equipamiento especializado y configuración técnica",
        "validacion": "asignatura in aula.asignaturas_asociadas",
        "consecuencia_violacion": "Falta de equipamiento necesario para laboratorio"
    }

    HABILITACION_PROFESOR_ASIGNATURA = {
        "descripcion": "Solo profesores que imparten esa asignatura específica",
        "alcance": "Competencias académicas y autorización institucional",
        "validacion": "asignatura in profesor.asignaturas_imparte",
        "consecuencia_violacion": "Profesor no habilitado para contenido específico"
    }

    # ══════════════════════════════════════════════════════════════
    # RESTRICCIONES DE COHERENCIA TEMPORAL
    # ══════════════════════════════════════════════════════════════

    HORARIOS_CONFIGURADOS_OBLIGATORIOS = {
        "descripcion": "Solo usar horarios configurados en horarios_grid por asignatura",
        "alcance": "Planificación académica autorizada",
        "validacion": "slot_temporal in horarios_grid[asignatura] AND día in días_permitidos",
        "consecuencia_violacion": "Horario no autorizado por planificación académica"
    }

    CALENDARIO_ACADEMICO_VIGENTE = {
        "descripcion": "Solo asignar en fechas que existen en el calendario académico",
        "alcance": "Período lectivo oficial",
        "validacion": "fecha_especifica in fechas_calendario AND horario_asignado == día",
        "consecuencia_violacion": "Asignación fuera del período lectivo oficial"
    }

    # ══════════════════════════════════════════════════════════════
    # RESTRICCIONES DE EQUILIBRIO ORGANIZACIONAL
    # ══════════════════════════════════════════════════════════════

    GRUPOS_PARES_OBLIGATORIO = {
        "descripcion": "Los grupos deben ser pares; si impares, solo 1 grupo puede ser impar",
        "alcance": "Organización equilibrada de laboratorios",
        "validacion": "len(grupos) % 2 == 0 OR grupos_impares <= 1",
        "consecuencia_violacion": "Desequilibrio organizacional inaceptable"
    }

    ALUMNOS_ELEGIBLES_EXCLUSIVOS = {
        "descripcion": "Solo alumnos matriculados que no tengan laboratorio aprobado",
        "alcance": "Elegibilidad académica para laboratorio",
        "validacion": "matriculado == True AND lab_aprobado == False",
        "consecuencia_violacion": "Inclusión de alumnos no elegibles"
    }


# ====================================================================
# RESTRICCIONES BLANDAS DEL SISTEMA (DESEABLES - CONFIGURABLES)
# ====================================================================

class RestriccionesBlandas:
    """
    Restricciones deseables que pueden violarse temporalmente pero deben minimizarse

    Características:
    - Violación = Penalización en función objetivo, no error crítico
    - Tienen pesos configurables (0-100)
    - El sistema busca minimizar violaciones pero las tolera si es necesario
    - Pueden intercambiarse unas por otras según prioridades
    """

    # ══════════════════════════════════════════════════════════════
    # CONFLICTOS ACADÉMICOS DE ALUMNOS
    # ══════════════════════════════════════════════════════════════

    ALUMNO_SIN_CONFLICTOS_TEMPORALES = {
        "descripcion": "Un alumno no puede tener múltiples asignaturas simultáneamente",
        "alcance": "Conflictos en horario personal de estudiantes",
        "peso_default": 15,
        "metrica": "Número de alumnos con solapamientos temporales",
        "optimizacion": "Minimizar intersecciones entre grupos por slot temporal"
    }

    # ══════════════════════════════════════════════════════════════
    # CALIDAD DE DISTRIBUCIÓN ACADÉMICA
    # ══════════════════════════════════════════════════════════════

    EQUILIBRIO_GRUPOS_OPTIMO = {
        "descripcion": "Grupos deben tener tamaños similares (diferencia máxima configurable)",
        "alcance": "Calidad pedagógica y equidad entre estudiantes",
        "peso_default": 25,
        "metrica": "Diferencia máxima entre tamaño mayor y menor grupo",
        "optimizacion": "Minimizar diferencias de tamaño entre grupos de misma asignatura"
    }

    UTILIZACION_AULA_EFICIENTE = {
        "descripcion": "Optimizar ocupación de aulas (objetivo configurable, típicamente 80-90%)",
        "alcance": "Eficiencia en uso de recursos físicos",
        "peso_default": 25,
        "metrica": "Desviación del objetivo de utilización por aula",
        "optimizacion": "Acercar utilización real al objetivo configurado"
    }


# ====================================================================
# PRIORIDADES Y OPTIMIZACIONES DEL SISTEMA
# ====================================================================

class PrioridadesOptimizacion:
    """
    Criterios de optimización que mejoran la calidad de la solución

    Características:
    - Definen qué constituye una "mejor" solución
    - Tienen pesos configurables que determinan importancia relativa
    - Se aplican después de garantizar restricciones duras
    - Permiten balance entre múltiples objetivos
    """

    # ══════════════════════════════════════════════════════════════
    # PRIORIDADES TEMPORALES CRÍTICAS
    # ══════════════════════════════════════════════════════════════

    HORAS_TEMPRANAS_PRIORITARIAS = {
        "descripcion": "Rellenar franjas tempranas antes que tardías (ej: 9:30-11:30 antes que 17:30-19:30)",
        "justificacion": "Mejor rendimiento académico y disponibilidad de estudiantes",
        "peso_default": 40,  # PESO CRÍTICO
        "implementacion": "Ordenar horarios por hora_inicio ascendente",
        "metrica": "Porcentaje de asignaciones en horarios tempranos vs tardíos"
    }

    FECHAS_LEJANAS_PRIORITARIAS = {
        "descripcion": "Llenar días más lejanos primero, dejar próximos libres para flexibilidad",
        "justificacion": "Maximizar flexibilidad para ajustes y cambios posteriores",
        "peso_default": 30,
        "implementacion": "Ordenar fechas disponibles por fecha descendente (más lejana primero)",
        "metrica": "Distribución temporal de asignaciones a lo largo del semestre"
    }

    # ══════════════════════════════════════════════════════════════
    # PRIORIDADES ACADÉMICAS INSTITUCIONALES
    # ══════════════════════════════════════════════════════════════

    DOBLE_GRADO_PRIORIDAD_ABSOLUTA = {
        "descripcion": "Doble grado (EE302, etc.) tiene prioridad sobre grado simple (A302, etc.)",
        "justificacion": "Menor flexibilidad horaria y mayor complejidad académica",
        "peso_default": 30,
        "implementacion": "Procesar alumnos doble grado primero en algoritmo de grupos",
        "criterio_deteccion": "Grupos con 2+ letras al inicio (EE, AA, etc.) = doble grado"
    }

    GRUPOS_PARES_PREFERENCIA = {
        "descripcion": "Preferir número par de grupos por asignatura para mejor organización",
        "justificacion": "Facilita organización, coordinación y distribución de recursos",
        "peso_default": 20,
        "implementacion": "Ajustar número de grupos hacia par cuando sea posible",
        "metrica": "Porcentaje de asignaturas con número par de grupos"
    }

    # ══════════════════════════════════════════════════════════════
    # OPTIMIZACIONES DE RECURSOS
    # ══════════════════════════════════════════════════════════════

    DISTRIBUCION_PROFESORES_EQUILIBRADA = {
        "descripcion": "Distribuir carga de trabajo equitativamente entre profesores",
        "justificacion": "Equidad laboral y optimización de recursos humanos",
        "peso_default": 20,
        "implementacion": "Ordenar profesores por carga actual (ascendente)",
        "metrica": "Diferencia máxima de grupos asignados entre profesores"
    }

    COMPATIBILIDAD_ASIGNATURA_AULA_OPTIMA = {
        "descripcion": "Maximizar compatibilidad y especialización aula-asignatura",
        "justificacion": "Mejor aprovechamiento de equipamiento especializado",
        "peso_default": 25,
        "implementacion": "Priorizar aulas más específicas para cada asignatura",
        "metrica": "Nivel de especialización de aulas asignadas"
    }


# ====================================================================
# PARÁMETROS DE CONFIGURACIÓN DEL SISTEMA
# ====================================================================

class ParametrosConfiguracion:
    """
    Parámetros numéricos y booleanos que controlan el comportamiento del sistema

    Características:
    - Valores ajustables según necesidades institucionales
    - Afectan calidad y características de la solución generada
    - Permiten adaptación a diferentes contextos académicos
    - Deben validarse para evitar configuraciones incoherentes
    """

    # ══════════════════════════════════════════════════════════════
    # PARÁMETROS BOOLEANOS DE ACTIVACIÓN
    # ══════════════════════════════════════════════════════════════

    PARAMETROS_BOOLEANOS = {
        "preferir_grupos_pares": {
            "descripcion": "Activar preferencia por número par de grupos",
            "default": True,
            "impacto": "Algoritmo de generación de grupos"
        },

        "priorizar_horas_tempranas": {
            "descripcion": "Activar priorización de franjas horarias tempranas",
            "default": True,
            "impacto": "Orden de asignación de horarios"
        },

        "aplicar_prioridad_doble_grado": {
            "descripcion": "Activar prioridad de doble grado sobre grado simple",
            "default": True,
            "impacto": "Orden de procesamiento de alumnos"
        },

        "permitir_intercambio_automatico": {
            "descripcion": "Permitir intercambios automáticos para resolver conflictos",
            "default": True,
            "impacto": "Capacidad de resolución automática de problemas"
        },

        "generar_reportes_detallados": {
            "descripcion": "Activar generación de reportes y análisis completos",
            "default": True,
            "impacto": "Nivel de detalle en salidas del sistema"
        }
    }

    # ══════════════════════════════════════════════════════════════
    # PESOS DE OPTIMIZACIÓN (0-100)
    # ══════════════════════════════════════════════════════════════

    PESOS_OPTIMIZACION = {
        "peso_horas_tempranas": {
            "descripcion": "Peso para priorización de horas tempranas",
            "rango": "0-100",
            "default": 40,
            "categoria": "CRÍTICO - Mayor impacto en calidad"
        },

        "peso_doble_grado": {
            "descripcion": "Peso para prioridad de estudiantes de doble grado",
            "rango": "0-100",
            "default": 30,
            "categoria": "Alto impacto académico"
        },

        "peso_equilibrio_grupos": {
            "descripcion": "Peso para equilibrio de tamaños entre grupos",
            "rango": "0-100",
            "default": 25,
            "categoria": "Calidad pedagógica"
        },

        "peso_utilizacion_aulas": {
            "descripcion": "Peso para optimización de utilización de aulas",
            "rango": "0-100",
            "default": 25,
            "categoria": "Eficiencia de recursos"
        },

        "peso_compatibilidad_asignaturas": {
            "descripcion": "Peso para compatibilidad asignatura-aula",
            "rango": "0-100",
            "default": 25,
            "categoria": "Especialización técnica"
        },

        "peso_grupos_pares": {
            "descripcion": "Peso para preferencia por número par de grupos",
            "rango": "0-100",
            "default": 20,
            "categoria": "Organización administrativa"
        },

        "peso_distribucion_profesores": {
            "descripcion": "Peso para distribución equilibrada entre profesores",
            "rango": "0-100",
            "default": 20,
            "categoria": "Equidad laboral"
        },

        "peso_conflictos_alumnos": {
            "descripcion": "Peso para penalización de conflictos temporales de alumnos",
            "rango": "0-100",
            "default": 15,
            "categoria": "Restricción blanda principal"
        }
    }

    # ══════════════════════════════════════════════════════════════
    # CONFIGURACIONES ADICIONALES NUMÉRICAS
    # ══════════════════════════════════════════════════════════════

    CONFIGURACIONES_ADICIONALES = {
        "diferencia_maxima_grupos": {
            "descripcion": "Diferencia máxima permitida entre tamaños de grupos",
            "tipo": "int",
            "default": 1,
            "rango": "0-5",
            "unidad": "alumnos"
        },

        "utilizacion_aula_optima": {
            "descripcion": "Porcentaje objetivo de utilización de aulas",
            "tipo": "int",
            "default": 85,
            "rango": "60-95",
            "unidad": "porcentaje"
        },

        "factor_penalizacion_conflictos": {
            "descripcion": "Factor multiplicador para penalizar conflictos de alumnos",
            "tipo": "int",
            "default": 100,
            "rango": "1-1000",
            "unidad": "multiplicador"
        },

        "tamaño_grupo_minimo": {
            "descripcion": "Número mínimo de alumnos por grupo",
            "tipo": "int",
            "default": 8,
            "rango": "5-15",
            "unidad": "alumnos"
        },

        "tamaño_grupo_maximo": {
            "descripcion": "Número máximo de alumnos por grupo",
            "tipo": "int",
            "default": 20,
            "rango": "15-30",
            "unidad": "alumnos"
        }
    }


# ====================================================================
# ORIGEN Y LOCALIZACIÓN DE DATOS EN EL SISTEMA
# ====================================================================

class OrigenDatos:
    """
    Mapeo completo de dónde se obtiene cada tipo de información necesaria

    Características:
    - Referencia exacta a secciones del JSON de configuración
    - Estructura de datos esperada para cada elemento
    - Validaciones requeridas para garantizar integridad
    - Dependencias entre diferentes fuentes de datos
    """

    # ══════════════════════════════════════════════════════════════
    # DATOS DE ALUMNOS
    # ══════════════════════════════════════════════════════════════

    ALUMNOS = {
        "ubicacion_json": "configuracion.alumnos.datos",
        "estructura_requerida": {
            "dni": "string - Identificador único obligatorio",
            "nombre": "string - Nombre del alumno",
            "apellidos": "string - Apellidos del alumno",
            "email": "string - Correo electrónico",
            "grupos_matriculado": "list[string] - Códigos de grupos (ej: ['A302', 'EE302'])",
            "asignaturas_matriculadas": "dict - {asignatura: {matriculado: bool, lab_aprobado: bool}}",
            "matricula": "string - Número de matrícula",
            "exp_agora": "string - Expediente Agora",
            "exp_centro": "string - Expediente del centro"
        },
        "validaciones_criticas": [
            "DNI único y no vacío",
            "grupos_matriculado debe ser lista válida",
            "asignaturas_matriculadas debe contener datos de elegibilidad"
        ],
        "procesamiento_especial": "Detección automática de doble grado por códigos de grupo"
    }

    # ══════════════════════════════════════════════════════════════
    # DATOS DE PROFESORES
    # ══════════════════════════════════════════════════════════════

    PROFESORES = {
        "ubicacion_json": "configuracion.profesores.datos",
        "estructura_requerida": {
            "id": "string - Identificador único obligatorio",
            "nombre": "string - Nombre del profesor",
            "apellidos": "string - Apellidos del profesor",
            "asignaturas_imparte": "list[string] - Códigos de asignaturas habilitadas",
            "dias_trabajo": "list[string] - Días disponibles (['Lunes', 'Martes', ...])",
            "horarios_bloqueados": "dict - {día: {franja: motivo}}",
            "fechas_no_disponibles": "list[string] - Fechas específicas no disponibles",
            "observaciones": "string - Notas adicionales"
        },
        "validaciones_criticas": [
            "ID único y no vacío",
            "asignaturas_imparte debe contener al menos una asignatura",
            "dias_trabajo debe contener al menos un día válido",
            "horarios_bloqueados debe usar formato HH:MM-HH:MM"
        ]
    }

    # ══════════════════════════════════════════════════════════════
    # DATOS DE AULAS
    # ══════════════════════════════════════════════════════════════

    AULAS = {
        "ubicacion_json": "configuracion.aulas.datos",
        "estructura_requerida": {
            "nombre": "string - Identificador único del aula",
            "capacidad": "int - Número máximo de alumnos",
            "equipamiento": "string - Descripción del equipamiento",
            "edificio": "string - Edificio donde se encuentra",
            "planta": "string - Planta del edificio",
            "disponible": "bool - Si está operativa",
            "asignaturas_asociadas": "list[string] - Asignaturas compatibles",
            "fechas_no_disponibles": "list[string] - Fechas de mantenimiento/reservas"
        },
        "validaciones_criticas": [
            "Nombre único y no vacío",
            "Capacidad mayor que 0",
            "asignaturas_asociadas debe contener al menos una asignatura",
            "fechas_no_disponibles en formato DD/MM/YYYY"
        ]
    }

    # ══════════════════════════════════════════════════════════════
    # DATOS DE ASIGNATURAS
    # ══════════════════════════════════════════════════════════════

    ASIGNATURAS = {
        "ubicacion_json": "configuracion.asignaturas.datos",
        "estructura_requerida": {
            "codigo": "string - Código único de asignatura",
            "nombre": "string - Nombre completo",
            "curso": "string - Curso académico",
            "semestre": "string - Semestre de impartición",
            "tipo": "string - Tipo de asignatura",
            "descripcion": "string - Descripción detallada",
            "grupos_asociados": "list[string] - Grupos que cursan la asignatura",
            "planificacion": "dict - {clases_año: int, grupos_previstos: int}",
            "configuracion_laboratorio": "dict - Configuración específica de laboratorio"
        },
        "validaciones_criticas": [
            "Código único y no vacío",
            "planificacion.clases_año debe ser número positivo",
            "grupos_asociados debe coincidir con grupos de alumnos matriculados"
        ]
    }

    # ══════════════════════════════════════════════════════════════
    # DATOS DE HORARIOS
    # ══════════════════════════════════════════════════════════════

    HORARIOS = {
        "ubicacion_json": "configuracion.horarios.datos",
        "estructura_requerida": {
            "asignatura": {
                "grupos": "list[string] - Grupos que pueden usar este horario",
                "horarios_grid": "dict - {franja: {día: [grupos_permitidos]}}"
            }
        },
        "formato_franja": "HH:MM-HH:MM (ej: '09:30-11:30')",
        "dias_validos": "['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']",
        "validaciones_criticas": [
            "Franjas en formato correcto HH:MM-HH:MM",
            "Días deben ser nombres válidos de días de semana",
            "grupos_permitidos debe corresponder con grupos existentes",
            "Coherencia entre semestres si hay múltiples semestres"
        ],
        "procesamiento_especial": "Soporte multi-semestre con identificadores únicos"
    }

    # ══════════════════════════════════════════════════════════════
    # DATOS DE CALENDARIO ACADÉMICO
    # ══════════════════════════════════════════════════════════════

    CALENDARIO = {
        "ubicacion_json": "configuracion.calendario.datos",
        "estructura_requerida": {
            "semestre_N": {
                "YYYY-MM-DD": {
                    "horario_asignado": "string - Día de la semana",
                    "observaciones": "string - Notas sobre la fecha"
                }
            }
        },
        "validaciones_criticas": [
            "Fechas en formato YYYY-MM-DD correcto",
            "horario_asignado debe corresponder con día real de la fecha",
            "Suficientes fechas por día de semana para cumplir planificación"
        ],
        "generacion_mapeos": [
            "fechas_por_horario: {día_semana: [lista_fechas]}",
            "horario_por_fecha: {fecha: día_semana}",
            "Soporte multi-semestre con identificadores _S1, _S2"
        ]
    }

    # ══════════════════════════════════════════════════════════════
    # DATOS DE GRUPOS ACADÉMICOS
    # ══════════════════════════════════════════════════════════════

    GRUPOS = {
        "ubicacion_json": "configuracion.grupos.datos",
        "estructura_requerida": {
            "codigo": "string - Código del grupo (A302, EE302, etc.)",
            "nombre": "string - Nombre descriptivo",
            "curso_actual": "string - Curso académico actual",
            "coordinador": "string - Responsable del grupo",
            "departamento": "string - Departamento académico",
            "asignaturas_asociadas": "list[string] - Asignaturas que cursa el grupo"
        },
        "validaciones_criticas": [
            "Código único y no vacío",
            "asignaturas_asociadas debe coincidir con asignaturas configuradas",
            "Coherencia con grupos_matriculado de alumnos"
        ]
    }


# ====================================================================
# ALGORITMOS Y FLUJO DE PROCESAMIENTO
# ====================================================================

class FlujoProcesamiento:
    """
    Definición del orden y metodología de procesamiento del sistema

    Características:
    - Secuencia obligatoria de pasos para garantizar coherencia
    - Puntos de validación entre etapas
    - Criterios de éxito/fallo para cada fase
    - Estrategias de recuperación ante errores
    """

    # ══════════════════════════════════════════════════════════════
    # SECUENCIA PRINCIPAL DE PROCESAMIENTO
    # ══════════════════════════════════════════════════════════════

    FASES_OBLIGATORIAS = {
        "FASE_1_CARGA_VALIDACION": {
            "descripcion": "Carga y validación de configuración JSON completa",
            "entrada": "Archivo configuracion_labs.json",
            "salida": "Estructuras de datos validadas",
            "validaciones": [
                "Estructura JSON válida",
                "Secciones obligatorias presentes",
                "Tipos de datos correctos",
                "Referencias cruzadas coherentes"
            ],
            "criterio_exito": "Todos los datos cargados sin errores críticos",
            "estrategia_fallo": "Mostrar errores específicos y abortar"
        },

        "FASE_2_GENERACION_GRUPOS": {
            "descripcion": "Generación de grupos equilibrados por asignatura",
            "entrada": "Alumnos elegibles por asignatura",
            "salida": "Grupos balanceados con asignación de alumnos",
            "algoritmos": [
                "Filtrado de alumnos elegibles (no aprobados)",
                "Priorización de doble grado",
                "Generación de grupos pares cuando posible",
                "Equilibrado por diferencia máxima configurable"
            ],
            "criterio_exito": "Al menos un grupo generado por asignatura",
            "estrategia_fallo": "Continuar con asignaturas válidas, reportar fallidas"
        },

        "FASE_3_ASIGNACION_RECURSOS": {
            "descripcion": "Asignación de aulas, profesores y horarios a grupos",
            "entrada": "Grupos generados + recursos disponibles",
            "salida": "Asignaciones temporales completas",
            "algoritmos": [
                "Validación de restricciones duras",
                "Priorización de horas tempranas",
                "Distribución en fechas lejanas primero",
                "Optimización de utilización de aulas",
                "Equilibrado de carga entre profesores"
            ],
            "criterio_exito": "Al menos 50% de grupos asignados exitosamente",
            "estrategia_fallo": "Popup con detalles, opción de guardar parcial"
        },

        "FASE_4_OPTIMIZACION": {
            "descripcion": "Optimización multi-criterio de asignaciones",
            "entrada": "Asignaciones válidas iniciales",
            "salida": "Asignaciones optimizadas",
            "algoritmos": [
                "Función objetivo multi-criterio",
                "Aplicación de pesos configurables",
                "Intercambios automáticos si están habilitados",
                "Resolución de conflictos blandos"
            ],
            "criterio_exito": "Mejora en función objetivo o mantener calidad",
            "estrategia_fallo": "Usar asignaciones iniciales sin optimización"
        },

        "FASE_5_GENERACION_RESULTADOS": {
            "descripcion": "Formateo y preparación de resultados para GUI",
            "entrada": "Asignaciones finales + estadísticas",
            "salida": "Estructura de datos para visualización",
            "formatos": [
                "Horarios completos por laboratorio",
                "Estadísticas de calidad del proceso",
                "Problemas detectados y resolución",
                "Datos para ver_resultados.py"
            ],
            "criterio_exito": "Resultado válido generado",
            "estrategia_fallo": "Resultado mínimo con información de error"
        }
    }

    # ══════════════════════════════════════════════════════════════
    # CRITERIOS DE CALIDAD Y VALIDACIÓN
    # ══════════════════════════════════════════════════════════════

    METRICAS_CALIDAD = {
        "porcentaje_grupos_asignados": "grupos_con_recursos / total_grupos_generados",
        "utilizacion_promedio_aulas": "promedio(alumnos_grupo / capacidad_aula)",
        "equilibrio_distribucion": "1 - (diferencia_max_grupos / promedio_tamaño_grupos)",
        "cumplimiento_horas_tempranas": "asignaciones_tempranas / total_asignaciones",
        "balance_carga_profesores": "1 - (diferencia_max_carga / promedio_carga)",
        "conflictos_alumnos": "número_alumnos_con_solapamientos_temporales"
    }

    UMBRALES_ACEPTACION = {
        "minimo_grupos_asignados": "50%",
        "utilizacion_aula_minima": "60%",
        "utilizacion_aula_maxima": "100%",
        "diferencia_maxima_grupos": "según configuración (default: 1 alumno)",
        "conflictos_criticos_permitidos": "0 violaciones de restricciones duras"
    }


# ====================================================================
# CONFIGURACIÓN DE INTERFAZ Y EXPERIENCIA DE USUARIO
# ====================================================================

class ConfiguracionInterfaz:
    """
    Parámetros de interfaz gráfica y interacción con usuario

    Características:
    - Tema oscuro profesional por defecto
    - Precisión en terminología técnica
    - Simplicidad antes que complejidad visual
    - Transparencia en procesos y decisiones del sistema
    """

    TEMA_VISUAL = {
        "esquema_colores": "Oscuro profesional",
        "colores_principales": {
            "fondo": "#2b2b2b",
            "texto": "#ffffff",
            "acentos": "#4fc3f7",
            "exito": "#81c784",
            "advertencia": "#ffc107",
            "error": "#ff6b6b"
        },
        "tipografia": "'Segoe UI', Arial, sans-serif",
        "principios": [
            "Legibilidad máxima en texto técnico",
            "Contraste adecuado para uso prolongado",
            "Iconografía consistente y descriptiva"
        ]
    }

    INTERACCION_USUARIO = {
        "popups_decision": {
            "seleccion_grupos": "Comparar opción automática vs configurada",
            "fallos_asignacion": "Mostrar detalles específicos + opción continuar",
            "confirmacion_cambios": "Explicar impacto antes de aplicar"
        },
        "transparencia_algoritmos": [
            "Mostrar razones de recomendaciones automáticas",
            "Explicar qué parámetros influyeron en decisiones",
            "Detallar por qué grupos fallaron en asignación"
        ],
        "principio_comunicacion": "Precisión técnica + simplicidad explicativa"
    }

    LOGGING_USUARIO = {
        "niveles": ["info", "success", "warning", "error"],
        "formatos": [
            "Proceso principal: 🚀 🔄 ✅ para indicar progreso",
            "Detalles técnicos: → • - para estructura jerárquica",
            "Resultados numéricos: 📊 para estadísticas",
            "Problemas: ⚠️ ❌ para alertas y errores"
        ],
        "verbosidad": "Detalles suficientes para auditoría sin saturar"
    }


# ====================================================================
# DOCUMENTACIÓN DE IMPLEMENTACIÓN
# ====================================================================

class DocumentacionTecnica:
    """
    Referencias técnicas para desarrolladores y mantenimiento del sistema

    Información clave:
    - Stack tecnológico utilizado
    - Patrones de diseño aplicados
    - Extensibilidad y mantenimiento
    - Puntos críticos del sistema
    """

    STACK_TECNOLOGICO = {
        "lenguaje_principal": "Python 3.8+",
        "interfaz_grafica": "PyQt6",
        "procesamiento_datos": "Pandas, JSON nativo",
        "exportacion": "reportlab (PDF), openpyxl (Excel)",
        "arquitectura": "Modular orientada a objetos",
        "paradigmas": [
            "Separación de responsabilidades",
            "Validación de restricciones centralizada",
            "Configuración declarativa",
            "Logging transparente"
        ]
    }

    PUNTOS_EXTENSION = {
        "nuevas_restricciones": "Agregar en RestriccionesValidator",
        "nuevas_optimizaciones": "Extender OptimizadorConfigurable",
        "nuevos_formatos_export": "Módulo exportación en ver_resultados.py",
        "nuevos_algoritmos_grupos": "Métodos en GeneradorGrupos",
        "soporte_multi_campus": "Extensión de estructura de aulas"
    }

    MANTENIMIENTO_CRITICO = {
        "validacion_json": "Mantener coherencia entre estructura JSON y código",
        "actualizacion_calendario": "Actualizar fechas académicas por semestre",
        "revision_restricciones": "Validar restricciones con normativa académica",
        "optimizacion_rendimiento": "Monitorear tiempos con datasets grandes",
        "testing_integracion": "Probar con configuraciones reales regularmente"
    }


# ====================================================================
# RESUMEN EJECUTIVO DEL SISTEMA
# ====================================================================

"""
SISTEMA OPTIM - RESUMEN EJECUTIVO DE CONFIGURACIÓN

RESTRICCIONES DURAS (NO NEGOCIABLES):
• Profesor único por slot temporal
• Aula exclusiva por slot temporal  
• Capacidad física de aulas respetada
• Disponibilidad de profesores y aulas obligatoria
• Compatibilidad asignatura-aula requerida
• Horarios académicos autorizados únicamente
• Calendario académico vigente respetado

RESTRICCIONES BLANDAS (OPTIMIZABLES):
• Conflictos temporales de alumnos minimizados
• Equilibrio de tamaños entre grupos
• Utilización eficiente de aulas

PRIORIDADES CRÍTICAS:
• Horas tempranas prioritarias (peso 40 - CRÍTICO)
• Doble grado prioritario sobre grado simple (peso 30)
• Fechas lejanas antes que próximas
• Grupos pares preferidos

ORIGEN DE DATOS:
• Alumnos: configuracion.alumnos.datos (eligibilidad académica)
• Profesores: configuracion.profesores.datos (disponibilidad y habilitación)
• Aulas: configuracion.aulas.datos (capacidad y compatibilidad)
• Horarios: configuracion.horarios.datos (planificación autorizada)
• Calendario: configuracion.calendario.datos (fechas académicas vigentes)

PROCESAMIENTO:
1. Carga y validación integral
2. Generación de grupos equilibrados con prioridades
3. Asignación de recursos con restricciones duras
4. Optimización multi-criterio configurable
5. Generación de resultados para visualización

FILOSOFÍA DEL SISTEMA:
Precisión técnica + Simplicidad funcional + Transparencia algorítmica
"""