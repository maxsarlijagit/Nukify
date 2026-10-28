# SPDX-License-Identifier: GPL-3.0-or-later
from model import blank,new_node,demo


def example(name,assets):
    if name=='Composicion':return demo(assets)
    g=blank();g.update(width=320,height=240,last=24)
    def add(kind,x,y,params=None,inputs=None):
        n=new_node(g,kind,x,y);n['params'].update(params or {});n['inputs']=inputs or {};return n['id']
    if name=='Curvas y roto':
        from animation import set_key
        bg=add('Constant',-160,-180,{'r':.05,'g':.08,'b':.12})
        mask=add('Roto',180,-180,{'points':[[.35,.3],[.55,.3],[.55,.7],[.35,.7]],'shape_group':'Objeto','groups':[{'id':'Objeto','rotation':15}],'motion_samples':8,'shutter':.5})
        node=g['nodes'][-1];set_key(node,'shape_x',1,-60,'bezier');set_key(node,'shape_x',24,60,'bezier')
        node['expressions']={'shape_y':'15 * sin(frame * pi / 12)'}
        fg=add('Constant',0,-180,{'r':1.,'g':.45,'b':.08})
        result=add('Merge',0,40,inputs={'A':fg,'B':bg,'Mask':mask})
        add('Write',0,200,inputs={'Image':result});g['viewer']=result;g['viewer_b']=mask
        return g
    if name=='Integracion 3D':
        bg=add('Read',-340,100,{'path':str(assets/'production/plate_####.png')})
        camera=add('Camera',260,-240)
        cube=add('Geometry',-180,-240,{'scale':.65})
        g['nodes'][-1]['animation']={'ry':{'interpolation':'linear','keys':[[1,0],[24,90]]}}
        light=add('Light',40,-240)
        scene=add('Scene',-100,-90,inputs={'Object':cube,'Light':light})
        render=add('RenderLayers',100,70,inputs={'Scene':scene,'Camera':camera})
        merge=add('Merge',100,220,inputs={'A':render,'B':bg})
        add('Write',100,360,inputs={'Image':merge});g['viewer']=merge;g['viewer_b']=render
        return g
    if name=='EXR y Cryptomatte':
        g.update(width=64,height=64,last=1)
        path=str(assets/'production/crypto.exr')
        read=add('Read',-180,-220,{'path':path,'layer':'ViewLayer.Combined'})
        mask=add('Cryptomatte',120,-220,{'path':path,'layer':'ViewLayer.CryptoObject','matte_id':'Cube'})
        write=add('Write',120,-20,{'preserve_exr':path,'output_layer':'Nukify.Matte'},{'Image':mask})
        g['viewer']=mask;return g
    plate=str(assets/'production/plate_####.png');insert=str(assets/'production/insert.png')
    bg=add('Read',-180,-220,{'path':plate})
    if name=='Chroma y roto':
        fg=add('Read',100,-220,{'path':str(assets/'production/chroma_####.png')})
        key=add('ChromaKey',100,-100,{'r':.007,'g':.515,'b':.009}, {'Image':fg})
        roto=add('Roto',340,-100,{'points':[[.2,.15],[.85,.15],[.85,.9],[.2,.9]],'feather':2.})
        result=add('Merge',100,60,inputs={'A':key,'B':bg,'Mask':roto})
    else:
        fg=add('Read',100,-220,{'path':insert})
        kind='PlanarTracker' if name=='Planar' else 'Tracker2D'
        params={'tracking_path':plate,'reference':1}
        if kind=='Tracker2D':params['tracks']=[[.4,.4],[.65,.65]]
        track=add(kind,100,-90,params,{'Image':fg})
        result=add('Merge',100,80,inputs={'A':track,'B':bg})
    add('Write',100,210,inputs={'Image':result});g['viewer']=result
    return g
