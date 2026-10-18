"""Split disconnected blade/hub geometry from the supplied Mavic FBX inspection.

Writes centimeters, Z-up FBX assets. No synthetic replacement blades are used.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'artifacts/mavic2/geometry.json').read_text())
vertices = np.array(data['vertices'])
triangles = np.array(data['triangles']).reshape(-1, 3)
assert np.allclose(vertices.max(0), [5.85873985, -0.34573817, 5.22483015], atol=0.001), 'Expected original inspection coordinates'
_, inverse = np.unique(vertices.round(5), axis=0, return_inverse=True)
parents = list(range(inverse.max() + 1))
def find(a):
    while parents[a] != a:
        parents[a] = parents[parents[a]]
        a = parents[a]
    return a
for tri in inverse[triangles]:
    for b in tri[1:]:
        parents[find(b)] = find(tri[0])
groups = {}
for i, tri in enumerate(inverse[triangles]):
    groups.setdefault(find(tri[0]), []).append(i)
components = sorted(groups.values(), key=len, reverse=True)
assert [len(c) for c in components[:13]] == [7115,959,561,474,466,162,159,158,143,100,100,100,100]

# AirSim order: front right, rear left, front left, rear right.
# Original model X points left, Z forward, negative Y up after import correction.
rotors = [(8,12), (6,9), (7,11), (5,10)]
transformed = vertices[:, [2,0,1]] * [8,-8,-8] + [-20.89932,23.43496,-7.707744]
out = ROOT / 'fbx' / 'mavic2-separated'
out.mkdir(exist_ok=True)

def write_fbx(name, face_ids, pivot):
    faces = triangles[face_ids]
    used, indices = np.unique(faces, return_inverse=True)
    coords = (transformed[used] - pivot) * [1,-1,1]
    indices = indices.reshape(-1,3)
    indices[:,2] = -indices[:,2] - 1
    # The axis reflection needs winding reversal to preserve outward faces.
    indices = np.column_stack((indices[:,1], indices[:,0], indices[:,2]))
    vs = ','.join(format(float(v), '.9g') for v in coords.ravel())
    fs = ','.join(str(int(v)) for v in indices.ravel())
    text = '''; FBX 7.4.0 project file
FBXHeaderExtension: {
 FBXHeaderVersion: 1003
 FBXVersion: 7400
}
GlobalSettings: {
 Version: 1000
 Properties70: {
  P: "UpAxis", "int", "Integer", "",2
  P: "UpAxisSign", "int", "Integer", "",1
  P: "FrontAxis", "int", "Integer", "",1
  P: "FrontAxisSign", "int", "Integer", "",-1
  P: "CoordAxis", "int", "Integer", "",0
  P: "CoordAxisSign", "int", "Integer", "",1
  P: "UnitScaleFactor", "double", "Number", "",1
 }
}
Documents: {
 Count: 1
 Document: 999, "", "Scene" {
  RootNode: 0
 }
}
Definitions: {
 Version: 100
 Count: 2
 ObjectType: "Geometry" {
  Count: 1
 }
 ObjectType: "Model" {
  Count: 1
 }
}
Objects: {
 Geometry: 1000, "Geometry::NAME", "Mesh" {
  Vertices: *NV {
   a: VERTICES
  }
  PolygonVertexIndex: *NF {
   a: FACES
  }
  GeometryVersion: 124
 }
 Model: 1001, "Model::NAME", "Mesh" {
  Version: 232
  Properties70: {
   P: "Lcl Translation", "Lcl Translation", "", "A",0,0,0
   P: "Lcl Rotation", "Lcl Rotation", "", "A",0,0,0
   P: "Lcl Scaling", "Lcl Scaling", "", "A",1,1,1
  }
  Shading: T
  Culling: "CullingOff"
 }
}
Connections: {
 C: "OO",1000,1001
 C: "OO",1001,0
}
'''
    for a,b in [('NAME',name),('NV',str(coords.size)),('NF',str(indices.size)),('VERTICES',vs),('FACES',fs)]:
        text = text.replace(a,b)
    (out / (name + '.fbx')).write_text(text, encoding='ascii')
    return {'name':name,'triangles':len(faces),'pivot_cm':list(pivot),'min':coords.min(0).tolist(),'max':coords.max(0).tolist()}

removed = set()
report = []
for i, (blade, cap) in enumerate(rotors):
    ids = components[blade] + components[cap]
    removed.update(ids)
    hub = transformed[triangles[components[cap]]].reshape(-1,3)
    pivot = (hub.min(0) + hub.max(0)) / 2
    report.append(write_fbx('SM_Mavic2_Rotor'+str(i), ids, pivot))
body_ids = [i for i in range(len(triangles)) if i not in removed]
report.append(write_fbx('SM_Mavic2_Body', body_ids, np.zeros(3)))
assert sum(r['triangles'] for r in report) == len(triangles)
(out/'parts.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

