from flask import Flask, request, render_template, jsonify
import ply.lex as lex
import ply.yacc as yacc
import ast
import operator

# Calculadora Descendente Recursivo con AST
OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

def eval_expr_ast(expr):
    node = ast.parse(expr, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in OPERADORES:
                if op_type == ast.Div and right == 0:
                    raise ZeroDivisionError("Error: División por cero")
                return OPERADORES[op_type](left, right)
            else:
                raise TypeError(f"Operador no soportado: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in OPERADORES:
                return OPERADORES[op_type](operand)
            else:
                raise TypeError(f"Operador unario no soportado: {op_type}")
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise TypeError("Solo se permiten números")
        else:
            raise TypeError(f"Nodo no soportado: {type(node)}")

    return _eval(node)
OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

OPERADORES_PALABRAS = {
    ast.Add: "plus",
    ast.Sub: "minus",
    ast.Mult: "times",
    ast.Div: "divided by",
    ast.USub: "negative",
}

def eval_expr_ast(expr):
    node = ast.parse(expr, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in OPERADORES:
                if op_type == ast.Div and right == 0:
                    raise ZeroDivisionError("Error: División por cero")
                return OPERADORES[op_type](left, right)
            else:
                raise TypeError(f"Operador no soportado: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in OPERADORES:
                return OPERADORES[op_type](operand)
            else:
                raise TypeError(f"Operador unario no soportado: {op_type}")
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise TypeError("Solo se permiten números")
        else:
            raise TypeError(f"Nodo no soportado: {type(node)}")

    return _eval(node)

def ast_to_words(node):
    if isinstance(node, ast.Expression):
        return ast_to_words(node.body)
    elif isinstance(node, ast.BinOp):
        left = ast_to_words(node.left)
        right = ast_to_words(node.right)
        op = OPERADORES_PALABRAS.get(type(node.op), '?')
        left = f"({left})" if isinstance(node.left, ast.BinOp) else left
        right = f"({right})" if isinstance(node.right, ast.BinOp) else right
        return f"{left} {op} {right}"
    elif isinstance(node, ast.UnaryOp):
        operand = ast_to_words(node.operand)
        op = OPERADORES_PALABRAS.get(type(node.op), '?')
        return f"{op} {operand}"
    elif isinstance(node, ast.Num):
        return str(node.n)
    elif isinstance(node, ast.Constant):
        return str(node.value)
    else:
        return "<?>"

# Analizador con PLY

tokens = (
    'NUMBER', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN', 'RPAREN',
)

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value)
    return t

t_ignore = ' \t'

def t_error(t):
    t.lexer.skip(1)

lexer = lex.lex()

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        if p[3] == 0:
            p[0] = 'Error: División por cero'
        else:
            p[0] = p[1] / p[3]

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = p[1]

def p_error(p):
    p[0] = "Error de sintaxis"

parser = yacc.yacc()

# Rutas

app = Flask(__name__)

@app.route('/')
def menu():
    return render_template('menu.html')

@app.route('/ply')
def ply_page():
    return render_template('analizador_ply.html')

@app.route('/eval_ply', methods=['POST'])
def eval_ply():
    expr = request.form.get('expression')
    if not expr:
        return jsonify({'result': 'No hay expresión para evaluar.'})

    result = parser.parse(expr)
    try:
        val = float(result)
        if val.is_integer():
            result = int(val)
        else:
            result = val
    except Exception:
        pass

    return jsonify({'result': str(result)})

@app.route('/recursive', methods=['GET', 'POST'])
def recursive_page():
    expression = ''
    eval_result = None
    error_msg = None
    expr_words = None

    if request.method == 'POST':
        expression = request.form.get('expression', '')
        if expression:
            try:
                node = ast.parse(expression, mode='eval')
                eval_result = eval_expr_ast(expression)
                expr_words = ast_to_words(node)
            except Exception as e:
                error_msg = str(e)

    return render_template('analizador_descendente.html',
                           expression=expression,
                           eval_result=eval_result,
                           error_msg=error_msg,
                           expr_words=expr_words)

if __name__ == '__main__':
    app.run(debug=True)