#################
#### imports ####
#################
import logging

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_basicauth import BasicAuth
from flask_login import LoginManager
from flask_dotenv import DotEnv
from flask_bcrypt import Bcrypt
from flask_restful import Api
from flask_rq import RQ

from project.database import db
from config import config as project_config

################
#### config ####
################


def read_env(app, config_class):
    """
    config environment variables and override with .env declared ones. use configuration given by environment
    variable APP_ENV if "config_class" is not given
    """
    env = DotEnv()
    env.init_app(app, env_file=".env")

    # get correct APP_ENV and right variable
    if not config_class:
        config_class = project_config.get(app.config.get('APP_ENV'))
    app.config.from_object(config_class)
    return app

def setup_logger(app):
    """
    config logger depending on APP_ENV
    """
    log_level = logging.DEBUG if app.config.get("TESTING") else logging.INFO
    log_format = "[%(asctime)s] {%(filename)s#%(funcName)s:%(lineno)d} %(levelname)s - %(message)s"
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(log_format))
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    # remove default Flask debug handler
    del app.logger.handlers[0]
    return app
    
    
app = Flask(__name__)
app = read_env(app, None)
app = setup_logger(app)

from project.users.views import users_blueprint
from project.home.views import home_blueprint
# register our blueprints
app.register_blueprint(users_blueprint)
app.register_blueprint(home_blueprint)

Bcrypt(app)
RQ(app)
basic_auth = BasicAuth(app)
db.init_app(app)

from project.models import User

# import custom login manager functions
login_manager = LoginManager(app)
login_manager.login_view = "users.login"
# jinja extensions
app.jinja_env.add_extension('jinja2.ext.do')

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()
