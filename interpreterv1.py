# exports Interpreter class
from intbase import InterpreterBase
from brewparse import parse_program

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None):
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
        self.var_to_val = {} # need self???
       
        # main func node = get main func node (ast)
        # is program node guaranteed to be first???
        prog_node = ast.get(InterpreterBase.PROGRAM_DEF)
        
        # get single node in program function list -> main()
        # only one node so name will be main
        # i dont think any args rn
        main_func_node = prog_node.get('functions')[0].get(InterpreterBase.FUNC_DEF)
        # ??? need this

        #run_func(main_func_node)
        run_func(main_func_node)

        # process nodes of the AST to run the program
    
    def run_func(func_node):
        # run statements in order that they appear in the program
        # aka order of execution
        for statement_node in func_node.get('statements'):
			run_statement(statement_node)

    def run_statement(statement_node):
        # look inside the statement nodes and figure out how to tell what they are
        if statement_node.elem_type == "=": # assignment
            do_assignment(statement_node)
        elif statement_node.elem_type == InterpreterBase.FCALL_DEF: # function call
            do_func_call(statement_node)
# 76485
    def do_assignment(statement_node):
        pass
        # target_var_name = get_target_variable_name(statement_node)
		# source_node = get_expression_node(statement_node)
		# resulting_value = evaluate_expression(source_node)
		# this.variable_name_to_value[target_var_name] = resulting_value

    def do_func_call(statement_node):
         pass
    
    def evaluate_expression(expression_node):
        pass
        #if is_value_node(expression_node):
            # return get_value(expression_node)
        # else if is_variable_node(expression_node):
            # return get_value_of_variable(expression_node)
        # else if is_binary_operator(expression_node):
            # return evaluate_binary_operator(expression_node)
        # ...
    
    # more funcs...
