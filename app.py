import os
import tempfile
import streamlit as st

from core.pdf_extractor import TecnoandinaPDFExtractor
from core.ppt_generator import ExecutivePPTGenerator

# Configuración de página con branding Agrosuper
st.set_page_config(
    page_title="Generador de Reportes - Agrosuper",
    page_icon="assets/logo_cerdo_ventilacion.png" if os.path.exists("assets/logo_cerdo_ventilacion.png") else "📊",
    layout="wide"
)

# Estilo visual corporativo (Azul #1B365D y Naranja #E87722)
st.markdown("""
    <style>
    .main-header {
        background-color: #1B365D;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-bottom: 5px solid #E87722;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 26px;
    }
    .main-header p {
        color: #CBD5E1;
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    .stButton>button {
        background-color: #E87722;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 24px;
        border-radius: 6px;
    }
    .stButton>button:hover {
        background-color: #D96B27;
        color: white;
    }
    </style>
    <div class="main-header">
        <h1>¡Hola Alex Retamal! 👋</h1>
        <p>Generador Automático de Presentaciones Ejecutivas | Ventilación Reproductora Agrosuper</p>
    </div>
""", unsafe_allow_html=True)

# ----------------- Formulario de Parámetros -----------------
col_config1, col_config2 = st.columns(2)

with col_config1:
    semana_val = st.text_input("Nombre de la Semana:", value="SEMANA 45")

with col_config2:
    estilo_ppt = st.radio(
        "Estilo Visual de la Presentación:",
        options=["agrosuper", "gamma"],
        format_func=lambda x: "Corporativo Agrosuper (Azul / Naranja)" if x == "agrosuper" else "Minimalista Gamma (Verde / Editorial)",
        horizontal=True
    )

tab1, tab2, tab3 = st.tabs([
    "📄 1. Reporte PDF Tecnoandina",
    "📝 2. Reuniones y Observaciones",
    "🚨 3. Emergencias y Fotos"
])

# Tab 1: Carga de Archivo PDF
with tab1:
    st.subheader("Cargar Resumen Semanal de Alertas")
    uploaded_pdf = st.file_uploader("Selecciona el archivo PDF de Tecnoandina", type=["pdf"])
    if uploaded_pdf:
        st.success(f"PDF cargado: {uploaded_pdf.name}")
    else:
        st.info("Si no adjuntas un PDF, se generará la presentación usando los datos del template base.")

# Tab 2: Notas y Bitácora
with tab2:
    st.subheader("Bitácora de Gestión y Acuerdos Técnicos (Lámina 5)")
    texto_obs_default = (
        "1. Alertas sin datos generales (Sondas y Nidos): Reunión coordinada con técnicos de Fancom para desbloquear restricciones y revisar recepción de datos.\n"
        "2. Alertas por nidos fuera de rango (> ±3 °C): Pendiente confirmación del área de Reproductoras para ampliar rangos operativos sin afectar bienestar animal.\n"
        "3. Alertas por nidos en límite absoluto (> 46 °C a 57 °C): Se detectó ubicación heterogénea de sensores (alimentación vs retorno). Se reubicará sensor en Grupo 9 como piloto."
    )
    texto_observaciones = st.text_area("Observaciones técnicas (una por línea):", value=texto_obs_default, height=160)
    uploaded_foto_obs = st.file_uploader("Captura o gráfico opcional (ej. Grafana)", type=["png", "jpg", "jpeg"], key="foto_obs")

# Tab 3: Emergencias y Fotos de Terreno
with tab3:
    st.subheader("Reporte de Emergencias y Contingencias (Lámina 6)")
    titulo_emergencia = st.text_input("Título de la Emergencia:", value="Falla Eléctrica Grupo 9 (Roedor en Cable FSU4) y Corte en Testaje")

    col_em1, col_em2 = st.columns(2)
    with col_em1:
        detalle_def = (
            "Grupo 9 presentó cortocircuito por cable de sensor de tapete eléctrico dañado por roedor.\n"
            "Daño en puerto principal de pantalla FSU4, afectando tapetes y extractores variables en salas 5 y 6 (en parto).\n"
            "En Testaje se registró corte eléctrico en Pabellón 1 generando encierro temporal."
        )
        detalle_emergencia = st.text_area("Diagnóstico e Impacto Operativo:", value=detalle_def, height=140)

    with col_em2:
        acciones_def = (
            "Reemplazo de cable dañado por acción de roedores y revisión electrónica de placa FSU4.\n"
            "Verificación operativa de tapetes eléctricos y extractores variables en salas 5 y 6.\n"
            "Coordinación con equipo de Mantención en Testaje para medidas correctivas post-corte."
        )
        acciones_emergencia = st.text_area("Acciones Correctivas / Preventivas:", value=acciones_def, height=140)

    uploaded_fotos_eme = st.file_uploader("Fotos de evidencia en terreno (máx. 3)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# ----------------- Procesamiento y Descarga -----------------
st.divider()

if st.button("⚡ GENERAR PRESENTACIÓN EJECUTIVA (.PPTX)", use_container_width=True):
    with st.spinner("Procesando datos del PDF y maquetando diapositivas..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Guardar y procesar PDF (o usar template por defecto si no se adjuntó)
            if uploaded_pdf is not None:
                pdf_temp_path = os.path.join(temp_dir, "reporte.pdf")
                with open(pdf_temp_path, "wb") as f:
                    f.write(uploaded_pdf.getbuffer())
                extractor = TecnoandinaPDFExtractor(pdf_temp_path)
            else:
                extractor = TecnoandinaPDFExtractor("")

            datos_pdf = extractor.extraer_datos()

            # 2. Guardar imagen de observaciones si existe
            ruta_foto_obs = ""
            if uploaded_foto_obs is not None:
                ruta_foto_obs = os.path.join(temp_dir, uploaded_foto_obs.name)
                with open(ruta_foto_obs, "wb") as f:
                    f.write(uploaded_foto_obs.getbuffer())

            # 3. Guardar fotos de emergencias
            rutas_fotos_eme = []
            if uploaded_fotos_eme:
                for idx, foto in enumerate(uploaded_fotos_eme[:3]):
                    fpath = os.path.join(temp_dir, f"emergencia_{idx}_{foto.name}")
                    with open(fpath, "wb") as f:
                        f.write(foto.getbuffer())
                    rutas_fotos_eme.append(fpath)

            datos_usuario = {
                "autor": "Alex Retamal Lobos",
                "semana": semana_val,
                "texto_observaciones": texto_observaciones,
                "foto_observaciones": ruta_foto_obs,
                "titulo_emergencia": titulo_emergencia,
                "detalle_emergencia": detalle_emergencia,
                "acciones_emergencia": acciones_emergencia,
                "fotos_emergencia": rutas_fotos_eme
            }

            # 4. Generar PPTX
            output_pptx = os.path.join(temp_dir, "presentacion.pptx")
            generador = ExecutivePPTGenerator(output_pptx, estilo=estilo_ppt)
            generador.generar_presentacion_completa(datos_pdf, datos_usuario)

            with open(output_pptx, "rb") as f:
                pptx_bytes = f.read()

        sufijo = "Gamma" if estilo_ppt == "gamma" else "Agrosuper"
        nombre_salida = f"Reporte_{sufijo}_{semana_val.replace(' ', '_')}.pptx"

        st.success(f"✅ ¡Presentación generada exitosamente! (Periodo detectado: {datos_pdf['periodo']})")
        st.download_button(
            label="📥 DESCARGAR REPORTE POWERPOINT (.PPTX)",
            data=pptx_bytes,
            file_name=nombre_salida,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )