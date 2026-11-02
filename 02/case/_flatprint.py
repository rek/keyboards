#!/usr/bin/env python
"""Lay baseplate-left-unwedged flat for printing: rotate so the bottom face is
horizontal on the bed (Z=0), lip pointing up. Same part, print-friendly orientation."""
import numpy as np, trimesh
m=trimesh.load('baseplate-left-unwedged.stl'); V=m.vertices
up=m.face_normals[:,2]>0.9; P=V[np.unique(m.faces[up])]
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]; sol=np.linalg.lstsq(A,P[:,2],rcond=None)[0]
for _ in range(3):
    r=P[:,2]-A@sol; k=np.abs(r-np.median(r))<0.4; sol=np.linalg.lstsq(A[k],P[k,2],rcond=None)[0]
a,b,c=sol; n=np.array([-a,-b,1.0]); n/=np.linalg.norm(n)
Tr=trimesh.geometry.align_vectors(n,[0,0,1.0])      # rotate plate normal -> straight up
m.apply_transform(Tr)
m.apply_translation([-m.bounds[0][0],-m.bounds[0][1],-m.bounds[0][2]])  # seat at origin, Z=0
m.export('baseplate-left-unwedged-print.stl'); bb=m.bounds
dn=m.face_normals[:,2]<-0.9; bz=m.vertices[np.unique(m.faces[dn])][:,2]
print('WROTE baseplate-left-unwedged-print.stl watertight=%s'%m.is_watertight)
print('  footprint %.1f x %.1f mm, height %.2f mm'%(bb[1][0]-bb[0][0],bb[1][1]-bb[0][1],bb[1][2]-bb[0][2]))
print('  bottom face Z %.3f..%.3f (flat on bed if ~0)'%(bz.min(),bz.max()))
