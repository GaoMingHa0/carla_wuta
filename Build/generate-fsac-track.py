"""Generate an analytic, closed FSAC-style track from supplied constraints."""
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out = Path('/home/wuta/carla/Build/fsac-track')
out.mkdir(exist_ok=True)
width = 3.5
points = np.array([(0,0),(65,0),(80,15),(65,30),(25,30),(25,45),
                   (65,45),(80,60),(60,85),(10,85),(-15,65),(-10,40),(-25,20)],float)
points += (40,20)
radii = [10,8,10,8,7,7,8,10,10,12,10,6,9]
corners=[]
for i,p in enumerate(points):
    a=p-points[i-1];a/=np.linalg.norm(a)
    b=points[(i+1)%len(points)]-p;b/=np.linalg.norm(b)
    turn=math.atan2(float(np.cross(a,b)),float(a@b))
    d=radii[i]*math.tan(abs(turn)/2)
    enter=p-a*d;leave=p+b*d
    sign=1 if turn>0 else -1
    centre=enter+sign*radii[i]*np.array([-a[1],a[0]])
    corners.append(dict(enter=enter,leave=leave,centre=centre,turn=turn,radius=radii[i]))

segments=[]
for i,c in enumerate(corners):
    j=(i+1)%len(points);n=corners[j]
    delta=n['enter']-c['leave']
    # A negative projection would mean adjacent corner fillets overlap.
    assert delta@(points[j]-points[i])>0, ('Overlapping fillets',i)
    heading=math.atan2(delta[1],delta[0])
    segments.append(dict(type='line',x=float(c['leave'][0]),y=float(c['leave'][1]),
                         heading=heading,length=float(np.linalg.norm(delta)),curvature=0))
    segments.append(dict(type='arc',x=float(n['enter'][0]),y=float(n['enter'][1]),heading=heading,
                         length=abs(n['turn'])*n['radius'],curvature=math.copysign(1/n['radius'],n['turn'])))
s=0
for seg in segments:seg['s']=s;s+=seg['length']
length=s

def at(distance):
    distance%=length
    seg=next(x for x in segments if distance<x['s']+x['length']+1e-9)
    d=distance-seg['s'];h=seg['heading'];k=seg['curvature']
    if k:
        x=seg['x']+(math.sin(h+k*d)-math.sin(h))/k
        y=seg['y']-(math.cos(h+k*d)-math.cos(h))/k
    else:x=seg['x']+d*math.cos(h);y=seg['y']+d*math.sin(h)
    h+=k*d
    return np.array([x,y]),np.array([-math.sin(h),math.cos(h)]),h

samples=[]
for d in np.linspace(0,length,math.ceil(length/.25)+1):
    p,n,h=at(float(d));samples.append({'s':float(d),'x':float(p[0]),'y':float(p[1]),'yaw_rad':h})
centre=np.array([[p['x'],p['y']] for p in samples])
normals=np.array([[-math.sin(p['yaw_rad']),math.cos(p['yaw_rad'])] for p in samples])
left=centre+normals*width/2;right=centre-normals*width/2

def intersects(a,b,c,d):
    if np.any(np.maximum(a,b)<np.minimum(c,d)) or np.any(np.maximum(c,d)<np.minimum(a,b)):return False
    cross=lambda u,v:float(u[0]*v[1]-u[1]*v[0])
    return cross(b-a,c-a)*cross(b-a,d-a)<-1e-10 and cross(d-c,a-c)*cross(d-c,b-c)<-1e-10
for boundary in (left,right):
    for i in range(len(boundary)-1):
        for j in range(i+2,len(boundary)-1):
            if i==0 and j==len(boundary)-2:continue
            assert not intersects(boundary[i],boundary[i+1],boundary[j],boundary[j+1]),'Self intersection'

cones=[]
for seg in segments:
    gap=2.5 if seg['type']=='arc' else 4.0
    count=math.ceil(seg['length']/gap)
    for d in np.linspace(seg['s'],seg['s']+seg['length'],count,endpoint=False):
        p,n,_=at(float(d))
        for side,sign,colour in [('left',1,'Blue'),('right',-1,'Red')]:
            q=p+sign*n*(width/2+.1)
            cones.append({'s':float(d),'x':float(q[0]),'y':float(q[1]),'side':side,'colour':colour})
# Start/finish lies on the first straight, 8m after its beginning.
start_s=8.0
for d in (start_s-.75,start_s+.75):
    p,n,_=at(d)
    for sign in (-1,1):
        q=p+sign*n*(width/2+.1)
        cones.append({'s':d,'x':float(q[0]),'y':float(q[1]),'side':'start_finish','colour':'Yellow'})

with (out/'FSAC_Road.obj').open('w') as f:
    f.write('o FSAC_Road\n')
    for a,b in zip(left,right):
        for p in (a,b):f.write('v %.8f %.8f 0\n'%(p[0]*100,p[1]*100))
    for i in range(len(left)):
        f.write('vt 0 %.8f\nvt 1 %.8f\n'%(samples[i]['s']/width,samples[i]['s']/width))
    for i in range(len(left)-1):
        a=2*i+1;b=a+1;c=a+2;d=a+3
        f.write('f %d/%d %d/%d %d/%d\n'%(a,a,b,b,c,c))
        f.write('f %d/%d %d/%d %d/%d\n'%(b,b,d,d,c,c))

