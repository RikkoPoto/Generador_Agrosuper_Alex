import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.pdf_extractor import TecnoandinaPDFExtractor
from core.ppt_generator import ExecutivePPTGenerator


class AgrosuperAppUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Automatizador de Presentaciones Ejecutivas - Agrosuper")
        self.root.geometry("960x780")
        self.root.configure(bg="#F1F5F9")

        # Variables de estado
        self.ruta_pdf = tk.StringVar(value="")
        self.ruta_foto_obs = tk.StringVar(value="")
        self.lista_fotos_emergencia = []
        self.semana_var = tk.StringVar(value="SEMANA 44")
        self.estilo_ppt_var = tk.StringVar(value="gamma")  # 'agrosuper' o 'gamma'
        self.titulo_emergencia_var = tk.StringVar(value="Falla Eléctrica Grupo 9 (Roedor en Cable FSU4) y Corte en Testaje")

        self._configurar_estilos()
        self._construir_interfaz()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#F1F5F9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 8], background="#CBD5E1", foreground="#1E293B")
        style.map("TNotebook.Tab", background=[("selected", "#1B365D")], foreground=[("selected", "#FFFFFF")])

    def _construir_interfaz(self):
        # ================= BANNER SUPERIOR =================
        banner = tk.Frame(self.root, bg="#1B365D", height=85)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        franja_naranja = tk.Frame(self.root, bg="#E87722", height=5)
        franja_naranja.pack(fill="x")

        lbl_saludo = tk.Label(
            banner,
            text="¡Hola Alex Retamal! 👋",
            font=("Segoe UI", 20, "bold"),
            bg="#1B365D",
            fg="#FFFFFF"
        )
        lbl_saludo.pack(anchor="w", padx=25, pady=(12, 0))

        lbl_sub = tk.Label(
            banner,
            text="Generador Automático de Presentaciones Ejecutivas  |  Ventilación Reproductora Agrosuper",
            font=("Segoe UI", 10),
            bg="#1B365D",
            fg="#CBD5E1"
        )
        lbl_sub.pack(anchor="w", padx=25)

        # ================= CONTENEDOR CENTRAL (TABS) =================
        main_container = tk.Frame(self.root, bg="#F1F5F9", padx=20, pady=15)
        main_container.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True)

        tab_pdf = tk.Frame(notebook, bg="#FFFFFF", padx=20, pady=20)
        notebook.add(tab_pdf, text="  1. Reporte PDF y Estilo (Láminas 1 a 4)  ")
        self._armar_tab_pdf(tab_pdf)

        tab_obs = tk.Frame(notebook, bg="#FFFFFF", padx=20, pady=20)
        notebook.add(tab_obs, text="  2. Reuniones y Observaciones (Lámina 5)  ")
        self._armar_tab_observaciones(tab_obs)

        tab_eme = tk.Frame(notebook, bg="#FFFFFF", padx=20, pady=20)
        notebook.add(tab_eme, text="  3. Emergencias y Fotos (Lámina 6)  ")
        self._armar_tab_emergencias(tab_eme)

        # ================= FOOTER CON BOTÓN DE ACCIÓN =================
        footer = tk.Frame(self.root, bg="#E2E8F0", height=70, padx=25)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.lbl_estado = tk.Label(
            footer,
            text="Listo para generar. Elige el diseño y presiona el botón naranja.",
            font=("Segoe UI", 10),
            bg="#E2E8F0",
            fg="#334155"
        )
        self.lbl_estado.pack(side="left", pady=20)

        btn_generar = tk.Button(
            footer,
            text="⚡ GENERAR PRESENTACIÓN  (.PPTX)",
            font=("Segoe UI", 11, "bold"),
            bg="#E87722",
            fg="#FFFFFF",
            activebackground="#D96B27",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self._ejecutar_generacion
        )
        btn_generar.pack(side="right", pady=12)

    def _armar_tab_pdf(self, parent):
        tk.Label(parent, text="Configuración General, Estilo Visual y Telemetría", font=("Segoe UI", 13, "bold"), bg="#FFFFFF", fg="#1B365D").pack(anchor="w", pady=(0, 10))

        frm_sem = tk.Frame(parent, bg="#FFFFFF")
        frm_sem.pack(fill="x", pady=5)
        tk.Label(frm_sem, text="Nombre de la Semana (Portada):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", width=28, anchor="w").pack(side="left")
        tk.Entry(frm_sem, textvariable=self.semana_var, font=("Segoe UI", 10), width=35, bg="#F8FAFC", relief="solid", bd=1).pack(side="left", padx=5)

        # Selector de Estilo Visual (Agrosuper vs Gamma)
        frm_estilo = tk.LabelFrame(parent, text=" 🎨 Selecciona el Diseño de la Presentación ", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1B365D", padx=15, pady=12)
        frm_estilo.pack(fill="x", pady=10)

        tk.Radiobutton(
            frm_estilo,
            text="Estilo 1: Corporativo Agrosuper (Barra Azul Marino, Acentos Naranjas y Logo Institucional)",
            variable=self.estilo_ppt_var,
            value="agrosuper",
            font=("Segoe UI", 10, "bold"),
            bg="#F8FAFC",
            fg="#1B365D",
            activebackground="#F8FAFC"
        ).pack(anchor="w", pady=3)

        tk.Radiobutton(
            frm_estilo,
            text="Estilo 2: Minimalista - Estilo Gamma (Editorial Limpio, Tarjetas Verde Esmeralda / Lima)",
            variable=self.estilo_ppt_var,
            value="gamma",
            font=("Segoe UI", 10, "bold"),
            bg="#F8FAFC",
            fg="#118B50",
            activebackground="#F8FAFC"
        ).pack(anchor="w", pady=3)

        frm_file = tk.LabelFrame(parent, text=" 📄 Archivo PDF de Tecnoandina (Resumen Semanal de Alertas) ", font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#1B365D", padx=15, pady=12)
        frm_file.pack(fill="x", pady=10)

        tk.Entry(frm_file, textvariable=self.ruta_pdf, font=("Segoe UI", 10), width=65, state="readonly").pack(side="left", padx=(0, 10), ipady=4)
        tk.Button(
            frm_file, text="📂 Buscar PDF...", font=("Segoe UI", 10, "bold"),
            bg="#1B365D", fg="#FFFFFF", relief="flat", padx=12, pady=4, cursor="hand2",
            command=self._seleccionar_pdf
        ).pack(side="left")

        info_box = tk.Label(
            parent,
            text=(
                "💡 ¿Qué hace este módulo automáticamente?\n"
                "• Extrae Alertas Totales, Disponibilidad InfluxDB, Nidos Activos y Falla de Sondas.\n"
                "• Construye los gráficos comparativos y semáforo adaptados a la paleta del estilo elegido."
            ),
            font=("Segoe UI", 10), bg="#EFF6FF", fg="#1E3A8A", justify="left", padx=15, pady=12, relief="solid", bd=1
        )
        info_box.pack(fill="x", pady=8)

    def _armar_tab_observaciones(self, parent):
        tk.Label(parent, text="Reuniones, Calibraciones y Problemáticas Generales (Lámina 5)", font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#1B365D").pack(anchor="w")
        tk.Label(parent, text="Escribe un punto por línea. El sistema lo maquetará en tarjetas ejecutivas:", font=("Segoe UI", 10), bg="#FFFFFF", fg="#64748B").pack(anchor="w", pady=(0, 8))

        self.txt_observaciones = tk.Text(parent, height=12, font=("Segoe UI", 10), bg="#F8FAFC", relief="solid", bd=1, padx=10, pady=10)
        self.txt_observaciones.pack(fill="both", expand=True, pady=5)

        texto_ejemplo_obs = (
            "1. Alertas sin datos generales (Sondas y Nidos): Reunión coordinada con técnicos de Fancom para desbloquear restricciones y revisar recepción de datos.\n"
            "2. Alertas por nidos fuera de rango (> ±3 °C): Pendiente confirmación del área de Reproductoras para ampliar rangos operativos sin afectar bienestar animal.\n"
            "3. Alertas por nidos en límite absoluto (> 46 °C a 57 °C): Se detectó ubicación heterogénea de sensores (alimentación vs retorno). Se reubicará sensor en Grupo 9 como piloto."
        )
        self.txt_observaciones.insert("1.0", texto_ejemplo_obs)

        frm_img_obs = tk.Frame(parent, bg="#FFFFFF")
        frm_img_obs.pack(fill="x", pady=10)
        tk.Label(frm_img_obs, text="Captura o Gráfico Opcional (ej. Grafana):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF").pack(side="left")
        tk.Entry(frm_img_obs, textvariable=self.ruta_foto_obs, font=("Segoe UI", 9), width=45, state="readonly").pack(side="left", padx=10)
        tk.Button(frm_img_obs, text="🖼️ Adjuntar Imagen", bg="#475569", fg="#FFFFFF", relief="flat", padx=10, command=self._seleccionar_foto_obs).pack(side="left")

    def _armar_tab_emergencias(self, parent):
        frm_top = tk.Frame(parent, bg="#FFFFFF")
        frm_top.pack(fill="x", pady=(0, 8))
        tk.Label(frm_top, text="Título de la Emergencia:", font=("Segoe UI", 10, "bold"), bg="#FFFFFF").pack(side="left")
        tk.Entry(frm_top, textvariable=self.titulo_emergencia_var, font=("Segoe UI", 10), width=60, bg="#F8FAFC", relief="solid", bd=1).pack(side="left", padx=10)

        tk.Label(parent, text="Diagnóstico e Impacto Operativo (1 viñeta por línea):", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#1B365D").pack(anchor="w")
        self.txt_eme_detalle = tk.Text(parent, height=5, font=("Segoe UI", 10), bg="#F8FAFC", relief="solid", bd=1, padx=8, pady=6)
        self.txt_eme_detalle.pack(fill="x", pady=(2, 8))
        self.txt_eme_detalle.insert("1.0", (
            "Grupo 9 presentó cortocircuito por cable de sensor de tapete eléctrico dañado por roedor.\n"
            "Daño en puerto principal de pantalla FSU4, afectando tapetes y extractores variables en salas 5 y 6 (en parto).\n"
            "En Testaje se registró corte eléctrico en Pabellón 1 generando encierro temporal."
        ))

        tk.Label(parent, text="Acciones Correctivas y Preventivas Realizadas:", font=("Segoe UI", 10, "bold"), bg="#FFFFFF", fg="#16A34A").pack(anchor="w")
        self.txt_eme_acciones = tk.Text(parent, height=5, font=("Segoe UI", 10), bg="#F8FAFC", relief="solid", bd=1, padx=8, pady=6)
        self.txt_eme_acciones.pack(fill="x", pady=(2, 8))
        self.txt_eme_acciones.insert("1.0", (
            "Reemplazo de cable dañado por acción de roedores y revisión electrónica de placa FSU4.\n"
            "Verificación operativa de tapetes eléctricos y extractores variables en salas 5 y 6.\n"
            "Coordinación con equipo de Mantención en Testaje para medidas correctivas post-corte."
        ))

        frm_fotos = tk.Frame(parent, bg="#F8FAFC", padx=10, pady=8, relief="solid", bd=1)
        frm_fotos.pack(fill="x", pady=5)
        tk.Button(
            frm_fotos, text="📸 Seleccionar Fotos de Evidencia (Máx. 3)",
            font=("Segoe UI", 10, "bold"), bg="#1B365D", fg="#FFFFFF", relief="flat", padx=12, pady=4,
            command=self._seleccionar_fotos_emergencia
        ).pack(side="left")

        self.lbl_fotos_count = tk.Label(frm_fotos, text="0 fotos seleccionadas", font=("Segoe UI", 10), bg="#F8FAFC", fg="#475569")
        self.lbl_fotos_count.pack(side="left", padx=15)

    # ================= EVENTOS DE BOTONES =================
    def _seleccionar_pdf(self):
        path = filedialog.askopenfilename(title="Seleccionar PDF Semanal Tecnoandina", filetypes=[("Archivos PDF", "*.pdf")])
        if path:
            self.ruta_pdf.set(path)
            self.lbl_estado.config(text=f"PDF cargado: {os.path.basename(path)}")

    def _seleccionar_foto_obs(self):
        path = filedialog.askopenfilename(title="Seleccionar captura o gráfico", filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if path:
            self.ruta_foto_obs.set(path)

    def _seleccionar_fotos_emergencia(self):
        paths = filedialog.askopenfilenames(title="Seleccionar hasta 3 fotos de terreno", filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if paths:
            self.lista_fotos_emergencia = list(paths[:3])
            nombres = ", ".join([os.path.basename(p) for p in self.lista_fotos_emergencia])
            self.lbl_fotos_count.config(text=f"{len(self.lista_fotos_emergencia)} foto(s): {nombres}")

    def _ejecutar_generacion(self):
        estilo_elegido = self.estilo_ppt_var.get()
        sufijo_estilo = "Gamma" if estilo_elegido == "gamma" else "Agrosuper"

        ruta_salida = filedialog.asksaveasfilename(
            title="Guardar Presentación Ejecutiva",
            defaultextension=".pptx",
            initialfile=f"Reporte_{sufijo_estilo}_{self.semana_var.get().replace(' ', '_')}.pptx",
            filetypes=[("PowerPoint Presentation", "*.pptx")]
        )
        if not ruta_salida:
            return

        try:
            self.lbl_estado.config(text=f"⏳ Generando presentación en estilo {sufijo_estilo}...")
            self.root.update_idletasks()

            if self.ruta_pdf.get() and os.path.exists(self.ruta_pdf.get()):
                extractor = TecnoandinaPDFExtractor(self.ruta_pdf.get())
                datos_pdf = extractor.extraer_datos()
            else:
                extractor = TecnoandinaPDFExtractor("")
                datos_pdf = {
                    "periodo": "29-10-2026 al 05-11-2026",
                    "alertas_totales": "2.263",
                    "alertas_por_dia": "305",
                    "variacion_alertas": "15%",
                    "disponibilidad_real": "85,3%",
                    "disp_anterior": "82,9%",
                    "nidos_activos": "139 de 250",
                    "tiempo_fuera_rango": "11,8%",
                    "t_fuera_rango_ant": "6,7%",
                    "desconexiones_totales": "54",
                    "horas_desconexion": "222 h",
                    "fallas_sonda": "430",
                    "comparativa_alertas": extractor._extraer_comparativa_alertas(""),
                    "disponibilidad_grupos": extractor._extraer_disponibilidad_grupos(""),
                    "grupos_criticos_texto": "Grupo 20 (12,9%), Grupo 28 (48,6%), Grupo 10 (74,0%), Grupo 23 (91,6%), Grupo 19 (94,0%), Grupo 25 (96,6%).",
                    "peores_nidos_texto": "Grupo 21 PAB13-MAT2-N4 (81%), Grupo 24-PAB18-MAT15-N3 (79%), Grupo 23-PAB20-MAT21-N3 (78%)."
                }

            datos_usuario = {
                "autor": "Alex Retamal Lobos",
                "semana": self.semana_var.get(),
                "texto_observaciones": self.txt_observaciones.get("1.0", "end").strip(),
                "foto_observaciones": self.ruta_foto_obs.get(),
                "titulo_emergencia": self.titulo_emergencia_var.get(),
                "detalle_emergencia": self.txt_eme_detalle.get("1.0", "end").strip(),
                "acciones_emergencia": self.txt_eme_acciones.get("1.0", "end").strip(),
                "fotos_emergencia": self.lista_fotos_emergencia
            }

            generador = ExecutivePPTGenerator(ruta_salida, estilo=estilo_elegido)
            generador.generar_presentacion_completa(datos_pdf, datos_usuario)

            self.lbl_estado.config(text=f"✅ ¡Presentación ({sufijo_estilo}) creada con éxito!")
            messagebox.showinfo(
                "¡Presentación Lista!",
                f"Hola Alex, tu presentación con estilo {sufijo_estilo} se generó en:\n\n{ruta_salida}"
            )

        except Exception as e:
            self.lbl_estado.config(text="❌ Error al generar la presentación.")
            messagebox.showerror("Error", f"Ocurrió un detalle al crear el archivo:\n{str(e)}")