"""
Insight Agent package.
"""
from agents.insight.schemas import Insight, InsightResult
from agents.insight.agent import run_insight

__all__ = ["Insight", "InsightResult", "run_insight"]
