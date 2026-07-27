"""
scripts/process_avatar.py
==========================
Blender Python script executed headlessly via:
    blender.exe -b --python scripts/process_avatar.py

This script is executed INSIDE Blender's Python environment (bpy).
Do NOT run this directly with python — it must be called through Blender.

Pipeline:
  1. Clear Blender default scene
  2. Import avatar FBX (assets/avatar/anchor.fbx or Ch33_nonPBR.fbx)
  3. Setup 50mm portrait camera (news anchor framing)
  4. Setup 3-point studio lighting (Key / Fill / Rim)
  5. Export processed_anchor.glb -> assets/avatar/processed_anchor.glb
"""

import bpy
import os
import sys

# ─────────────────────────────────────────
# Resolve Project Root & Avatar Paths
# ─────────────────────────────────────────
# When called via: blender -b --python scripts/process_avatar.py
# __file__ = scripts/process_avatar.py  (or absolute path)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
AVATAR_DIR = os.path.join(PROJECT_ROOT, "assets", "avatar")

# Support anchor.fbx (preferred) or Ch33_nonPBR.fbx (fallback)
INPUT_CANDIDATES = [
    os.path.join(AVATAR_DIR, "anchor.fbx"),
    os.path.join(AVATAR_DIR, "Ch33_nonPBR.fbx"),
]

OUTPUT_GLB = os.path.join(AVATAR_DIR, "processed_anchor.glb")

# Allow external override via environment variable
if "BLENDER_INPUT_AVATAR" in os.environ:
    INPUT_CANDIDATES = [os.environ["BLENDER_INPUT_AVATAR"]] + INPUT_CANDIDATES
if "BLENDER_OUTPUT_GLB" in os.environ:
    OUTPUT_GLB = os.environ["BLENDER_OUTPUT_GLB"]


def log(msg):
    print(f"[Blender Avatar] {msg}", flush=True)


def find_input_avatar():
    for candidate in INPUT_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None


# ─────────────────────────────────────────
# Step 1: Clear Default Scene
# ─────────────────────────────────────────
log("=" * 60)
log("AI-NewsTube — 3D News Anchor Processing Pipeline")
log("=" * 60)
log(f"Project Root : {PROJECT_ROOT}")
log(f"Avatar Dir   : {AVATAR_DIR}")
log(f"Output GLB   : {OUTPUT_GLB}")

log("Step 1: Clearing default Blender scene...")
bpy.ops.wm.read_factory_settings(use_empty=True)

# Remove all objects, meshes, lights, cameras from the blank scene
for block in bpy.data.objects:
    bpy.data.objects.remove(block, do_unlink=True)

# ─────────────────────────────────────────
# Step 2: Import Avatar FBX
# ─────────────────────────────────────────
input_file = find_input_avatar()
if not input_file:
    log("ERROR: No avatar FBX found! Expected:")
    for c in INPUT_CANDIDATES:
        log(f"  - {c}")
    sys.exit(1)

log(f"Step 2: Importing avatar: {os.path.basename(input_file)}")
ext = os.path.splitext(input_file)[1].lower()

try:
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(
            filepath=input_file,
            use_manual_orientation=False,
            global_scale=1.0,
            bake_space_transform=False,
            use_custom_normals=True,
            use_image_search=True,
            use_alpha_decals=False,
            decal_offset=0.0,
            use_anim=True,
            anim_offset=1.0,
            use_subsurf=False,
            use_custom_props=True,
            ignore_leaf_bones=False,
            force_connect_children=False,
            automatic_bone_orientation=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            use_prepost_rot=True,
        )
        log("  FBX import complete.")
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=input_file)
        log("  GLTF/GLB import complete.")
    elif ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=input_file)
        log("  .blend scene loaded.")
    else:
        log(f"  Unsupported format: {ext}")
        sys.exit(1)
except Exception as e:
    log(f"  ERROR during import: {e}")
    sys.exit(1)


# ─────────────────────────────────────────
# Step 3: Setup Portrait Camera
# ─────────────────────────────────────────
log("Step 3: Setting up news presenter portrait camera...")

camera_data = bpy.data.cameras.new(name="NewsAnchorCamera")
camera_data.lens = 50.0          # 50mm — classic portrait / news lens
camera_data.clip_start = 0.1
camera_data.clip_end = 100.0

