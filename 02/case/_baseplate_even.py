#!/usr/bin/env python
"""TRUE-EVEN baseplate. Lip = constant 0.30mm offset from the case's inner cavity
wall AND notched to keep 0.30mm from any INTERIOR walls/posts (e.g. the inner wall
running along the left/bottom that forms a ~2mm channel). Uniform 1.875mm plate
following the angle, output FLAT for printing."""
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
import trimesh
CASE='bottom-shell-left.stl'
THICK=1.875; LIP_H=2.0; WALL=1.6; EMBED=0.6; CLEAR_FULL=0.30
m=trimesh.load(CASE); V=m.vertices
dn=m.face_normals[:,2]<-0.9; fz=np.array([V[f][:,2].mean() for f in m.faces[dn]])
mid=(fz.min()+fz.max())/2; rim=np.where(dn)[0][fz<mid]; ceil=np.where(dn)[0][fz>=mid]
P=V[np.unique(m.faces[rim])];A=np.c_[P[:,0],P[:,1],np.ones(len(P))];(a,b,c),*_=np.linalg.lstsq(A,P[:,2],rcond=None)
def big(p): return max(p.geoms,key=lambda g:g.area) if p.geom_type=='MultiPolygon' else p
def outline(fidx): return sg.Polygon(big(unary_union([sg.Polygon(t) for t in V[fidx][:,:,:2]]).buffer(0)).exterior).simplify(0.05)
USB=sg.box(67,36.8,82,44)
foot=big(outline(m.faces).difference(USB))
cav =big(outline(m.faces[ceil]).difference(USB))
# INTERIOR obstacles = vertical faces at cavity height sitting >0.6mm inside the wall
side=np.abs(m.face_normals[:,2])<0.3; fcz=V[m.faces[side]].mean(axis=1)[:,2]
inb=(fcz>16)&(fcz<24.5); innerzone=cav.buffer(-0.6)
obs=[sg.Polygon(t) for t in V[m.faces[side][inb]][:,:,:2] if sg.Polygon(t).is_valid and innerzone.contains(sg.Polygon(t).centroid)]
OBST=unary_union(obs).buffer(0) if obs else sg.Polygon()
print('interior obstacle area %.0f mm^2 -> lip will be notched to clear it'%OBST.area)
def shear(me): me.vertices[:,2]+=a*me.vertices[:,0]+b*me.vertices[:,1]; return me
n=np.array([-a,-b,1.0]); n/=np.linalg.norm(n)
def flatten(me):
    me.apply_transform(trimesh.geometry.align_vectors(n,[0,0,1.0]))
    me.apply_translation([-me.bounds[0][0],-me.bounds[0][1],-me.bounds[0][2]]); return me
def plate(f2d): w=trimesh.creation.extrude_polygon(f2d,THICK); w.vertices[:,2]+=(c-THICK); return shear(w)
def lip_pieces(r2d):
    out=[]
    for g in (r2d.geoms if r2d.geom_type=='MultiPolygon' else [r2d]):
        if g.area<0.4: continue
        L=trimesh.creation.extrude_polygon(g,LIP_H+EMBED); L.vertices[:,2]+=(c-EMBED); out.append(shear(L))
    return out
def make(f2d,cav2d,CLEAR,clip=None):
    ring=big(cav2d.buffer(-CLEAR)).difference(big(cav2d.buffer(-(CLEAR+WALL))))
    ring=ring.difference(OBST.buffer(CLEAR))          # notch lip to clear interior walls/posts
    if clip is not None: ring=ring.intersection(clip)
    return trimesh.boolean.union([plate(f2d), *lip_pieces(ring)],engine='manifold')

full=flatten(make(foot,cav,CLEAR_FULL)); full.export('baseplate-left-even-print.stl'); bb=full.bounds
print('baseplate-left-even-print.stl watertight=%s %.0fx%.0f x%.2fmm'%(full.is_watertight,bb[1][0]-bb[0][0],bb[1][1]-bb[0][1],bb[1][2]-bb[0][2]))
minx,miny,maxx,maxy=foot.bounds; strip=sg.box(minx-1,miny-1,minx+13,maxy+1); fstrip=big(foot.intersection(strip)); parts=[]
for k,CLEAR in enumerate([0.20,0.30,0.40]):
    cp=flatten(make(fstrip,cav,CLEAR,clip=strip)); cp.apply_translation([k*22,0,0]); parts.append(cp)
trimesh.util.concatenate(parts).export('snapfit-coupons-even.stl')
print('WROTE snapfit-coupons-even.stl (0.20/0.30/0.40 even)')
