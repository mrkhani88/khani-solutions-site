"""Editable QElectroTech concept drawings and matching portable SVGs.

Native diagram primitives, not an electrical netlist or a hydraulic solver.
All dimensions/ratings remain design assumptions. Run on Intel with Python 3.
"""
from pathlib import Path
import xml.etree.ElementTree as E
import html, json

OUT=Path(__file__).resolve().parents[1]/'diagram'
OUT.mkdir(exist_ok=True)
BLUE='#167bac'; ORANGE='#cb552d'; INK='#17394d'; GRAY='#667a86'; GREEN='#307d67'
W,H=1440,960
root=E.Element('project',version='0.90',title='Data-center cooling | Stage 02 | Design R1')
E.SubElement(root,'properties')
new=E.SubElement(root,'newdiagrams')
E.SubElement(new,'border',cols='24',colsize='60',rows='12',rowsize='80',displaycols='false',displayrows='false')
E.SubElement(new,'inset',title='Concept review - not for construction',author='Mohammadreza Khani',date='20261023',folio='%id/%total')

class Sheet:
 def __init__(self,num,title,sub):
  self.num=num; self.title=title
  self.d=E.SubElement(root,'diagram',version='0.90',title=title,author='Mohammadreza Khani',date='20261023',folio='%id/%total',cols='24',colsize='60',rows='12',rowsize='80',height='980',displayrows='false',displaycols='false',order=str(num),filename='DC-HYD-R1')
  E.SubElement(self.d,'defaultconductor',type='simple')
  self.shapes=E.SubElement(self.d,'shapes');self.inputs=E.SubElement(self.d,'inputs')
  self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="1440" height="960" fill="white"/>']
  self.text(38,31,'KHANI SOLUTIONS  /  DATA-CENTER HYDRAULICS',13,GRAY,True)
  self.text(38,61,title,27,INK,True);self.text(38,106,sub,14,GRAY)
  self.line([(38,139),(1402,139)],INK,1)
  self.text(38,919,f'DC-HYD-0{num}  |  R1  |  23 OCT 2026  |  Concept for review; not construction documentation',13,GRAY)
 def text(self,x,y,t,size=14,color=INK,bold=False):
  # QGraphicsTextItem has a 4 px document margin. Use explicit pixel sizing.
  qhtml=f'<html><body style="margin:0;font-family:DejaVu Sans;font-size:{size}px;color:{color};font-weight:{700 if bold else 400}"><p style="margin:0">{html.escape(t)}</p></body></html>'
  E.SubElement(self.inputs,'input',x=str(x-4),y=str(y-4),rotation='0',text=qhtml,font=f'DejaVu Sans,{size},-1,5,{75 if bold else 50},0,0,0,0,0')
  self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="hanging" font-family="DejaVu Sans,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(t)}</text>')
 def shape(self,typ,attrs,color,width=2,fill=None,dash=False,points=None):
  a={'type':typ,'is_movable':'1','z':'0','closed':'1' if fill else '0',**{k:str(v) for k,v in attrs.items()}}
  q=E.SubElement(self.shapes,'shape',a)
  E.SubElement(q,'pen',style='DashLine' if dash else 'SolidLine',color=color,widthF=str(width))
  E.SubElement(q,'brush',style='SolidPattern' if fill else 'NoBrush',color=fill or color)
  if points:
   ps=E.SubElement(q,'points')
   for x,y in points:E.SubElement(ps,'point',x=str(x),y=str(y))
 def line(self,points,color=INK,width=2,dash=False):
  self.shape('Polygon',{},color,width,None,dash,points)
  pts=' '.join(f'{x},{y}' for x,y in points)
  self.svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="6 5"' if dash else '')+'/>')
 def poly(self,points,color=INK,fill='white',width=2):
  self.shape('Polygon',{},color,width,fill,False,points+[points[0]])
  self.svg.append(f'<polygon points="'+ ' '.join(f'{x},{y}' for x,y in points)+f'" fill="{fill}" stroke="{color}" stroke-width="{width}"/>')
 def box(self,x,y,w,h,color=INK,fill='white',dash=False):
  self.shape('Rectangle',dict(x1=x,y1=y,x2=x+w,y2=y+h,rx=0,ry=0),color,1.6,fill,dash)
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{color}" stroke-width="1.6"'+(' stroke-dasharray="6 5"' if dash else '')+'/>')
 def circle(self,x,y,r,color=INK,fill='white'):
  self.shape('Ellipse',dict(x1=x-r,y1=y-r,x2=x+r,y2=y+r),color,1.8,fill)
  self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{color}" stroke-width="1.8"/>')
 def arrow(self,x,y,dx=1,dy=0,color=BLUE):
  self.poly([(x+dx*9,y+dy*9),(x-dx*7-dy*5,y-dy*7+dx*5),(x-dx*7+dy*5,y-dy*7-dx*5)],color,color,1)
 def valve(self,x,y,vertical=False,color=INK):
  p=[(-11,-7),(11,7),(11,-7),(-11,7)]
  if vertical:p=[(-b,a) for a,b in p]
  self.poly([(x+a,y+b) for a,b in p],color,'white',1.5)
 def instrument(self,x,y,label,color=INK,r=19):
  self.circle(x,y,r,color);self.text(x-r+4,y-7,label,11,color,True)
 def save(self,name):
  (OUT/(name+'.svg')).write_text(''.join(self.svg)+'</svg>')

