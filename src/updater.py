import sys
from helper import get_absolute_path, log
from subprocess import run, Popen, PIPE, STDOUT
import threading
import os
import traceback

class Update_Handler(object):
    def __init__(self, git_path, repo_path: str = "..", script_path: str = __file__):
        self.script_path = script_path
        self.repo_path = repo_path
        self.git_path = git_path
        if not os.path.isfile(self.git_path):
            log.error("Git not found, using default path")
            self.git_path = "git"

    def get_latest_tag(self):
        try:
            self.fetch()
            result = run([self.git_path, "tag"], cwd=self.repo_path, stdout=PIPE)
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
            result = run([self.git_path, "fetch", "--all", "--tags"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT)
            log.debug(result.stdout.decode('utf-8'))
        except Exception:
            log.debug(traceback.format_exc())

    def pull(self):
        try:
            self.fetch()
            result = run([self.git_path, "reset", "--hard"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT)
            log.debug(result.stdout.decode('utf-8'))
            result = run([self.git_path, "reset", "pull"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT)
            log.debug(result.stdout.decode('utf-8'))
        except Exception:
            log.debug(traceback.format_exc())

    def update(self, callback):
        
        def run_in_thread(callback):
            self.pull()
            requirements_file = "requirements.txt"
            if os.path.isfile(get_absolute_path("../python/CPU", self.script_path)):
                requirements_file = "requirements.cpu.txt"

            process = Popen([sys.executable, "-m", "pip", "install", "-U", "-r", get_absolute_path(requirements_file, self.script_path), "--no-warn-script-location"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    log.debug(str(line)[2:-5])
            process.wait()
            process = Popen([sys.executable, "-m", "pip", "cache", "purge"], cwd=self.repo_path, stdout=PIPE, stderr=STDOUT)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    log.debug(str(line)[2:-5])
            process.wait()
            callback()

        thread = threading.Thread(target=run_in_thread, args=(callback,))
        thread.start()
        # returns immediately after the thread starts
        return thread
