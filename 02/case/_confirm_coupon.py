#!/usr/bin/env python
"""Single confirmation strip: a short-edge slice of the final (un-wedged, 1.875mm,
+0.375 lip) plate in flat print orientation. One piece, the validated clearance."""
import numpy as np, trimesh
DEPTH=13.0
m=trimesh.load('baseplate-left-unwedged-print.stl'); bb=m.bounds
box=trimesh.creation.box([DEPTH, (bb[1][1]-bb[0][1])+4, (bb[1][2]-bb[0][2])+4])
box.apply_translation([bb[0][0]+DEPTH/2, (bb[0][1]+bb[1][1])/2, (bb[0][2]+bb[1][2])/2])
strip=trimesh.boolean.intersection([m,box],engine='manifold')
strip.apply_translation([-strip.bounds[0][0],-strip.bounds[0][1],-strip.bounds[0][2]])
strip.export('snapfit-coupon-confirm.stl'); sb=strip.bounds
print('WROTE snapfit-coupon-confirm.stl watertight=%s'%strip.is_watertight)
print('  %.0f mm long x %.0f mm deep x %.2f mm tall (+0.375 lip, 1.875mm plate)'%(
  sb[1][1]-sb[0][1], sb[1][0]-sb[0][0], sb[1][2]-sb[0][2]))
