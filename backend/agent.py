import xgboost as xgb
import numpy as np
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
import os
from langchain_groq import ChatGroq

try:
    safety_model = xgb.XGBClassifier()
    safety_model.load_model("wake_safety_model.ubj")
except xgb.core.XGBoostError:
    print("[WARNING] wake_safety_model.ubj not found. Run train_wake_model.py first.")
    safety_model = None

@tool
def issue_descent_clearance(callsign: str):
    """Issues a descent clearance to an aircraft."""
    pass

@tool
def divert_heavy_aircraft(callsign: str):
    """Diverts a heavy aircraft to a different holding pattern."""
    pass

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY")
).bind_tools([issue_descent_clearance, divert_heavy_aircraft])

class AgentState(TypedDict):
    telemetry: List[Dict[str, Any]]
    conflicts: List[str]
    commands: List[str]
    messages: List[Any]

def check_safety_override(ac1, ac2):
    if not safety_model:
        return False
        
    alt_diff = abs(ac1['z'] - ac2['z'])
    lat_dist = np.sqrt((ac1['x'] - ac2['x'])**2 + (ac1['y'] - ac2['y'])**2)
    
    is_lead_heavy = 1 if ac1['wake_category'] == 'Heavy' else 0
    is_trail_heavy = 1 if ac2['wake_category'] == 'Heavy' else 0
    
    features = np.array([[alt_diff, lat_dist, is_lead_heavy, is_trail_heavy]])
    return bool(safety_model.predict(features)[0])

def detect_conflicts(state: AgentState):
    telemetry = state["telemetry"]
    conflicts = []
    
    for i in range(len(telemetry)):
        for j in range(i + 1, len(telemetry)):
            ac1 = telemetry[i]
            ac2 = telemetry[j]
            
            if check_safety_override(ac1, ac2):
                conflicts.append(
                    f"Wake/Separation Warning predicted between {ac1['id']} ({ac1['wake_category']}) "
                    f"and {ac2['id']} ({ac2['wake_category']})."
                )
    return {"conflicts": conflicts}

def call_llm(state: AgentState):
    conflicts = state["conflicts"]
    commands = []
    
    if not conflicts:
        return {"commands": [], "messages": []}
        
    prompt = f"Active airspace conflicts detected:\n{chr(10).join(conflicts)}\nResolve these using available tools."
    messages = [
        SystemMessage(content="You are an autonomous ATC safety agent. Use tools to resolve airspace conflicts."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "issue_descent_clearance":
                target = tool_call.get("args", {}).get("callsign", "UNKNOWN")
                commands.append(f"CLEAR_{target}_DESCENT")
            elif tool_call["name"] == "divert_heavy_aircraft":
                target = tool_call.get("args", {}).get("callsign")
                if target:
                    commands.append(f"DIVERT_{target}")
                    
    return {"commands": commands, "messages": [response]}

def safety_gatekeeper(state: AgentState):
    conflicts = state["conflicts"]
    commands = state["commands"]
    final_commands = []
    
    broadcasts = [f"System Alert: {c}" for c in conflicts]
    
    for cmd in commands:
        if "CLEAR" in cmd and len(conflicts) > 0:
            print("\n[SYSTEM OVERRIDE] LLM attempted unsafe clearance. Command blocked.")
        else:
            final_commands.append(cmd)
            if "DIVERT" in cmd:
                target = cmd.split("_")[1]
                broadcasts.append(f"{target}, traffic alert. Immediate diversion required. Turn right heading zero four zero.")
            elif "DESCENT" in cmd:
                target = cmd.split("_")[1]
                broadcasts.append(f"{target}, cleared for descent. Maintain safe separation.")
            
    return {"commands": final_commands, "broadcasts": broadcasts}

workflow = StateGraph(AgentState)
workflow.add_node("detect_conflicts", detect_conflicts)
workflow.add_node("call_llm", call_llm)
workflow.add_node("safety_gatekeeper", safety_gatekeeper)

workflow.set_entry_point("detect_conflicts")
workflow.add_edge("detect_conflicts", "call_llm")
workflow.add_edge("call_llm", "safety_gatekeeper")
workflow.add_edge("safety_gatekeeper", END)

app = workflow.compile()

def run_agent_loop(raw_telemetry: List[Dict[str, Any]]):
    initial_state = {
        "telemetry": raw_telemetry,
        "conflicts": [],
        "commands": [],
        "messages": []
    }
    
    final_state = app.invoke(initial_state)
    return {
        "telemetry": final_state["telemetry"],
        "conflicts": final_state["conflicts"],
        "broadcasts": final_state.get("broadcasts", [])
    }