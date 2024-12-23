import requests
from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.io as pio

app = Flask(__name__)

API_KEY = '60DUozrNN5XgQG9u4VK9tyZSjjLYEEA9'
BASE_URL = "http://dataservice.accuweather.com"


def get_location_key(city_name):
    url = f"{BASE_URL}/locations/v1/cities/search"
    params = {"apikey": API_KEY, "q": city_name}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]['Key'], data[0]['GeoPosition']['Latitude'], data[0]['GeoPosition']['Longitude']
        else:
            return None, None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location key: {e}")
        return None, None, None


def get_weather_data(location_key, days=1):
    url = f"{BASE_URL}/forecasts/v1/daily/{days}day/{location_key}"
    params = {"apikey": API_KEY, "details": "true", "metric": "true"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        route_points = request.form.get('route_points')
        forecast_days = int(request.form.get('forecast_days'))

        if route_points:
            cities = [city.strip() for city in route_points.split(',')]
            weather_data = []
            map_data = []

            for city in cities:
                location_key, lat, lon = get_location_key(city)
                if location_key:
                    data = get_weather_data(location_key, days=forecast_days)
                    if data:
                        daily_forecasts = data['DailyForecasts']
                        weather_data.append({
                            'city': city,
                            'latitude': lat,
                            'longitude': lon,
                            'forecasts': [
                                {
                                    'date': forecast['Date'],
                                    'temperature': forecast['Temperature']['Maximum']['Value'],
                                    'rain_probability': forecast['Day']['RainProbability']
                                }
                                for forecast in daily_forecasts
                            ]
                        })
                        map_data.append({
                            'city': city,
                            'latitude': lat,
                            'longitude': lon,
                            'description': f"Temp: {daily_forecasts[0]['Temperature']['Maximum']['Value']}°C, Rain: {daily_forecasts[0]['Day']['RainProbability']}%"
                        })

            # Генерация графиков
            temperature_graph = generate_temperature_graph(weather_data)
            rain_graph = generate_rain_graph(weather_data)
            map_graph = generate_map_graph(map_data)

            return render_template(
                'result.html',
                temperature_graph=temperature_graph,
                rain_graph=rain_graph,
                map_graph=map_graph,
                cities=cities
            )

    return render_template('index.html')


def generate_temperature_graph(weather_data):
    fig = go.Figure()
    for city_data in weather_data:
        city = city_data['city']
        dates = [forecast['date'] for forecast in city_data['forecasts']]
        temperatures = [forecast['temperature'] for forecast in city_data['forecasts']]
        fig.add_trace(go.Scatter(x=dates, y=temperatures, mode='lines+markers', name=city))
    fig.update_layout(title='Температура по маршруту', xaxis_title='Дата', yaxis_title='Температура (°C)')
    return pio.to_html(fig, full_html=False)


def generate_rain_graph(weather_data):
    fig = go.Figure()
    for city_data in weather_data:
        city = city_data['city']
        dates = [forecast['date'] for forecast in city_data['forecasts']]
        rain_probs = [forecast['rain_probability'] for forecast in city_data['forecasts']]
        fig.add_trace(go.Bar(x=dates, y=rain_probs, name=city))
    fig.update_layout(title='Вероятность осадков по маршруту', xaxis_title='Дата', yaxis_title='Вероятность осадков (%)')
    return pio.to_html(fig, full_html=False)


def generate_map_graph(map_data):
    fig = go.Figure()
    for data in map_data:
        fig.add_trace(go.Scattermapbox(
            lat=[data['latitude']],
            lon=[data['longitude']],
            mode='markers',
            marker=go.scattermapbox.Marker(size=14),
            text=data['description']
        ))
    fig.update_layout(
        title='Карта маршрута',
        mapbox=dict(style='open-street-map', zoom=4,
                    center=dict(lat=map_data[0]['latitude'] if map_data else 0, lon=map_data[0]['longitude'] if map_data else 0)),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return pio.to_html(fig, full_html=False)


if __name__ == '__main__':
    app.run(debug=True)