s=Sheet(1,'01  /  The complete cooling loop','Ten parallel racks x 100 kW liquid load | 35 / 45 C rack coolant | facility boundary 25 / 35 C, illustrative')
# Separate circuits share a thermal exchanger only.
s.box(169,350,136,210,INK,'#f1f6f8');s.text(189,365,'HX-101',21,INK,True)
s.line([(214,410),(214,530)],GREEN,4);s.line([(262,410),(262,530)],BLUE,4)
for y in [426,450,474,498]:s.line([(225,y),(249,y-12)],GRAY,1)
s.arrow(214,478,0,1,GREEN);s.arrow(262,478,0,-1,BLUE)
s.text(183,574,'Plate heat exchanger',13);s.text(192,595,'1 MW target',13,GRAY)
s.line([(40,420),(169,420)],GREEN,3);s.arrow(125,420,1,0,GREEN)
s.line([(169,510),(40,510)],GREEN,3);s.arrow(98,510,-1,0,GREEN)
s.text(40,375,'FWS supply',13,GREEN,True);s.text(40,395,'25 C',13,GREEN);s.text(40,532,'FWS return',13,GREEN,True);s.text(40,552,'~35 C',13,GREEN)
s.text(40,637,'Facility plant is a boundary.',13,GRAY);s.text(40,659,'Site heat rejection is selected later.',13,GRAY)
s.text(172,318,'Two fluids do not mix',14,INK,True)
# TCS suction and pump branches.
s.line([(305,420),(390,420)],BLUE,3)
s.line([(390,290),(390,550)],BLUE,3);s.line([(720,290),(720,550)],BLUE,3)
for i,y in enumerate([310,420,530]):
 col=BLUE if i<2 else GRAY
 s.line([(390,y),(720,y)],col,2.5,dash=i==2)
 s.valve(445,y,color=col);s.circle(520,y,25,col);s.poly([(508,y-16),(508,y+16),(540,y)],col,'white',1.5)
 s.poly([(602,y-10),(622,y),(602,y+10)],col,'white',1.5);s.line([(625,y-12),(625,y+12)],col,1.5);s.valve(674,y,color=col)
 s.text(483,y-56,f'P-101{chr(65+i)}',17,col,True)
 s.text(478,y+32,'Duty' if i<2 else 'Standby',12,col)
s.text(407,606,'Three 50% pumps: two running + one standby',14,INK,True)
s.text(408,631,'Stage 01 / duty: 43.4 m3/h at ~27.5 m head',13,GRAY)
s.text(408,653,'Curves, motor sizing and standby logic: next stage',13,GRAY)
s.text(410,699,'Each branch: isolation -> pump -> check -> isolation',12,GRAY)
# Expansion reference and pump suction pressure.
s.line([(390,290),(390,224),(337,224)],BLUE,2)
s.box(280,181,57,86,GREEN,'#f1f8f4');s.line([(282,224),(335,224)],GREEN,1,dash=True)
s.text(265,151,'EV-101 / fill',14,GREEN,True)
s.text(280,275,'Size / precharge TBD',11,GRAY)
s.line([(352,420),(352,368)],GRAY,1);s.instrument(352,348,'PT-S',GRAY)
# Discharge and filtration.
s.line([(720,310),(1180,310),(1180,420)],BLUE,3);s.arrow(768,310)
s.box(807,279,95,62,INK,'#f1f6f8');s.line([(821,329),(889,292)],GRAY,2);s.text(815,285,'F-101 A/B',12,INK,True)
s.text(787,351,'Duplex filter',14);s.text(786,373,'No open bypass',12,GRAY)
s.line([(785,310),(785,237),(930,237),(930,310)],GRAY,1,dash=True);s.instrument(855,237,'PDT',GRAY)
s.line([(748,310),(748,250)],GRAY,1);s.instrument(748,230,'PT-D',GRAY)
s.instrument(1100,310,'FT',BLUE);s.line([(1020,310),(1020,263)],GRAY,1);s.instrument(1020,245,'TT-S',GRAY)
s.arrow(1140,310)
s.text(1036,351,'H-101 supply',15,BLUE,True);s.text(1043,375,'125 mm clear ID',13,BLUE)
# Relief branch to safe collection, no claimed setting.
s.line([(970,310),(970,180),(1275,180)],GRAY,1.8)
s.valve(1050,180,color=GRAY);s.text(1012,151,'PSV-101',13,GRAY,True);s.arrow(1250,180,1,0,GRAY)
s.text(1118,202,'Safe collection / setting TBD',12,GRAY)
# Downstream rack block and critical DP feedback.
s.box(1098,420,164,159,INK,'#eff5f8');s.text(1116,440,'R-01 ... R-10',17,INK,True)
s.text(1115,476,'Ten parallel racks',13);s.text(1124,501,'100 kW / rack',13);s.text(1113,530,'144.7 L/min / rack',13,BLUE)
s.arrow(1180,400,0,1)
s.line([(1180,579),(1180,725),(305,725),(305,510)],ORANGE,3)
s.arrow(1180,636,0,1,ORANGE);s.arrow(972,725,-1,0,ORANGE);s.arrow(305,630,0,-1,ORANGE)
s.text(815,744,'H-102 return | 125 mm clear ID | nominal 45 C',14,ORANGE,True)
s.line([(1070,725),(1070,675)],GRAY,1);s.instrument(1070,656,'TT-R',GRAY)
s.line([(1180,397),(1324,397),(1324,585),(1180,585)],GRAY,1,dash=True);s.instrument(1324,487,'PDT',GRAY)
s.text(1290,531,'Critical',12,GRAY);s.text(1290,550,'rack DP',12,GRAY)
s.text(1101,594,'See Sheet 02 for branches',12,GRAY)
s.line([(775,725),(775,777)],GRAY,1.5);s.valve(775,755,True,GRAY);s.arrow(775,777,0,1,GRAY);s.text(805,767,'DV-101 low-point drain',12,GRAY)
for x,title,lines in [(38,'1  /  Set the duty',['1 MW into liquid, plus pump heat.','Residual room-air load is separate.']),(496,'2  /  Move and distribute',['Pump speed will regulate rack DP.','Branch balancing remains necessary.']),(953,'3  /  Protect and maintain',['Provide vents, drains and leak detection.','Pressure ratings / relief remain TBD.'])]:
 s.box(x,817,440,79,'#d8e4ea','#f6f9fb');s.text(x+14,828,title,15,INK,True)
 for i,t in enumerate(lines):s.text(x+14,852+i*18,t,12,GRAY)
