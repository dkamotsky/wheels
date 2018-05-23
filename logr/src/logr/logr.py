import queue
import logging
import logging.handlers
import time
from functools import wraps


__default_logger = logging.getLogger("logr_default")

__root = None
__root_handler = None
__root_formatter = None
__root_listener = None
__root_queue_handler = None
__console_handler = None
app_log = __default_logger


def elapsed_log(func):
    """
    generates a 'time elapsed' debug log for decorated function execution, in s
    :param func: function
    :return: decorator
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        _start = time.time()
        result = func(*args, **kwargs)
        _time = time.time() - _start
        app_log.debug("[%s] complete. Time elapsed: %.2f s", func.__name__, _time)
        return result

    return wrapper


def __setlevels(root_level):
    global __root_handler
    global __root
    logging.captureWarnings(True)
    if __root_handler:
        __root_handler.setLevel(root_level)
    if __root:
        __root.setLevel(root_level)
    logging.getLogger("py.warnings").setLevel(logging.ERROR)
    logging.getLogger("summa.preprocessing.cleaner").setLevel(logging.WARNING)
    logging.getLogger("gensim.models.word2vec").setLevel(logging.INFO)


"""
    Look at the bottom of this file:
    this function runs on this module's import.
"""


def config():
    import logr.config
    global __root
    global __root_handler
    global __root_formatter
    global app_log
    if app_log is __default_logger:
        app_log.info("Configuring logging subsystem...")
        __root_handler = logging.handlers.RotatingFileHandler(logr.config.APP_LOG_FILE, mode='a', maxBytes=logr.config.APP_LOG_SIZE,
                                                              backupCount=logr.config.APP_LOG_BACKUPS, encoding='UTF-8', delay=False)
        if logr.config.APP_LOG_FORMAT:
            __root_formatter = logging.Formatter(logr.config.APP_LOG_FORMAT)
            __root_handler.setFormatter(__root_formatter)
        __root = logging.getLogger()
        __root.addHandler(__root_handler)
        __root.propagate = False
        app_log = logging.getLogger(logr.config.APP_NAME)
        __setlevels(logr.config.APP_LOG_LEVEL)
    else:
        app_log.debug("Logging subsystem already configured.")


def console(root_level = logging.INFO):
    global __root
    global __root_formatter
    global __console_handler
    config()
    if __console_handler is None:
        app_log.info("Starting console logging...")
        __console_handler = logging.StreamHandler()
        if __root_formatter:
            __console_handler.setFormatter(__root_formatter)
        __root.addHandler(__console_handler)
        __setlevels(root_level)
    else:
        app_log.info("Console logging has already been started.")
    return app_log


def detach_console():
    global __root
    global __console_handler
    config()
    if __console_handler is None:
        app_log.info("Console logging is not enabled.")
    else:
        app_log.info("Stopping console logging...")
        try:
            __root.removeHandler(__console_handler)
        except:
            pass
        finally:
            __console_handler = None


def start_async_logging():
    import logr.config
    ###
    # For Python 3 logging configuration, please refer to https://docs.python.org/3/howto/logging-cookbook.html
    ###
    global __root_handler
    global __root_listener
    global __root_queue_handler
    global __root
    config()
    if __root_queue_handler is None:
        app_log.info("Starting async logging...")
        ###
        # Limit Queue size to python_asynch_logging_queue_size (100K) records.
        # When Queue reaches this size, insertions will block until records are consumed.
        # For details, please refer to https://docs.python.org/3/library/queue.html
        ###
        root_queue = queue.Queue(logr.config.APP_LOG_QUEUE_SIZE)
        __root_queue_handler = logging.handlers.QueueHandler(root_queue)
        __root_listener = logging.handlers.QueueListener(root_queue, __root_handler, respect_handler_level=True)
        __root_listener.start()
        __root.addHandler(__root_queue_handler)
        __root.removeHandler(__root_handler)
    else:
        app_log.info("Async logging has already been started.")


def stop_async_logging():
    global __root
    global __root_listener
    global __root_handler
    global __root_queue_handler
    config()
    if __root_queue_handler is None:
        app_log.info("Async logging is not running.")
    else:
        app_log.info("Stopping async logging...")
        try:
            __root.addHandler(__root_handler)
            if __root_queue_handler:
                __root.removeHandler(__root_queue_handler)
            if __root_listener:
                __root_listener.stop()
        except:
            pass
        finally:
            __root_queue_handler = None
