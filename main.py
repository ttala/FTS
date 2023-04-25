
import dash
from dash import html, dcc, ctx  # Input, Output,
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import configparser
from dash_bootstrap_templates import load_figure_template
from flights_call_process import *
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from geopy.geocoders import Nominatim


load_figure_template('LUX')
#app = dash.Dash(external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
#app = DashProxy(prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])
app = DashProxy(external_stylesheets=[dbc.themes.LUX], transforms=[MultiplexerTransform()]
                ,suppress_callback_exceptions=True)
geolocator = Nominatim(user_agent=app.title)

config_path = 'config.ini'
config = configparser.RawConfigParser()
config.read(config_path)
mapbox_key = config.get('MAPBOX', 'KEY')


# Lat Long center
lat_center = 46.6047
long_center = -0.6401

# Main figure shows at the start
def get_figure(data):
    fig = go.Figure(go.Scattermapbox(
        mode="markers",
        lon=list(data.lng),
        lat=list(data.lat),
        marker={"size": 8, "color": '#00FF00', "symbol": "airport"},
        hoverinfo="text",
        hovertext=["{}".format(i) for i in data['flight_iata']]
    ))
    fig.update_layout(
        mapbox={
            'accesstoken': mapbox_key,
            'style': "outdoors",
            'zoom': 5,
            'center': {'lon': long_center, 'lat': lat_center}
        },
        width=900,
        height=600,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )
    return fig

# Figure to focus on a specific flight
def get_figure_flight(data, flight):
    location = geolocator.geocode(flight["dep_city"])
    df_db = get_enRoute_flights()
    
    iata = flight['flight_iata']
    if iata not in df_db.index: # If the flight hasn't been registered before in the db
        lons, lats = data['lng'].loc[iata], data['lat'].loc[iata]
    else:
        lons, lats = df_db['lng'].loc[iata], df_db['lat'].loc[iata]
    if not isinstance(lons, list):
        lons = [lons]
    if not isinstance(lats, list):
        lats = [lats]
    
    lons.append(flight["lng"])
    lons.insert(0, location.longitude)
    lats.append(flight["lat"])
    lats.insert(0, location.latitude)
    figure = go.Figure(go.Scattermapbox(
        mode="markers",
        lon=[flight['lng']],
        lat=[flight['lat']],
        marker={"size": 10, "color": '#00FF00', "symbol": "airport"},
        hoverinfo="text",
        hovertext=iata
    ))
    figure.update_layout(
        mapbox={
            'accesstoken': mapbox_key,
            'style': "outdoors",
            'center': {'lon': flight['lng'], 'lat': flight['lat']},
            'zoom': 5
        },
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
    )
    figure.add_trace(go.Scattermapbox(
        mode="lines",
        lon=lons,
        lat=lats,
        marker={'size': 10})
    )
    return figure


def get_pie_graph(data):
    pie_df = data.groupby('airline_name').size().reset_index(name='count')
    pie_df = pie_df.sort_values(by=['count'], ascending=False).head(10)
    pie_graph = px.pie(pie_df, values=pie_df['count'], names=pie_df['airline_name'],
                       width=500, height=190)
    pie_graph.update_layout(margin=dict(t=3, b=0, l=0, r=0))
    return pie_graph


def get_hist_graph(data):
    # calcul du nombre total de vol sortant et entrant par aéroport
    data_dep = data[['flight_iata', 'dep_country']].groupby('dep_country').size().reset_index(name='count') \
        .rename(columns={'dep_country': 'country'})
    data_arr = data[['flight_iata', 'arr_country']].groupby('arr_country').size().reset_index(name='count') \
        .rename(columns={'arr_country': 'country'})
    stat = pd.concat([data_dep, data_arr]).groupby(
        ['country']).sum().reset_index()
    # stat = stat.sort_values(by='count', ascending=False).head(10)
    stat['country'] = stat['country'].astype('string')
    stat['count'] = stat['count'].astype('int')
    # import pdb;pdb.set_trace()
    fig = px.bar(stat, x='country', y='count', labels={
                 'x': 'Country', 'y': 'Flights'}, width=500, height=270)
    return fig


