import time
import random
import logging
from typing import Iterator, Dict, Any

class StreamingLogger:
    """
    Standard logger configuration for the monitor to stream logs to stdout.
    """
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

logger = StreamingLogger("BizPulseMonitor")

class CampaignMonitor:
    """
    Monitors a campaign's Return On Ad Spend (ROAS) and enforces business rules
    such as auto-pausing the campaign if performance drops below a threshold.
    """
    
    def __init__(self, campaign_id: str, roas_threshold: float = 1.5):
        self.campaign_id = campaign_id
        self.roas_threshold = roas_threshold
        self.is_paused = False

    def fetch_daily_roas(self, day: int) -> float:
        """
        Simulates fetching the daily ROAS metric from an external ad network API
        (e.g., Google Ads, Meta Ads).
        
        Args:
            day: The current day of the simulation.
            
        Returns:
            The simulated ROAS value.
        """
        # Create a simulated downward trend with some random variance
        # Starts strong around ~2.5, trends downwards by 0.2 per day
        base_roas = 2.5 - (day * 0.2) 
        variance = random.uniform(-0.3, 0.4)
        return max(0.0, round(base_roas + variance, 2))

    def auto_pause_campaign(self):
        """
        Executes the API call to pause the campaign in the external ad network.
        """
        logger.warning(f"ACTION REQUIRED: Auto-pausing campaign '{self.campaign_id}' to prevent budget drain.")
        # In a real environment, you would call the Ad Network API here.
        time.sleep(0.5) # Simulate API latency
        self.is_paused = True
        logger.info(f"Campaign '{self.campaign_id}' successfully paused.")

    def stream_monitoring(self, total_days: int = 7) -> Iterator[Dict[str, Any]]:
        """
        Simulates continuous monitoring over a given number of days.
        Yields a stream of log events and structured metrics.
        
        Args:
            total_days: Number of days to simulate monitoring for.
            
        Yields:
            Dictionary containing daily metrics and status.
        """
        logger.info(f"Initializing {total_days}-day monitoring for campaign '{self.campaign_id}'.")
        logger.info(f"Active ROAS Threshold: {self.roas_threshold}")
        
        for day in range(1, total_days + 1):
            if self.is_paused:
                logger.info(f"[Day {day}] Monitoring bypassed. Campaign is in paused state.")
                yield {"day": day, "status": "paused"}
                continue
                
            logger.info(f"[Day {day}] Fetching campaign performance metrics...")
            
            # Simulate processing delay to create a streaming effect
            time.sleep(1.0)
            
            current_roas = self.fetch_daily_roas(day)
            logger.info(f"[Day {day}] Evaluated ROAS: {current_roas}")
            
            result = {
                "day": day,
                "roas": current_roas,
                "status": "active"
            }
            
            if current_roas < self.roas_threshold:
                logger.error(f"[Day {day}] ALERT: ROAS ({current_roas}) dropped below safety threshold ({self.roas_threshold})!")
                self.auto_pause_campaign()
                result["status"] = "paused"
            elif current_roas < self.roas_threshold + 0.3:
                logger.warning(f"[Day {day}] WARNING: ROAS ({current_roas}) is approaching the safety threshold ({self.roas_threshold})!")
                result["status"] = "warning"
                
            yield result

if __name__ == "__main__":
    # Local execution / Simulation test
    monitor = CampaignMonitor(campaign_id="camp_winback_east_002", roas_threshold=1.5)
    
    print("--- Starting Monitor Stream ---")
    
    # Consume the generator to trigger the simulated streaming execution
    try:
        for daily_update in monitor.stream_monitoring(total_days=7):
            print(f"Emitted Payload: {daily_update}\n")
            time.sleep(0.5) # Additional pacing for readability in console
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user.")
