import os
import re
import pdfplumber


class TecnoandinaPDFExtractor:
    """
    Extrae dinámicamente todos los KPIs, datos para gráficos (Slide 2 y Slide 3)
    y textos de diagnóstico desde cualquier PDF semanal de Tecnoandina.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    @staticmethod
    def _limpiar_texto_pdf(texto: str) -> str:
        """
        Corrige los glifos corruptos de la fuente embebida del PDF (donde '(' aparece
        como un carácter del Área de Uso Privado Unicode o \ufffd -> cuadrado con '?').
        """
        if not texto:
            return ""

        # 1. Reemplazar comillas especiales
        texto = texto.replace("«", "'").replace("»", "'").replace("“", "'").replace("”", "'")

        # 2. En los PDFs de Tecnoandina, el '(' suele venir codificado en el rango PUA (\ue000-\uf8ff) o \ufffd
        texto = re.sub(r"[\ue000-\uf8ff\ufffd]+", "(", texto)

        # 3. Si algún otro carácter no-ASCII extraño quedó justo antes de un número que cierra con ')', convertirlo en '('
        texto = re.sub(r"[^\x20-\x7EáéíóúÁÉÍÓÚñÑüÜ°ºª▼▲≥≤\n\r\t]+\s*(\d)", r"(\1", texto)

        # 4. Si el '(' se perdió por completo dejando "Grupo 9 44% datos)", reconstruirlo: "Grupo 9 (44% datos)"
        texto = re.sub(r"(Grupo\s+\d+)\s+(\d+%[^()\n]*\))", r"\1 (\2", texto)

        # 5. Evitar paréntesis dobles "((" o espacios después de '('
        texto = re.sub(r"\(+", "(", texto)
        texto = re.sub(r"\(\s+", "(", texto)

        return texto

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
                t = page.extract_text(layout=False) or ""
                paginas_texto.append(self._limpiar_texto_pdf(t))

        texto_completo = "\n".join(paginas_texto)
        if not texto_completo.strip():
            return datos

        # 1. Periodo
        m_per = re.search(r"Periodo del\s+(\d{2}-\d{2}-\d{4}\s+al\s+\d{2}-\d{2}-\d{4})", texto_completo, re.IGNORECASE)
        if m_per:
            datos["periodo"] = m_per.group(1).strip()

        # 2. Alertas Totales, Promedio por día y Variación
        m_res_al = re.search(r"Llegaron a QA\s+([\d\.]+)\s+alertas\s*\(?(\d+)\s+por d[ií]a\)?", texto_completo, re.IGNORECASE)
        if m_res_al:
            datos["alertas_totales"] = m_res_al.group(1)
            datos["alertas_por_dia"] = m_res_al.group(2)

        m_var2 = re.search(r"(bajaron|subieron|aumentaron|disminuyeron)\s+un\s+(\d+%)\s+respecto", texto_completo, re.IGNORECASE)
        if m_var2:
            verbo = m_var2.group(1).lower()
            es_baja = "bajar" in verbo or "disminu" in verbo
            datos["tendencia_alertas"] = "▼" if es_baja else "▲"
            datos["verbo_alertas"] = "bajaron" if es_baja else "subieron"
            datos["variacion_alertas"] = m_var2.group(2)

        # 3. Disponibilidad Real (InfluxDB) y Periodo Anterior
        m_disp = re.search(r"Disponibilidad real de datos\s*\(?InfluxDB\)?:\s*([\d,]+%)", texto_completo, re.IGNORECASE)
        if m_disp:
            datos["disponibilidad_real"] = m_disp.group(1)

        m_disp_ant = re.search(r"Periodo anterior:\s*([\d,]+%)", texto_completo, re.IGNORECASE)
        if m_disp_ant:
            datos["disp_anterior"] = m_disp_ant.group(1)
            try:
                act_d = float(datos["disponibilidad_real"].replace("%", "").replace(",", "."))
                ant_d = float(datos["disp_anterior"].replace("%", "").replace(",", "."))
                datos["tendencia_disp"] = "▲" if act_d >= ant_d else "▼"
            except Exception:
                pass

        # 4. Nidos Activos
        m_nidos = re.search(r"(\d+\s+de\s+250)\s+nidos\s*\(?\d+%\)?\s+estuvieron\s+activos", texto_completo, re.IGNORECASE)
        if not m_nidos:
            m_nidos = re.search(r"(\d+\s+de\s+250)", texto_completo, re.IGNORECASE)
        if m_nidos:
            datos["nidos_activos"] = m_nidos.group(1)

        # 5. Tiempo fuera de rango y Periodo Anterior
        m_tfr = re.search(r"Los nidos estuvieron fuera de rango el\s*([\d,]+%)\s*del tiempo", texto_completo, re.IGNORECASE)
        if m_tfr:
            datos["tiempo_fuera_rango"] = m_tfr.group(1)

        m_tfr_det = re.search(
            r"fuera de rango el\s*[\d,]+%\s*del tiempo y\s*(\d+\s*de\s*\d+\s*nidos\s*\(?\d+%\)?)\s*tuvieron.*?Periodo anterior:\s*([\d,]+%)",
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
        m_desc = re.search(r"Se registraron\s+(\d+)\s+desconexiones de grupo completo\s*\(?(\d+\s*h)\)?", texto_completo, re.IGNORECASE)
        if m_desc:
            datos["desconexiones_totales"] = m_desc.group(1)
            datos["horas_desconexion"] = m_desc.group(2)

        # 7. Fallas de Sonda
        m_sonda = re.search(r"y\s+(\d+)\s+de posible falla de sonda", texto_completo, re.IGNORECASE)
        if m_sonda:
            datos["fallas_sonda"] = m_sonda.group(1)

        # =========================================================================
        # 8. EXTRACCIÓN ROBUSTA PARA LOS 2 GRÁFICOS (SLIDE 2 Y SLIDE 3)
        # =========================================================================
        comp_extraida = self._extraer_comparativa_alertas_robusto(texto_completo)
        if comp_extraida:
            datos["comparativa_alertas"] = comp_extraida

        grupos_extraidos = self._extraer_disponibilidad_grupos_robusto(paginas_texto, texto_completo)
        if grupos_extraidos:
            datos["disponibilidad_grupos"] = grupos_extraidos

        # 9. Textos dinámicos Lámina 3
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

        # 10. Textos dinámicos Lámina 4
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

    def _extraer_comparativa_alertas_robusto(self, texto: str) -> dict:
        """
        Lee la tabla '1. Alertas generadas' (Página 1) línea por línea.
        Busca las filas de 'Total' (o 'D2' para falla de sonda) y extrae los 2 últimos
        decimales: [Por día (Actual), Por día periodo anterior (Anterior)].
        """
        categorias = ["T° Fuera Rango", "Nido Sin Datos", "Falla Sonda"]
        val_rango = None
        val_datos = None
        val_sonda = None

        for linea in texto.splitlines():
            l_low = linea.lower()
            # Extraer todos los números con coma decimal de la línea (ej. ['81,8', '168,3'])
            decimales = re.findall(r"\d+,\d+", linea)
            if len(decimales) >= 2:
                act = float(decimales[-2].replace(",", "."))
                ant = float(decimales[-1].replace(",", "."))

                if "fuera de rango" in l_low and "total" in l_low:
                    val_rango = (act, ant)
                elif "nido sin datos" in l_low and "total" in l_low:
                    val_datos = (act, ant)
                elif "falla de sonda" in l_low and ("total" in l_low or "d2" in l_low):
                    val_sonda = (act, ant)

        if val_rango and val_datos and val_sonda:
            return {
                "categorias": categorias,
                "actual": [val_rango[0], val_datos[0], val_sonda[0]],
                "anterior": [val_rango[1], val_datos[1], val_sonda[1]]
            }
        return None

    def _extraer_disponibilidad_grupos_robusto(self, paginas_texto: list, texto_completo: str) -> list:
        """
        Extrae el porcentaje de disponibilidad real (InfluxDB) de los 14 grupos.
        Busca primero en la tabla '2. Estatus por grupo' (Página 1) y como respaldo
        en la tabla '6. Alertas sin datos frente a los datos reales' (Página 5).
        """
        encontrados = {}

        # 1. Buscar en Página 1 dentro del bloque "Estatus por grupo"
        texto_p1 = paginas_texto[0] if paginas_texto else texto_completo
        m_bloque_p1 = re.search(r"Estatus por grupo(.+?)(?:Recap de alertas|$)", texto_p1, re.IGNORECASE | re.DOTALL)
        bloque_p1 = m_bloque_p1.group(1) if m_bloque_p1 else texto_p1

        for linea in bloque_p1.splitlines():
            # Buscar líneas que comiencen con "Grupo XX" y contengan Crítico/Atención/Normal
            m_grp = re.match(r"^\s*(Grupo\s+\d+)\s+(?:Cr[íi]tico|Atenci[óo]n|Normal)\b(.*)$", linea, re.IGNORECASE)
            if m_grp:
                nombre_grp = " ".join(m_grp.group(1).split()).title()
                resto_linea = m_grp.group(2)
                # El primer porcentaje en esa fila siempre es "Disponibilidad de datos" (ej: 16,4%)
                m_pct = re.search(r"(\d+,\d+)%", resto_linea)
                if m_pct:
                    encontrados[nombre_grp] = float(m_pct.group(1).replace(",", "."))

        # 2. Respaldo en Página 5 (Sección 6: "Grupo XX  16,4%") por si algún grupo quedó fuera
        if len(encontrados) < 14 and len(paginas_texto) >= 5:
            texto_p5 = paginas_texto[-1]
            for linea in texto_p5.splitlines():
                m_g5 = re.search(r"\b(Grupo\s+\d+)\b.*?(\d+,\d+)%", linea, re.IGNORECASE)
                if m_g5:
                    nombre_grp = " ".join(m_g5.group(1).split()).title()
                    if nombre_grp not in encontrados:
                        encontrados[nombre_grp] = float(m_g5.group(2).replace(",", "."))

        if len(encontrados) >= 5:
            # Ordenar de menor a mayor disponibilidad para el gráfico semáforo
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