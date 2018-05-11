import queue
import logging
import logging.handlers
import time
from functools import wraps

root = None
root_handler = None
root_formatter = None
root_listener = None
root_queue_handler = None
console_handler = None
app_log = None


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
    global root_handler
    global root
    logging.captureWarnings(True)
    if root_handler:
        root_handler.setLevel(root_level)
    if root:
        root.setLevel(root_level)
    logging.getLogger("py.warnings").setLevel(logging.ERROR)
    logging.getLogger("summa.preprocessing.cleaner").setLevel(logging.WARNING)
    logging.getLogger("gensim.models.word2vec").setLevel(logging.INFO)


"""
    Look at the bottom of this file:
    this function runs on this module's import.
"""


def config():
    from logr.config import *
    global root
    global root_handler
    global root_formatter
    global app_log
    if app_log is None:
        print("Configuring logging subsystem...")
        root_handler = logging.handlers.RotatingFileHandler(APP_LOG_FILE, mode='a', maxBytes=APP_LOG_SIZE,
                                                            backupCount=APP_LOG_BACKUPS, encoding='UTF-8', delay=False)
        if APP_LOG_FORMAT:
            root_formatter = logging.Formatter(APP_LOG_FORMAT)
            root_handler.setFormatter(root_formatter)
        root = logging.getLogger()
        root.addHandler(root_handler)
        root.propagate = False
        app_log = logging.getLogger(APP_NAME)
        __setlevels(APP_LOG_LEVEL)
    else:
        app_log.debug("Logging subsystem already configured.")


def console(root_level):
    global root
    global root_formatter
    global console_handler
    config()
    if console_handler is None:
        app_log.info("Starting console logging...")
        console_handler = logging.StreamHandler()
        if root_formatter:
            console_handler.setFormatter(root_formatter)
        root.addHandler(console_handler)
        __setlevels(root_level)
    else:
        app_log.info("Async logging has already been started.")
    return app_log


def detach_console():
    global root
    global console_handler
    config()
    if console_handler is None:
        app_log.info("Console logging is not enabled.")
    else:
        app_log.info("Stopping console logging...")
        try:
            root.removeHandler(console_handler)
        except:
            pass
        finally:
            console_handler = None


def start_async_logging():
    from logr.config import *
    ###
    # For Python 3 logging configuration, please refer to https://docs.python.org/3/howto/logging-cookbook.html
    ###
    global root_handler
    global root_listener
    global root_queue_handler
    global root
    config()
    if root_queue_handler is None:
        app_log.info("Starting async logging...")
        ###
        # Limit Queue size to python_asynch_logging_queue_size (100K) records.
        # When Queue reaches this size, insertions will block until records are consumed.
        # For details, please refer to https://docs.python.org/3/library/queue.html 
        ###    
        root_queue = queue.Queue(APP_LOG_QUEUE_SIZE)
        root_queue_handler = logging.handlers.QueueHandler(root_queue)
        root_listener = logging.handlers.QueueListener(root_queue, root_handler, respect_handler_level=True)
        root_listener.start()
        root.addHandler(root_queue_handler)
        root.removeHandler(root_handler)
    else:
        app_log.info("Async logging has already been started.")


def stop_async_logging():
    global root
    global root_listener
    global root_handler
    global root_queue_handler
    config()
    if root_queue_handler is None:
        app_log.info("Async logging is not running.")
    else:
        app_log.info("Stopping async logging...")
        try:
            root.addHandler(root_handler)
            if root_queue_handler:
                root.removeHandler(root_queue_handler)
            if root_listener:
                root_listener.stop()
        except:
            pass
        finally:
            root_queue_handler = None


config()
