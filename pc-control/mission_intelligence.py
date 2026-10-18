"""PC-side mission intelligence. Outputs advisory routes; Android remains the flight safety gate."""
from __future__ import annotations
import csv, hashlib, json, math, os, sqlite3, tempfile, urllib.request, webbrowser
from dataclasses import dataclass
from pathlib import Path

EARTH_M = 6_371_000.0

def distance(a, b, c, d):
    x, y = math.radians(c-a), math.radians(d-b)
    h = math.sin(x/2)**2 + math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(y/2)**2
    return EARTH_M*2*math.asin(math.sqrt(max(0, min(1, h))))

@dataclass(frozen=True)
class Point:
    lat: float; lon: float; alt: float

@dataclass(frozen=True)
class Zone:
    name: str; lat: float; lon: float; radius_m: float

class MissionDatabase:
    """SQLite store for versioned geofences and terrain samples."""
    def __init__(self, path):
        self.path = Path(path); self.db = sqlite3.connect(self.path)
        self.db.executescript("""
          create table if not exists meta(key text primary key,value text not null);
          create table if not exists zones(name text,lat real,lon real,radius_m real,source text,updated_at text);
          create table if not exists terrain(lat real,lon real,elevation_m real,source text,updated_at text);
        """)
    def import_json(self, path):
        data=json.loads(Path(path).read_text(encoding="utf-8")); source=data.get("source",Path(path).name); updated=data.get("updatedAt","")
        zones=[Zone(str(z["name"]),float(z["lat"]),float(z["lon"]),float(z["radiusM"])) for z in data.get("zones",[])]
        if any(not (-90<=z.lat<=90 and -180<=z.lon<=180 and z.radius_m>0) for z in zones): raise ValueError("圍欄資料無效")
        with self.db:
            self.db.execute("delete from zones")
            self.db.executemany("insert into zones values(?,?,?,?,?,?)",[(z.name,z.lat,z.lon,z.radius_m,source,updated) for z in zones])
            self.db.execute("insert or replace into meta values('geofence_updated',?)",(updated,))
        return len(zones)
    def import_terrain_csv(self,path,source="DEM CSV"):
        rows=[]
        with Path(path).open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f): rows.append((float(r["lat"]),float(r["lon"]),float(r["elevation_m"]),source,""))
        if not rows: raise ValueError("地形 CSV 沒有資料")
        with self.db:
            self.db.execute("delete from terrain"); self.db.executemany("insert into terrain values(?,?,?,?,?)",rows)
        return len(rows)
    def zones(self): return [Zone(*r) for r in self.db.execute("select name,lat,lon,radius_m from zones")]
    def close(self): self.db.close()
    def nearest_elevation(self,lat,lon,max_m=100):
        best=None
        for a,b,e in self.db.execute("select lat,lon,elevation_m from terrain"):
            d=distance(lat,lon,a,b)
            if d<=max_m and (best is None or d<best[0]): best=(d,e)
        return None if best is None else best[1]

def parse_route(text):
    out=[]
    for n,line in enumerate(text.splitlines(),1):
        if not line.strip() or line.lstrip().startswith("#"): continue
        try: a,b,c=map(float,line.split(",")); out.append(Point(a,b,c))
        except Exception as exc: raise ValueError(f"航線第 {n} 行格式錯誤") from exc
    if len(out)<2: raise ValueError("至少需要兩個航點")
    return out

def route_report(points,db,home_elevation_m=None,clearance_m=10):
    errors=[]
    for i,(a,b) in enumerate(zip(points,points[1:]),1):
        steps=max(1,math.ceil(distance(a.lat,a.lon,b.lat,b.lon)/5))
        for j in range(steps+1):
            t=j/steps; lat=a.lat+(b.lat-a.lat)*t; lon=a.lon+(b.lon-a.lon)*t; alt=a.alt+(b.alt-a.alt)*t
            for z in db.zones():
                if distance(lat,lon,z.lat,z.lon)<=z.radius_m: errors.append(f"第 {i} 段進入圍欄：{z.name}"); break
            elev=db.nearest_elevation(lat,lon)
            if home_elevation_m is not None and elev is None: errors.append(f"第 {i} 段缺少鄰近地形資料")
            elif elev is not None and home_elevation_m+alt-elev<clearance_m: errors.append(f"第 {i} 段地形淨空不足 {clearance_m} m")
    return list(dict.fromkeys(errors))

