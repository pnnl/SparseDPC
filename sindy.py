import torch
from neuromancer.dynamics.ode import ODESystem
from library import FunctionLibrary

class SINDy(ODESystem):
    """
    Sparse Identification of Nonlinear Dynamics
    Reference: https://www.pnas.org/doi/10.1073/pnas.1517384113
    """


    def __init__(
        self,
        library,
        threshold=1e-2,
        n_out=None
    ):
        """
        :param library: (FunctionLibrary) the library of candidate functions
        :param threshold: (float) all functions with coefficients lower than this are omitted
        """
        assert isinstance(library, FunctionLibrary), "Must be valid library"

        self.n_out = n_out
        if n_out is None:
            self.n_out = library.n_features

        super().__init__(library.shape[1], self.n_out)


        self.library = library
        self.threshold = threshold
        init_coef = torch.rand((self.library.shape[0], self.n_out))
        self.coef = torch.nn.Parameter(init_coef, requires_grad=True)
        self.float()

    def ode_equations(self, x, u=None):
        """
        :param x: (torch.tensor) time series data
        """
        #assert x.ndim == 2, "Input must not be empty"
        lib_eval = None
        if u is None:
            #assert x.shape[1] == self.library.shape[1], "Must have same number of states as insize"
            lib_eval = self.library.evaluate(x)

        else:
            #assert x.shape[1] + u.shape[1] == self.library.shape[1], "Must have same number of states and inputs as library"
            lib_eval = self.library.evaluate(x,u)

        output = torch.matmul(lib_eval, self.coef)
        return output


    def __str__(self):
        """
        return: (str) a list of the linear combinations of candidate functions for each state variable
        """
        f_names = self.library.__str__()
        f_names = f_names.split(", ")
        return_str = ""

        for i in range(self.nx):
            return_str += f"dx{i}/dt = "
            for j in range(len(f_names)):
                coef = self.coef[j, i]
                if torch.abs(coef) > self.threshold:
                    func = f_names[j]
                    return_str += f"{coef:.3f}*{func} + "
            return_str = return_str[:-2]
            return_str += "\n"

        return return_str

    def set_parameters(self, new_params):
        assert self.coef.shape == new_params.shape, "New parameters must have same shape"
        assert isinstance(new_params, torch.nn.Parameter), "Must be torch.nn.Parameter"
        assert new_params.requires_grad, "Must require gradients"

        self.coef = new_params


