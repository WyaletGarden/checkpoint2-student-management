import logging
import os

# Xác định thư mục gốc của project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Gom tất cả thành 1 dòng duy nhất (bỏ hết các dấu \n)
log_format = "%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s"

def get_logger(name: str):
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Ghi ra file
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
        
        # In ra terminal
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.propagate = False
        
    return logger