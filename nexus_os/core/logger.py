import logging

def setup_logger(log_level):
    logger = logging.getLogger("nexus_os")
    logger.setLevel(getattr(logging, log_level.upper()))
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, log_level.upper()))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
