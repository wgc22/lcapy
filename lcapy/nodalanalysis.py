"""This module performs nodal analysis.  It is primarily for showing
the equations rather than for evaluating them.

Copyright 2019-2020 Michael Hayes, UCECE

"""

from .circuitgraph import CircuitGraph
from .tmatrix import tMatrix
from .utils import equation
import sympy as sym

__all__ = ('NodalAnalysis', )


class NodalAnalysis(object):
    """
    This is an experimental class for nodal analysis.  The API
    is likely to change.

    >>> from lcapy import Circuit, NodalAnalysis
    >>> cct = Circuit('''
    ... V1 1 0 {u(t)}; down
    ... R1 1 2; right=2
    ... L1 2 3; down=2
    ... W1 0 3; right
    ... W 1 5; up
    ... W 2 6; up
    ... C1 5 6; right=2
    ...''')    

    To perform nodal analysis in the Laplace domain:

    >>> na = NodalAnalysis(cct.laplace())
    
    To display the system of equations (in matrix form) that needs to
    be solved:
    
    >>> na.equations().pprint()
    
    To display the equations found by applying KCL at each node:
    
    >>> na.nodal_equations().pprint()

    """

    def __init__(self, cct, node_prefix=''):
        """`cct` is a netlist
        `node_prefix` can be used to avoid ambiguity between
        component voltages and node voltages."""

        self.cct = cct
        self.G = CircuitGraph(cct)

        self.kind = self.cct.kind
        if self.kind == 'super':
            self.kind = 'time'

        self.node_prefix = node_prefix
        
        self._unknowns = self._make_unknowns()
        
        self._y = matrix([val for key, val in self._unknowns.items() if key != '0'])
        
        self._equations = self._make_equations()

        
    def nodes(self):

        return self.G.nodes()

    def _make_unknowns(self):

        # Determine node voltage variables.
        unknowns = ExprDict()

        # cct.node_list is sorted alphabetically
        for node in self.cct.node_list:
            if node.startswith('*'):
                continue            
            if node == '0':
                unknowns[node] = 0
            else:
                unknowns[node] = Voltage('v%s%s(t)' % (self.node_prefix, node)).select(self.kind)
        return unknowns

    def _make_equations(self):

        equations = {}
        for node in self.nodes():
            if node == '0':
                continue
            # Ignore dummy nodes
            if node.startswith('*'):
                continue

            voltage_sources = []
            for elt in self.G.connected(node):
                if elt.type == 'V':
                    voltage_sources.append(elt)

            if voltage_sources != []:
                elt = voltage_sources[0]
                n1 = self.G.node_map[elt.nodenames[0]]
                n2 = self.G.node_map[elt.nodenames[1]]

                V = elt.cpt.v_equation(0, self.kind)
                
                lhs, rhs = self._unknowns[n1], self._unknowns[n2] + V

            else:
                result = Current(0).select(self.kind)
                for elt in self.G.connected(node):
                    if len(elt.nodenames) < 2:
                        raise ValueError('Elt %s has too few nodes' % elt)
                    n1 = self.G.node_map[elt.nodenames[0]]
                    n2 = self.G.node_map[elt.nodenames[1]]
                    if node == n1:
                        pass
                    elif node == n2:
                        n1, n2 = n2, n1
                    else:
                        raise ValueError('Component %s does not have node %s' % (elt, node))
                    result += elt.cpt.i_equation(self._unknowns[n1] - self._unknowns[n2], self.kind)
                lhs, rhs = result, expr(0)

            equations[node] = (lhs, rhs)

        return equations        

    def equations_dict(self):
        """Return dictionary of equations keyed by node name."""

        equations_dict = ExprDict()
        for node, (lhs, rhs) in self._equations.items():
            equations_dict[node] = equation(lhs, rhs)

        return equations_dict
    
    def nodal_equations(self):
        """Return the equations found by applying KCL at each node.  This is a
        directory of equations keyed by the node name."""

        return self.equations_dict()

    def _analyse(self):

        if self.kind == 'time':
            raise ValueError('Cannot put time domain equations into matrix form')

        subsdict = {}
        for node, v in self._unknowns.items():
            if v == 0:
                continue
            subsdict[v.expr] = 'X_X' + node

        exprs = []
        for node, (lhs, rhs) in self._equations.items():
            lhs = lhs.subs(subsdict).expr.expand()
            rhs = rhs.subs(subsdict).expr.expand()            
            exprs.append(lhs - rhs)
            
        y = []
        for y1 in self._y:
            y.append(y1.subs(subsdict).expr);
        
        A, b = sym.linear_eq_to_matrix(exprs, *y)
        return A, b

    @property
    def A(self):
        """Return A matrix where A y = b."""

        if hasattr(self, '_A'):
            return matrix(self._A)
        self._A, self._b = self._analyse()
        return self._A

    @property
    def b(self):
        """Return b vector where A y = b."""        

        if hasattr(self, '_b'):
            return matrix(self._b)
        self._A, self._b = self._analyse()
        return self._b    

    @property
    def y(self):
        """Return y vector where A y = b."""
        return self._y
    
    def equations(self):
        """Return the equations in matrix form where A y = b."""

        A, b = self.A, self.b
        
        return expr(sym.Eq(sym.MatMul(A, self.y), b), evaluate=False)

from .expr import ExprDict, expr
from .texpr import Vt
from .voltage import Voltage
from .current import Current
from .matrix import matrix
