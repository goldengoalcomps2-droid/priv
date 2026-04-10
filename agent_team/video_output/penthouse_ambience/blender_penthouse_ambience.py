"""
Blender Recreation Script: Luxury Penthouse Ambience
Based on video analysis of: https://www.youtube.com/watch?v=yZ3M8-d1QU4

Scene: Rooftop penthouse with infinity pool, city skyline with
skyscrapers, sunset/twilight sky transitioning through deep blues
and purples, cinematic vignette, moody ambient atmosphere.

Usage:
    1. Open Blender
    2. Go to Scripting workspace
    3. Open this file
    4. Click "Run Script"
    5. Render > Render Animation (or press Ctrl+F12)

Output: 5-minute (9000 frames @ 30fps) dark ambience video at 1920x1080
"""

import bpy
import math
import random

# ═══════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in bpy.data.collections:
    bpy.data.collections.remove(c)
for m in bpy.data.materials:
    bpy.data.materials.remove(m)
for w in bpy.data.worlds:
    bpy.data.worlds.remove(w)

# ═══════════════════════════════════════════════════════════
# RENDER SETTINGS - 5 minute video at 1080p 30fps
# ═══════════════════════════════════════════════════════════
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 9000  # 5 minutes
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.ffmpeg.audio_codec = 'AAC'

# Use Eevee for speed
scene.render.engine = 'BLENDER_EEVEE'

# ═══════════════════════════════════════════════════════════
# COLOUR PALETTE (from video analysis)
# ═══════════════════════════════════════════════════════════
BLACK = (0.0, 0.0, 0.0, 1.0)
DARK_BLUE = (0.02, 0.04, 0.12, 1.0)
DARK_PURPLE = (0.08, 0.02, 0.14, 1.0)
MUTED_BLUE = (0.06, 0.10, 0.22, 1.0)
SUNSET_ORANGE = (0.35, 0.12, 0.05, 1.0)
SUNSET_PINK = (0.25, 0.08, 0.15, 1.0)
POOL_CYAN = (0.02, 0.15, 0.20, 1.0)
POOL_GLOW = (0.05, 0.25, 0.35, 1.0)
WINDOW_WARM = (0.4, 0.3, 0.15, 1.0)
CITY_LIGHT = (0.6, 0.55, 0.4, 1.0)

# ═══════════════════════════════════════════════════════════
# WORLD / SKY - Gradient sunset to night
# ═══════════════════════════════════════════════════════════
world = bpy.data.worlds.new("AmbienceWorld")
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

# Sky gradient using texture coordinate + gradient
tex_coord = nodes.new('ShaderNodeTexCoord')
mapping = nodes.new('ShaderNodeMapping')
gradient = nodes.new('ShaderNodeTexGradient')
gradient.gradient_type = 'LINEAR'

color_ramp = nodes.new('ShaderNodeValToRGB')
color_ramp.color_ramp.elements[0].position = 0.0
color_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.02, 1)  # Deep black at top
color_ramp.color_ramp.elements[1].position = 0.4
color_ramp.color_ramp.elements[1].color = (0.02, 0.03, 0.10, 1)  # Dark blue middle

e2 = color_ramp.color_ramp.elements.new(0.55)
e2.color = (0.06, 0.02, 0.12, 1)  # Purple band

e3 = color_ramp.color_ramp.elements.new(0.65)
e3.color = (0.20, 0.06, 0.08, 1)  # Sunset orange/red glow

e4 = color_ramp.color_ramp.elements.new(0.75)
e4.color = (0.30, 0.10, 0.05, 1)  # Warm horizon

e5 = color_ramp.color_ramp.elements.new(1.0)
e5.color = (0.08, 0.04, 0.03, 1)  # Faded warm bottom

bg = nodes.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 0.8
output = nodes.new('ShaderNodeOutputWorld')

links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
mapping.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
links.new(gradient.outputs['Color'], color_ramp.inputs['Fac'])
links.new(color_ramp.outputs['Color'], bg.inputs['Color'])
links.new(bg.outputs['Background'], output.inputs['Surface'])

