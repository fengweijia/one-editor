from typing import Dict, Any

def decide(job_ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {"decisions": {"rate_limit": {"rpm": 60}, "blacklist": [], "compliance_flags": [], "model_tiering": "standard"}}
