from pathlib import Path
import json,math,os
import numpy as np
from shapely.geometry import Polygon,LineString
P=Path(__file__).resolve().parent; C=Path(os.environ.get('MIDNIGHT_R5_CASE_DIR',str(P/'cfd'))); C.mkdir(parents=True,exist_ok=True)
if any(d.is_dir() and d.name.replace('.','',1).isdigit() and float(d.name)>0 for d in C.iterdir()):
 raise SystemExit('Solved fields already exist. Set MIDNIGHT_R5_CASE_DIR to a new, empty case directory to preserve this run.')
g=json.loads((P/'geometry.json').read_text()); original=Polygon(g['body_outline_m'])
# Preserve vent endpoints while simplifying very short CAD polyline segments.
a,b=map(np.array,g['vent']['endpoints_m']); points=np.array(g['body_outline_m'])
ia=int(np.argmin(np.linalg.norm(points-a,axis=1)));ib=int(np.argmin(np.linalg.norm(points-b,axis=1)))
assert (ia+1)%len(points)==ib
wall=np.concatenate((points[ib:],points[:ia+1]))
wall=np.array(LineString(wall).simplify(.001,preserve_topology=True).coords)
body=wall
# Wall runs from b to a; closing line a->b is hot-gas inlet.
poly=Polygon(body); assert poly.is_valid
error=original.boundary.hausdorff_distance(poly.boundary)
assert error<.0011
n=len(body)
lines=['SetFactory("Built-in");','Mesh.MshFileVersion = 2.2;', 'Mesh.Algorithm = 6;', 'Mesh.RecombinationAlgorithm = 1;', 'Mesh.Optimize = 1;']
for i,(x,y) in enumerate(body,1):lines.append(f'Point({i}) = {{{x:.12g}, {y:.12g}, 0, 0.08}};')
for i in range(n):lines.append(f'Line({i+1}) = {{{i+1}, {(i+1)%n+1}}};')
rect=[(-16.4,0),(32.8,0),(32.8,24.6),(-16.4,24.6)]
for i,(x,y) in enumerate(rect,n+1):lines.append(f'Point({i}) = {{{x}, {y}, 0, 1.5}};')
for i in range(4):lines.append(f'Line({n+i+1}) = {{{n+i+1}, {n+(i+1)%4+1}}};')
lines += ['Curve Loop(1) = {'+', '.join(str(n+i+1) for i in range(4))+'};','Curve Loop(2) = {'+', '.join(str(i+1) for i in range(n))+'};','Plane Surface(1) = {1,2};']
lines += [f'Field[1] = Distance; Field[1].CurvesList = {{{n}}}; Field[1].Sampling = 60;',
 'Field[2] = Threshold; Field[2].InField = 1; Field[2].SizeMin = 0.0125; Field[2].SizeMax = 1.5; Field[2].DistMin = 0.08; Field[2].DistMax = 0.8;',
 'Field[3] = Box; Field[3].VIn = 0.10; Field[3].VOut = 1.5; Field[3].XMin = 3.5; Field[3].XMax = 8.5; Field[3].YMin = 0; Field[3].YMax = 2.2; Field[3].Thickness = 0.7;',
 'Field[4] = Box; Field[4].VIn = 0.23; Field[4].VOut = 1.5; Field[4].XMin = 0; Field[4].XMax = 12; Field[4].YMin = 0; Field[4].YMax = 8; Field[4].Thickness = 2;',
 'Field[6] = Distance; Field[6].CurvesList = {'+', '.join(str(i) for i in range(1,n))+'}; Field[6].Sampling = 6;',
 'Field[7] = Threshold; Field[7].InField = 6; Field[7].SizeMin = 0.08; Field[7].SizeMax = 1.5; Field[7].DistMin = 0.1; Field[7].DistMax = 1.2;',
 'Field[8] = Box; Field[8].VIn = 0.006; Field[8].VOut = 1.5; Field[8].XMin = -0.10; Field[8].XMax = 1.15; Field[8].YMin = 0; Field[8].YMax = 0.38; Field[8].Thickness = 0.15;',
 'Field[5] = Min; Field[5].FieldsList = {2,3,4,7,8}; Background Field = 5;',
 'Mesh.MeshSizeExtendFromBoundary = 0;', 'Mesh.MeshSizeFromPoints = 0;', 'Mesh.MeshSizeFromCurvature = 0;',
 'Recombine Surface {1};',
 'out[] = Extrude {0,0,0.1} { Surface{1}; Layers{1}; Recombine; };',
 'Physical Surface("frontAndBack") = {1, out[0]};',
 'Physical Surface("ground") = {out[2]};',
 'Physical Surface("farfield") = {out[3],out[4],out[5]};',
 # The hole-loop lateral faces are returned in reverse curve order.
 'Physical Surface("aircraftWall") = {'+', '.join(f'out[{7+i}]' for i in range(n-1))+'};',
 'Physical Surface("hotGasInlet") = {out[6]};',
 'Physical Volume("externalAir") = {out[1]};']