# ═══════════════════════════════════════════════════════════
# CAMERA
# ═══════════════════════════════════════════════════════════
bpy.ops.object.camera_add(location=(0, -12, 3.5), rotation=(math.radians(82), 0, 0))
camera = bpy.context.active_object
camera.name = "AmbienceCamera"
scene.camera = camera
camera.data.lens = 28  # Wide angle for penthouse feel
camera.data.dof.use_dof = True
camera.data.dof.aperture_fstop = 2.8
camera.data.dof.focus_distance = 15

# Very subtle camera drift over 5 minutes
camera.keyframe_insert(data_path="location", frame=1)
camera.location = (0.15, -11.8, 3.55)
camera.keyframe_insert(data_path="location", frame=4500)
camera.location = (-0.1, -12.1, 3.45)
camera.keyframe_insert(data_path="location", frame=9000)

# Smooth interpolation
for fc in camera.animation_data.action.fcurves:
    for kf in fc.keyframe_points:
        kf.interpolation = 'BEZIER'
        kf.easing = 'EASE_IN_OUT'

# ═══════════════════════════════════════════════════════════
# PENTHOUSE FLOOR / DECK
# ═══════════════════════════════════════════════════════════
# Dark stone/concrete deck
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
deck = bpy.context.active_object
deck.name = "PenthouseDeck"
deck_mat = bpy.data.materials.new("DeckMaterial")
deck_mat.use_nodes = True
deck_nodes = deck_mat.node_tree.nodes
deck_bsdf = deck_nodes["Principled BSDF"]
deck_bsdf.inputs['Base Color'].default_value = (0.03, 0.03, 0.04, 1)
deck_bsdf.inputs['Roughness'].default_value = 0.85
deck.data.materials.append(deck_mat)

# ═══════════════════════════════════════════════════════════
# INFINITY POOL
# ═══════════════════════════════════════════════════════════
# Pool basin
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 3, -0.15))
pool = bpy.context.active_object
pool.name = "InfinityPool"
pool.scale = (5, 2.5, 0.4)
pool_mat = bpy.data.materials.new("PoolEdge")
pool_mat.use_nodes = True
pool_bsdf = pool_mat.node_tree.nodes["Principled BSDF"]
pool_bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.03, 1)
pool_bsdf.inputs['Roughness'].default_value = 0.3
pool.data.materials.append(pool_mat)

# Pool water surface
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 3, 0.1))
water = bpy.context.active_object
water.name = "PoolWater"
water.scale = (4.8, 2.3, 1)

water_mat = bpy.data.materials.new("WaterMaterial")
water_mat.use_nodes = True
wn = water_mat.node_tree.nodes
wl = water_mat.node_tree.links
w_bsdf = wn["Principled BSDF"]
w_bsdf.inputs['Base Color'].default_value = POOL_CYAN
w_bsdf.inputs['Roughness'].default_value = 0.05
w_bsdf.inputs['IOR'].default_value = 1.33
w_bsdf.inputs['Alpha'].default_value = 0.7
w_bsdf.inputs['Metallic'].default_value = 0.0
# Emission - compatible with Blender 4.0+
try:
    w_bsdf.inputs['Emission Color'].default_value = POOL_GLOW
    w_bsdf.inputs['Emission Strength'].default_value = 0.3
except KeyError:
    w_bsdf.inputs['Emission'].default_value = POOL_GLOW
    w_bsdf.inputs['Emission Strength'].default_value = 0.3

# Animated water ripple via noise texture
noise = wn.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 8
noise.inputs['Detail'].default_value = 6
noise.inputs['Roughness'].default_value = 0.7

# Animate noise offset for water movement via mapping node
water_mapping = wn.new('ShaderNodeMapping')
water_texcoord = wn.new('ShaderNodeTexCoord')
wl.new(water_texcoord.outputs['Generated'], water_mapping.inputs['Vector'])
wl.new(water_mapping.outputs['Vector'], noise.inputs['Vector'])

# Keyframe the mapping offset to animate water
water_mapping.inputs['Location'].default_value = (0, 0, 0)
water_mapping.inputs['Location'].keyframe_insert(data_path="default_value", frame=1)
water_mapping.inputs['Location'].default_value = (5, 3, 0)
water_mapping.inputs['Location'].keyframe_insert(data_path="default_value", frame=9000)

