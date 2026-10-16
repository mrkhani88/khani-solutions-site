"""Lesson 1: thermal capacitance, heating, cooling and conservation.
Open source Python + NumPy + SciPy + Matplotlib. No commercial solver needed.
Run from any directory. All inputs are explicit, uncalibrated teaching assumptions.
"""
from pathlib import Path
import sys,json,csv,platform,hashlib
import numpy as np
import scipy
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'results').mkdir(exist_ok=True)
(ROOT/'review').mkdir(exist_ok=True)
P=json.loads((ROOT/'source/inputs.json').read_text())
g=P['geometry_mm'];w,h,t=[g[k]/1000 for k in ['width','height','thickness']]
volume=w*h*t;area=2*(w*h+w*t+h*t)
mass=P['density_kg_m3']*volume;capacity=mass*P['specific_heat_J_kgK']
conductance=P['effective_surface_loss_W_m2K']*area
tau=capacity/conductance;resistance=1/conductance
ta=P['ambient_temperature_C'];t0=P['initial_temperature_C'];q=P['heat_input_W']
on=P['heating_duration_s'];end=P['total_duration_s'];dt=P['output_interval_s']
assert all(v>0 for v in [w,h,t,mass,capacity,conductance,dt]) and 0<on<end and q>=0
assert abs(on/dt-round(on/dt))<1e-9 and abs(end/dt-round(end/dt))<1e-9
def rhs(power):
    def f(time,state):
        loss=conductance*(state[0]-ta)
        return [(power-loss)/capacity,loss]
    return f
heatt=np.arange(0,on+dt/2,dt);coolt=np.arange(on,end+dt/2,dt)
warm=solve_ivp(rhs(q),(0,on),[t0,0.0],t_eval=heatt,rtol=1e-10,atol=1e-11)
cool=solve_ivp(rhs(0.0),(on,end),warm.y[:,-1],t_eval=coolt,rtol=1e-10,atol=1e-11)
assert warm.success and cool.success
time=np.concatenate([warm.t,cool.t[1:]])
temp=np.concatenate([warm.y[0],cool.y[0,1:]])
lost=np.concatenate([warm.y[1],cool.y[1,1:]])
input_energy=q*np.minimum(time,on);stored=capacity*(temp-t0)
residual=input_energy-stored-lost
theta0=t0-ta;asymptote=q/conductance
theta_at_off=asymptote+(theta0-asymptote)*np.exp(-on/tau)
analytic=ta+np.where(time<=on,asymptote+(theta0-asymptote)*np.exp(-time/tau),theta_at_off*np.exp(-(time-on)/tau))
error=float(np.max(np.abs(temp-analytic)))
energy_error=float(np.max(np.abs(residual)))
assert error<1e-6,(error,'Numerical/analytical disagreement')
assert energy_error<1e-5,(energy_error,'Energy conservation failure')
assert np.all(np.diff(warm.y[0])>=-1e-8) and np.all(np.diff(cool.y[0])<=1e-8)
assert temp.min()>=ta-1e-8
rows=[]
for i,tt in enumerate(time):
    rows.append([float(tt),float(tt/60),float(temp[i]),q if tt<on else 0.0,float(conductance*(temp[i]-ta)),float(input_energy[i]),float(stored[i]),float(lost[i]),float(residual[i]),float(analytic[i])])
