"""Synthetic identification exercise; NOT measured hardware or vehicle validation.

Run with Python 3, numpy and scipy. Writes two experiment CSVs, explorer.json,
summary.json and verification/correlation/audit.json relative to this stage.
Calibration fits only the first experiment. The second remains held out.
The nonlinear synthetic generator and linear fitted model intentionally differ.
"""
from pathlib import Path
import csv
import hashlib
import json
import time
import numpy as np
from scipy.optimize import least_squares

B = Path(__file__).resolve().parents[2]
R = B / 'results/correlation'
V = B / 'verification/correlation'
R.mkdir(parents=True, exist_ok=True)
V.mkdir(parents=True, exist_ok=True)
TIME = np.arange(0., 3600.1, 10.)
TRUTH = np.array([3.5, 2.8, 260., 1200.])
INITIAL = np.array([2., 4., 400., 800.])
NAMES = ['component_to_plate_G', 'plate_to_boundary_G', 'component_C', 'plate_C']
UNITS = ['W/K', 'W/K', 'J/K', 'J/K']


def conditions(t, experiment):
    if experiment == 'calibration':
        p = np.select([t < 300, t < 1200, t < 1800, t < 2400], [20., 80., 10., 50.], 0.)
        ta = np.zeros_like(np.asarray(t)) + 20.
    else:
        p = np.select([t < 500, t < 1100, t < 2000, t < 2800], [15., 65., 35., 75.], 5.)
        ta = 17. + 3. * np.sin(2 * np.pi * np.asarray(t) / 3600.)
    return np.asarray(p), np.asarray(ta)


def generate(experiment, dt=.5):
    # Integrate temperature and boundary heat independently of the fitted model.
    y = np.array([20., 20., 0., 0.])
    result = [y.copy()]
    for k in range(int(3600 / dt)):
        t = k * dt
        # Avoid an interval's ending discontinuity entering the earlier pulse.
        def rhs(x, tt):
            p, ta = conditions(min(tt, t + dt - 1e-9), experiment)
            g = TRUTH[0] * (1 + .0015 * max(0., (x[0] + x[1]) / 2 - float(ta)))
            qc = g * (x[0] - x[1])
            qb = TRUTH[1] * (x[1] - float(ta))
            return np.array([(float(p) - qc) / TRUTH[2], (qc - qb) / TRUTH[3], float(p), qb])
        a = rhs(y, t)
        b = rhs(y + dt*a/2, t+dt/2)
        c = rhs(y + dt*b/2, t+dt/2)
        d = rhs(y + dt*c, t+dt)
        y = y + dt*(a+2*b+2*c+d)/6
        if (k+1) % round(10/dt) == 0:
            result.append(y.copy())
    out = np.array(result)
    stored = TRUTH[2]*(out[:,0]-20) + TRUTH[3]*(out[:,1]-20)
    closure = out[:,2]-out[:,3]-stored
    return out[:,:2], float(np.max(np.abs(closure)))


def predict(params, experiment):
    g, h, cc, cp = params
    a = np.array([[-g/cc, g/cc], [g/cp, -(g+h)/cp]])
    vals, vecs = np.linalg.eig(a)
    step = (vecs @ np.diag(np.exp(vals*10)) @ np.linalg.inv(vecs)).real
    y = np.array([20.,20.])
    out = [y.copy()]
    p, ta = conditions(TIME[:-1], experiment)
    for q, ambient in zip(p, ta):
        equilibrium = np.array([ambient+q/h+q/g, ambient+q/h])
        y = equilibrium + step @ (y-equilibrium)
        out.append(y.copy())
    return np.array(out)


def metrics(pred, obs):
    err = pred-obs
    return {'component_RMSE_K': float(np.sqrt(np.mean(err[:,0]**2))),
            'plate_RMSE_K': float(np.sqrt(np.mean(err[:,1]**2))),
            'component_max_abs_K': float(np.max(np.abs(err[:,0]))),
            'plate_max_abs_K': float(np.max(np.abs(err[:,1]))),
            'component_mean_error_K': float(err[:,0].mean()),
            'plate_mean_error_K': float(err[:,1].mean())}


