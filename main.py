#!/usr/bin/env python3
"""
File: main.py
Author: Jan Kühnemund
Description: Main entry point for the FastAPI application.
"""

from utils import setup_logging
import uvicorn

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
