import random
from pathlib import Path
from typing import List

import structlog

from agents.monitor.schemas import MonitorResult
from agents.monitor.prompts import MONITOR_SYSTEM_INSTRUCTION

log = structlog.get_logger()

class MonitorAgent:
    """
    Post-campaign watchdog that evaluates ROAS over a simulated 7-day period.
    """
    
    def __init__(self, campaign_id: str, roas_threshold: float = 1.5):
        self.campaign_id = campaign_id
        self.roas_threshold = roas_threshold
        # Note: In a fully ADK-integrated environment, we would initialize the LlmAgent here:
        # from google.adk.agents import LlmAgent
        # self.agent = LlmAgent(name="campaign_monitor", instruction=MONITOR_SYSTEM_INSTRUCTION, ...)
        
    def _mock_pause_campaign_tool(self) -> str:
        """
        Mock tool state to pause the campaign and stop budget drain.
        """
        log.warning("Active termination instruction executed. Tool called: pause_campaign", campaign_id=self.campaign_id)
        return "PAUSED_DUE_TO_ROAS"
        
    def _fetch_simulated_roas(self, day: int) -> float:
        """
        Simulates daily ROAS fetching with a downward trend.
        """
        base_roas = 2.5 - (day * 0.2)
        variance = random.uniform(-0.3, 0.4)
        return max(0.0, round(base_roas + variance, 2))

    def run_watchdog(self) -> MonitorResult:
        """
        Runs the 7-day monitoring loop, intervening if ROAS drops below the threshold.
        """
        log.info("Starting campaign monitor watchdog", campaign_id=self.campaign_id, limit=self.roas_threshold)
        
        daily_roas_log: List[float] = []
        days_tracked = 0
        termination_status = "COMPLETED"
        
        for day in range(1, 8):
            days_tracked = day
            roas = self._fetch_simulated_roas(day)
            daily_roas_log.append(roas)
            
            log.info(f"[Day {day}] Monitored ROAS: {roas}")
            
            if roas < self.roas_threshold:
                log.error(f"[Day {day}] ALERT: ROAS ({roas}) dropped below safety limit ({self.roas_threshold}).")
                
                # Immediately return an active termination instruction / call tool
                termination_status = self._mock_pause_campaign_tool()
                log.warning("Budget drain stopped.")
                break
        
        result = MonitorResult(
            campaign_id=self.campaign_id,
            days_tracked=days_tracked,
            daily_roas_log=daily_roas_log,
            termination_status=termination_status
        )
        
        # Save state cleanly
        workspace = Path(__file__).resolve().parent.parent.parent
        state_dir = workspace / ".state" / "monitor_runs"
        state_dir.mkdir(parents=True, exist_ok=True)
        out_path = state_dir / f"{self.campaign_id}_monitor.json"
        
        out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        
        log.info(
            "Monitoring finished", 
            campaign_id=self.campaign_id, 
            termination_status=termination_status, 
            days_tracked=days_tracked
        )
        
        return result

def run_monitor(campaign_id: str) -> MonitorResult:
    """Helper entry point for orchestration."""
    agent = MonitorAgent(campaign_id=campaign_id)
    return agent.run_watchdog()
