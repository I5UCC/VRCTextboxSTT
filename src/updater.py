import sys
from helper import get_absolute_path
from subprocess import run, Popen, PIPE, STDOUT, STARTUPINFO, STARTF_USESHOWWINDOW
import threading
import os
import traceback
import logging

log = logging.getLogger(__name__)

class Update_Handler(object):
    def __init__(self, git_path, repo_path: str = "..", script_path: str = __file__):
        self.script_path = script_path
        self.repo_path = repo_path
        self.git_path = git_path
        if not os.path.isfile(self.git_path):
            log.error("Git not found, using default path")
            self.git_path = "git"
        self.startupinfo = STARTUPINFO()
        self.startupinfo.dwFlags = STARTF_USESHOWWINDOW
        self.startupinfo.wShowWindow = 0

    def get_latest_tag(self):
        try:
            self.fetch()
            result = run([self.git_path, "tag"], cwd=self.repo_path, stdout=PIPE, startupinfo=self.startupinfo)
            tags = result.stdout.decode('utf-8')
            latest_tag = tags[tags.rfind("v"):].strip()
            return latest_tag
        except Exception:
            log.debug(traceback.format_exc())
            return None
    
    def check_for_updates(self, current_version: str = None) -> tuple:
        if current_version is None:
            return False, None

        latest_tag = self.get_latest_tag()
        log.debug("Latest Tag: " + str(latest_tag))

        if latest_tag is None:
            return False, None

        update_available = current_version != latest_tag

        return update_available, latest_tag
    
    def fetch(self):
        try:
            log.debug("Fetching Tags")
            result = run([self.git_path, "fetch", "--all", "--tags", "--force"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT, startupinfo=self.startupinfo)
            log.debug(result.stdout.decode('utf-8'))
        except Exception:
            log.debug(traceback.format_exc())

    def pull(self):
        try:
            self.fetch()
            result = run([self.git_path, "reset", "--hard"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT, startupinfo=self.startupinfo)
            log.debug(result.stdout.decode('utf-8'))
            result = run([self.git_path, "pull", "--rebase"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT, startupinfo=self.startupinfo)
            log.debug(result.stdout.decode('utf-8'))
        except Exception:
            log.debug(traceback.format_exc())

    def update(self, callback, ui_output):
        
        def run_in_thread(callback):
            ui_output("Updating... 0%")
            self.pull()
            requirements_file = "requirements.txt"
            if os.path.isfile(get_absolute_path("../python/CPU", self.script_path)):
                requirements_file = "requirements.cpu.txt"
            ui_output("Updating... 10%")

            process = Popen([sys.executable, "-m", "pip", "install", "-U", "-r", get_absolute_path(requirements_file, self.script_path), "--no-warn-script-location"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT, startupinfo=self.startupinfo)
            ui_output("Updating... 25%")
            i = 20
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    log.debug(str(line)[2:-5])
                    per = int((i/70)*100)
                    if per > 99:
                        per = 99
                    ui_output(f"Updating... {str(per)}%")
                    i += 1
            process.wait()
            ui_output("Updating... 99%")
            process = Popen([sys.executable, "-m", "pip", "cache", "purge"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT, startupinfo=self.startupinfo)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    log.debug(str(line)[2:-5])
            process.wait()
            ui_output("Updating... 100%")
            callback()

        thread = threading.Thread(target=run_in_thread, args=(callback,))
        thread.start()
        # returns immediately after the thread starts
        return thread
