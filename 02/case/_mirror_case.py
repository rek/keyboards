#!/usr/bin/env python
"""Mirror the current case bottom-shell-left.stl across X -> bottom-shell-right.stl.
Split halves are mirror images. (trimesh auto-flips winding on a reflection; only
invert if volume came out negative.)"""
import numpy as np, trimesh
m=trimesh.load('bottom-shell-left.stl')
m.apply_transform(np.diag([-1.0,1,1,1]))
if m.volume<0: m.invert()
m.export('bottom-shell-right.stl'); bb=m.bounds
print('bottom-shell-right.stl watertight=%s vol=%.0f (>0 good)  size %.1f x %.1f x %.1f'%(
  m.is_watertight,m.volume,bb[1][0]-bb[0][0],bb[1][1]-bb[0][1],bb[1][2]-bb[0][2]))
