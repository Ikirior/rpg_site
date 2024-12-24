from flask import Flask, render_template, send_from_directory
import folium
import requests
import pandas as pd
import os

app = Flask(__name__)

# Função para carregar os dados de contaminação a partir de um arquivo CSV
def read_contamination_data_csv(file_path):
    df = pd.read_csv(file_path, sep=';')  # Usar o separador correto (';')
    return df

# Função para determinar a cor e opacidade de um país com base na contaminação
def contamination_style(country_name, contamination_data):
    name_mapping = {
        "United States of America": "United States",
    }
    country_key = name_mapping.get(country_name, country_name)

    contamination_level = contamination_data.loc[contamination_data['country'] == country_key, 'contamination'].values
    if contamination_level.size > 0:
        contamination_level = contamination_level[0]
    else:
        contamination_level = 0

    fill_opacity = contamination_level / 100
    return {
        "fillColor": "#FF0000" if contamination_level > 0 else "#222831",
        "color": "#FFFFFF",
        "weight": 0.5,
        "fillOpacity": fill_opacity,
    }

@app.route('/')
def index():
    # Baixar dados GeoJSON de uma API pública
    url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"
    response = requests.get(url)
    world_geojson = response.json()

    # Carregar os dados de contaminação a partir do arquivo CSV
    contamination_data = read_contamination_data_csv('static/contamination_data.csv')

    # Converter os dados para um formato que o template pode usar (lista de dicionários)
    contamination_data_dict = contamination_data.to_dict(orient='records')

    # Criar o mapa base
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    # Adicionar GeoJSON ao mapa com estilo
    folium.GeoJson(
        world_geojson,
        style_function=lambda feature: contamination_style(feature["properties"]["name"], contamination_data),
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["País:"], labels=True),
    ).add_to(m)

    # Adicionar marcadores para cada país com o nome, capital, latitude, longitude e contaminação
    for _, row in contamination_data.iterrows():
        country = row['country']
        capital = row['capital']
        latitude = row['reclat']
        longitude = row['reclong']
        contamination_level = row['contamination']

        folium.Marker(
            location=[latitude, longitude],
            popup=f"{country} - Capital: {capital}<br>Contaminação: {contamination_level}%",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # Salvar o mapa no diretório 'static'
    map_path = os.path.join('static', 'map.html')
    m.save(map_path)

    # Renderizar a página com o mapa e os dados de contaminação
    return render_template('index.html', map_url='map.html', contamination_data=contamination_data_dict)

if __name__ == '__main__':
    app.run(debug=True)
