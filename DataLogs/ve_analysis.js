// VE Table Analysis: Map datalog AFR readings to VE table cells
// Calculates exact corrections needed

const fs = require('fs');

// Current VE Table from MSQ (rows=MAP ascending, cols=RPM ascending)
const rpmBins = [500, 700, 900, 1200, 1500, 1800, 2200, 2700, 3000, 3400, 3900, 4300, 4800, 5200, 5700, 6200];
const mapBins = [16, 26, 30, 36, 40, 46, 50, 56, 60, 66, 70, 76, 86, 90, 96, 100];

const veTable = [
  [30, 30, 32, 35, 39, 43, 47, 50, 53, 56, 59, 61, 63, 65, 63, 61],  // MAP 16
  [31, 31, 33, 36, 40, 44, 48, 51, 54, 57, 60, 62, 64, 66, 64, 62],  // MAP 26
  [32, 32, 34, 37, 41, 45, 49, 52, 55, 58, 61, 63, 65, 67, 65, 63],  // MAP 30
  [34, 34, 36, 39, 43, 47, 51, 54, 57, 60, 63, 65, 67, 69, 67, 65],  // MAP 36
  [36, 36, 38, 41, 45, 49, 53, 56, 59, 62, 65, 67, 69, 71, 69, 67],  // MAP 40
  [38, 38, 40, 43, 47, 51, 55, 58, 61, 64, 67, 69, 71, 73, 71, 69],  // MAP 46
  [40, 40, 42, 45, 49, 53, 57, 60, 63, 66, 69, 71, 73, 75, 73, 71],  // MAP 50
  [42, 42, 44, 47, 51, 55, 59, 62, 65, 68, 71, 73, 75, 77, 75, 73],  // MAP 56
  [45, 45, 47, 50, 54, 58, 62, 65, 68, 71, 74, 76, 78, 80, 78, 76],  // MAP 60
  [48, 48, 50, 53, 57, 61, 65, 68, 71, 74, 77, 79, 81, 83, 81, 79],  // MAP 66
  [50, 50, 52, 55, 59, 63, 67, 70, 73, 76, 79, 81, 83, 85, 83, 81],  // MAP 70
  [52, 52, 54, 57, 61, 65, 69, 72, 75, 78, 81, 83, 85, 87, 85, 83],  // MAP 76
  [54, 54, 56, 59, 63, 67, 71, 74, 77, 80, 83, 85, 87, 89, 87, 85],  // MAP 86
  [55, 55, 57, 60, 64, 68, 72, 75, 78, 81, 84, 86, 88, 90, 88, 86],  // MAP 90
  [56, 56, 58, 61, 65, 69, 73, 76, 79, 82, 85, 87, 89, 91, 89, 87],  // MAP 96
  [57, 57, 59, 62, 66, 70, 74, 77, 80, 83, 86, 88, 90, 92, 90, 88],  // MAP 100
];

// Target AFR for this engine: 14.7 at cruise/idle, 12.8 at WOT
function getTargetAFR(map, rpm) {
  if (map >= 90) return 12.8;  // WOT - rich for power/safety
  if (map >= 80) return 13.2;  // High load
  if (map >= 70) return 13.5;  // Medium-high load
  if (map >= 60) return 14.0;  // Medium load
  return 14.7;                  // Cruise/idle - stoichiometric
}

// Find nearest bin indices
function findBinIndex(value, bins) {
  if (value <= bins[0]) return 0;
  if (value >= bins[bins.length - 1]) return bins.length - 1;
  for (let i = 0; i < bins.length - 1; i++) {
    if (value >= bins[i] && value < bins[i + 1]) {
      // Return the nearest bin
      return (value - bins[i]) < (bins[i + 1] - value) ? i : i + 1;
    }
  }
  return bins.length - 1;
}

