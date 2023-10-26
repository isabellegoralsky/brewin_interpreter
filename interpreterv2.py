# exports Interpreter class VERSION 2.0
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)

    def run(self, program):
        # program is a list of strs that represent a syntactically valid Brewin prog
        # ex ['func main() { ', 'first = inputi("Enter a first #: ");', …, '}']
        # each item in list is a different line

        # use parser to parse the source code into AST
        # will always start with main function
        # main fucntion will have 1+ statements inside
        # assignment and printing are statements that are OK
        ast = parse_program(program)
        self.variable_name_to_value = {} # need self???
        
        # main func node = get main func node (ast)
        # is program node guaranteed to be first???
        #prog_node = ast.get(InterpreterBase.PROGRAM_DEF)
        
        # get single node in program function list -> main()
        # only one node so name will be main
        # i dont think any args rn
        main_func_node = ast.get('functions')[0]
        if main_func_node.get('name') != 'main':
            super().error(ErrorType.NAME_ERROR,"No main() function was found",)


        #run_func(main_func_node)
        self.run_func(main_func_node)

        # process nodes of the AST to run the program
    
    def run_func(self, func_node):
        # run statements in order that they appear in the program
        # aka order of execution
        for statement_node in func_node.get('statements'):
            self.run_statement(statement_node)
            #print(statement_node)

    def run_statement(self, statement_node):
        # look inside the statement nodes and figure out how to tell what they are
        if statement_node.elem_type == "=":
            # assignment
            self.do_assignment(statement_node)
        elif statement_node.elem_type == InterpreterBase.FCALL_DEF:
            # function call
            self.do_print_fcall(statement_node)
        elif statement_node.elem_type == InterpreterBase.IF_DEF:
            # elif if statement
            self.do_if_statement(statement_node)
        elif statement_node.elem_type == InterpreterBase.WHILE_DEF:
            # elif while loop
            self.do_while_loop(statement_node)
        elif statement_node.elem_type == InterpreterBase.RETURN_DEF:
            # elif return statement
            self.do_ret_statement(statement_node)

    def do_assignment(self, statement_node):
        target_var_name = statement_node.get('name')
        # in x = 2 + 10 this is x
        source_node = statement_node.get('expression')
        #print("target ", target_var_name, "expression ", source_node)
        # either expression like 2+10, value like 2, or var like x=y
        resulting_value = self.evaluate_expression(source_node)
        #print("result ", resulting_value)
        self.variable_name_to_value[target_var_name] = resulting_value

    def do_print_fcall(self, statement_node):
        # in v1 must be a print call
        if statement_node.get('name') == 'print':
            out_str = ""
            for arg in statement_node.get('args'):
                s = str(self.evaluate_expression(arg))
                if s == "True":
                    outstr += "true"
                elif s == "False":
                    outstr += "false"
                else:
                    out_str += s
            super().output(out_str)
        else:
            super().error(ErrorType.NAME_ERROR,"print function only allowed",)
        # throw err if not
        # also its 0+ nodes
    
    def do_if_statement(self, statement_node):
        cond = self.evaluate_expression(statement_node.get('condition'))
        if not isinstance(cond, bool):
            super().error(ErrorType.TYPE_ERROR,"condition of if statement must be type bool",)
        if cond:
            for s in statement_node.get('statements'):
                self.run_statement(s)
        elif statement_node.get('else_statements') is not None:
            for s in statement_node.get('else_statements'):
                self.run_statement(s)
    
    def do_while_loop(self, statement_node):
        cond = self.evaluate_expression(statement_node.get('condition'))
        if not isinstance(cond, bool):
            super().error(ErrorType.TYPE_ERROR,"condition of while loop must be type bool",)
        while cond:
            for s in statement_node.get('statements'):
                self.run_statement(s)
    
    def do_ret_statement(self, statement_node):
        return self.evaluate_expression(statement_node.get('expression')) # does this handle none??
    
    def evaluate_expression(self, node):
        if node.elem_type in {InterpreterBase.STRING_DEF, InterpreterBase.INT_DEF,
                              InterpreterBase.BOOL_DEF, InterpreterBase.NIL_DEF}:
            # value node
            return self.get_value(node)
        elif node.elem_type == InterpreterBase.VAR_DEF:
            # variable node
            return self.get_value_of_variable(node)
        elif node.elem_type in {'+','-','*','/','<','>','<=','>=','!=', '==', '||', '&&'}:
            # expression node representing binary operation
            return self.evaluate_binary_operator(node)
        elif node.elem_type == "fcall":
            # eval it
            # SIWTCH TO HANDLE MORE THAN JUST INPUT I
            return self.do_inputi_fcall(node)
        elif node.elem_type == InterpreterBase.NEG_DEF or node.elem_type == InterpreterBase.NOT_DEF:
            # unary operation
            return self.evaluate_unary_operator(node)
            
    def do_inputi_fcall(self, statement_node):
        # in v1 must be a print call
        if statement_node.get('name') == 'inputi':
            # output the single param which is the prompt (if any)
            if len(statement_node.get('args')) == 1:
                super().output(str(self.evaluate_expression(statement_node.get('args')[0])))
            elif len(statement_node.get('args')) > 1:
                super().error(ErrorType.NAME_ERROR,"inputi function can only have 1 or 0 args",)
            
            # guarantee that the input is a valid integer in String form
            user_input = super().get_input()
            if user_input == None:
                super().error(ErrorType.FAULT_ERROR,"inputi function takes in an integer",)
            return int(user_input)
        else:
            super().error(ErrorType.NAME_ERROR,"inputi function only allowed",)
        # throw err if not
        # also its 0+ nodes
    
    # value of value node
    def get_value(self, val_node):
        if val_node.elem_type == InterpreterBase.NIL_DEF:
            return None
        elif val_node.elem_type == InterpreterBase.BOOL_DEF:
            if val_node.get('val') == 'true':
                return True
            else:
                return False
        return val_node.get('val')
    
    # value of var node
    def get_value_of_variable(self, var_node):
        if var_node.get('name') in self.variable_name_to_value:
            return self.variable_name_to_value[var_node.get('name')]
        else:
            super().error(ErrorType.NAME_ERROR, f"Variable {var_node.get('name')} has not been defined",)
    
    # binary ops, bool and arith
    def evaluate_binary_operator(self, expression_node):
        # dict holds op1 and op2
        op1 = expression_node.get('op1')
        op2 = expression_node.get('op2')

        op1 = self.evaluate_expression(op1)
        op2 = self.evaluate_expression(op2)
        
        if isinstance(op1,int) and isinstance(op2, int):
            if expression_node.elem_type == '+':
                return op1 + op2
            elif expression_node.elem_type == '-':
                return op1 - op2
            elif expression_node.elem_type == '*':
                return op1 * op2
            elif expression_node.elem_type == '/':
                return op1 // op2
            elif expression_node.elem_type == '==':
                return op1 == op2
            elif expression_node.elem_type == '<':
                return op1 < op2
            elif expression_node.elem_type == '>':
                return op1 > op2
            elif expression_node.elem_type == '<=':
                return op1 <= op2
            elif expression_node.elem_type == '>=':
                return op1 >= op2
            elif expression_node.elem_type == '!=':
                return op1 != op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for integer operation",
                          )
        elif isinstance(op1,bool) and isinstance(op2, bool):
            if expression_node.elem_type == '==':
                return op1 == op2
            elif expression_node.elem_type == '||':
                return op1 or op2
            elif expression_node.elem_type == '&&':
                return op1 and op2
            elif expression_node.elem_type == '!=':
                return op1 != op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for boolean comparison",
                          )
        elif isinstance(op1, str) and isinstance(op2, str):
            if expression_node.elem_type == '==':
                return op1 == op2
            elif expression_node.elem_type == '!=':
                return op1 != op2
            elif expression_node.elem_type == '+':
                return op1 + op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for string operations",
                          )
        elif expression_node.elem_type == '==' or expression_node.elem_type == '!=':
            # comparison vals of diff types
            return False
        
        else:
            super().error(ErrorType.TYPE_ERROR,"Incompatible types for binary operation",
                          )
        
    # unary op neg or ! eval
    def evaluate_unary_operator(self, expression_node):
        # dict holds op1
        op1 = self.evaluate_expression(expression_node.get('op1'))
        
        if expression_node.elem_type == InterpreterBase.NEG_DEF:
            if not isinstance(op1,int):
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic negation",
                            )
            return -op1
        else:
            if not isinstance(op1,bool):
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for boolean negation",
                            )
            return not op1


## DELETEEE AT END
## open source testing ##