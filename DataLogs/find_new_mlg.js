const fs = require('fs');
const chatPath = 'C:\\Users\\User1\\AppData\\Roaming\\Code\\User\\workspaceStorage\\5323181ec9c0e79a376a9c20c4ff0a51\\chatSessions\\91e9721a-f7ad-4450-a4af-0b181291c495.json';
const outPath = 'C:\\Users\\User1\\Documents\\TunerStudioProjects\\Passat2025\\DataLogs\\find_new_mlg.txt';

const stat = fs.statSync(chatPath);
console.log('File size: ' + (stat.size / 1024 / 1024).toFixed(1) + ' MB');

// We need to search more of the file - read last 50MB
const fd = fs.openSync(chatPath, 'r');
const chunkSize = 50 * 1024 * 1024;
const start = Math.max(0, stat.size - chunkSize);
const buffer = Buffer.alloc(Math.min(chunkSize, stat.size));
const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, start);
fs.closeSync(fd);

const data = buffer.toString('utf-8', 0, bytesRead);

// Search for messages where AI asks user to make/record a new datalog
const regex = /"value"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
let match;
const results = [];

while ((match = regex.exec(data)) !== null) {
    let text = match[1];
    if (text.length > 100) {
        let decoded = text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
        const lower = decoded.toLowerCase();
        // Look for AI telling user to make a new datalog/drive/record
        if ((lower.includes('new datalog') || lower.includes('new mlg') || lower.includes('go for a drive') || 
             lower.includes('record a new') || lower.includes('make a new log') || lower.includes('take a new') ||
             lower.includes('need a new') || lower.includes('need you to') || lower.includes('next step') ||
             lower.includes('please record') || lower.includes('please make') || lower.includes('please go') ||
             lower.includes('fresh datalog') || lower.includes('fresh log') || lower.includes('start logging'))
            && !decoded.includes('base64')
            && decoded.length > 100
            && decoded.length < 10000) {
            results.push({
                position: match.index,
                text: decoded.substring(0, 4000)
            });
        }
    }
}

let output = `=== AI MESSAGES ASKING FOR NEW DATALOG (last 50MB) ===\n`;
output += `Total found: ${results.length}\n\n`;

// Show last 10
const recent = results.slice(-10);
recent.forEach((m, i) => {
    output += `--- Match ${i + 1} (position ${m.position}) ---\n`;
    output += m.text + '\n\n';
});

fs.writeFileSync(outPath, output, 'utf-8');
console.log(`Found ${results.length} matches. Saved last ${recent.length}.`);