(C/'mesh.geo').write_text('\n'.join(lines)+'\n')
(C/'mesh_geometry.json').write_text(json.dumps({'outline_m':body.tolist(),'CAD_boundary_max_deviation_m':error,'span_m':.1,'vent_target_size_m':.0125,'geometry_units':'m','simplification_reason':'remove sub-millimetre construction segments without changing vent endpoints'},indent=2))
for d in ['0','constant','system']:(C/d).mkdir(exist_ok=True)
def header(obj,cls='dictionary'):
 return f'FoamFile\n{{\n version 2.0; format ascii; class {cls}; object {obj};\n}}\n'
def write(folder,name,content,cls='dictionary'):(C/folder/name).write_text(header(name,cls)+content+'\n')
write('constant','g','dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);','uniformDimensionedVectorField')
write('constant','thermophysicalProperties','''thermoType { type heRhoThermo; mixture pureMixture; transport sutherland; thermo hConst; equationOfState perfectGas; specie specie; energy sensibleEnthalpy; }
pRef 101325;
mixture { specie { molWeight 28.965; } thermodynamics { Cp 1005; Hf 0; } transport { As 1.458e-6; Ts 110.4; } }''')
write('constant','turbulenceProperties','simulationType RAS;\nRAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }')
write('system','fvSchemes','''ddtSchemes { default Euler; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes { default none; div(phi,U) Gauss upwind; div(phi,h) Gauss upwind; div(phi,e) Gauss upwind; div(phi,K) Gauss upwind; div(phi,Ekp) Gauss upwind; div(phi,k) Gauss upwind; div(phi,omega) Gauss upwind; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
fluxRequired { default no; p_rgh; }
wallDist { method meshWave; }''')
write('system','fvSolution','''solvers {
 "rho.*" { solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0; }
 p_rgh { solver GAMG; tolerance 1e-7; relTol 0.03; smoother DICGaussSeidel; cacheAgglomeration true; agglomerator faceAreaPair; nCellsInCoarsestLevel 20; mergeLevels 1; }
 p_rghFinal { $p_rgh; relTol 0; }
 "(U|h|e|k|omega)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-7; relTol 0.05; }
 "(U|h|e|k|omega)Final" { $U; relTol 0; }
}
PIMPLE { momentumPredictor yes; nOuterCorrectors 1; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 101325; }
relaxationFactors { equations { ".*" 1; } }''')
functions='''
functions {
 extrema { type fieldMinMax; libs (fieldFunctionObjects); fields (T U p rho); mode magnitude; writeControl adjustableRunTime; writeInterval 0.1; log false; }
 inletMass { type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name hotGasInlet; operation sum; writeFields false; fields (phi); writeControl timeStep; writeInterval 1; log false; }
 farfieldMass { type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name farfield; operation sum; writeFields false; fields (phi); writeControl timeStep; writeInterval 1; log false; }
 massInventory { type volFieldValue; libs (fieldFunctionObjects); operation volIntegrate; writeFields false; fields (rho); writeControl timeStep; writeInterval 1; log false; }
 groundTemperature { type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name ground; operation max; writeFields false; fields (T); writeControl adjustableRunTime; writeInterval 0.1; log false; }
 groundWallHeatFlux { type wallHeatFlux; libs (fieldFunctionObjects); patches (ground aircraftWall); writeControl adjustableRunTime; writeInterval 0.5; log false; }
}
'''
write('system','controlDict','''application buoyantPimpleFoam;
startFrom startTime; startTime 0; stopAt endTime; endTime 10;
deltaT 1e-5; adjustTimeStep yes; maxCo 0.6; maxDeltaT 0.002;
writeControl adjustableRunTime; writeInterval 0.25; purgeWrite 0;
writeFormat ascii; writePrecision 10; timeFormat general; timePrecision 8;
runTimeModifiable true;
'''+functions)
write('system','decomposeParDict','numberOfSubdomains 6; method scotch;')
def field(name,cls,dims,initial,bc):
 content=f'dimensions {dims};\ninternalField uniform {initial};\nboundaryField\n{{\n'
 for key,value in bc.items():content+=f' {key}\n {{ {value} }}\n'
 content+=' frontAndBack { type empty; }\n}'
 write('0',name,content,cls)
