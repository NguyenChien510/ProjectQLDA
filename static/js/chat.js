let currentFileId = null;
let currentFileName = "";

const fileList = document.getElementById('file-list');
const fileUpload = document.getElementById('file-upload');
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatHeader = document.getElementById('chat-header');
const fileSearch = document.getElementById('file-search');

// Load sessions on startup
async function loadSessions() {
    const res = await fetch('/sessions');
    const sessions = await res.json();
    renderFileList(sessions);
}

function renderFileList(sessions) {
    fileList.innerHTML = '';
    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = `file-item ${currentFileId === session.file_id ? 'active' : ''}`;
        item.innerHTML = `<i class="far fa-file-alt"></i> ${session.file_name}`;
        item.onclick = () => selectSession(session.file_id, session.file_name);
        fileList.appendChild(item);
    });
}

async function selectSession(fileId, fileName) {
    currentFileId = fileId;
    currentFileName = fileName;
    chatHeader.innerText = fileName;
    
    // Enable input
    userInput.disabled = false;
    sendBtn.disabled = false;
    
    // Update active UI
    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.toggle('active', el.innerText.includes(fileName));
    });
    
    // Load messages
    const res = await fetch(`/history/${fileId}`);
    const history = await res.json();
    
    chatMessages.innerHTML = '';
    if (history.length === 0) {
        appendMessage('assistant', `Tôi đã sẵn sàng trả lời các câu hỏi về tài liệu: ${fileName}. Bạn có thể gõ "Tóm tắt tài liệu" để xem bản tóm tắt.`);
    } else {
        history.forEach(msg => appendMessage(msg.role, msg.content));
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
    
    // Loading indicator
    const loadingId = 'loading-' + Date.now();
    appendMessage('assistant', '<span class="dots"></span>', loadingId);
    
    const formData = new FormData();
    formData.append('file_id', currentFileId);
    formData.append('message', text);
    
    try {
        const res = await fetch('/chat', { method: 'POST', body: formData });
        const data = await res.json();
        
        // Replace loading with answer
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.querySelector('.content').innerHTML = marked.parse(data.answer);
        }
    } catch (err) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.querySelector('.content').innerText = 'Lỗi: Không thể kết nối với server.';
        }
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendMessage(role, content, id = null) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (id) div.id = id;
    
    const icon = role === 'user' ? 'fa-user-astronaut' : 'fa-robot';
    
    div.innerHTML = `
        <div class="avatar"><i class="fas ${icon}"></i></div>
        <div class="content">${marked.parse(content)}</div>
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

// Auto resize textarea
userInput.oninput = () => {
    userInput.style.height = 'auto';
    userInput.style.height = userInput.scrollHeight + 'px';
};

// Search filter
fileSearch.oninput = (e) => {
    const term = e.target.value.toLowerCase();
    document.querySelectorAll('.file-item').forEach(item => {
        const text = item.innerText.toLowerCase();
        item.style.display = text.includes(term) ? 'flex' : 'none';
    });
};

loadSessions();
