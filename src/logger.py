import logging
import os
import traceback
from datetime import datetime
import shutil
import psutil
from glob import glob
import sys

log = logging.getLogger(__name__)

class LogToFile(object):
    def __init__(self, cache_path):
        logfile = os.path.join(cache_path, 'latest.log')
        process_cache(cache_path, logfile)

        self.logger = log
        self.level = logging.DEBUG
        self.linebuf = ''
        self.ui_output = None

        logging.basicConfig(
            level=self.level,
            format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
            filename=logfile,
            filemode='a'
        )

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())
            if self.ui_output:
                self.ui_output(line.rstrip())

    def flush(self):
        pass

    def set_ui_output(self, output_method):
        self.ui_output = output_method
    
    def remove_ui_output(self):
        self.ui_output = None

def process_cache(cache_path, latest_log):
    try:
        os.mkdir(cache_path)
    except FileExistsError:
        pass
    except Exception:
        log.fatal("Failed to create cache directory: ")
        log.error(traceback.format_exc())

    try:
        logs = glob(cache_path + "/*.log")
        if len(logs) >= 5:
            logs.sort(key=os.path.getmtime)
            for log in logs[:-5]:
                os.remove(log)

        if os.path.isfile(latest_log):
            shutil.copy(latest_log, os.path.join(cache_path, datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")))
    except Exception:
        logging.error("Error processing old logs:")
        log.error(traceback.format_exc())

    open(latest_log, 'w').close()


def get_absolute_path(relative_path, script_path=__file__) -> str:
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(script_path)))
    return os.path.join(base_path, relative_path)


def force_single_instance():
    """Force single instance by killing other instances of the same Name."""

    try:
        _pid = os.getpid()
        _procname = psutil.Process(_pid).name()

        for proc in psutil.process_iter():
            if proc.name() == _procname and proc.pid != _pid:
                proc.kill()
    except Exception:
        pass
