import os, json, requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
BASE=os.environ["SUPABASE_URL"].strip().rstrip("/")
KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"].strip()
HEAD={"apikey":KEY,"Authorization":"Bearer "+KEY}
SINCE=(datetime.now(timezone.utc)-timedelta(days=7)).isoformat()
def read(table,fields,filters):
    output=[]
    for offset in range(0,10000,1000):
        params={"select":fields,"measured_at":"gte."+SINCE,"order":"measured_at.asc","limit":"1000","offset":str(offset),**filters}
        r=requests.get(BASE+"/rest/v1/"+table,headers=HEAD,params=params,timeout=30)
        if not r.ok:
            try:
                err = r.json()
                code = str(err.get("code", "onbekend")) if isinstance(err, dict) else "onbekend"
                message = str(err.get("message", "geen bericht")) if isinstance(err, dict) else "geen bericht"
                print(f"Supabase foutcode: {code[:120]}", flush=True)
                print(f"Supabase melding: {message[:240]}", flush=True)
            except ValueError:
                print("Supabase gaf geen JSON-foutmelding.", flush=True)
            raise RuntimeError(f"Export {table} failed with HTTP {r.status_code}")
        batch=r.json()
        output.extend(batch)
        if len(batch)<1000:break
    return output
p1=read("p1_measurements","measured_at,net_power_w",{"location_name":"eq.Fleur en Stef"})
solar=read("solar_production","measured_at,power_w",{"inverter_serial":"eq.7E0FC0FE-4B"})
# Estimate typical house baseload from observed night imports (00:00-05:00).
# A conservative default is used until enough readings exist.
from statistics import median
from zoneinfo import ZoneInfo
night=[]
for row in p1:
    try:
        hour=datetime.fromisoformat(row["measured_at"].replace("Z","+00:00")).astimezone(ZoneInfo("Europe/Amsterdam")).hour
        if 0<=hour<5 and 0<=float(row["net_power_w"])<=2500:
            night.append(float(row["net_power_w"]))
    except (ValueError,TypeError,KeyError):
        pass
base_w=round(median(night)) if len(night)>=12 else 450
base_w=max(150,min(1500,base_w))
forecast={"status":"unavailable","hours":[],"baseline_w":base_w}
try:
    r=requests.get("https://api.open-meteo.com/v1/forecast",params={
        "latitude":52.37,"longitude":6.76,
        "hourly":"global_tilted_irradiance,cloud_cover,precipitation_probability,precipitation,temperature_2m,weather_code",
        "tilt":35,"azimuth":0,"timezone":"Europe/Amsterdam","forecast_days":4
    },timeout=25)
    r.raise_for_status()
    h=r.json()["hourly"]
    hours=[]
    for i,t in enumerate(h["time"]):
        rad=h["global_tilted_irradiance"][i]
        solar_w=round(max(0,min(7200,float(rad)*7.2*0.78))) if rad is not None else 0
        hours.append({
            "time":t,
            "solar_w":solar_w,
            "surplus_w":max(0,solar_w-base_w),
            "rain_pct":h["precipitation_probability"][i],
            "rain_mm":h["precipitation"][i],
            "temp_c":h["temperature_2m"][i],
            "weather_code":h["weather_code"][i],
            "cloud_pct":h["cloud_cover"][i]
        })
    forecast={"status":"estimated","hours":hours,"baseline_w":base_w,
        "method":"Open-Meteo, 7.2 kWp, tilt 35°, performance factor 0.78; estimated baseload from night readings"}
except (requests.RequestException,KeyError,ValueError,TypeError):
    print("Weather forecast unavailable")
Path("docs").mkdir(exist_ok=True)
Path("docs/data.json").write_text(json.dumps({"p1":p1,"solar":solar,"forecast":forecast},ensure_ascii=False),encoding="utf-8")
print(f"Exported {len(p1)} P1 and {len(solar)} solar measurements")
