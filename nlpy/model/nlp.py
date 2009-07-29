# nlp.py
# Define an abstract class to represent a general
# nonlinear optimization problem.
# D. Orban, 2004.

class NLPModel:
    """
    Instances of class NLPModel represent an abstract nonlinear optimization
    problem. It features methods to evaluate the objective and constraint
    functions, and their derivatives. Instances of the general class do not
    do anything interesting; they must be subclassed and specialized.

    Initialization arguments include
     n       the number of variables (default: 0)
     m       the number of general (non bound) constraints (default: 0)
     name    the name of the model (default: 'Generic')

    They can also include keyword arguments from the following list
     x0      the initial point (default: all 0)
     pi0     the vector of initial multipliers (default: all 0)
     Lvar    the vector of lower bounds on the variables (default: all -Infinity)
     Uvar    the vector of upper bounds on the variables (default: all +Infinity)
     Lcon    the vector of lower bounds on the constraints (default: all -Infinity)
     Ucon    the vector of upper bounds on the constraints (default: all +Infinity)

    Constraints are classified into 3 classes:
     linear, nonlinear and network.
    Indices of linear    constraints are found in member lin (default: empty)
    Indices of nonlinear constraints are found in member nln (default: all)
    Indices of network   constraints are found in member net (default: empty)

    If necessary, additional arguments may be passed in kwargs.

    $Id: nlp.py 88 2008-09-29 04:43:15Z d-orban $
    """
    
    def __init__( self, n = 0, m = 0, name = 'Generic', **kwargs ):
    
        import numpy
        import math

        self.n = n          # Number of variables
        self.m = m          # Number of general constraints
        self.name = name    # Problem name

        # Initialize local value for Infinity
        self.Infinity = 1e+20
        self.negInfinity = - self.Infinity
        self.zero = 0.0
        self.one = 1.0

        # Set initial point
        if 'x0' in kwargs.keys():
            self.x0 = kwargs['x0']
        else:
            self.x0 = numpy.zeros( self.n, 'd' )

        # Set initial multipliers
        if 'pi0' in kwargs.keys():
            self.pi0 = kwargs['pi0']
        else:
            self.pi0 = numpy.zeros( self.m, 'd' )

        # Set lower bounds on variables    Lvar[i] <= x[i]  i = 1,...,n
        if 'Lvar' in kwargs.keys():
            self.Lvar = kwargs['Lvar']
        else:
            self.Lvar = self.negInfinity * numpy.ones( self.n, 'd' )

        # Set upper bounds on variables    x[i] <= Uvar[i]  i = 1,...,n
        if 'Uvar' in kwargs.keys():
            self.Uvar = kwargs['Uvar']
        else:
            self.Uvar = self.Infinity * numpy.ones( self.n, 'd' )

        # Set lower bounds on constraints  Lcon[i] <= c[i]  i = 1,...,m
        if 'Lcon' in kwargs.keys():
            self.Lcon = kwargs['Lcon']
        else:
            self.Lcon = self.negInfinity * numpy.ones( self.m, 'd' )

        # Set upper bounds on constraints  c[i] <= Ucon[i]  i = 1,...,m
        if 'Ucon' in kwargs.keys():
            self.Ucon = kwargs['Ucon']
        else:
            self.Ucon = self.Infinity * numpy.ones( self.m, 'd' )

        # Default classification of constraints
        self.lin = []                          # Linear    constraints
        self.nln = range( self.m )             # Nonlinear constraints
        self.net = []                          # Network   constraints
        self.nlin = len( self.lin )            # Number of linear constraints
        self.nnln = len( self.nln )            # Number of nonlinear constraints
        self.nnet = len( self.net )            # Number of network constraints

        # Maintain lists of indices for each type of constraints:
        self.rangeC = []    # Range constraints:       cL <= c(x) <= cU
        self.lowerC = []    # Lower bound constraints: cL <= c(x)
        self.upperC = []    # Upper bound constraints:       c(x) <= cU
        self.equalC = []    # Equality constraints:    cL  = c(x)  = cU
        self.freeC  = []    # "Free" constraints:    -inf <= c(x) <= inf

        for i in range( self.m ):
            if self.Lcon[i] > self.negInfinity and self.Ucon[i] < self.Infinity:
                if self.Lcon[i] == self.Ucon[i]:
                    self.equalC.append( i )
                else:
                    self.rangeC.append( i )
            elif self.Lcon[i] > self.negInfinity:
                self.lowerC.append( i )
            elif self.Ucon[i] < self.Infinity:
                self.upperC.append( i )
            else:
                self.freeC.append( i )
        
        self.nlowerC = len( self.lowerC )   # Number of lower bound constraints
        self.nrangeC = len( self.rangeC )   # Number of range constraints
        self.nupperC = len( self.upperC )   # Number of upper bound constraints
        self.nequalC = len( self.equalC )   # Number of equality constraints
        self.nfreeC  = len( self.freeC  )   # The rest: should be 0

        # Proceed similarly with bound constraints
        self.rangeB = []
        self.lowerB = []
        self.upperB = []
        self.fixedB = []
        self.freeB  = []

        for i in range( self.n ):
            if self.Lvar[i] > self.negInfinity and self.Uvar[i] < self.Infinity:
                if self.Lvar[i] == self.Uvar[i]:
                    self.fixedB.append( i )
                else:
                    self.rangeB.append( i )
            elif self.Lvar[i] > self.negInfinity:
                self.lowerB.append( i )
            elif self.Uvar[i] < self.Infinity:
                self.upperB.append( i )
            else:
                self.freeB.append( i )

        self.nlowerB = len( self.lowerB )
        self.nrangeB = len( self.rangeB )
        self.nupperB = len( self.upperB )
        self.nfixedB = len( self.fixedB )
        self.nfreeB  = len( self.freeB  )
        self.nbounds = self.n - self.nfreeB

        # Define default stopping tolerances
        self.stop_d = math.pow( 10.0, -6.0 )    # Dual feasibility
        self.stop_c = math.pow( 10.0, -6.0 )    # Complementarty
        self.stop_p = math.pow( 10.0, -6.0 )    # Primal feasibility

        # Initialize some counters
        self.feval = 0    # evaluations of objective  function
        self.geval = 0    #                           gradient
        self.Heval = 0    #                Lagrangian Hessian
        self.Hprod = 0    #                matrix-vector products with Hessian
        self.ceval = 0    #                constraint functions
        self.Jeval = 0    #                           gradients
        self.Jprod = 0    #                matrix-vector products with Jacobian

    def ResetCounters( self ):
        self.feval = 0
        self.geval = 0
        self.Heval = 0
        self.Hprod = 0
        self.ceval = 0
        self.Jeval = 0
        self.Jprod = 0
        return None

    # Evaluate optimality residuals
    def OptimalityResiduals( self, x, z, **kwargs ):
        return (None, None, None)

    # Decide whether optimality is attained
    def AtOptimality( self, x, z, **kwargs ):
        (d, c, p) = self.OptimalityResiduals( x, z, **kwargs )
        if d <= self.stop_d and c <= self.stop_c and p <= self.stop_p:
            return True
        return False

    # Evaluate objective function at x
    def obj( self, x, **kwargs ):
        return None

    # Evaluate objective gradient at x
    def grad( self, x, **kwargs ):
        return None
        
    # Evaluate vector of constraints at x
    def cons( self, x, **kwargs ):
        return None

    # Evaluate i-th constraint at x
    def icons( self, i, x, **kwargs ):
        return None

    # Evalutate i-th constraint gradient at x
    # Gradient is returned as a dense vector
    def igrad( self, i, x, **kwargs ):
        return None

    # Evaluate i-th constraint gradient at x
    # Gradient is returned as a sparse vector
    def sigrad( self, i, x, **kwargs ):
        return (None, None)

    # Evaluate constraints Jacobian at x
    def jac( self, x, **kwargs ):
        return None

    # Evaluate Lagrangian Hessian at (x,z)
    def hess( self, x, z, **kwargs ):
        return None

    # Evaluate matrix-vector product between
    # the Hessian of the Lagrangian and a vector
    def hprod( self, x, z, p, **kwargs ):
        return None