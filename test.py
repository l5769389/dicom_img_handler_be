class A():
    def __init__(self):
        print('a init')
        self.name = 'zhangs'
        pass

    def call(self):
        print('a call')
        print(self.name)

class B(A):
    def __init__(self):
        pass

    def sleep(self):
        self.call()


b = B()
b.sleep()
