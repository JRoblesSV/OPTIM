"""
Interfaces gráficas para OPTIM - Sistema de Programación de Laboratorios
"""

try:
    from .configurar_calendario import ConfigurarCalendario
    from .configurar_horarios import ConfigurarHorarios
    from .ver_resultados import VerResultados

    # Exportaciones
    __all__ = ['ConfigurarCalendario', 'ConfigurarHorarios', 'VerResultados']

except ImportError as e:
    print(f"⚠️ Error importando interfaces: {e}")
    # Las clases dummy las maneja gui_labs.py, no aquí
    raise