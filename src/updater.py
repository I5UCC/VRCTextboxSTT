import sys
import git
import git.cmd
from helper import get_absolute_path, log
from subprocess import Popen, PIPE, STDOUT
import threading
import os

class Update_Handler(object):
    def __init__(self, repo_path: str = "..", script_path: str = __file__):
        self.script_path = script_path
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_latest_tag(self):
        self.fetch_tags()
        tags = sorted(self.repo.tags, key=lambda t: t.commit.committed_datetime)
        latest_tag = tags[-1]
        return str(latest_tag)
    
    def check_for_updates(self, current_version: str = None) -> tuple:
        if current_version is None:
            return False, None
        latest_tag = self.get_latest_tag()

        update_available = current_version != latest_tag

        return update_available, latest_tag
    
    def fetch_tags(self):
        git.Git(self.repo_path).execute("git fetch --all --tags")
    
    def pull(self):
        git.Git(self.repo_path).execute("git pull --rebase --autostash")

    def update(self, callback):
        
        def run_in_thread(callback):
            self.pull()
            requirements_file = "requirements.txt"
            if os.path.isfile(get_absolute_path("../python/CPU", self.script_path)):
                requirements_file = "requirements.cpu.txt"

            process = Popen([sys.executable, "-m", "pip", "install", "-U", "-r", get_absolute_path(requirements_file, self.script_path)], stdout=PIPE, stderr=STDOUT)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    log.debug(str(line)[2:-5])
            process.wait()
            process = Popen([sys.executable, "-m", "pip", "cache", "purge"], stdout=PIPE, stderr=STDOUT)
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    log.debug(str(line)[2:-5])
            process.wait()
            callback()

        thread = threading.Thread(target=run_in_thread, args=(callback,))
        thread.start()
        # returns immediately after the thread starts
        return thread
