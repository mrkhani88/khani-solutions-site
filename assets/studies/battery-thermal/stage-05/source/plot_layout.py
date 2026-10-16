"""Plan and schematic stack, all dimensions read from the thermal inputs."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1];P=json.loads((R/'source/inputs.json').read_text());G=P['graphite'];A=P['spreader_adhesive']
fig,(ax,bx)=plt.subplots(1,2,figsize=(11,5),layout='constrained');x,y,xx,yy=G['footprint_global_mm']
ax.add_patch(Rectangle((x,y),xx-x,yy-y,fc='#b7d7dc',ec='#23505d',lw=1.5));ax.add_patch(Rectangle((46,39),19,20,fc='#76a08c',ec='#315a45'))
px,py,pxx,pyy=P['rf_pad']['footprint_global_mm'];ax.add_patch(Rectangle((px,py),pxx-px,pyy-py,fc='#d7994c',ec='#754713'))
ax.text(55,56.5,'RF pad',ha='center',va='center',fontsize=9);ax.text(55.5,47,'RF PCB',ha='center');ax.text(53,73,'Graphite + adhesive\n30 × 50 mm',ha='center',fontsize=11)
ax.set(xlim=(34,72),ylim=(25,85),xlabel='x (mm)',ylabel='y (mm)',title='Plan view · assumed inner-cover footprint');ax.set_aspect('equal')
layers=[('RF PCB',.6,'#76a08c'),('RF pad',2.075,'#d7994c'),('Graphite',.1,'#73818a'),('Adhesive',.025,'#7cbdc4'),('Back glass',.8,'#b6c5ce')]
for i,(label,t,color) in enumerate(layers):bx.add_patch(Rectangle((0,i),1,.85,fc=color,ec='#3d5865'));bx.text(.5,i+.425,f'{label} · {t:g} mm',ha='center',va='center',fontsize=10)
bx.set(xlim=(-.08,1.08),ylim=(-.15,5),title='Section through pad · schematic, not to scale');bx.set_axis_off();fig.suptitle('Stage 05 · Bonded graphite inside the original enclosure')
fig.savefig(R/'review/spreader_layout.png',dpi=170);fig.savefig(R/'review/spreader_layout.svg');plt.close(fig)
