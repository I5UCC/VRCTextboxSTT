import logging


class LogToFile(object):
    def __init__(self, logger, level, logfile):
        self.logger = logger
        self.level = level
        self.linebuf = ''

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
            filename=logfile,
            filemode='a'
        )

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass
