const fs = require('fs');
const chatPath = 'C:\\Users\\User1\\AppData\\Roaming\\Code\\User\\workspaceStorage\\5323181ec9c0e79a376a9c20c4ff0a51\\chatSessions\\91e9721a-f7ad-4450-a4af-0b181291c495.json';
const outPath = 'C:\\Users\\User1\\Documents\\TunerStudioProjects\\Passat2025\\DataLogs\\last_ai_response.txt';

const stat = fs.statSync(chatPath);
const fd = fs.openSync(chatPath, 'r');

// Read last 300KB
const chunkSize = 300000;
const buffer = Buffer.alloc(chunkSize);
fs.readSync(fd, buffer, 0, chunkSize, stat.size - chunkSize);
fs.closeSync(fd);
const data = buffer.toString('utf-8');

// Find "value" fields with substantial text
const results = [];
const regex = /"value"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
let match;
while ((match = regex.exec(data)) !== null) {
    let text = match[1];
    text = text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
    if (text.length > 100 && !text.includes('base64') && !/^[A-Za-z0-9+/=\s]{200,}$/.test(text)) {
        results.push(text);
    }
}

let output = '=== LAST AI RESPONSES FROM SESSION ===\n\n';
const recent = results.slice(-5);
recent.forEach((t, i) => {
    output += `--- Response block ${i + 1} of ${recent.length} ---\n`;
    output += t.substring(0, 5000) + '\n\n';
});

fs.writeFileSync(outPath, output, 'utf-8');
console.log('Found ' + results.length + ' text blocks total');
console.log('Saved last ' + recent.length + ' to: ' + outPath);
