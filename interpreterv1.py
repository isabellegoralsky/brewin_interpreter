# exports Interpreter class
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
        if statement_node.elem_type == "=": # assignment
            # print("high")
            self.do_assignment(statement_node)
        elif statement_node.elem_type == InterpreterBase.FCALL_DEF:
            # function call
            self.do_print_fcall(statement_node)

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
                out_str += str(self.evaluate_expression(arg))
            super().output(out_str)
        else:
            super().error(ErrorType.NAME_ERROR,"print function only allowed",)
        # throw err if not
        # also its 0+ nodes
    
    def evaluate_expression(self, node):
        if node.elem_type == InterpreterBase.STRING_DEF or node.elem_type == InterpreterBase.INT_DEF:
            # value node
            return self.get_value(node)
        elif node.elem_type == InterpreterBase.VAR_DEF:
            # variable node
            return self.get_value_of_variable(node)
        elif node.elem_type == '+' or node.elem_type == '-':
            # expression node representing binary operation
            return self.evaluate_binary_operator(node)
        elif node.elem_type == "fcall":
            # eval it
            # in v1 will be a inputi fcall
            return self.do_inputi_fcall(node)
            
    def do_inputi_fcall(self, statement_node):
        # in v1 must be a print call
        if statement_node.get('name') == 'inputi':
            # output the single param which is the prompt (if any)
            if len(statement_node.get('args')) == 1:
                super().output(str(self.evaluate_expression(statement_node.get('args')[0])))
            elif len(statement_node.get('args')) > 1:
                super().error(ErrorType.NAME_ERROR,"inputi function can only have 1 or 0 args",)
            # throw err if >1
            # can guarantee the input will be a valid integer value so
            # go from str -> int
            user_input = InterpreterBase().get_input()
            return int(user_input)
        else:
            super().error(ErrorType.NAME_ERROR,"inputi function only allowed",)
        # throw err if not
        # also its 0+ nodes
    
    # value of value node
    def get_value(self, val_node):
        return val_node.get('val')
    
    # value of var node
    def get_value_of_variable(self, var_node):
        if var_node.get('name') in self.variable_name_to_value:
            return self.variable_name_to_value[var_node.get('name')]
        else:
            super().error(ErrorType.NAME_ERROR, f"Variable {var_node.get('name')} has not been defined",)
    
    # binary op + or - eval
    def evaluate_binary_operator(self, expression_node):
        # dict holds op1 and op2
        op1 = expression_node.get('op1')
        op2 = expression_node.get('op2')

        op1 = self.evaluate_expression(op1)
        op2 = self.evaluate_expression(op2)
        
        if isinstance(op1,str) or isinstance(op2,str):
            super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic operation",
                          )
        # print("op1 ", op1, "op2", op2)
        if expression_node.elem_type == '+':
            return op1 + op2
        else: # subtraction
            return op1 - op2

          

    # STARTING THESE BY THROWING NO ERRS

## DELETEEE AT END
## open source testing ##
# def main():
# interpreter = Interpreter()
# p1 = """func main() { /* a function that computes the sum of 2 numbers */
# first = 2;
# second = 5;
# sum = (first + second);
# print("The sum is ", sum, "!");  }"""
# p2 = """func main() { /* a function that computes the sum of 2 numbers */ 
# first = inputi("enter a #: ");
# second = 5;
# sum = (first + second);
# print("The sum is ", sum, "!");  } """
# p3 = """func main() {
    # a = 5 + 10;
    # print(a);  }"""
    # interpreter.run(p3)
    
# if __name__ == "__main__":
 #   main()