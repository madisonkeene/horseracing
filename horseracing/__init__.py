from flask import Flask, g, redirect, url_for, render_template
import os

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'tmp.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    # Register blueprints
    from . import auth
    app.register_blueprint(auth.bp)
    app.add_url_rule('/auth', endpoint='auth_index')

    from . import admin
    app.register_blueprint(admin.bp)
    app.add_url_rule('/admin', endpoint='admin.login')

    from . import bet
    app.register_blueprint(bet.bp)

    from . import leaderboard
    app.register_blueprint(leaderboard.bp)
    app.add_url_rule('/leaderboard', endpoint='leaderboard')

    from . import race
    app.register_blueprint(race.bp)

    # Home page
    @app.route('/')
    def index():
        if g.user == None:
            return redirect(url_for('auth_index'))
        return redirect(url_for('leaderboard'))

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def permission_denied(error):
        return render_template('errors/403.html'), 403

    return app