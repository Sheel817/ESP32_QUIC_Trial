import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../..');
const outputDir=path.join(root,'outputs/HOME_BOARD_WIFI_PS_NONE_20261104');
await fs.mkdir(outputDir,{recursive:true});
const tcp=JSON.parse(await fs.readFile(path.join(root,'profiles/tcp_tls_wifi_ps_none_20261104/validation.json'),'utf8'));
if(tcp.result!=='PASS')throw Error('Build not validated');
const schedule=[['QUIC','CONTROL'],['TCP_TLS','LAG100_OUT'],['QUIC','DROP1_OUT'],['TCP_TLS','CONTROL'],['QUIC','LAG100_OUT'],['TCP_TLS','DROP1_OUT'],['TCP_TLS','DROP1_OUT'],['QUIC','LAG100_OUT'],['TCP_TLS','CONTROL'],['QUIC','DROP1_OUT'],['TCP_TLS','LAG100_OUT'],['QUIC','CONTROL'],['QUIC','LAG100_OUT'],['TCP_TLS','DROP1_OUT'],['QUIC','CONTROL'],['TCP_TLS','LAG100_OUT'],['QUIC','DROP1_OUT'],['TCP_TLS','CONTROL']];
const headers=['order','block','run_id','transport','condition','boot_replicate','status','recording_seconds','warmup_exclude_below_ms','target_rtts','configured_lag_ms','configured_drop_percent','effect_direction','board','wifi_ps_mode','artifact_id','preflight_status','startup_status','settings_evidence_type','boot_session_id','reset_release_utc','recording_end_utc','actual_duration_seconds','actual_assigned_ip','eligible_count','selected_count','shortfall','connection_error_count','sequence_gap_count','mean_app_rtt_ms','minimum_app_rtt_ms','maximum_app_rtt_ms','metadata_path','raw_serial_path','deviation_reason'];
const rows=schedule.map(([transport,condition],i)=>{
 const id=`HBPSN-${String(i+1).padStart(2,'0')}`;
 return [i+1,Math.floor(i/6)+1,id,transport,condition,Math.floor(i/6)+1,'NOT_RUN',2220,60000,415,condition==='LAG100_OUT'?100:0,condition==='DROP1_OUT'?1:0,condition==='CONTROL'?'none':'outbound_only','HOME_BOARD','WIFI_PS_NONE',`${transport}_PSN`,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,`runs/${id}/metadata.json`,null,null];
});
const frequencies=new Map();
rows.forEach(r=>{const key=`${r[3]}/${r[4]}`;frequencies.set(key,(frequencies.get(key)||0)+1);});
if(rows.length!==18||frequencies.size!==6||[...frequencies.values()].some(n=>n!==3))throw Error('Invalid design');
function letter(n){let r='';while(n){n--;r=String.fromCharCode(65+n%26)+r;n=Math.floor(n/26);}return r;}
const workbook=Workbook.create();
const sheet=workbook.worksheets.add('Run register');
sheet.showGridLines=false;
const last=letter(headers.length);
sheet.getRange(`A1:${last}19`).values=[headers,...rows];
sheet.getRange(`A1:${last}19`).format.font={name:'Arial',size:10,color:'#17212B'};
sheet.getRange(`A1:${last}19`).format.rowHeight=23;
sheet.getRange(`A1:${last}19`).format.columnWidth=19;
sheet.getRange(`A1:${last}1`).format={fill:'#28445B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',rowHeight:44};
sheet.getRange(`A2:${last}19`).format.verticalAlignment='center';
sheet.getRange('A1:B19').format.columnWidth=9;
sheet.getRange('C1:D19').format.columnWidth=14;
sheet.getRange('E1:E19').format.columnWidth=19;
sheet.getRange('F1:F19').format.columnWidth=13;
sheet.getRange('G1:G19').format.columnWidth=21;
sheet.getRange('AG1:AG19').format.columnWidth=36;
sheet.getRange('AI1:AI19').format.columnWidth=40;
sheet.getRange('Q2:AI19').format.fill='#FFF6DB';
for(const c of [1,2,6,8,9,10,11,12,23,25,26,27,28,29])sheet.getRange(`${letter(c)}2:${letter(c)}19`).setNumberFormat('0');
sheet.getRange('AD2:AF19').setNumberFormat('0.0000');
sheet.getRange('G2:G19').dataValidation={rule:{type:'list',values:['NOT_RUN','FAILED_STARTUP','FAILED_SETTINGS','INTERRUPTED','COMPLETE_SHORTFALL','COMPLETE']}};
sheet.getRange('AA2').formulas=[['=IF(ISNUMBER(Z2),MAX(0,J2-Z2),"")']];
sheet.getRange('AA2:AA19').fillDown();
sheet.freezePanes.freezeRows(1);
sheet.freezePanes.freezeColumns(3);
sheet.tables.add(`A1:${last}19`,true,'HomeBoardRunRegister');
workbook.recalculate();
sheet.getRange('Z2').values=[[0]];
workbook.recalculate();
if(sheet.getRange('AA2').values[0][0]!==415)throw Error('Zero-selected shortfall incorrect: '+JSON.stringify(sheet.getRange('AA2').values));
sheet.getRange('Z2').values=[[null]];
workbook.recalculate();
if(sheet.getRange('AA2').values[0][0]!=='')throw Error('Unrun shortfall must be blank');
console.log((await workbook.inspect({kind:'table',range:'Run register!A1:L19',include:'values,formulas',tableMaxRows:4,tableMaxCols:12,maxChars:1400})).ndjson);
console.log((await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:400})).ndjson);
for(const [name,range] of [['schedule','A1:L19'],['conditions','M1:W19'],['results','X1:AI19']]){
 const preview=await workbook.render({sheetName:'Run register',range,scale:1,format:'png'});
 await fs.writeFile(path.join(here,`register_${name}_preview.png`),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(workbook)).save(path.join(outputDir,'run_register.xlsx'));
const csv=matrix=>matrix.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\r\n')+'\r\n';
await fs.writeFile(path.join(here,'run_register.csv'),csv([headers,...rows]),'utf8');
const artifacts=[];
for(const [transport,build] of [['QUIC','profiles/wifi_ps_none_20261103/build'],['TCP_TLS','profiles/tcp_tls_wifi_ps_none_20261104/build']]){
 for(const name of ['quic_demo.bin','quic_demo.elf','bootloader/bootloader.bin','partition_table/partition-table.bin']){
  const file=path.join(root,build,name);const bytes=await fs.readFile(file);
  artifacts.push({artifact_id:`${transport}_PSN`,transport,path:file,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
 }
}
const files=[];
for(const file of [path.join(here,'EXPERIMENT_PLAN_PROPOSED_V1.md'),path.join(here,'run_register.csv'),path.join(outputDir,'run_register.xlsx'),path.join(root,'profiles/tcp_tls_wifi_ps_none_20261104/source_before.json'),path.join(root,'profiles/tcp_tls_wifi_ps_none_20261104/validation.json')])files.push({path:file,sha256:crypto.createHash('sha256').update(await fs.readFile(file)).digest('hex')});
await fs.writeFile(path.join(here,'freeze_manifest.json'),JSON.stringify({protocol_id:'HOME_BOARD_WIFI_PS_NONE_20261104_PROPOSED_V1',status:'PROPOSED_NOT_STARTED',prepared_utc:new Date().toISOString(),runs:18,recording_seconds_each:2220,first_eligible_count_target:415,eligibility:'Initial boot; ESP log uptime >=60000 and <2220000; within 2220-second host-monotonic recording',artifacts,files,schedule:schedule.map(([transport,condition],i)=>({order:i+1,run_id:rows[i][2],block:rows[i][1],transport,condition}))},null,2),'utf8');
console.log(JSON.stringify({register_rows:rows.length,combinations:[...frequencies],xlsx:path.join(outputDir,'run_register.xlsx'),csv:path.join(here,'run_register.csv')},null,2));
