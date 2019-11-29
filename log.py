import logging
import os
import sys


class Log:
    log_enabled = False
    debug_func = None
    error_func = None
    info_func = None

    @classmethod
    def initialize(cls, delete_existing_file):
        cls.log_enabled = '-l' in sys.argv
        log_path = 'oc.log'
        if not delete_existing_file:
            if os.path.exists(log_path):
                os.remove(log_path)
        log_kwargs = dict()
        if cls.log_enabled:
            log_kwargs.update(dict(filename=log_path, filemode='a'))
        logging.basicConfig(
            **log_kwargs,
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%H:%M:%S',
            level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        if cls.log_enabled:
            cls.debug_func = logging.debug
            cls.info_func = logging.info
            cls.error_func = logging.error
        else:
            cls.debug_func = cls.info_func = cls.error_func = print

    @classmethod
    def debug(cls, *args, **kwargs):
        cls.debug_func(*args, **kwargs)

    @classmethod
    def info(cls, *args, **kwargs):
        cls.info_func(*args, **kwargs)

    @classmethod
    def error(cls, *args, **kwargs):
        cls.error_func(*args, **kwargs)
