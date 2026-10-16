"""Draw assumed pad placement from the same input dimensions as CAD and solver."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1];P=json.loads((R/'source/inputs.json').read_text());D=json.loads((R/'source/cad_parameters.json').read_text());pad=P['rf_pad']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white'})
fig,(ax,bx)=plt.subplots(1,2,figsize=(10.5,4.6),layout='constrained')
ax.add_patch(Rectangle((46,39),19,20,facecolor='#e0ece5',edgecolor='#377456',lw=1.5))
for c in D['chips']:
    if c['z']!=4.8:continue
    ax.add_patch(Rectangle((c['x'],c['y']),c['length'],c['width'],facecolor='#9aa7af',edgecolor='#425360'))
    ax.text(c['x']+c['length']/2,c['y']+c['width']/2,c['id'],ha='center',va='center')
x0,y0,x1,y1=pad['footprint_global_mm'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#4dbfc2',edgecolor='#195b65',lw=1.5))
ax.text((x0+x1)/2,(y0+y1)/2,'RF pad\n16 × 5 mm',ha='center',va='center',fontsize=9)
ax.set(xlim=(44,67),ylim=(37,61),xlabel='x (mm)',ylabel='y (mm)',title='Plan view · pad clears the RF packages');ax.set_aspect('equal')
for y,h,col,label in [(4.2,.6,'#8bad97','RF PCB'),(4.8,2.2,'#4dbfc2','Pad · 2.2 mm installed'),(7,.8,'#bdc9d1','Back cover')]:
    bx.add_patch(Rectangle((0,y),16,h,facecolor=col,edgecolor='#34515e'));bx.text(8,y+h/2,label,ha='center',va='center',fontsize=10)
bx.set(xlim=(-1,17),ylim=(3.8,8.2),xlabel='Pad length (mm)',ylabel='z (mm)',title='Section through the clear pad strip');bx.set_yticks([4.2,4.8,7,7.8])
fig.suptitle('Stage 04 · Assumed RF board-to-enclosure thermal pad',fontsize=13)
(R/'review').mkdir(exist_ok=True)
fig.savefig(R/'review/pad_layout.png',dpi=180);fig.savefig(R/'review/pad_layout.svg');plt.close(fig)
