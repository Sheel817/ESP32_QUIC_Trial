import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const study=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(study,'../../..');
const request=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const csvPath=path.join(study,'run_register.csv');
const xlsxPath=path.join(root,'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx');
const csvBook=await Workbook.fromCSV(await fs.readFile(csvPath,'utf8'),{sheetName:'CSV'});
const matrix=csvBook.worksheets.getItemAt(0).getRange('A1:AI19').values;
const headers=matrix[0];
if(matrix[1][2]!=='HBPSN-01'||matrix[1][3]!=='QUIC'||matrix[1][4]!=='CONTROL')throw Error('Run identity mismatch');
const otherCsv=JSON.stringify(matrix.slice(2));
const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsxPath));
const sheet=workbook.worksheets.getItem('Run register');
const blankNormalized=values=>JSON.stringify(values.map(row=>row.map(v=>v==null?'':v)));
const otherValues=blankNormalized(sheet.getRange('A3:AI19').values);
const otherFormulas=JSON.stringify(sheet.getRange('A3:AI19').formulas);
const out=request.output_dir;await fs.mkdir(out,{recursive:true});
if(!request.final){const preview=await workbook.render({sheetName:'Run register',range:'A1:L5',scale:1,format:'png'});await fs.writeFile(path.join(out,'register_before.png'),new Uint8Array(await preview.arrayBuffer()));}
for(const [field,value] of Object.entries(request.patch)){
 const index=headers.indexOf(field);if(index<0)throw Error('Unknown field '+field);
 matrix[1][index]=value==null?'':String(value);sheet.getCell(1,index).values=[[value==null?null:value]];
}
sheet.getRange('G2').dataValidation={rule:{type:'list',values:['NOT_RUN','RUNNING','FAILED_STARTUP','FAILED_SETTINGS','INTERRUPTED','COMPLETE_SHORTFALL','COMPLETE']}};
workbook.recalculate();
if(JSON.stringify(matrix.slice(2))!==otherCsv||blankNormalized(sheet.getRange('A3:AI19').values)!==otherValues||JSON.stringify(sheet.getRange('A3:AI19').formulas)!==otherFormulas)throw Error('Another entry changed');
const preview=await workbook.render({sheetName:'Run register',range:'A1:L5',scale:1,format:'png'});
await fs.writeFile(path.join(out,request.final?'register_final.png':'register_running.png'),new Uint8Array(await preview.arrayBuffer()));
console.log((await workbook.inspect({kind:'table',range:'Run register!A1:L3',include:'values,formulas',tableMaxRows:3,tableMaxCols:12,maxChars:1000})).ndjson);
if(request.dry_run){console.log('Register updater prepared; no register file changed.');process.exit(0);}
const temp=xlsxPath+'.tmp.xlsx';await(await SpreadsheetFile.exportXlsx(workbook)).save(temp);await fs.rename(temp,xlsxPath);
const csv=matrix.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\r\n')+'\r\n';
await fs.writeFile(csvPath+'.tmp',csv,'utf8');await fs.rename(csvPath+'.tmp',csvPath);
await fs.writeFile(path.join(out,request.final?'register_final_update.json':'register_running_update.json'),JSON.stringify({updated_utc:new Date().toISOString(),run_id:'HBPSN-01',patch:request.patch,other_17_entries_unchanged:true},null,2));