bump = wn.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.02
wl.new(noise.outputs['Fac'], bump.inputs['Height'])
wl.new(bump.outputs['Normal'], w_bsdf.inputs['Normal'])

if hasattr(water_mat, 'blend_method'):
    water_mat.blend_method = 'BLEND'
water.data.materials.append(water_mat)

# ═══════════════════════════════════════════════════════════
# CITY SKYLINE - Skyscrapers
# ═══════════════════════════════════════════════════════════
building_mat = bpy.data.materials.new("BuildingMaterial")
building_mat.use_nodes = True
b_bsdf = building_mat.node_tree.nodes["Principled BSDF"]
b_bsdf.inputs['Base Color'].default_value = (0.01, 0.015, 0.03, 1)
b_bsdf.inputs['Roughness'].default_value = 0.4

# Window glow material
window_mat = bpy.data.materials.new("WindowGlow")
window_mat.use_nodes = True
win_bsdf = window_mat.node_tree.nodes["Principled BSDF"]
win_bsdf.inputs['Base Color'].default_value = WINDOW_WARM
win_bsdf.inputs['Emission Color'].default_value = WINDOW_WARM
win_bsdf.inputs['Emission Strength'].default_value = 2.0

# Generate skyline
random.seed(42)
for i in range(25):
    x = -20 + i * 1.8 + random.uniform(-0.5, 0.5)
    y = 20 + random.uniform(0, 8)
    height = random.uniform(4, 14)
    width = random.uniform(0.6, 1.4)
    depth = random.uniform(0.6, 1.2)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, height/2))
    building = bpy.context.active_object
    building.name = f"Skyscraper_{i}"
    building.scale = (width, depth, height)
    building.data.materials.append(building_mat)

    # Add some lit windows (small emissive cubes on building face)
    if random.random() > 0.3:
        for j in range(random.randint(2, 6)):
            wx = x + random.uniform(-width*0.4, width*0.4)
            wz = random.uniform(1, height - 1)
            bpy.ops.mesh.primitive_cube_add(size=0.15, location=(wx, y - depth*0.51, wz))
            win = bpy.context.active_object
            win.name = f"Window_{i}_{j}"
            win.scale = (random.uniform(0.5, 1.5), 0.1, random.uniform(0.3, 0.8))
            win.data.materials.append(window_mat)

# ═══════════════════════════════════════════════════════════
# PENTHOUSE GLASS RAILING
# ═══════════════════════════════════════════════════════════
glass_mat = bpy.data.materials.new("GlassRailing")
glass_mat.use_nodes = True
g_bsdf = glass_mat.node_tree.nodes["Principled BSDF"]
g_bsdf.inputs['Base Color'].default_value = (0.8, 0.85, 0.9, 1)
g_bsdf.inputs['Alpha'].default_value = 0.15
g_bsdf.inputs['Roughness'].default_value = 0.05
g_bsdf.inputs['IOR'].default_value = 1.5

# Front railing
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 5.5, 0.6))
railing = bpy.context.active_object
railing.name = "GlassRailing"
railing.scale = (6, 0.03, 0.6)
railing.data.materials.append(glass_mat)

# ═══════════════════════════════════════════════════════════
# AMBIENT FURNITURE
# ═══════════════════════════════════════════════════════════
# Lounge chairs by the pool
lounge_mat = bpy.data.materials.new("LoungeMaterial")
lounge_mat.use_nodes = True
l_bsdf = lounge_mat.node_tree.nodes["Principled BSDF"]
l_bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.06, 1)
l_bsdf.inputs['Roughness'].default_value = 0.6

for i, x in enumerate([-3, -1.5, 1.5, 3]):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.5, 0.2))
    chair = bpy.context.active_object
    chair.name = f"LoungeChair_{i}"
    chair.scale = (0.4, 0.9, 0.15)
    chair.data.materials.append(lounge_mat)

