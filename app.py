import faicons as fa
import plotly.express as px
import pandas as pd

# cargar datos y computar valores extáticos
from shared import app_dir, tips
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

# Calcular el rango de valores de facturas para el control deslizante
bill_rng = (min(tips.total_bill), max(tips.total_bill))

# Añadir título de página y opciones
ui.page_opts(title="Propinas Restaurante", fillable=True)

# Crear la barra lateral con controles de filtrado
with ui.sidebar(open="desktop"):
    ui.input_slider(
        "total_bill",                   # ID del input
        "Bill amount",                  # Etiqueta para el usuario   
        min=bill_rng[0],                # Valor mínimo
        max=bill_rng[1],                # Valor máximo
        value=bill_rng,                 # VAlor inicial (rango completo)
        pre="€"                         # Prefijo para los valores
    )
    ui.input_checkbox_group(
        "time",                         # ID del input
        "Food service",                 # Etiqueta para el usuario
        ["Lunch", "Dinner"],            # Opciones disponibles
        selected=["Lunch", "Dinner"],   # Opciones seleccionadas inicialmente
        inline=True,                    # Mostrar horizontalmente
    )

    ui.input_selectize(
        "days",                         # ID del input
        "Día de la semana",                 # Etiqueta para el usuario
        ["Sun", "Sat", "Fri", "Thur"],            # Opciones disponibles
        selected=["Sun", "Sat", "Fri", "Thur"],   # Opciones seleccionadas inicialmente
        multiple=True,                  # Mostrar horizontalmente
    )

    ui.input_action_button("reset", "Reset filter") # Botón para reiniciar filtros




# Definir iconos para la interfaz
ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-euro": fa.icon_svg("euro-sign"),
    "ellipsis": fa.icon_svg("ellipsis"),
    "users": fa.icon_svg("users")
}

# Crear fila de caja de valores
with ui.layout_columns(fill=False):
    # Primera caja de valor : Total de propinas
    with ui.value_box(showcase=ICONS["user"]):
        "Total tippers"

        @render.express
        def total_tippers():
            tips_data().shape[0]

    # Segunda caja de valor: Propina promedio
    with ui.value_box(showcase=ICONS["wallet"]):
        "Propina Media"
    
        @render.express
        def average_tip():
            d = tips_data()
            if d.shape[0] > 0:
                perc = d.tip / d.total_bill
                f"{perc.mean():.1%}"

    # Tercera caja de valor: Factura promedio
    with ui.value_box(showcase=ICONS["currency-euro"]):
        "Factura Media"

        @render.express
        def average_bill():
            d = tips_data()
            if d.shape[0] > 0:
                bill = d.total_bill.mean()  # Calcular factura promedio
                f"€{bill:.2f}"              # Formatear como moneda

    # Cuarta caja de valor: Tamaño promedio
    with ui.value_box(showcase=ICONS["users"]):
        "Tamaño de Grupo Medio"

        @render.express
        def average_size():
            d = tips_data()
            if d.shape[0] > 0:
                avg_size = d["size"].mean()
                f"{avg_size:.1f} px"

