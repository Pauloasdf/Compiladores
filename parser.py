from ply import yacc
from lexer import lexer, tokens
from symtable import add_symbol, set_symbol, get_symbol, get_symbols_by_class

import time
import sys


precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MUL', 'DIV'),
    ('left', 'POW'),
    ('left', 'OPEN_PAR')
)


def p_program(p):
    ''' program : statement other_statement'''
    statements = [p[1]]
    if p[2]:
        statements.extend(p[2])
    p[0] = statements


def p_other_statement(p):
    ''' other_statement : statement other_statement
        | empty
    '''
    if p[1]:
        statements = [p[1]]
        if p[2]:
            statements.extend(p[2])
        p[0] = statements

    
def p_statement(p):
    ''' statement : value_expression 
        | assign_expression 
        | declaration_expression
        | procedure_call
        | bool_expression
        | while_statement
        | if_statement
    '''
    p[0] = p[1]


def p_value_expression(p):
    ''' value_expression : NUMBER 
        | COLON_ID
        | RETURN_NUMBER
    '''
    if p[1] == 'RANDOM':
        p[0] = 'RAND'
        return
    elif p[1] == 'TYPEIN':
        p[0] = 'CALL READ'
        return

    if isinstance(p[1], str):
        if ':' in p[1]:
            colon_id = p[1].replace(':', '')
            symbol = get_symbol(colon_id)
            if symbol is None:
                add_symbol(colon_id, 'VAR')
            p[0] = f'LOAD {colon_id}'
        else:
            p[0] = get_symbol(p[1])['code']
    else:
        p[0] = f'PUSH {float(p[1])}'


def p_value_expression_list(p):
    ''' value_expression_list : value_expression value_expression_list
        | empty 
    '''
    if p[1]:
        if ':' in p[1]:
            value_expressions = ['LOAD ' + p[1].replace(':', '')]
            if p[2]:
                value_expressions.extend(p[2])
            p[0] = value_expressions
        else:
            value_expressions = [p[1]]
            if p[2]:
                value_expressions.extend(p[2])
            p[0] = value_expressions


def p_parentheses(prod):
    ''' value_expression : OPEN_PAR value_expression CLOSE_PAR '''
    prod[0] = prod[2]


def p_arithmetic_expression(p):
    ''' value_expression : value_expression PLUS value_expression 
        | value_expression MINUS value_expression 
        | value_expression MUL value_expression 
        | value_expression DIV value_expression
        | value_expression POW value_expression
    '''
    oper = {
        '+': 'ADD',
        '-': 'SUB',
        '*': 'MUL',
        '/': 'DIV',
        '^': 'POW'
    }
    p[0] = f'{p[1]}\n'
    p[0] += f'{p[3]}\n'
    p[0] += oper[p[2]]


def p_assign_expression(p):
    ''' assign_expression : IDENTIFIER ASSIGN value_expression '''
    if get_symbol(p[1]) is None:
        add_symbol(p[1], 'VAR')
    set_symbol(p[1], value=p[3].split(' ')[1])
    p[0] = f'{p[3]}\n'
    p[0] += f'STOR {p[1]}'


def p_declaration_expression(p):
    ''' declaration_expression : TO IDENTIFIER argument_list other_statement END '''
    add_symbol(p[2], 'CUSTOM_FUNC')

    function_code = f'DEF {p[2]}:\n'

    if p[3]:
        function_code += '\n'.join(p[3]) + '\n'

    function_code += '\n'.join(p[4]) + '\n'
    function_code += 'RET'

    set_symbol(p[2], code=function_code)
    

def p_argument_list(p):
    ''' argument_list : COLON_ID argument_list
        | empty 
    '''
    if p[1]:
        arguments = ['STOR ' + p[1].replace(':', '')]
        if p[2]:
            arguments.extend(p[2])
        p[0] = arguments


