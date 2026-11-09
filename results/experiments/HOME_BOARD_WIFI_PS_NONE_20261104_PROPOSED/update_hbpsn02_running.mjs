import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const study=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(study,'../../..');
const request=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
const finalReview=request.phase==='FINAL_REVIEW_PENDING';
const manualReview=request.phase==='MANUAL_REVIEW_APPROVED';
if(request.run_id!=='HBPSN-02'||!(request.patch.status==='RUNNING'||(finalReview&&request.patch.status==='FAILED_SETTINGS')||(manualReview&&request.patch.status==='COMPLETE')))throw Error('Unsupported HBPSN-02 status/phase');
if(manualReview){
 const bytes=await fs.readFile(request.review_evidence_path);
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==request.review_evidence_sha256)throw Error('Manual review evidence hash mismatch');
 const review=JSON.parse(bytes.toString('utf8'));
 if(review.run_id!=='HBPSN-02'||review.decision!=='COMPLETE'||review.validity_status!=='APPROVED_UNDER_ORIGINAL_FROZEN_PLAN'||review.operator_confirmation_reviewed!==true)throw Error('Positive status requires explicit completed manual review');
}
const csvPath=path.join(study,'run_register.csv');
const xlsxPath=path.join(root,'outputs/HOME_BOARD_WIFI_PS_NONE_20261104/run_register.xlsx');
const csvBefore=await fs.readFile(csvPath);
const staged=await fs.readFile(request.csv_staged_path);
const rows=b=>b.toString('utf8').split('\r\n');
const oldRows=rows(csvBefore),newRows=rows(staged);
if(oldRows.length!==newRows.length||oldRows.some((x,i)=>i!==2&&x!==newRows[i]))throw Error('CSV changed another row');
const book=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsxPath));
const sheet=book.worksheets.getItem('Run register');
const snapshot=()=>JSON.stringify({values:sheet.getRange('A1:AI19').values.filter((x,i)=>i!==2).map(row=>row.map(v=>v==null?'':v)),formulas:sheet.getRange('A1:AI19').formulas.filter((x,i)=>i!==2)});
const others=snapshot();
if(sheet.getRange('C3:E3').values[0].join('/')!=='HBPSN-02/TCP_TLS/LAG100_OUT')throw Error('Workbook row identity mismatch');
const headers=sheet.getRange('A1:AI1').values[0];
for(const [field,value] of Object.entries(request.patch)){
 const index=headers.indexOf(field);if(index<0)throw Error('Unknown register field '+field);
 sheet.getCell(2,index).values=[[value]];
}
sheet.getRange('G3').dataValidation={rule:{type:'list',values:['NOT_RUN','RUNNING','FAILED_STARTUP','FAILED_SETTINGS','INTERRUPTED','COMPLETE_SHORTFALL','COMPLETE']}};
book.recalculate();
if(snapshot()!==others)throw Error('Another row changed in workbook');
const preview=await book.render({sheetName:'Run register',range:'A1:L5',scale:1,format:'png'});
await fs.writeFile(path.join(request.output_dir,manualReview?'register_manual_review.png':finalReview?'register_final_review.png':'register_running.png'),new Uint8Array(await preview.arrayBuffer()));
const temp=xlsxPath+'.hbpsn02.tmp.xlsx';await(await SpreadsheetFile.exportXlsx(book)).save(temp);await fs.rename(temp,xlsxPath);
if(!(await fs.readFile(csvPath)).equals(csvBefore))throw Error('Concurrent register modification');
await fs.writeFile(csvPath+'.hbpsn02.tmp',staged);await fs.rename(csvPath+'.hbpsn02.tmp',csvPath);
await fs.writeFile(path.join(request.output_dir,manualReview?'register_manual_review_update.json':finalReview?'register_final_review_update.json':'register_running_update.json'),JSON.stringify({updated_utc:new Date().toISOString(),run_id:'HBPSN-02',status:request.patch.status,processing_status:manualReview||finalReview?'FINALIZED':'RUNNING',evidence_review:manualReview?'APPROVED_WITH_FLAGS':finalReview?'PENDING':'NOT_STARTED',other_17_rows_unchanged:true,hbpsn01_unchanged:true,validity_approved:manualReview,review_evidence_path:manualReview?request.review_evidence_path:null},null,2));
console.log((await book.inspect({kind:'table',range:'Run register!C2:G4',include:'values',tableMaxRows:3,tableMaxCols:5,maxChars:800})).ndjson);
