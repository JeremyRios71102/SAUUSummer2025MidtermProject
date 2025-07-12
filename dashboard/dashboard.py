import dash
from dash import html, dcc
import requests
import pandas as pd
from dash.dependencies import Input, Output
from datetime import datetime
import plotly.graph_objs as go

# ---- Config ----
VM_ENDPOINTS = {
    "1": "http://<VM1-IP>:5000/metrics",
    "2": "http://<VM2-IP>:5000/metrics",
    "3": "http://<VM3-IP>:5000/metrics",
    "4": "http://<VM4-IP>:5000/metrics"
}
UPDATE_INTERVAL = 5 * 1000  # in milliseconds

# ---- App Setup ----
app = dash.Dash(__name__)
app.title = "Server Monitor"

# ---- Layout ----
app.layout = html.Div([
    html.H2("Live Server Monitoring Dashboard"),
    dcc.Tabs([
        dcc.Tab(label=f"VM {name}", children=[
            html.Div([
                html.Div(dcc.Graph(id=f"{name}-cpu-graph"), style={"width": "48%", "display": "inline-block", "padding": "10px"}),
                html.Div(dcc.Graph(id=f"{name}-mem-graph"), style={"width": "48%", "display": "inline-block", "padding": "10px"})
            ]),
            html.Div([
                html.Div(dcc.Graph(id=f"{name}-disk-graph"), style={"width": "48%", "display": "inline-block", "padding": "10px"}),
                html.Div(dcc.Graph(id=f"{name}-io-graph"), style={"width": "48%", "display": "inline-block", "padding": "10px"})
            ]),
            html.Div([
                html.Div(dcc.Graph(id=f"{name}-net-graph"), style={"width": "48%", "display": "inline-block", "padding": "10px"})
            ]),
            html.Div(id=f"{name}-alerts", style={"whiteSpace": "pre-line", "color": "red", "margin": "10px"})
        ]) for name in VM_ENDPOINTS
    ]),
    dcc.Interval(id="update", interval=UPDATE_INTERVAL, n_intervals=0)
])

# ---- Placeholder Figure Function ----
def placeholder_fig(title_text):
    fig = go.Figure()
    fig.update_layout(
        title=title_text,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{
            "text": "No data available",
            "xref": "paper", "yref": "paper",
            "showarrow": False,
            "font": {"size": 16}
        }]
    )
    return fig

# ---- Dynamic Callbacks ----
for name, url in VM_ENDPOINTS.items():
    @app.callback(
        [Output(f"{name}-cpu-graph", "figure"),
         Output(f"{name}-mem-graph", "figure"),
         Output(f"{name}-disk-graph", "figure"),
         Output(f"{name}-io-graph", "figure"),
         Output(f"{name}-net-graph", "figure"),
         Output(f"{name}-alerts", "children")],
        [Input("update", "n_intervals")]
    )
    def update_graphs(n, url=url, name=name):
        try:
            res = requests.get(url, timeout=2).json()
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Save to CSV
            row = {
                "time": timestamp,
                "cpu": res["cpu"],
                "mem": res["memory"],
                "disk": res["disk"],
                "diskio": res["diskio"],
                "net": res["net"]
            }
            df = pd.DataFrame([row])
            df.to_csv(f"data/{name.lower()}_metrics.csv", mode='a', header=False, index=False)

            # Gauge plots for percentages
            cpu_fig = go.Figure(go.Indicator(mode="gauge+number", value=res["cpu"], title={"text": "CPU %"}))
            cpu_fig.update_layout(title="CPU Usage")
            mem_fig = go.Figure(go.Indicator(mode="gauge+number", value=res["memory"], title={"text": "Memory %"}))
            mem_fig.update_layout(title="Memory Usage")
            disk_fig = go.Figure(go.Indicator(mode="gauge+number", value=res["disk"], title={"text": "Disk Usage %"}))
            disk_fig.update_layout(title="Disk Usage")

            # Number indicators for throughput
            io_fig = go.Figure(go.Indicator(mode="number", value=res["diskio"], number={'suffix': " MB/s"}, title={"text": "Disk I/O"}))
            io_fig.update_layout(title="Disk I/O Rate")
            net_fig = go.Figure(go.Indicator(mode="number", value=res["net"], number={'suffix': " KB/s"}, title={"text": "Network"}))
            net_fig.update_layout(title="Network Throughput")

            # Alerts
            alerts = ""
            if res["cpu"] > 80:
                alerts += f"{timestamp} – High CPU usage ({res['cpu']}%)\n"
            if res["memory"] > 75:
                alerts += f"{timestamp} – High Memory usage ({res['memory']}%)\n"
            if res["disk"] > 85:
                alerts += f"{timestamp} – High Disk usage ({res['disk']}%)\n"
            if res["diskio"] > 50:
                alerts += f"{timestamp} – High Disk I/O ({res['diskio']} MB/s)\n"
            if res["net"] > 1000:
                alerts += f"{timestamp} – High Network usage ({res['net']} KB/s)\n"

            return cpu_fig, mem_fig, disk_fig, io_fig, net_fig, alerts

        except Exception as e:
            return (
                placeholder_fig("CPU Usage"),
                placeholder_fig("Memory Usage"),
                placeholder_fig("Disk Usage"),
                placeholder_fig("Disk I/O Rate"),
                placeholder_fig("Network Throughput"),
                f"Error: {str(e)}")

# ---- Run ----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
