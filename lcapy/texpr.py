"""This module provides the TimeDomainExpression class to represent time domain expressions.

Copyright 2014--2020 Michael Hayes, UCECE

"""

from __future__ import division
from .expr import Expr
from .functions import exp
from .sym import fsym, ssym, tsym, j, oo, tausym
from .acdc import ACChecker, is_dc, is_ac, is_causal
from .laplace import laplace_transform
from .fourier import fourier_transform
from sympy import Heaviside, limit, Integral, Expr as symExpr


class TimeDomainExpression(Expr):

    """t-domain expression or symbol."""

    var = tsym
    domain_name = 'Time'
    domain_units = 's'

    def __init__(self, val, **assumptions):

        check = assumptions.pop('check', True)        
        assumptions['real'] = True
        super(TimeDomainExpression, self).__init__(val, **assumptions)

        self._fourier_conjugate_class = FourierDomainExpression
        self._laplace_conjugate_class = LaplaceDomainExpression

        expr = self.expr        
        if check and expr.find(ssym) != set() and not expr.has(Integral):
            raise ValueError(
                't-domain expression %s cannot depend on s' % expr)
        if check and expr.find(fsym) != set() and not expr.has(Integral):
            raise ValueError(
                't-domain expression %s cannot depend on f' % expr)                            

    def infer_assumptions(self):

        self.assumptions['dc'] = False
        self.assumptions['ac'] = False
        self.assumptions['causal'] = False

        var = self.var
        if is_dc(self, var):
            self.assumptions['dc'] = True
            return

        if is_ac(self, var):
            self.assumptions['ac'] = True
            return

        if is_causal(self, var):
            self.assumptions['causal'] = True

    def laplace(self, evaluate=True, **assumptions):
        """Determine one-sided Laplace transform with 0- as the lower limit."""

        # The assumptions are required to help with the inverse Laplace
        # transform if required.
        self.infer_assumptions()

        assumptions = self.merge_assumptions(**assumptions)
        
        result = laplace_transform(self.expr, self.var, ssym, evaluate=evaluate)

        if hasattr(self, '_laplace_conjugate_class'):
            result = self._laplace_conjugate_class(result, **assumptions)
        else:
            result = LaplaceDomainExpression(result, **assumptions)
        return result

    def LT(self, **assumptions):
        """Convert to s-domain.   This is an alias for laplace."""

        return self.laplace(**assumptions)
    
    def fourier(self, evaluate=True, **assumptions):
        """Attempt Fourier transform."""

        assumptions = self.merge_assumptions(**assumptions)
        
        result = fourier_transform(self.expr, self.var, fsym, evaluate=evaluate)

        if hasattr(self, '_fourier_conjugate_class'):
            result = self._fourier_conjugate_class(result, **assumptions)
        else:
            result = FourierDomainExpression(result **self.assumptions)
        return result

    def FT(self, **assumptions):
        """Convert to f-domain.   This is an alias for fourier."""

        return self.fourier(**assumptions)    

    def phasor(self, **assumptions):

        check = ACChecker(self, t)
        if not check.is_ac:
            raise ValueError('Do not know how to convert %s to phasor' % self)
        phasor = PhasorExpression(check.amp * exp(j * check.phase), omega=check.omega)
        return phasor

    def plot(self, t=None, **kwargs):
        """Plot the time waveform.  If t is not specified, it defaults to the
        range (-0.2, 2).  t can be a vector of specified instants, a
        tuple specifing the range, or a constant specifying the
        maximum value with the minimum value set to 0.

        kwargs include:
        axes - the plot axes to use otherwise a new figure is created
        xlabel - the x-axis label
        ylabel - the y-axis label
        xscale - the x-axis scaling, say for plotting as ms
        yscale - the y-axis scaling, say for plotting mV
        in addition to those supported by the matplotlib plot command.
        
        The plot axes are returned."""

        from .plot import plot_time
        return plot_time(self, t, **kwargs)

    def sample(self, t):

        """Return a discrete-time signal evaluated at time values specified by
        vector t. """

        return self.evaluate(t)

    def initial_value(self):
        """Determine value at t = 0. 
        See also pre_initial_value and post_initial_value"""

        return self.subs(0)

    def pre_initial_value(self):
        """Determine value at t = 0-.
        See also initial_value and post_initial_value"""

        return self.limit(self.var, 0, dir='-')

    def post_initial_value(self):
        """Determine value at t = 0+.
        See also pre_initial_value and initial_value"""

        return self.limit(self.var, 0, dir='+')    

    def final_value(self):
        """Determine value at t = oo."""

        return self.limit(self.var, oo)

    def remove_condition(self):
        """Remove the piecewise condition from the expression.
        See also force_causal."""

        if not self.is_conditional:
            return self
        expr = self.expr
        expr = expr.args[0].args[0]
        return self.__class__(expr)

    def force_causal(self):
        """Remove the piecewise condition from the expression
        and multiply by Heaviside function.  See also remove_condition."""

        if self.is_causal:
            return self
        
        expr = self.expr
        if self.is_conditional:
            expr = expr.args[0].args[0]            
        expr = expr * Heaviside(t)
        return self.__class__(expr)        

    def convolve(self, impulseresponse, commutate=False, **assumptions):
        """Convolve self with impulse response."""

        if not isinstance(impulseresponse, TimeDomainExpression):
            raise ValueError('Expecting TimeDomainExpression for impulse response')

        f1 = self.expr
        f2 = impulseresponse.expr
        if commutate:
            f1, f2 = f2, f1
        result = Integral(f1.subs(self.var, self.var - tausym) *
                          f2.subs(self.var, tausym),
                          (tausym, -oo, oo))
        return self.__class__(result, **assumptions)

    
