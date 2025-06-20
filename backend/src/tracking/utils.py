from typing import Optional
from datetime import datetime
from fastapi import Request
from user_agents import parse

def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    user_agent = request.headers.get("user-agent", "")
    user_agent_info = parse(user_agent)
    
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": user_agent,
        "browser": user_agent_info.browser.family,
        "os": user_agent_info.os.family,
        "device": user_agent_info.device.family,
        "is_mobile": user_agent_info.is_mobile,
        "timestamp": datetime.utcnow()
    }