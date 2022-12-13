from ply import lex


arithmetical = [
    'PLUS',
    'MINUS',
    'MUL',
    'DIV',
    'POW'
]

logical = [
    'EQUALS',
    'DIFF',
    'GREATER',
    'LOWER',
    'GREATEQ',
    'LOWEQ',
]

reserved = ['IF', 'THEN', 'END', 'ELSE', 'WHILE', 'TO', "AND", "OR"]

tokens = [
    'RETURN_NUMBER', 'NUMBER', 'IDENTIFIER', 'COLON_ID', 'ASSIGN', 'OPEN_PAR', 'CLOSE_PAR'
] + logical + reserved + arithmetical

t_EQUALS = '=='
t_DIFF = '<>'
t_GREATER = '>'
t_LOWER = '<'
t_GREATEQ = '>='
t_LOWEQ = '<='
t_ASSIGN = '='
t_PLUS = '\+'
t_MINUS = '-'
t_MUL = '\*'
t_DIV = '/'
t_POW = '\^'
t_OPEN_PAR = '\('
t_CLOSE_PAR = '\)'

t_ignore  = ' \t'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_IDENTIFIER(t):
    r'[_a-zA-Z][_a-zA-Z0-9]*'

    if t.value == 'RANDOM' or t.value == 'TYPEIN':
        t.type = 'RETURN_NUMBER'
        return t
    
    if t.value in (reserved or logical):
        t.type = t.value
    else:
        t.type = 'IDENTIFIER'
    return t

def t_COLON_ID(t):
    r':[_a-zA-Z][_a-zA-Z0-9]*'
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def lexer():
    """Create a new lexer object."""
    return lex.lex()