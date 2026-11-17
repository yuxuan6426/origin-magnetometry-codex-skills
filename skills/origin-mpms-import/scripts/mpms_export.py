"""Build Origin-ready files from one authoritative set of curve values."""
from __future__ import annotations
import csv, json, colorsys
from pathlib import Path
from mpms_core import curve_values,curve_metadata,DataError

HEADERS=['Temperature_K','Field_Oe','Moment_emu','Magnetization_emu_g']
UNITS=['K','Oe','emu','emu/g']

def json_write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def write_csv(path,headers,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(headers)
        for row in rows:
            writer.writerow(['' if v is None else format(v,'.17g') if isinstance(v,float) else v for v in row])

def style_sheet(ws,widths=None):
    from openpyxl.styles import Font,PatternFill,Alignment
    from openpyxl.utils import get_column_letter
    ws.freeze_panes='A4' if ws.title!='INDEX' else 'A2'
    ws.sheet_view.showGridLines=True
    for row in ws.iter_rows(min_row=1,max_row=min(3,ws.max_row)):
        for cell in row:
            cell.alignment=Alignment(vertical='center',wrap_text=True)
            if cell.row==1:
                cell.font=Font(name='Calibri',size=11,bold=True,color='FFFFFF')
                cell.fill=PatternFill('solid',fgColor='254B68')
            else:
                cell.font=Font(name='Calibri',size=10,color='34495E')
                cell.fill=PatternFill('solid',fgColor='EAF1F6')
    ws.row_dimensions[1].height=42 if ws.title!='INDEX' else 30
    if ws.title!='INDEX':ws.row_dimensions[2].height=20;ws.row_dimensions[3].height=45
    for col in range(1,ws.max_column+1):ws.column_dimensions[get_column_letter(col)].width=(widths[col-1] if widths and col<=len(widths) else 23)
    for row in ws.iter_rows(min_row=4 if ws.title!='INDEX' else 2):
        for cell in row:
            if isinstance(cell.value,(int,float)):cell.number_format='0.0000000000E+00'

def write_index(wb,manifest):
    ws=wb.create_sheet('INDEX',0)
    columns=['curve_id','type','mode','condition','points','source_records','moment_source','mass_mg','CSV','notes']
    ws.append(columns)
    for c in manifest['curves']:
        ws.append([c['id'],c['category'],c['mode'],c['label'],c['points'],f"{c['first_record']}-{c['last_record']}",c['moment_source'],manifest['sample_mass_mg'],c['csv'],'; '.join(c['warnings'])])
    style_sheet(ws,[12,18,10,58,12,20,35,14,24,34])
    # INDEX has ordinary data rows, rather than the three-row import header.
    from openpyxl.styles import Font,PatternFill,Alignment
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.fill=PatternFill(fill_type=None);cell.font=Font(name='Calibri',size=11,color='172B3A');cell.alignment=Alignment(vertical='top',wrap_text=True)
            if cell.column in (5,8):cell.number_format='0.########'
    ws.auto_filter.ref=ws.dimensions

def write_workbooks(output,curves,values,manifest):
    from openpyxl import Workbook
    wide=Workbook();wide.remove(wide.active)
    for category in ['MT','MH_loop','MH_initial','MH_partial']:
        selected=[c for c in curves if c.category==category]
        if not selected:continue
        ws=wide.create_sheet(category)
        ws.append([item for c in selected for item in [f'{c.id}_'+('Temperature_K' if category=='MT' else 'Field_Oe'),f'{c.id}_Moment_emu',f'{c.id}_Magnetization_emu_g']])
        ws.append([item for c in selected for item in [('K' if category=='MT' else 'Oe'),'emu','emu/g']])
        ws.append([c.label for c in selected for _ in range(3)])
        for i in range(max(len(values[c.id]) for c in selected)):
            ws.append([item for c in selected for item in ([values[c.id][i][0 if category=='MT' else 1],values[c.id][i][2],values[c.id][i][3]] if i<len(values[c.id]) else [None,None,None])])
        style_sheet(ws)
    write_index(wide,manifest);wide.save(output/'wide.xlsx')
    split=Workbook();split.remove(split.active)
    for c in curves:
        ws=split.create_sheet(c.id)
        ws.append(HEADERS);ws.append(UNITS);ws.append([c.label]*4)
        for row in values[c.id]:ws.append(row)
        style_sheet(ws)
    write_index(split,manifest);split.save(output/'per_curve.xlsx')

def generate_ogs(curves,mass_mg):
    """Only native LabTalk and CSV imports are needed on the laboratory PC."""
    ycol=4 if mass_mg is not None else 3
    ylabel='Magnetization (emu/g)' if mass_mg is not None else 'Moment (emu)'
    lines=['// MPMS data import and MT/MH plots. Origin 2018+ design target.','[Main]',
           'string mpmsRoot$;','dlgPath path:=mpmsRoot$ title:="Select the extracted MPMS data package folder";',
           'if(mpmsRoot.GetLength()==0) { type "Folder selection cancelled."; break 1; }',
           'run.section("%(mpmsRoot$)\\import_and_plot.ogs", Import);','',
           '[Import]','type "Starting MPMS import...";','if(@V<9.5) { type "Origin 2018 or newer is required by this script. CSV files can be imported manually."; break 1; }',
           'int mpmsPageCount=0;','doc -e P { mpmsPageCount++; }',
           'if(mpmsPageCount>0) { type "Please open an empty Origin project, then run the script again."; break 1; }',
           'string mpmsTarget$="%(mpmsRoot$)/origin_result.opju";',
           'if(mpmsTarget.IsFile()) { type "origin_result.opju already exists. Choose a fresh package folder or rename the existing result."; break 1; }',
           f'newbook name:=MPMSData sheet:={len(curves)} option:=lsname;']
    for i,c in enumerate(curves,1):
        lines.extend(['win -a MPMSData;',f'page.active={i};',f'layer.name$="{c.id}";',
            f'impASC fname:="%(mpmsRoot$)/csv/{c.id}.csv" options.ImpMode:=0 options.Names.AutoNames:=0 options.Names.FNameToBk:=0 options.Names.FNameToSht:=0 options.Sparklines:=0;',
            f'layer.name$="{c.id}";',
            f'if(wks.nCols!=4) {{ type "Import failed for {c.id}. Check the selected package folder."; break 1; }}',
            f'wks.col1.lname$="Temperature"; wks.col1.unit$="K";',
            'wks.col2.lname$="Magnetic Field"; wks.col2.unit$="Oe";',
            'wks.col3.lname$="Moment"; wks.col3.unit$="emu";',
            f'wks.col{ycol}.lname$="{c.label}"; wks.col{ycol}.unit$="'+('emu/g' if mass_mg is not None else 'emu')+'";'])
    lines.append(f'type "Imported {len(curves)} measurement segments. Creating graphs...";')
    def plot(c,name,new=True,overview=False,color='color(36,88,166)'):
        xcol=1 if c.category=='MT' else 2
        return f'plotxy iy:=[MPMSData]{c.id}!({xcol},{ycol}) plot:={200 if overview else 202} color:={color} ogl:='+ (f'[<new template:=line name:={name}>];' if new else f'[{name}]1!;')
    def format_graph(title,xlabel):
        return [f'page.longname$="{title}";',f'label -xb "{xlabel}";',f'label -yl "{ylabel}";','layer -a;']
    for i,c in enumerate(curves,1):
        lines.append(plot(c,f'P{i:03d}'));lines.append('set %C -z 3;');lines.extend(format_graph(c.label,'Temperature (K)' if c.category=='MT' else 'Magnetic Field (Oe)'))
    groups={}
    for c in curves:groups.setdefault((c.category,c.mode),[]).append(c)
    for i,((category,mode),selected) in enumerate(groups.items(),1):
        name=f'G{i:03d}'
        for j,c in enumerate(selected):
            rgb=tuple(round(v*255) for v in colorsys.hsv_to_rgb(.66*(1-j/max(1,len(selected)-1)),.8,.72))
            lines.append(plot(c,name,j==0,True,'color('+','.join(map(str,rgb))+')'))
        lines.extend(format_graph(f'{category} {mode} overview','Temperature (K)' if category=='MT' else 'Magnetic Field (Oe)'))
        lines.append('legend -r;')
        entries=[rf'\l({j}) {c.id} '+(c.direction if category=='MT' else f'{sum(r.temperature for r in c.records)/len(c.records):.2f} K') for j,c in enumerate(selected,1)]
        lines.append('legend.text$="'+'%(CRLF)'.join(entries)+'";')
        lines.extend(['legend.fsize=11;','legend.background=0;'])
        if len(selected)>6:
            lines.extend(['layer.width=57;','layer.left=15;','legend.attach=2;',
                          'legend.x=layer.x.to+(layer.x.to-layer.x.from)*0.25;',
                          'legend.y=(layer.y.from+layer.y.to)/2;'])
    lines.extend(['pe_save fname:=mpmsTarget$;','type "MPMS import and plotting complete. Saved origin_result.opju in the data package folder.";',''])
    return '\n'.join(lines)

def export_dataset(dataset,curves,mass_mg,dc_source,output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise DataError('Choose an empty output directory so prior results remain available.')
    values={c.id:curve_values(c,mass_mg,dc_source) for c in curves}
    manifest={'schema_version':1,'source_file':dataset.filename,'source_sha256':dataset.sha256,'source_encoding':dataset.encoding,
              'record_count':len(dataset.records),'input_columns':len(dataset.column_names),'sample_mass_mg':mass_mg,'dc_moment_source':dc_source,
              'normalization':'moment_emu / sample_mass_mg * 1000' if mass_mg is not None else 'raw moment in emu',
              'curves':[{**curve_metadata(c,dc_source),'csv':f'csv/{c.id}.csv','worksheet':c.id} for c in curves]}
    output.mkdir(parents=True,exist_ok=True);(output/'csv').mkdir()
    for c in curves:write_csv(output/'csv'/f'{c.id}.csv',HEADERS,values[c.id])
    write_csv(output/'source_rows.csv',['curve_id','curve_row','source_record','source_physical_line'],[(c.id,i,r.number,r.physical_line) for c in curves for i,r in enumerate(c.records,1)])
    json_write(output/'manifest.json',manifest)
    write_workbooks(output,curves,values,manifest)
    with (output/'import_and_plot.ogs').open('w',encoding='utf-8-sig',newline='\r\n') as f:f.write(generate_ogs(curves,mass_mg))
    mass_text=f'样品质量：{mass_mg} mg' if mass_mg is not None else '保留原始磁矩 emu'
    summary=['# Origin 数据导入包','',f'数据：{dataset.filename}',f'有效记录：{len(dataset.records)}；测量段：{len(curves)}；{mass_text}。',
      '', '## 导入方式','',
      '1. 解压整个数据包，保留 csv 子目录。',
      '2. 手动导入：选择 wide.xlsx 的 MT/MH 数据表，或 per_curve.xlsx 中所需的 C001 等工作表。前三行依次为列名、单位、条件，数据从第4行开始。INDEX 是曲线目录。',
      '   Origin 2021b及以上：先激活工作簿，选 Data（数据）→ Connect to File（连接到文件）→ Excel，或点击工具栏的 Import Excel 按钮。选择所需工作表；Column Labels 中 Long Name=1、Units=2、Comments From/To=3，确认数值从第4行开始。旧版使用 Data → Import from File → Excel，配置相同的标签行。',
      '3. 分表版 MT 选择 A 列作 X、D 列作 Y；MH 选择 B 列作 X、D 列作 Y。原始 emu 模式下使用 C 列作 Y。',
      '4. 自动导入和画图：在 Origin 打开空白工程，按 Alt+3 打开命令窗口，执行 run.section("D:\\实际文件夹\\import_and_plot.ogs", Main);，引号内替换为脚本的实际完整路径，保留 Windows 反斜杠。文件夹选择框中选择解压后的数据包文件夹。',
      '5. 脚本完成后生成 origin_result.opju，图中保留各测量段及按模式分类的总览。',
      '', '## 数据含义','',
      'MT 横轴为温度 K，MH 横轴为磁场 Oe。归一化纵轴为质量磁化强度 emu/g；原始磁矩 emu 同时保留。',
      '曲线按采集顺序排列；同温度不同模式或独立扫场分开。单向曲线的 initial 标签描述其近零起始的扫场形态。',
      'mass 为本次明确提供的样品质量；仪器 Mass (grams) 字段表示运动部件质量。',
      '提示含义：one_way_or_partial_sweep 为单向或部分扫场；open_or_incomplete_cycle 为回线末端尚未完整返回；short_segment_review 为短段需复核。均保留实测点，结合实验记录判断。',
      '', '## 测量段','', '|ID|条件|记录范围|点数|提示|','|---|---|---|---:|---|']
    summary += [f"|{c['id']}|{c['label']}|{c['first_record']}–{c['last_record']}|{c['points']}|{'; '.join(c['warnings'])}|" for c in manifest['curves']]
    summary += ['', '兼容范围：转换使用 Python 3.10+ 与 openpyxl 3.1.x。脚本已在 OriginPro 2026（10.30018）用本项目两份样例实测；2018–2025 为接口兼容目标，尚无对应实机测试。每次云端生成的数据包以本次实际检查为准；运行脚本后才产生 OPJU。数值已在 Python 中计算，导入时选择数值即可。', '']
    (output/'使用说明.md').write_text('\n'.join(summary),encoding='utf-8')
    return manifest
