import sys
from helper import get_absolute_path
import subprocess
import os
import traceback
import logging
import time
import ctypes
from packaging import version

log = logging.getLogger(__name__)

class Update_Handler(object):
    def __init__(self, git_path, repo_path: str = "..", script_path: str = __file__):
        self.script_path = script_path
        self.repo_path = repo_path
        self.git_path = git_path
        if not os.path.isfile(self.git_path):
            log.error("Git not found, using default path")
            self.git_path = "git"
        self.startupinfo = subprocess.STARTUPINFO()
        self.startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        self.startupinfo.wShowWindow = 0
        self.cache_folder = os.path.join(os.path.dirname(sys.executable), "cache")
        self.custom_env = {**os.environ, 'TMPDIR': self.cache_folder}

    def get_latest_tag(self):
        try:
            self.fetch()
            result = subprocess.run([self.git_path, "tag"], cwd=self.repo_path, stdout=subprocess.PIPE, startupinfo=self.startupinfo)
            tags = result.stdout.decode('utf-8')
            latest_tag = "v0.0.0"
            for tag in tags.split("\n"):
                if "-" in tag or tag == "":
                    continue
                if version.parse(tag) > version.parse(latest_tag):
                    latest_tag = tag
            return latest_tag
        except Exception:
            log.debug(traceback.format_exc())
            return None
    
    def check_for_updates(self, current_version: str = None) -> tuple:
        if current_version is None:
            return False, None

        latest_tag = self.get_latest_tag()
        log.debug("Latest Tag: " + str(latest_tag))

        if latest_tag is None or ("-" in latest_tag and "-" not in current_version):
            return False, None

        update_available = current_version != latest_tag

        return update_available, latest_tag

    def fetch(self):
        try:
            log.debug("Fetching Tags")
            result = subprocess.run([self.git_path, "fetch", "--all", "--tags", "--force"], cwd=self.repo_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=self.startupinfo)
            log.debug(result.stdout.decode('utf-8'))
        except Exception:
            log.debug(traceback.format_exc())

    def update(self, callback, ui_output):
        path = get_absolute_path("force_update.bat", self.script_path)
        process = subprocess.Popen([path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        while process.poll() is None:
            ui_output("Updating.")
            time.sleep(0.5)
            ui_output("Updating..")
            time.sleep(0.5)
            ui_output("Updating...")
            time.sleep(0.5)

        if process.returncode != 0:
            ctypes.windll.user32.MessageBoxW(0, "The Update process may have failed, please try again or run `force_update.bat` in the src folder as administator", f"TextboxSTT - Unexpected Error - {str(process.returncode)}", 0)
        else:
            ui_output("Update finished! Restarting...")
            time.sleep(1)
        callback()
