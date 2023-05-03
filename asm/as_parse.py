from sly import Parser
import as_lex as lx
import as_stmt as stmt
import as_expr as expr


class Program:
    def __init__(self):
        self.instructions = []

    def add(self, instruction):
        self.instructions.append(instruction)
        self.instructions.append(None)


class AsParser(Parser):
    def __init__(self, program):
        self.prg = program
        self.lineno = 0

    # debugfile = 'parser.out'

    tokens = lx.AsLexer.tokens
    precedence = (
        ('left', "+", "-"),
        ('left', "*", DIV),
        ('right', UMINUS)
        )

    @_('statements statement')
    def statements(self, p):
        pass

    @_('statement')
    def statements(self, p):
        pass

    @_('SEPARATOR')
    def statement(self, p):
        pass

    @_('statement_type SEPARATOR')
    def statement(self, p):
        self.prg.add(p.statement_type)

    @_('labels statement_type SEPARATOR')
    def statement(self, p):
        self.prg.add(p.labels)
        self.prg.add(p.statement_type)

    @_('labels SEPARATOR')
    def statement(self, p):
        self.prg.add(p.labels)

    @_('labels label')
    def labels(self, p):
        return p.labels

    @_('label')
    def labels(self, p):
        return stmt.LabelStmt(self.lineno, p.label)

    @_('NAME_LABEL', 'NUM_LABEL')
    def label(self, p):
        self.lineno = p.lineno
        return p[0]

    @_('expression')
    def statement_type(self, p):
        return stmt.ExpressionStmt(self.lineno, p.expression)

    @_('assignment_statement')
    def statement_type(self, p):
        return p.assignment_statement

    @_('string_statement')
    def statement_type(self, p):
        return p.string_statement

    @_('keyword_statement')
    def statement_type(self, p):
        return p.keyword_statement

    @_('PSEUDO_OP_SIMPLE')
    def statement_type(self, p):
        self.lineno = p.lineno
        return stmt.PseudoOpStmt(self.lineno, p.PSEUDO_OP_SIMPLE)

    @_('PSEUDO_OP_IF expression')
    def statement_type(self, p):
        self.lineno = p.lineno
        return stmt.PseudoOpStmt(self.lineno, p.PSEUDO_OP_IF, p.expression)

    @_('PSEUDO_OP_GLOBL identifiers')
    def statement_type(self, p):
        self.lineno = p.lineno
        return stmt.PseudoOpStmt(self.lineno, p.PSEUDO_OP_GLOBL, p.identifiers)

    @_('PSEUDO_OP_COMM ID "," expression')
    def statement_type(self, p):
        self.lineno = p.lineno
        return stmt.PseudoOpStmt(self.lineno, p.PSEUDO_OP_COMM, [p.ID, p.expression])

    @_('PSEUDO_OP_BYTE pseudo_op_expressions')
    def statement_type(self, p):
        self.lineno = p.lineno
        return stmt.PseudoOpStmt(self.lineno, p.PSEUDO_OP_BYTE, p.pseudo_op_expressions)

    @_('CONST_DCHAR')
    def statement_type(self, p):
        self.lineno = p.lineno
        return stmt.ConstStmt(self.lineno, p.CONST_DCHAR)

    @_('pseudo_op_expressions pseudo_op_expression')
    def pseudo_op_expressions(self, p):
        p.pseudo_op_expressions.append(p.pseudo_op_expression)
        return p.pseudo_op_expressions

    @_('pseudo_op_expression')
    def pseudo_op_expressions(self, p):
        return [p.pseudo_op_expression]

    @_('expression %prec UMINUS', '"," expression %prec UMINUS')
    def pseudo_op_expression(self, p):
        return p.expression

    @_('identifiers identifier')
    def identifiers(self, p):
        pass

    @_('identifier')
    def identifiers(self, p):
        return p.identifier

    @_('ID')
    def identifier(self, p):
        self.lineno = p.lineno
        return p.ID

    @_('identifier_assignment_statement')
    def assignment_statement(self, p):
        return p.identifier_assignment_statement

    @_('expression_operand')
    def expression(self, p):
        return expr.Expression(p.expression_operand)

    @_('"!" expression_operand')
    def expression(self, p):
        return expr.UnaryExpression("!", p.expression_operand)

    @_('"-" expression_operand %prec UMINUS')
    def expression(self, p):
        return expr.UnaryExpression("-", p.expression_operand)

    @_('double_op_expression')
    def expression(self, p):
        return p.double_op_expression

    @_('bracket_expression')
    def expression(self, p):
        return p.bracket_expression

    @_('expression expression_operator expression %prec UMINUS')
    def double_op_expression(self, p):
        return expr.BinaryExpression(p.expression_operator, p.expression0, p.expression1)

    @_('ID', 'CONST_CHAR', 'CONST_CHAR_META', 'TEMP_SYM', 'LOCATION_OP %prec UMINUS', 'RELOCATION_OP')
    def expression_operand(self, p):
        self.lineno = p.lineno
        return p[0]

    @_('CONST_DEC')
    def expression_operand(self, p):
        self.lineno = p.lineno
        return p.CONST_DEC

    @_('CONST_OCT')
    def expression_operand(self, p):
        self.lineno = p.lineno
        return p.CONST_OCT

    @_('"+"', '"-"', '"*"', 'DIV', '"&"', '"|"', 'SHIFT_R', 'SHIFT_L', '"%"', '"^"')
    def expression_operator(self, p):
        self.lineno = p.lineno
        return p[0]

    @_('SIMPLE_KEYWORD')
    def keyword_statement(self, p):
        self.lineno = p.lineno
        return stmt.KeywordStmt(self.lineno, p.SIMPLE_KEYWORD)

    # Messy below for SINGLE_OP and DOUBLE_OP keyword.
    # A valid instruction can be, for example: clr a, or: mov a, r0
    # 'a' in these cases are parsed as an expression, however, in the context of keyword statements it should be
    # understood as relative addressing. Thus, when executing mov a, r0 (and a is a named label as an example), it is
    # not the location of label a that should be moved into r0, but the value at the location of a. If a is located at
    # 1234, we should read the value at memory location 1234 and move that to register r0. This is done in class
    # AddrIndex (which also handles the cases of mov X(r1), r0 which is moving the value at location X+r1 to r0).
    # But, the statement mov a, r0 is parsed as: mov expression, register. Therefore, we detect if one of the
    # operands is of type "Expression" and replace this with an "AddrIndex"-object instead.
    # Trying to parse it directly as an AddrIndex (see production below) will create a reduce/reduce conflict,
    # so this is a workaround.
    # End of mess...

    @_('BRANCH_KEYWORD expression', 'EXT_BRANCH_KEYWORD expression')
    def keyword_statement(self, p):
        self.lineno = p.lineno
        if p.expression.type() == "Expression":
            op = expr.AddrIndex(None, p.expression)
        elif p.expression.type() == "BinaryExpression":
            op = expr.AddrIndex(None, p.expression)
        else:
            op = p.expression

        return stmt.KeywordStmt(self.lineno, p[0], op)

    @_('SINGLE_OP_KEYWORD operand')
    def keyword_statement(self, p):
        self.lineno = p.lineno

        if p.operand.type() == "Expression":
            op = expr.AddrIndex(None, p.operand)
        elif p.operand.type() == "BinaryExpression":
            op = expr.AddrIndex(None, p.operand)
        else:
            op = p.operand

        return stmt.KeywordStmt(self.lineno, p.SINGLE_OP_KEYWORD, op)

    @_('DOUBLE_OP_KEYWORD operand "," operand')
    def keyword_statement(self, p):
        self.lineno = p.lineno

        if p.operand0.type() == "Expression":
            op0 = expr.AddrIndex(None, p.operand0)
        elif p.operand0.type() == "BinaryExpression":
            op0 = expr.AddrIndex(None, p.operand0)
        else:
            op0 = p.operand0

        if p.operand1.type() == "Expression":
            op1 = expr.AddrIndex(None, p.operand1)
        elif p.operand1.type() == "BinaryExpression":
            op1 = expr.AddrIndex(None, p.operand1)
        else:
            op1 = p.operand1

        return stmt.KeywordStmt(self.lineno, p.DOUBLE_OP_KEYWORD, op0, op1)

    @_('misc_instr')
    def keyword_statement(self, p):
        return p.misc_instr

    @_('fp_instr')
    def keyword_statement(self, p):
        return p.fp_instr

    @_('syscall')
    def keyword_statement(self, p):
        return p.syscall

    @_('misc_single_op_instr', 'misc_double_op_instr')
    def misc_instr(self, p):
        return p[0]

    @_('MISC_SINGLE_OP_KEYWORD operand')
    def misc_single_op_instr(self, p):
        self.lineno = p.lineno
        if p.operand.type() == "Expression":
            op = expr.AddrIndex(None, p.operand)
        elif p.operand.type() == "BinaryExpression":
            op = expr.AddrIndex(None, p.operand)
        else:
            op = p.operand
        return stmt.KeywordStmt(self.lineno, p.MISC_SINGLE_OP_KEYWORD, op)

    @_('MISC_DOUBLE_OP_KEYWORD operand "," operand')
    def misc_double_op_instr(self, p):
        self.lineno = p.lineno
        if p.operand0.type() == "Expression":
            op0 = expr.AddrIndex(None, p.operand0)
        elif p.operand0.type() == "BinaryExpression":
            op0 = expr.AddrIndex(None, p.operand0)
        else:
            op0 = p.operand0

        if p.operand1.type() == "Expression":
            op1 = expr.AddrIndex(None, p.operand1)
        elif p.operand1.type() == "BinaryExpression":
            op1 = expr.AddrIndex(None, p.operand1)
        else:
            op1 = p.operand1

        return stmt.KeywordStmt(self.lineno, p.MISC_DOUBLE_OP_KEYWORD, op0, op1)

    @_('FP_SIMPLE_KEYWORD')
    def fp_instr(self, p):
        self.lineno = p.lineno
        return stmt.KeywordStmt(self.lineno, p.FP_SIMPLE_KEYWORD)

    @_('fp_single_op_instr')
    def fp_instr(self, p):
        return p.fp_single_op_instr

    @_('fp_double_op_instr')
    def fp_instr(self, p):
        return p.fp_double_op_instr

    @_('FP_SINGLE_OP_KEYWORD operand')
    def fp_single_op_instr(self, p):
        self.lineno = p.lineno
        if p.operand.type() == "Expression":
            op = expr.AddrIndex(None, p.operand)
        elif p.operand.type() == "BinaryExpression":
            op = expr.AddrIndex(None, p.operand)
        else:
            op = p.operand
        return stmt.KeywordStmt(self.lineno, p.FP_SINGLE_OP_KEYWORD, op)

    @_('FP_DOUBLE_OP_KEYWORD operand "," operand')
    def fp_double_op_instr(self, p):
        self.lineno = p.lineno
        if p.operand0.type() == "Expression":
            op0 = expr.AddrIndex(None, p.operand0)
        elif p.operand0.type() == "BinaryExpression":
            op0 = expr.AddrIndex(None, p.operand0)
        else:
            op0 = p.operand0

        if p.operand1.type() == "Expression":
            op1 = expr.AddrIndex(None, p.operand1)
        elif p.operand1.type() == "BinaryExpression":
            op1 = expr.AddrIndex(None, p.operand1)
        else:
            op1 = p.operand1

        return stmt.KeywordStmt(self.lineno, p.FP_DOUBLE_OP_KEYWORD, op0, op1)

    @_('SYSCALL ID')
    def syscall(self, p):
        self.lineno = p.lineno
        return stmt.SyscallStmt(self.lineno, p.ID)

    @_('SYSCALL SYSCALL_SERVICE')
    def syscall(self, p):
        self.lineno = p.lineno
        return stmt.SyscallStmt(self.lineno, p.SYSCALL_SERVICE)

    @_('STR')
    def string_statement(self, p):
        self.lineno = p.lineno
        return stmt.StringStmt(self.lineno, p.STR)

    @_('operand "=" expression %prec UMINUS',)
    def identifier_assignment_statement(self, p):
        self.lineno = p.lineno
        return stmt.AssignmentStmt(self.lineno, p.operand, p.expression)

    @_('"[" expression "]"')
    def bracket_expression(self, p):
        return p.expression

    @_('expression %prec UMINUS', 'address')
    def operand(self, p):
        return p[0]

    @_('TEMP_SYM RELOCATION_OP', 'TEMP_SYM ID')
    def operand(self, p):
        self.lineno = p.lineno
        return expr.TempSymExpression(p.TEMP_SYM, p[1])

    @_('direct_addressing', 'indirect_addressing', 'immediate_addressing')
    def address(self, p):
        return p[0]

    @_('register')
    def direct_addressing(self, p):
        return expr.AddrRegister(p[0])

    @_('autoincrement_address', 'autodecrement_address', 'index_address')
    def direct_addressing(self, p):
        return p[0]

    @_('"(" register ")" "+"')
    def autoincrement_address(self, p):
        return expr.AddrAutoIncrement(p.register)

    @_('"-" "(" register ")"')
    def autodecrement_address(self, p):
        return expr.AddrAutoDecrement(p.register)

    @_('expression "(" register ")"')
    def index_address(self, p):
        return expr.AddrIndex(p.register, p.expression)

    @_('register_deferred', 'autoincrement_deferred', 'autodecrement_deferred', 'index_deferred')
    def indirect_addressing(self, p):
        return p[0]

    @_('"*" register', '"(" register ")"')
    def register_deferred(self, p):
        return expr.AddrRegisterDeferred(p.register)

    @_('"*" "(" register ")" "+"')
    def autoincrement_deferred(self, p):
        return expr.AddrAutoIncrementDeferred(p.register)

    @_('"*" "-" "(" register ")"')
    def autodecrement_deferred(self, p):
        return expr.AddrAutoDecrementDeferred(p.register)

    @_('"*" "(" register ")"')
    def index_deferred(self, p):
        return expr.AddrIndexDeferred(p.register, None)

    @_('"*" expression "(" register ")"')
    def index_deferred(self, p):
        return expr.AddrIndexDeferred(p.register, p.expression)

    @_('immediate', 'relative_deferred', 'absolute')
    def immediate_addressing(self, p):
        return p[0]

    @_('"$" expression')
    def immediate(self, p):
        return expr.AddrImmediate(p.expression)

    @_('"*" expression')
    def relative_deferred(self, p):
        return expr.AddrRelativeDeferred(p.expression)

    @_('"*" "$" expression')
    def absolute(self, p):
        return expr.AddrAbsolute(p.expression)

    @_('REG_KEYWORD', 'FP_REG_KEYWORD')
    def register(self, p):
        self.lineno = p.lineno
        return p[0]


def parse(instruction):
    lexer = lx.AsLexer()
    parser = AsParser(Program())

    parser.parse(lexer.tokenize(instruction))
    
    return parser.prg


if __name__ == '__main__':
    files = ['as11.s', 'as12.s', 'as13.s', 'as14.s', 'as15.s', 'as16.s', 'as17.s', 'as18.s', 'as19.s',
             'as21.s', 'as22.s', 'as23.s', 'as24.s', 'as25.s', 'as26.s', 'as27.s', 'as28.s', 'as29.s']
    for file in files:
        with open(file, 'r') as f:
            print("Parsing {} ".format(file), end='')
            prg = parse(f.read())
            for instr in prg.instructions:
                print("{} {}".format(type(instr).__name__, instr))
