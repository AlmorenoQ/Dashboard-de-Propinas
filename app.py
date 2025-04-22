import faicons as fa
import plotly.express as px

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
with ui.layout_columns(col_widths=[6, 6, 12]):
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

            return px.scatter(
                tips_data(),
                x="total_bill",
                y="tip",
                color=None if color == "none" else color,
                size="size" if use_size else None,
                trendline="lowess",  # Añadir línea de tendencia
            )
        
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
                )
            )

            return plt
        
    # 
    with ui.layout_columns():
        # Cuarta Tarjeta: Gráfico de líneas
        with ui.card(full_screen=True):
            ui.card_header("Gráfico de propinas por día de la semana")

            @render_plotly
            def simple_bar_chart():
                tips_by_day = tips.groupby('day')['tip'].sum().reset_index()

                day_order = ["Thur", "Fri", "Sat", "Sun"]
                tips_by_day["day"] = pd.Categorical(tips_by_day["day"], categories=day_order, ordered=True)
                tips_by_day = tips_by_day.sort_values("day")

                plt = px.bar(tips_by_day,
                              x='day', 
                              y='tip')

                return plt
                

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