"""Tessellate the supplied STEP, orient Y-up to Z-up, export UE centimetres."""
import json
import math
from pathlib import Path
import gmsh

out = Path('/home/wuta/carla/Build/cone-assets')
out.mkdir(exist_ok=True)
gmsh.initialize()
gmsh.option.setString('Geometry.OCCTargetUnit', 'M')
gmsh.model.occ.importShapes('/home/wuta/下载/黄色小锥桶.STEP')
gmsh.model.occ.synchronize()
gmsh.option.setNumber('Mesh.MeshSizeMin', 0.004)
gmsh.option.setNumber('Mesh.MeshSizeMax', 0.012)
gmsh.model.mesh.generate(2)
tags, coords, _ = gmsh.model.mesh.getNodes()
index = {int(t): i + 1 for i, t in enumerate(tags)}
vertices = [(coords[i]*100, -coords[i+2]*100, coords[i+1]*100)
            for i in range(0, len(coords), 3)]
triangles = []
types, _, nodes = gmsh.model.mesh.getElements(2)
for kind, ids in zip(types, nodes):
    if kind != 2:
        raise RuntimeError('Expected triangular mesh, got ' + str(kind))
    triangles.extend(tuple(index[int(t)] for t in ids[i:i+3]) for i in range(0, len(ids), 3))
with (out/'SM_TrackCone.obj').open('w') as f:
    f.write('# STEP millimetres converted to Unreal centimetres; Z up; base pivot\no TrackCone\n')
    for v in vertices: f.write('v %.9f %.9f %.9f\n' % v)
    for x,y,z in vertices:
        f.write('vt %.9f %.9f\n' % (math.atan2(y,x)/(2*math.pi)+0.5, z/28.0))
    for tri in triangles: f.write('f %d/%d %d/%d %d/%d\n' % tuple(n for i in tri for n in (i,i)))
info = {'source': '/home/wuta/下载/黄色小锥桶.STEP', 'dimensions_cm': [20,20,28],
        'vertices': len(vertices), 'triangles': len(triangles),
        'colours': ['red','blue','yellow'], 'pivot': 'base centre',
        'geometry': 'one shared mesh; three material variants'}
(out/'conversion.json').write_text(json.dumps(info,indent=2)+'\n')
gmsh.finalize()
print(json.dumps(info,indent=2))