# ═══════════════════════════════════════════════════════════
# LIGHTING
# ═══════════════════════════════════════════════════════════
# Sunset glow from horizon
bpy.ops.object.light_add(type='AREA', location=(0, 30, 5))
sunset_light = bpy.context.active_object
sunset_light.name = "SunsetGlow"
sunset_light.data.energy = 50
sunset_light.data.color = (1.0, 0.4, 0.2)
sunset_light.data.size = 40
sunset_light.rotation_euler = (math.radians(100), 0, 0)

# Animate sunset fading slightly over 5 min
sunset_light.data.energy = 50
sunset_light.data.keyframe_insert(data_path="energy", frame=1)
sunset_light.data.energy = 35
sunset_light.data.keyframe_insert(data_path="energy", frame=9000)

# Pool underwater glow
bpy.ops.object.light_add(type='AREA', location=(0, 3, -0.3))
pool_light = bpy.context.active_object
pool_light.name = "PoolGlow"
pool_light.data.energy = 20
pool_light.data.color = (0.1, 0.5, 0.7)
pool_light.data.size = 8
pool_light.rotation_euler = (0, 0, 0)

# Subtle ambient fill
bpy.ops.object.light_add(type='AREA', location=(0, -5, 8))
fill = bpy.context.active_object
fill.name = "AmbientFill"
fill.data.energy = 10
fill.data.color = (0.3, 0.3, 0.5)
fill.data.size = 15
fill.rotation_euler = (math.radians(60), 0, 0)

# City light bounce
bpy.ops.object.light_add(type='POINT', location=(0, 15, 2))
city_bounce = bpy.context.active_object
city_bounce.name = "CityBounce"
city_bounce.data.energy = 15
city_bounce.data.color = (0.7, 0.6, 0.4)

# ═══════════════════════════════════════════════════════════
# COMPOSITING - Vignette + Colour Grade
# ═══════════════════════════════════════════════════════════
scene.use_nodes = True
tree = scene.node_tree
nodes_c = tree.nodes
links_c = tree.links
nodes_c.clear()

rl = nodes_c.new('CompositorNodeRLayers')
comp = nodes_c.new('CompositorNodeComposite')

# Colour balance - push shadows to blue/purple
cb = nodes_c.new('CompositorNodeColorBalance')
cb.correction_method = 'LIFT_GAMMA_GAIN'
cb.lift = (0.85, 0.85, 1.0)  # Blue shadows
cb.gamma = (0.95, 0.90, 1.0)  # Purple midtones
cb.gain = (1.0, 0.95, 0.90)  # Warm highlights

# Ellipse mask for vignette
ellipse = nodes_c.new('CompositorNodeEllipseMask')
ellipse.width = 0.85
ellipse.height = 0.85

blur_v = nodes_c.new('CompositorNodeBlur')
blur_v.size_x = 200
blur_v.size_y = 200

mix_vig = nodes_c.new('CompositorNodeMixRGB')
mix_vig.blend_type = 'MULTIPLY'
mix_vig.inputs['Fac'].default_value = 0.7

# Slight glow/bloom
glare = nodes_c.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'MEDIUM'
glare.mix = -0.85
glare.threshold = 0.8
glare.size = 6

# Wire up compositing
links_c.new(rl.outputs['Image'], cb.inputs['Image'])
links_c.new(cb.outputs['Image'], glare.inputs['Image'])
links_c.new(glare.outputs['Image'], mix_vig.inputs[1])
links_c.new(ellipse.outputs['Mask'], blur_v.inputs['Image'])
links_c.new(blur_v.outputs['Image'], mix_vig.inputs[2])
links_c.new(mix_vig.outputs['Image'], comp.inputs['Image'])

# ═══════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("  PENTHOUSE AMBIENCE SCENE READY")
print("=" * 60)
print(f"  Duration: 5 minutes (9000 frames @ 30fps)")
print(f"  Resolution: 1920x1080")
print(f"  Scene: Luxury penthouse, infinity pool, city skyline, sunset")
print(f"  Palette: Deep blacks, dark blues, muted purples, warm sunset")
print(f"  Effects: Vignette, colour grade, pool water ripple, bloom")
print(f"  Render: Press Ctrl+F12 or Render > Render Animation")
print("=" * 60)
