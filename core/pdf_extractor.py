import os
import re
import pdfplumber


class TecnoandinaPDFExtractor:
    """
    Extractor de alta precisión para reportes PDF semanales de Tecnoandina.
    Evita colisiones de columnas en tarjetas KPI y extrae tablas para gráficos.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    @staticmethod
    def _sanitizar_glifo_parentesis(texto: str) -> str:
        """
        En los PDFs de Tecnoandina, el carácter '(' en cierta fuente viene sin mapeo Unicode
        (aparece como carácter no-ASCII o cuadrado '?'). Esta función lo restaura a '('.
        """
        if not texto:
            return ""

        texto = texto.replace("«", "'").replace("»", "'").replace("“", "'").replace("”", "'")

        # Caracteres válidos en español y reportes técnicos
        permitidos = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "áéíóúÁÉÍÓÚñÑüÜ"
            " \n\r\t.,:;/%°ºª+-()'\"▼▲≥≤|•"
        )

        resultado = []
        for ch in texto:
            if ch in permitidos:
                resultado.append(ch)
            else:
                # Cualquier glifo corrupto de la fuente se convierte en '('
                resultado.append("(")

        limpio = "".join(resultado)
        # Si quedó "Grupo 9 44% datos)" sin paréntesis de apertura, agregarlo
        limpio = re.sub(r"(Grupo\s+\d+)\s+(\d+%[^()\n]*\))", r"\1 (\2", limpio)
        # Limpiar paréntesis repetidos "((" -> "(" y "( " -> "("
        limpio = re.sub(r"\(+", "(", limpio)
        limpio = re.sub(r"\(\s+", "(", limpio)
        return limpio

    def obtener_template_por_defecto(self) -> dict:
        """Template base antiguo cuando no se adjunta ningún PDF."""
        return {
            "periodo": "29-10-2026 al 05-11-2026",
            "alertas_totales": "2.263",
            "alertas_por_dia": "305",
            "variacion_alertas": "15%",
            "tendencia_alertas": "▼",
            "verbo_alertas": "bajaron",
            "disponibilidad_real": "85,3%",
            "disp_anterior": "82,9%",
            "tendencia_disp": "▲",
            "nidos_activos": "139 de 250",
            "tiempo_fuera_rango": "11,8%",
            "t_fuera_rango_ant": "6,7%",
            "tendencia_fuera_rango": "▲",
            "nidos_con_alerta_temp": "192 de 250 nidos",
            "desconexiones_totales": "54",
            "horas_desconexion": "222 h",
            "fallas_sonda": "430",
            "comparativa_alertas": {
                "categorias": ["T° Fuera Rango", "Nido Sin Datos", "Falla Sonda"],
                "actual": [168.3, 86.0, 58.1],
                "anterior": [195.0, 95.0, 65.0]
            },
            "disponibilidad_grupos": [
                ("Grupo 20", 12.9), ("Grupo 28", 48.6), ("Grupo 10", 74.0),
                ("Grupo 23", 91.6), ("Grupo 19", 94.0), ("Grupo 25", 96.6),
                ("Grupo 24", 97.6), ("Grupo 21", 98.1), ("Grupo 6", 98.1),
                ("Grupo 8", 98.6), ("Grupo 26", 98.9), ("Grupo 22", 99.6),
                ("Grupo 9", 99.9), ("Grupo 5", 100.0)
            ],
            "grupos_criticos_texto": "Grupo 20 (12,9%), Grupo 28 (48,6%), Grupo 10 (74,0%), Grupo 23 (91,6%), Grupo 19 (94,0%), Grupo 25 (96,6%).",
            "brecha_alertas_texto": "49 alertas 'sin datos' quedaron abiertas en plataforma pese a reconexión (Disponibilidad por alertas: 64,6% vs Real InfluxDB: 85,3%).",
            "nidos_cero_texto": "7 nidos reportaron 0 lecturas válidas (6 corresponden al Nido 2 de cada sala del Grupo 28 sin sonda conectada).",
            "prioridad_intervencion_texto": "Revisar conectividad en Grupo 20 (12,9%) y Grupo 28 (48,6%).",
            "concentracion_desconexiones_texto": "Grupo 20 lidera con 35 caídas (148,2 h), seguido de Grupo 10 (35,0 h) y Grupo 26 (12,2 h).",
            "caidas_simultaneas_texto": "7 eventos con 3 o más grupos caídos en simultáneo (causa atribuible a red/plataforma central y no a terreno).",
            "horario_critico_texto": "El 66% de los cortes >30 min inicia en horario laboral (08:00 a 17:59 hrs, peak a las 10:00 hrs).",
            "peores_nidos_texto": "Grupo 21 PAB13-MAT2-N4 (81%), Grupo 24-PAB18-MAT15-N3 (79%), Grupo 23-PAB20-MAT21-N3 (78%).",
            "top_salas_alertas_texto": (
                "  - Grupo 22 | PAB13 Mat 2 (88 alertas: 56 falla sonda)\n"
                "  - Grupo 8  | PAB01 Mat 5 (69 alertas: 59 T° fuera rango)\n"
                "  - Grupo 25 | PAB16 Mat 8 (57 alertas: 142 hrs fuera rango)"
            )
        }

    def extraer_datos(self) -> dict:
        datos = self.obtener_template_por_defecto()
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            return datos

        paginas_texto = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                paginas_texto.append(self._sanitizar_glifo_parentesis(t))

        texto_completo = "\n".join(paginas_texto)
        if not texto_completo.strip():
            return datos

        # =========================================================================
        # 1. EXTRACCIÓN EXACTA DE LAS 6 TARJETAS KPI (Desde "Resumen del periodo")
        # Evita que las columnas de las cajas superiores mezclen "399" con "de 250"
        # =========================================================================
        m_per = re.search(r"Periodo del\s+(\d{2}-\d{2}-\d{4}\s+al\s+\d{2}-\d{2}-\d{4})", texto_completo, re.IGNORECASE)
        if m_per:
            datos["periodo"] = m_per.group(1).strip()

        # KPI 1: Alertas Totales, por día y variación
        # "Llegaron a QA 1.945 alertas (251 por día): 634 de Tº fuera de rango, 912 de nido sin datos y 399 de posible falla de sonda; en promedio diario, bajaron un 20%"
        m_res1 = re.search(r"Llegaron a QA\s+([\d\.]+)\s+alertas\s*\(?(\d+)\s+por d[ií]a\)?", texto_completo, re.IGNORECASE)
        if m_res1:
            datos["alertas_totales"] = m_res1.group(1)
            datos["alertas_por_dia"] = m_res1.group(2)

        m_var = re.search(r"(bajaron|subieron|aumentaron|disminuyeron)\s+un\s+(\d+%)", texto_completo, re.IGNORECASE)
        if m_var:
            es_baja = "bajar" in m_var.group(1).lower() or "disminu" in m_var.group(1).lower()
            datos["tendencia_alertas"] = "▼" if es_baja else "▲"
            datos["verbo_alertas"] = "bajaron" if es_baja else "subieron"
            datos["variacion_alertas"] = m_var.group(2)

       # KPI 2 y KPI 3: Disponibilidad Real (78,6%) y Nidos Activos (93 de 250)
        # "Disponibilidad real de datos (InfluxDB): 78,6% de las lecturas de nido fueron válidas... 93 de 250 nidos (37%) estuvieron activos"
        m_disp_real = re.search(r"Disponibilidad real de datos[^:]*:\s*([\d,]+%)", texto_completo, re.IGNORECASE)
        if m_disp_real:
            datos["disponibilidad_real"] = m_disp_real.group(1)
        else:
            # Respaldo en página 2: "De 186.000 lecturas esperadas de nido: 78,6% válidas"
            m_disp_p2 = re.search(r"lecturas esperadas de nido:\s*([\d,]+%)\s*v[áa]lidas", texto_completo, re.IGNORECASE)
            if m_disp_p2:
                datos["disponibilidad_real"] = m_disp_p2.group(1)

        # KPI 3: Nidos Activos (93 de 250)
        # 1. Buscar dentro de "Resumen del periodo" ("93 de 250 nidos") donde nunca se cruza con las cajas superiores
        m_bloque_res = re.search(r"Resumen del periodo(.+?)Alertas generadas", texto_completo, re.IGNORECASE | re.DOTALL)
        texto_resumen = m_bloque_res.group(1) if m_bloque_res else texto_completo

        m_nidos_act = re.search(r"(\d+)\s+de\s+250\s+nidos", texto_resumen, re.IGNORECASE)
        if not m_nidos_act:
            # 2. Respaldo directo en la tarjeta superior ("93 de 250" seguido de "reportó" o "intermitentes")
            m_nidos_act = re.search(r"\b(\d{1,3})\s+de\s+250\b(?=\s*\n?\s*\d+%\s*report)", texto_completo, re.IGNORECASE)
        if not m_nidos_act:
            # 3. Segundo respaldo general en el bloque de resumen
            m_nidos_act = re.search(r"tiempo\.\s*(\d+)\s+de\s+250", texto_completo, re.IGNORECASE)

        if m_nidos_act:
            datos["nidos_activos"] = f"{m_nidos_act.group(1)} de 250"

        # Buscar Nidos Activos estrictamente en la frase "XX de 250 nidos (YY%) estuvieron activos"
        m_nidos_act = re.search(r"(\d+\s+de\s+250)\s+nidos\s*\(?\d+%\)?\s+estuvieron\s+activos", texto_completo, re.IGNORECASE)
        if m_nidos_act:
            datos["nidos_activos"] = " ".join(m_nidos_act.group(1).split())

        # KPI 4: Tiempo fuera de rango (11,6%)
        m_tfr = re.search(r"Los nidos estuvieron fuera de rango el\s*([\d,]+%)\s*del tiempo", texto_completo, re.IGNORECASE)
        if m_tfr:
            datos["tiempo_fuera_rango"] = m_tfr.group(1)

        # Periodos anteriores de las tarjetas KPI (En Página 1 aparecen dos veces "Periodo anterior: XX,X%":
        # el 1° es Disponibilidad [85,2%] y el 2° es Tiempo fuera de rango [14,1%])
        periodos_ant_p1 = re.findall(r"Periodo anterior:\s*([\d,]+%)", paginas_texto[0] if paginas_texto else texto_completo, re.IGNORECASE)
        if len(periodos_ant_p1) >= 1:
            datos["disp_anterior"] = periodos_ant_p1[0]
            try:
                act_d = float(datos["disponibilidad_real"].replace("%", "").replace(",", "."))
                ant_d = float(datos["disp_anterior"].replace("%", "").replace(",", "."))
                datos["tendencia_disp"] = "▲" if act_d >= ant_d else "▼"
            except Exception:
                pass
        if len(periodos_ant_p1) >= 2:
            datos["t_fuera_rango_ant"] = periodos_ant_p1[1]

        # Respaldo de Periodo anterior de Tiempo fuera de rango en Página 4:
        # "Los nidos estuvieron fuera de rango el 11,6% del tiempo y 176 de 250 nidos (70%) tuvieron al menos una alerta de Tº. Periodo anterior: 14,1%"
        m_tfr_p4 = re.search(
            r"fuera de rango el\s*[\d,]+%\s*del tiempo y\s*(\d+\s*de\s*\d+\s*nidos\s*\(?\d+%\)?)\s*tuvieron[^\n]*?Periodo anterior:\s*([\d,]+%)",
            texto_completo, re.IGNORECASE
        )
        if m_tfr_p4:
            datos["nidos_con_alerta_temp"] = m_tfr_p4.group(1)
            datos["t_fuera_rango_ant"] = m_tfr_p4.group(2)

        try:
            act_val = float(datos["tiempo_fuera_rango"].replace("%", "").replace(",", "."))
            ant_val = float(datos["t_fuera_rango_ant"].replace("%", "").replace(",", "."))
            datos["tendencia_fuera_rango"] = "▼" if act_val < ant_val else "▲"
        except Exception:
            pass

        # KPI 5: Desconexiones de grupo (60 y 364 h)
        m_desc = re.search(r"Se registraron\s+(\d+)\s+desconexiones de grupo completo\s*\(?(\d+\s*h)\)?", texto_completo, re.IGNORECASE)
        if m_desc:
            datos["desconexiones_totales"] = m_desc.group(1)
            datos["horas_desconexion"] = m_desc.group(2)

        # KPI 6: Fallas de Sonda (399)
        m_sonda = re.search(r"y\s+(\d+)\s+de posible falla de sonda", texto_completo, re.IGNORECASE)
        if m_sonda:
            datos["fallas_sonda"] = m_sonda.group(1)

        # =========================================================================
        # 2. EXTRACCIÓN DE DATOS PARA LOS 2 GRÁFICOS (SLIDE 2 Y SLIDE 3)
        # =========================================================================
        comp_extraida = self._extraer_comparativa_alertas_infalible(texto_completo)
        if comp_extraida:
            datos["comparativa_alertas"] = comp_extraida

        grupos_extraidos = self._extraer_disponibilidad_grupos_infalible(texto_completo)
        if grupos_extraidos:
            datos["disponibilidad_grupos"] = grupos_extraidos

        # =========================================================================
        # 3. TEXTOS DINÁMICOS DE LÁMINAS 3 Y 4
        # =========================================================================
        m_crit = re.search(r"Grupos cr[íi]ticos:\s*(.+?)(?:\.\s*En atenci[óo]n:|\nLos nidos)", texto_completo, re.IGNORECASE | re.DOTALL)
        if m_crit:
            limpio = " ".join(m_crit.group(1).split())
            datos["grupos_criticos_texto"] = limpio + "."

        m_brecha = re.search(
            r"(\d+)\s+alertas[^\n]*?sin datos[^\n]*?quedaron abiertas.*?([\d,]+%).*?([\d,]+%)",
            texto_completo, re.IGNORECASE | re.DOTALL
        )
        if m_brecha:
            datos["brecha_alertas_texto"] = (
                f"{m_brecha.group(1)} alertas 'sin datos' quedaron abiertas en plataforma pese a reconexión "
                f"(Disponibilidad por alertas: {m_brecha.group(2)} vs Real InfluxDB: {m_brecha.group(3)})."
            )

        m_cero = re.search(r"(\d+\s+nidos\s+no\s+tuvieron\s+ninguna\s+lectura\s+v[áa]lida;[^\n]+)", texto_completo, re.IGNORECASE)
        if m_cero:
            datos["nidos_cero_texto"] = m_cero.group(1).strip()

        if datos["disponibilidad_grupos"]:
            peores_2 = sorted(datos["disponibilidad_grupos"], key=lambda x: x[1])[:2]
            if len(peores_2) >= 2:
                datos["prioridad_intervencion_texto"] = (
                    f"Revisar conectividad en {peores_2[0][0]} ({peores_2[0][1]:.1f}%) y {peores_2[1][0]} ({peores_2[1][1]:.1f}%)."
                )

        m_conc = re.search(r"\d+\s+desconexiones de grupo completo:\s*([^\n]+)", texto_completo, re.IGNORECASE)
        if m_conc:
            partes = [p.strip() for p in m_conc.group(1).split(",") if p.strip()]
            top_3_desc = ", ".join(partes[:3])
            datos["concentracion_desconexiones_texto"] = f"Mayor concentración en: {top_3_desc}."

        m_simul = re.search(r"Hubo\s+(\d+)\s+periodos con 3 o m[áa]s grupos desconectados a la vez", texto_completo, re.IGNORECASE)
        if m_simul:
            datos["caidas_simultaneas_texto"] = (
                f"{m_simul.group(1)} eventos con 3 o más grupos caídos en simultáneo (causa atribuible a red/plataforma central y no a terreno)."
            )

        m_hor = re.search(
            r"El\s+(\d+%)\s+de los cortes de 30 min o m[áa]s comienza entre\s+([\d:]+)\s+y\s+([\d:]+)\s*\(?m[áa]ximo a las\s+([\d:]+)\)?",
            texto_completo, re.IGNORECASE
        )
        if m_hor:
            datos["horario_critico_texto"] = (
                f"El {m_hor.group(1)} de los cortes >30 min inicia en horario laboral ({m_hor.group(2)} a {m_hor.group(3)} hrs, peak a las {m_hor.group(4)} hrs)."
            )

        m_peores_nidos = re.search(r"Nidos con m[áa]s tiempo fuera de rango:\s*(.+?)\.\n", texto_completo, re.IGNORECASE | re.DOTALL)
        if m_peores_nidos:
            datos["peores_nidos_texto"] = " ".join(m_peores_nidos.group(1).split()) + "."

        top_salas = self._extraer_top_salas_alertas(texto_completo)
        if top_salas:
            datos["top_salas_alertas_texto"] = top_salas

        return datos

    def _extraer_comparativa_alertas_infalible(self, texto: str) -> dict:
        """
        Extrae los promedios diarios (Actual vs Anterior) de la tabla '1. Alertas generadas'.
        Funciona incluso si pdfplumber une o separa saltos de línea entre celdas.
        """
        categorias = ["T° Fuera Rango", "Nido Sin Datos", "Falla Sonda"]

        # Cortar únicamente la zona de la tabla 1 (entre "Por día, periodo anterior" y "Estatus por grupo")
        m_zona = re.search(r"periodo anterior(.+?)(?:Estatus por grupo|Alertas por d[ií]a)", texto, re.IGNORECASE | re.DOTALL)
        zona = m_zona.group(1) if m_zona else texto

        # Buscar cada fila Total (o D2 en sonda) permitiendo cualquier carácter o salto corto entre columnas
        m_rango = re.search(r"fuera de rango\s+Total\s+[\d\.]+\s+(\d+,\d+)\s+(\d+,\d+)", zona, re.IGNORECASE)
        m_datos = re.search(r"Nido sin datos\s+Total\s+[\d\.]+\s+(\d+,\d+)\s+(\d+,\d+)", zona, re.IGNORECASE)
        m_sonda = re.search(r"falla de sonda\s+(?:Total|D2)\s+[\d\.]+\s+(\d+,\d+)\s+(\d+,\d+)", zona, re.IGNORECASE)

        if m_rango and m_datos and m_sonda:
            return {
                "categorias": categorias,
                "actual": [
                    float(m_rango.group(1).replace(",", ".")),
                    float(m_datos.group(1).replace(",", ".")),
                    float(m_sonda.group(1).replace(",", "."))
                ],
                "anterior": [
                    float(m_rango.group(2).replace(",", ".")),
                    float(m_datos.group(2).replace(",", ".")),
                    float(m_sonda.group(2).replace(",", "."))
                ]
            }
        return None

    def _extraer_disponibilidad_grupos_infalible(self, texto: str) -> list:
        """
        Extrae la disponibilidad de los 14 grupos desde la tabla '2. Estatus por grupo'
        usando búsqueda global (no línea por línea) y sumando los datos de la sección 6.
        """
        encontrados = {}

        # Método 1: Búsqueda global en la tabla "Estatus por grupo"
        # Patrón: "Grupo XX" + (Crítico|Atención|Normal) + Nidos (entero) + Disponibilidad (XX,X%)
        m_estatus = re.search(r"Estatus por grupo(.+?)(?:Disponibilidad de datos|Salas con menor|$)", texto, re.IGNORECASE | re.DOTALL)
        zona_estatus = m_estatus.group(1) if m_estatus else texto

        matches_t2 = re.findall(
            r"(Grupo\s+\d+)\s+(?:Cr[íi]tico|Atenci[óo]n|Normal)\s+\d+\s+(\d+,\d+)%",
            zona_estatus, re.IGNORECASE
        )
        for grp, pct in matches_t2:
            nombre = " ".join(grp.split()).title()
            encontrados[nombre] = float(pct.replace(",", "."))

        # Método 2: Si en la sección 6 (Página 5) hay grupos adicionales (incluso apilados como "Grupo 26\nGrupo 5\n94,7%\n97,4%")
        if len(encontrados) < 14:
            m_sec6 = re.search(r"Disponibilidad InfluxDB(.+?)(?:C[óo]mo se calcula|$)", texto, re.IGNORECASE | re.DOTALL)
            if m_sec6:
                zona_6 = m_sec6.group(1)
                grupos_sec6 = [f"Grupo {n}" for n in re.findall(r"Grupo\s+(\d+)", zona_6, re.IGNORECASE)]
                pcts_sec6 = [float(p.replace(",", ".")) for p in re.findall(r"(\d+,\d+)%", zona_6)]
                if len(grupos_sec6) == len(pcts_sec6) and len(grupos_sec6) >= 10:
                    for g_nom, p_val in zip(grupos_sec6, pcts_sec6):
                        if g_nom not in encontrados:
                            encontrados[g_nom] = p_val

        if len(encontrados) >= 5:
            return sorted(encontrados.items(), key=lambda x: x[1])

        return None

    def _extraer_top_salas_alertas(self, texto: str) -> str:
        m_seccion = re.search(
            r"Salas con m[áa]s alertas[^\n]*(.+?)Nidos con m[áa]s tiempo fuera de rango",
            texto, re.IGNORECASE | re.DOTALL
        )
        if not m_seccion:
            return ""

        bloque = m_seccion.group(1)
        filas = re.findall(
            r"(Grupo\s+\d+)\s+(PAB\d+\s+Maternidad\s+\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            bloque, re.IGNORECASE
        )
        if not filas:
            return ""

        lineas_out = []
        for grp, sala, t_rango, s_datos, f_sonda, total, hrs in filas[:3]:
            sala_corta = re.sub(r"Maternidad", "Mat", sala, flags=re.IGNORECASE)
            detalles = []
            if int(s_datos) > 0:
                detalles.append(f"{s_datos} sin datos")
            if int(f_sonda) > 0:
                detalles.append(f"{f_sonda} falla sonda")
            if int(t_rango) > 0:
                detalles.append(f"{t_rango} T° fuera rango")
            det_str = ", ".join(detalles[:2])
            lineas_out.append(f"  - {grp.title()} | {sala_corta} ({total} alertas: {det_str})")

        return "\n".join(lineas_out)