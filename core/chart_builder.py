import matplotlib.pyplot as plt


class ChartBuilder:
    """
    Genera gráficos ejecutivos en formato PNG de alta resolución (300 DPI)
    adaptados al estilo seleccionado ('agrosuper' o 'gamma').
    """

    @staticmethod
    def crear_grafico_comparativo_alertas(datos_comp: dict, ruta_salida: str, estilo: str = "agrosuper"):
        categorias = datos_comp["categorias"]
        actual = datos_comp["actual"]
        anterior = datos_comp["anterior"]

        x = range(len(categorias))
        width = 0.35

        fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=300)
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FFFFFF')

        if estilo == "gamma":
            color_ant = '#8CC63F'   # Verde lima Gamma
            color_act = '#118B50'   # Verde esmeralda oscuro Gamma
            color_tit = '#0F172A'
        else:
            color_ant = '#94A3B8'   # Gris azulado
            color_act = '#E87722'   # Naranja Agrosuper
            color_tit = '#1B365D'

        rects1 = ax.bar([i - width/2 for i in x], anterior, width, label='Semana Anterior', color=color_ant)
        rects2 = ax.bar([i + width/2 for i in x], actual, width, label='Semana Actual', color=color_act)

        ax.set_title('Promedio Diario de Alertas (Actual vs Anterior)', fontsize=11, fontweight='bold', color=color_tit, pad=15)
        ax.set_xticks(list(x))
        ax.set_xticklabels(categorias, fontsize=9.5, fontweight='bold', color='#334155')
        ax.legend(frameon=False, fontsize=9)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CBD5E1')
        ax.spines['bottom'].set_color('#CBD5E1')
        ax.grid(axis='y', linestyle='--', alpha=0.4, color='#CBD5E1')
        ax.set_axisbelow(True)

        for rect in rects1 + rects2:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1E293B')

        plt.tight_layout()
        plt.savefig(ruta_salida, dpi=300)
        plt.close(fig)

    @staticmethod
    def crear_grafico_semaforo_grupos(lista_grupos: list, ruta_salida: str, estilo: str = "agrosuper"):
        grupos = [g[0] for g in reversed(lista_grupos)]
        valores = [g[1] for g in reversed(lista_grupos)]

        colores = []
        for v in valores:
            if v < 80.0:
                colores.append('#DC2626')  # Rojo crítico
            elif v < 95.0:
                colores.append('#F59E0B' if estilo == "agrosuper" else '#8CC63F')
            else:
                colores.append('#16A34A' if estilo == "agrosuper" else '#118B50')

        fig, ax = plt.subplots(figsize=(6.8, 4.5), dpi=300)
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FFFFFF')

        bars = ax.barh(grupos, valores, color=colores, height=0.68)

        color_tit = '#0F172A' if estilo == "gamma" else '#1B365D'
        ax.set_title('Disponibilidad Real de Datos por Grupo (%) - InfluxDB', fontsize=11, fontweight='bold', color=color_tit, pad=12)
        ax.set_xlim(0, 112)
        ax.axvline(95, color=color_tit, linestyle='--', linewidth=1, alpha=0.7, label='Meta Óptima (95%)')
        ax.legend(loc='lower right', frameon=True, facecolor='#F8FAFC', fontsize=8.5)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CBD5E1')
        ax.spines['bottom'].set_color('#CBD5E1')
        ax.tick_params(axis='y', labelsize=8.5)

        for bar in bars:
            w = bar.get_width()
            ax.annotate(f'{w:.1f}%',
                        xy=(w, bar.get_y() + bar.get_height() / 2),
                        xytext=(4, 0), textcoords="offset points",
                        ha='left', va='center', fontsize=8, fontweight='bold', color='#1E293B')

        plt.tight_layout()
        plt.savefig(ruta_salida, dpi=300)
        plt.close(fig)