def get_hist_graph_airport(data):
    # calcul du nombre total de vol sortant et entrant par aéroport
    data_dep = data[['flight_iata', 'dep_airport', 'dep_city']].groupby(['dep_airport', 'dep_city']).size().reset_index(name='count') \
        .rename(columns={'dep_airport': 'airport', 'dep_city': 'city'})
    data_arr = data[['flight_iata', 'arr_airport', 'arr_city']].groupby(['arr_airport', 'arr_city']).size().reset_index(name='count') \
        .rename(columns={'arr_airport': 'airport', 'arr_city': 'city'})
    stat = pd.concat([data_dep, data_arr]).groupby(
        ['airport', 'city']).sum().reset_index()

    stat = stat.sort_values(by='count', ascending=False).head(10)

    stat['airport'] = stat['airport'].str[:12]
    stat['airport'] = stat['airport'].astype('string')
    stat['city'] = stat['city'].astype('string')
    stat['count'] = stat['count'].astype('int')
    # import pdb;pdb.set_trace()
    fig = px.bar(stat, x='airport', y='count', labels={'x': 'Airport', 'y': 'Flights'},
                 width=500, height=290, hover_data={'Airport': stat.airport, 'City': stat.city})
    return fig


raw_flights = get_airlab_flights()
df_ab = clean_filter_flights(raw_flights)
df_all = get_all_flights()
figure = get_figure(df_ab)
# start_date, ends_date = get_dates(df_all)
# range_date = f'From {start_date} date to {ends_date}'
app.layout = html.Div([
    dbc.Row(html.H1('Live Flights + Statistics',
            style={'textAlign': 'center', 'color': 'mediumturquoise', 'background': 'beige'})),
            
    dbc.Row([
        dbc.Col(
            dbc.Row([
                # interval activated once/week or when page refreshed
                dcc.Interval(id='interval_db',
                             interval=86400000 * 7, n_intervals=0),
                dcc.Graph(id='map', figure=figure)

            ])),
        html.Br(),
        dbc.Col(
            dbc.Row([
                dcc.RadioItems(
                    id='radio',
                    options=[
                        {
                            "label": html.Div(['Statictics'], style={'font-size': 15, 'margin-right': 100}),
                            "value": "ST",
                        },
                        {
                            "label": html.Div(['Track Flight'], style={'font-size': 15, 'font-size': 15}),
                            "value": "TF",
                        },

                    ],
                    value='ST'
                ),
                dbc.Row(id='sidebar', style={'margin': '10px'})
            ])),
    ], style={'margin': '10px'}),
])


layout_stats = html.Div([
    dcc.Dropdown(id='select_country',
                        options=[{'label': x, 'value': x}
                                 for x in df_all['dep_country'].unique().tolist()],
                        placeholder="Select a country"),
    dcc.Graph(id='hist-graph', figure=get_hist_graph(df_all)),
    html.H6("Airlines distribution"),
    dcc.Graph(id='pie-graph', figure=get_pie_graph(df_all)),
])

info_flight  = html.Div([
            html.P(id='placeholder'),
            html.H6('Find a flight', style={
                    'textAlign': 'left', 'fontWeight': 'bold'}),

            html.Div(dcc.Dropdown(id='select_vol',
                                options=[{'label': x, 'value': x}
                                        for x in df_ab['flight_iata'].sort_values().unique()],
                                multi=False,
                                placeholder="Insert IATA Flight")
                    ),
            html.Br(),
            html.Div(id='info_vol'),
            html.Br(),
            html.Div(id='test_vol'),
        ], style={"background-color": "#f8f9fa"})

@app.callback(
    Output('sidebar', 'children'),
    Input('radio', 'value'))
