#!/usr/bin/env python
"""Full baseplate (angle-following plate + cavity friction lip) and fresh coupons,
both derived from the UPDATED bottom-shell-left case."""
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
import trimesh
CASE='bottom-shell-left.stl'
THICK=3.0; LIP_H=2.0; WALL=1.6; EMBED=0.6
m=trimesh.load(CASE); V=m.vertices
dn=m.face_normals[:,2]<-0.9; fz=np.array([V[f][:,2].mean() for f in m.faces[dn]])
mid=(fz.min()+fz.max())/2; rim=np.where(dn)[0][fz<mid]; ceil=np.where(dn)[0][fz>=mid]
P=V[np.unique(m.faces[rim])];A=np.c_[P[:,0],P[:,1],np.ones(len(P))];(a,b,c),*_=np.linalg.lstsq(A,P[:,2],rcond=None)
def big(p): return max(p.geoms,key=lambda g:g.area) if p.geom_type=='MultiPolygon' else p
def outline(fidx): return sg.Polygon(big(unary_union([sg.Polygon(t) for t in V[fidx][:,:,:2]]).buffer(0)).exterior).simplify(0.05)
USB=sg.box(67,36.8,82,44)   # USB-C bump region -> surgically removed (NO global open, so step corners stay tight)
foot=big(outline(m.faces).difference(USB))
cav =big(outline(m.faces[ceil]).difference(USB))   # exterior only -> no switch-hole rings
def shear(mesh): mesh.vertices[:,2]+=a*mesh.vertices[:,0]+b*mesh.vertices[:,1]; return mesh

def plate(foot2d, base_h=THICK):
    w=trimesh.creation.extrude_polygon(foot2d, base_h); w.vertices[:,2]+=(c-base_h); return shear(w)
def lip(ring2d):
    L=trimesh.creation.extrude_polygon(ring2d, LIP_H+EMBED); L.vertices[:,2]+=(c-EMBED); return shear(L)

def make(foot2d, cav2d, CLEAR, out):
    pl=plate(foot2d)
    ring=big(cav2d.buffer(-CLEAR)).difference(big(cav2d.buffer(-(CLEAR+WALL))))
    if not ring.is_empty:
        comb=trimesh.boolean.union([pl, lip(big(ring) if ring.geom_type=='MultiPolygon' else ring)],engine='manifold')
    else: comb=pl
    comb.export(out); bb=comb.bounds
    print('%s: watertight=%s vol=%.0f  Zspan %.1f..%.1f'%(out,comb.is_watertight,comb.volume,bb[0][2],bb[1][2]))

# full part at provisional clearance
make(foot, cav, 0.25, 'baseplate-left-v3.stl')

# coupons: short-edge strips at 3 clearances
minx,miny,maxx,maxy=foot.bounds
strip=sg.box(minx-1,miny-1,minx+13,maxy+1)
fstrip=big(foot.intersection(strip))
parts=[]
for k,CLEAR in enumerate([0.10,0.25,0.40]):
    pl=plate(fstrip)
    ring=big(cav.buffer(-CLEAR)).difference(big(cav.buffer(-(CLEAR+WALL)))).intersection(strip)
    cp=trimesh.boolean.union([pl, lip(big(ring))],engine='manifold')
    cp.apply_translation([k*25,0,0]); parts.append(cp)
    print('coupon %d (L->R): CLEAR=%.2f mm/side'%(k+1,CLEAR))
trimesh.util.concatenate(parts).export('snapfit-coupons-v3.stl')
print('WROTE snapfit-coupons-v3.stl (L->R 0.10/0.25/0.40), baseplate-left-v3.stl (lip @0.25 provisional)')
