import json
import math
import unreal

unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
folder = '/Game/ChronoTest/Cones'
bottom = 28 - 14 * 26 / math.hypot(26, 6)
top = 28 - 6 * 26 / math.hypot(26, 6)

def material(name, directory):
    m = unreal.load_asset(directory + '/' + name)
    if m is None:
        m = tools.create_asset(name, directory, unreal.Material, unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(m)
    return m

def node(m, cls):
    return unreal.MaterialEditingLibrary.create_material_expression(m, cls)

def scalar(m, value):
    n = node(m, unreal.MaterialExpressionConstant)
    n.set_editor_property('r', value)
    return n

def colour(m, rgb):
    n = node(m, unreal.MaterialExpressionConstant3Vector)
    n.set_editor_property('constant', unreal.LinearColor(*rgb, 1))
    return n

def wire(a, b, pin):
    if pin == 'Input': pin = ''
    if not unreal.MaterialEditingLibrary.connect_material_expressions(a, '', b, pin):
        raise RuntimeError('Cannot connect material pin: ' + str(b.get_class().get_name()) + '.' + pin)

def output(n, m, prop):
    unreal.MaterialEditingLibrary.connect_material_property(n, '', prop)

materials = {}
for name, rgb in [('Red', (0.8, .006, .006)), ('Blue', (.006, .05, .8)), ('Yellow', (1, .72, .003))]:
    m = material('M_Cone_' + name, folder)
    # Object-local position keeps the band attached to each translated cone.
    wp = node(m, unreal.MaterialExpressionWorldPosition)
    local = node(m, unreal.MaterialExpressionTransformPosition)
    local.set_editor_property('transform_source_type', unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    local.set_editor_property('transform_type', unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    wire(wp, local, 'Input')
    z = node(m, unreal.MaterialExpressionComponentMask)
    z.set_editor_property('r', False); z.set_editor_property('g', False); z.set_editor_property('b', True)
    wire(local, z, 'Input')
    sub = node(m, unreal.MaterialExpressionSubtract)
    wire(z, sub, 'A'); wire(scalar(m, (bottom + top) / 2), sub, 'B')
    distance = node(m, unreal.MaterialExpressionAbs); wire(sub, distance, 'Input')
    edge = node(m, unreal.MaterialExpressionSubtract)
    wire(distance, edge, 'A'); wire(scalar(m,(top-bottom)/2), edge, 'B')
    ceiling = node(m, unreal.MaterialExpressionCeil); wire(edge,ceiling,'Input')
    clipped = node(m, unreal.MaterialExpressionSaturate); wire(ceiling,clipped,'Input')
    band = node(m, unreal.MaterialExpressionOneMinus); wire(clipped,band,'Input')
    blend = node(m, unreal.MaterialExpressionLinearInterpolate)
    wire(colour(m, rgb), blend, 'A'); wire(colour(m, (.95,.95,.95)), blend, 'B'); wire(band, blend, 'Alpha')
    output(blend, m, unreal.MaterialProperty.MP_BASE_COLOR)
    for a, b, prop in [(.65,.2,unreal.MaterialProperty.MP_ROUGHNESS),(.35,.9,unreal.MaterialProperty.MP_SPECULAR)]:
        lerp = node(m, unreal.MaterialExpressionLinearInterpolate)
        wire(scalar(m,a),lerp,'A');wire(scalar(m,b),lerp,'B');wire(band,lerp,'Alpha');output(lerp,m,prop)
    unreal.MaterialEditingLibrary.recompile_material(m)
    lib.save_loaded_asset(m, False)
    mesh = unreal.load_asset(folder + '/SM_Cone_' + name)
    count = len(mesh.get_editor_property('static_materials'))
    for i in range(count): mesh.set_material(i, m)
    lib.save_loaded_asset(mesh, False)
    materials[name] = m

road = material('M_ChronoAsphalt', '/Game/ChronoTest')
position = node(road, unreal.MaterialExpressionWorldPosition)
noise = node(road, unreal.MaterialExpressionNoise)
noise.set_editor_property('scale', .15)
noise.set_editor_property('levels', 2)
wire(position, noise, 'Position')
mix = node(road, unreal.MaterialExpressionLinearInterpolate)
wire(colour(road,(.025,.028,.032)),mix,'A');wire(colour(road,(.07,.075,.08)),mix,'B');wire(noise,mix,'Alpha')
output(mix,road,unreal.MaterialProperty.MP_BASE_COLOR)
output(scalar(road,.92),road,unreal.MaterialProperty.MP_ROUGHNESS)
unreal.MaterialEditingLibrary.recompile_material(road)
lib.save_loaded_asset(road,False)

unreal.EditorLevelLibrary.load_level('/Game/ChronoTest/ChronoFlat')
counts = {'Red':0, 'Blue':0, 'Yellow':0}
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith('ChronoFlat_Ground'):
        actor.static_mesh_component.set_material(0, road)
    if label.startswith('TrackCone_'):
        name = label.split('_')[1]
        comp = actor.static_mesh_component
        for i in range(comp.get_num_materials()): comp.set_material(i, materials[name])
        counts[name] += 1
    if label == 'ChronoFlat_Sun':
        actor.light_component.set_editor_property('intensity', 5.0)
        actor.set_actor_rotation(unreal.Rotator(-55,-30,0), False)
if not unreal.EditorLevelLibrary.save_current_level(): raise RuntimeError('Save map failed')
with open('/home/wuta/carla/Build/config-logs/appearance-config.json','w') as f:
    json.dump({'cones':counts,'band_z_cm':[bottom,top], 'reference':'6-14cm along slope down from cone top','ground':'M_ChronoAsphalt'},f,indent=2)
unreal.log('APPEARANCE_READY: ' + str(counts))
unreal.SystemLibrary.quit_editor()
