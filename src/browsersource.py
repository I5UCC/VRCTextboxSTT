import waitress
from flask import Flask, render_template_string, jsonify
from kthread import KThread
from config import obs_config
import requests
import traceback
import logging
import ctypes
import json
import os

log = logging.getLogger(__name__)

class FlaskAppWrapper(object):

    def __init__(self, app, port, **configs):
        self.app = app
        self.port = port
        self.running = False
        self.configs(**configs)
        self.server = waitress.create_server(self.app, host="127.0.0.1", port=self.port)
        self.flask_thread = KThread(target=self.server.run)

    def configs(self, **configs):
        for config, value in configs:
            self.app.config[config.upper()] = value

    def add_endpoint(self, endpoint=None, endpoint_name=None, handler=None, methods=['GET'], *args, **kwargs):
        self.app.add_url_rule(endpoint, endpoint_name, handler, methods=methods, *args, **kwargs)
    
    def start(self):
        if self.running:
            return True
        
        try:
            self.flask_thread.start()
            self.running = True
            return True
        except Exception:
            log.error(f"Error starting Waitress server: ")
            log.error(traceback.format_exc())
            return False

    def kill(self):
        if not self.running:
            return True

        try:
            self.flask_thread.kill()
            self.running = False
            return True
        except Exception:
            log.error(f"Error killing Waitress server: ")
            log.error(traceback.format_exc())
            return False

class OBSBrowserSource(object):

    def __init__(self, config: obs_config, template_path: str, cache_path: str):
        self.template_path = template_path
        self.text = ""
        self.finished = True
        self.config: obs_config = config
        self.running = False
        self.emotes = dict()
        self.emote_cache = cache_path + "emotes.json"
        if self.config.seventv.enabled and self.config.seventv.emote_set != "":
            self.emotes = self.get_7tv_emote_set(self.config.seventv.emote_set)
            open(self.emote_cache, "w").write(json.dumps(self.emotes, indent=4))
        try: 
            self.app = FlaskAppWrapper(Flask(__name__), self.config.port)
            self.app.add_endpoint('/', 'flask_root', self.flask_root, methods=['GET'])
            self.app.add_endpoint('/transcript', 'flask_get_transcript', self.flask_get_transcript, methods=['GET'])
            self.app.add_endpoint('/emotes', 'flask_get_emotes', self.flask_get_emotes, methods=['GET'])
        except:
            log.error(f"Couldn't initialize Browser source")
            log.error(traceback.format_exc())
        
    def get_7tv_emote_set(self, emote_set_id: str):
        try:
            r = requests.get(f"https://7tv.io/v3/emote-sets/{emote_set_id}")
            _emotes = dict((emote["name"], f'https://cdn.7tv.app/emote/{emote["data"]["id"]}/4x.webp') for emote in r.json()["emotes"])
            log.info(f"Loaded 7TV emote set {emote_set_id}, {len(_emotes)} emotes found.")
            return _emotes
        except KeyError:
            log.error(f"Couldn't get 7TV emote set {emote_set_id}")
            log.error("Either 7TV has Rate limited you or the emote set doesn't exist.")
            if os.path.isfile(self.emote_cache):
                log.error(f"Cached emotes found, using them instead.")
                return json.loads(open(self.emote_cache).read())
            else:
                ctypes.windll.user32.MessageBoxW(0, f"Couldn't get 7TV emote set {emote_set_id}\nEither 7TV has Rate limited you or the emote set doesn't exist.", "TextboxSTT - Unexpected Error", 0)
                return dict()

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
        _html = _html.replace("[SPEED]", str(self.config.speed))
        _html = _html.replace("[SIZE]", str(self.config.size))

        log.info("Website Accessed.")
        return render_template_string(_html)
    
    def flask_get_transcript(self):
        return jsonify(self.text, self.finished)
    
    def flask_get_emotes(self):
        return jsonify(self.emotes, "g" if self.config.seventv.case_sensitive else "gi")
    
    def start(self):
        self.running = True
        log.info(f"Flask server started on 127.0.0.1:{self.config.port}")
        return self.app.start()

    def stop(self):
        self.running = False
        return self.app.kill()

    def setText(self, text):
        self.text = text
    
    def setFinished(self, state):
        self.finished = state
