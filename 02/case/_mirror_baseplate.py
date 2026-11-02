#!/usr/bin/env python
"""Mirror the finished left even-baseplate (flat print orientation) -> right."""
import numpy as np, trimesh
for src,out in [('baseplate-left-even-print.stl','baseplate-right-even-print.stl'),
                ('snapfit-coupons-even.stl','snapfit-coupons-even-right.stl')]:
    m=trimesh.load(src)
    m.apply_transform(np.diag([-1.0,1,1,1]))
    if m.volume<0: m.invert()
    m.apply_translation([-m.bounds[0][0],-m.bounds[0][1],-m.bounds[0][2]])  # reseat flat at origin
    m.export(out); bb=m.bounds
    dn=m.face_normals[:,2]<-0.9; bz=m.vertices[np.unique(m.faces[dn])][:,2]
    print('%s watertight=%s  %.0fx%.0f x%.2f  bottomZ %.3f (flat if ~0)'%(out,m.is_watertight,bb[1][0]-bb[0][0],bb[1][1]-bb[0][1],bb[1][2]-bb[0][2],bz.min()))
