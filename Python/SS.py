'''
------------------------------------------------------------------------
Last updated: 3/17/2015

Calculates steady state of OLG model with S age cohorts, using simple
bin_weights and no taxes in order to be able to converge in the steady
state, in order to get initial values for later simulations

This py-file calls the following other file(s):
            income.py
            demographics.py
            tax_funcs.py
            OUTPUT/given_params.pkl
            OUTPUT/Nothing/wealth_data_moments.pkl
            OUTPUT/Nothing/labor_data_moments.pkl
            OUTPUT/Nothing/{}.pkl
                name depends on what iteration just ran
            OUTPUT/SS/d_inc_guess.pkl
                if calibrating the income tax to match the wealth tax

This py-file creates the following other file(s):
    (make sure that an OUTPUT folder exists)
            OUTPUT/Nothing/{}.pkl
                name depends on what iteration is being run
            OUTPUT/Nothing/initial_guesses_for_SS.pkl
            OUTPUT/Nothing/payroll_inputs.pkl
            OUTPUT/SSinit/ss_init.pkl
            OUTPUT/SS/Tss_var.pkl
------------------------------------------------------------------------
'''

# Packages
import numpy as np
import time
import os
import scipy.optimize as opt
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import income
from scipy import stats
import demographics
import tax_funcs as tax


'''
------------------------------------------------------------------------
Imported user given values
------------------------------------------------------------------------
S            = number of periods an individual lives
J            = number of different ability groups
T            = number of time periods until steady state is reached
bin_weights_init  = percent of each age cohort in each ability group
starting_age = age of first members of cohort
ending age   = age of the last members of cohort
E            = number of cohorts before S=1
beta         = discount factor for each age cohort
sigma        = coefficient of relative risk aversion
alpha        = capital share of income
nu_init      = contraction parameter in steady state iteration process
               representing the weight on the new distribution gamma_new
A            = total factor productivity parameter in firms' production
               function
delta        = depreciation rate of capital for each cohort
ctilde       = minimum value amount of consumption
bqtilde      = minimum bequest value
ltilde       = measure of time each individual is endowed with each
               period
eta          = Frisch elasticity of labor supply
g_y          = growth rate of technology for one cohort
TPImaxiter   = Maximum number of iterations that TPI will undergo
TPImindist   = Cut-off distance between iterations for TPI
b_ellipse    = value of b for elliptical fit of utility function
k_ellipse    = value of k for elliptical fit of utility function
omega_ellipse= value of omega for elliptical fit of utility function
slow_work    = time at which chi_n starts increasing from 1
mean_income  = mean income from IRS data file used to calibrate income tax
               (scalar)
a_tax_income = used to calibrate income tax (scalar)
b_tax_income = used to calibrate income tax (scalar)
c_tax_income = used to calibrate income tax (scalar)
d_tax_income = used to calibrate income tax (scalar)
tau_sales    = sales tax (scalar)
tau_bq       = bequest tax (scalar)
tau_lump     = lump sum tax (scalar)
tau_payroll  = payroll tax (scalar)
theta_tax    = payback value for payroll tax (scalar)
retire       = age in which individuals retire(scalar)
h_wealth     = wealth tax parameter h
p_wealth     = wealth tax parameter p
m_wealth     = wealth tax parameter m
thetas_simulation = is this the last simulation before getting
                replacement rates
scal         = value to scale the initial guesses by in order to get the
               fsolve to converge
name_of_last = name of last simulation that ran
name_of_it   = name of current simulation
------------------------------------------------------------------------
'''

# variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments.pkl", "r"))
# for key in variables:
#     globals()[key] = variables[key]

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_25.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top25 = highest_wealth_data_new
top25[2:26] = 500.0

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_50.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top50 = highest_wealth_data_new

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_70.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top70 = highest_wealth_data_new

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_80.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top80 = highest_wealth_data_new

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_90.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top90 = highest_wealth_data_new

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_99.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top99 = highest_wealth_data_new

