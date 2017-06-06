class newClass:
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.c = False

class1 = newClass(1,2)
class1.c = True
print class1.c
