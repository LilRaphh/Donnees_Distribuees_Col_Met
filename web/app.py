from flask import Flask, render_template

app = Flask(__name__)

apps = ["OpenSky", "WeatherAPI", "FlightsAPI"]

# Mapping app -> URL Grafana (iframe)
grafana_urls = {
    "OpenSky": "http://localhost:3000/goto/bf2lewepo3mdca?orgId=1",
}

@app.route("/")
def index():
    return render_template("index.html", apps=apps)

@app.route("/app/<app_name>")
def app_page(app_name):
    return render_template("app.html", apps=apps, app_name=app_name, grafana_urls=grafana_urls)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
