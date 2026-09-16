import asyncio
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF

from agent import run_agent_loop
from live_traffic import fetch_telemetry

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_stats = {
    "unique_flights": set(),
    "total_conflicts": 0,
    "conflict_logs": [] 
}

def process_airspace(airport_code):
    raw_telemetry = fetch_telemetry(airport_code)
    
    # Explicitly return empty arrays so the React frontend clears the radar
    if not raw_telemetry:
        return {"telemetry": [], "conflicts": [], "broadcasts": []}
        
    for ac in raw_telemetry:
        session_stats["unique_flights"].add(ac["id"])
        
    final_state = run_agent_loop(raw_telemetry)
    
    if final_state and final_state.get("conflicts"):
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        for conflict in final_state["conflicts"]:
            if not session_stats["conflict_logs"] or session_stats["conflict_logs"][-1]["detail"] != conflict:
                session_stats["conflict_logs"].append({
                    "time": current_time,
                    "detail": conflict
                })
                session_stats["total_conflicts"] += 1
                
    return final_state

@app.websocket("/ws/telemetry/{airport_code}")
async def websocket_endpoint(websocket: WebSocket, airport_code: str):
    await websocket.accept()
    try:
        while True:
            final_state = await asyncio.to_thread(process_airspace, airport_code)
            if final_state:
                await websocket.send_json({
                    "telemetry": final_state.get("telemetry", []),
                    "conflicts": final_state.get("conflicts", []),
                    "broadcasts": final_state.get("broadcasts", [])
                })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print("React frontend disconnected.")

@app.get("/download-report/{airport_code}")
def download_report(airport_code: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=12)
    
    pdf.cell(200, 10, txt="GLOBAL AIRSPACE AUTOMATED SHIFT REPORT", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Date/Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.cell(200, 10, txt=f"Unique Flights Tracked: {len(session_stats['unique_flights'])}", ln=True)
    pdf.cell(200, 10, txt=f"Total Conflicts Flagged (XGBoost): {session_stats['total_conflicts']}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Courier", style='B', size=11)
    pdf.cell(200, 10, txt="DETAILED CONFLICT LOG", ln=True)
    pdf.set_font("Courier", size=9)
    
    if not session_stats["conflict_logs"]:
        pdf.cell(200, 10, txt="No conflicts recorded during this session.", ln=True)
    else:
        for log in session_stats["conflict_logs"]:
            pdf.cell(25, 8, txt=log["time"], border=1)
            x_before = pdf.get_x()
            pdf.multi_cell(165, 8, txt=log["detail"], border=1)
            pdf.set_xy(x_before - 25, pdf.get_y())
            
    file_path = "shift_report.pdf"
    pdf.output(file_path)
    return FileResponse("shift_report.pdf", media_type="application/pdf", filename=f"Shift_Report_{airport_code}.pdf")