camera_obj = bpy.data.objects.new("NewsAnchorCamera", camera_data)
bpy.context.scene.collection.objects.link(camera_obj)
bpy.context.scene.camera = camera_obj

# Position camera in front of avatar at anchor height
camera_obj.location = (0.0, -2.2, 1.55)
camera_obj.rotation_euler = (1.47, 0.0, 0.0)  # ~84° tilt looking at avatar

log(f"  Camera: 50mm portrait lens at {camera_obj.location}")


# ─────────────────────────────────────────
# Step 4: Setup 3-Point Studio Lighting
# ─────────────────────────────────────────
log("Step 4: Setting up 3-point news studio lighting...")

# Key Light — primary warm front light
key_data = bpy.data.lights.new(name="KeyLight", type="AREA")
key_data.energy = 1200
key_data.color = (1.0, 0.96, 0.90)
key_data.size = 1.5
key_obj = bpy.data.objects.new("KeyLight", key_data)
bpy.context.scene.collection.objects.link(key_obj)
key_obj.location = (1.8, -1.8, 2.8)
key_obj.rotation_euler = (0.95, 0.0, 0.52)
log("  Key Light: warm area light (1200W)")

# Fill Light — cool soft left side fill
fill_data = bpy.data.lights.new(name="FillLight", type="AREA")
fill_data.energy = 500
fill_data.color = (0.85, 0.92, 1.0)
fill_data.size = 2.0
fill_obj = bpy.data.objects.new("FillLight", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-2.0, -1.6, 2.4)
fill_obj.rotation_euler = (0.95, 0.0, -0.52)
log("  Fill Light: cool area light (500W)")

# Rim / Backlight — creates separation from background
rim_data = bpy.data.lights.new(name="RimLight", type="SPOT")
rim_data.energy = 800
rim_data.color = (0.88, 0.94, 1.0)
rim_data.spot_size = 1.0
rim_obj = bpy.data.objects.new("RimLight", rim_data)
bpy.context.scene.collection.objects.link(rim_obj)
rim_obj.location = (0.0, 2.0, 3.0)
rim_obj.rotation_euler = (-2.3, 0.0, 0.0)
log("  Rim Light: spot backlight (800W)")


# ─────────────────────────────────────────
# Step 5: Configure Scene & Render Settings
# ─────────────────────────────────────────
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = True

# ─────────────────────────────────────────
# Step 6: Render 3D Anchor Character Frame (PNG)
# ─────────────────────────────────────────
RENDER_PNG = os.path.join(PROJECT_ROOT, "assets", "studio", "ai_anchor_3d.png")
log(f"Step 6: Rendering 3D character portrait frame from Blender to {os.path.basename(RENDER_PNG)}...")
os.makedirs(os.path.dirname(RENDER_PNG), exist_ok=True)

try:
    scene.render.filepath = RENDER_PNG
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    # Try EEVEE or Cycles for high quality fast render
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        try:
            scene.render.engine = 'BLENDER_EEVEE'
        except Exception:
            scene.render.engine = 'CYCLES'
            scene.cycles.samples = 16

    bpy.ops.render.render(write_still=True)
    log(f"  SUCCESS: Rendered 3D avatar portrait ({os.path.getsize(RENDER_PNG)} bytes)")
except Exception as e:
    log(f"  WARNING: 3D render warning: {e}")

# ─────────────────────────────────────────
# Step 7: Export processed_anchor.glb
# ─────────────────────────────────────────
log("Step 7: Exporting processed 3D anchor to GLB format...")

os.makedirs(os.path.dirname(OUTPUT_GLB), exist_ok=True)

try:
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format="GLB",
        export_apply=True,           # Apply modifiers
        export_yup=True,             # glTF Y-up convention
        export_materials="EXPORT",   # Include materials
        export_animations=True,      # Include Mixamo rig animations
        export_skins=True,           # Include armature / skinning weights
        export_morph=True,           # Include shape keys / morph targets
        export_cameras=True,         # Include camera
        export_lights=True,          # Include studio lights
    )
    size_bytes = os.path.getsize(OUTPUT_GLB)
    size_mb = size_bytes / (1024 * 1024)
    log(f"  SUCCESS: processed_anchor.glb exported ({size_mb:.2f} MB)")
    log(f"  Path: {OUTPUT_GLB}")
except Exception as e:
    log(f"  ERROR during GLB export: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

log("=" * 60)
log("Blender Avatar Processing Pipeline COMPLETE!")
log("=" * 60)
