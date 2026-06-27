import dash
from dash import html
import flask

from app import logger
from app.components.sidebar import create_sidebar
from app.services.data_service import init_data
from app.routes.health import health_bp, mark_data_ready, mark_models_ready
from app.routes.forecast import forecast_bp

server = flask.Flask(__name__)


@server.before_request
def redirect_root():
    if flask.request.path == "/":
        return flask.redirect("/dashboard")

server.register_blueprint(health_bp)
server.register_blueprint(forecast_bp)

app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    pages_folder="pages",
    assets_folder="assets",
    suppress_callback_exceptions=True,
    title="Demand Forecast AI",
    update_title="Loading...",
)

app.layout = html.Div(
    className="app-container",
    children=[
        create_sidebar(),
        html.Main(
            className="main-content",
            children=[
                dash.page_container,
            ],
        ),
    ],
)


def _init_app():
    logger.info("Initializing application...")
    try:
        init_data()
        mark_data_ready()
        logger.info("Data loaded successfully")
    except Exception as e:
        logger.exception("Failed to load data: %s", e)

    try:
        from app.services.forecast_service import _load_module
        _load_module()
        mark_models_ready()
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.exception("Failed to load models: %s", e)


_init_app()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8000)
