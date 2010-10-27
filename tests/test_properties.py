'''
New properties
'''

from init import test, import_pymt_no_window

def unittest_property():
    import_pymt_no_window()
    from pymt.c_ext.c_properties import Property

    a = Property(-1)
    test(a.get() == -1)
    a.set(0)
    test(a.get() == 0)
    a.set(1)
    test(a.get() == 1)

def unittest_property_observer():
    import_pymt_no_window()
    from pymt.c_ext.c_properties import Property

    a = Property(-1)
    test(a.get() == -1)
    global observe_called
    observe_called = 0
    def observe(value):
        global observe_called
        observe_called = 1
    a.bind(observe)

    a.set(0)
    test(a.get() == 0)
    test(observe_called == 1)
    observe_called = 0
    a.set(0)
    test(a.get() == 0)
    test(observe_called == 0)
    a.set(1)
    test(a.get() == 1)
    test(observe_called == 1)

def unittest_property_stringcheck():
    import_pymt_no_window()
    from pymt.c_ext.c_properties import StringProperty

    a = StringProperty('')
    test(a.get() == '')
    a.set('hello')
    test(a.get() == 'hello')

    try:
        a.set(88) # number shouldn't be accepted
        test('string accept number, fail.' == 0)
    except ValueError:
        test('string dont accept number')

def unittest_property_numericcheck():
    import_pymt_no_window()
    from pymt.c_ext.c_properties import NumericProperty

    a = NumericProperty(0)
    test(a.get() == 0)
    a.set(99)
    test(a.get() == 99)

    try:
        a.set('') # string shouldn't be accepted
        test('number accept string, fail.' == 0)
    except ValueError:
        test('number dont accept string')

def unittest_property_propertynone():
    import_pymt_no_window()
    from pymt.c_ext.c_properties import NumericProperty

    a = NumericProperty(0, allownone=True)
    test(a.get() == 0)
    try:
        a.set(None)
        test(a.get() == None)
    except ValueError, e:
        print e
        test('none not accepted' == 0)
    a.set(1)
    test(a.get() == 1)


