from flask import Flask
from app.routes import dashboard, watchlist, run_screening, ai_recommendation

def create_app():
    app = Flask(__name__)

    # Register Blueprint
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(watchlist.bp)
    app.register_blueprint(run_screening.bp)
    app.register_blueprint(ai_recommendation.bp)

    return app
