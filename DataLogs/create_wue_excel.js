const XLSX = require('xlsx');

// WUE bins and values
const coolantBins = [-40, -26, 10, 19, 28, 37, 50, 65, 80, 90];

const currentWUE =     [180, 175, 168, 154, 134, 121, 112, 106, 102, 100];
const recommendedWUE = [195, 190, 182, 154, 150, 138, 122, 110, 102, 100];

// Sheet 1: Comparison (current vs recommended)
const wsCompare = [
  ['Coolant °C', 'Current WUE %', 'New WUE %', 'Change'],
];
for (let i = 0; i < coolantBins.length; i++) {
  const change = recommendedWUE[i] - currentWUE[i];
  const changeStr = change > 0 ? `+${change}` : `${change}`;
  wsCompare.push([coolantBins[i], currentWUE[i], recommendedWUE[i], change]);
}

// Sheet 2: Values only for paste into TunerStudio (single column, top to bottom)
const wsPaste = [];
for (let i = 0; i < recommendedWUE.length; i++) {
  wsPaste.push([recommendedWUE[i]]);
}

const wb = XLSX.utils.book_new();

const ws1 = XLSX.utils.aoa_to_sheet(wsCompare);
ws1['!cols'] = [{ wch: 12 }, { wch: 14 }, { wch: 12 }, { wch: 8 }];
XLSX.utils.book_append_sheet(wb, ws1, 'WUE Comparison');

const ws2 = XLSX.utils.aoa_to_sheet(wsPaste);
ws2['!cols'] = [{ wch: 6 }];
XLSX.utils.book_append_sheet(wb, ws2, 'Paste into TunerStudio');

const outPath = 'WUE_TABLE_CORRECTED.xlsx';
XLSX.writeFile(wb, outPath);
console.log(`Created: ${outPath}`);
console.log('Sheet 1: "WUE Comparison" - current vs new values');
console.log('Sheet 2: "Paste into TunerStudio" - select all, copy, paste into WUE% column');