def select_view(value):
    if value == 'ST':
        return layout_stats
    else:
        return info_flight


@app.callback([Output('map', 'figure'), Output('pie-graph', 'figure'),
              Output('hist-graph', 'figure')], 
              [Input('interval_db', 'n_intervals'), Input('select_country', 'value')]
              )
def update_page(n_intervals, country):
    if country:
        data = df_all.loc[(df_all['dep_country'] == country) & (df_all['arr_country'] == country)]
        pie_graph = get_pie_graph(data)
        hist_graph = get_hist_graph_airport(data)
    else:
        pie_graph = get_pie_graph(df_all)
        hist_graph = get_hist_graph(df_all)
    global df_ab
    raw_flights = get_airlab_flights()
    df_ab = clean_filter_flights(raw_flights)
    return get_figure(df_ab), pie_graph, hist_graph


@app.callback(
    [Output('info_vol', 'children'), Output('map', 'figure')],
     [Input('select_vol', 'value')]) 
def show_flight(iata):
    flight = 0
    if iata:
        flight = get_flight_info(iata)
        if flight != 0:
            new_fig = get_figure_flight(df_ab, flight)
            new_layout = get_detail_flight(flight)
            return new_layout, new_fig
        else:
            return html.H6("Flight not found, it may have already landed."), get_figure(df_ab)
    
    return html.Div(""), get_figure(df_ab)


@app.callback(
    [Output('info_vol', 'children'), Output('map', 'figure'), Output('select_vol', 'value')],
     [Input('map', 'clickData')]) 
def show_flight_click(clickData):
    flight = 0
    if clickData:
        iata = clickData["points"][0]['hovertext']
        flight = get_flight_info(iata)
        if flight != 0:
            new_fig = get_figure_flight(df_ab, flight)
            new_layout = get_detail_flight(flight)
            return new_layout, new_fig, iata
        else:
            return html.H6("Flight not found, it may have already landed."), get_figure(df_ab)
    
    return html.Div(""), get_figure(df_ab), ""

# @app.callback(Output('info_vol', 'children'),
#             [Input('close_flight_detail', 'n_clicks')])
# def reset_map(n_clicks):
#     triggered_id = ctx.triggered_id
#     if triggered_id == 'info_vol':
#         return info_flight()
    

def get_detail_flight(current_flight):
    if not current_flight:
        return ""
    detail = html.Div([
        dbc.Row([
            dbc.Row([
                    dbc.Col(html.P("Flight Number:", id='key', style={'margin-top': 7})),
                    dbc.Col(html.P(current_flight["flight_iata"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Departure City:", id='key')),
                    dbc.Col(html.P(current_flight["dep_city"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Arrival City:", id='key')),
                    dbc.Col(html.P(current_flight["arr_city"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Departure Airport:", id='key')),
                    dbc.Col(html.P(current_flight["dep_name"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Arrival Airport:", id='key')),
                    dbc.Col(html.P(current_flight["arr_name"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Airline:", id='key')),
                    dbc.Col(html.P(current_flight["airline_name"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Aircraft:", id='key')),
                    dbc.Col(html.P(current_flight["aircraft_icao"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Departure Time (UTC):", id='key')),
                    dbc.Col(html.P(current_flight["dep_actual_utc"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Arrival Time (UTC):", id='key')),
                    dbc.Col(html.P(current_flight["arr_time_utc"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Delay (min):", id='key')),
                    dbc.Col(html.P(current_flight["delayed"], id='key'))
                    ]),
            dbc.Row([
                    dbc.Col(html.P("Speed (km/h):", id='key')),
                    dbc.Col(html.P(current_flight["speed"], id='key'))
                    ]),
        ],
            style={
            'textAlign': 'center',
                'color': '#0000CD',
                'fontWeight': 'bold',
                'fontSize': 14,
                'border-style': 'solid'
        })

    ])
    return detail


if __name__ == '__main__':
    app.run_server(debug=True)
