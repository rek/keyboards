#!/usr/bin/env python
"""bottom-shell-left -> flat-bottomed WEDGE.
Keep the EXACT existing tilted, two-level top surface (rim + recessed pocket that
the keyboard half nests into). Replace the tilted underside with a vertical skirt
down to one flat horizontal plane + a flat bottom cap. Writes a NEW file."""
import numpy as np, shapely.geometry as sg
from shapely.ops import unary_union
from collections import defaultdict
import trimesh

SRC, OUT = 'bottom-shell-left.stl', 'bottom-shell-left-wedge.stl'
m = trimesh.load(SRC)
V = m.vertices

up   = m.face_normals[:,2] >  0.9     # rim + recessed floor (the mating top)
side = np.abs(m.face_normals[:,2]) < 0.3

def boundary_loops(faces):
    ec = defaultdict(int)
    for f in faces:
        for e in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]: ec[tuple(sorted(e))]+=1
    bnd=[e for e,c in ec.items() if c==1]
    adj=defaultdict(list)
    for u,v in bnd: adj[u].append(v); adj[v].append(u)
    unused=set(bnd); loops=[]
    while unused:
        s,c=next(iter(unused)); unused.discard((s,c) if (s,c) in unused else tuple(sorted((s,c))))
        loop=[s,c]
        while True:
            nxt=[w for w in adj[c] if tuple(sorted((c,w))) in unused]
            if not nxt: break
            w=nxt[0]; unused.discard(tuple(sorted((c,w)))); 
            if w==s: break
            loop.append(w); c=w
        loops.append(loop)
    return loops

# step-wall vertices = the two ~10944 loops bounding the up-faces
uploops = sorted(boundary_loops(m.faces[up]), key=lambda L: len(L), reverse=True)
outer_loop = max(uploops, key=lambda L: abs(0.5*np.sum(V[L][:,0]*np.roll(V[L][:,1],-1)-np.roll(V[L][:,0],-1)*V[L][:,1])))
step_verts = set(v for L in uploops if L is not outer_loop for v in L)

# step-wall faces: side faces fully inside the step loops
step_faces = m.faces[side & np.array([set(f).issubset(step_verts) for f in m.faces])]

keep = np.vstack([m.faces[up], step_faces])
loops = boundary_loops(keep)
print('kept faces:', len(keep), ' open boundary loops after keep:', len(loops), '(want 1 = outer)')
ring = max(loops, key=lambda L: abs(0.5*np.sum(V[L][:,0]*np.roll(V[L][:,1],-1)-np.roll(V[L][:,0],-1)*V[L][:,1])))
assert len(loops)==1, f'expected single outer loop, got {len(loops)}'

ZFLOOR = float(m.bounds[0][2])
# build skirt + flat cap
verts = V.copy().tolist()
faces = keep.tolist()
botidx = {}
for vi in ring:
    botidx[vi] = len(verts); verts.append([V[vi,0], V[vi,1], ZFLOOR])
n=len(ring)
for i in range(n):                       # vertical skirt quads
    a,b = ring[i], ring[(i+1)%n]; A,B = botidx[a], botidx[b]
    faces.append([a,b,B]); faces.append([a,B,A])
# flat bottom cap (triangulate footprint polygon)
poly = sg.Polygon([(V[vi,0],V[vi,1]) for vi in ring]).buffer(0)
v2d,f2d = trimesh.creation.triangulate_polygon(poly)
base = len(verts)
for x,y in v2d: verts.append([x,y,ZFLOOR])
for t in f2d: faces.append([base+t[0], base+t[2], base+t[1]])   # downward

w = trimesh.Trimesh(np.array(verts), np.array(faces), process=True)
w.merge_vertices()
if w.volume < 0: w.invert()
w.export(OUT)
bb=w.bounds
print(f'WROTE {OUT}  watertight={w.is_watertight}  vol={w.volume:.0f} mm^3')
print(f'  flat bottom Z={ZFLOOR:.3f}  size {bb[1][0]-bb[0][0]:.1f} x {bb[1][1]-bb[0][1]:.1f} x {bb[1][2]-bb[0][2]:.1f} mm')
print(f'  Z range {bb[0][2]:.3f}..{bb[1][2]:.3f}  (top preserved, bottom now flat)')
