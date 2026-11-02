#!/usr/bin/env python
"""Add a perimeter friction-fit lip to baseplate-left so it press-fits into the
top-shell's inner skirt cavity. No hardware, no changes to the printed top-shell.

Calibrated for 0.4mm-nozzle FDM:
  CLEAR  0.15 mm/side  -> snug press fit (tune up if too tight, down if too loose)
  LIP_H  3.0  mm tall  (cavity is ~4.8 deep; leaves clearance so it grips, not bottoms)
  WALL   1.6  mm thick rib
The lip outer wall is inset from the baseplate edge to meet the ~2.0mm skirt's
inner face; INSET below = (baseplate-edge -> cavity wall) + CLEAR.
"""
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
from collections import defaultdict
import trimesh

SRC, OUT = 'baseplate-left.stl', 'baseplate-left-snapfit.stl'
CLEAR=0.15; LIP_H=3.0; WALL=1.6; EMBED=0.6
INSET = 3.6 + CLEAR          # baseplate edge -> cavity inner wall (~3.6) + clearance

m=trimesh.load(SRC); V=m.vertices
up=m.face_normals[:,2]>0.9
vi=np.unique(m.faces[up].ravel()); P=V[vi]
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]; (a,b,c),*_=np.linalg.lstsq(A,P[:,2],rcond=None)
def topz(x,y): return a*x+b*y+c

def loops(faces):
    ec=defaultdict(int)
    for f in faces:
        for e in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]: ec[tuple(sorted(e))]+=1
    bnd=[e for e,k in ec.items() if k==1]; adj=defaultdict(list)
    for u,v in bnd: adj[u].append(v); adj[v].append(u)
    un=set(bnd); out=[]
    while un:
        s,cu=next(iter(un)); un.discard(tuple(sorted((s,cu)))); L=[s,cu]
        while True:
            nx=[w for w in adj[cu] if tuple(sorted((cu,w))) in un]
            if not nx: break
            w=nx[0]; un.discard(tuple(sorted((cu,w))))
            if w==s: break
            L.append(w); cu=w
        out.append(L)
    return out
ring=max(loops(m.faces[up]), key=lambda L: abs(0.5*np.sum(V[L][:,0]*np.roll(V[L][:,1],-1)-np.roll(V[L][:,0],-1)*V[L][:,1])))
Pout=sg.Polygon([(V[i,0],V[i,1]) for i in ring]).buffer(0)

Plo=Pout.buffer(-INSET)
Pli=Plo.buffer(-WALL)
def big(p): return max(p.geoms,key=lambda g:g.area) if p.geom_type=='MultiPolygon' else p
Plo=big(Plo); Pli=big(Pli)
lip2d=Plo.difference(Pli)
print(f'lip outer bbox {Plo.bounds[2]-Plo.bounds[0]:.1f} x {Plo.bounds[3]-Plo.bounds[1]:.1f} mm  (target cavity ~147.6 x 86.6)')
if lip2d.geom_type=='MultiPolygon':
    print('  note: lip ring split into', len(lip2d.geoms),'pieces (thin areas pinched) -> partial lip')

# build lip solid: extrude flat then shear onto the tilted plate top
H=LIP_H+EMBED
lip=trimesh.creation.extrude_polygon(lip2d, H)
LV=lip.vertices.copy()
LV[:,2]=LV[:,2]+ (a*LV[:,0]+b*LV[:,1]+c) - EMBED   # z + topz(x,y) - EMBED
lip.vertices=LV
print('lip body watertight:', lip.is_watertight, ' vol %.0f mm^3'%lip.volume)

comb=trimesh.util.concatenate([m, lip]); comb.merge_vertices()
comb.export(OUT)
bb=comb.bounds
print(f'WROTE {OUT}  bodies=2 (plate+lip, weld at slice)  Zrange {bb[0][2]:.2f}..{bb[1][2]:.2f}')
print(f'  lip rises {LIP_H} mm above plate, {WALL} mm thick, {CLEAR} mm/side clearance')
