"""Check approximate lumped dynamics against spatial semidiscrete transient model.
Matched constant plate, geometry, materials, capacities and source steps.
This is model-to-model reduction verification, not measurement correlation.
"""
from pathlib import Path
import json,numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import splu
from conduction import solve
B=Path(__file__).resolve().parents[2];V=B/'verification/engineering';R=B/'results/engineering'
records=[];q=np.array([456.75,100,100,300,76.595744680851])
for dt in [5,2.5]:
 rec,K,C=solve(40,30,4,10,.00025,6,system=True);N=len(C)-5;GG=np.linalg.inv(np.array(rec['R_K_W']));Cr=np.array(rec['C_J_K']);full=np.zeros(N+5);small=np.zeros(5)
 A=splu(K+diags(C/dt));Ar=np.diag(Cr/dt)+GG;history=[]
 for i in range(int(1800/dt)+1):
  t=i*dt;Q=q if 30<=t<630 else np.zeros(5);rhs=C/dt*full;rhs[N:]+=Q;full=A.solve(rhs);small=np.linalg.solve(Ar,Cr/dt*small+Q)
  if i%int(10/dt)==0:history.append([t,*full[N:],*small])
 a=np.array(history);error=abs(a[:,1:6]-a[:,6:11]);records.append(dict(dt_s=dt,spatial_cells=N,lumped_nodes=5,max_abs_terminal_difference_K=float(error.max()),peak_spatial_rise_K=float(a[:,1:6].max()),peak_lumped_rise_K=float(a[:,6:11].max()),relative_peak_difference=float(abs(a[:,1:6].max()-a[:,6:11].max())/a[:,1:6].max())))
 if dt==2.5:
  np.savetxt(R/'reduction-transient.csv',a,delimiter=',',header='time_s,spatial_tx_K,spatial_beamformer_K,spatial_baseband_K,spatial_server_K,spatial_power_K,reduced_tx_K,reduced_beamformer_K,reduced_baseband_K,reduced_server_K,reduced_power_K',comments='')
out=dict(method='Backward Euler matched spatial and reduced ODEs; full-load600s heat pulse at30s into initiallyisothermal assembly; platefixed; no boundary dynamics',scope='Independent spatial-vs-reduced dynamic check. Not test correlation. Assumed homogeneous board/package-case terminals.',runs=records,acceptance_max_terminal_error_K=1,passed=max(x['max_abs_terminal_difference_K'] for x in records)<1)
(V/'dynamic-reduction-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert out['passed']
