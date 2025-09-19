"""
OPTIM - Sistema de Programación de Laboratorios
Paquete principal del proyecto

Estructura:
├── gui_labs.py              # Interfaz principal
├── modules/                 # Módulos del sistema
│   ├── interfaces/          # Ventanas de configuración
│   ├── utils/              # Utilidades
│   ├── scheduling/         # Lógica de scheduling
│   └── data_sources/       # Gestión de datos

Autor: Javier Robles Molina - SoftVier
Universidad: ETSIDI (UPM)
"""

__version__ = "1.0.0"
__author__ = "Javier Robles Molina"
__description__ = "OPTIM - Sistema de Programación Automática de Laboratorios"

# ========= IMPORTS PRINCIPALES =========
try:
    # Importar interfaces desde modules.interfaces
    from .modules.interfaces import ConfigurarCalendario, ConfigurarHorarios, VerResultados

    INTERFACES_DISPONIBLES = True

    # Re-exportar para fácil acceso
    __all__ = [
        'ConfigurarCalendario',
        'ConfigurarHorarios',
        'VerResultados'
    ]

except ImportError as e:
    print(f"⚠️ Interfaces no disponibles: {e}")
    INTERFACES_DISPONIBLES = False
    __all__ = []

# ========= METADATA DEL PROYECTO =========
PROJECT_INFO = {
    'name': 'OPTIM',
    'full_name': 'Optimized Process for Task Integration and Management',
    'description': 'Sistema de Programación Automática de Laboratorios',
    'university': 'ETSIDI - Universidad Politécnica de Madrid',
    'stack': 'Python + PyQt6 + Pandas + NumPy + OpenPyXL',
    'version': __version__,
    'interfaces_available': INTERFACES_DISPONIBLES
}

# ========= CONFIGURACIÓN GLOBAL =========
DEFAULT_CONFIG = {
    'theme': 'dark',
    'max_capacity_default': 24,
    'min_capacity': 10,
    'max_capacity': 50,
    'default_semester': 1,
    'export_formats': ['xlsx', 'pdf', 'csv'],
    'time_slots': {
        'start': '08:00',
        'end': '20:00',
        'duration': '02:00',
        'lunch_start': '14:00',
        'lunch_end': '15:00'
    }
}


# ========= FUNCIONES UTILITARIAS =========
def get_project_info():
    """Obtener información completa del proyecto"""
    return PROJECT_INFO.copy()


def check_dependencies():
    """Verificar dependencias críticas del sistema"""
    dependencies = {
        'PyQt6': False,
        'pandas': False,
        'numpy': False,
        'openpyxl': False
    }

    missing = []

    for dep_name, _ in dependencies.items():
        try:
            if dep_name == 'PyQt6':
                import PyQt6
            elif dep_name == 'openpyxl':
                import openpyxl
            else:
                __import__(dep_name)
            dependencies[dep_name] = True
        except ImportError:
            dependencies[dep_name] = False
            missing.append(dep_name)

    return {
        'status': dependencies,
        'missing': missing,
        'all_ok': len(missing) == 0
    }


def get_config():
    """Obtener configuración por defecto"""
    return DEFAULT_CONFIG.copy()


# ========= INICIALIZACIÓN =========
print(f"📦 OPTIM v{__version__} - Paquete principal inicializado")
print(f"🎯 Interfaces: {'✅ Disponibles' if INTERFACES_DISPONIBLES else '❌ No disponibles'}")

# Verificar dependencias al importar
_deps = check_dependencies()
if not _deps['all_ok']:
    print(f"⚠️ Dependencias faltantes: {', '.join(_deps['missing'])}")
else:
    print("✅ Todas las dependencias disponibles")