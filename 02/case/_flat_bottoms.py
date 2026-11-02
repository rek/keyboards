#!/usr/bin/env python
"""Two print-friendly baseplates, BOTH dead-flat bottom on Z=0, single watertight
solids (manifold boolean union -> clean normals):
  A) baseplate-left-flat.stl   - flat plate, no angle (keyboard sits flat).
  B) baseplate-left-wedge.stl  - flat bottom + 4 deg tilted top (keeps typing angle).
Both carry the friction-fit lip rib on top."""
import numpy as np, shapely.geometry as sg
from collections import defaultdict
import trimesh

SRC='baseplate-left.stl'
PLATE_T=1.5; LIP_H=3.0; WALL=1.6; GROW=-0.025; INSET=3.6-GROW   # lip grown +0.375mm/side (coupon-calibrated)
SLOPE=0.07140; MIN_T=1.5

m=trimesh.load(SRC); V=m.vertices; up=m.face_normals[:,2]>0.9
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
x0=np.array(Pout.exterior.coords)[:,0].min()
def big(p): return max(p.geoms,key=lambda g:g.area) if p.geom_type=='MultiPolygon' else p
lip2d=big(Pout.buffer(-INSET)).difference(big(Pout.buffer(-(INSET+WALL))))

def shear_top(mesh, topfn):
    z=mesh.vertices[:,2]; hi=z>z.max()-1e-6
    mesh.vertices[hi,2]=np.array([topfn(x,y) for x,y in mesh.vertices[hi,:2]])
    return mesh

def build(name, topfn, base_h):
    base=trimesh.creation.extrude_polygon(Pout, base_h)        # bottom z=0, flat
    if abs(base_h-PLATE_T)>1e-9 or True: base=shear_top(base, topfn)
    lip=trimesh.creation.extrude_polygon(lip2d, LIP_H+0.6)
    lip=shear_top(lip, lambda x,y: topfn(x,y)+LIP_H)           # lip top
    lv=lip.vertices; lo=lv[:,2]<lv[:,2].min()+ (LIP_H)         # lip bottom band -> embed onto top
    lip.vertices[:, :]=lip.vertices                            # noop keep
    # set lip bottom onto top surface minus 0.6 embed
    zb=lip.vertices[:,2]; isbot=zb<(np.array([topfn(x,y) for x,y in lip.vertices[:,:2]])+0.05)
    lip.vertices[isbot,2]=np.array([topfn(x,y) for x,y in lip.vertices[isbot,:2]])-0.6
    out=trimesh.boolean.union([base,lip],engine='manifold')
    out.export(name); bb=out.bounds; dn=out.face_normals[:,2]<-0.9
    z=out.vertices[np.unique(out.faces[dn])][:,2]
    print(f'{name}: watertight={out.is_watertight}  bottomZ {z.min():.3f}..{z.max():.3f} ({"FLAT" if z.max()-z.min()<1e-3 else "CHECK"})  Zmax {bb[1][2]:.2f}  vol {out.volume:.0f}')

build('baseplate-left-flat.stl',  lambda x,y: PLATE_T, PLATE_T+2)
build('baseplate-left-wedge.stl', lambda x,y: MIN_T+SLOPE*(x-x0), 30.0)