# Crear diseño principal con tres tarjetas
with ui.layout_columns(col_widths=[6, 6]):
    # Primera tarjeta: Tabla de datos
    with ui.card(full_screen=True):
        ui.card_header("Tabla de propinas")

        @render.data_frame
        def table():
            return render.DataGrid(tips_data())
    
    # Segunda tarjeta: Gráfico de dispersión
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Factura Total vs Propina"
            # Menú emergente para opciones de color
            with ui.popover(title="Añadir una variable de color", placement="top"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "scatter_color",
                    None,
                    ["none", "sex", "smoker", "day", "time"],
                    inline=True,
                )
                
                ui.input_checkbox(
                    "show_size",
                    "Ver tamaño de grupo en los puntos:",
                    value=False                    
                )

        # Renderizar el gráfico de dispersión
        @render_plotly
        def scatterplot():
            color = input.scatter_color()
            use_size = input.show_size()

            fig =  px.scatter(
                tips_data(),
                x="total_bill",
                y="tip",
                color=None if color == "none" else color,
                size="size" if use_size else None,
                trendline="lowess",  # Añadir línea de tendencia
            )

            # Ajustar tamaño del gráfico para que ocupe todo el espacio disponible
            fig.update_layout(
                autosize=True,
                margin=dict(l=50, r=30, t=30, b=50)
            )
        
            return fig
        
    # Tercera tarjeta: Gráfico de densidad (ridgeplot)
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Porcentaje de propinas"
            with ui.popover(title="Añade un color a la variable"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "tip_perc_y",
                    "Partir por:",
                    ["sex", "smoker", "day", "time"],
                    selected="day",  # Valor predeterminado
                    inline=True,
                )
        @render_plotly
        def tip_perc():
            from ridgeplot import ridgeplot

            dat = tips_data()
            dat["percent"] = dat.tip / dat.total_bill
            yvar = input.tip_perc_y()       # Variable para dividir
            uvals = dat[yvar].unique()     # Valores únicos de esa variable

            # Crear muestras para cada valor único
            samples = [[dat.percent[dat[yvar] == val]] for val in uvals]

            # Crear el gráfico ridgeplot
            plt = ridgeplot(
                samples=samples,
                labels=uvals,
                bandwidth=0.01,
                colorscale="viridis",
                colormode="row-index",
            )

            # Ajustar la leyenda
            plt.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
                ),
                autosize=True,
                margin=dict(l=50, r=30, t=30, b=50)
            )

            return plt
    
     # Gráfico de barras por día de la semana
    with ui.card(full_screen=True, height="400px"):  # Establecer altura fija
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Propinas por día de la semana"
            with ui.popover(title="Opciones de visualización"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "bar_metric",
                    "Métrica:",
                    ["Total propinas", "Propina media", "Porcentaje de propina"],
                    selected="Total propinas",
                    inline=True,
                )
                ui.input_checkbox(
                    "show_day_count",
                    "Muestra el número de visitas por día",
                    value=True
                )

        @render_plotly
        def tips_by_day():
            data = tips_data()
            
            if data.shape[0] == 0:
                return px.bar(title="No hay dato para mostrar con los filtros actuales")
            
            metric = input.bar_metric()
            
            if metric == "Total propinas":
                day_tips = data.groupby("day")["tip"].sum().reset_index()
                day_tips.columns = ["day", "value"]
                y_title = "Total propinas (€)"
            
            elif metric == "Propina media":
                day_tips = data.groupby("day")["tip"].mean().reset_index()
                day_tips.columns = ["day", "value"]
                y_title = "Propina media (€)"
            
            else:  # Tip percentage
                data["percent"] = data.tip / data.total_bill * 100
                day_tips = data.groupby("day")["percent"].mean().reset_index()
                day_tips.columns = ["day", "value"]
                y_title = "Porcentaje de propina medio (%)"
            
            # Ordenar los días correctamente
            day_order = ["Thur", "Fri", "Sat", "Sun"]
            day_tips["day"] = pd.Categorical(day_tips["day"], categories=day_order, ordered=True)
            day_tips = day_tips.sort_values("day")
            
            # Configuración base para la gráfica
            fig_params = {
                'x': 'day',
                'y': 'value',
                'color': 'day',
                'labels': {'vañue': y_title, 'day': 'Día de la semana'},
                'title': f'{metric} por día de la semana'
            }

            # Mostrar conteo de visitas si está activado
            if input.show_day_count():
                day_count = data.groupby("day").size().reset_index()
                day_count.columns = ["day", "count"]
                day_count["day"] = pd.Categorical(day_count["day"], categories=day_order, ordered=True)
                day_count = day_count.sort_values("day")
                
                hover_template = "<b>%{x}</b><br>" + \
                                f"{y_title}: %{{y:.2f}}<br>" + \
                                "Número de visitas: %{customdata}<br>"
                
                fig = px.bar(
                    day_tips,
                    **fig_params
                )
                
                fig.update_traces(hovertemplate=hover_template)
            else:
                fig = px.bar(
                    day_tips,
                    **fig_params
                )
            
            fig.update_layout(
                showlegend=True,
                xaxis_title="Día de la semana",
                yaxis_title=y_title,
                autosize=True,
                margin=dict(l=50, r=30, t=30, b=50)
            )
            
            return fig
        
    
                

# Incluir estilos CSS personalizados
ui.include_css(app_dir / "styles.css")

# --------------------------------------------------------
# Cálculos reactivos y efectos
# --------------------------------------------------------

# Función reactiva para filtrar datos según entradas del usuario
@reactive.calc
def tips_data():
    bill = input.total_bill()
    idx1 = tips.total_bill.between(bill[0], bill[1])
    idx2 = tips.time.isin(input.time())
    idx3 = tips.day.isin(input.days())
    return tips[idx1 & idx2 & idx3]

# Efecto reactivo para restablecer filtros cuando se hace clic en el botón
@reactive.effect
@reactive.event(input.reset)  # Activar cuando se haga clic en "reset"
def _():
    ui.update_slider("total_bill", value=bill_rng)  # Restablecer control deslizante
    ui.update_checkbox_group("time", selected=["Lunch", "Dinner"])  # Restablecer casillas
    ui.update_selectize("days",selected=["Sun", "Sat", "Fri", "Thur"])