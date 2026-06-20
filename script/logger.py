import logging
import json
import os
from datetime import datetime

# Centralized logging configuration
LOG_FILE = "/home/wyndhamdesert/logs/gaiaflow.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "agent": getattr(record, "agent_name", "unknown"),
            "message": record.getMessage()
        }
        return json.dumps(log_record)

def get_logger(agent_name):
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    # Adapter to inject agent_name into logs
    return logging.LoggerAdapter(logger, {"agent_name": agent_name})
