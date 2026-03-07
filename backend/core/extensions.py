"""
Shared Flask extensions — instantiated without an app so blueprints can
import them freely, then initialised via init_app() in app.py.
"""
from flask_jwt_extended import JWTManager

jwt = JWTManager()
