from lcapy import *
from lcapy.discretetime import *
import unittest
import sympy as sym


class LcapyTester(unittest.TestCase):

    """Unit tests for lcapy

    """

    def test_ztransform(self):

        self.assertEqual(nexpr(1).ztransform(), z / (z - 1), "1")
        self.assertEqual(nexpr(3).ztransform(), 3 * z / (z - 1), "3")
        self.assertEqual(Heaviside(n).ztransform(), z / (z - 1), "Heaviside(n)")
        self.assertEqual(3 * Heaviside(n).ztransform(), 3 * z / (z - 1), "3 * Heaviside(n)")
        self.assertEqual(Heaviside(n + 1).ztransform(), 1 / (z - 1), "Heaviside(n + 1)")
        self.assertEqual(unitimpulse(n).ztransform(), 1, "unitimpulse(n)")
        self.assertEqual(3 * unitimpulse(n).ztransform(), 3, "unitimpulse(n)")        
        self.assertEqual(unitimpulse(n - 1).ztransform(), 1 / z, "unitimpulse(n - 1)")
        self.assertEqual(unitimpulse(n - 2).ztransform(), 1 / z**2, "unitimpulse(n - 2)")
        self.assertEqual(3 * unitimpulse(n - 2).ztransform(), 3 / z**2, "3 * unitimpulse(n - 2)")
        self.assertEqual(3 * unitimpulse(n + 2).ztransform(), 3 * z**2, "3 * unitimpulse(n + 2)")                
        self.assertEqual(expr('v(n)').ztransform(), expr('V(z)'), "v(n)")
        self.assertEqual(expr('v(n / 3)').ztransform(), expr('V(z**3)'), "v(n/3)")
        self.assertEqual(expr('3 * v(n / 3)').ztransform(), expr('3 * V(z**3)'), "3 * v(n/3)")
        self.assertEqual(expr('v(n-3)').ztransform(), expr('V(z) / z**3'), "v(n - 3)")
        self.assertEqual(nexpr('x(n)').ztransform(), zexpr('X(z)'), "x(n)")
                         

    def test_inverse_ztransform(self):

        self.assertEqual(zexpr(1).inverse_ztransform(), unitimpulse(n), "1")
        self.assertEqual((z**-1).inverse_ztransform(), unitimpulse(n-1), "z**-1")
        self.assertEqual((z**-2).inverse_ztransform(), unitimpulse(n-2), "z**-2")
        self.assertEqual(zexpr('1 / (1 - a * z ** -1)').inverse_ztransform(causal=True), nexpr('a**n * u(n)'), "1 / (1 - a * z)")                        
        self.assertEqual(zexpr('X(z)').inverse_ztransform(), nexpr('x(n)'), "X(z)")


    def test_misc(self):

        x = 3 * unitimpulse(n - 2)
        y = x.differentiate()
        X = x.ZT().ndifferentiate().IZT()
        
        