with (ROOT/'results/temperature_history.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['time_s','time_min','average_cell_temperature_C','applied_heat_W_right_continuous','ambient_heat_loss_W','cumulative_input_J','stored_energy_above_initial_J','cumulative_ambient_loss_J','energy_residual_J','analytical_temperature_C']);writer.writerows(rows)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#243d50','text.color':'#243d50','axes.edgecolor':'#687b8a','xtick.color':'#526879','ytick.color':'#526879','savefig.facecolor':'white'})
fig,(ax,ax2)=plt.subplots(2,1,figsize=(11,7),sharex=True,gridspec_kw={'height_ratios':[2,1]},constrained_layout=True)
ax.plot(time/60,temp,c='#246287',lw=2.5,label='Average cell temperature')
ax.axhline(ta,c='#6b7882',ls='--',lw=1.3,label='Ambient 25 °C')
ax.axvline(on/60,c='#a7b3bd',ls=':',lw=1.1)
peak=float(temp.max());pk=int(temp.argmax())
ax.annotate(f'{peak:.2f} °C at heat-off',xy=(time[pk]/60,peak),xytext=(14,peak-.4),arrowprops={'arrowstyle':'-','color':'#607585'},fontsize=11)
ax.set_ylabel('Average cell temperature (°C)');ax.set_title('Stage 01   Single-cell heating and cooling',loc='left',fontweight='bold',fontsize=16)
ax.set_ylim(min(ta,t0)-.5,peak+1.5)
ax.grid(axis='y',alpha=.18);ax.legend(loc='upper left',frameon=False)
ax2.step([0,on/60,on/60,end/60],[q,q,0,0],where='post',c='#c48b38',lw=2.3,label='Prescribed heat input')
ax2.plot(time/60,conductance*(temp-ta),c='#246287',lw=1.8,ls='--',label='Heat transferred to ambient')
ax2.set(xlabel='Time (min)',ylabel='Heat rate (W)',xlim=(0,end/60),ylim=(-.05,max(q*1.15,.1)));ax2.set_xticks([0,5,10,15,20,25,30]);ax2.grid(axis='y',alpha=.18);ax2.legend(loc='upper right',frameon=False)
fig.get_layout_engine().set(rect=(0,.07,1,.93))
fig.text(.02,.018,'Illustrative assumptions: 1 W for 10 min, then 20 min cooldown. Uniform temperature; no enclosure or charging model.\nUncalibrated teaching example; not measured Apple or Wisk performance.',fontsize=10,color='#607585')
fig.savefig(ROOT/'review/heating_cooling.png',dpi=190);fig.savefig(ROOT/'review/heating_cooling.svg');plt.close(fig)
fig,ax=plt.subplots(figsize=(11,5),constrained_layout=True)
ax.plot(time/60,input_energy,c='#333f48',lw=2,label='Cumulative heat input')
ax.plot(time/60,stored,c='#246287',lw=2,label='Energy stored in cell')
ax.plot(time/60,lost,c='#c48b38',lw=2,ls='--',label='Cumulative heat lost to ambient')
ax.set(xlabel='Time (min)',ylabel='Energy relative to initial state (J)',xlim=(0,end/60),ylim=(0,q*on*1.12),title='Energy balance: input = stored + transferred to ambient')
ax.set_xticks([0,5,10,15,20,25,30]);ax.grid(axis='y',alpha=.18);ax.legend(frameon=False,loc='upper left');fig.savefig(ROOT/'review/energy_balance.png',dpi=190);plt.close(fig)
summary={'model':'0D uniform-temperature teaching model','input_provenance':P['provenance'],'cell_volume_m3':volume,'exposed_area_m2':area,'assumed_mass_kg':mass,'thermal_capacity_J_K':capacity,'thermal_conductance_W_K':conductance,'thermal_resistance_K_W':resistance,'time_constant_s':tau,'peak_temperature_C':peak,'peak_time_s':float(time[pk]),'final_temperature_C':float(temp[-1]),'input_energy_J':float(input_energy[-1]),'stored_energy_final_J':float(stored[-1]),'ambient_loss_final_J':float(lost[-1]),'max_absolute_energy_residual_J':energy_error,'max_analytical_comparison_error_K':error,'rows':len(rows),'simulation_status':'Solved and numerically verified; not experimentally validated','mesh':'Not applicable to this 0D model','versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2))
(ROOT/'results/history.json').write_text(json.dumps({'time_s':time.tolist(),'temperature_C':temp.tolist(),'input_energy_J':input_energy.tolist(),'stored_energy_J':stored.tolist(),'ambient_loss_J':lost.tolist()},separators=(',',':')))
print(json.dumps(summary,indent=2))
