from lcapy import *
import unittest
import sympy as sym


class LcapyTester(unittest.TestCase):

    """Unit tests for lcapy

    """

    def assertEqual2(self, ans1, ans2, comment):

        ans1 = ans1.canonical()
        ans2 = ans2.canonical()

        try:
            self.assertEqual(ans1, ans2, comment)
        except AssertionError as e:
            ans1.pprint()
            ans2.pprint()
            raise AssertionError(e)

    def test_VR_ac1(self):
        """Lcapy: check VR ac network

        """

        a = Vac(4) | R(2)

        self.assertEqual(a.is_dc, False, "DC incorrect")
        self.assertEqual(a.is_ac, True, "AC incorrect")


    def test_VR_dc1(self):
        """Lcapy: check VR dc network

        """

        a = Vdc(4) | R(2)

        self.assertEqual(a.is_ivp, False, "is_ivp incorrect")
        self.assertEqual(a.is_ac, False, "AC incorrect")
        self.assertEqual(a.is_dc, True, "DC incorrect")


    def test_VC_dc1(self):
        """Lcapy: check VC dc network

        """

        a = Vdc(4) + C(2)

        self.assertEqual(a.is_ivp, False, "is_ivp incorrect")
        self.assertEqual(a.is_ac, False, "AC incorrect")
        self.assertEqual(a.is_dc, True, "DC incorrect")


    def test_VC_dc2(self):
        """Lcapy: check VC dc network

        """

        a = Vdc(4) + C(2, 0)

        self.assertEqual(a.is_ivp, True, "is_ivp incorrect")
        self.assertEqual(a.is_ac, False, "AC incorrect")
        self.assertEqual(a.is_dc, False, "DC incorrect")

    def test_thevenin_ac(self):
        """Lcapy: check ac Thevenin conversion

        """
        a = (Vac('1') + C(2)) | R(3)
        
        self.assertEqual(a.norton().isc, TimeDomainCurrent(-2 * omega0 * sin(omega0 * t)),
                         "Isc incorrect")
        self.assertEqual(a.thevenin().isc,  TimeDomainCurrent(-2 * omega0 * sin(omega0 * t)),
                         "Isc incorrect")
        
    def test_superposition(self):
        """Lcapy: check network superposition"""

        a = Vac(40) + Vnoise(20) + Vstep(10) + R(5)
        self.assertEqual(a.Voc.dc, 0, "Voc.dc error")
        self.assertEqual(a.Voc.has_dc, False, "Voc.has_dc error")
        self.assertEqual(a.Voc.is_dc, False, "Voc.is_dc error")
        self.assertEqual(a.Voc.has_ac, True, "Voc.has_ac error")
        self.assertEqual(a.Voc.is_ac, False, "Voc.is_ac error")                                
        self.assertEqual2(a.Voc.s, 10 / s, "Voc.s error")
        self.assertEqual(a.Voc.n.expr, AngularFourierDomainNoiseVoltage(20).expr, "Voc.n error")
        self.assertEqual2(a.Voc.w, PhasorVoltage(40), "Voc.w error")
        self.assertEqual2(a.Isc.s, 2 / s, "Isc.s error")
        # FIXME, this intermittently fails.
        self.assertEqual(a.Isc.n.expr, AngularFourierDomainNoiseCurrent(4).expr, "Isc.n error")
        self.assertEqual2(a.Isc.w, PhasorCurrent(8), "Isc.w error")        
        
    def test_ivp(self):
        """Lcapy: check network with initial values"""

        a = Vstep(10) + C('C1', 5)
        self.assertEqual(a.is_ivp, True, "IVP fail")
        self.assertEqual2(a.Voc.s, 15 / s, "Voc fail")

    def test_causal(self):
        """Lcapy: check network is causal"""

        a = Vstep(10) + C('C1')
        self.assertEqual(a.is_causal, True, "causal fail")
        self.assertEqual(a.Isc.is_causal, True, "causal fail")        
        
        
    def test_YZ(self):

        a = R(1) + V(2) + R(3)
        self.assertEqual(a.Z, 4, "series Z")
        self.assertEqual(a.Y, expr('1 / 4'), "series Y")

        b = (R(1) + V(2)) | R(3)
        self.assertEqual(b.Z, expr('3 / 4'), "par Z")
        self.assertEqual(b.Y, expr('4 / 3'), "par Y")                        
