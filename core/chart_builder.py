import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


class ChartBuilder:
    """
    Construye los gráficos en alta resolución a partir de los datos extraídos del PDF.
    """

    @staticmethod
    def crear_grafico_comparativo_alertas(datos_comp: dict, output_path: str, estilo: str = "agrosuper"):
        categorias = datos_comp.get("categorias", ["T° Fuera Rango", "Nido Sin Datos", "Falla Sonda"])
        actual = datos_comp.get("actual", [81.8, 117.7, 51.5])
        anterior = datos_comp.get("anterior", [168.3, 86.0, 58.1])

        x = np.arange(len(categorias))
        width = 0.35

        plt.close("all")
        fig, ax = plt.subplots(figsize=(6.2, 4.8), dpi=300)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        if estilo.lower() == "gamma":
            color_ant = "#8CC63F"
            color_act = "#118B50"
        else:
            color_ant = "#94A3B8"
            color_act = "#E87722"

        rects1 = ax.bar(x - width / 2, anterior, width, label="Semana Anterior", color=color_ant, zorder=3)
        rects2 = ax.bar(x + width / 2, actual, width, label="Semana Actual", color=color_act, zorder=3)

        ax.set_title("Promedio Diario de Alertas (Actual vs Anterior)", fontsize=11.5, fontweight="bold", color="#0F172A", pad=14)
        ax.set_xticks(x)
        ax.set_xticklabels(categorias, fontsize=9.5, fontweight="bold", color="#1E293B")
        ax.grid(axis="y", linestyle="--", alpha=0.4, color="#CBD5E1", zorder=0)

        max_val = max(max(actual, default=100), max(anterior, default=100))
        ax.set_ylim(0, max_val * 1.2)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")

        for rect in rects1:
            h = rect.get_height()
            ax.annotate(
                f"{h:.1f}",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color="#334155"
            )

        for rect in rects2:
            h = rect.get_height()
            ax.annotate(
                f"{h:.1f}",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color="#0F172A"
            )

        ax.legend(frameon=False, loc="upper right", fontsize=9)
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def crear_grafico_semaforo_grupos(lista_grupos: list, output_path: str, estilo: str = "agrosuper"):
        # Ordenar de mayor a menor para que matplotlib dibuje el menor (más crítico) arriba del todo
        datos_ord = sorted(lista_grupos, key=lambda x: x[1], reverse=True)
        nombres = [x[0] for x in datos_ord]
        valores = [x[1] for x in datos_ord]

        colores = []
        for v in valores:
            if v < 80.0:
                colores.append("#DC2626")  # Rojo (< 80%)
            elif v < 95.0:
                colores.append("#8CC63F" if estilo.lower() == "gamma" else "#F59E0B")  # Atención (< 95%)
            else:
                colores.append("#118B50" if estilo.lower() == "gamma" else "#16A34A")  # Normal (>= 95%)

        plt.close("all")
        fig, ax = plt.subplots(figsize=(6.8, 5.2), dpi=300)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        y_pos = np.arange(len(nombres))
        bars = ax.barh(y_pos, valores, color=colores, height=0.68, zorder=3)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(nombres, fontsize=8.5, fontweight="bold", color="#1E293B")
        ax.set_xlim(0, 112)
        ax.set_title("Disponibilidad Real de Datos por Grupo (%) - InfluxDB", fontsize=11, fontweight="bold", color="#0F172A", pad=12)

        ax.axvline(95.0, color="#64748B", linestyle="--", linewidth=1.2, label="Meta Óptima (95%)", zorder=4)
        ax.grid(axis="x", linestyle=":", alpha=0.4, color="#CBD5E1", zorder=0)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")

        for bar in bars:
            w = bar.get_width()
            ax.annotate(
                f"{w:.1f}%",
                xy=(w, bar.get_y() + bar.get_height() / 2),
                xytext=(4, 0),
                textcoords="offset points",
                ha="left", va="center",
                fontsize=8, fontweight="bold", color="#1E293B"
            )

        ax.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="#CBD5E1", fontsize=8.5)
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)