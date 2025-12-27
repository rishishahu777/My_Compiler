from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

# ==========================
# LEXER
# ==========================
TOKEN_SPEC = [
    ('NUMBER',  r'\d+'),
    ('LET',     r'maanlo'),
    ('PRINT',   r'batao'),
    ('ID',      r'[a-zA-Z_]\w*'),
    ('PLUS',    r'\+'),
    ('MINUS',   r'-'),
    ('MULT',    r'\*'),
    ('DIV',     r'/'),
    ('EQUAL',   r'='),
    ('NEWLINE', r'\n'),
    ('SKIP',    r'[ \t]+'),
]

def tokenize(code):
    tokens = []
    pos = 0

    while pos < len(code):
        match = None
        for tok_type, pattern in TOKEN_SPEC:
            regex = re.compile(pattern)
            match = regex.match(code, pos)
            if match:
                text = match.group(0)
                if tok_type not in ('SKIP', 'NEWLINE'):
                    tokens.append((tok_type, text))
                pos = match.end()
                break

        if not match:
            raise SyntaxError(f"Illegal character: {code[pos]}")

    return tokens


# ==========================
# AST NODES
# ==========================
class Let:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class Print:
    def __init__(self, expr):
        self.expr = expr


# ==========================
# PARSER
# ==========================
def parse_expression(tokens, i):
    expr = []
    while i < len(tokens) and tokens[i][0] not in ('LET', 'PRINT'):
        if tokens[i][0] in ('NUMBER', 'ID', 'PLUS', 'MINUS', 'MULT', 'DIV'):
            expr.append(tokens[i])
            i += 1
        else:
            break
    return expr, i


def parse(tokens):
    ast = []
    i = 0

    while i < len(tokens):
        if tokens[i][0] == 'LET':
            name = tokens[i + 1][1]
            i += 3
            expr, i = parse_expression(tokens, i)
            ast.append(Let(name, expr))

        elif tokens[i][0] == 'PRINT':
            i += 1
            expr, i = parse_expression(tokens, i)
            ast.append(Print(expr))

        else:
            raise SyntaxError(f"Unexpected token {tokens[i]}")

    return ast


# ==========================
# BYTECODE GENERATOR
# ==========================
def generate(ast):
    bytecode = []

    for node in ast:
        if isinstance(node, Let):
            operators = []
            for token in node.expr:
                if token[0] == 'NUMBER':
                    bytecode.append(('LOAD_CONST', int(token[1])))
                elif token[0] == 'ID':
                    bytecode.append(('LOAD', token[1]))
                elif token[0] == 'PLUS':
                    operators.append('ADD')
                elif token[0] == 'MINUS':
                    operators.append('SUB')
                elif token[0] == 'MULT':
                    operators.append('MUL')
                elif token[0] == 'DIV':
                    operators.append('DIV')

            for op in operators:
                bytecode.append((op,))

            bytecode.append(('STORE', node.name))

        elif isinstance(node, Print):
            operators = []
            for token in node.expr:
                if token[0] == 'NUMBER':
                    bytecode.append(('LOAD_CONST', int(token[1])))
                elif token[0] == 'ID':
                    bytecode.append(('LOAD', token[1]))
                elif token[0] == 'PLUS':
                    operators.append('ADD')
                elif token[0] == 'MINUS':
                    operators.append('SUB')
                elif token[0] == 'MULT':
                    operators.append('MUL')
                elif token[0] == 'DIV':
                    operators.append('DIV')

            for op in operators:
                bytecode.append((op,))

            bytecode.append(('PRINT',))

    return bytecode


# ==========================
# VIRTUAL MACHINE
# ==========================
def run(bytecode):
    stack = []
    memory = {}
    output = []

    for instr in bytecode:
        op = instr[0]

        if op == 'LOAD_CONST':
            stack.append(instr[1])

        elif op == 'LOAD':
            if instr[1] not in memory:
                raise NameError(f"Variable '{instr[1]}' not defined")
            stack.append(memory[instr[1]])

        elif op == 'ADD':
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)

        elif op == 'SUB':
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        elif op == 'MUL':
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        elif op == 'DIV':
            b = stack.pop()
            a = stack.pop()
            stack.append(a // b)

        elif op == 'STORE':
            memory[instr[1]] = stack.pop()

        elif op == 'PRINT':
            output.append(str(stack.pop()))

    return output


# ==========================
# FLASK ROUTES
# ==========================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/execute', methods=['POST'])
def execute():
    try:
        code = request.json.get('code', '')
        
        tokens = tokenize(code)
        ast = parse(tokens)
        bytecode = generate(ast)
        output = run(bytecode)
        
        return jsonify({
            'success': True,
            'output': '\n'.join(output)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    app.run(debug=True)