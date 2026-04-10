"""
AI Shorts System - Logger Configuration
=========================================
Configuración de logging profesional.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formateador con colores para consola."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(
    name: str = "ai_shorts",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura y retorna un logger profesional.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
        log_file: Ruta del archivo de log (opcional)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    
    # Evitar duplicados
    if logger.hasHandlers():
        return logger
    
    # Formato
    fmt = "%(asctime)s │ %(levelname)-12s │ %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    
    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(fmt, datefmt)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler de archivo (si se especifica)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s │ %(name)s │ %(levelname)-12s │ %(message)s",
            datefmt
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Logger global
logger = setup_logger(
    name="ai_shorts",
    level=logging.INFO,
    log_file="logs/ai_shorts.log"
)


def log_execution(func):
    """Decorador para registrar ejecución de funciones."""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info(f"▶ {func.__name__}()")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"✓ {func.__name__}() completado")
            return result
        except Exception as e:
            logger.error(f"✗ {func.__name__}() falló: {e}")
            raise
    
    return wrapper