def p_procedure_call(p):
    ''' procedure_call : IDENTIFIER value_expression_list '''
    p[0] = ''
    symbol = get_symbol(p[1])
    if symbol is not None:
        try:
            p[0] = symbol['code_before']
        except:
            pass
    
    if p[2]:
        p[0] += '\n'.join(p[2]) + '\n'

    if symbol is not None and symbol['type'] == 'FUNC':
        p[0] += '\n'.join({symbol["code"]})
    else:
        p[0] += f'CALL {p[1]}'


def p_bool_expression(p):
    ''' bool_expression : value_expression EQUALS value_expression
        | value_expression DIFF value_expression
        | value_expression GREATER value_expression
        | value_expression GREATEQ value_expression
        | value_expression LOWER value_expression
        | value_expression LOWEQ value_expression
    '''
    jumps = {
        '==': {
            'true': 'JZ',
            'false': 'JNZ'
        },
        '<>': {
            'true': 'JNZ',
            'false': 'JZ'
        },
        '>': {
            'true': 'JMORE',
            'false': 'JLESS'
        },
        '<': {
            'true': 'JLESS',
            'false': 'JMORE'
        },
        '>=': {
            'true': 'JMORE',
            'false': 'JLESS'
        },
        '<=': {
            'true': 'JLESS',
            'false': 'JMORE'
        }
    }
    p[0] = f'{p[1]}\n'
    p[0] += f'CMP {p[3].replace("PUSH ", "")}\n'
    transpiled_boolean_expression = [p[0]]
    transpiled_boolean_expression.append(jumps[p[2]])

    p[0] = transpiled_boolean_expression


def p_bool_expression_list(p):
    ''' bool_expression : bool_expression AND bool_expression 
        | bool_expression OR bool_expression 
    '''
    p[0] = p[1] + p[3]


def p_while_statement(p):
    ''' while_statement : WHILE OPEN_PAR bool_expression CLOSE_PAR other_statement END '''
    label_identifier = time.time()
    p[0] = f':while_{label_identifier}\n'
    p[0] += p[3][0]
    p[0] += f'{p[3][1]["false"]} :after_{label_identifier}\n'
    p[0] += '\n'.join(p[5]) + '\n'
    p[0] += f'JP :while_{label_identifier}\n'
    p[0] += f':after_{label_identifier}\n'


def p_if_statement(p):
    ''' if_statement : IF OPEN_PAR bool_expression CLOSE_PAR THEN other_statement END '''
    label_identifier = time.time()
    p[0] = p[3][0]
    p[0] += f'{p[3][1]["false"]} :endif_{label_identifier}\n'
    p[0] += f'JP :true_{label_identifier}\n'
    p[0] += f':true_{label_identifier}\n'
    p[0] += '\n'.join(p[6]) + '\n'
    p[0] += f':endif_{label_identifier}\n'


def p_if_else_statement(p):
    ''' if_statement : IF OPEN_PAR bool_expression CLOSE_PAR THEN other_statement ELSE other_statement END '''
    label_identifier = time.time()
    p[0] = p[3]
    p[0] += f'JZ :true_{label_identifier}\n'
    p[0] += f'JP :false_{label_identifier}\n'
    p[0] += f':true_{label_identifier}\n'
    p[0] += '\n'.join(p[6]) + '\n'
    p[0] += f'JP :endif_{label_identifier}\n'
    p[0] += f':false_{label_identifier}\n'
    p[0] += '\n'.join(p[8]) + '\n'
    p[0] += f':endif_{label_identifier}\n'


def p_empty(p):
    '''empty :'''
    p[0] = None


def p_error(token):
    if token:
        raise Exception(
            f"Unexpected token:{token.lineno}: {token.type}:'{token.value}'"
        )

    raise Exception("Syntax error at EOF.")


