import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const study=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(study,'../../..');
const request=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
if(request.run_id!=='HBPSN-03'||request.patch.status!=='FAILED_STARTUP')throw Error('Only HBPSN-03 initial startup failure supported');
const csvPath=path.join(study,'run_register.csv'),xlsxPath=path.join(root,'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx');
const original=await fs.readFile(csvPath),staged=await fs.readFile(request.csv_staged_path);
const oldRows=original.toString('utf8').split('\r\n'),newRows=staged.toString('utf8').split('\r\n');
if(oldRows.length!==newRows.length||oldRows.some((r,i)=>i!==3&&r!==newRows[i]))throw Error('Another CSV row changed');
const book=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsxPath));
const sheet=book.worksheets.getItem('Run register');
const snapshot=()=>JSON.stringify({values:sheet.getRange('A1:AI19').values.filter((r,i)=>i!==3).map(r=>r.map(v=>v==null?'':v)),formulas:sheet.getRange('A1:AI19').formulas.filter((r,i)=>i!==3)});
const others=snapshot();
if(sheet.getRange('C4:G4').values[0].filter((v,i)=>[0,1,2,4].includes(i)).join('/')!=='HBPSN-03/QUIC/DROP1_OUT/NOT_RUN')throw Error('Workbook identity/status differs');
if(process.argv[3]!=='--apply'){
 const before=await book.render({sheetName:'Run register',range:'A1:L5',scale:1,format:'png'});
 await fs.writeFile(path.join(request.output_dir,'register_before.png'),new Uint8Array(await before.arrayBuffer()));
 console.log((await book.inspect({kind:'table',range:'Run register!C2:G4',include:'values',tableMaxRows:3,tableMaxCols:5,maxChars:1000})).ndjson);
 process.exit(0);
}
const headers=sheet.getRange('A1:AI1').values[0];
for(const [field,value] of Object.entries(request.patch)){
 const index=headers.indexOf(field);if(index<0)throw Error('Unknown field '+field);
 sheet.getCell(3,index).values=[[value]];
}
book.recalculate();
if(snapshot()!==others)throw Error('Another workbook row changed');
const preview=await book.render({sheetName:'Run register',range:'A1:L5',scale:1,format:'png'});
await fs.writeFile(path.join(request.output_dir,'register_started_failure.png'),new Uint8Array(await preview.arrayBuffer()));
console.log((await book.inspect({kind:'table',range:'Run register!C2:G4',include:'values',tableMaxRows:3,tableMaxCols:5,maxChars:1000})).ndjson);
const temp=xlsxPath+'.hbpsn03.tmp.xlsx';await(await SpreadsheetFile.exportXlsx(book)).save(temp);
if(!(await fs.readFile(csvPath)).equals(original))throw Error('Concurrent register modification');
await fs.rename(temp,xlsxPath);await fs.writeFile(csvPath+'.hbpsn03.tmp',staged);await fs.rename(csvPath+'.hbpsn03.tmp',csvPath);
await fs.writeFile(path.join(request.output_dir,'register_started_failure_update.json'),JSON.stringify({updated_utc:new Date().toISOString(),run_id:'HBPSN-03',status:'FAILED_STARTUP',processing_status:'RECORDING_ORIGINAL_FIXED_WINDOW',validity_status:'NOT_APPROVED',other_17_rows_unchanged:true,hbpsn01_unchanged:true,hbpsn02_unchanged:true},null,2));
