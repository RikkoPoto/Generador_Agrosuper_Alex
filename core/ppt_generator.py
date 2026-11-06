import io
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

from core.chart_builder import ChartBuilder

# Paleta 1: Corporativo Agrosuper
AZUL_AGROSUPER = RGBColor(27, 54, 93)       # #1B365D
NARANJA_AGROSUPER = RGBColor(232, 119, 34)  # #E87722
FONDO_GRIS_CLARO = RGBColor(244, 246, 249)  # #F4F6F9

# Paleta 2: Estilo Gamma (PDF Chanchillas)
GAMMA_BG = RGBColor(245, 247, 246)          # Fondo gris verdoso muy suave
GAMMA_VERDE_OSCURO = RGBColor(17, 139, 80)  # #118B50 (Verde principal Gamma)
GAMMA_VERDE_LIMA = RGBColor(140, 198, 63)   # #8CC63F (Verde secundario Gamma)
GAMMA_CAJA_SUAVE = RGBColor(232, 245, 233)  # #E8F5E9 (Fondo de llamada inferior)
GAMMA_TITULO = RGBColor(15, 23, 42)         # #0F172A (Casi negro editorial)

# Colores Comunes
BLANCO = RGBColor(255, 255, 255)
TEXTO_OSCURO = RGBColor(30, 41, 59)
TEXTO_GRIS = RGBColor(100, 116, 139)
ROJO_CRITICO = RGBColor(220, 38, 38)
VERDE_OK = RGBColor(22, 163, 74)
BORDE_SUAVE = RGBColor(203, 213, 225)