wallkeys=['aircraftWall','ground']
vel=tuple(g['vent']['velocity_m_s'])
jet=f'({vel[0]:.12g} {vel[1]:.12g} 0)'
ubc={k:'type fixedValue; value uniform (0 0 0);' for k in wallkeys}
ubc['hotGasInlet']=f'type uniformFixedValue; uniformValue table ((0 {jet})(9.999999 {jet})(10 (0 0 0))(15 (0 0 0))); value uniform {jet};'
ubc['farfield']='type pressureInletOutletVelocity; value uniform (0 0 0);'
field('U','volVectorField','[0 1 -1 0 0 0 0]','(0 0 0)',ubc)
tbc={k:'type zeroGradient;' for k in wallkeys}
tbc['hotGasInlet']='type fixedValue; value uniform 873.15;'
tbc['farfield']='type inletOutlet; inletValue uniform 298.15; value uniform 298.15;'
field('T','volScalarField','[0 0 0 1 0 0 0]','298.15',tbc)
pbc={k:'type calculated; value uniform 101325;' for k in wallkeys+['hotGasInlet','farfield']}
field('p','volScalarField','[1 -1 -2 0 0 0 0]','101325',pbc)
prbc={k:'type fixedFluxPressure; value uniform 101325;' for k in wallkeys+['hotGasInlet']}
prbc['farfield']='type prghTotalPressure; p0 uniform 101325; gamma 1; value uniform 101325;'
field('p_rgh','volScalarField','[1 -1 -2 0 0 0 0]','101325',prbc)
for name,dims,initial,wall,jetval,ambient in [
 ('k','[0 2 -2 0 0 0 0]','1e-6','kqRWallFunction','6','1e-6'),
 ('omega','[0 0 -1 0 0 0 0]','1','omegaWallFunction','638.9','1'),
 ('nut','[0 2 -1 0 0 0 0]','0','nutkWallFunction','0','0'),
 ('alphat','[1 -1 -1 0 0 0 0]','0','compressible::alphatWallFunction','0','0')]:
 bc={key:f'type {wall}; value uniform {initial};' for key in wallkeys}
 if name in ('k','omega'):
  bc['hotGasInlet']=f'type fixedValue; value uniform {jetval};'
  bc['farfield']=f'type inletOutlet; inletValue uniform {ambient}; value uniform {ambient};'
 else:
  bc['hotGasInlet']=f'type calculated; value uniform {jetval};'
  bc['farfield']=f'type calculated; value uniform {ambient};'
 field(name,'volScalarField',dims,initial,bc)
(C/'midnight_ground.foam').touch()
print(json.dumps({'case':str(C),'mesh_vertices':n,'CAD_deviation_mm':error*1000,'solver':'buoyantPimpleFoam v2506','end_time_s':15},indent=2))
