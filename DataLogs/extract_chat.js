const fs = require('fs');
const chatPath = 'C:\\Users\\User1\\AppData\\Roaming\\Code\\User\\workspaceStorage\\5323181ec9c0e79a376a9c20c4ff0a51\\chatSessions\\91e9721a-f7ad-4450-a4af-0b181291c495.json';
const outPath = 'C:\\Users\\User1\\Documents\\TunerStudioProjects\\Passat2025\\DataLogs\\chat_session_extract.txt';

const stat = fs.statSync(chatPath);
console.log('File size: ' + (stat.size / 1024 / 1024).toFixed(1) + ' MB');

// Read last 5MB
const fd = fs.openSync(chatPath, 'r');
const chunkSize = 5 * 1024 * 1024;
const start = Math.max(0, stat.size - chunkSize);
const buffer = Buffer.alloc(Math.min(chunkSize, stat.size));
const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, start);
fs.closeSync(fd);

const data = buffer.toString('utf-8', 0, bytesRead);

// Extract user and assistant text content
const output = [];

// Find "text" fields that contain actual conversation
const textRegex = /"text"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
let match;
const allTexts = [];
while ((match = textRegex.exec(data)) !== null) {
    let text = match[1];
    // Unescape
    text = text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
    // Skip base64, very short, or binary-looking content
    if (text.length > 20 && !text.includes('base64') && !text.startsWith('data:') && !/^[A-Za-z0-9+/=\s]{100,}$/.test(text)) {
        allTexts.push(text);
    }
}

output.push('=== EXTRACTED CHAT SESSION (last 5MB of 220MB file) ===');
output.push('Total text fragments found: ' + allTexts.length);
output.push('');

// Write last 50 fragments (most recent conversation)
const recent = allTexts.slice(-50);
recent.forEach((t, i) => {
    output.push('--- Fragment ' + (i + 1) + ' ---');
    output.push(t.substring(0, 2000));
    output.push('');
});

fs.writeFileSync(outPath, output.join('\n'), 'utf-8');
console.log('Written to: ' + outPath);
console.log('Extracted ' + recent.length + ' text fragments');
