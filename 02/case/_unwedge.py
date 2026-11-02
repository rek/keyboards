#!/usr/bin/env python
"""Un-wedge: uniform-thickness plate following baseplate-left-wedge's 4.1deg top,
with that wedge's EXACT validated +0.375 lip grafted on top. No re-derivation."""
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
import trimesh
T=1.875
m=trimesh.load('baseplate-left-wedge.stl'); V=m.vertices
up=m.face_normals[:,2]>0.9; P=V[np.unique(m.faces[up])]
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]; sol=np.linalg.lstsq(A,P[:,2],rcond=None)[0]
for _ in range(3):
    res=P[:,2]-A@sol; keep=np.abs(res-np.median(res))<0.4
    sol=np.linalg.lstsq(A[keep],P[keep,2],rcond=None)[0]
a,b,c=sol
def big(p): return max(p.geoms,key=lambda g:g.area) if p.geom_type=='MultiPolygon' else p
foot=sg.Polygon(big(unary_union([sg.Polygon(t) for t in V[m.faces][:,:,:2]]).buffer(0)).exterior).simplify(0.05)
# uniform plate: top on plane z=ax+by+c, bottom T below (parallel)
plate=trimesh.creation.extrude_polygon(foot, T); plate.vertices[:,2]+=a*plate.vertices[:,0]+b*plate.vertices[:,1]+(c-T)
# lip = the wedge above its plate-top plane (boolean), grafted on
n=np.array([-a,-b,1.0]); n/=np.linalg.norm(n)
Tb=trimesh.geometry.align_vectors([0,0,1.0],n); Tb[:3,3]=np.array([0,0,c-0.6])+n*200.0
box=trimesh.creation.box([500,500,400]); box.apply_transform(Tb)
lip=trimesh.boolean.intersection([m,box],engine='manifold')
out=trimesh.boolean.union([plate,lip],engine='manifold')
out.export('baseplate-left-unwedged.stl'); bb=out.bounds
print('plate-top tilt %.2fdeg, lip vol %.0f'%(np.degrees(np.arctan(np.hypot(a,b))),lip.volume))
print('WROTE baseplate-left-unwedged.stl watertight=%s  size %.1f x %.1f x %.1f (uniform %.1fmm + lip)'%(
  out.is_watertight,bb[1][0]-bb[0][0],bb[1][1]-bb[0][1],bb[1][2]-bb[0][2],T))