class TimeDomainAdmittance(TimeDomainExpression):

    """t-domain 'admittance' value."""

    units = 'siemens/s'

    def __init__(self, val, **assumptions):

        super(TimeDomainAdmittance, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = LaplaceDomainAdmittance
        self._fourier_conjugate_class = FourierDomainAdmittance


class TimeDomainImpedance(TimeDomainExpression):

    """t-domain 'impedance' value."""

    units = 'ohms/s'

    def __init__(self, val, **assumptions):

        super(TimeDomainImpedance, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = LaplaceDomainImpedance
        self._fourier_conjugate_class = FourierDomainImpedance


class TimeDomainVoltage(TimeDomainExpression):

    """t-domain voltage (units V)."""

    quantity = 'Voltage'
    units = 'V'
    superkind = 'Voltage'        

    def __init__(self, val, **assumptions):

        super(TimeDomainVoltage, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = LaplaceDomainVoltage
        self._fourier_conjugate_class = FourierDomainVoltage

    def cpt(self):
        from .oneport import V
        return V(self)

    def __mul__(self, x):
        """Multiply"""

        if isinstance(x, TimeDomainAdmittance):
            raise ValueError('Need to convolve expressions.')
        if isinstance(x, (ConstantExpression, TimeDomainExpression, symExpr, int, float, complex)):
            return super(TimeDomainVoltage, self).__mul__(x)
        self._incompatible(x, '*')        

    def __truediv__(self, x):
        """Divide"""

        if isinstance(x, TimeDomainImpedance):
            raise ValueError('Need to deconvolve expressions.')
        if isinstance(x, (ConstantExpression, TimeDomainExpression, symExpr, int, float, complex)):
            return super(TimeDomainVoltage, self).__truediv__(x)
        self._incompatible(x, '/')        

        
class TimeDomainCurrent(TimeDomainExpression):

    """t-domain current (units A)."""

    quantity = 'Current'
    units = 'A'
    superkind = 'Current'    

    def __init__(self, val, **assumptions):

        super(TimeDomainCurrent, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = LaplaceDomainCurrent
        self._fourier_conjugate_class = FourierDomainCurrent

    def cpt(self):
        from .oneport import I
        return I(self)

    def __mul__(self, x):
        """Multiply"""

        if isinstance(x, TimeDomainImpedance):
            raise ValueError('Need to convolve expressions.')
        if isinstance(x, (ConstantExpression, TimeDomainExpression, symExpr, int, float, complex)):
            return super(TimeDomainCurrent, self).__mul__(x)
        self._incompatible(x, '*')        

    def __truediv__(self, x):
        """Divide"""

        if isinstance(x, TimeDomainAdmittance):
            raise ValueError('Need to deconvolve expressions.')        
        if isinstance(x, (ConstantExpression, TimeDomainExpression, symExpr, int, float, complex)):
            return super(TimeDomainCurrent, self).__truediv__(x)
        self._incompatible(x, '/')        
        

class TimeDomainImpulseResponse(TimeDomainExpression):

    """impulse response"""

    quantity = 'Impulse response'
    units = '1/s'

    def __init__(self, val, **assumptions):

        super(TimeDomainImpulseResponse, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = LaplaceDomainTransferFunction
        self._fourier_conjugate_class = FourierDomainTransferFunction

def texpr(arg, **assumptions):
    """Create TimeDomainExpression object.  If `arg` is tsym return t"""

    if arg is tsym:
        return t
    return TimeDomainExpression(arg, **assumptions)

from .sexpr import LaplaceDomainTransferFunction, LaplaceDomainCurrent, LaplaceDomainVoltage, LaplaceDomainAdmittance, LaplaceDomainImpedance, LaplaceDomainExpression
from .fexpr import FourierDomainTransferFunction, FourierDomainCurrent, FourierDomainVoltage, FourierDomainAdmittance, FourierDomainImpedance, FourierDomainExpression
from .cexpr import ConstantExpression
from .phasor import PhasorExpression
t = TimeDomainExpression('t')
