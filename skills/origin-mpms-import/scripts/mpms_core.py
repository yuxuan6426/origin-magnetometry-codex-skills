"""Portable MPMS3 parsing, chronological segmentation and normalization."""
from __future__ import annotations
import csv, hashlib, io, math, statistics
from dataclasses import dataclass, field
from pathlib import Path

TEMPERATURE='Temperature (K)'
FIELD='Magnetic Field (Oe)'
VSM='Moment (emu)'
DC_FIXED='DC Moment Fixed Ctr (emu)'
DC_FREE='DC Moment Free Ctr (emu)'

class DataError(ValueError):
    pass

def numeric(value):
    if value is None or str(value).strip() in ('','--','---'): return None
    try:
        result=float(str(value).replace('D','E').replace('d','e'))
        return result if math.isfinite(result) else None
    except ValueError:
        return None

@dataclass
class Record:
    number:int
    physical_line:int
    temperature:float
    field:float
    timestamp:float|None
    mode:str
    moments:dict

@dataclass
class Dataset:
    filename:str
    sha256:str
    encoding:str
    header:list
    column_names:list
    records:list[Record]

@dataclass
class Curve:
    id:str
    category:str
    mode:str
    records:list[Record]
    direction:str=''
    warnings:list[str]=field(default_factory=list)

    @property
    def label(self):
        t=statistics.median(r.temperature for r in self.records)
        h=statistics.median(r.field for r in self.records)
        if self.category=='MT':return f'MT {self.mode} {self.direction} H={h:.1f} Oe'
        suffix='initial' if self.category=='MH_initial' else ('loop' if self.category=='MH_loop' else 'partial')
        return f'MH {self.mode} T={t:.2f} K {suffix} {self.id}'

def parse_dat(path):
    path=Path(path); raw=path.read_bytes()
    for encoding in ('utf-8-sig','gb18030'):
        try:text=raw.decode(encoding);break
        except UnicodeDecodeError:pass
    else:raise DataError('File encoding must be UTF-8 or GB18030.')
    lines=text.splitlines()
    marker=next((i for i,s in enumerate(lines) if s.strip().casefold()=='[data]'),None)
    if marker is None:raise DataError('MPMS [Data] marker is missing.')
    reader=csv.reader(lines[marker+1:]); headers=next(reader,[])
    headers=[h.strip() for h in headers]
    if len(set(headers))!=len(headers):raise DataError('Data column names are duplicated.')
    for required in (TEMPERATURE,FIELD):
        if required not in headers:raise DataError(f'Required column is missing: {required}')
    if not any(h in headers for h in (VSM,DC_FIXED,DC_FREE)):raise DataError('No recognized magnetic-moment column.')
    records=[]
    for line_number,values in enumerate(reader,start=marker+3):
        if not any(v.strip() for v in values):continue
        if len(values)!=len(headers):raise DataError(f'Line {line_number}: expected {len(headers)} fields, got {len(values)}.')
        row=dict(zip(headers,values)); t=numeric(row[TEMPERATURE]);h=numeric(row[FIELD])
        if t is None or h is None:raise DataError(f'Line {line_number}: temperature or field is not finite.')
        moments={k:numeric(row.get(k)) for k in (VSM,DC_FIXED,DC_FREE)}
        has_vsm=moments[VSM] is not None;has_dc=any(moments[k] is not None for k in (DC_FIXED,DC_FREE))
        if has_vsm==has_dc:raise DataError(f'Line {line_number}: magnetic-moment mode is ambiguous or missing; inspect this record.')
        records.append(Record(len(records)+1,line_number,t,h,numeric(row.get('Time Stamp (sec)')),'VSM' if has_vsm else 'DC',moments))
    if not records:raise DataError('No measurement records.')
    return Dataset(path.name,hashlib.sha256(raw).hexdigest(),encoding,lines[:marker],headers,records)

def chunks(records,key):
    if not records:return []
    result=[];current=[records[0]]
    for row in records[1:]:
        if key(row)!=key(current[-1]):result.append(current);current=[]
        current.append(row)
    result.append(current);return result

def split_mt(rows):
    """Split a thermal reversal only after three consistent significant steps."""
    if len(rows)<4:return [(rows,'warming' if rows[-1].temperature>=rows[0].temperature else 'cooling')]
    signs=[0]+[(1 if d>0.15 else -1 if d<-.15 else 0) for d in [rows[i].temperature-rows[i-1].temperature for i in range(1,len(rows))]]
    direction=next((s for s in signs if s),1);start=0;parts=[]
    for i in range(1,len(rows)):
        if signs[i] and signs[i]!=direction:
            future=[s for s in signs[i:] if s][:3]
            if len(future)==3 and all(s==-direction for s in future):
                extremum=(max if direction==1 else min)(range(start,i+1),key=lambda j:rows[j].temperature)
                boundary=extremum+1
                parts.append((rows[start:boundary],'warming' if direction==1 else 'cooling'))
                start=boundary;direction=-direction
    parts.append((rows[start:],'warming' if direction==1 else 'cooling'))
    return parts

def split_temperature(rows,tolerance):
    parts=[];current=[]
    for row in rows:
        anchor=statistics.median(r.temperature for r in current) if current else row.temperature
        if current and abs(row.temperature-anchor)>tolerance:
            parts.append(current);current=[]
        current.append(row)
    if current:parts.append(current)
    return parts

