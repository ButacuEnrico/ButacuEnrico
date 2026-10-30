"""Blender turntable of the AI year as real 3D pillars, for turntable.webp.

371 days of Claude Code + Codex tokens (data/ai-usage.json) stand as bevelled
pillars on a dark plinth in a dark studio; the camera circles once per loop.
Run headless; it writes PNG frames, then scripts/make_turntable.sh packs them.

  blender -b -P scripts/turntable.py -- <frames_dir> [first last [samples [percent]]]
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(ARGS[0]) if ARGS else ROOT / "build" / "frames"
FRAMES = 96
FIRST, LAST = (int(ARGS[1]), int(ARGS[2])) if len(ARGS) > 2 else (1, FRAMES)
COLS = 20
AMBER = (1.0, 0.24, 0.02)
GREEN = (0.02, 0.55, 0.28)


def material(name, colour, rough, emit=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*colour, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*colour, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return m


def pillar(name, x, y, w, h, mat, bevel=0.035):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * w, (v.co.z + 0.5) * h))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, h / 3), segments=2, affect="EDGES")
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (x, y, 0)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    usage = json.loads((ROOT / "data" / "ai-usage.json").read_text())
    claude, codex = usage["claude"]["year"], usage["openai"]["year"]
    peak = max(a + b for a, b in zip(claude, codex)) or 1
    rows = math.ceil(len(claude) / COLS)

    idle = material("idle", (0.035, 0.04, 0.05), 0.55)
    lit = {"claude": material("claude", AMBER, 0.28, emit=0.08),
           "openai": material("openai", GREEN, 0.28, emit=0.08)}
    plinth = material("plinth", (0.012, 0.013, 0.016), 0.35)
    floor = material("floor", (0.006, 0.006, 0.008), 0.42)

    for i, (a, b) in enumerate(zip(claude, codex)):
        c, r = i % COLS, i // COLS
        x, y = (c - (COLS - 1) / 2) * 1.0, ((rows - 1) / 2 - r) * 1.0
        ripple = 0.08 * math.sin(c * 0.6) * math.cos(r * 0.5)
        if a + b:
            h = 0.45 + 3.4 * math.sqrt((a + b) / peak)
            pillar(f"day{i}", x, y, 0.86, h, lit["claude" if a >= b else "openai"])
        else:
            pillar(f"day{i}", x, y, 0.86, 0.22 + ripple + 0.04, idle)

    base = pillar("plinth", 0, 0, 1.0, 0.7, plinth, bevel=0.12)
    base.scale = (COLS + 1.4, rows + 1.4, 1)
    base.location.z = -0.7
    ground = pillar("floor", 0, 0, 1.0, 0.01, floor, bevel=0.0)
    ground.scale = (400, 400, 1)
    ground.location.z = -0.71

    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.005, 0.007, 1)
    scene.world = world

    def light(name, kind, loc, energy, colour=(1, 1, 1), size=6.0):
        data = bpy.data.lights.new(name, kind)
        data.energy = energy
        data.color = colour
        if kind == "AREA":
            data.size = size
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        direction = Vector((0, 0, 0.6)) - Vector(loc)
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(obj)

    light("key", "AREA", (-14, -10, 22), 9000, size=14)
    light("rim", "AREA", (16, 18, 9), 3500, colour=(1.0, 0.55, 0.22), size=10)
    light("fill", "AREA", (18, -16, 6), 1200, colour=(0.6, 0.75, 1.0), size=12)

    rig = bpy.data.objects.new("rig", None)
    bpy.context.collection.objects.link(rig)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 42
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 5.6
    cam = bpy.data.objects.new("cam", cam_data)
    cam.parent = rig
    cam.location = (0, -42, 28)
    cam.rotation_euler = (Vector((0, 0, 0.4)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
    cam_data.dof.focus_distance = (Vector(cam.location) - Vector((0, 0, 0.4))).length
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    scene.cycles.device = "GPU"
    scene.cycles.samples = int(ARGS[3]) if len(ARGS) > 3 else 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 880, 440
    scene.render.resolution_percentage = int(ARGS[4]) if len(ARGS) > 4 else 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"  # no alpha: it smears lossy WebP frames
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    return scene, rig


def main():
    scene, rig = build()
    OUT.mkdir(parents=True, exist_ok=True)
    for frame in range(FIRST, LAST + 1):
        rig.rotation_euler.z = (frame - 1) / FRAMES * 2 * math.pi
        scene.render.filepath = str(OUT / f"f{frame:03d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"frame {frame}/{LAST}", flush=True)


main()
