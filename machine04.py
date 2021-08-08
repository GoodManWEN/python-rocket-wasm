import struct

class Function:

    def __init__(self, nparams, returns, code):
        self.nparams = nparams
        self.returns = returns
        self.code = code

class Machine:

    def __init__(self, functions, memsize=65536):
        self.functions = functions # function table
        self.items = []
        self.memory = bytearray(memsize)

    def load(self, addr):
        return struct.unpack('<d', self.memory[addr:addr+8])[0]

    def store(self, addr, val):
        self.memory[addr:addr+8] = struct.pack('<d', val)

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def call(self, func, *args):
        locals = dict(enumerate(args))  # { 0: args[0], 1: args[1], 2: args[2]}
        try:
            self.execute(func.code, locals)
        except Return:
            pass
        if func.returns:
            return self.pop()

    def execute(self, instructions, locals):
        for op, *args in instructions:
            print(op, args, self.items)
            if op == 'const':
                self.push(args[0])
            elif op == 'add':
                right = self.pop()
                left = self.pop()
                self.push(left + right)
            elif op == 'sub':
                right = self.pop()
                left = self.pop()
                self.push(left - right)
            elif op == 'mul':
                right = self.pop()
                left = self.pop()
                self.push(left * right)
            elif op == 'le':
                right = self.pop()
                left = self.pop()
                self.push(left <= right)
            elif op == 'ge':
                right = self.pop()
                left = self.pop()
                self.push(left >= right)
            elif op == 'load':
                addr = self.pop()
                self.push(self.load(addr))
            elif op == 'store':
                val = self.pop()
                addr = self.pop()
                self.store(addr, val)
            elif op == 'local.get':
                self.push(locals[args[0]])
            elif op == 'local.set':
                locals[args[0]] = self.pop()
            elif op == 'call':
                func = self.functions[args[0]]
                fargs = reversed([ self.pop() for _ in range(func.nparams) ])
                result = self.call(func, *fargs)
                if func.returns:
                    self.push(result)

            # if (test) { consequence } else { alternative }
            elif op == 'br':
                raise Break(args[0])
            elif op == 'br_if':
                if self.pop():
                    raise Break(args[0])

            # ('block', [ instructions ])
            elif op == 'block': 
                try:
                    self.execute(args[0], locals)
                except Break as b:
                    if b.level > 0:
                        b.level -= 1
                        raise 

            # if (test) { consequence } else { alternative }
            # 
            # ('block', [
            #         ('block', [
            #                 test,
            #                 ('br_if', 0),  # Goto 0
            #                 alternative,
            #                 ('br', 1),     # Goto 1
            #             ]
            #         ), # Label : 0
            #         consequence,
            #     ]
            # ) # Label : 1

            elif op == 'loop':
                while True:
                    try:
                        self.execute(args[0], locals)
                        break 
                    except Break as b:
                        if b.level > 0:
                            b.level -= 1
                            raise 

            # while (test) { body }
            # ('block', [
            #         ('loop', [    # Label 0
            #                 not test
            #                 ('br_if', 1),   # Goto 1: (break)
            #                 body
            #                 ('br', 0),      # Goto 0: (continue)
            #             ]
            #         )
            #     ]
            # )   # Label 1

            elif op == 'return':
                raise Return()

            else:
                raise RuntimeError(f'Bad op {op}')

class Break(Exception):

    def __init__(self, level):
        self.level = level

class Return(Exception):
    pass


def example():
    # def update_position(x, v, dt):
    #     return x + v*dt
    # 
    # x = 2
    # v = 3
    # x = x + v * 0.1

    update_position = Function(nparams = 3, returns = True, code = [
        ('local.get', 0), # x
        ('local.get', 1), # v
        ('local.get', 2), # dt
        ('mul', ), 
        ('add', ), 
    ])

    functions = [update_position, ]
    # Compute 2 + 3 * 0.1
    x_addr = 22
    v_addr = 42

    # while x > 0 {
    #     x = update_position(x, v, 0.1)
    #     if x >= 70 {
    #         v = -v;
    #     }
    # }

    code = [
        ('block', [
                ('loop', [
                        ('const', x_addr),
                        ('load', ),
                        ('const', 0.0),
                        ('le', ),
                        ('br_if', 1),
                        ('const', x_addr),
                        ('const', x_addr),
                        ('load', ),
                        ('const', v_addr),
                        ('load', ),
                        ('const', 0.1),
                        ('call', 0),
                        ('store', ),
                        ('block', [
                                ('const', x_addr), 
                                ('load', ),
                                ('const', 70.0),
                                ('ge', ),
                                ('block', [
                                        ('br_if', 0),
                                        ('br', 1),
                                    ]
                                ),
                                ('const', v_addr),
                                ('const', 0.0),
                                ('const', v_addr),
                                ('load', ),
                                ('sub', ),
                                ('store', ),
                            ]
                        ),
                        ('br', 0),
                    ]
                )
            ]
        )
    ]

    m = Machine(functions)
    m.store(x_addr, 2.0)
    m.store(v_addr, 3.0)
    m.execute(code, None)
    print('Result', m.load(x_addr))

if __name__ == '__main__':
    example()
