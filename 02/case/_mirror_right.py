#!/usr/bin/env python
"""Right-hand parts by mirroring the proven left parts across X (split halves are
mirror images), inheriting the calibrated lip (+0.375mm) and printed case design."""
import numpy as np, trimesh
REFL=np.diag([-1.0,1,1,1])
def mirror(src,out):
    m=trimesh.load(src)
    m.apply_transform(REFL)          # trimesh auto-fixes winding on reflection
    if m.volume<0: m.invert()        # safety net only if needed
    m.export(out); bb=m.bounds
    print(f'{out:30s} watertight={m.is_watertight} vol={m.volume:.0f} (>0 good)  size {bb[1][0]-bb[0][0]:.1f}x{bb[1][1]-bb[0][1]:.1f}x{bb[1][2]-bb[0][2]:.1f}')
mirror('baseplate-left-flat.stl', 'baseplate-right-flat.stl')
mirror('baseplate-left-wedge.stl','baseplate-right-wedge.stl')
mirror('top-shell-left.stl',      'top-shell-right.stl')
