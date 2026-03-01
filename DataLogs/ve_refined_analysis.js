// Refined VE Analysis - Separates hot (VE correction) from cold (WUE correction)
const fs = require('fs');

const rpmBins = [500, 700, 900, 1200, 1500, 1800, 2200, 2700, 3000, 3400, 3900, 4300, 4800, 5200, 5700, 6200];
const mapBins = [16, 26, 30, 36, 40, 46, 50, 56, 60, 66, 70, 76, 86, 90, 96, 100];

const veTable = [
  [30,30,32,35,39,43,47,50,53,56,59,61,63,65,63,61],
  [31,31,33,36,40,44,48,51,54,57,60,62,64,66,64,62],
  [32,32,34,37,41,45,49,52,55,58,61,63,65,67,65,63],
  [34,34,36,39,43,47,51,54,57,60,63,65,67,69,67,65],
  [36,36,38,41,45,49,53,56,59,62,65,67,69,71,69,67],
  [38,38,40,43,47,51,55,58,61,64,67,69,71,73,71,69],
  [40,40,42,45,49,53,57,60,63,66,69,71,73,75,73,71],
  [42,42,44,47,51,55,59,62,65,68,71,73,75,77,75,73],
  [45,45,47,50,54,58,62,65,68,71,74,76,78,80,78,76],
  [48,48,50,53,57,61,65,68,71,74,77,79,81,83,81,79],
  [50,50,52,55,59,63,67,70,73,76,79,81,83,85,83,81],
  [52,52,54,57,61,65,69,72,75,78,81,83,85,87,85,83],
  [54,54,56,59,63,67,71,74,77,80,83,85,87,89,87,85],
  [55,55,57,60,64,68,72,75,78,81,84,86,88,90,88,86],
  [56,56,58,61,65,69,73,76,79,82,85,87,89,91,89,87],
  [57,57,59,62,66,70,74,77,80,83,86,88,90,92,90,88],
];

// WUE values and bins
const wueBins = [-40, -26, 10, 19, 28, 37, 50, 65, 80, 90];
const wueValues = [180, 175, 168, 154, 134, 121, 112, 106, 102, 100];

function getTargetAFR(map) {
  if (map >= 90) return 12.8;
  if (map >= 80) return 13.2;
  if (map >= 70) return 13.5;
  if (map >= 60) return 14.0;
  return 14.7;
}

function findBinIndex(value, bins) {
  if (value <= bins[0]) return 0;
  if (value >= bins[bins.length - 1]) return bins.length - 1;
  for (let i = 0; i < bins.length - 1; i++) {
    if (value >= bins[i] && value < bins[i + 1]) {
      return (value - bins[i]) < (bins[i + 1] - value) ? i : i + 1;
    }
  }
  return bins.length - 1;
}

function interpolateWUE(clt) {
  if (clt <= wueBins[0]) return wueValues[0];
  if (clt >= wueBins[wueBins.length - 1]) return wueValues[wueValues.length - 1];
  for (let i = 0; i < wueBins.length - 1; i++) {
    if (clt >= wueBins[i] && clt < wueBins[i + 1]) {
      const frac = (clt - wueBins[i]) / (wueBins[i + 1] - wueBins[i]);
      return wueValues[i] + frac * (wueValues[i + 1] - wueValues[i]);
    }
  }
  return 100;
}

