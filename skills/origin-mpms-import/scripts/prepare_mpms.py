#!/usr/bin/env python3
"""Inspect MPMS3 DAT or create an Origin import package."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from mpms_core import parse_dat,segment,curve_metadata,DataError

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['inspect','convert'])
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--mass-mg',type=float)
    parser.add_argument('--raw',action='store_true',help='Export raw emu without mass normalization.')
    parser.add_argument('--dc-source',choices=['fixed','free'])
    parser.add_argument('--profile',type=Path,default=Path(__file__).resolve().parents[1]/'references/mpms3-profile.json')
    parser.add_argument('--segments',type=Path,help='JSON list of explicit inclusive record intervals.')
    args=parser.parse_args()
    try:
        profile=json.loads(args.profile.read_text(encoding='utf-8'))
        dc_source=args.dc_source or profile['dc_moment_source']
        data=parse_dat(args.input)
        overrides=json.loads(args.segments.read_text(encoding='utf-8')) if args.segments else None
        curves=segment(data,profile.get('temperature_tolerance_K',.5),profile.get('field_tolerance_Oe',5),overrides)
        if args.action=='inspect':
            report={'source_file':data.filename,'records':len(data.records),'columns':len(data.column_names),'curves':[curve_metadata(c,dc_source) for c in curves]}
        else:
            if args.output is None:raise DataError('--output is required for conversion.')
            if args.raw and args.mass_mg is not None:raise DataError('Choose either --raw or --mass-mg.')
            if not args.raw and args.mass_mg is None:raise DataError('Provide the actual sample mass with --mass-mg, or explicitly choose --raw.')
            from mpms_export import export_dataset
            report=export_dataset(data,curves,None if args.raw else args.mass_mg,dc_source,args.output)
        print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
        return 0
    except (DataError,OSError,json.JSONDecodeError,ImportError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
