"""Render our independent schematic, not manufacturer CAD. Requires matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
p=Path(__file__).resolve().parent
fig,ax=plt.subplots(figsize=(16,7.2));fig.patch.set_facecolor('#f4f7fb');ax.set_facecolor('#f4f7fb')
ax.set_xlim(0,20);ax.set_ylim(0,8);ax.axis('off')
blue='#087eac';red='#c74a43';ink='#16334c';muted='#52677b'
def box(x,y,w,h,label,fc='#ffffff',edge=ink,size=11):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08,rounding_size=0.08',edgecolor=edge,facecolor=fc,lw=1.5))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',color=ink,fontsize=size)
def arr(a,b,c):
    ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',lw=2.4,color=c))
ax.text(.4,7.6,'Proposed 1 MW liquid-cooling module',fontsize=22,weight='bold',color=ink)
ax.text(.4,7.16,'Independent concept | 10 parallel racks | Hydraulic schematic, not a scaled floor plan or AWS drawing',fontsize=11,color=muted)
box(.5,2.8,3.0,3.1,'CDU\n\nPlate heat exchanger\n\n3 x 50% pumps\n2 duty + 1 standby',size=12)
ax.plot([3.5,18.4],[6.25,6.25],color=blue,lw=4);ax.plot([3.5,3.5],[5.5,6.25],color=blue,lw=3)
arr((3.6,6.25),(4.5,6.25),blue)
ax.text(7,6.55,'35 C supply | total 24.1 L/s | target clear ID 125 mm',fontsize=11,color=blue)
ax.plot([3.5,18.4],[2.55,2.55],color=red,lw=4);ax.plot([3.5,3.5],[2.55,3.1],color=red,lw=3)
arr((6,2.55),(4.8,2.55),red)
ax.text(7,2.05,'45 C return | segmented headers in the 1D model',fontsize=11,color=red)
for i in range(10):
    x=4.85+i*1.37
    box(x,3.6,.9,1.65,f'R{i+1:02}\n\n100 kW',fc='#eaf2f8',size=9)
    ax.plot([x+.45,x+.45],[5.25,6.25],color=blue,lw=2)
    arr((x+.45,5.9),(x+.45,5.35),blue)
    ax.plot([x+.45,x+.45],[2.55,3.6],color=red,lw=2)
    arr((x+.45,3.45),(x+.45,2.9),red)
ax.text(4.25,1.68,'Each branch: valve + sensor + manifold + parallel server paths',fontsize=10,color=muted)
box(.5,.55,3,.95,'Facility heat rejection\nDry cooler / chiller / heat reuse',size=10)
arr((1.2,1.5),(1.2,2.7),blue);arr((2.8,2.7),(2.8,1.5),red)
ax.text(4.25,1.22,'Heat crosses the CDU exchanger; facility water and IT coolant stay separate.',fontsize=12,color=ink)
ax.text(4.25,.68,'Branch: 2.41 L/s, 40 mm clear ID. Preliminary pump duty: 86.8 m3/h at ~28 m head.',fontsize=11,color=muted)
ax.text(.5,.08,'Assumed 35/45 C water loop. Device losses and routing lengths are placeholders; no network/CFD simulation yet.',fontsize=10,color=muted)
fig.tight_layout(pad=.6)
fig.savefig(p/'proposed-module-layout.png',dpi=150,facecolor=fig.get_facecolor())
fig.savefig(p/'proposed-module-layout.svg',facecolor=fig.get_facecolor())

svg=p/"proposed-module-layout.svg"
svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
