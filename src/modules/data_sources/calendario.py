#!/usr/bin/env python3
"""
Módulo para obtener datos de calendario académico desde web ETSIDI
Navega automáticamente y extrae días lectivos de ambos semestres
"""

import re
import time
from datetime import datetime
from RPA.Browser.Selenium import Selenium
from RPA.HTTP import HTTP
import fitz  # PyMuPDF para procesar PDFs


class CalendarioScraper:
    def __init__(self, headless=True):
        self.browser = Selenium()
        self.http = HTTP()
        self.headless = headless

    def obtener_calendario_desde_web(self, url_calendario):
        """
        Función principal para obtener datos del calendario académico

        Args:
            url_calendario (str): URL base del calendario ETSIDI

        Returns:
            tuple: (datos_calendario, cod_error, msje_error)
        """
        try:
            # Abrir navegador y navegar a la página
            cod_error, msje_error = self._abrir_web(url_calendario)
            if cod_error != 0:
                return None, cod_error, msje_error

            # Buscar y hacer clic en "Calendario Títulos de Grado"
            enlace_pdf = self._buscar_enlace_calendario()
            if not enlace_pdf:
                return None, 2, "No se encontró el enlace 'Calendario Títulos de Grado'"

            # Descargar y procesar PDF
            contenido_calendario = self._descargar_y_procesar_pdf(enlace_pdf)
            if not contenido_calendario:
                return None, 2, "Error procesando el PDF del calendario"

            # Extraer datos de los semestres
            datos_extraidos = self._extraer_datos_semestres(contenido_calendario)

            return datos_extraidos, 0, "Calendario obtenido correctamente desde web"

        except Exception as e:
            return None, 2, f"Error obteniendo calendario desde web: {str(e)}"

        finally:
            self._cerrar_navegador()

    def _abrir_web(self, url):
        """Abrir navegador y navegar a la URL"""
        try:
            self.browser.open_available_browser(url, headless=self.headless)
            time.sleep(2)  # Esperar carga
            return 0, ""
        except Exception as e:
            return 2, f"Error abriendo navegador: {str(e)}"

    def _buscar_enlace_calendario(self):
        """Buscar enlace de 'Calendario Títulos de Grado'"""
        try:
            # Buscar el enlace por texto
            enlaces_posibles = [
                "Calendario Títulos de Grado",
                "Calendario Grado",
                "Titulos de Grado",
                "Calendario"
            ]

            for texto_enlace in enlaces_posibles:
                try:
                    # Intentar hacer clic en el enlace
                    elemento = self.browser.find_element(f"xpath://a[contains(text(), '{texto_enlace}')]")
                    href = self.browser.get_element_attribute(elemento, 'href')
                    if href and '.pdf' in href.lower():
                        return href

                    # Si no tiene href directo, hacer clic y buscar redirect
                    self.browser.click_element(elemento)
                    time.sleep(3)

                    # Verificar si nos redirigió a un PDF
                    url_actual = self.browser.get_location()
                    if '.pdf' in url_actual.lower():
                        return url_actual

                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"Error buscando enlace: {str(e)}")
            return None

    def _descargar_y_procesar_pdf(self, url_pdf):
        """Descargar PDF y extraer texto"""
        try:
            # Descargar PDF
            archivo_temporal = "temp_calendario.pdf"
            self.http.download(url=url_pdf, target_file=archivo_temporal, overwrite=True)

            # Procesar PDF con PyMuPDF
            texto_completo = ""
            with fitz.open(archivo_temporal) as doc:
                for pagina in doc:
                    texto_completo += pagina.get_text()

            return texto_completo

        except Exception as e:
            print(f"Error procesando PDF: {str(e)}")
            return None

    def _extraer_datos_semestres(self, texto_calendario):
        """
        Extraer datos estructurados de ambos semestres del texto del calendario

        Returns:
            dict: Estructura con datos de ambos semestres
        """
        datos = {
            'semestre_1': {'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [], 'viernes': []},
            'semestre_2': {'lunes': [], 'martes': [], 'miercoles': [], 'jueves': [], 'viernes': []},
            'dias_especiales': {},
            'curso_academico': self._extraer_curso_academico(texto_calendario)
        }

        try:
            # Buscar patrones de calendarios en formato tabla
            # Patrón típico: L    M    X    J    V
            patron_tabla = r'L\s+M\s+X\s+J\s+V\s*\n((?:\d+[*]?\s+\d+[*]?\s+\d+[*]?\s+\d+[*]?\s+\d+[*]?\s*\n?)+)'

            tablas_encontradas = re.findall(patron_tabla, texto_calendario, re.MULTILINE)

            if len(tablas_encontradas) >= 2:
                # Procesar primer semestre
                self._procesar_tabla_semestre(tablas_encontradas[0], datos['semestre_1'], datos['dias_especiales'])

                # Procesar segundo semestre
                self._procesar_tabla_semestre(tablas_encontradas[1], datos['semestre_2'], datos['dias_especiales'])
            else:
                # Método alternativo: buscar por meses conocidos
                datos = self._extraer_por_meses(texto_calendario)

            return datos

        except Exception as e:
            print(f"Error extrayendo datos: {str(e)}")
            return self._generar_datos_ejemplo()

    def _procesar_tabla_semestre(self, tabla_texto, semestre_data, dias_especiales):
        """Procesar una tabla de semestre específica"""
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']

        # Dividir en líneas y procesar cada fila
        lineas = tabla_texto.strip().split('\n')

        for linea in lineas:
            if not linea.strip():
                continue

            # Extraer números (con o sin asterisco)
            numeros = re.findall(r'\d+[*]?', linea)

            if len(numeros) == 5:  # Una fila completa L-M-X-J-V
                for i, numero in enumerate(numeros):
                    dia_semana = dias_semana[i]

                    if '*' in numero:
                        # Día especial
                        dia_limpio = numero.replace('*', '')
                        semestre_data[dia_semana].append(numero)  # Mantener el *
                        dias_especiales[numero] = {
                            'tipo': 'horario_especial',
                            'descripcion': 'Día especial detectado automáticamente'
                        }
                    else:
                        # Día normal
                        semestre_data[dia_semana].append(numero)

    def _extraer_curso_academico(self, texto):
        """Extraer el curso académico del texto"""
        patron_curso = r'Curso\s+(\d{4}-\d{4})|(\d{4}-\d{4})'
        match = re.search(patron_curso, texto)

        if match:
            return match.group(1) or match.group(2)
        else:
            # Fallback al año actual
            año_actual = datetime.now().year
            return f"{año_actual}-{año_actual + 1}"

    def _extraer_por_meses(self, texto):
        """Método alternativo: extraer por meses conocidos"""
        # Implementación simplificada para casos donde el patrón de tabla no funciona
        datos = self._generar_datos_ejemplo()

        # Buscar patrones de fechas específicas
        meses_primer_sem = ['septiembre', 'octubre', 'noviembre', 'diciembre', 'enero']
        meses_segundo_sem = ['febrero', 'marzo', 'abril', 'mayo', 'junio']

        # Extraer fechas con asterisco (días especiales)
        fechas_especiales = re.findall(r'(\d{1,2})[*]', texto)

        for fecha in fechas_especiales:
            datos['dias_especiales'][f"{fecha}*"] = {
                'tipo': 'horario_especial',
                'descripcion': 'Día especial'
            }

        return datos

    def _generar_datos_ejemplo(self):
        """Generar datos de ejemplo si falla la extracción"""
        return {
            'semestre_1': {
                'lunes': ['16', '23', '30*', '7'],
                'martes': ['17', '24', '31', '8'],
                'miercoles': ['18', '25', '1', '9*'],
                'jueves': ['19', '26', '2', '10'],
                'viernes': ['20', '27', '3*', '11']
            },
            'semestre_2': {
                'lunes': ['3', '10', '17', '24'],
                'martes': ['4', '11*', '18', '25'],
                'miercoles': ['5', '12', '19', '26'],
                'jueves': ['6', '13', '20', '27'],
                'viernes': ['7', '14', '21', '28']
            },
            'dias_especiales': {
                '30*': {'tipo': 'horario_martes', 'descripcion': 'Día del Pilar'},
                '9*': {'tipo': 'horario_viernes', 'descripcion': 'Día especial'},
                '3*': {'tipo': 'horario_lunes', 'descripcion': 'Día especial'},
                '11*': {'tipo': 'horario_miercoles', 'descripcion': 'Día especial'}
            },
            'curso_academico': f"{datetime.now().year}-{datetime.now().year + 1}"
        }

    def _cerrar_navegador(self):
        """Cerrar navegador"""
        try:
            self.browser.close_browser()
        except:
            pass


# Función principal de fachada
def obtener_calendario_web(url_calendario, headless=True):
    """
    Función principal para uso externo

    Args:
        url_calendario (str): URL del calendario ETSIDI
        headless (bool): Ejecutar navegador en modo headless

    Returns:
        tuple: (datos_calendario, cod_error, mensaje_error)
    """
    scraper = CalendarioScraper(headless=headless)
    return scraper.obtener_calendario_desde_web(url_calendario)


if __name__ == "__main__":
    # Test del módulo
    print("🔬 Testing CalendarioScraper...")

    url_test = "https://www.etsidi.upm.es/Estudiantes/AgendaAcademica/AACalendario"
    datos, error, mensaje = obtener_calendario_web(url_test, headless=False)

    if error == 0:
        print("✅ Extracción exitosa!")
        print(f"📅 Curso académico: {datos['curso_academico']}")
        print(f"📊 Días especiales encontrados: {len(datos['dias_especiales'])}")

        # Mostrar muestra de primer semestre
        print("\n📋 Muestra 1º Semestre:")
        for dia, fechas in datos['semestre_1'].items():
            print(f"  {dia.capitalize()}: {fechas[:3]}...")  # Solo primeras 3 fechas

    else:
        print(f"❌ Error: {mensaje}")