class ExecutivePPTGenerator:
    """
    Genera la presentación ejecutiva completa en formato .pptx (16:9).
    Soporta dos estilos visuales:
      - 'agrosuper': Encabezado azul marino, acentos naranjas, portada enriquecida y logo grande.
      - 'gamma': Estilo minimalista editorial (Chanchillas), tarjetas con acento superior verde y bloques limpios.
    """

    def __init__(self, output_path: str, estilo: str = "agrosuper"):
        self.output_path = output_path
        self.estilo = estilo.lower()
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.blank_layout = self.prs.slide_layouts[6]

    @property
    def color_primario(self):
        return GAMMA_VERDE_OSCURO if self.estilo == "gamma" else AZUL_AGROSUPER

    @property
    def color_secundario(self):
        return GAMMA_VERDE_LIMA if self.estilo == "gamma" else NARANJA_AGROSUPER

    def generar_presentacion_completa(self, datos_pdf: dict, datos_usuario: dict):
        ruta_graf_comp = "temp_chart_comp.png"
        ruta_graf_sem = "temp_chart_semaforo.png"
        ChartBuilder.crear_grafico_comparativo_alertas(datos_pdf["comparativa_alertas"], ruta_graf_comp, self.estilo)
        ChartBuilder.crear_grafico_semaforo_grupos(datos_pdf["disponibilidad_grupos"], ruta_graf_sem, self.estilo)

        self._slide_1_portada(datos_pdf, datos_usuario)
        self._slide_2_kpis_y_alertas(datos_pdf, ruta_graf_comp)
        self._slide_3_disponibilidad_grupos(datos_pdf, ruta_graf_sem)
        self._slide_4_focos_criticos_terreno(datos_pdf)
        self._slide_5_gestion_y_reuniones(datos_usuario)
        self._slide_6_emergencias_y_fotos(datos_usuario)

        self.prs.save(self.output_path)

        for temp_file in [ruta_graf_comp, ruta_graf_sem]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    # =========================================================================
    # UTILIDADES DE DISEÑO ADAPTABLES (AGROSUPER vs GAMMA)
    # =========================================================================
    def _aplicar_encabezado(self, slide, titulo: str, subtitulo: str):
        if self.estilo == "gamma":
            # Estilo Gamma Original: Fondo claro continuo sin barra pesada arriba
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            bg.fill.solid()
            bg.fill.fore_color.rgb = GAMMA_BG
            bg.line.fill.background()

            # Píldora / Acento superior izquierdo en Azul Agrosuper
            pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(0.35), Inches(0.12), Inches(0.65))
            pill.fill.solid()
            pill.fill.fore_color.rgb = AZUL_AGROSUPER
            pill.line.fill.background()

            # Título editorial oscuro grande
            tb = slide.shapes.add_textbox(Inches(0.75), Inches(0.25), Inches(9.3), Inches(0.85))
            tf = tb.text_frame
            p = tf.paragraphs[0]
            p.text = titulo
            p.font.size = Pt(24)
            p.font.bold = True
            p.font.color.rgb = GAMMA_TITULO
            p.font.name = "Segoe UI"

            p2 = tf.add_paragraph()
            p2.text = subtitulo
            p2.font.size = Pt(11)
            p2.font.color.rgb = TEXTO_GRIS
            p2.font.name = "Segoe UI"

            # Etiqueta superior derecha estilo Gamma en Azul Agrosuper con logo agrandado
            badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.25), Inches(0.22), Inches(2.55), Inches(0.82))
            badge.fill.solid()
            badge.fill.fore_color.rgb = AZUL_AGROSUPER
            badge.line.fill.background()

            logo_path = self._obtener_ruta_recurso(os.path.join("assets", "logo_agrosuper_white.webp"))
            if os.path.exists(logo_path):
                self._insertar_imagen_encuadrada(slide, logo_path, Inches(10.4), Inches(0.28), Inches(2.25), Inches(0.7))
            else:
                p_b = badge.text_frame.paragraphs[0]
                p_b.text = "AGROSUPER"
                p_b.font.size = Pt(14)
                p_b.font.bold = True
                p_b.font.color.rgb = BLANCO
                p_b.alignment = PP_ALIGN.CENTER

        else:
            # Estilo Corporativo Agrosuper Clásico (con logo más grande en el encabezado)
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            bg.fill.solid()
            bg.fill.fore_color.rgb = FONDO_GRIS_CLARO
            bg.line.fill.background()

            header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.1))
            header.fill.solid()
            header.fill.fore_color.rgb = AZUL_AGROSUPER
            header.line.fill.background()

            accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.1), Inches(13.333), Inches(0.07))
            accent.fill.solid()
            accent.fill.fore_color.rgb = NARANJA_AGROSUPER
            accent.line.fill.background()

            tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.14), Inches(9.3), Inches(0.5))
            tf = tb.text_frame
            p = tf.paragraphs[0]
            p.text = titulo
            p.font.size = Pt(22)
            p.font.bold = True
            p.font.color.rgb = BLANCO
            p.font.name = "Calibri"

            p2 = tf.add_paragraph()
            p2.text = subtitulo
            p2.font.size = Pt(11)
            p2.font.color.rgb = RGBColor(203, 213, 225)
            p2.font.name = "Calibri"

            logo_path = os.path.join("assets", "logo_agrosuper_white.webp")
            if os.path.exists(logo_path):
                # Logo Agrosuper más grande y visible en el encabezado azul
                self._insertar_imagen_encuadrada(slide, logo_path, Inches(10.15), Inches(0.1), Inches(2.7), Inches(0.9))
            else:
                tb_logo = slide.shapes.add_textbox(Inches(10.2), Inches(0.25), Inches(2.7), Inches(0.5))
                p_logo = tb_logo.text_frame.paragraphs[0]
                p_logo.text = "AGROSUPER"
                p_logo.alignment = PP_ALIGN.RIGHT
                p_logo.font.size = Pt(20)
                p_logo.font.bold = True
                p_logo.font.italic = True
                p_logo.font.color.rgb = BLANCO

    def _crear_tarjeta_kpi(self, slide, left, top, width, height, titulo_kpi, valor_principal, subtexto, color_acento):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = BLANCO

        if self.estilo == "gamma":
            card.line.color.rgb = BORDE_SUAVE
            card.line.width = Pt(1)
            # Barra superior estilo Gamma (como en lámina 3 de Chanchillas)
            top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.05), top, width - Inches(0.1), Inches(0.08))
            top_bar.fill.solid()
            top_bar.fill.fore_color.rgb = color_acento
            top_bar.line.fill.background()
        else:
            card.line.color.rgb = color_acento
            card.line.width = Pt(1.5)

        tb = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.12), width - Inches(0.3), height - Inches(0.2))
        tf = tb.text_frame
        tf.word_wrap = True

        if self.estilo == "gamma":
            # En Gamma el número gigante va primero y en color verde/acento
            p_val = tf.paragraphs[0]
            p_val.text = str(valor_principal)
            p_val.font.size = Pt(26)
            p_val.font.bold = True
            p_val.font.color.rgb = GAMMA_VERDE_OSCURO if color_acento != ROJO_CRITICO else ROJO_CRITICO

            p_tit = tf.add_paragraph()
            p_tit.text = titulo_kpi
            p_tit.font.size = Pt(10.5)
            p_tit.font.bold = True
            p_tit.font.color.rgb = GAMMA_TITULO

            p_sub = tf.add_paragraph()
            p_sub.text = subtexto
            p_sub.font.size = Pt(9)
            p_sub.font.color.rgb = TEXTO_GRIS
        else:
            p_tit = tf.paragraphs[0]
            p_tit.text = titulo_kpi.upper()
            p_tit.font.size = Pt(10)
            p_tit.font.bold = True
            p_tit.font.color.rgb = TEXTO_GRIS

            p_val = tf.add_paragraph()
            p_val.text = str(valor_principal)
            p_val.font.size = Pt(24)
            p_val.font.bold = True
            p_val.font.color.rgb = AZUL_AGROSUPER

            p_sub = tf.add_paragraph()
            p_sub.text = subtexto
            p_sub.font.size = Pt(9.5)
            p_sub.font.color.rgb = NARANJA_AGROSUPER if "▲" in subtexto or "Crítico" in subtexto else VERDE_OK

    def _insertar_imagen_encuadrada(self, slide, img_path, left, top, max_w, max_h):
        if not img_path or not os.path.exists(img_path):
            return
        try:
            with Image.open(img_path) as img:
                w_px, h_px = img.size
                ratio = w_px / h_px
                box_ratio = max_w / max_h

                if ratio > box_ratio:
                    final_w = max_w
                    final_h = max_w / ratio
                else:
                    final_h = max_h
                    final_w = max_h * ratio

                offset_x = left + (max_w - final_w) / 2
                offset_y = top + (max_h - final_h) / 2

                if img_path.lower().endswith(".webp"):
                    img_stream = io.BytesIO()
                    img.convert("RGBA").save(img_stream, format="PNG")
                    img_stream.seek(0)
                    slide.shapes.add_picture(img_stream, int(offset_x), int(offset_y), width=int(final_w), height=int(final_h))
                else:
                    slide.shapes.add_picture(img_path, int(offset_x), int(offset_y), width=int(final_w), height=int(final_h))
        except Exception as e:
            print(f"No se pudo cargar la imagen {img_path}: {e}")

    # =========================================================================
    # CONSTRUCCIÓN DE LAS 6 DIAPOSITIVAS
    # =========================================================================

    def _obtener_ruta_recurso(rel_path: str) -> str:
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, rel_path)

    def _slide_1_portada(self, datos_pdf: dict, datos_usuario: dict):
        slide = self.prs.slides.add_slide(self.blank_layout)
        logo_path = self._obtener_ruta_recurso(os.path.join("assets", "logo_agrosuper_white.webp"))
        logo_cerdo = self._obtener_ruta_recurso(os.path.join("assets", "logo_cerdo_ventilacion.png"))

        if self.estilo == "gamma":
            # Portada Estilo Gamma Original (con el panel derecho en Azul Agrosuper como pediste)
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            bg.fill.solid()
            bg.fill.fore_color.rgb = GAMMA_BG
            bg.line.fill.background()

            # Panel derecho en Azul Agrosuper
            panel_der = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.5), 0, Inches(4.833), Inches(7.5))
            panel_der.fill.solid()
            panel_der.fill.fore_color.rgb = AZUL_AGROSUPER
            panel_der.line.fill.background()

            # Franja fina verde lima
            franja_lima = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.38), 0, Inches(0.12), Inches(7.5))
            franja_lima.fill.solid()
            franja_lima.fill.fore_color.rgb = NARANJA_AGROSUPER
            franja_lima.line.fill.background()

            # Logo Agrosuper grande en el panel derecho azul
            if os.path.exists(logo_path):
                self._insertar_imagen_encuadrada(slide, logo_path, Inches(9.1), Inches(1.2), Inches(3.6), Inches(1.4))

            # Si está el logo del cerdo, también luce excelente en el centro-abajo del panel derecho
            if os.path.exists(logo_cerdo):
                card_ilust = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(3.0), Inches(3.8), Inches(3.4))
                card_ilust.fill.solid()
                card_ilust.fill.fore_color.rgb = BLANCO
                card_ilust.line.fill.background()
                self._insertar_imagen_encuadrada(slide, logo_cerdo, Inches(9.15), Inches(3.15), Inches(3.5), Inches(3.1))

            tb = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(7.2), Inches(4.8))
            tf = tb.text_frame
            tf.word_wrap = True

            p0 = tf.paragraphs[0]
            p0.text = f"Reporte Ejecutivo de Ventilación\n{datos_usuario.get('semana', 'SEMANA 44')}: Cerdos Reproductores"
            p0.font.size = Pt(34)
            p0.font.bold = True
            p0.font.color.rgb = GAMMA_TITULO

            p1 = tf.add_paragraph()
            p1.text = f"\nComparativa de Alertas QA, Disponibilidad InfluxDB y Contingencias\nPeriodo: {datos_pdf['periodo']}"
            p1.font.size = Pt(15)
            p1.font.color.rgb = TEXTO_GRIS

            # Etiquetas tipo píldora abajo como en Gamma
            tag1 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.5), Inches(4.5), Inches(0.48))
            tag1.fill.solid()
            tag1.fill.fore_color.rgb = GAMMA_CAJA_SUAVE
            tag1.line.color.rgb = GAMMA_VERDE_OSCURO
            p_t1 = tag1.text_frame.paragraphs[0]
            p_t1.text = "AGROSUPER 2026 | EQUIPO TÉCNICO VENTILACIÓN"
            p_t1.font.size = Pt(10)
            p_t1.font.bold = True
            p_t1.font.color.rgb = GAMMA_VERDE_OSCURO
            p_t1.alignment = PP_ALIGN.CENTER

        else:
            # =========================================================================
            # PORTADA CORPORATIVA AGROSUPER MEJORADA (Sin vacío visual + Cerdo Grande)
            # =========================================================================
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            bg.fill.solid()
            bg.fill.fore_color.rgb = AZUL_AGROSUPER
            bg.line.fill.background()

            # Franja lateral Naranja más estilizada
            franja = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.5), Inches(7.5))
            franja.fill.solid()
            franja.fill.fore_color.rgb = NARANJA_AGROSUPER
            franja.line.fill.background()

            # Segunda línea fina de acento
            franja2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.62), 0, Inches(0.08), Inches(7.5))
            franja2.fill.solid()
            franja2.fill.fore_color.rgb = NARANJA_AGROSUPER
            franja2.line.fill.background()

            # Logo Agrosuper Blanco Grande arriba a la derecha
            if os.path.exists(logo_path):
                self._insertar_imagen_encuadrada(slide, logo_path, Inches(9.2), Inches(0.25), Inches(3.2), Inches(1.05))

            # Tarjeta blanca principal más amplia y equilibrada
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.15), Inches(1.4), Inches(11.35), Inches(5.35))
            card.fill.solid()
            card.fill.fore_color.rgb = BLANCO
            card.line.color.rgb = NARANJA_AGROSUPER
            card.line.width = Pt(2)

            # Barra decorativa interna izquierda dentro de la tarjeta blanca
            barra_int = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.6), Inches(1.95), Inches(0.1), Inches(3.0))
            barra_int.fill.solid()
            barra_int.fill.fore_color.rgb = NARANJA_AGROSUPER
            barra_int.line.fill.background()

            # Textos principales (Columna Izquierda de la Portada)
            tb = slide.shapes.add_textbox(Inches(1.85), Inches(1.85), Inches(5.8), Inches(3.4))
            tf = tb.text_frame
            tf.word_wrap = True

            p0 = tf.paragraphs[0]
            p0.text = "TORRE DE CONTROL REPRODUCTORA CERDOS"
            p0.font.size = Pt(12)
            p0.font.bold = True
            p0.font.color.rgb = NARANJA_AGROSUPER

            p1 = tf.add_paragraph()
            p1.text = "REPORTE EJECUTIVO\nDE VENTILACIÓN"
            p1.font.size = Pt(32)
            p1.font.bold = True
            p1.font.color.rgb = AZUL_AGROSUPER

            p_sem = tf.add_paragraph()
            p_sem.text = f"\n{datos_usuario.get('semana', 'SEMANA 44').upper()}"
            p_sem.font.size = Pt(22)
            p_sem.font.bold = True
            p_sem.font.color.rgb = NARANJA_AGROSUPER

            # Tarjetas inferiores de metadatos (eliminan el vacío de abajo)
            box_per = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.6), Inches(5.35), Inches(2.9), Inches(0.95))
            box_per.fill.solid()
            box_per.fill.fore_color.rgb = FONDO_GRIS_CLARO
            box_per.line.color.rgb = BORDE_SUAVE
            tf_per = box_per.text_frame
            tf_per.word_wrap = True
            p_bp1 = tf_per.paragraphs[0]
            p_bp1.text = "PERIODO ANALIZADO"
            p_bp1.font.size = Pt(9)
            p_bp1.font.bold = True
            p_bp1.font.color.rgb = TEXTO_GRIS
            p_bp2 = tf_per.add_paragraph()
            p_bp2.text = datos_pdf["periodo"]
            p_bp2.font.size = Pt(11.5)
            p_bp2.font.bold = True
            p_bp2.font.color.rgb = AZUL_AGROSUPER

            box_resp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.7), Inches(5.35), Inches(3.0), Inches(0.95))
            box_resp.fill.solid()
            box_resp.fill.fore_color.rgb = FONDO_GRIS_CLARO
            box_resp.line.color.rgb = BORDE_SUAVE
            tf_resp = box_resp.text_frame
            tf_resp.word_wrap = True
            p_br1 = tf_resp.paragraphs[0]
            p_br1.text = "RESPONSABLE TÉCNICO"
            p_br1.font.size = Pt(9)
            p_br1.font.bold = True
            p_br1.font.color.rgb = TEXTO_GRIS
            p_br2 = tf_resp.add_paragraph()
            p_br2.text = datos_usuario.get("autor", "Alex Retamal Lobos")
            p_br2.font.size = Pt(11.5)
            p_br2.font.bold = True
            p_br2.font.color.rgb = AZUL_AGROSUPER

            # Logo del Cerdo y Ventilador BIEN GRANDE a la derecha (4.3 x 4.2 pulgadas)
            if os.path.exists(logo_cerdo):
                self._insertar_imagen_encuadrada(
                    slide,
                    logo_cerdo,
                    left=Inches(7.85),
                    top=Inches(1.85),
                    max_w=Inches(4.35),
                    max_h=Inches(4.4)
                )

    def _slide_2_kpis_y_alertas(self, datos_pdf: dict, ruta_graf_comp: str):
        slide = self.prs.slides.add_slide(self.blank_layout)
        self._aplicar_encabezado(
            slide,
            "1. Resumen Ejecutivo de Alertas y Telemetría",
            f"Indicadores generales QA e InfluxDB | Periodo: {datos_pdf['periodo']}"
        )

        kpis = [
            ("Alertas Totales QA", datos_pdf["alertas_totales"], f"▼ {datos_pdf['variacion_alertas']} vs sem. anterior ({datos_pdf['alertas_por_dia']}/día)", self.color_primario),
            ("Disponibilidad Real", datos_pdf["disponibilidad_real"], f"▲ Anterior: {datos_pdf['disp_anterior']} (InfluxDB)", self.color_primario),
            ("Nidos Activos", datos_pdf["nidos_activos"], "Lectura válida >95% del tiempo", self.color_secundario),
            ("Tiempo Fuera Rango", datos_pdf["tiempo_fuera_rango"], f"▲ Periodo anterior: {datos_pdf['t_fuera_rango_ant']}", ROJO_CRITICO),
            ("Desconexiones Grupo", datos_pdf["desconexiones_totales"], f"Acumulado: {datos_pdf['horas_desconexion']} sin datos", self.color_secundario),
            ("Fallas de Sonda", datos_pdf["fallas_sonda"], "Alertas nivel D2 detectadas", self.color_secundario),
        ]

        start_x, start_y = Inches(0.5), Inches(1.35)
        card_w, card_h = Inches(2.85), Inches(1.6)
        gap_x, gap_y = Inches(0.25), Inches(0.2)

        for idx, (tit, val, sub, col) in enumerate(kpis):
            row = idx // 2
            col_idx = idx % 2
            x = start_x + col_idx * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            self._crear_tarjeta_kpi(slide, x, y, card_w, card_h, tit, val, sub, col)

        chart_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.65), Inches(1.35), Inches(6.2), Inches(5.2))
        chart_card.fill.solid()
        chart_card.fill.fore_color.rgb = BLANCO
        chart_card.line.color.rgb = BORDE_SUAVE

        self._insertar_imagen_encuadrada(slide, ruta_graf_comp, Inches(6.8), Inches(1.5), Inches(5.9), Inches(4.9))

        # Si es estilo Gamma, agregamos la barra inferior de conclusión como en la lámina 3 de Chanchillas
        if self.estilo == "gamma":
            call_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(6.68), Inches(12.35), Inches(0.55))
            call_box.fill.solid()
            call_box.fill.fore_color.rgb = GAMMA_CAJA_SUAVE
            call_box.line.color.rgb = GAMMA_VERDE_OSCURO
            p_c = call_box.text_frame.paragraphs[0]
            p_c.text = f"Síntesis: Las alertas diarias bajaron un {datos_pdf['variacion_alertas']} respecto a la semana previa, alcanzando {datos_pdf['disponibilidad_real']} de lecturas válidas en InfluxDB."
            p_c.font.size = Pt(11)
            p_c.font.bold = True
            p_c.font.color.rgb = GAMMA_VERDE_OSCURO

    def _slide_3_disponibilidad_grupos(self, datos_pdf: dict, ruta_graf_sem: str):
        slide = self.prs.slides.add_slide(self.blank_layout)
        self._aplicar_encabezado(
            slide,
            "2. Disponibilidad de Datos y Semáforo por Grupo",
            "Porcentaje de intervalos válidos cada 15 min en los 250 nidos configurados"
        )

        left_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), Inches(7.1), Inches(5.5))
        left_card.fill.solid()
        left_card.fill.fore_color.rgb = BLANCO
        left_card.line.color.rgb = BORDE_SUAVE
        self._insertar_imagen_encuadrada(slide, ruta_graf_sem, Inches(0.65), Inches(1.5), Inches(6.8), Inches(5.3))

        right_card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.85), Inches(1.4), Inches(5.0), Inches(5.5))
        right_card.fill.solid()
        right_card.fill.fore_color.rgb = GAMMA_CAJA_SUAVE if self.estilo == "gamma" else BLANCO
        right_card.line.color.rgb = self.color_primario if self.estilo == "gamma" else ROJO_CRITICO
        right_card.line.width = Pt(2)

        tb = slide.shapes.add_textbox(Inches(8.1), Inches(1.6), Inches(4.5), Inches(5.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = "DIAGNÓSTICO DE GRUPOS CRÍTICOS"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = self.color_primario if self.estilo == "gamma" else ROJO_CRITICO

        puntos = [
            f"• Grupos en Estado Crítico:\n  {datos_pdf['grupos_criticos_texto']}",
            "• Brecha Alertas vs Realidad:\n  49 alertas 'sin datos' quedaron abiertas en plataforma pese a reconexión (Disponibilidad por alertas: 64,6% vs Real InfluxDB: 85,3%).",
            "• Nidos Sin Lectura (Valor 0):\n  7 nidos reportaron 0 lecturas válidas (6 corresponden al Nido 2 de cada sala del Grupo 28 sin sonda conectada).",
            "• Prioridad de Intervención:\n  Revisar conectividad en Grupo 20 (12,9%) y Grupo 28 (48,6%)."
        ]

        for punto in puntos:
            p_item = tf.add_paragraph()
            p_item.text = "\n" + punto
            p_item.font.size = Pt(11.5)
            p_item.font.color.rgb = TEXTO_OSCURO

    def _slide_4_focos_criticos_terreno(self, datos_pdf: dict):
        slide = self.prs.slides.add_slide(self.blank_layout)
        self._aplicar_encabezado(
            slide,
            "3. Focos Críticos en Terreno: Desconexiones y Temperatura",
            "Análisis de caídas simultáneas y nidos con mayor desviación térmica"
        )

        c1 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), Inches(6.0), Inches(5.5))
        c1.fill.solid()
        c1.fill.fore_color.rgb = BLANCO
        c1.line.color.rgb = self.color_primario
        c1.line.width = Pt(1.5)

        tb1 = slide.shapes.add_textbox(Inches(0.75), Inches(1.65), Inches(5.5), Inches(5.0))
        tf1 = tb1.text_frame
        tf1.word_wrap = True
        p1 = tf1.paragraphs[0]
        p1.text = "PATRÓN DE DESCONEXIONES Y RED"
        p1.font.size = Pt(15)
        p1.font.bold = True
        p1.font.color.rgb = self.color_primario

        items_red = [
            f"• Total Desconexiones de Grupo: {datos_pdf['desconexiones_totales']} eventos ({datos_pdf['horas_desconexion']} acumuladas).",
            "• Concentración por Grupo:\n  Grupo 20 lidera con 35 caídas (148,2 h), seguido de Grupo 10 (35,0 h) y Grupo 26 (12,2 h).",
            "• Caídas Simultáneas (Falla Común):\n  7 eventos con 3 o más grupos caídos en simultáneo (causa atribuible a red/plataforma central y no a terreno).",
            "• Horario Crítico de Cortes:\n  El 66% de los cortes >30 min inicia en horario laboral (08:00 a 17:59 hrs, peak a las 10:00 hrs)."
        ]
        for it in items_red:
            p = tf1.add_paragraph()
            p.text = "\n" + it
            p.font.size = Pt(12)
            p.font.color.rgb = TEXTO_OSCURO

        c2 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.4), Inches(6.0), Inches(5.5))
        c2.fill.solid()
        c2.fill.fore_color.rgb = BLANCO
        c2.line.color.rgb = self.color_secundario
        c2.line.width = Pt(1.5)

        tb2 = slide.shapes.add_textbox(Inches(7.05), Inches(1.65), Inches(5.5), Inches(5.0))
        tf2 = tb2.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = "RANKING DE SALAS Y NIDOS FUERA DE RANGO"
        p2.font.size = Pt(15)
        p2.font.bold = True
        p2.font.color.rgb = self.color_primario if self.estilo == "gamma" else NARANJA_AGROSUPER

        items_temp = [
            f"• Exposición Térmica Global:\n  Los nidos operaron fuera de rango el {datos_pdf['tiempo_fuera_rango']} del tiempo (192 de 250 nidos presentaron al menos 1 alerta).",
            f"• Nidos más Críticos del Periodo:\n  {datos_pdf['peores_nidos_texto']}",
            "• Salas con Mayor Volumen de Eventos Únicos:\n  - Grupo 22 | PAB13 Mat 2 (88 alertas: 56 falla sonda)\n  - Grupo 8  | PAB01 Mat 5 (69 alertas: 59 T° fuera rango)\n  - Grupo 25 | PAB16 Mat 8 (57 alertas: 142 hrs fuera rango)"
        ]
        for it in items_temp:
            p = tf2.add_paragraph()
            p.text = "\n" + it
            p.font.size = Pt(12)
            p.font.color.rgb = TEXTO_OSCURO

    def _slide_5_gestion_y_reuniones(self, datos_usuario: dict):
        slide = self.prs.slides.add_slide(self.blank_layout)
        self._aplicar_encabezado(
            slide,
            "4. Gestión Técnica Semanal, Reuniones y Mejoras",
            "Seguimiento de problemáticas operativas, acuerdos con proveedores y calibraciones"
        )

        img_obs = datos_usuario.get("foto_observaciones", "")
        ancho_texto = Inches(6.8) if (img_obs and os.path.exists(img_obs)) else Inches(12.3)

        card_txt = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), ancho_texto, Inches(5.5))
        card_txt.fill.solid()
        card_txt.fill.fore_color.rgb = BLANCO
        card_txt.line.color.rgb = BORDE_SUAVE

        tb = slide.shapes.add_textbox(Inches(0.8), Inches(1.65), ancho_texto - Inches(0.6), Inches(5.0))
        tf = tb.text_frame
        tf.word_wrap = True

        p_tit = tf.paragraphs[0]
        p_tit.text = "BITÁCORA DE GESTIÓN Y ACUERDOS TÉCNICOS"
        p_tit.font.size = Pt(16)
        p_tit.font.bold = True
        p_tit.font.color.rgb = self.color_primario

        lineas = [l.strip() for l in datos_usuario.get("texto_observaciones", "").split("\n") if l.strip()]
        for linea in lineas:
            p = tf.add_paragraph()
            prefijo = "• " if not linea.startswith(("-", "•", "1.", "2.", "3.")) else ""
            p.text = f"\n{prefijo}{linea}"
            p.font.size = Pt(12.5)
            p.font.color.rgb = TEXTO_OSCURO

        if img_obs and os.path.exists(img_obs):
            card_img = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.55), Inches(1.4), Inches(5.25), Inches(5.5))
            card_img.fill.solid()
            card_img.fill.fore_color.rgb = BLANCO
            card_img.line.color.rgb = BORDE_SUAVE
            self._insertar_imagen_encuadrada(slide, img_obs, Inches(7.7), Inches(1.55), Inches(4.95), Inches(5.2))

    def _slide_6_emergencias_y_fotos(self, datos_usuario: dict):
        slide = self.prs.slides.add_slide(self.blank_layout)
        self._aplicar_encabezado(
            slide,
            "5. Reporte de Emergencias y Contingencias en Terreno",
            "Incidentes críticos de la semana, diagnóstico de causa raíz y plan de acción"
        )

        card_izq = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), Inches(6.2), Inches(5.5))
        card_izq.fill.solid()
        card_izq.fill.fore_color.rgb = BLANCO
        card_izq.line.color.rgb = ROJO_CRITICO
        card_izq.line.width = Pt(1.5)

        tb = slide.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(5.7), Inches(5.1))
        tf = tb.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = f"INCIDENTE: {datos_usuario.get('titulo_emergencia', 'Contingencia Operativa').upper()}"
        p0.font.size = Pt(14)
        p0.font.bold = True
        p0.font.color.rgb = ROJO_CRITICO

        p_desc_tit = tf.add_paragraph()
        p_desc_tit.text = "\nDiagnóstico e Impacto:"
        p_desc_tit.font.size = Pt(12)
        p_desc_tit.font.bold = True
        p_desc_tit.font.color.rgb = self.color_primario

        for l in [x.strip() for x in datos_usuario.get("detalle_emergencia", "").split("\n") if x.strip()]:
            p = tf.add_paragraph()
            p.text = f"• {l}" if not l.startswith(("•", "-")) else l
            p.font.size = Pt(11)
            p.font.color.rgb = TEXTO_OSCURO

        p_acc_tit = tf.add_paragraph()
        p_acc_tit.text = "\nAcciones Correctivas / Preventivas:"
        p_acc_tit.font.size = Pt(12)
        p_acc_tit.font.bold = True
        p_acc_tit.font.color.rgb = VERDE_OK

        for l in [x.strip() for x in datos_usuario.get("acciones_emergencia", "").split("\n") if x.strip()]:
            p = tf.add_paragraph()
            p.text = f"✓ {l}" if not l.startswith(("✓", "•", "-")) else l
            p.font.size = Pt(11)
            p.font.color.rgb = TEXTO_OSCURO

        fotos = [f for f in datos_usuario.get("fotos_emergencia", []) if os.path.exists(f)]
        card_der = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.95), Inches(1.4), Inches(5.85), Inches(5.5))
        card_der.fill.solid()
        card_der.fill.fore_color.rgb = BLANCO
        card_der.line.color.rgb = BORDE_SUAVE

        if len(fotos) == 1:
            self._insertar_imagen_encuadrada(slide, fotos[0], Inches(7.15), Inches(1.6), Inches(5.45), Inches(5.1))
        elif len(fotos) == 2:
            self._insertar_imagen_encuadrada(slide, fotos[0], Inches(7.15), Inches(1.6), Inches(5.45), Inches(2.45))
            self._insertar_imagen_encuadrada(slide, fotos[1], Inches(7.15), Inches(4.25), Inches(5.45), Inches(2.45))
        elif len(fotos) >= 3:
            self._insertar_imagen_encuadrada(slide, fotos[0], Inches(7.15), Inches(1.6), Inches(2.65), Inches(2.45))
            self._insertar_imagen_encuadrada(slide, fotos[1], Inches(9.95), Inches(1.6), Inches(2.65), Inches(2.45))
            self._insertar_imagen_encuadrada(slide, fotos[2], Inches(7.15), Inches(4.25), Inches(5.45), Inches(2.45))
        else:
            tb_empty = slide.shapes.add_textbox(Inches(7.5), Inches(3.8), Inches(4.8), Inches(1.0))
            p_emp = tb_empty.text_frame.paragraphs[0]
            p_emp.text = "Sin fotografías adjuntas para esta semana"
            p_emp.alignment = PP_ALIGN.CENTER
            p_emp.font.color.rgb = TEXTO_GRIS