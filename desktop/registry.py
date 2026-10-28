# SPDX-License-Identifier: GPL-3.0-or-later
"""Versioned node contracts shared by UI, persistence and Blender worker."""
from copy import deepcopy

NODES = {}


def register(name, category, inputs=(), defaults=None, enums=None, mask=False):
    NODES[name] = dict(category=category, inputs=list(inputs), defaults=defaults or {},
                       enums=enums or {}, mask=mask, version=1)


register('Read', 'Image', defaults={'path': '', 'colorspace': 'Auto', 'alpha': 'Auto', 'layer': 'Image'},
         enums={'colorspace': ['Auto', 'sRGB', 'Linear Rec.709', 'Non-Color'], 'alpha': ['Auto', 'STRAIGHT', 'PREMUL', 'CHANNEL_PACKED', 'NONE']})
register('Constant', 'Image', defaults={'r': .18, 'g': .18, 'b': .18, 'a': 1.})
register('Write', 'Image', ['Image'], {'preserve_exr': '', 'output_layer': ''})
register('Color', 'Color', ['Image'], {'exposure': 0.})
register('Grade', 'Color', ['Image'], dict(blackpoint=0., whitepoint=1., lift=0., gain=1., multiply=1., offset=0., gamma=1.,gain_r=1.,gain_g=1.,gain_b=1.,offset_r=0.,offset_g=0.,offset_b=0.,gamma_r=1.,gamma_g=1.,gamma_b=1.))
register('ColorCorrect', 'Color', ['Image'], dict(saturation=1., contrast=1., gamma=1., gain=1., lift=0., **{region+'_'+key:value for region in ['shadows','midtones','highlights'] for key,value in dict(saturation=1.,contrast=1.,gamma=1.,gain=1.,lift=0.).items()}))
register('Multiply', 'Color', ['Image'], {'value': 1.})
register('Add', 'Color', ['Image'], {'value': 0.})
register('Clamp', 'Color', ['Image'], {'minimum': 0., 'maximum': 1.})
register('Invert', 'Color', ['Image'])
register('ColorSpace', 'Color', ['Image'], {'source': 'sRGB', 'destination': 'Linear Rec.709'})
register('Premult', 'Channel', ['Image'])
register('Unpremult', 'Channel', ['Image'])
register('Shuffle', 'Channel', ['Image'], dict(r='R', g='G', b='B', a='A'), {k: ['R','G','B','A','0','1'] for k in 'rgba'})
register('Copy', 'Channel', ['B', 'A'], {'source': 'A', 'destination': 'A'}, {k: list('RGBA') for k in ['source','destination']})
register('AlphaMask', 'Channel', ['Image'], mask=True)
register('Merge', 'Merge', ['B', 'A', 'Mask'], {'mix': 1., 'operation': 'over'}, {'operation': ['over','plus','multiply','screen','difference']})
register('Blur', 'Filter', ['Image'], {'size': 8})
register('DilateErode', 'Filter', ['Image'], {'distance': 0})
register('EdgeBlur', 'Filter', ['Image'], {'size': 2})
register('Transform', 'Transform', ['Image'], {'x': 0., 'y': 0., 'scale': 1., 'rotation': 0., 'pivot_x': .5, 'pivot_y': .5})
register('Crop', 'Transform', ['Image'], {'left': 0, 'bottom': 0, 'right': 960, 'top': 540})
register('Reformat', 'Transform', ['Image'], {'width': 960, 'height': 540})
register('CornerPin', 'Transform', ['Image'], {'corners': [[0.,0.],[1.,0.],[1.,1.],[0.,1.]]})
register('FrameHold', 'Time', ['Image'], {'frame': 1})
register('TimeOffset', 'Time', ['Image'], {'offset': 0})
register('TimeRemap', 'Time', ['Image'], {'source_frame': 1.})
register('Switch', 'Time', ['B','A'], {'which': 0}, {'which': [0,1]})
register('Mask', 'Draw', defaults={'x': .5, 'y': .5, 'width': .6, 'height': .6}, mask=True)
register('Roto', 'Draw', defaults={'points': [], 'feather': 0., 'invert': False, 'shape_name': 'Shape1', 'shape_operation': 'max', 'shape_order': 0, 'shapes': [], 'x':0., 'y':0., 'scale':1., 'rotation':0.}, enums={'shape_operation':['max','add','subtract','intersect']}, mask=True)
register('MaskCombine', 'Draw', ['B','A'], {'operation':'max'}, {'operation':['max','add','subtract','intersect']}, mask=True)
register('ChromaKey', 'Keyer', ['Image'], {'r': 0., 'g': 1., 'b': 0., 'screen_balance': .5, 'despill': 1., 'clip_black': 0., 'clip_white': 1.,'blur_pre':0,'blur_post':0,'dilate_distance':0,'feather_distance':0,'edge_kernel_radius':3,'edge_kernel_tolerance':.1,'despill_balance':.5,'output':'Image'}, {'output':['Image','Matte','Edges']})
register('LumaKey', 'Keyer', ['Image'], {'low': .1, 'high': .9})
register('Despill', 'Keyer', ['Image'], {'channel': 'G', 'factor': 1.}, {'channel': ['R','G','B']})
register('Tracker2D', 'Tracking', ['Image'], {'tracking_path': '', 'pattern_size': 31, 'pyramid_levels': 4, 'max_fb_error': 1., 'max_step': 64., 'tracks': [], 'reference': 1, 'mode': 'matchmove', 'x': 0., 'y': 0., 'scale': 1., 'rotation': 0.}, {'mode': ['matchmove','stabilize']})
register('PlanarTracker', 'Tracking', ['Image'], {'tracking_path': '', 'pattern_size': 31, 'pyramid_levels': 4, 'max_fb_error': 1., 'max_step': 64., 'corners': [[.2,.2],[.8,.2],[.8,.8],[.2,.8]], 'reference': 1, 'mode':'cornerpin'}, {'mode':['cornerpin','matchmove','stabilize']})
register('ZDefocus', 'Filter', ['Image','Depth'], {'fstop': 128., 'zscale': 1., 'maxblur': 16.})
register('VectorBlur', 'Filter', ['Image','Depth','Vector'], {'samples': 16, 'factor': 1.})
register('Grain', 'Filter', ['Image'], {'amount': .01, 'seed': 1})
register('Regrain', 'Filter', ['Image','Plate','Clean'], {'amount': 1.})
register('Cryptomatte', 'Channel', defaults={'path': '', 'layer': '', 'matte_id': ''}, mask=True)
register('Dot', 'Utilities', ['Image'])
register('Backdrop', 'Utilities', defaults={'label': 'Backdrop', 'width': 400., 'height': 260.})

