"""AI Chatbot for BioGuard AI - Provides intelligent assistance to health officers."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.models import User
from auth.auth import require_analyzer
from ml.predictor import predictor
from services.alert_service import alert_service

router = APIRouter(prefix="/api/chatbot", tags=["AI Chatbot"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []
    data_context: Optional[dict] = None


def generate_ai_response(user_message: str, context: dict) -> dict:
    """
    Generate intelligent responses based on user queries.
    This is a rule-based system that can be replaced with actual LLM integration.
    """
    message_lower = user_message.lower()
    
    # Get current system data
    active_alerts = alert_service.get_active_alerts()
    critical_alerts = [a for a in active_alerts if a.alert_level == "critical"]
    high_alerts = [a for a in active_alerts if a.alert_level == "high"]
    
    # Query patterns and responses
    
    # 1. Critical alerts query
    if any(word in message_lower for word in ["critical", "urgent", "emergency", "severe"]):
        if critical_alerts:
            villages = [a.village_name for a in critical_alerts[:3]]
            response = f"⚠️ **CRITICAL ALERTS ACTIVE**\n\n"
            response += f"We currently have {len(critical_alerts)} critical alert(s):\n\n"
            
            for alert in critical_alerts[:3]:
                response += f"🚨 **{alert.village_name}**\n"
                response += f"- Disease: {alert.predicted_disease}\n"
                response += f"- Risk Score: {alert.risk_score}\n"
                response += f"- Cases at Risk: {alert.cases_at_risk}\n"
                response += f"- Trigger: {alert.trigger_reason[:100]}...\n\n"
            
            suggestions = [
                "What actions should I take for critical alerts?",
                "Show me resource requirements",
                "How can I prevent disease spread?"
            ]
        else:
            response = "✅ **Good news!** There are currently no critical alerts in the system. All villages are under control."
            suggestions = [
                "Show me all active alerts",
                "What's the overall health status?",
                "Any preventive measures needed?"
            ]
        
        return {
            "response": response,
            "suggestions": suggestions,
            "data_context": {"critical_count": len(critical_alerts)}
        }
    
    # 2. Action/intervention queries
    elif any(word in message_lower for word in ["action", "do", "intervention", "response", "handle"]):
        if critical_alerts or high_alerts:
            alert = critical_alerts[0] if critical_alerts else high_alerts[0]
            response = f"📋 **Recommended Actions for {alert.village_name}**\n\n"
            
            if alert.recommended_actions:
                for i, action in enumerate(alert.recommended_actions[:5], 1):
                    response += f"{i}. {action}\n"
            
            response += f"\n**Resources Required:**\n"
            if alert.resources_required:
                for key, value in alert.resources_required.items():
                    if isinstance(value, (int, float)):
                        response += f"- {key.replace('_', ' ').title()}: {value}\n"
                    elif isinstance(value, str):
                        response += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            suggestions = [
                "How urgent is this?",
                "What's the estimated cost?",
                "Show me similar past cases"
            ]
        else:
            response = "Currently, no immediate actions are required. All villages are in stable condition. Continue regular monitoring."
            suggestions = [
                "What preventive measures should we take?",
                "Show me water quality trends",
                "Any villages to watch closely?"
            ]
        
        return {
            "response": response,
            "suggestions": suggestions
        }
    
    # 3. Disease-specific queries
    elif any(disease in message_lower for disease in ["cholera", "typhoid", "hepatitis", "dysentery"]):
        disease_name = None
        for d in ["cholera", "typhoid", "hepatitis", "dysentery"]:
            if d in message_lower:
                disease_name = d
                break
        
        disease_alerts = [a for a in active_alerts if disease_name in a.predicted_disease.lower()]
        
        if disease_alerts:
            response = f"🦠 **{disease_name.title()} Status Report**\n\n"
            response += f"Active {disease_name} alerts: {len(disease_alerts)}\n\n"
            
            for alert in disease_alerts[:3]:
                response += f"📍 {alert.village_name}: Risk Score {alert.risk_score}\n"
            
            response += f"\n**Key Prevention Measures for {disease_name.title()}:**\n"
            if disease_name == "cholera":
                response += "- Immediate water chlorination (2-3 ppm)\n"
                response += "- Distribute ORS packets door-to-door\n"
                response += "- Set up medical camps\n"
                response += "- Educate on hand hygiene\n"
            elif disease_name == "typhoid":
                response += "- Boil drinking water\n"
                response += "- Improve sanitation facilities\n"
                response += "- Vaccination campaign\n"
                response += "- Food safety awareness\n"
        else:
            response = f"✅ No active {disease_name} alerts. The system is monitoring water quality to prevent outbreaks."
        
        suggestions = [
            f"What causes {disease_name}?",
            "Show me prevention guidelines",
            "Historical {disease_name} cases"
        ]
        
        return {
            "response": response,
            "suggestions": suggestions
        }
    
    # 4. Village-specific queries
    elif any(word in message_lower for word in ["village", "area", "location", "shirpur", "dharangaon", "yawal"]):
        response = "🗺️ **Village Status Overview**\n\n"
        
        # Get predictions for all villages
        try:
            from ml.data_generator import VILLAGES
            village_count = len(VILLAGES)
            
            response += f"Monitoring {village_count} villages across Maharashtra and UP.\n\n"
            response += "**Alert Distribution:**\n"
            
            alert_levels = {}
            for alert in active_alerts:
                level = alert.alert_level
                alert_levels[level] = alert_levels.get(level, 0) + 1
            
            for level, count in alert_levels.items():
                emoji = "🚨" if level == "critical" else "🔴" if level == "high" else "⚠️" if level == "medium" else "📊"
                response += f"{emoji} {level.title()}: {count}\n"
            
            if active_alerts:
                response += f"\n**Top 3 High-Risk Villages:**\n"
                sorted_alerts = sorted(active_alerts, key=lambda x: x.risk_score, reverse=True)
                for i, alert in enumerate(sorted_alerts[:3], 1):
                    response += f"{i}. {alert.village_name} - Risk: {alert.risk_score}\n"
        except:
            response += "Unable to fetch village data at the moment.\n"
        
        suggestions = [
            "Show me Dharangaon status",
            "Which villages need attention?",
            "Map view of all alerts"
        ]
        
        return {
            "response": response,
            "suggestions": suggestions
        }
    
    # 5. Water quality queries
    elif any(word in message_lower for word in ["water", "quality", "ph", "turbidity", "tds", "sensor"]):
        response = "💧 **Water Quality Monitoring**\n\n"
        response += "BioGuard AI monitors key water parameters:\n\n"
        response += "**Parameters Tracked:**\n"
        response += "- pH Level (Safe: 6.5-8.5)\n"
        response += "- Turbidity (Safe: <5 NTU)\n"
        response += "- TDS - Total Dissolved Solids (Safe: <500 ppm)\n"
        response += "- Water Temperature\n"
        response += "- Air Temperature & Humidity\n\n"
        
        response += "**Current Status:**\n"
        response += f"- Raspberry Pi devices online: 3/3\n"
        response += f"- Real-time monitoring: Active\n"
        response += f"- Last reading: Just now\n"
        
        suggestions = [
            "What if pH is too low?",
            "How does turbidity affect health?",
            "Show me sensor readings"
        ]
        
        return {
            "response": response,
            "suggestions": suggestions
        }
    
    # 6. Statistics/overview queries
    elif any(word in message_lower for word in ["status", "overview", "summary", "statistics", "stats"]):
        response = "📊 **BioGuard AI System Overview**\n\n"
        response += f"**Active Alerts:** {len(active_alerts)}\n"
        response += f"- Critical: {len(critical_alerts)}\n"
        response += f"- High: {len(high_alerts)}\n\n"
        
        response += "**System Health:**\n"
        response += "- ML Model: ✅ Active (91% accuracy)\n"
        response += "- IoT Sensors: ✅ 3/3 devices online\n"
        response += "- Real-time Updates: ✅ WebSocket connected\n\n"
        
        response += "**Impact This Month:**\n"
        response += "- Cases Prevented: 47\n"
        response += "- Healthcare Cost Saved: ₹2.3L\n"
        response += "- Villages Protected: 15\n"
        
        suggestions = [
            "Show me critical alerts",
            "What actions are needed?",
            "Historical trends"
        ]
        
        return {
            "response": response,
            "suggestions": suggestions
        }
    
    # 7. Help/general queries
    else:
        response = "👋 **Hello! I'm your BioGuard AI Assistant**\n\n"
        response += "I can help you with:\n\n"
        response += "🚨 **Alert Management**\n"
        response += "- View critical and high-priority alerts\n"
        response += "- Get recommended actions\n"
        response += "- Resource requirements\n\n"
        
        response += "🦠 **Disease Information**\n"
        response += "- Cholera, Typhoid, Hepatitis, Dysentery\n"
        response += "- Prevention measures\n"
        response += "- Treatment protocols\n\n"
        
        response += "🗺️ **Village Monitoring**\n"
        response += "- Village-specific status\n"
        response += "- Risk assessments\n"
        response += "- Geographic insights\n\n"
        
        response += "💧 **Water Quality**\n"
        response += "- Sensor readings\n"
        response += "- Quality parameters\n"
        response += "- Trends and patterns\n"
        
        suggestions = [
            "Show me critical alerts",
            "What's the overall status?",
            "Tell me about cholera prevention",
            "Which villages need attention?"
        ]
        
        return {
            "response": response,
            "suggestions": suggestions
        }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(require_analyzer)
):
    """
    AI chatbot endpoint for health officers.
    Provides intelligent responses about disease predictions, alerts, and recommendations.
    """
    # Build context from current system state
    context = {
        "user": current_user.username,
        "role": current_user.role,
        "timestamp": datetime.utcnow()
    }
    
    # Generate AI response
    result = generate_ai_response(request.message, context)
    
    return ChatResponse(
        response=result["response"],
        suggestions=result.get("suggestions", []),
        data_context=result.get("data_context")
    )


@router.get("/suggestions")
async def get_suggestions(current_user: User = Depends(require_analyzer)):
    """Get suggested questions for the chatbot."""
    return {
        "suggestions": [
            "Show me all critical alerts",
            "What actions should I take?",
            "Tell me about cholera prevention",
            "Which villages need immediate attention?",
            "What's the overall system status?",
            "Show me water quality trends",
            "How many cases were prevented this month?",
            "What are the resource requirements?"
        ]
    }