def detour_route(points,db,margin_m=15):
    """Conservative circle detour; refuses overlapping/ambiguous cases."""
    zones=db.zones(); out=[points[0]]
    for target in points[1:]:
        start=out[-1]; hit=[z for z in zones if _segment_near(start,target,z)<z.radius_m+margin_m]
        if len(hit)>1: raise ValueError("同一路段碰到多個圍欄，簡易規劃器拒絕規劃")
        if hit:
            z=hit[0]; lat_scale=111_320; lon_scale=lat_scale*math.cos(math.radians(z.lat))
            sx=(start.lon-z.lon)*lon_scale; sy=(start.lat-z.lat)*lat_scale
            tx=(target.lon-z.lon)*lon_scale; ty=(target.lat-z.lat)*lat_scale
            vx,vy=tx-sx,ty-sy; length=math.hypot(vx,vy)
            if length<1: raise ValueError("路段過短")
            nx,ny=-vy/length,vx/length; radius=z.radius_m+margin_m
            candidates=[]
            for sign in (-1,1):
                x,y=nx*radius*sign,ny*radius*sign
                candidates.append(Point(z.lat+y/lat_scale,z.lon+x/lon_scale,max(start.alt,target.alt)))
            via=min(candidates,key=lambda p:distance(start.lat,start.lon,p.lat,p.lon)+distance(p.lat,p.lon,target.lat,target.lon))
            out.append(via)
        out.append(target)
    errors=route_report(out,db)
    if any("圍欄" in e for e in errors): raise ValueError("無法產生通過圍欄驗證的航線")
    return out

def _segment_near(a,b,z):
    lat_scale=111_320; lon_scale=lat_scale*math.cos(math.radians(z.lat))
    ax=(a.lon-z.lon)*lon_scale; ay=(a.lat-z.lat)*lat_scale; bx=(b.lon-z.lon)*lon_scale; by=(b.lat-z.lat)*lat_scale
    vx,vy=bx-ax,by-ay; q=0 if vx*vx+vy*vy==0 else max(0,min(1,-(ax*vx+ay*vy)/(vx*vx+vy*vy)))
    return math.hypot(ax+q*vx,ay+q*vy)

def thermal_report(path,threshold_c=80):
    rows=[]
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        for row in csv.reader(f): rows.append([float(x) for x in row])
    flat=[x for r in rows for x in r]
    if not flat or any(len(r)!=len(rows[0]) for r in rows): raise ValueError("熱像矩陣必須是完整矩形 CSV")
    return {"rows":len(rows),"columns":len(rows[0]),"minC":min(flat),"maxC":max(flat),"meanC":sum(flat)/len(flat),"hotPixels":sum(x>=threshold_c for x in flat)}

def inspect_ai_model(path):
    p=Path(path)
    if p.suffix.lower()!='.onnx' or not p.is_file(): raise ValueError("請提供 ONNX 模型")
    return {"path":str(p.resolve()),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"ready":True,
            "note":"模型已登錄；必須另以標註驗證集確認類別、輸入尺寸與準確率後才可用於告警。"}

def upload_file(endpoint,token,path):
    if not endpoint.lower().startswith("https://"): raise ValueError("雲端端點必須使用 HTTPS")
    data=Path(path).read_bytes(); req=urllib.request.Request(endpoint,data=data,method="POST",headers={"Content-Type":"application/octet-stream","Authorization":"Bearer "+token,"X-File-Name":Path(path).name})
    with urllib.request.urlopen(req,timeout=20) as response: return response.status

def create_map(points,db):
    payload=json.dumps({"route":[p.__dict__ for p in points],"zones":[z.__dict__ for z in db.zones()]},ensure_ascii=False)
    html=f'''<!doctype html><meta charset="utf-8"><title>Mavic 任務地圖</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><div id="m" style="height:100vh"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>const d={payload};const m=L.map('m').setView([d.route[0].lat,d.route[0].lon],17);L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'© OpenStreetMap contributors'}}).addTo(m);L.polyline(d.route.map(p=>[p.lat,p.lon]),{{color:'blue'}}).addTo(m);d.zones.forEach(z=>L.circle([z.lat,z.lon],{{radius:z.radius_m,color:'red'}}).bindTooltip(z.name).addTo(m));</script>'''
    path=Path(tempfile.gettempdir())/"mavic_mission_map.html"; path.write_text(html,encoding="utf-8"); webbrowser.open(path.as_uri()); return path
