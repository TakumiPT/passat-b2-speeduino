const XLSX = require('xlsx');

// RPM bins (columns) and MAP bins (rows) - matching TunerStudio layout
const rpmBins = [500, 700, 900, 1200, 1500, 1800, 2200, 2700, 3000, 3400, 3900, 4300, 4800, 5200, 5700, 6200];
const mapBins = [100, 96, 90, 86, 76, 70, 66, 60, 56, 50, 46, 40, 36, 30, 26, 16];

// Corrected VE table (top=100kPa, bottom=16kPa, same as TunerStudio view)
const veData = [
  [57, 57, 59, 62, 66, 70, 74, 77, 80, 83, 86, 88, 90, 92, 90, 88],
  [56, 56, 58, 61, 65, 69, 73, 76, 79, 82, 85, 87, 89, 91, 89, 87],
  [55, 55, 57, 60, 64, 68, 72, 75, 78, 81, 84, 86, 88, 90, 88, 86],
  [54, 54, 56, 59, 63, 67, 71, 74, 77, 80, 83, 85, 87, 89, 87, 85],
  [52, 52, 54, 57, 61, 65, 69, 72, 75, 78, 81, 83, 85, 87, 85, 83],
  [50, 50, 52, 55, 59, 63, 67, 70, 73, 76, 79, 81, 83, 85, 83, 81],
  [48, 48, 50, 53, 57, 61, 65, 68, 71, 74, 77, 79, 81, 83, 81, 79],
  [45, 45, 47, 50, 54, 58, 62, 65, 68, 71, 74, 76, 78, 80, 78, 76],
  [42, 42, 44, 47, 51, 55, 59, 62, 65, 68, 71, 73, 75, 77, 75, 73],
  [40, 40, 42, 45, 49, 53, 57, 60, 63, 66, 69, 71, 73, 75, 73, 71],
  [38, 38, 40, 43, 47, 51, 55, 58, 61, 64, 67, 69, 71, 73, 71, 69],
  [36, 36, 38, 34, 45, 49, 53, 56, 59, 62, 65, 67, 69, 71, 69, 67],  // RPM1200: 41→34
  [34, 34, 36, 34, 43, 47, 51, 54, 57, 60, 63, 65, 67, 69, 67, 65],  // RPM1200: 39→34
  [32, 32, 34, 36, 41, 45, 49, 52, 55, 58, 61, 63, 65, 67, 65, 63],  // RPM1200: 37→36
  [31, 31, 33, 36, 40, 43, 45, 51, 54, 57, 60, 62, 64, 66, 64, 62],  // RPM1800:44→43, RPM2200:48→45
  [30, 30, 32, 35, 39, 43, 47, 50, 53, 56, 59, 61, 63, 65, 63, 61],
];

// Build worksheet data
// Sheet 1: VE table with headers (for reference)
const wsData = [];

// Header row: empty cell + RPM bins
wsData.push(['kPa \\ RPM', ...rpmBins]);

// Data rows
for (let i = 0; i < mapBins.length; i++) {
  wsData.push([mapBins[i], ...veData[i]]);
}

// Sheet 2: VE values only (no headers) - for direct paste into TunerStudio
const wsDataOnly = [];
for (let i = 0; i < veData.length; i++) {
  wsDataOnly.push([...veData[i]]);
}

// Create workbook
const wb = XLSX.utils.book_new();

// Sheet 1 - with labels
const ws1 = XLSX.utils.aoa_to_sheet(wsData);
// Set column widths
ws1['!cols'] = [{ wch: 10 }, ...rpmBins.map(() => ({ wch: 5 }))];
XLSX.utils.book_append_sheet(wb, ws1, 'VE Table (with labels)');

// Sheet 2 - values only for paste
const ws2 = XLSX.utils.aoa_to_sheet(wsDataOnly);
ws2['!cols'] = rpmBins.map(() => ({ wch: 5 }));
XLSX.utils.book_append_sheet(wb, ws2, 'Paste into TunerStudio');

// Write file
const outPath = 'VE_TABLE_CORRECTED.xlsx';
XLSX.writeFile(wb, outPath);
console.log(`Created: ${outPath}`);
console.log('Sheet 1: "VE Table (with labels)" - for reference');
console.log('Sheet 2: "Paste into TunerStudio" - select all, copy, paste into VE table');