s.save('01-system-piping')

s=Sheet(2,'02  /  The ten parallel rack branches','Direct-return baseline | each branch is individually isolatable and balanceable | diagram is schematic, not to scale')
s.text(38,169,'SUPPLY FROM SHEET 01  ->  H-101  |  35 C  |  125 mm clear ID',16,BLUE,True)
s.line([(50,245),(1385,245)],BLUE,3);s.arrow(90,245)
s.line([(1385,710),(50,710)],ORANGE,3);s.arrow(90,710,-1,0,ORANGE)
s.text(38,737,'RETURN TO SHEET 01  <-  H-102  |  nominal 45 C  |  125 mm clear ID',16,ORANGE,True)
for i in range(10):
 x=150+i*125;n=i+1
 s.line([(x,245),(x,420)],BLUE,2);s.line([(x,530),(x,710)],ORANGE,2)
 s.circle(x,245,3,BLUE,BLUE);s.circle(x,710,3,ORANGE,ORANGE)
 s.valve(x,303,True,BLUE);s.text(x-43,269,f'IV-{201+i}S',11,BLUE)
 s.instrument(x,368,'FI',BLUE,17);s.text(x-27,392,f'FI-{201+i}',10,GRAY)
 s.box(x-42,420,84,110,INK,'#f1f6f8');s.text(x-29,436,f'R-{n:02d}',18,INK,True)
 s.text(x-26,469,'100 kW',12);s.text(x-32,494,'Rack HX /',11,GRAY);s.text(x-33,510,'cold plates',11,GRAY)
 s.valve(x,588,True,ORANGE);s.text(x-38,606,f'BV-{201+i}',11,ORANGE)
 s.valve(x,663,True,ORANGE);s.text(x-42,680,f'IV-{201+i}R',11,ORANGE)
 s.arrow(x,332,0,1,BLUE);s.arrow(x,553,0,1,ORANGE)
s.line([(1385,245),(1385,206)],BLUE,1.5);s.valve(1385,219,True,BLUE);s.text(1237,187,'AV-101 high-point vent',12,BLUE)
s.line([(1385,710),(1385,662)],ORANGE,1.5);s.valve(1385,679,True,ORANGE);s.text(1310,622,'AV-102',12,ORANGE);s.text(1301,642,'Return vent',12,ORANGE)
s.text(41,788,'Each rack design target: 2.412 L/s = 144.7 L/min. Branch clear ID: 40 mm. Equal heat loads do not guarantee equal flow.',14,INK,True)
s.text(41,819,'IV = isolation valve | FI = flow indication | BV = balancing valve | AV = air vent. Ports / QDs at rack connection: vendor selection pending.',13,GRAY)
s.text(41,848,'Critical-rack differential pressure uses supply and return taps; control sensor placement is checked in the OpenModelica network.',13,GRAY)
s.text(41,877,'Initial rack internal loss: assumed 100 kPa at design flow. Actual rack curves, fitting losses and valve settings are not yet selected.',13,GRAY)
s.save('02-rack-branches')

E.indent(root,space='  ')
E.ElementTree(root).write(OUT/'DataCenter_Piping_R1.qet',encoding='utf-8',xml_declaration=True)
print(json.dumps({'project':str(OUT/'DataCenter_Piping_R1.qet'),'folios':2,'native_shapes':len(root.findall('.//shape')),'native_texts':len(root.findall('.//input')),'note':'Editable native drawing primitives. Graphical P&ID only; no simulated hydraulic connectivity.'},indent=2))
