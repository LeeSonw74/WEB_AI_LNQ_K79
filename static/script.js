const chatIcon = document.getElementById('chatbot-icon');
const chatContainer = document.getElementById('chat-container');
const form = document.getElementById('chat-form');
const textarea = form.querySelector('textarea');
const loading = document.getElementById('loading');
const chatBody = document.getElementById('chat-body');

let isDragging = false;
let initialX = 0;
let initialY = 0;
let currentX = 20;
let currentY = 20;
let clickStartTime = 0;
const dragThreshold = 200;

// Toggle menu với hiệu ứng trượt
function toggleMenu() {
  const menu = document.getElementById('navbar-menu');
  menu.classList.toggle('active');
}

// Chuyển đổi chế độ Dark/Light
function toggleTheme() {
  document.body.classList.toggle('dark-mode');
  const moonIcon = document.querySelector('.theme-toggle i');
  if (document.body.classList.contains('dark-mode')) {
    moonIcon.classList.remove('fa-moon');
    moonIcon.classList.add('fa-sun');
  } else {
    moonIcon.classList.remove('fa-sun');
    moonIcon.classList.add('fa-moon');
  }
}

// Mở/đóng khung chat
function toggleChat(event) {
  if (chatContainer.classList.contains('visible')) {
    chatContainer.classList.remove('visible');
  } else {
    chatContainer.classList.add('visible');
    updateChatPosition();
  }
}

// Ẩn khung chat và xóa tin nhắn
function minimizeChat() {
  chatBody.innerHTML = '';
  textarea.value = '';
  chatContainer.classList.remove('visible');
}

// Xóa dữ liệu và đóng khung chat
function clearAndCloseChat() {
  chatBody.innerHTML = '';
  chatContainer.classList.remove('visible');
  textarea.value = '';
}

// Gửi tin nhắn bằng AJAX
function sendMessage() {
  const input = textarea.value.trim();
  if (input) {
    showLoading();
    $.post('/send_message', { input: input }, function(response) {
      if (response.status === 'success') {
        chatBody.innerHTML = ''; // Xóa nội dung cũ
        response.history.forEach(chat => {
          const userDiv = document.createElement('div');
          userDiv.className = 'message-wrapper';
          userDiv.innerHTML = `
            <div class="message user-message"><span>${chat[0]}</span></div>
            <div class="message bot-message"><span style="white-space: pre-wrap;">${chat[1]}</span></div>
          `;
          chatBody.appendChild(userDiv);
        });
        textarea.value = '';
        hideLoading();
        scrollToBottom();
      } else {
        hideLoading();
        alert(response.message);
      }
    }).fail(function() {
      hideLoading();
      alert('Lỗi khi gửi tin nhắn.');
    });
  } else {
    alert('Vui lòng nhập câu hỏi.');
  }
}

// Hiển thị loading
function showLoading() {
  loading.style.display = 'flex';
  textarea.disabled = true;
}

// Ẩn loading
function hideLoading() {
  loading.style.display = 'none';
  textarea.disabled = false;
}

// Gửi khi nhấn Enter
textarea.addEventListener('keypress', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    showLoading();
    sendMessage();
  }
});

// Cuộn xuống tin nhắn mới nhất
function scrollToBottom() {
  chatBody.scrollTop = chatBody.scrollHeight;
}

// Cập nhật nội dung từ server
window.addEventListener('load', function() {
  hideLoading();
  scrollToBottom();
});

// Kéo thả biểu tượng chatbot
if (chatIcon) {
  chatIcon.addEventListener('mousedown', startDragging);
  document.addEventListener('mousemove', drag);
  document.addEventListener('mouseup', stopDragging);
}

function startDragging(e) {
  if (e.button === 0) {
    e.preventDefault();
    initialX = e.clientX - currentX;
    initialY = e.clientY - currentY;
    clickStartTime = Date.now();
    isDragging = true;
    chatIcon.style.cursor = 'grabbing';
  }
}

function drag(e) {
  if (isDragging) {
    e.preventDefault();
    currentX = e.clientX - initialX;
    currentY = e.clientY - initialY;

    currentX = Math.max(0, Math.min(currentX, window.innerWidth - chatIcon.offsetWidth));
    currentY = Math.max(0, Math.min(currentY, window.innerHeight - chatIcon.offsetHeight));

    chatIcon.style.left = currentX + 'px';
    chatIcon.style.top = currentY + 'px';

    if (chatContainer.classList.contains('visible')) {
      updateChatPosition();
    }
  }
}

function stopDragging(e) {
  if (isDragging) {
    isDragging = false;
    chatIcon.style.cursor = 'move';
    const clickDuration = Date.now() - clickStartTime;
    if (clickDuration < dragThreshold) {
      toggleChat(e);
    }
  }
}

function updateChatPosition() {
  const iconRect = chatIcon.getBoundingClientRect();
  const chatWidth = chatContainer.offsetWidth;
  const windowWidth = window.innerWidth;
  const margin = 10;

  if (iconRect.left + chatWidth + margin > windowWidth) {
    chatContainer.style.left = (iconRect.left - chatWidth - margin) + 'px';
    chatContainer.style.right = 'auto';
  } else {
    chatContainer.style.left = (iconRect.left + chatIcon.offsetWidth + margin) + 'px';
    chatContainer.style.right = 'auto';
  }

  chatContainer.style.top = (iconRect.top - chatContainer.offsetHeight + chatIcon.offsetHeight + margin) + 'px';
}

window.addEventListener('resize', function() {
  if (chatContainer && chatContainer.classList.contains('visible')) {
    updateChatPosition();
  }
});