variables = pickle.load(open("OUTPUT/Nothing/wealth_data_moments_fit_100.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]
top100 = highest_wealth_data_new



variables = pickle.load(open("OUTPUT/Nothing/labor_data_moments.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]

variables = pickle.load(open("OUTPUT/given_params.pkl", "r"))
for key in variables:
    globals()[key] = variables[key]

if os.path.isfile("OUTPUT/SS/d_inc_guess.pkl"):
    d_tax_income = pickle.load(open("OUTPUT/SS/d_inc_guess.pkl", "r"))

'''
------------------------------------------------------------------------
Generate income and demographic parameters
------------------------------------------------------------------------
e            = S x J matrix of age dependent possible working abilities
               e_s
omega        = T x S x J array of demographics
g_n          = steady state population growth rate
omega_SS     = steady state population distribution
children     = T x starting_age x J array of children demographics
surv_rate    = S x 1 array of survival rates
mort_rate    = S x 1 array of mortality rates
------------------------------------------------------------------------
'''

omega, g_n, omega_SS, children, surv_rate = demographics.get_omega(
    S, J, T, bin_weights, starting_age, ending_age, E)
e = income.get_e(S, J, starting_age, ending_age, bin_weights, omega_SS)
mort_rate = 1-surv_rate

chi_n_guess = np.array([46.72535625 , 21.90168956 , 14.10656277 , 10.48757901 ,  8.24468698
 ,  7.00965194 ,  6.35592644 ,  5.76320126 ,  5.38718148 ,  4.93179926
 ,  4.50296601 ,  4.4837601  ,  4.25729461 ,  4.06454205 ,  3.82236466
 ,  3.5283917  ,  3.43839694 ,  3.27938519 ,  3.00692176 ,  2.89741885
 ,  2.55154497 ,  2.47060168 ,  2.21750773 ,  1.99909381 ,  1.80211985
 ,  1.75644516 ,  1.67044419 ,  1.66002588 ,  1.60855856 ,  1.59476512
 ,  1.58886041 ,  1.59452484 ,  1.59950561 ,  1.59031474 ,  1.66070228
 ,  1.68054519 ,  1.8254737  ,  1.94186311 ,  1.94152742 ,  2.23550489
 ,  2.43570763 ,  3.23722229 ,  4.23217255 ,  5.06278123 ,  6.50901148
 ,  8.84724929 ,  9.65367203 , 10.68915292 , 12.29749682 , 12.0337489
 , 12.19537525 , 13.41317733 , 14.1821549  , 14.28923497 , 15.06037503
 , 16.13006283 , 16.49621336 , 16.97579295 , 17.68256811 , 18.53896513
 , 19.15229409 , 20.08270302 , 20.9051273  , 21.7728119  , 22.65410311
 , 23.4079489  , 24.40885929 , 25.24812639 , 26.23554575 , 27.07093225
 , 27.88464332 , 28.91343336 , 29.84658209 , 30.88428511 , 31.91865849
 , 33.07939554 , 34.28269955 , 35.57428502 , 36.95183753 , 38.62390064])

# chi_n_guess = np.array([49.00057044  , 23.90365341  , 17.14681801  , 11.50124121  ,  9.85755664
#   ,  8.7154879   ,  7.15767215  ,  7.34394601  ,  6.80093094  ,  6.34735901
#   ,  5.9709501   ,  5.70412058  ,  5.38934339  ,  5.16113379  ,  4.69055998
#   ,  4.59601432  ,  4.38514552  ,  4.18661524  ,  4.06472044  ,  3.90976962
#   ,  3.83179291  ,  3.61879469  ,  3.45820069  ,  3.35436721  ,  3.19234473
#   ,  3.2402056   ,  2.98682084  ,  3.00407025  ,  2.89165622  ,  2.82876018
#   ,  2.82565226  ,  3.05320397  ,  2.99272344  ,  3.94641226  ,  3.59595253
#   ,  4.53070335  ,  4.55173119  ,  4.46714411  ,  4.70800298  ,  4.63891818
#   ,  4.7195259   ,  5.07892881  ,  5.19755713  ,  4.5080705   ,  4.16051791
#   ,  3.84712716  ,  4.18776844  ,  4.42981219  ,  6.07681143  ,  7.37181048
#   ,  8.04228608  ,  9.58393307  , 10.10896949  , 10.5037945   , 11.25913451
#   , 11.94928161  , 12.06471667  , 12.2993765   , 12.67719795  , 13.03637563
#   , 13.95367841  , 13.64963561  , 14.00865863  , 14.39030832  , 14.88669406
#   , 15.97365137  , 15.73642619  , 15.77177401  , 16.15049186  , 16.35159685
#   , 17.20394299  , 16.84850293  , 17.4477147   , 17.55336631  , 17.94471645
#   , 18.36101388  , 19.19443834  , 19.16986825  , 19.88847746  , 20.09786858])



surv_rate[-1] = 0.0
mort_rate[-1] = 1


'''
------------------------------------------------------------------------
Finding the Steady State
------------------------------------------------------------------------
K_guess_init = (S-1 x J) array for the initial guess of the distribution
               of capital
L_guess_init = (S x J) array for the initial guess of the distribution
               of labor
solutions    = ((S * (S-1) * J * J) x 1) array of solutions of the
               steady state distributions of capital and labor
Kssmat       = ((S-1) x J) array of the steady state distribution of
               capital
Kssmat2      = SxJ array of capital (zeros appended at the end of
               Kssmat2)
Kssmat3      = SxJ array of capital (zeros appended at the beginning of
               Kssmat)
Kssvec       = ((S-1) x 1) vector of the steady state level of capital
               (averaged across ability types)
Kss          = steady state aggregate capital stock
K_agg        = Aggregate level of capital
Lssmat       = (S x J) array of the steady state distribution of labor
Lssvec       = (S x 1) vector of the steady state level of labor
               (averaged across ability types)
Lss          = steady state aggregate labor
Yss          = steady state aggregate output
wss          = steady state real wage
rss          = steady state real rental rate
cssmat       = SxJ array of consumption across age and ability groups
runtime      = Time needed to find the steady state (seconds)
hours        = Hours needed to find the steady state
minutes      = Minutes needed to find the steady state, less the number
               of hours
seconds      = Seconds needed to find the steady state, less the number
               of hours and minutes
------------------------------------------------------------------------
'''

# Functions and Definitions


def get_Y(K_now, L_now):
    '''
    Parameters: Aggregate capital, Aggregate labor

    Returns:    Aggregate output
    '''
    Y_now = A * (K_now ** alpha) * ((L_now) ** (1 - alpha))
    return Y_now


def get_w(Y_now, L_now):
    '''
    Parameters: Aggregate output, Aggregate labor

    Returns:    Returns to labor
    '''
    w_now = (1 - alpha) * Y_now / L_now
    return w_now


def get_r(Y_now, K_now):
    '''
    Parameters: Aggregate output, Aggregate capital

    Returns:    Returns to capital
    '''
    r_now = (alpha * Y_now / K_now) - delta
    return r_now


def get_L(e, n):
    '''
    Parameters: e, n

    Returns:    Aggregate labor
    '''
    L_now = np.sum(e * omega_SS * n)
    return L_now


def MUc(c):
    '''
    Parameters: Consumption

    Returns:    Marginal Utility of Consumption
    '''
    output = c**(-sigma)
    return output


def MUl(n, chi_n):
    '''
    Parameters: Labor

    Returns:    Marginal Utility of Labor
    '''
    deriv = b_ellipse * (1/ltilde) * ((1 - (n / ltilde) ** upsilon) ** (
        (1/upsilon)-1)) * (n / ltilde) ** (upsilon - 1)
    output = chi_n.reshape(S, 1) * deriv
    return output


def MUb(chi_b, bq):
    '''
    Parameters: Intentional bequests

    Returns:    Marginal Utility of Bequest
    '''
    output = chi_b[-1, :].reshape(1, J) * (bq ** (-sigma))
    return output


def get_cons(r, k1, w, e, lab, bq, bins, k2, gy, tax):
    '''
    Parameters: rental rate, capital stock (t-1), wage, e, labor stock,
                bequests, bin_weights, capital stock (t), growth rate y, taxes

    Returns:    Consumption
    '''
    cons = (1 + r)*k1 + w*e*lab + bq / bins - k2*np.exp(gy) - tax
    return cons


def Euler1(w, r, e, L_guess, K1, K2, K3, B, factor, taulump, chi_b):
    '''
    Parameters:
        w        = wage rate (scalar)
        r        = rental rate (scalar)
        e        = distribution of abilities (SxJ array)
        L_guess  = distribution of labor (SxJ array)
        K1       = distribution of capital in period t ((S-1) x J array)
        K2       = distribution of capital in period t+1 ((S-1) x J array)
        K3       = distribution of capital in period t+2 ((S-1) x J array)
        B        = distribution of incidental bequests (1 x J array)
        factor   = scaling value to make average income match data
        taulump  = lump sum transfer from the government to the households
        xi       = coefficient of relative risk aversion
        chi_b    = discount factor of savings

    Returns:
        Value of Euler error.
    '''
    B_euler = B.reshape(1, J)
    tax1 = tax.total_taxes_SS(r, K1, w, e[:-1, :], L_guess[:-1, :], B_euler, bin_weights, factor, taulump)
    tax2 = tax.total_taxes_SS2(r, K2, w, e[1:, :], L_guess[1:, :], B_euler, bin_weights, factor, taulump)
    cons1 = get_cons(r, K1, w, e[:-1, :], L_guess[:-1, :], B_euler, bin_weights, K2, g_y, tax1)
    cons2 = get_cons(r, K2, w, e[1:, :], L_guess[1:, :], B_euler, bin_weights, K3, g_y, tax2)
    income = (r * K2 + w * e[1:, :] * L_guess[1:, :]) * factor
    deriv = (
        1 + r*(1-tax.tau_income(r, K1, w, e[1:, :], L_guess[1:, :], factor)-tax.tau_income_deriv(
            r, K1, w, e[1:, :], L_guess[1:, :], factor)*income)-tax.tau_w_prime(K2)*K2-tax.tau_wealth(K2))
    bequest_ut = (1-surv_rate[:-1].reshape(S-1, 1)) * np.exp(-sigma * g_y) * chi_b[:-1].reshape(S-1, J) * K2 ** (-sigma)
    euler = MUc(cons1) - beta * surv_rate[:-1].reshape(S-1, 1) * deriv * MUc(
        cons2) * np.exp(-sigma * g_y) - bequest_ut
    return euler


def Euler2(w, r, e, L_guess, K1_2, K2_2, B, factor, taulump, chi_n):
    '''
    Parameters:
        w        = wage rate (scalar)
        r        = rental rate (scalar)
        e        = distribution of abilities (SxJ array)
        L_guess  = distribution of labor (SxJ array)
        K1_2     = distribution of capital in period t (S x J array)
        K2_2     = distribution of capital in period t+1 (S x J array)
        B        = distribution of incidental bequests (1 x J array)
        factor   = scaling value to make average income match data
        taulump  = lump sum transfer from the government to the households

    Returns:
        Value of Euler error.
    '''
    B = B.reshape(1, J)
    tax1 = tax.total_taxes_SS(r, K1_2, w, e, L_guess, B, bin_weights, factor, taulump)
    cons = get_cons(r, K1_2, w, e, L_guess, B, bin_weights, K2_2, g_y, tax1)
    income = (r * K1_2 + w * e * L_guess) * factor
    deriv = 1 - tau_payroll - tax.tau_income(r, K1_2, w, e, L_guess, factor) - tax.tau_income_deriv(
        r, K1_2, w, e, L_guess, factor) * income
    euler = MUc(cons) * w * deriv * e - MUl(L_guess, chi_n)
    return euler


def Euler3(w, r, e, L_guess, K_guess, B, factor, chi_b, taulump):
    '''
    Parameters:
        w        = wage rate (scalar)
        r        = rental rate (scalar)
        e        = distribution of abilities (SxJ array)
        L_guess  = distribution of labor (SxJ array)
        K_guess  = distribution of capital in period t (S-1 x J array)
        B        = distribution of incidental bequests (1 x J array)
        factor   = scaling value to make average income match data
        chi_b    = discount factor of savings
        taulump  = lump sum transfer from the government to the households

    Returns:
        Value of Euler error.
    '''
    B = B.reshape(1, J)
    tax1 = tax.total_taxes_eul3_SS(r, K_guess[-2, :], w, e[-1, :], L_guess[-1, :], B, bin_weights, factor, taulump)
    cons = get_cons(r, K_guess[-2, :], w, e[-1, :], L_guess[-1, :], B, bin_weights, K_guess[-1, :], g_y, tax1)
    euler = MUc(cons) - np.exp(-sigma * g_y) * MUb(
        chi_b, K_guess[-1, :])
    return euler


def perc_dif_func(simul, data):
    '''
    Used to calculate the absolute percent difference between the data and
        simulated data
    '''
    frac = (simul - data)/data
    output = np.abs(frac)
    return output


def Steady_State(guesses, params):
    '''
    Parameters: Steady state distribution of capital guess as array
                size 2*S*J

    Returns:    Array of 2*S*J Euler equation errors
    '''
    chi_b = np.tile(np.array(params[:J]).reshape(1, J), (S, 1))
    chi_n = np.array(params[J:])
    K_guess = guesses[0: S * J].reshape((S, J))
    B = (K_guess * omega_SS * mort_rate.reshape(S, 1)).sum(0)
    K = (omega_SS * K_guess).sum()
    L_guess = guesses[S * J:-1].reshape((S, J))
    L = get_L(e, L_guess)
    Y = get_Y(K, L)
    w = get_w(Y, L)
    r = get_r(Y, K)
    BQ = (1 + r) * B
    K1 = np.array(list(np.zeros(J).reshape(1, J)) + list(K_guess[:-2, :]))
    K2 = K_guess[:-1, :]
    K3 = K_guess[1:, :]
    K1_2 = np.array(list(np.zeros(J).reshape(1, J)) + list(K_guess[:-1, :]))
    K2_2 = K_guess
    factor = guesses[-1]
    taulump = tax.tax_lump(r, K1_2, w, e, L_guess, BQ, bin_weights, factor, omega_SS)
    error1 = Euler1(w, r, e, L_guess, K1, K2, K3, BQ, factor, taulump, chi_b)
    error2 = Euler2(w, r, e, L_guess, K1_2, K2_2, BQ, factor, taulump, chi_n)
    error3 = Euler3(w, r, e, L_guess, K_guess, BQ, factor, chi_b, taulump)
    avI = ((r * K1_2 + w * e * L_guess) * omega_SS).sum()
    error4 = [mean_income - factor * avI]
    # Check and punish constraint violations
    mask1 = L_guess < 0
    error2[mask1] += 1e9
    mask2 = L_guess > ltilde
    error2[mask2] += 1e9
    if K_guess.sum() <= 0:
        error1 += 1e9
    tax1 = tax.total_taxes_SS(r, K1_2, w, e, L_guess, BQ, bin_weights, factor, taulump)
    cons = get_cons(r, K1_2, w, e, L_guess, BQ.reshape(1, J), bin_weights, K2_2, g_y, tax1)
    mask3 = cons < 0
    error2[mask3] += 1e9
    mask4 = K_guess[:-1] <= 0
    error1[mask4] += 1e9
    # print np.abs(np.array(list(error1.flatten()) + list(
    #     error2.flatten()) + list(error3.flatten()) + error4)).max()
    return list(error1.flatten()) + list(
        error2.flatten()) + list(error3.flatten()) + error4


def borrowing_constraints(K_dist, w, r, e, n, BQ):
    '''
    Parameters:
        K_dist = Distribution of capital ((S-1)xJ array)
        w      = wage rate (scalar)
        r      = rental rate (scalar)
        e      = distribution of abilities (SxJ array)
        n      = distribution of labor (SxJ array)
        BQ     = bequests

    Returns:
        False value if all the borrowing constraints are met, True
            if there are violations.
    '''
    b_min = np.zeros((S-1, J))
    b_min[-1, :] = (ctilde + bqtilde - w * e[S-1, :] * ltilde - BQ.reshape(
        1, J) / bin_weights) / (1 + r)
    for i in xrange(S-2):
        b_min[-(i+2), :] = (ctilde + np.exp(g_y) * b_min[-(i+1), :] - w * e[
            -(i+2), :] * ltilde - BQ.reshape(1, J) / bin_weights) / (1 + r)
    difference = K_dist - b_min
    if (difference < 0).any():
        return True
    else:
        return False


def constraint_checker(Kssmat, Lssmat, wss, rss, e, cssmat, BQ):
    '''
    Parameters:
        Kssmat = steady state distribution of capital ((S-1)xJ array)
        Lssmat = steady state distribution of labor (SxJ array)
        wss    = steady state wage rate (scalar)
        rss    = steady state rental rate (scalar)
        e      = distribution of abilities (SxJ array)
        cssmat = steady state distribution of consumption (SxJ array)
        BQ     = bequests

    Created Variables:
        flag1 = False if all borrowing constraints are met, true
               otherwise.
        flag2 = False if all labor constraints are met, true otherwise

    Returns:
        # Prints warnings for violations of capital, labor, and
            consumption constraints.
    '''
    # print 'Checking constraints on capital, labor, and consumption.'
    flag1 = False
    if Kssmat.sum() <= 0:
        print '\tWARNING: Aggregate capital is less than or equal to zero.'
        flag1 = True
    if borrowing_constraints(Kssmat, wss, rss, e, Lssmat, BQ) is True:
        print '\tWARNING: Borrowing constraints have been violated.'
        flag1 = True
    if flag1 is False:
        print '\tThere were no violations of the borrowing constraints.'
    flag2 = False
    if (Lssmat < 0).any():
        print '\tWARNING: Labor supply violates nonnegativity constraints.'
        flag2 = True
    if (Lssmat > ltilde).any():
        print '\tWARNING: Labor suppy violates the ltilde constraint.'
    if flag2 is False:
        print '\tThere were no violations of the constraints on labor supply.'
    if (cssmat < 0).any():
        print '\tWARNING: Consumption volates nonnegativity constraints.'
    else:
        print '\tThere were no violations of the constraints on consumption.'


def func_to_min(bq_guesses_init, other_guesses_init):
    '''
    Parameters:
        bq_guesses_init = guesses for chi_b
        other_guesses_init = guesses for the distribution of capital and labor
                            stock, and factor value

    Returns:
        The max absolute deviation between the actual and simulated
            wealth moments
    '''
    print bq_guesses_init
    Steady_State_X = lambda x: Steady_State(x, bq_guesses_init)

    variables = pickle.load(open("OUTPUT/Nothing/{}.pkl".format(name_of_last), "r"))
    for key in variables:
        globals()[key+'_pre'] = variables[key]
    solutions = opt.fsolve(Steady_State_X, solutions_pre, xtol=1e-13)
    K_guess = solutions[0: S * J].reshape((S, J))
    K2 = K_guess[:-1, :]
    factor = solutions[-1]
    # Wealth Calibration Euler
    p25_sim = K2[:, 0] * factor
    p50_sim = K2[:, 1] * factor
    p70_sim = K2[:, 2] * factor
    p80_sim = K2[:, 3] * factor
    p90_sim = K2[:, 4] * factor
    p99_sim = K2[:, 5] * factor
    p100_sim = K2[:, 6] * factor
    bq_perc_diff_25 = [perc_dif_func(np.mean(p25_sim[:24]), np.mean(top25[2:26]))] + [perc_dif_func(np.mean(p25_sim[24:45]), np.mean(top25[26:47]))]
    bq_perc_diff_50 = [perc_dif_func(np.mean(p50_sim[:24]), np.mean(top50[2:26]))] + [perc_dif_func(np.mean(p50_sim[24:45]), np.mean(top50[26:47]))]
    bq_perc_diff_70 = [perc_dif_func(np.mean(p70_sim[:24]), np.mean(top70[2:26]))] + [perc_dif_func(np.mean(p70_sim[24:45]), np.mean(top70[26:47]))]
    bq_perc_diff_80 = [perc_dif_func(np.mean(p80_sim[:24]), np.mean(top80[2:26]))] + [perc_dif_func(np.mean(p80_sim[24:45]), np.mean(top80[26:47]))]
    bq_perc_diff_90 = [perc_dif_func(np.mean(p90_sim[:24]), np.mean(top90[2:26]))] + [perc_dif_func(np.mean(p90_sim[24:45]), np.mean(top90[26:47]))]
    bq_perc_diff_99 = [perc_dif_func(np.mean(p99_sim[:24]), np.mean(top99[2:26]))] + [perc_dif_func(np.mean(p99_sim[24:45]), np.mean(top99[26:47]))]
    bq_perc_diff_100 = [perc_dif_func(np.mean(p100_sim[:24]), np.mean(top100[2:26]))] + [perc_dif_func(np.mean(p100_sim[24:45]), np.mean(top100[26:47]))]
    error5 = bq_perc_diff_25 + bq_perc_diff_50 + bq_perc_diff_70 + bq_perc_diff_80 + bq_perc_diff_90 + bq_perc_diff_99 + bq_perc_diff_100
    print error5
    # labor calibration euler
    labor_sim = ((solutions[S*J:2*S*J]).reshape(S, J)*bin_weights.reshape(1, J)).sum(axis=1)
    error6 = list(perc_dif_func(labor_sim, labor_dist_data))
    # combine eulers
    output = np.array(error5 + error6)
    fsolve_no_converg = np.abs(Steady_State_X(solutions)).max()
    if np.isnan(fsolve_no_converg):
        fsolve_no_converg = 1e6
    if fsolve_no_converg > 1e-4:
        output += 1e9
    else:
        var_names = ['solutions']
        dictionary = {}
        for key in var_names:
            dictionary[key] = locals()[key]
        pickle.dump(dictionary, open("OUTPUT/Nothing/{}.pkl".format(name_of_last), "w"))
    if (bq_guesses_init <= 0.0).any():
        output += 1e9
    weighting_mat = np.eye(2*J + S)
    # weighting_mat[10:10] = 10.0
    # weighting_mat[11:11] = 10.0
    # weighting_mat[12:12] = 10.0
    # weighting_mat[13:13] = 10.0
    scaling_val = 100.0
    value = np.dot(scaling_val * np.dot(output.reshape(1, 2*J+S), weighting_mat), scaling_val * output.reshape(2*J+S, 1))
    print value.sum()
    return value.sum()

starttime = time.time()
if name_of_last != 'none':
    variables = pickle.load(open("OUTPUT/Nothing/{}.pkl".format(name_of_last), "r"))
    for key in variables:
        globals()[key] = variables[key]
    guesses = list((solutions[:S*J].reshape(S, J) * scal).flatten()) + list(
        solutions[S*J:-1].reshape(S, J).flatten()) + [solutions[-1]]
else:
    K_guess_init = np.ones((S, J)) * .01
    L_guess_init = np.ones((S, J)) * .99 * ltilde
    Kg = (omega_SS * K_guess_init).sum()
    Lg = get_L(e, L_guess_init)
    Yg = get_Y(Kg, Lg)
    wguess = get_w(Yg, Lg)
    rguess = get_r(Yg, Kg)
    avIguess = ((rguess * K_guess_init + wguess * e * L_guess_init) * omega_SS).sum()
    factor_guess = [mean_income / avIguess]
    guesses = list(K_guess_init.flatten()) + list(L_guess_init.flatten()) + factor_guess




if 'final_bq_params' in globals() and chi_b_scaler is False:
    bq_guesses = final_bq_params
else:
    bq_guesses = np.ones(S+J)
    bq_guesses[0:J] = np.array([5, 10, 90, 250, 250, 250, 250]) + chi_b_scal
    print 'Chi_b:', bq_guesses[0:J]
    bq_guesses[J:] = chi_n_guess
    bq_guesses = list(bq_guesses)
func_to_min_X = lambda x: func_to_min(x, guesses)

bnds = tuple([(1e-6, None)] * (S + J))

if thetas_simulation:
    final_bq_params = opt.minimize(func_to_min_X, bq_guesses, method='TNC', tol=1e-6, bounds=bnds).x
    print 'The final bequest parameter values:', final_bq_params
else:
    final_bq_params = bq_guesses
Steady_State_X2 = lambda x: Steady_State(x, final_bq_params)
if 'solutions_pre' in globals():
    solutions = opt.fsolve(Steady_State_X2, solutions_pre, xtol=1e-13)
    print np.array(Steady_State_X2(solutions)).max()
else:
    solutions = opt.fsolve(Steady_State_X2, guesses, xtol=1e-13)
    print np.array(Steady_State_X2(solutions)).max()

#Calculate the fits
K_seefit = solutions[0: S * J].reshape((S, J))
K_see_fit = K_seefit[:-1, :]
factor_see_fit = solutions[-1]
# Wealth Calibration Euler
p25_sim = K_see_fit[:, 0] * factor_see_fit
p50_sim = K_see_fit[:, 1] * factor_see_fit
p70_sim = K_see_fit[:, 2] * factor_see_fit
p80_sim = K_see_fit[:, 3] * factor_see_fit
p90_sim = K_see_fit[:, 4] * factor_see_fit
p99_sim = K_see_fit[:, 5] * factor_see_fit
p100_sim = K_see_fit[:, 6] * factor_see_fit
bq_perc_diff_25 = [perc_dif_func(np.mean(p25_sim[:24]), np.mean(top25[2:26]))] + [perc_dif_func(np.mean(p25_sim[24:45]), np.mean(top25[26:47]))]
bq_perc_diff_50 = [perc_dif_func(np.mean(p50_sim[:24]), np.mean(top50[2:26]))] + [perc_dif_func(np.mean(p50_sim[24:45]), np.mean(top50[26:47]))]
bq_perc_diff_70 = [perc_dif_func(np.mean(p70_sim[:24]), np.mean(top70[2:26]))] + [perc_dif_func(np.mean(p70_sim[24:45]), np.mean(top70[26:47]))]
bq_perc_diff_80 = [perc_dif_func(np.mean(p80_sim[:24]), np.mean(top80[2:26]))] + [perc_dif_func(np.mean(p80_sim[24:45]), np.mean(top80[26:47]))]
bq_perc_diff_90 = [perc_dif_func(np.mean(p90_sim[:24]), np.mean(top90[2:26]))] + [perc_dif_func(np.mean(p90_sim[24:45]), np.mean(top90[26:47]))]
bq_perc_diff_99 = [perc_dif_func(np.mean(p99_sim[:24]), np.mean(top99[2:26]))] + [perc_dif_func(np.mean(p99_sim[24:45]), np.mean(top99[26:47]))]
bq_perc_diff_100 = [perc_dif_func(np.mean(p100_sim[:24]), np.mean(top100[2:26]))] + [perc_dif_func(np.mean(p100_sim[24:45]), np.mean(top100[26:47]))]
chi_fits = bq_perc_diff_25 + bq_perc_diff_50 + bq_perc_diff_70 + bq_perc_diff_80 + bq_perc_diff_90 + bq_perc_diff_99 + bq_perc_diff_100

if os.path.isfile("OUTPUT/Nothing/chi_b_fits.pkl"):
    variables = pickle.load(open("OUTPUT/Nothing/chi_b_fits.pkl", "r"))
    for key in variables:
        globals()[key] = variables[key]
    chi_fits_old = chi_fits_new
else:
    chi_fits_old = np.copy(chi_fits)
chi_fits_new = np.copy(chi_fits)
chi_b_vals_for_fit = bq_guesses[0:J]
var_names = ['chi_fits_old', 'chi_fits_new', 'chi_b_vals_for_fit']
dictionary = {}
for key in var_names:
    dictionary[key] = globals()[key]
pickle.dump(dictionary, open("OUTPUT/Nothing/chi_b_fits.pkl", "w"))

# Save the solutions of SS
if thetas_simulation is False:
    var_names = ['solutions', 'final_bq_params']
    dictionary = {}
    for key in var_names:
        dictionary[key] = globals()[key]
    pickle.dump(dictionary, open("OUTPUT/Nothing/{}.pkl".format(name_of_it), "w"))
else:
    var_names = ['solutions', 'final_bq_params']
    dictionary = {}
    for key in var_names:
        dictionary[key] = globals()[key]
    pickle.dump(dictionary, open("OUTPUT/Nothing/initial_guesses_for_SS.pkl", "w"))
if thetas_simulation is True or 'SS_initial_run' in globals():
    runtime = time.time() - starttime
    hours = runtime / 3600
    minutes = (runtime / 60) % 60
    seconds = runtime % 60
    Kssmat = solutions[0:(S-1) * J].reshape(S-1, J)
    BQ = solutions[(S-1)*J:S*J]
    Bss = (np.array(list(Kssmat) + list(BQ.reshape(1, J))).reshape(
        S, J) * omega_SS * mort_rate.reshape(S, 1)).sum(0)
    Kssmat2 = np.array(list(np.zeros(J).reshape(1, J)) + list(Kssmat))
    Kssmat3 = np.array(list(Kssmat) + list(BQ.reshape(1, J)))

    Kssvec = Kssmat.sum(1)
    Kss = (omega_SS[:-1, :] * Kssmat).sum() + (omega_SS[-1, :]*BQ).sum()
    Kssavg = Kssvec.mean()
    Kssvec = np.array([0]+list(Kssvec))
    Lssmat = solutions[S * J:-1].reshape(S, J)
    Lssvec = Lssmat.sum(1)
    Lss = get_L(e, Lssmat)
    Lssavg = Lssvec.mean()
    Yss = get_Y(Kss, Lss)
    wss = get_w(Yss, Lss)
    rss = get_r(Yss, Kss)
    k1_2 = np.array(list(np.zeros(J).reshape((1, J))) + list(Kssmat))
    factor_ss = solutions[-1]
    B = Bss * (1+rss)
    Tss = tax.tax_lump(rss, Kssmat2, wss, e, Lssmat, B, bin_weights, factor_ss, omega_SS)
    taxss = tax.total_taxes_SS(rss, Kssmat2, wss, e, Lssmat, B, bin_weights, factor_ss, Tss)
    cssmat = get_cons(rss, Kssmat2, wss, e, Lssmat, (1+rss)*B.reshape(1, J), bin_weights.reshape(1, J), Kssmat3, g_y, taxss)

    constraint_checker(Kssmat, Lssmat, wss, rss, e, cssmat, BQ)

    '''
    ------------------------------------------------------------------------
    Generate variables for graphs
    ------------------------------------------------------------------------
    k1          = (S-1)xJ array of Kssmat in period t-1
    k2          = copy of Kssmat
    k3          = (S-1)xJ array of Kssmat in period t+1
    k1_2        = SxJ array of Kssmat in period t
    k2_2        = SxJ array of Kssmat in period t+1
    euler1      = euler errors from first euler equation
    euler2      = euler errors from second euler equation
    euler3      = euler errors from third euler equation
    ------------------------------------------------------------------------
    '''
    k1 = np.array(list(np.zeros(J).reshape((1, J))) + list(Kssmat[:-1, :]))
    k2 = Kssmat
    k3 = np.array(list(Kssmat[1:, :]) + list(BQ.reshape(1, J)))
    k1_2 = np.array(list(np.zeros(J).reshape((1, J))) + list(Kssmat))
    k2_2 = np.array(list(Kssmat) + list(BQ.reshape(1, J)))

    K_eul3 = np.zeros((S, J))
    K_eul3[:S-1, :] = Kssmat
    K_eul3[-1, :] = BQ
    chi_b = np.tile(final_bq_params[:J].reshape(1, J), (S, 1))
    chi_n = np.array(final_bq_params[J:])
    euler1 = Euler1(wss, rss, e, Lssmat, k1, k2, k3, B, factor_ss, Tss, chi_b)
    euler2 = Euler2(wss, rss, e, Lssmat, k1_2, k2_2, B, factor_ss, Tss, chi_n)
    euler3 = Euler3(wss, rss, e, Lssmat, K_eul3, B, factor_ss, chi_b, Tss)

    '''
    ------------------------------------------------------------------------
    Save variables/values so they can be used in other modules
    ------------------------------------------------------------------------
    '''
    if 'thetas_simulation' in globals() and thetas_simulation is True:
        Kssmat_init = np.array(list(Kssmat) + list(BQ.reshape(1, J)))
        Lssmat_init = Lssmat
        var_names = ['retire', 'Lssmat_init', 'wss', 'factor_ss', 'e',
                     'J', 'omega_SS']
        dictionary = {}
        for key in var_names:
            dictionary[key] = globals()[key]
        pickle.dump(dictionary, open("OUTPUT/Nothing/payroll_inputs.pkl", "w"))
    if 'SS_initial_run' in globals():
        if SS_initial_run is True:
            Kssmat_init = np.array(list(Kssmat) + list(BQ.reshape(1, J)))
            Lssmat_init = Lssmat

            var_names = ['Kssmat_init', 'Lssmat_init']
            dictionary = {}
            for key in var_names:
                dictionary[key] = globals()[key]
            pickle.dump(dictionary, open("OUTPUT/SSinit/ss_init_tpi.pkl", "w"))

            var_names = ['S', 'beta', 'sigma', 'alpha', 'nu', 'A', 'delta', 'e', 'E',
                         'J', 'Kss', 'Kssvec', 'Kssmat', 'Lss', 'Lssvec', 'Lssmat',
                         'Yss', 'wss', 'rss', 'runtime', 'hours', 'minutes', 'omega',
                         'seconds', 'chi_n', 'chi_b', 'ltilde', 'ctilde', 'T',
                         'g_n', 'g_y', 'omega_SS', 'TPImaxiter', 'TPImindist', 'BQ',
                         'children', 'surv_rate', 'mort_rate', 'Bss', 'bin_weights',
                         'bqtilde', 'b_ellipse', 'k_ellipse', 'upsilon',
                         'factor_ss',  'a_tax_income', 'b_tax_income',
                         'c_tax_income', 'd_tax_income', 'tau_sales', 'tau_payroll',
                         'tau_bq', 'tau_lump', 'theta_tax', 'retire',
                         'mean_income', 'Kssavg', 'Kssmat2', 'Lssavg', 'cssmat',
                         'starting_age',
                         'ending_age', 'Tss', 'euler1', 'euler2', 'euler3',
                         'h_wealth', 'p_wealth', 'm_wealth']
            dictionary = {}
            for key in var_names:
                dictionary[key] = globals()[key]
            pickle.dump(dictionary, open("OUTPUT/SSinit/ss_init.pkl", "w"))
        else:
            var_names = ['S', 'beta', 'sigma', 'alpha', 'nu', 'A', 'delta', 'e', 'E',
                         'J', 'Kss', 'Kssvec', 'Kssmat', 'Lss', 'Lssvec', 'Lssmat',
                         'Yss', 'wss', 'rss', 'runtime', 'hours', 'minutes', 'omega',
                         'seconds', 'chi_n', 'chi_b', 'ltilde', 'ctilde', 'T',
                         'g_n', 'g_y', 'omega_SS', 'TPImaxiter', 'TPImindist', 'BQ',
                         'children', 'surv_rate', 'mort_rate', 'Bss', 'bin_weights',
                         'bqtilde', 'b_ellipse', 'k_ellipse', 'upsilon',
                         'factor_ss',  'a_tax_income', 'b_tax_income',
                         'c_tax_income', 'd_tax_income', 'tau_sales', 'tau_payroll',
                         'tau_bq', 'tau_lump', 'theta_tax', 'retire',
                         'mean_income', 'Kssavg', 'Kssmat2', 'Lssavg', 'cssmat',
                         'starting_age',
                         'ending_age', 'euler1', 'euler2', 'euler3', 'Tss',
                         'h_wealth', 'p_wealth', 'm_wealth']
            dictionary = {}
            for key in var_names:
                dictionary[key] = globals()[key]
            pickle.dump(dictionary, open("OUTPUT/SS/ss_vars.pkl", "w"))
            pickle.dump(Tss, open("OUTPUT/SS/Tss_var.pkl", "w"))
