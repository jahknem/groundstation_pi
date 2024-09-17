#!/usr/bin/env python3
"""
File: utils.py
Author: Jan Kühnemund
Description: Utility functions.
"""


import logging

def setup_logging():
    """
    Sets up logging configurations.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.debug("Logging configured.")
    logging.info("Starting application.")
