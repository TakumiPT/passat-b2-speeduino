// Extract all conversation text from the 210MB chat session
// Process in chunks to avoid memory issues
const fs = require('fs');
const chatPath = 'C:\\Users\\User1\\AppData\\Roaming\\Code\\User\\workspaceStorage\\5323181ec9c0e79a376a9c20c4ff0a51\\chatSessions\\91e9721a-f7ad-4450-a4af-0b181291c495.json';
const outPath = 'C:\\Users\\User1\\Documents\\TunerStudioProjects\\Passat2025\\DataLogs\\full_session_conversation.txt';

const stat = fs.statSync(chatPath);
const fileSize = stat.size;
console.log('File size: ' + (fileSize / 1024 / 1024).toFixed(1) + ' MB');

// Process the entire file in 10MB chunks with overlap
const chunkSize = 10 * 1024 * 1024;
const overlap = 50000; // 50KB overlap to catch split messages
const fd = fs.openSync(chatPath, 'r');
const outFd = fs.openSync(outPath, 'w');

let totalMessages = 0;
let position = 0;

fs.writeSync(outFd, '=== FULL SESSION CONVERSATION EXTRACT ===\n');
fs.writeSync(outFd, `File: ${chatPath}\n`);
fs.writeSync(outFd, `Size: ${(fileSize / 1024 / 1024).toFixed(1)} MB\n`);
fs.writeSync(outFd, `Extracted: ${new Date().toISOString()}\n\n`);

while (position < fileSize) {
    const readSize = Math.min(chunkSize, fileSize - position);
    const buffer = Buffer.alloc(readSize);
    fs.readSync(fd, buffer, 0, readSize, position);
    const data = buffer.toString('utf-8');
    
    // Extract user request messages
    const userReqRegex = /<userRequest>\s*([\s\S]*?)\s*<\/userRequest>/g;
    let match;
    while ((match = userReqRegex.exec(data)) !== null) {
        let text = match[1].trim();
        // Unescape JSON
        text = text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"');
        if (text.length > 3 && text.length < 5000) {
            fs.writeSync(outFd, `\n${'='.repeat(60)}\n`);
            fs.writeSync(outFd, `USER:\n`);
            fs.writeSync(outFd, text + '\n');
            totalMessages++;
        }
    }
    
    // Extract AI response "value" blocks that contain actual content (markdown responses)
    const valueRegex = /"value"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
    while ((match = valueRegex.exec(data)) !== null) {
        let text = match[1];
        if (text.length > 200 && text.length < 50000) {
            let decoded = text.replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"').replace(/\\\\/g, '\\');
            // Skip base64, file contents, terminal output, tool results
            if (!decoded.includes('base64') && 
                !/^[A-Za-z0-9+/=\s]{200,}$/.test(decoded) &&
                !decoded.startsWith('Note: The tool') &&
                !decoded.startsWith('Reading ') &&
                !decoded.startsWith('Read ') &&
                !decoded.startsWith('The following files') &&
                !decoded.startsWith('On branch ') &&
                !decoded.startsWith('Enumerating objects') &&
                !decoded.startsWith('[master ') &&
                !decoded.startsWith('c:\\') &&
                decoded.length > 200) {
                
                // Check if it looks like an AI response (has markdown formatting, complete sentences, etc.)
                const hasMarkdown = decoded.includes('#') || decoded.includes('**') || decoded.includes('|') || decoded.includes('- ');
                const hasWords = (decoded.match(/\s+/g) || []).length > 20;
                
                if (hasMarkdown || hasWords) {
                    fs.writeSync(outFd, `\n${'─'.repeat(60)}\n`);
                    fs.writeSync(outFd, `AI RESPONSE:\n`);
                    fs.writeSync(outFd, decoded.substring(0, 8000) + '\n');
                    totalMessages++;
                }
            }
        }
    }
    
    // Move to next chunk (with overlap to avoid splitting messages)
    position += chunkSize - overlap;
    process.stdout.write(`\rProcessed ${(position / 1024 / 1024).toFixed(0)}/${(fileSize / 1024 / 1024).toFixed(0)} MB...`);
}

fs.closeSync(fd);
fs.closeSync(outFd);

const outStat = fs.statSync(outPath);
console.log(`\nDone! Extracted ${totalMessages} messages.`);
console.log(`Output: ${outPath} (${(outStat.size / 1024).toFixed(0)} KB)`);
