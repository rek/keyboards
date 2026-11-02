#!/usr/bin/env python
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
import trimesh
CASE='bottom-shell-left.stl'; OUT='baseplate-left-v3.stl'; THICK=3.0
m=trimesh.load(CASE); V=m.vertices
dn=m.face_normals[:,2]<-0.9; fz=np.array([V[f][:,2].mean() for f in m.faces[dn]])
rim=np.where(dn)[0][fz < (fz.min()+fz.max())/2]
P=V[np.unique(m.faces[rim])]; A=np.c_[P[:,0],P[:,1],np.ones(len(P))]
(a,b,c),*_=np.linalg.lstsq(A,P[:,2],rcond=None)
tris=V[m.faces][:,:,:2]
foot=unary_union([sg.Polygon(t) for t in tris]).buffer(0.0)
if foot.geom_type=='MultiPolygon': foot=max(foot.geoms,key=lambda g:g.area)
foot=sg.Polygon(foot.exterior).simplify(0.05)
w=trimesh.creation.extrude_polygon(foot, THICK)        # flat watertight plate z:0..THICK
w.vertices[:,2] += a*w.vertices[:,0] + b*w.vertices[:,1] + (c-THICK)   # shear -> follows rim plane
if w.volume<0: w.invert()
w.export(OUT); bb=w.bounds
print('WROTE %s watertight=%s vol=%.0f follows %.2fdeg uniform %.1fmm'%(OUT,w.is_watertight,w.volume,np.degrees(np.arctan(np.hypot(a,b))),THICK))