function parseCSV(filename) {
  const data = fs.readFileSync(filename, 'utf8');
  const lines = data.split('\n').filter(l => l.trim());
  const headers = lines[0].split(';').map(h => h.replace(/"/g, '').trim());
  
  const idx = {
    time: headers.indexOf('Time'),
    rpm: headers.indexOf('RPM'),
    map: headers.indexOf('MAP'),
    afr: headers.indexOf('AFR'),
    clt: headers.indexOf('CLT'),
    tps: headers.indexOf('TPS'),
    pw: headers.indexOf('PW'),
    afrTarget: headers.indexOf('AFR Target'),
  };
  
  const points = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(';');
    const p = {
      time: parseFloat(cols[idx.time]),
      rpm: parseFloat(cols[idx.rpm]),
      map: parseFloat(cols[idx.map]),
      afr: parseFloat(cols[idx.afr]),
      clt: parseFloat(cols[idx.clt]),
      tps: parseFloat(cols[idx.tps]),
      pw: parseFloat(cols[idx.pw]),
    };
    
    if (isNaN(p.rpm) || p.rpm < 400 || isNaN(p.afr) || p.afr < 8 || p.afr > 22) continue;
    
    // Skip rapid transients
    if (i < lines.length - 1) {
      const nextTps = parseFloat(lines[i + 1].split(';')[idx.tps]);
      if (!isNaN(nextTps) && Math.abs(nextTps - p.tps) > 3) continue;
    }
    
    points.push(p);
  }
  return points;
}

// Parse both logs
const allPoints = [
  ...parseCSV('2026-02-28_17.53.41.csv'),
  ...parseCSV('2026-02-28_18.10.43.csv'),
];

console.log(`Total valid data points: ${allPoints.length}`);

// === PART 1: VE CORRECTIONS (HOT DATA ONLY, CLT >= 75°C) ===
console.log('\n' + '='.repeat(70));
console.log('PART 1: VE TABLE CORRECTIONS (using HOT data only, CLT >= 75°C)');
console.log('='.repeat(70));

const hotCells = {};
const coldCells = {};

for (const p of allPoints) {
  const ri = findBinIndex(p.rpm, rpmBins);
  const mi = findBinIndex(p.map, mapBins);
  const key = `${ri}_${mi}`;
  
  if (p.clt >= 75) {
    if (!hotCells[key]) hotCells[key] = [];
    hotCells[key].push(p);
  } else {
    if (!coldCells[key]) coldCells[key] = [];
    coldCells[key].push(p);
  }
}

// Process hot cells for VE corrections
const veCorrections = [];

for (const [key, points] of Object.entries(hotCells)) {
  if (points.length < 5) continue;
  
  const [ri, mi] = key.split('_').map(Number);
  const rpm = rpmBins[ri];
  const map = mapBins[mi];
  const currentVE = veTable[mi][ri];
  const target = getTargetAFR(map);
  
  // Trimmed mean AFR
  const afrs = points.map(p => p.afr).sort((a, b) => a - b);
  const trim = Math.floor(afrs.length * 0.1);
  const trimmed = trim > 0 ? afrs.slice(trim, -trim) : afrs;
  const avgAFR = trimmed.reduce((s, v) => s + v, 0) / trimmed.length;
  const avgCLT = points.reduce((s, p) => s + p.clt, 0) / points.length;
  
  // At CLT 75-100°C, WUE is 100-102%, negligible
  const cf = avgAFR / target;
  let newVE = Math.round(currentVE * cf);
  newVE = Math.max(20, Math.min(120, newVE));
  const change = newVE - currentVE;
  
  if (Math.abs(change) >= 1) {
    const confidence = points.length >= 100 ? 'HIGH' : points.length >= 20 ? 'MEDIUM' : 'LOW';
    veCorrections.push({
      rpm, map, ri, mi, currentVE, newVE, change, avgAFR, target, cf, 
      samples: points.length, avgCLT, confidence
    });
  }
}

veCorrections.sort((a, b) => a.mi - b.mi || a.ri - b.ri);

console.log('\nCell-by-cell corrections (hot data only):');
console.log('─'.repeat(100));
for (const c of veCorrections) {
  const dir = c.change > 0 ? 'LEAN' : 'RICH';
  const sign = c.change > 0 ? '+' : '';
  console.log(
    `[${c.confidence.padEnd(6)}] RPM ${String(c.rpm).padStart(4)} | MAP ${String(c.map).padStart(3)}kPa | ` +
    `VE ${String(c.currentVE).padStart(2)} → ${String(c.newVE).padStart(2)} (${sign}${c.change}) | ` +
    `AFR ${c.avgAFR.toFixed(1)} → ${c.target.toFixed(1)} | ${dir} | ` +
    `n=${String(c.samples).padStart(5)} | CLT ${c.avgCLT.toFixed(0)}°C`
  );
}

// === PART 2: WUE CORRECTIONS ===
console.log('\n' + '='.repeat(70));
console.log('PART 2: WUE ENRICHMENT CORRECTIONS (using COLD data, CLT < 75°C)');
console.log('='.repeat(70));

// Group cold data by temperature ranges matching WUE bins
const tempBuckets = [
  { min: -40, max: 15, label: '-40 to 10°C', wueBinIdx: [0, 1, 2] },
  { min: 15, max: 24, label: '15-24°C (WUE 154%)', wueBinIdx: [3] },
  { min: 24, max: 33, label: '24-33°C (WUE 134%)', wueBinIdx: [4] },
  { min: 33, max: 44, label: '33-44°C (WUE 121%)', wueBinIdx: [5] },
  { min: 44, max: 58, label: '44-58°C (WUE 112%)', wueBinIdx: [6] },
  { min: 58, max: 73, label: '58-73°C (WUE 106%)', wueBinIdx: [7] },
];

for (const bucket of tempBuckets) {
  const pts = allPoints.filter(p => p.clt >= bucket.min && p.clt < bucket.max && p.rpm < 2000);
  if (pts.length < 10) continue;
  
  const avgAFR = pts.reduce((s, p) => s + p.afr, 0) / pts.length;
  const avgCLT = pts.reduce((s, p) => s + p.clt, 0) / pts.length;
  const avgRPM = pts.reduce((s, p) => s + p.rpm, 0) / pts.length;
  const currentWUE = interpolateWUE(avgCLT);
  const targetAFR = 14.7;
  
  // To correct: newWUE = currentWUE * (measured_AFR / target_AFR)  
  // If lean (AFR > target), need MORE fuel, increase WUE
  const newWUE = Math.round(currentWUE * (avgAFR / targetAFR));
  const change = newWUE - Math.round(currentWUE);
  
  console.log(
    `${bucket.label.padEnd(25)} | avg CLT ${avgCLT.toFixed(1).padStart(5)}°C | ` +
    `AFR ${avgAFR.toFixed(1).padStart(5)} → ${targetAFR.toFixed(1)} | ` +
    `WUE ${Math.round(currentWUE)} → ${newWUE} (${change >= 0 ? '+' : ''}${change}) | ` +
    `n=${pts.length}`
  );
}

// Detailed WUE recommendation
console.log('\nRecommended WUE Table:');
console.log('─'.repeat(60));
console.log('Temp(°C) | Current | Needed  | Change');

// Calculate needed WUE at each bin temperature
for (let i = 0; i < wueBins.length; i++) {
  const temp = wueBins[i];
  const range = 8; // +/- range for averaging
  const pts = allPoints.filter(p => 
    p.clt >= temp - range && p.clt < temp + range && 
    p.rpm >= 400 && p.rpm < 2000
  );
  
  if (pts.length >= 5) {
    const avgAFR = pts.reduce((s, p) => s + p.afr, 0) / pts.length;
    const cf = avgAFR / 14.7;
    const newWUE = Math.round(wueValues[i] * cf);
    const change = newWUE - wueValues[i];
    console.log(
      `${String(temp).padStart(6)}°C | ${String(wueValues[i]).padStart(6)}% | ${String(newWUE).padStart(6)}% | ${change >= 0 ? '+' : ''}${change}% | n=${pts.length}`
    );
  } else {
    console.log(
      `${String(temp).padStart(6)}°C | ${String(wueValues[i]).padStart(6)}% |    N/A  | insufficient data (n=${pts.length})`
    );
  }
}

// === PART 3: BUILD FINAL VE TABLE ===
console.log('\n' + '='.repeat(70));
console.log('PART 3: RECOMMENDED VE TABLE (only hot-data corrections applied)');
console.log('='.repeat(70));

const newVeTable = veTable.map(row => [...row]);

// Apply only hot-data corrections with confidence filter
for (const c of veCorrections) {
  // Skip MAP 16 kPa corrections (unreliable - decel overrun, noisy WB readings)
  if (c.map === 16) {
    console.log(`  SKIPPED: RPM ${c.rpm}/MAP ${c.map} - decel overrun zone, WB readings unreliable`);
    continue;
  }
  // Skip very low sample corrections
  if (c.samples < 5) {
    console.log(`  SKIPPED: RPM ${c.rpm}/MAP ${c.map} - too few samples (${c.samples})`);
    continue;
  }
  newVeTable[c.mi][c.ri] = c.newVE;
}

// Smooth table to avoid discontinuities
// Check for cells that differ by more than 8 from both neighbors
console.log('\nSmoothing check (cells with >8 difference from neighbors):');
for (let m = 0; m < 16; m++) {
  for (let r = 0; r < 16; r++) {
    const val = newVeTable[m][r];
    const neighbors = [];
    if (r > 0) neighbors.push(newVeTable[m][r-1]);
    if (r < 15) neighbors.push(newVeTable[m][r+1]);
    if (m > 0) neighbors.push(newVeTable[m-1][r]);
    if (m < 15) neighbors.push(newVeTable[m+1][r]);
    
    const avgNeighbor = neighbors.reduce((s,v) => s+v, 0) / neighbors.length;
    if (Math.abs(val - avgNeighbor) > 8) {
      console.log(
        `  WARNING: RPM ${rpmBins[r]}/MAP ${mapBins[m]} = ${val}, neighbors avg = ${avgNeighbor.toFixed(0)} (diff ${Math.abs(val - avgNeighbor).toFixed(0)})`
      );
    }
  }
}

// Print final table
console.log('\nFinal VE Table (changed cells marked with *):');
console.log('       ' + rpmBins.map(r => String(r).padStart(5)).join(' '));
for (let m = 0; m < 16; m++) {
  const row = newVeTable[m].map((v, r) => {
    if (v !== veTable[m][r]) return `${String(v).padStart(4)}*`;
    return String(v).padStart(5);
  }).join(' ');
  console.log(`${String(mapBins[m]).padStart(3)}kPa ${row}`);
}

// Print MSQ format
console.log('\nMSQ format (for copy into TunerStudio):');
for (let m = 0; m < 16; m++) {
  console.log('         ' + newVeTable[m].map(v => `${v}.0`).join(' ') + ' ');
}

// === PART 4: RPM LIMITER ANALYSIS ===
console.log('\n' + '='.repeat(70));
console.log('PART 4: RPM LIMITER ANALYSIS');
console.log('='.repeat(70));

// Count samples near and above rev limit
const above6000 = allPoints.filter(p => p.rpm >= 6000);
const above6500 = allPoints.filter(p => p.rpm >= 6500);
const above7000 = allPoints.filter(p => p.rpm >= 7000);
const maxRPM = Math.max(...allPoints.map(p => p.rpm));

console.log(`\nRPM statistics:`);
console.log(`  Max RPM reached: ${maxRPM}`);
console.log(`  Samples above SoftRevLim (6000): ${above6000.length}`);
console.log(`  Samples above 6500 RPM: ${above6500.length}`);
console.log(`  Samples above HardRevLim (7000): ${above7000.length}`);

if (above6000.length > 0) {
  console.log('\nSamples above 6000 RPM with AFR:');
  // Group by RPM bands
  for (const band of [{min:6000,max:6500},{min:6500,max:7000},{min:7000,max:8000}]) {
    const pts = allPoints.filter(p => p.rpm >= band.min && p.rpm < band.max);
    if (pts.length > 0) {
      const afrs = pts.map(p => p.afr);
      const maps = pts.map(p => p.map);
      console.log(
        `  ${band.min}-${band.max} RPM: n=${pts.length}, ` +
        `AFR min=${Math.min(...afrs).toFixed(1)} avg=${(afrs.reduce((s,v)=>s+v,0)/afrs.length).toFixed(1)} max=${Math.max(...afrs).toFixed(1)}, ` +
        `MAP range ${Math.min(...maps).toFixed(0)}-${Math.max(...maps).toFixed(0)} kPa`
      );
    }
  }
}