spawn,_,yaw=at(start_s-3)
report={'length_m':length,'laps':3,'total_race_distance_m':3*length,'width_m':width,
        'longest_straight_m':max(x['length'] for x in segments if x['type']=='line'),
        'minimum_centreline_radius_m':min(radii),'hairpin_centreline_radius_m':7,
        'hairpin_outer_diameter_m':2*(7+width/2),'cone_count':len(cones),
        'start_s_m':start_s,'spawn':{'x':float(spawn[0]),'y':float(spawn[1]),'yaw_deg':math.degrees(yaw)},
        'constraints_pass':200<=length<=500 and max(x['length'] for x in segments if x['type']=='line')<=80 and width>=3 and 2*(7+width/2)>=9,
        'boundary_self_intersections':0,
        'coordinate_system':'metres, Unreal XY; CARLA API uses same XY; OpenDRIVE Y reflected',
        'basis':'User supplied D9.2 excerpts; geometric design check, not competition certification'}
data={'report':report,'segments':segments,'centreline':samples,'cones':cones}
(out/'track.json').write_text(json.dumps(data,indent=2)+'\n')
(out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')

geometry=[]
for seg in segments:
    shape='<line/>' if seg['type']=='line' else '<arc curvature="%.12f"/>'%(-seg['curvature'])
    geometry.append('<geometry s="%.10f" x="%.10f" y="%.10f" hdg="%.12f" length="%.10f">%s</geometry>'%(seg['s'],seg['x'],-seg['y'],-seg['heading'],seg['length'],shape))
xodr='''<?xml version="1.0"?><OpenDRIVE>
<header revMajor="1" revMinor="4" name="FSACLoop" version="1.0"><geoReference><![CDATA[+proj=tmerc +lat_0=31 +lon_0=121 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs]]></geoReference></header>
<road name="FSACLoop" length="%.10f" id="1" junction="-1">
<link><predecessor elementType="road" elementId="1" contactPoint="end"/><successor elementType="road" elementId="1" contactPoint="start"/></link>
<type s="0" type="town"><speed max="30" unit="m/s"/></type>
<planView>%s</planView><elevationProfile><elevation s="0" a="0" b="0" c="0" d="0"/></elevationProfile><lateralProfile/>
<lanes><laneOffset s="0" a="1.75" b="0" c="0" d="0"/><laneSection s="0"><center><lane id="0" type="none" level="false"/></center>
<right><lane id="-1" type="driving" level="false"><link><predecessor id="-1"/><successor id="-1"/></link><width sOffset="0" a="3.5" b="0" c="0" d="0"/></lane></right></laneSection></lanes><objects/><signals/>
</road></OpenDRIVE>'''%(length,''.join(geometry))
# Use one road per analytic segment so CARLA follows explicit inter-road links.
import xml.etree.ElementTree as ET
xml=ET.fromstring(xodr)
template=ET.tostring(xml.find('road'))
xml.remove(xml.find('road'))
for i,seg in enumerate(segments):
    road=ET.fromstring(template)
    road.set('id',str(i+1));road.set('length','%.10f'%seg['length'])
    road.find('link/predecessor').set('elementId',str((i-1)%len(segments)+1))
    road.find('link/successor').set('elementId',str((i+1)%len(segments)+1))
    plan=road.find('planView')
    for child in list(plan):plan.remove(child)
    geo=ET.fromstring(geometry[i]);geo.set('s','0');plan.append(geo)
    xml.append(road)
(out/'FSACLoop.xodr').write_text(ET.tostring(xml,encoding='unicode'))

fig,ax=plt.subplots(figsize=(12,10),facecolor='#fafafa')
ax.fill(np.r_[left[:,0],right[::-1,0]],np.r_[left[:,1],right[::-1,1]],color='#4b5058')
ax.plot(centre[:,0],centre[:,1],'--',color='white',lw=.8,alpha=.5)
for colour,hexcode in [('Red','#eb3b31'),('Blue','#009fdd'),('Yellow','#e7bd00')]:
    cs=[c for c in cones if c['colour']==colour];ax.scatter([c['x'] for c in cs],[c['y'] for c in cs],s=13,c=hexcode,label=colour+' cones',zorder=3)
p,n,h=at(start_s);a=p-n*width/2;b=p+n*width/2
ax.plot([a[0],b[0]],[a[1],b[1]],c='yellow',lw=3,zorder=4)
ax.annotate('START / FINISH · 3 laps',p,xytext=(p[0]+4,p[1]-12),arrowprops={'arrowstyle':'->'},fontsize=11)
p,_,h=at(start_s+10);ax.arrow(*p,5*math.cos(h),5*math.sin(h),width=.3,color='white',zorder=4)
ax.annotate('Hairpin: outer diameter 17.5 m',(63,57),xytext=(45,67),arrowprops={'arrowstyle':'->'},fontsize=10)
ax.set_title('FSAC high-speed tracking · closed loop\n%.1f m / lap · %.1f m wide · max straight %.1f m'%(length,width,report['longest_straight_m']),fontsize=16,pad=18)
ax.set_aspect('equal');ax.set_xlabel('X (m)');ax.set_ylabel('Y (m)');ax.grid(alpha=.16);ax.legend(loc='upper right')
fig.tight_layout();fig.savefig(out/'track-layout.png',dpi=170);plt.close(fig)
print(json.dumps(report,indent=2))
