const fs = require('fs');
const chatPath = 'C:\\Users\\User1\\AppData\\Roaming\\Code\\User\\workspaceStorage\\5323181ec9c0e79a376a9c20c4ff0a51\\chatSessions\\91e9721a-f7ad-4450-a4af-0b181291c495.json';
const outPath = 'C:\\Users\\User1\\Documents\\TunerStudioProjects\\Passat2025\\DataLogs\\find_mlg_message.txt';

const stat = fs.statSync(chatPath);
const fd = fs.openSync(chatPath, 'r');

// Read last 20MB to find mlg-related messages
const chunkSize = 20 * 1024 * 1024;
const start = Math.max(0, stat.size - chunkSize);
const buffer = Buffer.alloc(Math.min(chunkSize, stat.size));
const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, start);
fs.closeSync(fd);

const data = buffer.toString('utf-8', 0, bytesRead);

// Find all text fragments that mention mlg, datalog, or recording
const regex = /"value"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
let match;
const mlgMessages = [];
let idx = 0;

while ((match = regex.exec(data)) !== null) {
    let text = match[1];
    if (text.length > 50) {
        let decoded = text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
        const lower = decoded.toLowerCase();
        if ((lower.includes('mlg') || lower.includes('datalog') || lower.includes('data log') || lower.includes('record') || lower.includes('new log') || lower.includes('go for a drive') || lower.includes('take a log') || lower.includes('make a log')) 
            && !decoded.includes('base64') 
            && decoded.length > 80) {
            mlgMessages.push({
                index: idx,
                position: match.index,
                text: decoded.substring(0, 3000)
            });
        }
    }
    idx++;
}

let output = `=== MESSAGES MENTIONING MLG/DATALOG (last 20MB) ===\n`;
output += `Total found: ${mlgMessages.length}\n\n`;

// Show last 15 matches
const recent = mlgMessages.slice(-15);
recent.forEach((m, i) => {
    output += `--- Match ${i + 1} (block #${m.index}, position ${m.position}) ---\n`;
    output += m.text + '\n\n';
});

fs.writeFileSync(outPath, output, 'utf-8');
console.log(`Found ${mlgMessages.length} MLG-related messages. Saved last ${recent.length} to file.`);
