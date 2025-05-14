from flask import Flask, request, render_template, jsonify
import ply.lex as lex
import ply.yacc as yacc

# Analizador Descendente Recursivo

NUMBER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF = (
    'NUMBER', 'PLUS', 'MINUS', 'MUL', 'DIV', 'LPAREN', 'RPAREN', 'EOF'
)

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f'Token({self.type}, {self.value})'

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ''
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(NUMBER, self.number())

            if self.current_char == '+':
                self.advance()
                return Token(PLUS)

            if self.current_char == '-':
                self.advance()
                return Token(MINUS)

            if self.current_char == '*':
                self.advance()
                return Token(MUL)

            if self.current_char == '/':
                self.advance()
                return Token(DIV)

            if self.current_char == '(':
                self.advance()
                return Token(LPAREN)

            if self.current_char == ')':
                self.advance()
                return Token(RPAREN)

            raise Exception(f'Carácter inválido: {self.current_char}')

        return Token(EOF)

class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f'({self.left} {self.op.type} {self.right})'

class Num:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)

class ParserDescendente:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise Exception(f'Error de sintaxis: esperado {token_type}, encontrado {self.current_token.type}')

    def factor(self):
        token = self.current_token
        if token.type == NUMBER:
            self.eat(NUMBER)
            return Num(token.value)
        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node
        else:
            raise Exception(f'Error de sintaxis en factor: token inesperado {token.type}')

    def term(self):
        node = self.factor()
        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)
            node = BinOp(left=node, op=token, right=self.term())
        return node

    def parse(self):
        return self.expr()

def eval_ast(node):
    if isinstance(node, Num):
        return node.value
    elif isinstance(node, BinOp):
        left_val = eval_ast(node.left)
        right_val = eval_ast(node.right)
        op = node.op.type
        if op == PLUS:
            return left_val + right_val
        elif op == MINUS:
            return left_val - right_val
        elif op == MUL:
            return left_val * right_val
        elif op == DIV:
            if right_val == 0:
                raise Exception("Error: División por cero")
            return left_val / right_val
    else:
        raise Exception("Nodo inválido")

def recursive_parser(text):
    try:
        lexer = Lexer(text)
        parser = ParserDescendente(lexer)
        ast = parser.parse()
        resultado = eval_ast(ast)
        return resultado
    except Exception as e:
        return f"Error en parser descendente: {str(e)}"

# Analizador con PLY (Python Lex-Yacc)

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
    ast_result = None
    eval_result = None
    if request.method == 'POST':
        expression = request.form.get('expression', '')
        if expression:
            try:
                lexer = Lexer(expression)
                parser = ParserDescendente(lexer)
                ast = parser.parse()
                ast_result = repr(ast)
                eval_result = eval_ast(ast)
            except Exception as e:
                ast_result = f"Error: {e}"
                eval_result = None
    return render_template('analizador_descendente.html', expression=expression, ast_result=ast_result, eval_result=eval_result)

if __name__ == '__main__':
    app.run(debug=True)