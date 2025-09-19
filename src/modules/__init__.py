"""
OPTIM - Módulos del Sistema
Paquete que contiene todos los módulos especializados

Estructura:
├── interfaces/          # Ventanas de configuración (PyQt6)
├── utils/              # Utilidades generales
├── scheduling/         # Algoritmos de scheduling
└── data_sources/       # Gestión y validación de datos

Cada módulo tiene su responsabilidad específica y puede ser
importado independientemente.
"""

# ========= IMPORTS DE INTERFACES =========
try:
    from .interfaces import ConfigurarCalendario, ConfigurarHorarios, VerResultados

    INTERFACES_OK = True
except ImportError as e:
    print(f"⚠️ Error cargando interfaces: {e}")
    INTERFACES_OK = False

# ========= IMPORTS DE OTROS MÓDULOS (cuando estén implementados) =========
# try:
#     from .utils import DataValidator, ExportManager
#     from .scheduling import ScheduleGenerator, ConflictResolver
#     from .data_sources import AlumnosManager, LaboratoriosManager
#     MODULES_OK = True
# except ImportError:
#     MODULES_OK = False

# ========= EXPORTACIONES =========
if INTERFACES_OK:
    __all__ = [
        # Interfaces
        'ConfigurarCalendario',
        'ConfigurarHorarios',
        'VerResultados',

        # Funciones utilitarias
        'get_available_modules',
        'check_modules_status'
    ]
else:
    __all__ = [
        'get_available_modules',
        'check_modules_status'
    ]


# ========= FUNCIONES UTILITARIAS =========
def get_available_modules():
    """Obtener lista de módulos disponibles"""
    modules = {
        'interfaces': INTERFACES_OK,
        'utils': False,  # Placeholder
        'scheduling': False,  # Placeholder
        'data_sources': False  # Placeholder
    }
    return modules


def check_modules_status():
    """Verificar estado de todos los módulos"""
    modules = get_available_modules()
    available = [name for name, status in modules.items() if status]
    missing = [name for name, status in modules.items() if not status]

    return {
        'available': available,
        'missing': missing,
        'total': len(modules),
        'loaded': len(available)
    }


# ========= INFORMACIÓN DEL MÓDULO =========
MODULE_INFO = {
    'name': 'modules',
    'description': 'Módulos especializados del sistema OPTIM',
    'interfaces_loaded': INTERFACES_OK,
    'submodules': ['interfaces', 'utils', 'scheduling', 'data_sources']
}


def get_module_info():
    """Obtener información del paquete modules"""
    return MODULE_INFO.copy()


# ========= INICIALIZACIÓN =========
print(f"📁 Módulos OPTIM inicializados")
_status = check_modules_status()
print(f"📊 Estado: {_status['loaded']}/{_status['total']} módulos cargados")
if _status['available']:
    print(f"✅ Disponibles: {', '.join(_status['available'])}")
if _status['missing']:
    print(f"⚠️ Pendientes: {', '.join(_status['missing'])}")