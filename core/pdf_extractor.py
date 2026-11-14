import os
import re
import pdfplumber


class TecnoandinaPDFExtractor:
    """
    Extractor de alta precisión para reportes PDF semanales de Tecnoandina.
    Extrae KPIs, tablas para gráficos (Slide 2 y Slide 3) y diagnósticos dinámicos.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    @staticmethod
    def _sanitizar_glifo_parentesis(texto: str) -> str:
        """
        Corrige los glifos corruptos de la fuente embebida del PDF (donde '(' aparece
        como un carácter no-ASCII o cuadrado '?') y normaliza comillas.
        """
        if not texto:
            return ""

        texto = texto.replace("«", "'").replace("»", "'").replace("“", "'").replace("”", "'")

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
                resultado.append("(")

        limpio = "".join(resultado)
        limpio = re.sub(r"(Grupo\s+\d+)\s+(\d+%[^()\n]*\))", r"\1 (\2", limpio)
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
        tablas_paginas = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                # Extraer texto normal y también palabras ordenadas por coordenadas (top, x0)
                words = page.extract_words(x_tolerance=2, y_tolerance=3)
                if words:
                    # Agrupar palabras por línea visual (redondeando coordenada vertical 'top' cada 3 pts)
                    lineas_dict = {}
                    for w in words:
                        y_key = round(w["top"] / 3.0) * 3
                        lineas_dict.setdefault(y_key, []).append((w["x0"], w["text"]))
                    lineas_ordenadas = []
                    for y_key in sorted(lineas_dict.keys()):
                        palabras_linea = [txt for _, txt in sorted(lineas_dict[y_key], key=lambda item: item[0])]
                        lineas_ordenadas.append(" ".join(palabras_linea))
                    t_reconstruido = "\n".join(lineas_ordenadas)
                else:
                    t_reconstruido = page.extract_text() or ""

                t_limpio = self._sanitizar_glifo_parentesis(t_reconstruido)
                paginas_texto.append(t_limpio)

                try:
                    tbs = page.extract_tables()
                    if tbs:
                        tablas_paginas.extend(tbs)
                except Exception:
                    pass

        texto_completo = "\n".join(paginas_texto)
        if not texto_completo.strip():
            return datos

        # 1. Periodo
        m_per = re.search(r"Periodo del\s+(\d{2}-\d{2}-\d{4}\s+al\s+\d{2}-\d{2}-\d{4})", texto_completo, re.IGNORECASE)
        if m_per:
            datos["periodo"] = m_per.group(1).strip()

        # 2. KPI 1: Alertas Totales, por día y variación
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

        # 3. KPI 2: Disponibilidad Real (InfluxDB)
        m_disp_real = re.search(r"Disponibilidad real de datos[^:]*:\s*([\d,]+%)", texto_completo, re.IGNORECASE)
        if m_disp_real:
            datos["disponibilidad_real"] = m_disp_real.group(1)
        else:
            m_disp_p2 = re.search(r"lecturas esperadas de nido:\s*([\d,]+%)\s*v[áa]lidas", texto_completo, re.IGNORECASE)
            if m_disp_p2:
                datos["disponibilidad_real"] = m_disp_p2.group(1)

        # 4. KPI 3: Nidos Activos (93 de 250)
        m_bloque_res = re.search(r"Resumen del periodo(.+?)Alertas generadas", texto_completo, re.IGNORECASE | re.DOTALL)
        texto_resumen = m_bloque_res.group(1) if m_bloque_res else texto_completo

        m_nidos_act = re.search(r"(\d+)\s+de\s+250\s+nidos", texto_resumen, re.IGNORECASE)
        if not m_nidos_act:
            m_nidos_act = re.search(r"tiempo\.\s*(\d+)\s+de\s+250", texto_completo, re.IGNORECASE)
        if not m_nidos_act:
            m_nidos_act = re.search(r"\b(\d{1,3})\s+de\s+250\b", texto_resumen, re.IGNORECASE)
        if m_nidos_act:
            datos["nidos_activos"] = f"{m_nidos_act.group(1)} de 250"

        # 5. KPI 4: Tiempo fuera de rango (11,6%) y Periodos Anteriores
        m_tfr = re.search(r"Los nidos estuvieron fuera de rango el\s*([\d,]+%)\s*del tiempo", texto_completo, re.IGNORECASE)
        if m_tfr:
            datos["tiempo_fuera_rango"] = m_tfr.group(1)

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

        # 6. KPI 5: Desconexiones de grupo (60 y 364 h)
        m_desc = re.search(r"Se registraron\s+(\d+)\s+desconexiones de grupo completo\s*\(?(\d+\s*h)\)?", texto_completo, re.IGNORECASE)
        if m_desc:
            datos["desconexiones_totales"] = m_desc.group(1)
            datos["horas_desconexion"] = m_desc.group(2)

        # 7. KPI 6: Fallas de Sonda (399)
        m_sonda = re.search(r"y\s+(\d+)\s+de posible falla de sonda", texto_completo, re.IGNORECASE)
        if m_sonda:
            datos["fallas_sonda"] = m_sonda.group(1)

        # =========================================================================
        # 8. EXTRACCIÓN DE DATOS PARA LOS 2 GRÁFICOS (SLIDE 2 Y SLIDE 3)
        # =========================================================================
        comp_extraida = self._extraer_comparativa_alertas_infalible(texto_completo, tablas_paginas)
        if comp_extraida:
            datos["comparativa_alertas"] = comp_extraida

        grupos_extraidos = self._extraer_disponibilidad_grupos_infalible(paginas_texto, texto_completo, tablas_paginas)
        if grupos_extraidos:
            datos["disponibilidad_grupos"] = grupos_extraidos

        # =========================================================================
        # 9. TEXTOS DINÁMICOS DE LÁMINAS 3 Y 4
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

    def _extraer_comparativa_alertas_infalible(self, texto: str, tablas: list) -> dict:
        """
        Extrae los promedios diarios (Actual vs Anterior) de la tabla '1. Alertas generadas'.
        Busca por tokens numéricos después de 'Total' (o 'D2' en sonda) sin importar saltos de línea.
        """
        categorias = ["T° Fuera Rango", "Nido Sin Datos", "Falla Sonda"]
        res_act = [168.3, 86.0, 58.1]
        res_ant = [195.0, 95.0, 65.0]
        encontrado_alguno = False

        # Acotar a la primera mitad del documento (antes de "Estatus por grupo")
        idx_fin = texto.lower().find("estatus por grupo")
        zona = texto[:idx_fin] if idx_fin != -1 else texto

        # Patrón genérico: Nombre categoría -> Total -> [Entero Alertas] -> [Decimal Por Día] -> [Decimal Periodo Anterior]
        patrones = [
            (0, r"fuera\s+de\s+rango[\s|]*Total[^\d]*([\d\.]+)[\s|]+(\d+[,\.]\d+)[\s|]+(\d+[,\.]\d+)"),
            (1, r"Nido\s+sin\s+datos[\s|]*Total[^\d]*([\d\.]+)[\s|]+(\d+[,\.]\d+)[\s|]+(\d+[,\.]\d+)"),
            (2, r"falla\s+de\s+sonda[\s|]*(?:Total|D2)[^\d]*([\d\.]+)[\s|]+(\d+[,\.]\d+)[\s|]+(\d+[,\.]\d+)")
        ]

        for idx, pat in patrones:
            m = re.search(pat, zona, re.IGNORECASE | re.DOTALL)
            if m:
                try:
                    res_act[idx] = float(m.group(2).replace(",", "."))
                    res_ant[idx] = float(m.group(3).replace(",", "."))
                    encontrado_alguno = True
                except Exception:
                    pass

        if encontrado_alguno:
            return {"categorias": categorias, "actual": res_act, "anterior": res_ant}
        return None

    def _extraer_disponibilidad_grupos_infalible(self, paginas_texto: list, texto_completo: str, tablas: list) -> list:
        """
        Extrae la disponibilidad real (%) de los 14 grupos desde:
        1) La tabla '6. Alertas sin datos frente a los datos reales' (Página 5)
        2) La tabla '2. Estatus por grupo' (Página 1)
        """
        encontrados = {}

        # 1. Extraer de la tabla "Estatus por grupo" (Página 1)
        # Busca "Grupo XX" seguido en los próximos 40 caracteres por un estado y luego el primer porcentaje XX,X%
        idx_est = texto_completo.lower().find("estatus por grupo")
        idx_disp2 = texto_completo.lower().find("salas con menor disponibilidad")
        zona_est = texto_completo[idx_est:idx_disp2] if (idx_est != -1 and idx_disp2 != -1) else texto_completo

        matches_p1 = re.findall(
            r"Grupo\s+(\d+)[\s|]+(?:Cr[íi]tico|Atenci[óo]n|Normal)[\s|]+\d+[\s|]+(\d+[,\.]\d+)%",
            zona_est, re.IGNORECASE
        )
        for num_grp, pct in matches_p1:
            encontrados[f"Grupo {num_grp}"] = float(pct.replace(",", "."))

        # 2. Extraer de la tabla resumen de la Sección 6 (Página 5: "Disponibilidad InfluxDB")
        idx_sec6 = texto_completo.lower().find("disponibilidad influxdb")
        if idx_sec6 != -1:
            zona_6 = texto_completo[idx_sec6:]
            idx_calc = zona_6.lower().find("cómo se calcula")
            if idx_calc == -1:
                idx_calc = zona_6.lower().find("como se calcula")
            if idx_calc != -1:
                zona_6 = zona_6[:idx_calc]

            # A) Emparejamiento directo "Grupo XX  YY,Y%"
            for num_grp, pct in re.findall(r"Grupo\s+(\d+)[\s|]+(\d+[,\.]\d+)%", zona_6, re.IGNORECASE):
                encontrados[f"Grupo {num_grp}"] = float(pct.replace(",", "."))

            # B) Emparejamiento para filas apiladas ("Grupo 26 Grupo 5 94,7% 97,4%")
            for g1, g2, p1, p2 in re.findall(
                r"Grupo\s+(\d+)[\s|]+Grupo\s+(\d+)[\s|]+(\d+[,\.]\d+)%[\s|]+(\d+[,\.]\d+)%",
                zona_6, re.IGNORECASE
            ):
                encontrados[f"Grupo {g1}"] = float(p1.replace(",", "."))
                encontrados[f"Grupo {g2}"] = float(p2.replace(",", "."))

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
            r"(Grupo\s+\d+)[\s|]+(PAB\d+\s+Maternidad\s+\S+)[\s|]+(\d+)[\s|]+(\d+)[\s|]+(\d+)[\s|]+(\d+)[\s|]+(\d+)",
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