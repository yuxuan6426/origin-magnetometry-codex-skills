"""Generate the deterministic teaching DAT; this is not experimental data."""
import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output file.')
    rows = [[i, 2 + i * 2, 1000, (2 + i * 2) * 1e-5, '', ''] for i in range(15)]
    rows += [[15 + i, 30 - i * 2, 1000, (30 - i * 2) * 1.1e-5, '', ''] for i in range(15)]
    fields = [0,5000,10000,5000,0,-5000,-10000,-5000,0,5000,10000]
    rows += [[100 + i, 5, value, '', value * 1e-7 + ((1 if i < 5 else -1) * .0001), value * 1e-7]
             for i, value in enumerate(fields)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='', encoding='utf-8') as stream:
        stream.write('[Header]\nINFO,Synthetic teaching data,COMMENT\n[Data]\n')
        writer = csv.writer(stream)
        writer.writerow(['Time Stamp (sec)','Temperature (K)','Magnetic Field (Oe)','Moment (emu)',
                         'DC Moment Fixed Ctr (emu)','DC Moment Free Ctr (emu)'])
        writer.writerows(rows)


if __name__ == '__main__':
    main()
