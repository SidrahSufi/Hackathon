import os
import yaml
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ValidationResult:
    """
    Structured response object for policy validation results.
    """
    is_valid: bool
    policy_name: str
    message: str
    details: Optional[Dict[str, Any]] = None

class PolicyChecker:
    """
    Enforces business policies defined in a YAML configuration file.
    """
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.policies: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Loads the YAML configuration file containing the policies."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Policy configuration file not found at: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as file:
            try:
                self.policies = yaml.safe_load(file) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML policy file: {e}")

    def check_budget(self, requested_amount: float) -> ValidationResult:
        """
        Validates if the requested amount is within the budget cap.
        """
        budget_policy = self.policies.get("budget", {})
        cap = budget_policy.get("cap", 0)
        currency = budget_policy.get("currency", "UNKNOWN")
        
        if requested_amount <= cap:
            return ValidationResult(
                is_valid=True,
                policy_name="budget_cap",
                message=f"Budget request is within the {cap} {currency} limit.",
                details={"requested": requested_amount, "cap": cap, "currency": currency}
            )
        else:
            return ValidationResult(
                is_valid=False,
                policy_name="budget_cap",
                message=f"Requested amount ({requested_amount}) exceeds the budget cap ({cap} {currency}).",
                details={"requested": requested_amount, "cap": cap, "currency": currency}
            )

    def check_discount(self, requested_discount_pct: float, projected_margin_pct: float) -> ValidationResult:
        """
        Validates discount limits and margin floor.
        """
        discount_policy = self.policies.get("discount", {})
        max_pct = discount_policy.get("max_pct", 0)
        margin_floor_pct = discount_policy.get("margin_floor_pct", 100)
        
        errors = []
        is_valid = True
        
        if requested_discount_pct > max_pct:
            is_valid = False
            errors.append(f"Discount {requested_discount_pct}% exceeds maximum of {max_pct}%.")
            
        if projected_margin_pct < margin_floor_pct:
            is_valid = False
            errors.append(f"Projected margin {projected_margin_pct}% is below the floor of {margin_floor_pct}%.")
            
        return ValidationResult(
            is_valid=is_valid,
            policy_name="discount_and_margin",
            message=" | ".join(errors) if not is_valid else "Discount and margin policies met.",
            details={
                "requested_discount_pct": requested_discount_pct,
                "max_discount_pct": max_pct,
                "projected_margin_pct": projected_margin_pct,
                "margin_floor_pct": margin_floor_pct
            }
        )

    def check_rate_limit(self, api_name: str, current_usage: int) -> ValidationResult:
        """
        Validates if the current usage is within the defined rate limits for an API.
        """
        rate_limits = self.policies.get("rate_limits", {})
        limit = rate_limits.get(api_name)
        
        if limit is None:
            # If no limit is defined, assume unrestricted
            return ValidationResult(
                is_valid=True, 
                policy_name=f"rate_limit_{api_name}",
                message=f"No rate limit defined for {api_name}.",
                details={"current_usage": current_usage}
            )
            
        if current_usage < limit:
            return ValidationResult(
                is_valid=True,
                policy_name=f"rate_limit_{api_name}",
                message="Usage is within rate limits.",
                details={"current_usage": current_usage, "limit": limit}
            )
        else:
            return ValidationResult(
                is_valid=False,
                policy_name=f"rate_limit_{api_name}",
                message=f"Rate limit exceeded for {api_name}. Usage: {current_usage}, Limit: {limit}.",
                details={"current_usage": current_usage, "limit": limit}
            )

    def check_notification_window(self, check_time: Optional[datetime] = None) -> ValidationResult:
        """
        Validates if the given time (or current time) falls within the allowed notification window.
        """
        window = self.policies.get("notification_window", {})
        start_str = window.get("start", "00:00")
        end_str = window.get("end", "23:59")
        
        if check_time is None:
            check_time = datetime.now()
            
        current_time_str = check_time.strftime("%H:%M")
        
        # String comparison works elegantly for HH:MM format
        is_within_window = start_str <= current_time_str <= end_str
        
        if is_within_window:
            return ValidationResult(
                is_valid=True,
                policy_name="notification_window",
                message="Current time is within the notification window.",
                details={"current_time": current_time_str, "window_start": start_str, "window_end": end_str}
            )
        else:
            return ValidationResult(
                is_valid=False,
                policy_name="notification_window",
                message=f"Current time ({current_time_str}) is outside the allowed window ({start_str} - {end_str}).",
                details={"current_time": current_time_str, "window_start": start_str, "window_end": end_str}
            )

    def validate_all(self, context: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Helper method to run multiple validations based on a provided context dictionary.
        """
        results = {}
        
        if "requested_amount" in context:
            results["budget"] = self.check_budget(context["requested_amount"])
            
        if "requested_discount_pct" in context and "projected_margin_pct" in context:
            results["discount"] = self.check_discount(
                context["requested_discount_pct"], 
                context["projected_margin_pct"]
            )
            
        if "api_usage" in context:
            for api_name, usage in context["api_usage"].items():
                results[f"rate_limit_{api_name}"] = self.check_rate_limit(api_name, usage)
                
        # Always check time window
        check_time = context.get("check_time")
        results["notification_window"] = self.check_notification_window(check_time)
        
        return results

if __name__ == "__main__":
    # Local execution testing
    import sys
    
    # Resolving the absolute path relative to the current file structure for the YAML config
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    yaml_path = os.path.join(base_dir, 'agents', 'config', 'policies.yaml')
    
    try:
        checker = PolicyChecker(yaml_path)
        
        print("--- Testing Valid Inputs ---")
        res1 = checker.check_budget(500000)
        print(f"Budget (500000): {res1}")
        
        res2 = checker.check_discount(15, 20)
        print(f"Discount (15%, margin 20%): {res2}")
        
        res3 = checker.check_rate_limit("notification_api", 4000)
        print(f"Rate Limit (4000/5000): {res3}")
        
        # Test time inside window
        dt_in_window = datetime.strptime("14:00", "%H:%M")
        res4 = checker.check_notification_window(dt_in_window)
        print(f"Time (14:00): {res4}")
        
        print("\n--- Testing Invalid Inputs ---")
        bad_budget = checker.check_budget(1000000)
        print(f"Budget (1000000): {bad_budget}")
        
        bad_discount = checker.check_discount(25, 15)
        print(f"Discount (25%, margin 15%): {bad_discount}")
        
        dt_out_window = datetime.strptime("08:00", "%H:%M")
        bad_time = checker.check_notification_window(dt_out_window)
        print(f"Time (08:00): {bad_time}")
        
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
