import math
import requests

GLOBAL_AIRPORTS = {
    "LHR": {"lat": 51.4700, "lon": -0.4543, "name": "London Heathrow"},
    "JFK": {"lat": 40.6413, "lon": -73.7781, "name": "New York JFK"},
    "SIN": {"lat": 1.3644, "lon": 103.9915, "name": "Singapore Changi"},
    "MAA": {"lat": 12.9941, "lon": 80.1709, "name": "Chennai International"},
    "DXB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai International"}
}

# Extensive ICAO mapping covering major carriers for your 5 global hubs
ICAO_AIRLINES = {
    "BAW": "British Airways", "VIR": "Virgin Atlantic", "EZY": "easyJet", 
    "RYR": "Ryanair", "UAE": "Emirates", "QFA": "Qantas", "SIA": "Singapore Airlines",
    "DAL": "Delta Air Lines", "AAL": "American Airlines", "UAL": "United Airlines",
    "JBU": "JetBlue Airways", "AFR": "Air France", "DLH": "Lufthansa",
    "KLM": "KLM Royal Dutch", "SWR": "Swiss International", "AIC": "Air India", 
    "IGO": "IndiGo", "SEJ": "SpiceJet", "VTI": "Vistara", "AXM": "AirAsia", 
    "MAS": "Malaysia Airlines", "CPA": "Cathay Pacific", "THY": "Turkish Airlines", 
    "QTR": "Qatar Airways", "ETD": "Etihad Airways", "ACA": "Air Canada", 
    "WJA": "WestJet", "ANZ": "Air New Zealand", "ANA": "All Nippon Airways", 
    "JAL": "Japan Airlines", "KAL": "Korean Air", "CCA": "Air China", 
    "CES": "China Eastern", "CSN": "China Southern", "EFW": "European Air Transport", 
    "TAP": "TAP Air Portugal", "SAS": "SAS Scandinavian", "FIN": "Finnair", 
    "IBE": "Iberia", "AEA": "Air Europa", "SWA": "Southwest Airlines",
    "NKS": "Spirit Airlines", "FFT": "Frontier Airlines", "GFA": "Gulf Air",
    "OMA": "Oman Air", "SVA": "Saudia", "RJA": "Royal Jordanian", "MEA": "Middle East Airlines",
    "HAL": "Hawaiian Airlines", "ASA": "Alaska Airlines", "FDX": "FedEx Express",
    "UPS": "UPS Airlines", "GTI": "Atlas Air", "PAC": "Polar Air Cargo",
    "EXS": "Jet2", "WZZ": "Wizz Air", "BEE": "Flybe", "LOG": "Loganair"
}

def fetch_telemetry(airport_code="LHR"):
    center = GLOBAL_AIRPORTS.get(airport_code, GLOBAL_AIRPORTS["LHR"])
    url = f"https://api.adsb.lol/v2/lat/{center['lat']}/lon/{center['lon']}/dist/25"
    
    try:
        # Add a User-Agent to prevent Cloudflare/API blocking
        headers = {"User-Agent": "FlightRouter-PortfolioProject/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        
        # Catch HTML error pages (like 429 or 403) before .json() crashes
        if response.status_code != 200:
            print(f"API Blocked ({response.status_code}): {response.text[:40]}")
            return []
            
        data = response.json()
        telemetry = []
        scale_modifier = 0.4
        
        lon_scale = 60 * math.cos(math.radians(center['lat']))
        
        for ac in data.get('ac', []):
            if ac.get('alt_geom') and ac.get('alt_geom') > 1500 and ac.get('lat') and ac.get('lon'):
                y = (ac['lat'] - center['lat']) * 60 * scale_modifier
                x = (ac['lon'] - center['lon']) * lon_scale * scale_modifier
                
                callsign = ac.get("flight", "UNKNOWN").strip()
                operator_code = callsign[:3] if len(callsign) >= 3 else "Unknown"
                
                telemetry.append({
                    "id": callsign,
                    "x": x,
                    "y": y,
                    "z": ac['alt_geom'],
                    "wake_category": "Heavy" if ac.get("t") in ["B77W", "A388", "B789", "A359", "B748", "A333"] else "Medium",
                    "operator": ICAO_AIRLINES.get(operator_code, f"Unknown ({operator_code})")
                })
        return telemetry
    except Exception as e:
        print(f"API Error: {e}")
        return []