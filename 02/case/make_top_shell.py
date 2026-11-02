#!/usr/bin/env python
"""Generate a Choc V1 hotswap top shell (switch plate + perimeter skirt) from a
KiCad PCB's Edge.Cuts outline and switch positions.

Run inside the venv:  ../.venv-plate/bin/python make_top_shell.py
Geometry inputs were pre-extracted to case/_geom_<side>.json by the parse step.
"""
import json, math
import numpy as np
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity
import trimesh

# ---- design parameters (Choc V1 hotswap) ----------------------------------
PLATE_T   = 1.3    # plate thickness — Choc switch clips engage at ~1.3 mm
CUTOUT    = 13.8   # square switch cutout (Choc V1 plate spec)
WALL_T    = 2.0    # perimeter skirt wall thickness
FIT_GAP   = 0.30   # clearance between PCB edge and inner wall face
PLATE_GAP = 2.2    # plate underside -> PCB top (Choc above-PCB body height)
PCB_T     = 1.6    # PCB thickness
SKIRT_BLW = 1.0    # how far the skirt drops below the PCB bottom
ARC_SEG   = 24     # arc tessellation segments
HOLE_SIDES= 32
INCLUDE_HOLES = True   # carry the 3 interior circles through as holes

WALL_H = PLATE_GAP + PCB_T + SKIRT_BLW   # total skirt height below plate


def tess_arc(a, b, c, n=ARC_SEG):
    """Tessellate arc through start a, mid b, end c."""
    (x1,y1),(x2,y2),(x3,y3) = a,b,c
    d = 2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    if abs(d) < 1e-9:
        return [a, c]
    ux = ((x1**2+y1**2)*(y2-y3)+(x2**2+y2**2)*(y3-y1)+(x3**2+y3**2)*(y1-y2))/d
    uy = ((x1**2+y1**2)*(x3-x2)+(x2**2+y2**2)*(x1-x3)+(x3**2+y3**2)*(x2-x1))/d
    cx,cy = ux,uy
    r = math.hypot(x1-cx,y1-cy)
    a1 = math.atan2(y1-cy,x1-cx)
    a2 = math.atan2(y2-cy,x2-cx)
    a3 = math.atan2(y3-cy,x3-cx)
    # ensure monotone sweep start->mid->end
    def unwrap(prev,ang):
        while ang-prev > math.pi: ang -= 2*math.pi
        while ang-prev < -math.pi: ang += 2*math.pi
        return ang
    a2 = unwrap(a1,a2); a3 = unwrap(a2,a3)
    return [(cx+r*math.cos(a1+(a3-a1)*t/n), cy+r*math.sin(a1+(a3-a1)*t/n)) for t in range(n+1)]


def build_outline(geom):
    """Chain segments + tessellated arcs into one ordered closed ring."""
    edges = [list(s) for s in geom['segs']]
    for a,b,c in geom['arcs']:
        pts = tess_arc(a,b,c)
        for i in range(len(pts)-1):
            edges.append([pts[i],pts[i+1]])
    tol = 1e-3
    def close(p,q): return abs(p[0]-q[0])<tol and abs(p[1]-q[1])<tol
    ring = list(edges.pop(0))
    while edges:
        end = ring[-1]; found=False
        for i,(p,q) in enumerate(edges):
            if close(end,p): ring.append(q); edges.pop(i); found=True; break
            if close(end,q): ring.append(p); edges.pop(i); found=True; break
        if not found:
            raise RuntimeError(f"open outline, {len(edges)} edges left at {end}")
    return sg.Polygon(ring)


def yflip(poly, cx, cy):
    """KiCad Y-down -> model Y-up, about board centre."""
    return affinity.scale(affinity.translate(poly,-cx,-cy), xfact=1, yfact=-1, origin=(0,0))


def extrude(poly, height, z0):
    m = trimesh.creation.extrude_polygon(poly, height)
    m.apply_translation([0,0,z0])
    return m


def make(side):
    g = json.load(open(f"_geom_{side}.json"))
    xs=[p[0] for s in g['segs'] for p in s]; ys=[p[1] for s in g['segs'] for p in s]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2

    board = build_outline(g)
    if not board.is_valid:
        board = board.buffer(0)
    board = yflip(board, cx, cy)

    # footprints
    inner = board.buffer(FIT_GAP)             # inner wall face (PCB fits inside)
    outer = inner.buffer(WALL_T)              # outer wall face
    plate_face = outer                        # top plate spans full outer footprint

    # switch cutouts
    cuts=[]
    for x,y,rot in g['sw']:
        c = sg.box(-CUTOUT/2,-CUTOUT/2,CUTOUT/2,CUTOUT/2)
        c = affinity.rotate(c, -rot, origin=(0,0))     # Y-flip negates rotation
        px,py = x-cx, -(y-cy)
        cuts.append(affinity.translate(c, px, py))
    # interior holes
    if INCLUDE_HOLES:
        for (hx,hy),(ex,ey) in g['circles']:
            r=math.hypot(ex-hx,ey-hy)
            hc=sg.Point(hx-cx,-(hy-cy)).buffer(r,resolution=HOLE_SIDES//4)
            cuts.append(hc)
    holes = unary_union(cuts)

    plate2d = plate_face.difference(holes)
    plate = extrude(plate2d, PLATE_T, 0.0)                 # plate sits at z 0..PLATE_T

    ring2d = outer.difference(inner)                        # skirt cross-section
    skirt  = extrude(ring2d, WALL_H, -WALL_H)               # drops below plate

    shell = trimesh.util.concatenate([plate, skirt])
    try:
        shell = trimesh.boolean.union([plate, skirt])       # weld if manifold engine ok
    except Exception:
        pass

    out=f"top-shell-{side}.stl"
    shell.export(out)
    bb=shell.bounds
    print(f"{side}: {out}  watertight={shell.is_watertight}  "
          f"size {bb[1][0]-bb[0][0]:.1f} x {bb[1][1]-bb[0][1]:.1f} x {bb[1][2]-bb[0][2]:.1f} mm  "
          f"switches={len(g['sw'])} holes={len(g['circles'])}")

for s in ("left","right"):
    make(s)
print(f"\nparams: plate_t={PLATE_T} cutout={CUTOUT} wall_t={WALL_T} fit_gap={FIT_GAP} "
      f"plate_gap={PLATE_GAP} pcb_t={PCB_T} skirt_below={SKIRT_BLW} -> wall_h={WALL_H}")