function analyzeCSV(filename) {
  const data = fs.readFileSync(filename, 'utf8');
  const lines = data.split('\n').filter(l => l.trim());
  const headers = lines[0].split(';').map(h => h.replace(/"/g, '').trim());
  
  const timeIdx = headers.indexOf('Time');
  const rpmIdx = headers.indexOf('RPM');
  const mapIdx = headers.indexOf('MAP');
  const afrIdx = headers.indexOf('AFR');
  const cltIdx = headers.indexOf('CLT');
  const veIdx = headers.indexOf('VE _Current') !== -1 ? headers.indexOf('VE _Current') : headers.indexOf('VE1');
  const tpsIdx = headers.indexOf('TPS');
  const pwIdx = headers.indexOf('PW');
  const afrTargIdx = headers.indexOf('AFR Target');
  
  // Collect data points per VE cell
  // Key: "rpmBinIdx_mapBinIdx" -> array of {afr, afrTarget, clt, rpm, map}
  const cellData = {};
  let totalPoints = 0;
  let skippedLowRPM = 0;
  let skippedTransient = 0;
  
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(';');
    const rpm = parseFloat(cols[rpmIdx]);
    const map = parseFloat(cols[mapIdx]);
    const afr = parseFloat(cols[afrIdx]);
    const clt = parseFloat(cols[cltIdx]);
    const ve = parseFloat(cols[veIdx]);
    const tps = parseFloat(cols[tpsIdx]);
    const pw = parseFloat(cols[pwIdx]);
    const afrTarg = parseFloat(cols[afrTargIdx]);
    
    // Skip invalid data
    if (isNaN(rpm) || isNaN(map) || isNaN(afr) || rpm < 400 || afr < 8 || afr > 22) {
      skippedLowRPM++;
      continue;
    }
    
    // Skip data during rapid transients (TPS changing fast = AE active)
    // We want steady-state data only
    // Check next sample for TPS change
    if (i < lines.length - 1) {
      const nextCols = lines[i + 1].split(';');
      const nextTps = parseFloat(nextCols[tpsIdx]);
      if (!isNaN(nextTps) && Math.abs(nextTps - tps) > 3) {
        skippedTransient++;
        continue;
      }
    }
    
    const rpmBinIdx = findBinIndex(rpm, rpmBins);
    const mapBinIdx = findBinIndex(map, mapBins);
    const key = `${rpmBinIdx}_${mapBinIdx}`;
    
    if (!cellData[key]) {
      cellData[key] = [];
    }
    cellData[key].push({ afr, afrTarget: afrTarg, clt, rpm, map, ve, pw, tps });
    totalPoints++;
  }
  
  return { cellData, totalPoints, skippedLowRPM, skippedTransient };
}

// Analyze both running logs
console.log('=== VE TABLE CORRECTION ANALYSIS ===\n');

const files = ['2026-02-28_17.53.41.csv', '2026-02-28_18.10.43.csv'];
const combined = {};

for (const file of files) {
  console.log(`Processing: ${file}`);
  try {
    const result = analyzeCSV(file);
    console.log(`  Data points: ${result.totalPoints}, Skipped (low RPM/invalid): ${result.skippedLowRPM}, Skipped (transient): ${result.skippedTransient}`);
    
    // Merge into combined
    for (const [key, points] of Object.entries(result.cellData)) {
      if (!combined[key]) combined[key] = [];
      combined[key] = combined[key].concat(points);
    }
  } catch (e) {
    console.log(`  Error: ${e.message}`);
  }
}

console.log('\n=== CELL-BY-CELL ANALYSIS ===\n');
console.log('Format: VE Cell [RPM bin x MAP bin] | Current VE | Avg AFR | Target AFR | Correction Factor | New VE | Samples\n');

// Build correction table
const corrections = [];
const newVeTable = veTable.map(row => [...row]); // deep copy

// Sort keys for organized output
const keys = Object.keys(combined).sort((a, b) => {
  const [ar, am] = a.split('_').map(Number);
  const [br, bm] = b.split('_').map(Number);
  return am - bm || ar - br;
});

for (const key of keys) {
  const [rpmIdx, mapIdx_] = key.split('_').map(Number);
  const points = combined[key];
  
  if (points.length < 5) continue; // Need minimum samples for reliable correction
  
  const rpm = rpmBins[rpmIdx];
  const map = mapBins[mapIdx_];
  const currentVE = veTable[mapIdx_][rpmIdx];
  
  // Calculate average AFR (trim outliers)
  const afrs = points.map(p => p.afr).sort((a, b) => a - b);
  // Trim 10% from each end
  const trimCount = Math.floor(afrs.length * 0.1);
  const trimmed = afrs.slice(trimCount, afrs.length - trimCount);
  const avgAFR = trimmed.reduce((s, v) => s + v, 0) / trimmed.length;
  
  // Average CLT to understand temperature context
  const avgCLT = points.reduce((s, p) => s + p.clt, 0) / points.length;
  
  // Target AFR for this operating point
  const targetAFR = getTargetAFR(map, rpm);
  
  // VE correction: if AFR is lean (high), need MORE fuel = increase VE
  // VE_new = VE_current * (AFR_measured / AFR_target)
  const correctionFactor = avgAFR / targetAFR;
  let newVE = Math.round(currentVE * correctionFactor);
  
  // Clamp to reasonable range
  newVE = Math.max(20, Math.min(120, newVE));
  
  const change = newVE - currentVE;
  const changeStr = change > 0 ? `+${change}` : `${change}`;
  
  if (Math.abs(change) >= 1) {
    corrections.push({
      rpm, map, rpmIdx, mapIdx: mapIdx_,
      currentVE, newVE, change,
      avgAFR: avgAFR.toFixed(1),
      targetAFR,
      correctionFactor: correctionFactor.toFixed(3),
      samples: points.length,
      avgCLT: avgCLT.toFixed(1)
    });
    newVeTable[mapIdx_][rpmIdx] = newVE;
  }
  
  const needsChange = Math.abs(change) >= 1 ? ' <<<' : '';
  console.log(
    `RPM ${String(rpm).padStart(4)} | MAP ${String(map).padStart(3)}kPa | VE ${String(currentVE).padStart(2)}→${String(newVE).padStart(2)} (${changeStr.padStart(3)}) | AFR ${avgAFR.toFixed(1).padStart(5)} → ${targetAFR.toFixed(1)} | CF ${correctionFactor.toFixed(3)} | n=${String(points.length).padStart(5)} | CLT ${avgCLT.toFixed(0).padStart(3)}°C${needsChange}`
  );
}

console.log('\n=== CELLS NEEDING CHANGES ===\n');
corrections.sort((a, b) => Math.abs(b.change) - Math.abs(a.change));
for (const c of corrections) {
  const dir = c.change > 0 ? 'LEAN→increase' : 'RICH→decrease';
  console.log(
    `RPM ${String(c.rpm).padStart(4)} | MAP ${String(c.map).padStart(3)}kPa | VE ${c.currentVE}→${c.newVE} (${c.change > 0 ? '+' : ''}${c.change}) | ${dir} | AFR ${c.avgAFR}→${c.targetAFR} | ${c.samples} samples`
  );
}

// Temperature-separated analysis for WUE verification
console.log('\n=== AFR BY TEMPERATURE RANGE (for WUE verification) ===\n');
const tempRanges = [
  { min: -40, max: 20, label: 'Cold (<20°C)' },
  { min: 20, max: 40, label: 'Warming (20-40°C)' },
  { min: 40, max: 60, label: 'Mid (40-60°C)' },
  { min: 60, max: 80, label: 'Near-warm (60-80°C)' },
  { min: 80, max: 120, label: 'Hot (>80°C)' },
];

for (const range of tempRanges) {
  const points = [];
  for (const [key, data] of Object.entries(combined)) {
    for (const p of data) {
      if (p.clt >= range.min && p.clt < range.max && p.rpm >= 400 && p.rpm < 2000 && p.map < 60) {
        points.push(p);
      }
    }
  }
  if (points.length > 0) {
    const avgAfr = points.reduce((s, p) => s + p.afr, 0) / points.length;
    const avgClt = points.reduce((s, p) => s + p.clt, 0) / points.length;
    const avgRpm = points.reduce((s, p) => s + p.rpm, 0) / points.length;
    console.log(`${range.label}: avg AFR=${avgAfr.toFixed(1)}, avg CLT=${avgClt.toFixed(1)}°C, avg RPM=${avgRpm.toFixed(0)}, samples=${points.length}`);
  }
}

// High RPM analysis
console.log('\n=== HIGH RPM ANALYSIS (>5000 RPM - Rev Limiter Zone) ===\n');
for (const [key, data] of Object.entries(combined)) {
  const [rpmIdx, mapIdx_] = key.split('_').map(Number);
  const rpm = rpmBins[rpmIdx];
  if (rpm >= 4800) {
    const afrs = data.map(p => p.afr);
    const minAfr = Math.min(...afrs);
    const maxAfr = Math.max(...afrs);
    const avgAfr = afrs.reduce((s, v) => s + v, 0) / afrs.length;
    const rpms = data.map(p => p.rpm);
    const actualMaxRpm = Math.max(...rpms);
    console.log(
      `RPM bin ${rpm} | MAP ${mapBins[mapIdx_]}kPa | AFR min=${minAfr.toFixed(1)} avg=${avgAfr.toFixed(1)} max=${maxAfr.toFixed(1)} | actual max RPM=${actualMaxRpm} | n=${data.length}`
    );
  }
}

// Print the new VE table
console.log('\n=== PROPOSED NEW VE TABLE ===\n');
console.log('       ' + rpmBins.map(r => String(r).padStart(5)).join(' '));
for (let m = 0; m < mapBins.length; m++) {
  const changed = newVeTable[m].map((v, r) => {
    const old = veTable[m][r];
    if (v !== old) return `${String(v).padStart(4)}*`;
    return String(v).padStart(5);
  }).join(' ');
  console.log(`${String(mapBins[m]).padStart(3)}kPa ${changed}`);
}

console.log('\n=== ORIGINAL VE TABLE (for comparison) ===\n');
console.log('       ' + rpmBins.map(r => String(r).padStart(5)).join(' '));
for (let m = 0; m < mapBins.length; m++) {
  console.log(`${String(mapBins[m]).padStart(3)}kPa ${veTable[m].map(v => String(v).padStart(5)).join(' ')}`);
}

// Print MSQ format for copy-paste
console.log('\n=== VE TABLE IN MSQ FORMAT (copy-paste into TunerStudio) ===\n');
for (let m = 0; m < mapBins.length; m++) {
  console.log('         ' + newVeTable[m].map(v => `${v}.0`).join(' ') + ' ');
}
