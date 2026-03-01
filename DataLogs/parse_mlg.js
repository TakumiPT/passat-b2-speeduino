const fs = require('fs');

const csv = fs.readFileSync('2026-02-28_15.49.55.csv', 'utf-8');
const lines = csv.split('\n').filter(l => l.trim());

// Parse header - fields are separated by ; and quoted
const headers = lines[0].split(';').map(h => h.replace(/"/g, '').trim());
const units = lines[1].split(';').map(h => h.replace(/"/g, '').trim());

// Key column indices
const cols = {};
const wanted = ['Time', 'RPM', 'MAP', 'TPS', 'PW', 'CLT', 'IAT', 'Battery V', 'Advance _Current', 'Engine', 'Error #', 'Error ID', 'Sync Loss #', 'AFR', 'VE _Current', 'Accel Enrich', 'Duty Cycle', 'Dwell', 'Sync status', 'Loops/s', 'Gbattery', 'Gwarm', 'Gammae', 'AFR Target', 'TPS DOT', 'Idle Control', 'IAC value'];
wanted.forEach(name => {
  const idx = headers.indexOf(name);
  if (idx >= 0) cols[name] = idx;
});

console.log('=== AVAILABLE CHANNELS ===');
console.log(headers.map((h, i) => `${i}: ${h} (${units[i]})`).join('\n'));
console.log('\n=== KEY CHANNEL INDICES ===');
Object.entries(cols).forEach(([k, v]) => console.log(`${k}: col ${v}`));

// Parse data rows
const data = [];
for (let i = 2; i < lines.length; i++) {
  const fields = lines[i].split(';').map(f => f.replace(/"/g, '').trim());
  const row = {};
  Object.entries(cols).forEach(([name, idx]) => {
    row[name] = parseFloat(fields[idx]) || 0;
  });
  row._raw = fields;
  data.push(row);
}

console.log(`\n=== LOG SUMMARY (${data.length} rows) ===`);
console.log(`Duration: ${data[0].Time}s to ${data[data.length-1].Time}s (${(data[data.length-1].Time - data[0].Time).toFixed(1)}s total)`);

// Overall stats
const stats = (arr) => ({
  min: Math.min(...arr),
  max: Math.max(...arr),
  avg: (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1)
});

const rpmArr = data.map(d => d.RPM);
const mapArr = data.map(d => d.MAP);
const tpsArr = data.map(d => d.TPS);
const pwArr = data.map(d => d.PW);
const cltArr = data.map(d => d.CLT);
const batArr = data.map(d => d['Battery V']);
const advArr = data.map(d => d['Advance _Current']);
const afrArr = data.map(d => d.AFR);
const errArr = data.map(d => d['Error #']);
const syncArr = data.map(d => d['Sync Loss #']);

console.log(`\nRPM:     min=${stats(rpmArr).min} max=${stats(rpmArr).max} avg=${stats(rpmArr).avg}`);
console.log(`MAP:     min=${stats(mapArr).min} max=${stats(mapArr).max} avg=${stats(mapArr).avg} kPa`);
console.log(`TPS:     min=${stats(tpsArr).min} max=${stats(tpsArr).max} avg=${stats(tpsArr).avg} %`);
console.log(`PW:      min=${stats(pwArr).min} max=${stats(pwArr).max} avg=${stats(pwArr).avg} ms`);
console.log(`CLT:     min=${stats(cltArr).min} max=${stats(cltArr).max} avg=${stats(cltArr).avg}`);
console.log(`Battery: min=${stats(batArr).min} max=${stats(batArr).max} avg=${stats(batArr).avg} V`);
console.log(`Advance: min=${stats(advArr).min} max=${stats(advArr).max} avg=${stats(advArr).avg} deg`);
console.log(`AFR:     min=${stats(afrArr).min} max=${stats(afrArr).max} avg=${stats(afrArr).avg}`);
console.log(`Errors:  min=${stats(errArr).min} max=${stats(errArr).max}`);
console.log(`SyncLoss: min=${stats(syncArr).min} max=${stats(syncArr).max}`);

// Print first 20 data rows with key fields
console.log('\n=== FIRST 30 ROWS (Time | RPM | MAP | TPS | PW | CLT | BatV | Adv | AFR | Err | Sync | Engine) ===');
data.slice(0, 30).forEach((d, i) => {
  console.log(`${d.Time.toFixed(2)}s | RPM:${d.RPM} | MAP:${d.MAP} | TPS:${d.TPS} | PW:${d.PW}ms | CLT:${d.CLT} | Bat:${d['Battery V']}V | Adv:${d['Advance _Current']} | AFR:${d.AFR} | Err:${d['Error #']} | Sync:${d['Sync Loss #']} | Eng:${d['Engine']}`);
});

// Find cranking events (RPM > 0)
const crankRows = data.filter(d => d.RPM > 0);
console.log(`\n=== CRANKING EVENTS (${crankRows.length} rows with RPM > 0) ===`);
if (crankRows.length > 0) {
  console.log('First 30 cranking rows:');
  crankRows.slice(0, 30).forEach(d => {
    console.log(`${d.Time.toFixed(2)}s | RPM:${d.RPM} | MAP:${d.MAP} | TPS:${d.TPS} | PW:${d.PW}ms | CLT:${d.CLT} | Bat:${d['Battery V']}V | Adv:${d['Advance _Current']} | AFR:${d.AFR} | VE:${d['VE _Current']} | Gwarm:${d.Gwarm} | AE:${d['Accel Enrich']}`);
  });
}

// Check for RPM transitions
console.log('\n=== RPM TIMELINE (sampled every 20 rows) ===');
for (let i = 0; i < data.length; i += 20) {
  const d = data[i];
  console.log(`${d.Time.toFixed(1)}s | RPM:${d.RPM} | MAP:${d.MAP} | PW:${d.PW}ms | Bat:${d['Battery V']}V | Err:${d['Error #']} | Sync:${d['Sync Loss #']}`);
}
