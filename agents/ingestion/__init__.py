"""
Ingestion Agent package.
"""
from agents.ingestion.schemas import IngestionResult, Signal
from agents.ingestion.agent import run_ingestion

__all__ = ["Signal", "IngestionResult", "run_ingestion"]
