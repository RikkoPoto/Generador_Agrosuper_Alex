import os
import re
import pdfplumber


class TecnoandinaPDFExtractor:
    """
    Extrae dinámicamente todos los KPIs, tablas y textos de diagnóstico desde el
    PDF semanal de Tecnoandina. Si no se adjunta PDF, conserva el template antiguo.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def obtener_template_por_defecto(self) -> dict:
        """Template base antiguo cuando no se carga ningún PDF."""
        return {
            "periodo": "29-10-2026 al 05-11-2026",
            "alertas_totales": "2.263",
            "alertas_por_dia": "305",
            "variacion_alertas": "15%",
            "tendencia_alertas": "▼",
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
            "comparativa_alertas": self._extraer_comparativa_alertas(""),
            "disponibilidad_grupos": self._extraer_disponibilidad_grupos(""),
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

        texto_completo = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto_completo += t + "\n"

        if not texto_completo.strip():
            return datos

        # 1. Periodo
        m_per = re.search(r"Periodo del\s+(\d{2}-\d{2}-\d{4}\s+al\s+\d{2}-\d{2}-\d{4})", texto_completo, re.IGNORECASE)
        if m_per:
            datos["periodo"] = m_per.group(1).strip()

        # 2. Alertas Totales, Promedio por día y Variación
        m_res_al = re.search(r"Llegaron a QA\s+([\d\.]+)\s+alertas\s*\((\d+)\s+por d[ií]a\)", texto_completo, re.IGNORECASE)
        if m_res_al:
            datos["alertas_totales"] = m_res_al.group(1)
            datos["alertas_por_dia"] = m_res_al.group(2)
        else:
            m_al = re.search(r"Alertas generadas.*?\n([\d\.]+)", texto_completo, re.DOTALL)
            if m_al:
                datos["alertas_totales"] = m_al.group(1)

        m_var = re.search(r"([▼▲])\s*(\d+%)\s*vs\s*periodo\s*anterior", texto_completo, re.IGNORECASE)
        if m_var:
            datos["tendencia_alertas"] = m_var.group(1)
            datos["variacion_alertas"] = m_var.group(2)
        else:
            m_var2 = re.search(r"(bajaron|subieron)\s+un\s+(\d+%)\s+respecto\s+del\s+periodo", texto_completo, re.IGNORECASE)
            if m_var2:
                datos["tendencia_alertas"] = "▼" if "bajar" in m_var2.group(1).lower() else "▲"
                datos["variacion_alertas"] = m_var2.group(2)

        # 3. Disponibilidad Real (InfluxDB) y Periodo Anterior
        m_disp = re.search(r"Disponibilidad real de datos\s*\(InfluxDB\):\s*([\d,]+%)", texto_completo, re.IGNORECASE)
        if m_disp:
            datos["disponibilidad_real"] = m_disp.group(1)

        m_disp_ant = re.search(r"lecturas v[áa]lidas de nidos.*?\(InfluxDB\).*?([▼▲])?\s*Periodo anterior:\s*([\d,]+%)", texto_completo, re.IGNORECASE | re.DOTALL)
        if m_disp_ant:
            datos["disp_anterior"] = m_disp_ant.group(2)
            try:
                act_d = float(datos["disponibilidad_real"].replace("%", "").replace(",", "."))
                ant_d = float(datos["disp_anterior"].replace("%", "").replace(",", "."))
                datos["tendencia_disp"] = "▲" if act_d >= ant_d else "▼"
            except Exception:
                if m_disp_ant.group(1):
                    datos["tendencia_disp"] = m_disp_ant.group(1)

        # 4. Nidos Activos
        m_nidos = re.search(r"(\d+\s+de\s+250)\s+nidos\s*\(\d+%\)\s+estuvieron\s+activos", texto_completo, re.IGNORECASE)
        if not m_nidos:
            m_nidos = re.search(r"(\d+\s+de\s+250)\n\d+%\s+report[óo]", texto_completo, re.IGNORECASE)
        if m_nidos:
            datos["nidos_activos"] = m_nidos.group(1)

        # 5. Tiempo fuera de rango y Periodo Anterior
        m_tfr = re.search(r"Los nidos estuvieron fuera de rango el\s*([\d,]+%)\s*del tiempo", texto_completo, re.IGNORECASE)
        if m_tfr:
            datos["tiempo_fuera_rango"] = m_tfr.group(1)

        m_tfr_det = re.search(
            r"fuera de rango el\s*[\d,]+%\s*del tiempo y\s*(\d+\s*de\s*\d+\s*nidos\s*\(\d+%\))\s*tuvieron.*?Periodo anterior:\s*([\d,]+%)",
            texto_completo, re.IGNORECASE | re.DOTALL
        )
        if m_tfr_det:
            datos["nidos_con_alerta_temp"] = m_tfr_det.group(1)
            datos["t_fuera_rango_ant"] = m_tfr_det.group(2)
            try:
                act_val = float(datos["tiempo_fuera_rango"].replace("%", "").replace(",", "."))
                ant_val = float(datos["t_fuera_rango_ant"].replace("%", "").replace(",", "."))
                datos["tendencia_fuera_rango"] = "▼" if act_val < ant_val else "▲"
            except Exception:
                pass

        # 6. Desconexiones de grupo y Horas
        m_desc = re.search(r"Se registraron\s+(\d+)\s+desconexiones de grupo completo\s*\((\d+\s*h)\)", texto_completo, re.IGNORECASE)
        if m_desc:
            datos["desconexiones_totales"] = m_desc.group(1)
            datos["horas_desconexion"] = m_desc.group(2)

        # 7. Fallas de Sonda
        m_sonda = re.search(r"Posible falla de sonda\s+D2\s+(\d+)", texto_completo, re.IGNORECASE)
        if not m_sonda:
            m_sonda = re.search(r"y\s+(\d+)\s+de posible falla de sonda", texto_completo, re.IGNORECASE)
        if m_sonda:
            datos["fallas_sonda"] = m_sonda.group(1)

        # 8. Tablas para gráficos
        datos["comparativa_alertas"] = self._extraer_comparativa_alertas(texto_completo)
        datos["disponibilidad_grupos"] = self._extraer_disponibilidad_grupos(texto_completo)

        # 9. Textos dinámicos Lámina 3 (Diagnóstico de Grupos Críticos)
        m_crit = re.search(r"Grupos cr[íi]ticos:\s*(.+?)(?:\.\s*En atenci[óo]n:|\nLos nidos)", texto_completo, re.IGNORECASE | re.DOTALL)
        if m_crit:
            limpio = " ".join(m_crit.group(1).split())
            datos["grupos_criticos_texto"] = limpio + "."

        m_brecha = re.search(
            r"(\d+)\s+alertas\s+[«\"<']*sin datos[»\">']*.*?disponibilidad estimada con alertas\s*\(([\d,]+%)\)\s*es menor que la real\s*\(([\d,]+%)\)",
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

        # 10. Textos dinámicos Lámina 4 (Desconexiones, Caídas Simultáneas, Horarios y Salas)
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
            r"El\s+(\d+%)\s+de los cortes de 30 min o m[áa]s comienza entre\s+([\d:]+)\s+y\s+([\d:]+)\s*\(m[áa]ximo a las\s+([\d:]+)\)",
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

    def _extraer_comparativa_alertas(self, texto: str) -> dict:
        categorias = ["T° Fuera Rango", "Nido Sin Datos", "Falla Sonda"]
        actual = [168.3, 86.0, 58.1]
        anterior = [195.0, 95.0, 65.0]

        if not texto:
            return {"categorias": categorias, "actual": actual, "anterior": anterior}

        patrones = [
            r"fuera de rango\s+Total\s+[\d\.]+\s+([\d,]+)\s+([\d,]+)",
            r"Nido sin datos\s+Total\s+[\d\.]+\s+([\d,]+)\s+([\d,]+)",
            r"Posible falla de sonda\s+(?:Total|D2)\s+[\d\.]+\s+([\d,]+)\s+([\d,]+)"
        ]

        nuevos_act = []
        nuevos_ant = []
        for pat in patrones:
            m = re.search(pat, texto, re.IGNORECASE)
            if m:
                nuevos_act.append(float(m.group(1).replace(",", ".")))
                nuevos_ant.append(float(m.group(2).replace(",", ".")))

        if len(nuevos_act) == 3:
            return {"categorias": categorias, "actual": nuevos_act, "anterior": nuevos_ant}

        return {"categorias": categorias, "actual": actual, "anterior": anterior}

    def _extraer_disponibilidad_grupos(self, texto: str) -> list:
        default_grupos = [
            ("Grupo 20", 12.9), ("Grupo 28", 48.6), ("Grupo 10", 74.0),
            ("Grupo 23", 91.6), ("Grupo 19", 94.0), ("Grupo 25", 96.6),
            ("Grupo 24", 97.6), ("Grupo 21", 98.1), ("Grupo 6", 98.1),
            ("Grupo 8", 98.6), ("Grupo 26", 98.9), ("Grupo 22", 99.6),
            ("Grupo 9", 99.9), ("Grupo 5", 100.0)
        ]
        if not texto:
            return default_grupos

        encontrados = {}
        patron_tabla1 = re.findall(
            r"(Grupo\s+\d+)\s+(?:Cr[íi]tico|Atenci[óo]n|Normal)\s+\d+\s+([\d,]+)%",
            texto, re.IGNORECASE
        )
        for grp, val in patron_tabla1:
            nombre = " ".join(grp.split()).title()
            encontrados[nombre] = float(val.replace(",", "."))

        if len(encontrados) >= 5:
            return sorted(encontrados.items(), key=lambda x: x[1])

        return default_grupos

    def _extraer_top_salas_alertas(self, texto: str) -> str:
        m_seccion = re.search(
            r"Salas con m[áa]s alertas \(eventos [úu]nicos\)(.+?)Nidos con m[áa]s tiempo fuera de rango",
            texto, re.IGNORECASE | re.DOTALL
        )
        if not m_seccion:
            return ""

        bloque = m_seccion.group(1)
        filas = re.findall(
            r"(Grupo\s+\d+)\s+(PAB\d+\s+MATERNIDAD\s+\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            bloque, re.IGNORECASE
        )
        if not filas:
            return ""

        lineas_out = []
        for grp, sala, t_rango, s_datos, f_sonda, total, hrs in filas[:3]:
            sala_corta = re.sub(r"MATERNIDAD", "Mat", sala, flags=re.IGNORECASE)
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