if __name__ == "__main__":
    ORIGINAL_POSITION_X = '1'
    ORIGINAL_POSITION_Y = '1'

    add_symbol('PRINT', 'FUNC')
    set_symbol('PRINT', code='PUSH 1\nCALL WRITE')

    add_symbol('TYPEIN', 'FUNC')
    set_symbol('TYPEIN', code='CALL READ')
    
    add_symbol('FO', 'FUNC')
    set_symbol('FO', code='CALL MOVE', code_before='PUSH 0\n')

    add_symbol('FORWARD', 'FUNC')
    set_symbol('FORWARD', code='CALL MOVE', code_before='PUSH 0\n')

    add_symbol('LT', 'FUNC')
    set_symbol('LT', code='CALL MOVE', code_before='PUSH 90\n')

    add_symbol('LEFT', 'FUNC')
    set_symbol('LEFT', code='CALL MOVE', code_before='PUSH 90\n')

    add_symbol('BK', 'FUNC')
    set_symbol('BK', code='CALL MOVE', code_before='PUSH 180\n')

    add_symbol('BACKWARD', 'FUNC')
    set_symbol('BACKWARD', code='CALL MOVE', code_before='PUSH 180\n')

    add_symbol('RIGHT', 'FUNC')
    set_symbol('RIGHT', code='CALL MOVE', code_before='PUSH 270\n')

    add_symbol('RT', 'FUNC')
    set_symbol('RT', code='CALL MOVE', code_before='PUSH 270\n')

    add_symbol('PENUP', 'FUNC')
    set_symbol('PENUP', code='UNSET 1')

    add_symbol('PENDOWN', 'FUNC')
    set_symbol('PENDOWN', code='SET 1')

    add_symbol('PD', 'FUNC')
    set_symbol('PD', code='SET 1')

    add_symbol('WIPECLEAN', 'FUNC')
    set_symbol('WIPECLEAN', code='CLRSCR')
    
    add_symbol('WP', 'FUNC')
    set_symbol('WP', code='CLRSCR')

    add_symbol('CLEARSCREEN', 'FUNC')
    set_symbol('CLEARSCREEN', code='CLRSCR\nUNSET 1\nPUSH 50\nPUSH 50\nMVTO\nSET 1')

    add_symbol('CS', 'FUNC')
    set_symbol('CS', code='CLRSCR\nUNSET 1\nPUSH 50\nPUSH 50\nMVTO\nSET 1')

    add_symbol('HOME', 'FUNC')
    set_symbol('HOME', code=f'\nUNSET 1\nPUSH {ORIGINAL_POSITION_X}\nPUSH {ORIGINAL_POSITION_Y}\nMVTO\nSET 1')

    add_symbol('SETXY', 'FUNC')
    set_symbol('SETXY', code=f'\nUNSET 1\nMVTO\nSET 1')


    with (
        open(sys.argv[1], "rt") if len(sys.argv) > 1 else sys.stdin
    ) as source_file:
        SOURCE = "".join(source_file.readlines())

    mylex = lexer()
    parser = yacc.yacc(start="program")
    program = parser.parse(SOURCE, lexer=mylex, tracking=False)

    program_start = '.START __main__\n\n'
    program_init = f'.INIT {ORIGINAL_POSITION_X} {ORIGINAL_POSITION_Y} 100 100\n\n'
    program_data = '.DATA\n'
    program_code = '.CODE\n\n'

    program_data_declaration = ''
    for symbol in get_symbols_by_class('VAR'):
        program_data_declaration += f'{symbol} 0\n'

    program_functions_declaration = ''
    for symbol in get_symbols_by_class('CUSTOM_FUNC'):
        symbol_code = get_symbol(symbol)['code']
        program_functions_declaration += f'{symbol_code}\n'

    final_program = program_start + program_init

    if program_data_declaration != '':
        final_program += program_data + program_data_declaration + '\n'

    final_program += program_code

    final_program += 'DEF __main__:\n' + '\n'.join(str(s) for s in program)
    final_program += '\n\nHALT\n\n'

    final_program += program_functions_declaration

    final_program = final_program.replace('None', '')

    f = open("output.lasm", "w")
    f.write(final_program)
    f.close()

    print(final_program)
