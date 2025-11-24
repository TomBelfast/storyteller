import logging
import io

class StreamlitLogHandler(logging.Handler):
    """
    A custom logging handler that stores logs in a buffer 
    so they can be displayed in Streamlit.
    """
    def __init__(self):
        super().__init__()
        self.log_buffer = io.StringIO()

    def emit(self, record):
        msg = self.format(record)
        self.log_buffer.write(msg + "\n")

    def get_logs(self):
        return self.log_buffer.getvalue()

def setup_logging():
    """
    Configures the root logger to write to console and a Streamlit-accessible buffer.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Streamlit Handler (for UI display)
    streamlit_handler = StreamlitLogHandler()
    streamlit_handler.setFormatter(formatter)
    logger.addHandler(streamlit_handler)

    return streamlit_handler