def split_field_restart(rows):
    """Separate an abrupt field restart supported by a measurement pause."""
    if len(rows)<5:return [rows]
    span=max(r.field for r in rows)-min(r.field for r in rows)
    starts=[0];steps=[]
    for i in range(1,len(rows)):
        delta=abs(rows[i].field-rows[i-1].field)
        typical=statistics.median(steps[-12:]) if steps else delta
        gap=(rows[i].timestamp-rows[i-1].timestamp) if rows[i].timestamp is not None and rows[i-1].timestamp is not None else 0
        if len(steps)>=5 and delta>max(500,5*typical,.1*span) and gap>30:
            starts.append(i);steps=[]
        elif delta>5:steps.append(delta)
    return [rows[a:b] for a,b in zip(starts,starts[1:]+[len(rows)])]

def describe_mh(rows):
    fields=[r.field for r in rows];span=max(fields)-min(fields)
    threshold=max(5,span*.0001)
    signs=[1 if b-a>threshold else -1 if b-a<-threshold else 0 for a,b in zip(fields,fields[1:])]
    signs=[s for s in signs if s];changes=sum(a!=b for a,b in zip(signs,signs[1:]))
    steps=[abs(b-a) for a,b in zip(fields,fields[1:]) if abs(b-a)>threshold]
    step=statistics.median(steps) if steps else 0
    warnings=[]
    if changes>=1 and min(fields)<-threshold and max(fields)>threshold:
        kind='MH_loop'
        if abs(fields[-1]-max(fields))>max(10,2*step):warnings.append('open_or_incomplete_cycle')
    elif changes==0 and abs(fields[0])<=max(10,.01*max(abs(x) for x in fields)):
        kind='MH_initial'
    else:kind='MH_partial';warnings.append('one_way_or_partial_sweep')
    return kind,warnings

def segment(dataset,temperature_tolerance=.5,field_tolerance=5.0,overrides=None):
    if temperature_tolerance<=0 or field_tolerance<=0:raise DataError('Segmentation tolerances must be positive.')
    if overrides is not None:
        curves=[]
        for spec in overrides:
            a,b=spec['first_record'],spec['last_record']
            if not (isinstance(a,int) and isinstance(b,int) and 1<=a<=b<=len(dataset.records)):raise DataError('Invalid explicit record interval.')
            selected=dataset.records[a-1:b]
            if len({r.mode for r in selected})!=1:raise DataError('Explicit interval mixes measurement modes.')
            if spec['category'] not in ['MT','MH_loop','MH_initial','MH_partial']:raise DataError('Invalid curve category.')
            curves.append(Curve('',spec['category'],selected[0].mode,selected,spec.get('direction',''),['explicit_segment_boundary']))
    else:
        curves=[]
        for mode_rows in chunks(dataset.records,lambda r:r.mode):
            # Long stable-field spans with substantial temperature motion identify MT.
            fixed=[];start=0;anchor=mode_rows[0].field
            for i,row in enumerate(mode_rows[1:],1):
                if abs(row.field-anchor)>field_tolerance:
                    fixed.append((start,i));start=i;anchor=row.field
            fixed.append((start,len(mode_rows)))
            mt_mask=[False]*len(mode_rows)
            for a,b in fixed:
                group=mode_rows[a:b]
                if b-a>=10 and max(r.temperature for r in group)-min(r.temperature for r in group)>=3:
                    mt_mask[a:b]=[True]*(b-a)
            start=0
            for stop in range(1,len(mode_rows)+1):
                if stop<len(mode_rows) and mt_mask[stop]==mt_mask[start]:continue
                group=mode_rows[start:stop]
                if mt_mask[start]:
                    for part,direction in split_mt(group):curves.append(Curve('','MT',part[0].mode,part,direction))
                else:
                    for platform in split_temperature(group,temperature_tolerance):
                        for part in split_field_restart(platform):
                            kind,warnings=describe_mh(part)
                            if len(part)<3:warnings.append('short_segment_review')
                            curves.append(Curve('',kind,part[0].mode,part,warnings=warnings))
                start=stop
    covered=[r.number for c in curves for r in c.records]
    if covered!=list(range(1,len(dataset.records)+1)):raise DataError('Segments must cover each record once in acquisition order.')
    for i,curve in enumerate(curves,1):curve.id=f'C{i:03d}'
    return curves

def selected_source(mode,dc_source):
    if mode=='VSM':return VSM
    if dc_source not in ('fixed','free'):raise DataError('DC source must be fixed or free.')
    return DC_FIXED if dc_source=='fixed' else DC_FREE

def curve_values(curve,mass_mg,dc_source):
    if mass_mg is not None and (not math.isfinite(mass_mg) or mass_mg<=0):raise DataError('Sample mass must be a finite positive mg value.')
    source=selected_source(curve.mode,dc_source)
    result=[]
    for row in curve.records:
        moment=row.moments[source]
        if moment is None:raise DataError(f'Record {row.number}: selected source {source} has no value.')
        result.append([row.temperature,row.field,moment,moment/mass_mg*1000 if mass_mg is not None else None])
    return result

def curve_metadata(curve,dc_source):
    t=[r.temperature for r in curve.records];h=[r.field for r in curve.records]
    return {'id':curve.id,'label':curve.label,'category':curve.category,'mode':curve.mode,'direction':curve.direction,'points':len(curve.records),
            'first_record':curve.records[0].number,'last_record':curve.records[-1].number,'first_physical_line':curve.records[0].physical_line,'last_physical_line':curve.records[-1].physical_line,
            'temperature_median_K':statistics.median(t),'temperature_range_K':[min(t),max(t)],'field_range_Oe':[min(h),max(h)],
            'moment_source':selected_source(curve.mode,dc_source),'warnings':curve.warnings}
