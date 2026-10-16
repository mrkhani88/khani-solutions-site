"""Scientific plots from actual layer finite-volume temperatures."""
def figures(configs,B,ROOT,CASES):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,3,figsize=(11,9),layout='constrained')
    for col,(case,(m,r)) in enumerate(configs.items()):
        for row,name in enumerate(['BackGlass','Battery']):
            ax=axs[row,col];polys=[];values=[]
            for i in m.groups[name]:
                for tri in B.triangles(m.nodes[i]['poly']):polys.append(tri);values.append(r['peak'][i,2])
            pc=PolyCollection(polys,array=np.array(values),cmap='inferno',clim=(25,75),edgecolors='none',antialiased=False);ax.add_collection(pc);ax.add_patch(Rectangle((18,30),50,70,fill=False,ec='#20bbc9',ls='--',lw=1.3));ax.set(xlim=(0,71.6),ylim=(0,147.6),title=CASES[case]['label']+'\n'+name+' max '+format(max(values),'.3f')+' °C',xlabel='x (mm)',ylabel='y (mm)');ax.set_aspect('equal')
    fig.colorbar(pc,ax=axs,label='Layer temperature at600s (°C)',shrink=.8);fig.suptitle('Stage07 · Fixed50×70mm graphite · shared25–75°C scale');fig.savefig(ROOT/'review/adhesive_maps.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(13,4.3),layout='constrained')
    for ax,(name,metric) in zip(axs,[('BackGlass','max'),('Battery','mean'),('Battery','max')]):
        for case,(m,r) in configs.items():
            vals=[B.stats(m,f[:,2],name)[1 if metric=='mean' else 2] for f in r['field']];ax.plot(np.array(r['times'])/60,vals,lw=2,label=CASES[case]['label'])
        ax.set(title=name+' '+metric,xlabel='Time (min)',ylabel='Temperature (°C)',xlim=(0,30));ax.axvline(10,c='gray',ls=':');ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=8)
    fig.suptitle('Same3.75W for10min, then sources off');fig.savefig(ROOT/'review/adhesive_histories.png',dpi=160);plt.close(fig)
    # Pointwise changes at matching x/y control volumes; elevations may differ.
    fig,axs=plt.subplots(2,2,figsize=(9,8),layout='constrained');ref,rr=configs['reference'];datasets=[]
    for col,case in enumerate(['medium','thick']):
        m,r=configs[case]
        for row,name in enumerate(['BackGlass','Battery']):
            idx=m.groups[name];assert np.array_equal(idx,ref.groups[name]);delta=r['peak'][idx,2]-rr['peak'][idx,2];datasets.append((axs[row,col],case,name,idx,delta,m))
    limit=max(abs(x) for _,_,_,_,ds,_ in datasets for x in ds);limit=max(.01,np.ceil(limit*100)/100)
    for ax,case,name,idx,delta,m in datasets:
        polys=[];values=[]
        for i,d in zip(idx,delta):
            for tri in B.triangles(m.nodes[i]['poly']):polys.append(tri);values.append(d)
        pc=PolyCollection(polys,array=np.array(values),cmap='coolwarm',clim=(-limit,limit),edgecolors='none',antialiased=False);ax.add_collection(pc);ax.set_aspect('equal');ax.autoscale_view();ax.set(title=str(round(CASES[case]['adhesive_thickness_mm']*1000))+' µm − 25 µm\n'+name,xlabel='x (mm)',ylabel='y (mm)')
    fig.colorbar(pc,ax=axs,label='Pointwise temperature change at600s (K)',shrink=.8);fig.suptitle('Blue=cooler · Red=warmer · shared zero-centered scale');fig.savefig(ROOT/'review/adhesive_difference.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(11,4.2),layout='constrained')
    for ax,(case,(m,r)) in zip(axs,configs.items()):
        ta=m.adhesive_t;bottom=7-ta-.1
        for y,h,color,label in [(4.8,bottom-4.8,'#699eaa','RF pad'),(bottom,.1,'#353b43','Graphite'),(7-ta,ta,'#dc8e3c','Adhesive'),(7,.8,'#b4cbd6','Back glass')]:
            ax.add_patch(Rectangle((0,y),1,h,fc=color));ax.text(1.08,max(6.74,y+h/2),label,va='center',fontsize=9,clip_on=True)
        ax.set(xlim=(-.1,2.4),ylim=(6.6,7.85),title=CASES[case]['label'],ylabel='z (mm)');ax.set_xticks([]);ax.text(0,6.65,'Pad '+format(m.pad_t,'.3f')+' mm',fontsize=9)
    fig.suptitle('Section near inner cover · vertical scale in mm · lateral width schematic');fig.savefig(ROOT/'review/adhesive_stack.png',dpi=170);plt.close(fig)
