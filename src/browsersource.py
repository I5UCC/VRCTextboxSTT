import waitress
from flask import Flask, render_template_string, jsonify
from kthread import KThread
from config import obs_config
from helper import log

class FlaskAppWrapper(object):

    def __init__(self, app, port, **configs):
        self.app = app
        self.port = port
        self.configs(**configs)
        self.server = waitress.create_server(self.app, host="127.0.0.1", port=self.port)
        self.flask_thread = KThread(target=self.server.run)

    def configs(self, **configs):
        for config, value in configs:
            self.app.config[config.upper()] = value

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=['GET'], *args, **kwargs):
        self.app.add_url_rule(endpoint, endpoint_name, handler, methods=methods, *args, **kwargs)
    
    def start(self):
        try:
            self.flask_thread.start()
            return True
        except Exception as e:
            log.error(f"Error starting Waitress server: {str(e)}")
            return False

    def kill(self):
        try:
            self.flask_thread.kill()
            return True
        except Exception as e:
            log.error(f"Error killing Waitress server: {str(e)}")
            return False

class OBSBrowserSource(object):

    def __init__(self, config: obs_config, template_path):
        self.template_path = template_path
        self.text = ""
        self.config: obs_config = config
        self.app = FlaskAppWrapper(Flask(__name__), self.config.port)
        self.app.add_endpoint('/', 'flask_root', self.flask_root, methods=['GET'])
        self.app.add_endpoint('/transcript', 'flask_get_transcript', self.flask_get_transcript, methods=['GET'])
        self.running = False

    def flask_root(self):
        _html = ""
        with open(self.template_path) as f:
            _html = f.read()
    
        _html = _html.replace("[COLOR]", self.config.color)
        _html = _html.replace("[SHADOW]", self.config.shadow_color)
        _html = _html.replace("[FONT]", self.config.font)
        _html = _html.replace("[ALIGN]", self.config.align)
        _html = _html.replace("[PORT]", str(self.config.port))
        _html = _html.replace("[INTERVAL]", str(self.config.update_interval))

        log.info("Website Accessed.")
        return render_template_string(_html)
    
    def flask_get_transcript(self):
        return jsonify(self.text)
    
    def start(self):
        self.running = True
        return self.app.start()

    def stop(self):
        self.running = False
        return self.app.kill()

    def setText(self, text):
        self.text = text