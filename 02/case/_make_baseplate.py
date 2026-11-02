#!/usr/bin/env python
"""Thin angle-preserving baseplate for the printed top-shell.
Simple constant-thickness plate that follows the existing 4.09 deg tilt, so it
props the keyboard at that angle (does NOT flatten it like the wedge did).
Top face = the mating plane against the printed case bottom; bottom face parallel."""
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
from collections import defaultdict
import trimesh

SRC, OUT = 'bottom-shell-left.stl', 'baseplate-left.stl'
THICK = 2.0          # plate thickness (mm) -- angle is independent of this; tweak freely

m = trimesh.load(SRC); V = m.vertices
up = m.face_normals[:,2] > 0.9
# mating/top plane (tilted 4 deg)
vi=np.unique(m.faces[up].ravel()); P=V[vi]
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]; (a,b,c),*_=np.linalg.lstsq(A,P[:,2],rcond=None)
n=np.array([a,b,-1.0]); n=n/np.linalg.norm(n)*-1   # unit up-normal (a,b,1)/|.|
tilt=np.degrees(np.arctan(np.hypot(a,b)))
def topz(x,y): return a*x+b*y+c

# outer footprint loop from the top-face boundary
def loops(faces):
    ec=defaultdict(int)
    for f in faces:
        for e in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]: ec[tuple(sorted(e))]+=1
    bnd=[e for e,k in ec.items() if k==1]; adj=defaultdict(list)
    for u,v in bnd: adj[u].append(v); adj[v].append(u)
    un=set(bnd); out=[]
    while un:
        s,cu=next(iter(un)); un.discard((s,cu) if (s,cu) in un else tuple(sorted((s,cu)))); L=[s,cu]
        while True:
            nx=[w for w in adj[cu] if tuple(sorted((cu,w))) in un]
            if not nx: break
            w=nx[0]; un.discard(tuple(sorted((cu,w))))
            if w==s: break
            L.append(w); cu=w
        out.append(L)
    return out
ring=max(loops(m.faces[up]), key=lambda L: abs(0.5*np.sum(V[L][:,0]*np.roll(V[L][:,1],-1)-np.roll(V[L][:,0],-1)*V[L][:,1])))
poly=sg.Polygon([(V[i,0],V[i,1]) for i in ring]).buffer(0)

v2d,f2d=trimesh.creation.triangulate_polygon(poly)
verts=[]; faces=[]
# top cap (on tilted plane)
for x,y in v2d: verts.append([x,y,topz(x,y)])
nt=len(verts)
for t in f2d: faces.append([t[0],t[1],t[2]])             # up
# bottom cap = top shifted -THICK along normal
for x,y in v2d:
    p=np.array([x,y,topz(x,y)])-THICK*n; verts.append(p.tolist())
for t in f2d: faces.append([nt+t[0],nt+t[2],nt+t[1]])     # down
# skirt: walk outer ring of the triangulation boundary
ec=defaultdict(int)
for t in f2d:
    for e in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]: ec[tuple(sorted(e))]+=1
bedges=[e for e,k in ec.items() if k==1]
for i,j in bedges:
    faces.append([i,j,nt+j]); faces.append([i,nt+j,nt+i])

w=trimesh.Trimesh(np.array(verts),np.array(faces),process=True); w.merge_vertices()
if w.volume<0: w.invert()
w.export(OUT)
bb=w.bounds
print(f'top plane tilt {tilt:.2f} deg  | THICK={THICK} mm')
print(f'WROTE {OUT}  watertight={w.is_watertight}  vol={w.volume:.0f} mm^3')
print(f'  footprint {bb[1][0]-bb[0][0]:.1f} x {bb[1][1]-bb[0][1]:.1f} mm  Zrange {bb[0][2]:.2f}..{bb[1][2]:.2f}')
# confirm bottom is tilted (not flat), parallel to top
dn=w.face_normals[:,2]<-0.5; nb=(w.face_normals[dn]*w.area_faces[dn][:,None]).sum(0); nb/=np.linalg.norm(nb)
print('  bottom normal',np.round(nb,3),'-> tilt %.2f deg (must stay ~4, NOT 0)'%np.degrees(np.arccos(min(1,abs(nb[2])))))