def main():
    started=time.monotonic()
    rng=np.random.default_rng(6242026)
    truth={}
    observations={}
    closure={}
    for ex in ['calibration','held_out']:
        truth[ex],closure[ex]=generate(ex)
        observations[ex]=truth[ex]+rng.normal(0,.15,truth[ex].shape)+np.array([.10,-.05])
    # Only calibration observations enter the optimizer; held-out data are absent.
    def residual(logparams):
        return ((predict(np.exp(logparams),'calibration')-observations['calibration'])/.15).ravel()
    fit=least_squares(residual,np.log(INITIAL),bounds=(np.log([.3,.3,30,100]),np.log([30,30,2000,10000])),xtol=1e-11,ftol=1e-11,gtol=1e-11)
    fitted=np.exp(fit.x)
    runs=[]
    allmetrics={}
    for ex in ['calibration','held_out']:
        pred=predict(fitted,ex)
        initial=predict(INITIAL,ex)
        p,ta=conditions(TIME,ex)
        m=metrics(pred,observations[ex])
        m['initial_component_RMSE_K']=metrics(initial,observations[ex])['component_RMSE_K']
        m['initial_plate_RMSE_K']=metrics(initial,observations[ex])['plate_RMSE_K']
        m['study_acceptance_pass']=m['component_RMSE_K']<=1 and m['plate_RMSE_K']<=1 and m['component_max_abs_K']<=2 and m['plate_max_abs_K']<=2
        allmetrics[ex]=m
        run={'id':ex,'label':'Calibration experiment' if ex=='calibration' else 'Held-out prediction — no retuning',
             'ambient_C':ta.tolist(),'power_W':p.tolist(),
             'observed_component_C':observations[ex][:,0].tolist(),'observed_plate_C':observations[ex][:,1].tolist(),
             'predicted_component_C':pred[:,0].tolist(),'predicted_plate_C':pred[:,1].tolist(),
             'initial_component_C':initial[:,0].tolist(),'initial_plate_C':initial[:,1].tolist(),
             'residual_component_K':(pred-observations[ex])[:,0].tolist(),'residual_plate_K':(pred-observations[ex])[:,1].tolist()}
        runs.append(run)
        cols=['time_s']+[k for k in run if isinstance(run[k],list)]
        with (R/(ex+'.csv')).open('w',newline='') as f:
            w=csv.writer(f);w.writerow(cols)
            for i,t in enumerate(TIME):w.writerow([float(t)]+[run[k][i] for k in cols[1:]])
    # Different initial guess checks the solution is not a single-start artifact.
    fit2=least_squares(residual,np.log([6.,1.5,150.,2000.]),bounds=(np.log([.3,.3,30,100]),np.log([30,30,2000,10000])))
    parameter_delta=float(np.max(np.abs(np.exp(fit2.x)-fitted)/fitted))
    truth_fine,_=generate('held_out',.25)
    refinement_K=float(np.max(np.abs(truth_fine-truth['held_out'])))
    note='Synthetic observations generated by a nonlinear two-node model, with assumed 0.15 K independent Gaussian noise and fixed sensor biases (+0.10/-0.05 K). No physical measurements or OEM data.'
    summary={'status':'synthetic_demonstration','physical_validation':False,'label':note,
       'fit_parameters':[{'name':n,'unit':u,'initial':float(i),'fitted':float(f),'truth':float(t)} for n,u,i,f,t in zip(NAMES,UNITS,INITIAL,fitted,TRUTH)],
       'metrics':allmetrics,'acceptance':{'rmse_limit_K':1,'max_abs_limit_K':2,'study_chosen':True,'scope':'Workflow demonstration only; not hardware qualification criteria.'},
       'method':{'optimizer':'scipy.optimize.least_squares on log parameters','calibration_only':True,'held_out_retuning':False,'seed':6242026,'sample_interval_s':10,'synthetic_generator_step_s':.5,'model_discrepancy':'Generator component conductance increases 0.15 percent/K above boundary; fitted model uses constant conductance. Boundary holds sampled for 10s in predictor.','sensor_noise_sigma_K':.15,'sensor_bias_K':[.1,-.05]},
       'limitations':['Synthetic generator and fitted model share topology; this is not independent physical validation.','Fitted values absorb the selected nonlinear discrepancy and sensor bias.','No extrapolation to flight pressure or different materials is established.','Replace synthetic CSVs with calibrated measurements and repeat hold-out testing before hardware claims.'],
       'sources':{'calibration':'calibration.csv','held_out':'held_out.csv','script':'../../source/correlation/synthetic_correlation.py'}}
    explorer={'label':'Synthetic workflow demonstration — no physical measurements','time_s':TIME.tolist(),'runs':runs,'units':{'time':'s','temperature':'degC','power':'W','residual':'K'},'data_origin':note}
    (R/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
    (R/'explorer.json').write_text(json.dumps(explorer,separators=(',',':'),allow_nan=False))
    audit={'passed':bool(fit.success and parameter_delta<1e-4 and refinement_K<1e-3 and max(closure.values())<1e-6),
        'held_out_acceptance_pass':allmetrics['held_out']['study_acceptance_pass'],'physical_test_performed':False,
        'optimizer_success':bool(fit.success),'second_start_relative_parameter_difference':parameter_delta,
        'generator_half_step_max_temperature_difference_K':refinement_K,'generator_max_energy_residual_J':closure,
        'sample_count_each':len(TIME),'elapsed_s':time.monotonic()-started,
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (V/'audit.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps({'audit':audit,'metrics':allmetrics,'fit_parameters':summary['fit_parameters']},indent=2))
    if not audit['passed']:raise RuntimeError('Synthetic workflow numerical checks failed')


if __name__=='__main__':main()
