let currentFileId = null;
let currentFileName = "";
let currentFullText = "";
let messageSources = {}; // Store sources for each message index

const fileList = document.getElementById('file-list');
const fileUpload = document.getElementById('file-upload');
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatHeader = document.getElementById('chat-header');
const fileSearch = document.getElementById('file-search');

// Load sessions on startup
async function loadSessions() {
    try {
        const res = await fetch('/sessions');
        const sessions = await res.json();
        renderFileList(sessions);
    } catch (e) {
        console.error("Lỗi khi tải sessions:", e);
    }
}

function renderFileList(sessions) {
    fileList.innerHTML = '';
    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = `file-item ${currentFileId === session.file_id ? 'active' : ''}`;
        item.innerHTML = `
            <div class="file-info" onclick="selectSession('${session.file_id}', '${session.file_name}')">
                <i class="far fa-file-alt"></i> 
                <span>${session.file_name}</span>
            </div>
            <button class="delete-session-btn" onclick="deleteSession(event, '${session.file_id}')">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        fileList.appendChild(item);
    });
}

async function deleteSession(event, fileId) {
    event.stopPropagation();
    if (!confirm('Bạn có chắc chắn muốn xóa lịch sử chat và dữ liệu của tài liệu này?')) return;
    
    try {
        const res = await fetch(`/session/${fileId}`, { method: 'DELETE' });
        if (res.ok) {
            if (currentFileId === fileId) {
                currentFileId = null;
                currentFileName = "";
                currentFullText = "";
                chatHeader.innerText = "Chọn tài liệu để bắt đầu";
                chatMessages.innerHTML = '';
                userInput.disabled = true;
                sendBtn.disabled = true;
                toggleSourcePanel(false);
            }
            await loadSessions();
        } else {
            alert('Lỗi khi xóa session.');
        }
    } catch (err) {
        console.error(err);
        alert('Lỗi kết nối server.');
    }
}

async function selectSession(fileId, fileName) {
    currentFileId = fileId;
    currentFileName = fileName;
    chatHeader.innerText = fileName;
    
    // Enable input
    userInput.disabled = false;
    sendBtn.disabled = false;
    
    // Fetch full text
    try {
        const textRes = await fetch(`/text/${fileId}`);
        const textData = await textRes.json();
        currentFullText = textData.text;
    } catch (err) {
        console.error("Lỗi khi tải nội dung văn bản:", err);
        currentFullText = "";
    }
    
    // Update active UI
    document.querySelectorAll('.file-item').forEach(el => {
        const span = el.querySelector('.file-info span');
        if (span) {
            el.classList.toggle('active', span.innerText === fileName);
        }
    });
    
    // Load messages
    const res = await fetch(`/history/${fileId}`);
    const history = await res.json();
    
    chatMessages.innerHTML = '';
    messageSources = {};
    if (history.length === 0) {
        appendMessage('assistant', `Tôi đã sẵn sàng trả lời các câu hỏi về tài liệu: ${fileName}. Bạn có thể gõ "Tóm tắt tài liệu" để xem bản tóm tắt.`);
    } else {
        history.forEach((msg, idx) => {
            const id = `msg-${idx}`;
            let sources = [];
            if (msg.role === 'assistant' && msg.metadata) {
                try {
                    sources = JSON.parse(msg.metadata);
                    messageSources[id] = sources;
                } catch (e) {
                    console.error("Error parsing metadata:", e);
                }
            }
            appendMessage(msg.role, msg.content, id, sources);
        });
    }
}

fileUpload.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    appendMessage('assistant', `Đang xử lý file ${file.name}, vui lòng đợi giây lát... <span class="dots"></span>`);
    
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.file_id) {
            await loadSessions();
            selectSession(data.file_id, data.file_name);
        }
    } catch (err) {
        appendMessage('assistant', 'Có lỗi xảy ra khi upload file.');
    }
};

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || !currentFileId) return;
    
    userInput.value = '';
    userInput.style.height = 'auto';
    appendMessage('user', text);
    
    const loadingId = 'loading-' + Date.now();
    appendMessage('assistant', '<span class="dots"></span>', loadingId);
    
    const formData = new FormData();
    formData.append('file_id', currentFileId);
    formData.append('message', text);
    
    try {
        const res = await fetch('/chat', { method: 'POST', body: formData });
        if (!res.ok) {
            const errorMsg = await res.json().catch(() => ({message: "Lỗi hệ thống (500)"}));
            throw new Error(errorMsg.message || "Lỗi khi gọi API");
        }
        
        const data = await res.json();
        
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            const content = data.answer || "Lỗi định dạng dữ liệu";
            const sources = data.sources || [];
            
            loadingEl.querySelector('.content').innerHTML = formatAnswerWithCitations(content, sources, loadingId);
            messageSources[loadingId] = sources;
        }
    } catch (err) {
        console.error(err);
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.querySelector('.content').innerText = `Lỗi: ${err.message}`;
        }
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatAnswerWithCitations(text, sources, msgId) {
    if (typeof text !== 'string') text = String(text);
    
    let html = marked.parse(text);
    if (!sources || sources.length === 0) return html;

    let citationFound = false;
    sources.forEach(source => {
        const citationTag = `[${source.id}]`;
        const buttonHtml = `<button class="citation-btn" onclick="showSource('${msgId}', ${source.id})">${citationTag}</button>`;
        
        const escapedTag = citationTag.replace(/[\[\]]/g, '\\$&');
        const regex = new RegExp(escapedTag, 'g');
        
        if (html.match(regex)) {
            html = html.replace(regex, buttonHtml);
            citationFound = true;
        }
    });

    if (!citationFound && sources.length > 0) {
        html += `<div style="margin-top: 10px; border-top: 1px dashed #ccc; padding-top: 5px;">
                    <button class="citation-btn" style="font-size: 11px;" onclick="showSource('${msgId}', 1)">
                        <i class="fas fa-search"></i> Xem nguồn tài liệu
                    </button>
                 </div>`;
    }
    
    return html;
}

function showSource(msgId, sourceId) {
    const sources = messageSources[msgId];
    if (!sources) return;
    
    const source = sources.find(s => s.id === sourceId);
    if (!source) return;

    toggleSourcePanel(true);
    const sourceContent = document.getElementById('source-content');
    
    if (!currentFullText) {
        sourceContent.innerHTML = `<div class="placeholder-text">Không tìm thấy nội dung văn bản gốc.</div>`;
        return;
    }

    // New Accuracy Logic: Use offsets if available
    let highlightedText = "";
    if (source.start !== undefined && source.end !== undefined && source.start !== null) {
        const start = source.start;
        const end = source.end;
        
        const before = currentFullText.substring(0, start);
        const chunk = currentFullText.substring(start, end);
        const after = currentFullText.substring(end);
        
        // Escape HTML for safety, but keep our <mark>
        highlightedText = escapeHtml(before) + '<mark class="highlight">' + escapeHtml(chunk) + '</mark>' + escapeHtml(after);
    } else {
        // Fallback for older data: regex match
        const escapedContent = source.content.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedContent})`, 'gi');
        highlightedText = escapeHtml(currentFullText).replace(regex, '<mark class="highlight">$1</mark>');
    }
    
    sourceContent.innerHTML = `<pre>${highlightedText}</pre>`;
    
    setTimeout(() => {
        const firstMark = sourceContent.querySelector('mark');
        if (firstMark) {
            firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function toggleSourcePanel(show) {
    const panel = document.getElementById('source-panel');
    if (panel) {
        panel.classList.toggle('open', show);
    }
}

function appendMessage(role, content, id = null, sources = null) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (id) div.id = id;
    
    const icon = role === 'user' ? 'fa-user-astronaut' : 'fa-robot';
    
    let innerContent = "";
    if (role === 'assistant') {
        innerContent = formatAnswerWithCitations(content, sources || [], id);
    } else {
        innerContent = marked.parse(String(content));
    }

    div.innerHTML = `
        <div class="avatar"><i class="fas ${icon}"></i></div>
        <div class="content">${innerContent}</div>
    `;
    
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Event Listeners
sendBtn.onclick = sendMessage;
userInput.onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
};

userInput.oninput = () => {
    userInput.style.height = 'auto';
    userInput.style.height = userInput.scrollHeight + 'px';
};

fileSearch.oninput = (e) => {
    const term = e.target.value.toLowerCase();
    document.querySelectorAll('.file-item').forEach(item => {
        const span = item.querySelector('.file-info span');
        if (span) {
            const text = span.innerText.toLowerCase();
            item.style.display = text.includes(term) ? 'flex' : 'none';
        }
    });
};

loadSessions();
