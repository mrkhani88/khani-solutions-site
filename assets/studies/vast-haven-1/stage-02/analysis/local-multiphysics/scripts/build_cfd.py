"""Create three reproducible OpenFOAM v2512 microgravity equipment-bay cases."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def head(cls,obj):
    return f'FoamFile\n{{ version 2.0; format ascii; class {cls}; object {obj}; }}\n'
def make(name,speed,scale):
    p=ROOT/'cfd-flatpanel'/name
    for d in ['0','constant','system']: (p/d).mkdir(parents=True,exist_ok=True)
    xs=[0,.6,1,1.6]; ys=[0,.2,.6,.8]; zs=[0,.04,.8]
    vertices=[(x,y,z) for z in zs for y in ys for x in xs]
    vid=lambda i,j,k:k*16+j*4+i
    cells={}; blocks=[]
    for k in range(2):
      for j in range(3):
       for i in range(3):
        if (i,j,k)==(1,1,0): continue
        v=[vid(i,j,k),vid(i+1,j,k),vid(i+1,j+1,k),vid(i,j+1,k),vid(i,j,k+1),vid(i+1,j,k+1),vid(i+1,j+1,k+1),vid(i,j+1,k+1)]
        n=([9,6,9][i]*scale,[3,6,3][j]*scale,[2,14][k]*scale)
        cells[i,j,k]=v; blocks.append('hex ('+' '.join(map(str,v))+') ('+' '.join(map(str,n))+') simpleGrading (1 1 1)')
    patches={k:[] for k in ['inlet','outlet','walls','heater']}
    faces=[((-1,0,0),[0,4,7,3]),((1,0,0),[1,2,6,5]),((0,-1,0),[0,1,5,4]),((0,1,0),[3,7,6,2]),((0,0,-1),[0,3,2,1]),((0,0,1),[4,5,6,7])]
    for (i,j,k),v in cells.items():
      for (di,dj,dk),f in faces:
        nb=(i+di,j+dj,k+dk)
        if nb in cells: continue
        patch='heater' if nb==(1,1,0) else 'inlet' if nb[0]<0 else 'outlet' if nb[0]>2 else 'walls'
        patches[patch].append('('+' '.join(str(v[a]) for a in f)+')')
    txt=head('dictionary','blockMeshDict')+'scale 1;\nvertices\n(\n'+'\n'.join('(%g %g %g)'%v for v in vertices)+'\n);\nblocks\n(\n'+'\n'.join(blocks)+'\n);\nedges ();\nboundary\n(\n'
    for patch,f in patches.items(): txt+=f'{patch} {{ type '+('patch' if patch in ['inlet','outlet'] else 'wall')+'; faces (\n'+'\n'.join(f)+'\n); }\n'
    txt+='\n);\nmergePatchPairs ();\n'; (p/'system/blockMeshDict').write_text(txt)
    def field(n,cls,dim,initial,bc):
      (p/'0'/n).write_text(head(cls,n)+f'dimensions {dim};\ninternalField uniform {initial};\nboundaryField {{\n'+ '\n'.join(k+' { '+bc[k]+' }' for k in patches)+'\n}\n')
    field('U','volVectorField','[0 1 -1 0 0 0 0]',f'({speed} 0 0)',dict(inlet=f'type fixedValue; value uniform ({speed} 0 0);',outlet='type zeroGradient;',walls='type noSlip;',heater='type noSlip;'))
    field('p_rgh','volScalarField','[0 2 -2 0 0 0 0]','0',dict(inlet='type zeroGradient;',outlet='type fixedValue; value uniform 0;',walls='type fixedFluxPressure; rho rhok; value uniform 0;',heater='type fixedFluxPressure; rho rhok; value uniform 0;'))
    field('T','volScalarField','[0 0 0 1 0 0 0]','293.15',dict(inlet='type fixedValue; value uniform 293.15;',outlet='type zeroGradient;',walls='type zeroGradient;',heater='type fixedGradient; gradient uniform 343.4065934065934;'))
    field('alphat','volScalarField','[0 2 -1 0 0 0 0]','0',{k:'type calculated; value uniform 0;' for k in patches})
    (p/'constant/g').write_text(head('uniformDimensionedVectorField','g')+'dimensions [0 1 -2 0 0 0 0]; value (0 0 0);\n')
    # alpha=k/rho/cp; nu chosen consistently with Pr.
    (p/'constant/transportProperties').write_text(head('dictionary','transportProperties')+'transportModel Newtonian;\nnu 1.5e-5;\nbeta 0.0034;\nTRef 293.15;\nPr 0.695769230769;\nPrt 0.85;\n')
    (p/'constant/turbulenceProperties').write_text(head('dictionary','turbulenceProperties')+'simulationType laminar;\n')
    (p/'system/fvSchemes').write_text(head('dictionary','fvSchemes')+'''ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; div(phi,U) bounded Gauss linearUpwind grad(U); div(phi,T) bounded Gauss linearUpwind grad(T); div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
''')
    (p/'system/fvSolution').write_text(head('dictionary','fvSolution')+'''solvers {
p_rgh { solver GAMG; tolerance 1e-10; relTol 0.02; smoother GaussSeidel; }
"(U|T)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-10; relTol 0.02; }
}
SIMPLE { nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; residualControl { p_rgh 1e-8; U 1e-8; T 1e-8; } }
relaxationFactors { fields { p_rgh 0.3; } equations { U 0.7; T 0.7; } }
''')
    (p/'system/controlDict').write_text(head('dictionary','controlDict')+'''application buoyantBoussinesqSimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime 4000; deltaT 1;
writeControl timeStep; writeInterval 4000; purgeWrite 0; writeFormat ascii; writePrecision 12; writeCompression off;
timeFormat general; timePrecision 8; runTimeModifiable false;
functions {
    cells { type writeCellCentres; libs (fieldFunctionObjects); executeControl writeTime; writeControl writeTime; }
    outletT { type surfaceFieldValue; writeFields false; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name outlet; operation areaAverage; fields (T); }
    heaterT { type surfaceFieldValue; writeFields false; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name heater; operation areaAverage; fields (T); }
    outletFlow { type surfaceFieldValue; writeFields false; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name outlet; operation sum; fields (phi); }
    inletFlow { type surfaceFieldValue; writeFields false; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name inlet; operation sum; fields (phi); }
    inletP { type surfaceFieldValue; writeFields false; libs (fieldFunctionObjects); writeControl timeStep; writeInterval 1; regionType patch; name inlet; operation areaAverage; fields (p_rgh); }
}
''')
    (p/'case.foam').touch()
    (p/'assumptions.json').write_text(json.dumps(dict(geometry='1.6 x 0.8 x 0.8 m bay; 0.4 x 0.4 x 0.04 m electronics envelope attached to bottom',heat_W=2,heated_area_m2=.224,k_air_W_mK=.026,rho_kg_m3=1.2,cp_J_kgK=1005,nu_m2_s=1.5e-5,inlet_K=293.15,inlet_speed_m_s=speed,gravity=[0,0,0],flow_regime='Laminar screening assumption; Re based on .8m and nominal speed 1067 / 2133. Transition and mixing sensitivity unresolved.',mesh_scale=scale),indent=2))
    print(name)
make('baseline',.02,1)
make('double_flow',.04,1)
make('mesh_fine',.02,2)

make('mesh_finer',.02,3)
