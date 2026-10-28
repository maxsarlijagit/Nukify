# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded arithmetic expressions; no Python eval, attributes, imports or files."""
import ast,math,operator

FUNCTIONS={'sin':math.sin,'cos':math.cos,'abs':abs,'min':min,'max':max,'sqrt':math.sqrt,
           'clamp':lambda x,a,b:max(a,min(b,x))}
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod}

def evaluate(text,frame,value,lookup):
    if not isinstance(text,str) or len(text)>512:raise ValueError('Expresion demasiado larga')
    try:tree=ast.parse(text,mode='eval')
    except SyntaxError as exc:raise ValueError('Sintaxis de expresion invalida') from exc
    if sum(1 for _ in ast.walk(tree))>100:raise ValueError('Expresion demasiado compleja')
    def calc(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return node.value
        if isinstance(node,ast.Name) and node.id in ('frame','value','pi'):return {'frame':frame,'value':value,'pi':math.pi}[node.id]
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):return calc(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        if isinstance(node,ast.BinOp):
            a,b=calc(node.left),calc(node.right)
            if isinstance(node.op,ast.Pow):
                if abs(b)>16 or abs(a)>1e9:raise ValueError('Potencia fuera de limite')
                return a**b
            if type(node.op) in OPS:return OPS[type(node.op)](a,b)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords and len(node.args)<=8:
            if node.func.id=='ref' and len(node.args)==2 and all(isinstance(a,ast.Constant) and isinstance(a.value,str) for a in node.args):return lookup(*(a.value for a in node.args))
            if node.func.id in FUNCTIONS:return FUNCTIONS[node.func.id](*(calc(a) for a in node.args))
        raise ValueError('Operacion no permitida en expresion')
    try:result=calc(tree.body)
    except (ArithmeticError,TypeError) as exc:raise ValueError('Error numerico: '+str(exc)) from exc
    if not isinstance(result,(int,float)) or not math.isfinite(result) or abs(result)>1e9:raise ValueError('Resultado no finito o fuera de rango')
    return float(result)

def remap_refs(text,mapping):
    tree=ast.parse(text,mode='eval')
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='ref' and len(node.args)==2 and isinstance(node.args[0],ast.Constant):
            node.args[0].value=mapping.get(node.args[0].value,node.args[0].value)
    return ast.unparse(tree)
