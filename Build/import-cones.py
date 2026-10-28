"""Import the STEP-derived mesh and create red, blue and yellow cone assets."""
import json
import math
import unreal

unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
folder = '/Game/ChronoTest/Cones'
task = unreal.AssetImportTask()
task.set_editor_property('filename', '/home/wuta/carla/Build/cone-assets/SM_TrackCone.obj')
task.set_editor_property('destination_path', folder)
task.set_editor_property('destination_name', 'SM_TrackCone')
task.set_editor_property('automated', True)
task.set_editor_property('replace_existing', True)
task.set_editor_property('save', True)
options = unreal.FbxImportUI()
options.set_editor_property('import_mesh', True)
options.set_editor_property('import_materials', False)
options.set_editor_property('import_textures', False)
options.set_editor_property('import_as_skeletal', False)
options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
options.static_mesh_import_data.set_editor_property('combine_meshes', True)
options.static_mesh_import_data.set_editor_property('auto_generate_collision', True)
options.static_mesh_import_data.set_editor_property('convert_scene', False)
task.set_editor_property('options', options)
tools = unreal.AssetToolsHelpers.get_asset_tools()
tools.import_asset_tasks([task])
mesh = unreal.load_asset(folder + '/SM_TrackCone')
if not mesh:
    raise RuntimeError('Mesh import failed: ' + str(task.imported_object_paths))
# STEP cone starts 2 cm above the base; radius tapers 8 to 2 cm over 26 cm.
cone_vertical_cm = 26.0
cone_radius_change_cm = 6.0
cone_slant_cm = math.hypot(cone_vertical_cm, cone_radius_change_cm)
band_bottom_z = 28.0 - 14.0 * cone_vertical_cm / cone_slant_cm
band_top_z = 28.0 - 6.0 * cone_vertical_cm / cone_slant_cm
assets = []
for colour, rgb in [('Red', (0.8,0.01,0.01)), ('Blue', (0.01,0.08,0.8)), ('Yellow', (1.0,0.72,0.005))]:
    material_path = folder + '/M_Cone_' + colour
    material = unreal.load_asset(material_path)
    if material is None:
        material = tools.create_asset('M_Cone_' + colour, folder, unreal.Material, unreal.MaterialFactoryNew())
    if material:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
        def expr(cls):
            return unreal.MaterialEditingLibrary.create_material_expression(material, cls)
        def scalar(value):
            n = expr(unreal.MaterialExpressionConstant)
            n.set_editor_property('r',value)
            return n
        def connect(a,b,pin,output=''):
            unreal.MaterialEditingLibrary.connect_material_expressions(a,output,b,pin)
        uv = expr(unreal.MaterialExpressionTextureCoordinate)
        height = expr(unreal.MaterialExpressionComponentMask)
        height.set_editor_property('r',False)
        height.set_editor_property('g',True)
        connect(uv,height,'Input')
        offset = expr(unreal.MaterialExpressionSubtract)
        connect(height,offset,'A')
        connect(scalar((band_bottom_z + band_top_z) / 2.0 / 28.0),offset,'B')
        distance = expr(unreal.MaterialExpressionAbs)
        connect(offset,distance,'Input')
        band = expr(unreal.MaterialExpressionIf)
        connect(distance,band,'A')
        connect(scalar((band_top_z - band_bottom_z) / 2.0 / 28.0),band,'B')
        connect(scalar(0.0),band,'AGreaterThanB')
        connect(scalar(1.0),band,'AEqualsB')
        connect(scalar(1.0),band,'ALessThanB')
        node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
        node.set_editor_property('constant', unreal.LinearColor(*rgb, 1.0))
        white = expr(unreal.MaterialExpressionConstant3Vector)
        white.set_editor_property('constant', unreal.LinearColor(0.95,0.95,0.95,1))
        blend = expr(unreal.MaterialExpressionLinearInterpolate)
        connect(node,blend,'A')
        connect(white,blend,'B')
        connect(band,blend,'Alpha')
        unreal.MaterialEditingLibrary.connect_material_property(blend, '', unreal.MaterialProperty.MP_BASE_COLOR)
        rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
        rough.set_editor_property('r', 0.65)
        reflect_rough = expr(unreal.MaterialExpressionLinearInterpolate)
        connect(rough,reflect_rough,'A')
        connect(scalar(0.2),reflect_rough,'B')
        connect(band,reflect_rough,'Alpha')
        unreal.MaterialEditingLibrary.connect_material_property(reflect_rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        specular = expr(unreal.MaterialExpressionLinearInterpolate)
        connect(scalar(0.35),specular,'A')
        connect(scalar(0.9),specular,'B')
        connect(band,specular,'Alpha')
        unreal.MaterialEditingLibrary.connect_material_property(specular, '', unreal.MaterialProperty.MP_SPECULAR)
        unreal.MaterialEditingLibrary.recompile_material(material)
    path = folder + '/SM_Cone_' + colour
    variant = unreal.load_asset(path) or unreal.EditorAssetLibrary.duplicate_asset(folder + '/SM_TrackCone', path)
    if variant:
        # Recreate the copied mesh so updated height UVs reach every colour.
        unreal.EditorAssetLibrary.delete_asset(path)
        variant = unreal.EditorAssetLibrary.duplicate_asset(folder + '/SM_TrackCone', path)
    variant.set_material(0, material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    unreal.EditorAssetLibrary.save_loaded_asset(variant, False)
    assets.append({'colour': colour, 'mesh': path, 'material': material_path})
bounds = mesh.get_bounds()
summary = {'assets': assets, 'reflective_band_cm': {'distance_along_cone_from_top': [6,14], 'width_along_cone':8, 'vertical_z_from_base': [band_bottom_z,band_top_z], 'measured_cone_slant':cone_slant_cm, 'reference':'cone top at z=28cm; measured downward along slope; source geometry preserved'},
           'reflection_model': 'white low-roughness high-specular PBR approximation; no retroreflection calibration',
           'box_extent_cm': [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
           'bounds_origin_cm': [bounds.origin.x, bounds.origin.y, bounds.origin.z],
           'note': 'Static mesh assets imported; runtime spawning and collision response not yet tested.'}
with open('/home/wuta/carla/Build/config-logs/import-cones-result.json', 'w') as f:
    json.dump(summary, f, indent=2)
unreal.log('CONE_IMPORT_READY: ' + json.dumps(summary))
unreal.SystemLibrary.quit_editor()
