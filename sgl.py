# -*- coding: utf-8 -*-
"""
Routines for solving the 1-d time-independant schrodinger equation

@author: Mirco Hellwig, Joshua Schmidt
"""
import numpy as np
import scipy.interpolate
import scipy.linalg
import iomodul


def interpolate_potential(para):
    """
    Interpolates the potential using 3 different methods: linear, natural cubic
    splines and polynomial fit, and calls the corresponding write function

        Args:
            para:dictionary, written by iomodul.read_schrodinger_inp(),
                 containing all relevant parameters

        Returns:
            potential: array with all potential values V(x)
    """
    x_points = para['interpolation_points_x']
    y_points = para['interpolation_points_y']
    xaxis = np.linspace(para['xMin'], para['xMax'], para['nPoints'])
    if para['interpolation_type'] == 'linear':
        interpolation_fun = scipy.interpolate.interp1d(x_points, y_points)
    elif para['interpolation_type'] == 'cspline':
        interpolation_fun = scipy.interpolate.CubicSpline(x_points, y_points, bc_type='natural')
    elif para['interpolation_type'] == 'polynomial':
        fun_args = np.polyfit(x_points, y_points,
                              para['interpolation_points_number']-1)
        interpolation_fun = np.poly1d(fun_args)
    potential = interpolation_fun(xaxis)
    iomodul.write_potential(xaxis, potential, para['directory'])
    return potential


def _write_hamiltonian(para):
    potential = interpolate_potential(para)
    delta = np.abs(para['xMax']-para['xMin'])/para['nPoints']
    para['Delta'] = delta
    aa = 1/(para['mass']*delta**2)
    hamiltonian_diag = aa+potential
    hamiltonian_offdiag = -aa/2*np.ones(para['nPoints']-1)
    return hamiltonian_diag, hamiltonian_offdiag


def _norm_eigenvectors(eigenvectors, para):
    for ii in range(np.size(eigenvectors[0])):
        eigenvector_norm = para['Delta']*sum(np.abs(eigenvectors[1:-1, ii])**2)
        eigenvectors[:, ii] = eigenvectors[:, ii]/np.sqrt(eigenvector_norm)
    return eigenvectors


def expectation_values(para, eigenvectors):
    """
    Calculating expectation values of position operator and position uncertainty

        Args:
            para: dictionary, written by iomodul.read_schrodinger_inp(), \
                  containing all relevant parameters
            eigenvectors: eigenvectors of the hamiltonian, given by \
                          solve_hamiltonian()

        Returns:
            expval: array with the expectation values of the position operator \
                    for each eigenvector
            uncertainty: corresponding position uncertainty
    """
    expval = np.zeros(np.size(eigenvectors[0]))
    expval_squared = np.zeros(np.size(eigenvectors[0]))
    uncertainty = np.zeros(np.size(eigenvectors[0]))
    delta = para['Delta']
    x_i = np.linspace(para['xMin']+delta, para['xMax']-delta, para['nPoints']-2)
    for ii in range(np.size(eigenvectors[0])):
        expval[ii] = delta*np.sum(eigenvectors[1:-1, ii]**2*x_i)
        expval_squared[ii] = delta*np.sum(eigenvectors[1:-1, ii]**2*x_i**2)
        uncertainty[ii] = np.sqrt(expval_squared[ii]-expval[ii]**2)
    iomodul.write_expectation_values(expval, uncertainty, para['directory'])


def solve_hamiltonian(para):
    """
    Solves the 1-d SGL on interpolated potential

        Args:
            para: dictionary, written by iomodul.read_schrodinger_inp(),
                  containing all relevant parameters

        Returns:
            eigenvalues:  Array with the selected eigenvalues
            eigenvectors: linewise the corresponding, normed eigenvectors
    """
    hamiltonian_diag, hamiltonian_offdiag = _write_hamiltonian(para)
    # first and last eigenvalue -1 because python arrays start at 0, human ones at 1
    eigenvalues, eigenvectors = scipy.linalg.eigh_tridiagonal(hamiltonian_diag,
                                                              hamiltonian_offdiag,
                                                              False, 'i',
                                                              (para['first_eigenvalue']-1,
                                                               para['last_eigenvalue']-1))
    eigenvectors = _norm_eigenvectors(eigenvectors, para)
    iomodul.write_eigenvalues(eigenvalues, para['directory'])
    xaxis = np.linspace(para['xMin'], para['xMax'], para['nPoints'])
    iomodul.write_eigenvectors(eigenvectors, xaxis, para['directory'])
    return eigenvalues, eigenvectors