register('Camera', '3D', defaults=dict(x=0.,y=0.,z=6.,rx=0.,ry=0.,rz=0.,lens=50.,near=.1,far=1000.))
register('Card', '3D', defaults=dict(x=0.,y=0.,z=0.,rx=0.,ry=0.,rz=0.,scale=1.,r=.8,g=.35,b=.08,texture_path=''))
register('Geometry', '3D', defaults=dict(x=0.,y=0.,z=0.,rx=20.,ry=25.,rz=0.,scale=1.,r=.8,g=.35,b=.08,primitive='cube'), enums={'primitive':['cube','sphere','plane']})
register('Light', '3D', defaults=dict(x=2.,y=3.,z=4.,rx=0.,ry=0.,rz=0.,energy=800.,size=4.))
register('Project3D', '3D', ['Object','Camera'], dict(texture_path=''))
register('Scene', '3D', ['Object','Object2','Light'], dict(ambient=.15))
register('RenderLayers', '3D', ['Scene','Camera'], dict(samples=16,pass_name='Image'), {'pass_name':['Image','Alpha','Depth','Normal']})
TYPES = {'Camera':'camera','Card':'object','Geometry':'object','Project3D':'object','Light':'light','Scene':'scene'}
SOCKET_TYPES = {'Object':'object','Object2':'object','Light':'light','Scene':'scene','Camera':'camera'}

NODES['Roto']['defaults'].update(groups=[],shape_group='',shape_enabled=True,shape_opacity=1.,shape_x=0.,shape_y=0.,shape_scale=1.,shape_rotation=0.,motion_samples=1,shutter=.5)
for kind in ('Tracker2D','PlanarTracker'):NODES[kind]['defaults'].update(manual_points={},exclude_polygon=[],correction_points=[])
INPUTS = {k: v['inputs'] for k,v in NODES.items()}
DEFAULTS = {k: deepcopy(v['defaults']) for k,v in NODES.items()}
MASKS = {k for k,v in NODES.items() if v['mask']}
CATEGORY_COLORS = dict(Image='#c9a452', Color='#539bc2', Channel='#679bb5', Merge='#c78750', Filter='#8d79b7', Transform='#5aa99c', Time='#97ac72', Draw='#a17abb', Keyer='#74ab68', Tracking='#c79569', Utilities='#6c7888')
CATEGORY_COLORS['3D']='#709bc0'
