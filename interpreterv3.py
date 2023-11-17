# exports Interpreter class VERSION 2.0
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
from element import Element
import copy

class Val:
    def __init__(self, v):
        self.env = {'val':v}
        
    def getVal(self):
        return self.env['val']
    
    def setVal(self, v):
        self.env['val'] = v

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
        #self.variable_name_to_value = {} # need self???
        # save for func defs
        self.functions = ast.get('functions')
        
        
        # main func node = get main func node (ast)
        # is program node guaranteed to be first???
        #prog_node = ast.get(InterpreterBase.PROGRAM_DEF)
        
        # get main function from functions list in AST
        main_func_node = None
        for f in self.functions:
            if f.get('name') == 'main':
                main_func_node = f
                
        if main_func_node is None:
            super().error(ErrorType.NAME_ERROR,"No main() function was found",)


        #run_func(main_func_node)
        self.scopes = [{'name': 'main', 'vars_to_val': {}}] # main function uses global dict
        # process nodes of the AST to run the program
        self.run_func(main_func_node)

        self.scopes.pop()  #remove last item (just clean up. not necessary.)
    
    def run_func(self, func_node):
        # run statements in order that they appear in the program
        # aka order of execution
        for statement_node in func_node.get('statements'):
            ret = self.run_statement(statement_node)
            if ret is not None:
                return ret
            if statement_node.elem_type == InterpreterBase.RETURN_DEF:
                break
            #print(statement_node)
        return None

    def run_statement(self, statement_node):
        # look inside the statement nodes and figure out how to tell what they are
        if statement_node.elem_type == "=":
            # assignment
            return self.do_assignment(statement_node)
        elif statement_node.elem_type == InterpreterBase.FCALL_DEF:
            # function call
            if statement_node.get('name') == 'print':
                return self.do_print_fcall(statement_node)
            else:
                return self.fcall(statement_node)
        elif statement_node.elem_type == InterpreterBase.IF_DEF:
            # elif if statement
            return self.do_if_statement(statement_node)
        elif statement_node.elem_type == InterpreterBase.WHILE_DEF: # here
            # elif while loop
            return self.do_while_loop(statement_node)
        elif statement_node.elem_type == InterpreterBase.RETURN_DEF:
            # elif return statement
            #print(statement_node)
            return self.do_ret_statement(statement_node)

    def do_assignment(self, statement_node):
        target_var_name = statement_node.get('name')
        # in x = 2 + 10 this is x
        source_node = statement_node.get('expression')
        #print("target ", target_var_name, "expression ", source_node)
        # either expression like 2+10, value like 2, or var like x=y
        resulting_value = self.evaluate_expression(source_node)
        #print("result ", resulting_value)
        
        # if var name is in this function, set it
        # if var name is in scope of other functions, set it
        
        flag = False
        i = len(self.scopes) - 1
        while i >= 0:
            if target_var_name in self.scopes[i]['vars_to_val'].keys():
                flag = True
                self.scopes[i]['vars_to_val'][target_var_name].setVal(resulting_value)
                break
            i -= 1
        
        # else create it in this function
        if not flag:
            l = len(self.scopes) - 1
            self.scopes[l]['vars_to_val'][target_var_name] = Val(resulting_value)
        return None

    def fcall(self, fcall):
        
        # locate function in the function list
        for f in self.functions:
            # run func and maybe later check args
            if f.get('name') == fcall.get('name') and len(f.get('args')) == len(fcall.get('args')):
                self.scopes.append({'name': f.get('name'), 'vars_to_val': {}})
                # add args to the vars and values list
                # im thinking of creating a local vars list and adding them to thatprint("isabell")
                l = len(self.scopes) - 1
                for i in range(len(f.get('args'))):
                    if f.get('args')[i].elem_type == 'refarg':
                        self.scopes[l]['vars_to_val'][f.get('args')[i].get('name')] = copy.copy(self.scopes[l-1]['vars_to_val'][fcall.get('args')[i].get('name')])
                    else:
                        self.scopes[l]['vars_to_val'][f.get('args')[i].get('name')] = copy.deepcopy(self.scopes[l-1]['vars_to_val'][fcall.get('args')[i].get('name')])
                # run func
                fu = self.run_func(f)
                
                # want to remove scope
                self.scopes.pop()
                return fu
        
        # check for func in var
        i = len(self.scopes) - 1
        while i>=0:
            formal_func = self.scopes[i]['vars_to_val'][fcall.get('name')].getVal() # value of variable passed in as function

            if type(formal_func) is Element and formal_func.elem_type == 'func' and len(formal_func.get('args')) == len(fcall.get('args')):
                # run the function
                self.scopes.append({'name': fcall.get('name'), 'vars_to_val': {}})

                l = len(self.scopes) - 1
                for k in range(len(formal_func.get('args'))):
                    if formal_func.get('args')[k].elem_type == 'refarg':
                        self.scopes[l]['vars_to_val'][formal_func.get('args')[k].get('name')] = copy.copy(self.scopes[l-1]['vars_to_val'][fcall.get('args')[k].get('name')])
                    else:
                        if fcall.get('args')[k].elem_type == 'var':
                            self.scopes[l]['vars_to_val'][formal_func.get('args')[k].get('name')] = copy.deepcopy(self.scopes[l-1]['vars_to_val'][fcall.get('args')[k].get('name')])
                        else:
                            self.scopes[l]['vars_to_val'][formal_func.get('args')[k].get('name')] = Val(fcall.get('args')[k].get('val'))
                # run func
                fu = self.run_func(formal_func)
                
                # want to remove scope
                self.scopes.pop()
                return fu
            if type(formal_func) is Element and formal_func.elem_type == 'lambda' and len(formal_func.get('args')) == len(fcall.get('args')):
                print("my formal def :", formal_func)
                # lambda: args: [arg: name: a], statements: [fcall: name: print, args: [*: op1: [var: name: a], op2: [var: name: b]]], closures: {'b': <__main__.Val object at 0x1006947d0>}
                print("my lambda :", fcall)
                # fcall: name: x, args: [int: val: 20]
                self.scopes.append({'name': fcall.get('name'), 'vars_to_val': {}})
                
                # check closures. add these vars to the scoped environment
                l = len(self.scopes) - 1
                for key,val in formal_func.get('closures').items(): # key is var name and val is Val obj
                    # TODO: as long as the var name != name of an arg
                    self.scopes[l]['vars_to_val'][key] = val
                
                # check args and do the same as above
                for k in range(len(formal_func.get('args'))):
                    print("formal arg: ", formal_func.get('args')[k])
                    print("input: ", fcall.get('args')[k].elem_type)
                    if formal_func.get('args')[k].elem_type == 'refarg':
                        self.scopes[l]['vars_to_val'][formal_func.get('args')[k].get('name')] = copy.copy(self.scopes[l-1]['vars_to_val'][fcall.get('args')[k].get('name')])
                    else:
                        if fcall.get('args')[k].elem_type == 'var':
                            self.scopes[l]['vars_to_val'][formal_func.get('args')[k].get('name')] = copy.deepcopy(self.scopes[l-1]['vars_to_val'][fcall.get('args')[k].get('name')])
                        else:
                            # input is a primitive
                            self.scopes[l]['vars_to_val'][formal_func.get('args')[k].get('name')] = Val(fcall.get('args')[k].get('val'))
                # run the func
                fu = self.run_func(formal_func)
                
                # remove scope
                self.scopes.pop()
                return fu
            else:
                super().error(ErrorType.TYPE_ERROR,f"Function {fcall.get('name')} isn't a function",)
            i -=1;
        
        super().error(ErrorType.NAME_ERROR,f"Function {fcall.get('name')} wasn't found",)
        # throw err

    def do_print_fcall(self, statement_node):
        # in v1 must be a print call
        if statement_node.get('name') == 'print':
            outstr = ""
            for arg in statement_node.get('args'):
                s = self.evaluate_expression(arg)
                if s is None:
                    outstr += "nil"
                else:
                    s = str(s)
                    if s == "True":
                        outstr += "true"
                    elif s == "False":
                        outstr += "false"
                    else:
                        outstr += s
                    
                
            super().output(outstr)
        else:
            super().error(ErrorType.NAME_ERROR,"print function only allowed",)
        # throw err if not
        # also its 0+ nodes
    
    def do_if_statement(self, statement_node):
        self.scopes.append({'name': 'if', 'vars_to_val': {}})
        cond = self.evaluate_expression(statement_node.get('condition'))
        if type(cond) is not bool and type(cond) is not int:
            super().error(ErrorType.TYPE_ERROR,"condition of if statement must be type bool or int",)
            
        if type(cond) is int:
            if cond == 0:
                cond = False
            else:
                cond = True
            
        if cond:
            for s in statement_node.get('statements'):
                ret = self.run_statement(s)
                if ret is not None:
                    self.scopes.pop()
                    return ret
            self.scopes.pop()
            return None
        elif statement_node.get('else_statements') is not None:
            #print("BALLS")
            #print(self.scopes[len(self.scopes)-3])
            for s in statement_node.get('else_statements'):
                ret = self.run_statement(s)
                if ret is not None:
                    self.scopes.pop()
                    return ret
            self.scopes.pop()
            return None
        self.scopes.pop()
        return None
    
    def do_while_loop(self, statement_node):
        cond = self.evaluate_expression(statement_node.get('condition'))
        if type(cond) is not bool and type(cond) is not int:
            super().error(ErrorType.TYPE_ERROR,"condition of while loop must be type bool or int",)
            
        if type(cond) is int:
            if cond == 0:
                cond = False
            else:
                cond = True

        while cond:
            self.scopes.append({'name': 'while', 'vars_to_val': {}})
            for s in statement_node.get('statements'):
                ret = self.run_statement(s)
                if ret is not None:
                    self.scopes.pop()
                    return ret
            cond = self.evaluate_expression(statement_node.get('condition'))
            self.scopes.pop()
            if type(cond) is not bool and type(cond) is not int:
                super().error(ErrorType.TYPE_ERROR,"condition of while loop must be type bool or int",)
            
            if type(cond) is int:
                if cond == 0:
                    cond = False
                else:
                    cond = True
                
        
        return None
        
    
    def do_ret_statement(self, statement_node):
        if statement_node.get('expression') is not None:
            r = self.evaluate_expression(statement_node.get('expression'))
            if r == InterpreterBase.NIL_DEF:
                return None
            else:
                return copy.deepcopy(r)
        return None
    
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
            if node.get('name') == 'inputi':
                return self.do_inputi_fcall(node)
            elif node.get('name') == 'inputs':
                return self.do_inputs_fcall(node)
            elif node.get('name') == 'print':
                return self.do_print_fcall(node)
            else:
                return self.fcall(node)
        elif node.elem_type == InterpreterBase.LAMBDA_DEF:
            return self.create_lambda(node)
        elif node.elem_type == InterpreterBase.NEG_DEF or node.elem_type == InterpreterBase.NOT_DEF:
            # unary operation
            return self.evaluate_unary_operator(node)
         
    def create_lambda(self, lambda_exp):
        
        # need to create a closure of these vars
        # create a new key called closures with a dict of all vars and their vals
        i = 0
        lambda_exp.dict['closures'] = {}
        while i < len(self.scopes):
            for key,val in self.scopes[i]['vars_to_val'].items():
                # making a copy
                lambda_exp.dict['closures'][key] = Val(val.getVal())
            i += 1
        
        return lambda_exp
            
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
        
    def do_inputs_fcall(self, statement_node):
        # output the single param which is the prompt (if any)
        if len(statement_node.get('args')) == 1:
            super().output(str(self.evaluate_expression(statement_node.get('args')[0])))
        elif len(statement_node.get('args')) > 1:
            super().error(ErrorType.NAME_ERROR,"inputs function can only have 1 or 0 args",)
            
        # guarantee that the input is a valid integer in String form
        user_input = super().get_input()
        if user_input == None:
            super().error(ErrorType.FAULT_ERROR,"inputs function takes in a string",)
        return user_input
        # throw err if not
        # also its 0+ nodes
    
    # value of value node
    def get_value(self, val_node):
        if val_node.elem_type == InterpreterBase.NIL_DEF:
            return None
        
        return val_node.get('val')
    
    # value of var node
    def get_value_of_variable(self, var_node): # need to do this for the other ones too
        i = len(self.scopes) - 1
        while i >= 0:
            if var_node.get('name') in self.scopes[i]['vars_to_val'].keys() :
                return self.scopes[i]['vars_to_val'][var_node.get('name')].getVal()
            i -= 1
        
        count = 0
        func = None
        for f in self.functions:
            if f.get('name') == var_node.get('name'):
                count += 1
                func = f
        
        if func is not None:
            if count == 1:
                return func
            else:
                super().error(ErrorType.NAME_ERROR, f"Function var name {var_node.get('name')} is ambiguous",)
            
        
        super().error(ErrorType.NAME_ERROR, f"Variable {var_node.get('name')} has not been defined",)
    
    # binary ops, bool and arith
    def evaluate_binary_operator(self, expression_node):
        # dict holds op1 and op2
        op1 = expression_node.get('op1')
        op2 = expression_node.get('op2')
        
        #print("op1 expression node", op1)
        #print("op2 expression node", op2)

        op1 = self.evaluate_expression(op1)
        op2 = self.evaluate_expression(op2)
        
        #print("op1 evaled", op1)
        #print(expression_node.elem_type)
        #print("op2 evaled", op2)
        
        
        if type(op1) is int and type(op2) is int:
            if expression_node.elem_type == '+':
                # here
                return op1 + op2
            elif expression_node.elem_type == '-':
                # here
                return op1 - op2
            elif expression_node.elem_type == '*':
                # here
                return op1 * op2
            elif expression_node.elem_type == '/':
                # here
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
            elif expression_node.elem_type == '&&':
                if op1 != 0 and op2 != 0:
                    return True
                else:
                    return False
            elif expression_node.elem_type == '||':
                if op1 != 0 or op2 != 0:
                    return True
                else:
                    return False
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for integer operation",
                          )
        elif type(op1) is bool and type(op2) is bool:
            if expression_node.elem_type == '==':
                return op1 == op2
            elif expression_node.elem_type == '||':
                return op1 or op2
            elif expression_node.elem_type == '&&':
                return op1 and op2
            elif expression_node.elem_type == '!=':
                return op1 != op2
            elif expression_node.elem_type == '+':
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 + op2
            elif expression_node.elem_type == '-':
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 - op2
            elif expression_node.elem_type == '*':
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 * op2
            elif expression_node.elem_type == '/':
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 // op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for boolean comparison",
                          )
        elif type(op1) is str and type(op2) is str:
            if expression_node.elem_type == '==':
                return op1 == op2
            elif expression_node.elem_type == '!=':
                return op1 != op2
            elif expression_node.elem_type == '+':
                return op1 + op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for string operations",
                          )
        elif op1 is None and op2 is None:
            if expression_node.elem_type == '==':
                return True
            else:
                return False
        elif expression_node.elem_type == '+':
            if type (op1) is int and type (op2) is bool:
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 + op2
            elif type(op1) is bool and type (op2) is int:
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                return op1 + op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for binary operation",
                          )
        elif expression_node.elem_type == '-':
            if type (op1) is int and type (op2) is bool:
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 - op2
            elif type(op1) is bool and type (op2) is int:
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                return op1 - op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for binary operation",)
        elif expression_node.elem_type == '*':
            if type (op1) is int and type (op2) is bool:
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 * op2
            elif type(op1) is bool and type (op2) is int:
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                return op1 * op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for binary operation",)
        elif expression_node.elem_type == '/':
            if type (op1) is int and type (op2) is bool:
                if op2:
                    op2 = 1
                else:
                    op2 = 0
                return op1 // op2
            elif type(op1) is bool and type (op2) is int:
                if op1:
                    op1 = 1
                else:
                    op1 = 0
                return op1 // op2
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for binary operation",)
        elif expression_node.elem_type == '&&':
            if type (op1) is int and type (op2) is bool:
                # compare int and bool
                if op2 and op1 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op2 and op1 == 0:
                    # op2 is True and op1 is Zero
                    return False
                elif op1 == 0:
                    #op2 false
                    return False
            elif type(op1) is bool and type (op2) is int:
                # compare int and bool
                if op1 and op2 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op1 and op2 == 0:
                    # op2 is True and op1 is Zero
                    return False
                elif op2 == 0:
                    #op2 false
                    return False 
            else:
                return False
        elif expression_node.elem_type == '||':
            if type (op1) is int and type (op2) is bool:
                # compare int and bool
                if op2 and op1 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op2 and op1 == 0:
                    # op2 is True and op1 is Zero
                    return True
                elif op1 == 0:
                    #op2 false and op1 zero
                    return False
                else:
                    # op2 false and op1 non zero
                    return True
            elif type(op1) is bool and type (op2) is int:
                # compare int and bool
                if op1 and op2 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op1 and op2 == 0:
                    # op2 is True and op1 is Zero
                    return True
                elif op2 == 0:
                    #op2 false and op1 zero
                    return False
                else:
                    # op2 false and op1 non zero
                    return True   
            else:
                return False
        elif expression_node.elem_type == '==':
            # comparison vals of diff types
            if type (op1) is int and type (op2) is bool:
                # compare int and bool
                if op2 and op1 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op2 and op1 == 0:
                    # op2 is True and op1 is Zero
                    return False
                elif op1 == 0:
                    #op2 false and op1 zero
                    return True
                else:
                    # op2 false and op1 non zero
                    return False
            elif type(op1) is bool and type (op2) is int:
                # compare int and bool
                if op1 and op2 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op1 and op2 == 0:
                    # op2 is True and op1 is Zero
                    return False
                elif op2 == 0:
                    #op2 false and op1 zero
                    return True
                else:
                    # op2 false and op1 non zero
                    return False   
            elif type(op1) is Element and type(op2) is Element:
                # need function comparison
                if op1.elem_type == 'func' and op2.elem_type == 'func':
                    if op1.get('name') == op2.get('name') and op1.get('args') == op2.get('args') and op1.get('statements') == op2.get('statements'):
                        return True
                return False
            else:
                return False
        elif expression_node.elem_type == '!=':
            # comparison vals of diff types
            if type (op1) is int and type (op2) is bool:
                # compare int and bool
                if op2 and op1 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op2 and op1 == 0:
                    # op2 is True and op1 is Zero
                    return False
                elif op1 == 0:
                    #op2 false and op1 zero
                    return True
                else:
                    # op2 false and op1 non zero
                    return False
            elif type(op1) is bool and type (op2) is int:
                # compare int and bool
                if op1 and op2 != 0:
                    # op2 is True and op1 is non Zero
                    return True
                elif op1 and op2 == 0:
                    # op2 is True and op1 is Zero
                    return False
                elif op2 == 0:
                    #op2 false and op1 zero
                    return True
                else:
                    # op2 false and op1 non zero
                    return False 
            elif type(op1) is Element and type(op2) is Element:
                # need function comparison
                if op1.elem_type == 'func' and op2.elem_type == 'func':
                    if op1.get('name') == op2.get('name') and op1.get('args') == op2.get('args') and op1.get('statements') == op2.get('statements'):
                        return False
                return True
            else:
                return True
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
        else: # boolean negative
            if type(op1) is bool:
                return not op1
            elif type(op1) is int:
                if op1 == 0:
                    return True
                else:
                    return False
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for boolean negation",
                            )


## DELETEEE AT END
## open source testing ##

def main():
    inte = Interpreter()
    p1 = """func foo() {
  b = 5;
  f = lambda(a) { print(a*b); };   /* captures b = 5 */

  return f;
}

func main() {
  x = foo();
  x(20);   /* prints 100, the call to the lambda has access to b = 5 */
}"""
    inte.run(p1)
                
if __name__ == "__main__":
    main()