#!/usr/bin/env python
"""Short-edge test coupons: a full ~94mm short-edge strip of the flat baseplate + lip
at 3 clearances. Press each strip into the matching short edge of the printed top-shell
to judge the fit along the whole length, then rebuild the full plate at the winner."""
import numpy as np, shapely.geometry as sg
from collections import defaultdict
import trimesh

DEPTH=12.0          # how far in from the edge the strip reaches (X) - thin enough to test the lip, no excess plate
PLATE_T=1.5; LIP_H=3.0; WALL=1.6; base=3.6
EDGE='min'          # 'min' = left short edge, 'max' = right short edge

m=trimesh.load('baseplate-left.stl'); V=m.vertices; up=m.face_normals[:,2]>0.9
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
ring=max(loops(m.faces[up]),key=lambda L:abs(0.5*np.sum(V[L][:,0]*np.roll(V[L][:,1],-1)-np.roll(V[L][:,0],-1)*V[L][:,1])))
Pout=sg.Polygon([(V[i,0],V[i,1]) for i in ring]).buffer(0)
minx,miny,maxx,maxy=Pout.bounds
# full-length strip along one short edge (full Y extent, DEPTH into X)
if EDGE=='min': strip=sg.box(minx-1, miny-1, minx+DEPTH, maxy+1)
else:           strip=sg.box(maxx-DEPTH, miny-1, maxx+1, maxy+1)
def big(p): return max(p.geoms,key=lambda g:g.area) if p.geom_type=='MultiPolygon' else p
Pc=big(Pout.intersection(strip))
print(f'strip ({EDGE}-X short edge): {Pc.bounds[3]-Pc.bounds[1]:.0f} mm long x {Pc.bounds[2]-Pc.bounds[0]:.0f} mm deep')

parts=[]
# previous coupons were all too LOOSE -> grow the lip outward (real printed cavity is
# bigger than the model). GROW = mm the lip outer face moves OUT per side vs model-cavity fit.
for k,GROW in enumerate([0.4,0.8,1.2,1.5]):
    INSET=base-GROW
    lipout=big(Pout.buffer(-INSET))
    lip2d=lipout.difference(big(Pout.buffer(-(INSET+WALL)))).intersection(strip)
    lb=lipout.bounds
    plate=trimesh.creation.extrude_polygon(Pc, PLATE_T)
    lip=trimesh.creation.extrude_polygon(big(lip2d), LIP_H)
    lip.apply_translation([0,0,PLATE_T-0.6])
    cp=trimesh.boolean.union([plate,lip],engine='manifold')
    cp.apply_translation([k*(DEPTH+12),0,0])    # lay the 3 strips side by side, small->big lip
    parts.append(cp)
    print(f'coupon {k+1} (pos {k+1}/4 left->right): lip GROW +{GROW} mm/side  full lip outer {lb[2]-lb[0]:.1f} x {lb[3]-lb[1]:.1f} mm')
allc=trimesh.util.concatenate(parts); allc.export('snapfit-coupons.stl')
print('WROTE snapfit-coupons.stl  (4 short-edge strips, left->right = bigger lip; +0.4/+0.8/+1.2/+1.5 mm per side)')
