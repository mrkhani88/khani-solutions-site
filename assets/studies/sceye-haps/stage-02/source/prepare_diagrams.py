"""Add native OMEdit component placements, icons and connection lines; export matching hierarchy."""
from pathlib import Path
import re,json
B=Path(__file__).resolve().parents[1];p=B/'source/HAPSDiurnal.mo';s=p.read_text()
# First-iteration candidate conductances and effective radiator areas, not selected hardware.
s=s.replace('dcContact(G=12),mpptContact(G=10),strap(G=5*strapScale)','dcContact(G=20),mpptContact(G=25),strap(G=25*strapScale)').replace('boundary(A=2,ny=-0.8660254038','boundary(A=3.12,ny=-0.8660254038').replace('strap(G=7*strapScale)','strap(G=15*strapScale)').replace('boundary(A=3,ny=0.8660254038','boundary(A=3.12,ny=0.8660254038').replace('A=area/4-3.655','A=area/4-3.903')
classes=['Avionics','Battery','Payload','Propulsion','HullSolar','Structure','PowerManager','IntegratedMission']
types=['ThermalMass','Heater','ExternalSurface','Modelica.Thermal.HeatTransfer.Components.ThermalConductor','MissionEnvironment','HullSolar','Avionics','Battery','Payload','Propulsion','Structure','PowerManager']
ports=['Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a','Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b','Modelica.Blocks.Interfaces.RealInput','Modelica.Blocks.Interfaces.RealOutput','EnvironmentBus']
registry=json.loads((B/'inputs/model-hierarchy.json').read_text()) if (B/'inputs/model-hierarchy.json').exists() else {}
def split(text):
 parts=[];level=0;start=0
 for i,c in enumerate(text):
  if c=='(':level+=1
  elif c==')':level-=1
  elif c==',' and level==0:parts.append(text[start:i].strip());start=i+1
 parts.append(text[start:].strip());return parts
for cls in classes:
 match=re.search(r'^  model '+cls+r'\b.*?^  end '+cls+r';',s,re.S|re.M);block=match.group(0)
 if 'STAGE02_NATIVE_DIAGRAM' in block:continue
 instances=[]
 for typ in types:
  for m in re.finditer(r'(?m)^    '+re.escape(typ)+r' ([^;\n]+);',block):
   for decl in split(m.group(1)):
    name=re.match(r'\w+',decl).group();instances.append({'name':name,'type':typ,'declaration':decl})
 order={'environment':[-240,150],'hull':[-80,150],'power':[140,150],'avionics':[-240,-10],'battery':[-80,-10],'payload':[80,-10],'propulsion':[240,-10],'structure':[0,-160]}
 for i,node in enumerate(instances):
  pos=order.get(node['name']) if cls=='IntegratedMission' else None
  if pos is None:pos=[-240+(i%4)*160,140-(i//4)*80]
  node['position']=pos
 for typ in types:
  def replace(m):
   declarations=[]
   for d in split(m.group(1)):
    name=re.match(r'\w+',d).group();x,y=next(z['position'] for z in instances if z['name']==name);declarations.append(d+f' annotation(Placement(transformation(extent={{{{{x-45},{y-22}}},{{{x+45},{y+22}}}}})))')
   return '    '+typ+' '+',\n      '.join(declarations)+';'
  block=re.sub(r'(?m)^    '+re.escape(typ)+r' ([^;\n]+);',replace,block)
 conns=re.findall(r'connect\((\w+(?:\.\w+)*),(\w+(?:\.\w+)*)\);',block)
 positions={n['name']:n['position'] for n in instances}
 def annotate_conn(m):
  a,c=m.groups();pa=positions.get(a.split('.')[0],[-290,0]);pc=positions.get(c.split('.')[0],[290,0]);color='{0,105,135}' if ('env' in a or 'env' in c or 'bus' in a or 'bus' in c) else '{165,85,25}' if ('port' in a or 'port' in c or a in ['mount','hull'] or c in ['mount','hull']) else '{40,80,150}'
  return f'connect({a},{c}) annotation(Line(points={{{{{pa[0]},{pa[1]}}},{{{pc[0]},{pc[1]}}}}},color={color}));'
 block=re.sub(r'connect\((\w+(?:\.\w+)*),(\w+(?:\.\w+)*)\);',annotate_conn,block)
 icon='Icon(coordinateSystem(extent={{-100,-100},{100,100}}),graphics={Rectangle(extent={{-90,65},{90,-65}},lineColor={25,90,110},fillColor={231,243,248},fillPattern=FillPattern.Solid),Text(extent={{-85,50},{85,-30}},textString="'+cls+'")})'
 diagram='Diagram(coordinateSystem(extent={{-320,-260},{320,220}}))'
 if cls=='IntegratedMission':block=block.replace('annotation(experiment(', 'annotation('+diagram+','+icon+',experiment(')
 else:block=block.replace('  end '+cls+';', '    annotation('+diagram+','+icon+');\n  end '+cls+';')
 block=block.replace('  end '+cls+';', '    // STAGE02_NATIVE_DIAGRAM\n  end '+cls+';')
 s=s[:match.start()]+block+s[match.end():]
 registry[cls]={'components':instances,'connections':[{'a':a,'b':c} for a,c in conns],'rendering_scope':'Source-derived connection graph with native placements; not an OMEdit screenshot. Open the .mo file in OMEdit for native diagrams.'}
p.write_text(s);(B/'inputs/model-hierarchy.json').write_text(json.dumps(registry,indent=2)+'\n')
print('Native Modelica diagrams prepared for',len(registry),'hierarchical models.')
