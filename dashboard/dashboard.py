import dash
from dash import html, dcc
import requests
import pandas as pd
from dash.dependencies import Input, Output, State
from datetime import datetime
import plotly.graph_objs as go
import os

# ---- Config ----
VM_ENDPOINTS = {
    "1": "http://<VM1-IP>:5000/metrics",
    "2": "http://<VM2-IP>:5000/metrics",
    "3": "http://<VM3-IP>:5000/metrics",
    "4": "http://<VM4-IP>:5000/metrics"
}
UPDATE_INTERVAL = 5 * 1000  # in milliseconds

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# ---- App Setup ----
app = dash.Dash(__name__)
app.title = "Server Monitor"

def make_sliders(name):
    return html.Div([
        html.Label("CPU Threshold"),
        dcc.Slider(id=f"{name}-cpu-thresh", min=0, max=100, step=1, value=80,
                   persistence=True, persistence_type='local',
                   marks=None, tooltip={"placement": "bottom", "always_visible": True}),
        html.Label("Memory Threshold"),
        dcc.Slider(id=f"{name}-mem-thresh", min=0, max=100, step=1, value=75,
                   persistence=True, persistence_type='local',
                   marks=None, tooltip={"placement": "bottom", "always_visible": True}),
        html.Label("Disk Threshold"),
        dcc.Slider(id=f"{name}-disk-thresh", min=0, max=100, step=1, value=85,
                   persistence=True, persistence_type='local',
                   marks=None, tooltip={"placement": "bottom", "always_visible": True}),
        html.Label("Disk I/O Threshold"),
        dcc.Slider(id=f"{name}-io-thresh", min=0, max=100, step=1, value=50,
                   persistence=True, persistence_type='local',
                   marks=None, tooltip={"placement": "bottom", "always_visible": True}),
        html.Label("Network Threshold (KB/s)"),
        dcc.Slider(id=f"{name}-net-thresh", min=0, max=5000, step=100, value=1000,
                   persistence=True, persistence_type='local',
                   marks=None, tooltip={"placement": "bottom", "always_visible": True}),
    ], style={"margin": "20px"})

def make_line_fig(df, col, title, ylabel):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df[col], mode="lines+markers"))
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title=ylabel)
    return fig

app.layout = html.Div([
    html.H2("Live Server Monitoring Dashboard"),
    dcc.Tabs([
        dcc.Tab(label=f"VM {name}", children=[
            html.Div(id=f"{name}-alerts", style={
                "whiteSpace": "pre-wrap",  # Makes alerts appear below each other
                "color": "red",
                "margin": "10px",
                "fontWeight": "bold",
                "fontSize": "16px"
            }),
            make_sliders(name),
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
            html.Div([
                html.Div(dcc.Graph(id=f"{name}-cpu-history"), style={"width": "48%", "display": "inline-block", "padding": "10px"}),
                html.Div(dcc.Graph(id=f"{name}-mem-history"), style={"width": "48%", "display": "inline-block", "padding": "10px"}),
                html.Div(dcc.Graph(id=f"{name}-disk-history"), style={"width": "48%", "display": "inline-block", "padding": "10px"}),
                html.Div(dcc.Graph(id=f"{name}-io-history"), style={"width": "48%", "display": "inline-block", "padding": "10px"}),
                html.Div(dcc.Graph(id=f"{name}-net-history"), style={"width": "48%", "display": "inline-block", "padding": "10px"})
            ])
        ]) for name in VM_ENDPOINTS
    ]),
    dcc.Interval(id="update", interval=UPDATE_INTERVAL, n_intervals=0)
])


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

for name, url in VM_ENDPOINTS.items():
    @app.callback(
        [Output(f"{name}-cpu-graph", "figure"),
         Output(f"{name}-mem-graph", "figure"),
         Output(f"{name}-disk-graph", "figure"),
         Output(f"{name}-io-graph", "figure"),
         Output(f"{name}-net-graph", "figure"),
         Output(f"{name}-alerts", "children"),
         Output(f"{name}-cpu-history", "figure"),
         Output(f"{name}-mem-history", "figure"),
         Output(f"{name}-disk-history", "figure"),
         Output(f"{name}-io-history", "figure"),
         Output(f"{name}-net-history", "figure")],
        [Input("update", "n_intervals")],
        [State(f"{name}-cpu-thresh", "value"),
         State(f"{name}-mem-thresh", "value"),
         State(f"{name}-disk-thresh", "value"),
         State(f"{name}-io-thresh", "value"),
         State(f"{name}-net-thresh", "value")]
    )
    def update_graphs(n, cpu_t, mem_t, disk_t, io_t, net_t, url=url, name=name):
        try:
            res = requests.get(url, timeout=3).json()
            timestamp = datetime.now().strftime("%H:%M:%S")
            row = {
                "time": timestamp,
                "cpu": res["cpu"],
                "mem": res["memory"],
                "disk": res["disk"],
                "diskio": res["diskio"],
                "net": res["net"]
            }
            df = pd.DataFrame([row])
            df.to_csv(f"data/{name.lower()}_metrics.csv", mode='a', header=not os.path.exists(f"data/{name.lower()}_metrics.csv"), index=False)

            hist_df = pd.read_csv(f"data/{name.lower()}_metrics.csv")
            hist_df = hist_df.tail(50)

            alerts = []
            if res["cpu"] > cpu_t:
                alerts.append(f"{timestamp} – High CPU usage ({res['cpu']}%)")
            if res["memory"] > mem_t:
                alerts.append(f"{timestamp} – High Memory usage ({res['memory']}%)")
            if res["disk"] > disk_t:
                alerts.append(f"{timestamp} – High Disk usage ({res['disk']}%)")
            if res["diskio"] > io_t:
                alerts.append(f"{timestamp} – High Disk I/O ({res['diskio']} MB/s)")
            if res["net"] > net_t:
                alerts.append(f"{timestamp} – High Network usage ({res['net']} KB/s)")

            return (
                go.Figure(go.Indicator(mode="gauge+number", value=res["cpu"], title={"text": "CPU %"})),
                go.Figure(go.Indicator(mode="gauge+number", value=res["memory"], title={"text": "Memory %"})),
                go.Figure(go.Indicator(mode="gauge+number", value=res["disk"], title={"text": "Disk Usage %"})),
                go.Figure(go.Indicator(mode="number", value=res["diskio"], number={'suffix': " MB/s"}, title={"text": "Disk I/O"})),
                go.Figure(go.Indicator(mode="number", value=res["net"], number={'suffix': " KB/s"}, title={"text": "Network"})),
                html.Div([html.Div(alert) for alert in alerts]),
                make_line_fig(hist_df, "cpu", "CPU Usage Over Time", "%"),
                make_line_fig(hist_df, "mem", "Memory Usage Over Time", "%"),
                make_line_fig(hist_df, "disk", "Disk Usage Over Time", "%"),
                make_line_fig(hist_df, "diskio", "Disk I/O Over Time", "MB/s"),
                make_line_fig(hist_df, "net", "Network Usage Over Time", "KB/s")
            )

        except Exception as e:
            return (
                placeholder_fig("CPU Usage"),
                placeholder_fig("Memory Usage"),
                placeholder_fig("Disk Usage"),
                placeholder_fig("Disk I/O Rate"),
                placeholder_fig("Network Throughput"),
                f"Error: {str(e)}",
                placeholder_fig("CPU History"),
                placeholder_fig("Memory History"),
                placeholder_fig("Disk History"),
                placeholder_fig("Disk I/O History"),
                placeholder_fig("Network History")
            )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
