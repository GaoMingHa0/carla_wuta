import json
import unreal

unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
lib=unreal.EditorAssetLibrary
m=unreal.load_asset('/Game/ChronoTest/M_ChronoAsphalt')
m.set_editor_property('two_sided',True)
unreal.MaterialEditingLibrary.delete_all_material_expressions(m)
def node(cls):return unreal.MaterialEditingLibrary.create_material_expression(m,cls)
def wire(a,b,pin):
    assert unreal.MaterialEditingLibrary.connect_material_expressions(a,'',b,pin),pin
def scalar(value):
    n=node(unreal.MaterialExpressionConstant);n.set_editor_property('r',value);return n
def output(n,prop):assert unreal.MaterialEditingLibrary.connect_material_property(n,'',prop)

position=node(unreal.MaterialExpressionWorldPosition)
xy=node(unreal.MaterialExpressionComponentMask)
xy.set_editor_property('r',True);xy.set_editor_property('g',True)
wire(position,xy,'')
scale=node(unreal.MaterialExpressionDivide)
wire(xy,scale,'A');wire(scalar(200.0),scale,'B')
texture=unreal.load_asset('/Game/Carla/Static/GenericMaterials/Asphalt/Textures/Asphalt01/T_Asphalt01_d')
if not texture:raise RuntimeError('Asphalt texture missing')
sample=node(unreal.MaterialExpressionTextureSample)
sample.set_editor_property('texture',texture)
wire(scale,sample,'UVs')
desaturate=node(unreal.MaterialExpressionDesaturation)
wire(sample,desaturate,'');wire(scalar(1.0),desaturate,'Fraction')
darken=node(unreal.MaterialExpressionMultiply)
wire(desaturate,darken,'A');wire(scalar(.7),darken,'B')
output(darken,unreal.MaterialProperty.MP_BASE_COLOR)
output(scalar(.9),unreal.MaterialProperty.MP_ROUGHNESS)
output(scalar(.25),unreal.MaterialProperty.MP_SPECULAR)
unreal.MaterialEditingLibrary.recompile_material(m)
lib.save_loaded_asset(m,False)

apron=unreal.load_asset('/Game/ChronoTest/M_FSACApron')
if apron:
    unreal.MaterialEditingLibrary.delete_all_material_expressions(apron)
    rgb=unreal.MaterialEditingLibrary.create_material_expression(apron,unreal.MaterialExpressionConstant3Vector)
    rgb.set_editor_property('constant',unreal.LinearColor(.2,.2,.2,1))
    unreal.MaterialEditingLibrary.connect_material_property(rgb,'',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=unreal.MaterialEditingLibrary.create_material_expression(apron,unreal.MaterialExpressionConstant)
    rough.set_editor_property('r',.95)
    unreal.MaterialEditingLibrary.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(apron);lib.save_loaded_asset(apron,False)

unreal.EditorLevelLibrary.load_level('/Game/ChronoTest/FSACLoop')
report={'texture':texture.get_path_name(),'tile_size_m':2,'roughness':.9,'texture_saturation':0.0,'road_z_cm':1.0,'apron_top_cm':0}
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if actor.get_actor_label()=='ChronoFlat_Sun':
        actor.light_component.set_editor_property('use_temperature',False)
        actor.light_component.set_editor_property('light_color',unreal.Color(255,255,255,255))
    elif actor.get_actor_label()=='Daylight_Ambient':
        comp=actor.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property('light_color',unreal.Color(255,255,255,255))
        comp.set_editor_property('cubemap',unreal.load_asset('/Engine/EngineResources/GrayTextureCube.GrayTextureCube'))
    elif actor.get_actor_label()=='FSAC_AsphaltRoad_3p5m':
        actor.static_mesh_component.set_material(0,m)
        actor.set_actor_scale3d(unreal.Vector(1,-1,1))
        actor.set_actor_location(unreal.Vector(0,0,1.0),False,False)
        report['road_actor']=actor.get_actor_label()
    elif actor.get_actor_label().startswith('ChronoFlat_Ground'):
        if apron:actor.static_mesh_component.set_material(0,apron)
if not unreal.EditorLevelLibrary.save_current_level():raise RuntimeError('Cannot save map')
open('/home/wuta/carla/Build/config-logs/asphalt-texture-config.json','w').write(json.dumps(report,indent=2))
unreal.log('ASPHALT_TEXTURE_READY: '+str(report))
unreal.SystemLibrary.quit_editor()
