import logging
import queue

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(f"{msg}\n")
        except Exception:
            self.handleError(record)

def setup_logging(log_queue):
    """Set up logging to capture terminal output"""
    # Remove existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create queue handler
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(queue_handler) 