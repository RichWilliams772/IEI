from ..models import Breaker, Component

class ProtectionService:
    @staticmethod
    def check_breaker_status(breaker: Breaker) -> dict:
        """Check the status of a breaker for protection purposes"""
        return {
            "breaker_id": breaker.id,
            "state": breaker.state,
            "status": "closed" if breaker.state else "open",
            "is_operational": True
        }
    
    @staticmethod
    def check_system_protection(system_state: dict) -> dict:
        """Check overall system protection status"""
        # This would be more complex in a real implementation
        # For now, just return basic information
        
        breakers = [comp for comp in system_state["components"].values() 
                   if comp["type"] == "breaker"]
        
        total_breakers = len(breakers)
        open_breakers = sum(1 for b in breakers if not b["state"])
        closed_breakers = total_breakers - open_breakers
        
        return {
            "total_breakers": total_breakers,
            "open_breakers": open_breakers,
            "closed_breakers": closed_breakers,
            "system_status": "normal" if open_breakers == 0 else "partial_isolation"
        }