import collections
import pprint
import re
import sys

import ply.lex
import ply.yacc

__all__ = ['Field', 'Repeated', 'Table', 'Inline', 'Mount', 'parse_schema']

############################################# datatype /////////////////////////////////////////////
# I like 8-letter names where possible.  Hence the lack of a space for data type.

Field = collections.namedtuple('Field', ('datatype', 'number', 'name'))
Repeated = collections.namedtuple('Repeated', ('field',))

Table = collections.namedtuple('Table', ('name', 'key', 'fields'))
Inline = collections.namedtuple('Inline', ('name',))
Mount = collections.namedtuple('Mount', ('datatype', 'name', 'number',))

############################################### lexer //////////////////////////////////////////////

reserved = {
    'table': 'TABLE',
    'reserve': 'RESERVE',
    'repeated': 'REPEATED',
    'inline': 'INLINE',
    'mount': 'MOUNT',

    'int32': 'INT32',
    'int64': 'INT64',
    'uint32': 'UINT32',
    'uint64': 'UINT64',
    'sint32': 'SINT32',
    'sint64': 'SINT64',
    'Bool': 'BOOL',
    'fixed32': 'FIXED32',
    'fixed64': 'FIXED64',
    'sfixed32': 'SFIXED32',
    'sfixed64': 'SFIXED64',
    'float': 'FLOAT',
    'double': 'DOUBLE',
    'bytes': 'BYTES',
    'string': 'STRING',
}

tokens = (
    'COMMA',
    'EQUALS',
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'SEMICOLON',
    'COMMENT',
    'NUMBER',
    'ATOM',
) + tuple(reserved.values())

t_ignore = " \t"

t_COMMA = ','
t_EQUALS = '='
t_LPAREN = '\\('
t_RPAREN = '\\)'
t_LBRACE = '{'
t_RBRACE = '}'
t_SEMICOLON = ';'

def t_COMMENT(t):
    r'\#.*'
    pass

def t_NUMBER(t):
    r'[1-9][0-9]*'
    t.value = int(t.value)
    return t

def t_ATOM(t):
    r'[a-zA-Z_][-a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ATOM')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)
    raise RuntimeError("get me out of here")

############################################## parser //////////////////////////////////////////////

def p_definitions(t):
    '''definitions : empty
                   | definition definitions
    '''
    if len(t) == 2:
        t[0] = []
    elif len(t) == 3:
        t[0] = [t[1]] + t[2]
    else:
        assert 'Unhandled case.'

def p_empty(t):
    '''empty :
             | COMMENT
    '''

def p_definition(t):
    '''definition : table
    '''
    # NOTE(rescrv):  If you extend a definition to be more than a table, look out.
    t[0] = t[1]

def p_table(t):
    '''table : TABLE ATOM LPAREN atom_list RPAREN LBRACE table_body RBRACE
    '''
    name = t[2]
    key = t[4]
    fields = t[7]
    t[0] = Table(name=name, key=key, fields=fields)

def p_table_body_base(t):
    '''table_body : table_decl SEMICOLON
    '''
    t[0] = (t[1],)

def p_table_body_list(t):
    '''table_body : table_decl SEMICOLON table_body
    '''
    t[0] = (t[1],) + t[3]

def p_table_decl(t):
    '''table_decl : field
                  | reservation
                  | inline
                  | mount
    '''
    t[0] = t[1]

def p_table_field(t):
    '''field : datatype ATOM EQUALS NUMBER
    '''
    t[0] = Field(datatype=t[1], number=t[4], name=t[2])

def p_table_reserve(t):
    '''reservation : RESERVE NUMBER
    '''

def p_table_inline(t):
    '''inline : INLINE ATOM
    '''
    t[0] = Inline(name=t[2])

def p_table_mount(t):
    '''mount : MOUNT ATOM ATOM EQUALS NUMBER
    '''
    t[0] = Mount(datatype=t[2], name=t[3], number=t[5])

def p_datatype(t):
    '''datatype : REPEATED datatype
    '''
    t[0] = Repeated(t[2])

def p_datatype_terminal(t):
    '''datatype : INT32
                | INT64
                | UINT32
                | UINT64
                | SINT32
                | SINT64
                | BOOL
                | FIXED32
                | FIXED64
                | SFIXED32
                | SFIXED64
                | FLOAT
                | DOUBLE
                | BYTES
                | STRING
    '''
    t[0] = t[1]

def p_atom_list(t):
    '''atom_list : ATOM
                 | ATOM COMMA atom_list
    '''
    if len(t) == 2:
        t[0] = (t[1],)
    elif len(t) == 4:
        t[0] = (t[1],) + t[3]
    else:
        assert 'Unhandled case.'

def p_error(t):
    if t is not None:
        sys.stderr.write("Syntax error at '%s' on line %d.\n" % (t.value, t.lexer.lineno))
    else:
        sys.stderr.write("Syntax error.\n")
    raise RuntimeError("get me out of here")

############################################### misc ///////////////////////////////////////////////

def parse_schema(contents):
    lexer = ply.lex.lex(reflags=re.UNICODE)
    lexer.lineno = 1
    parser = ply.yacc.yacc(debug=0, write_tables=0)
    return parser.parse(contents, lexer=lexer)
