const form = document.getElementById('chat-form');
const textarea = form ? form.querySelector('textarea') : null;
const loading = document.getElementById('loading');
const chatBody = document.getElementById('chat-body');

if (!form || !textarea || !loading || !chatBody) {
  console.error('Một hoặc nhiều phần tử DOM không được tìm thấy trong scripts.js.');
}

function toggleMenu() {
  const menu = document.getElementById('navbar-menu');
  if (menu) {
    menu.classList.toggle('active');
  }
}

function toggleTheme() {
  document.body.classList.toggle('dark-mode');
  const moonIcon = document.querySelector('.theme-toggle i');
  const isDarkMode = document.body.classList.contains('dark-mode');
  if (moonIcon) {
    if (isDarkMode) {
      moonIcon.classList.remove('fa-moon');
      moonIcon.classList.add('fa-sun');
      localStorage.setItem('theme', 'dark');
    } else {
      moonIcon.classList.remove('fa-sun');
      moonIcon.classList.add('fa-moon');
      localStorage.setItem('theme', 'light');
    }
  }
}

function sendMessage() {
  const input = textarea.value.trim();
  if (input) {
    showLoading();
    $.post('/send_message', { input: input }, function(response) {
      if (response.status === 'success') {
        chatBody.innerHTML = '';
        response.history.forEach(chat => {
          const userDiv = document.createElement('div');
          userDiv.className = 'message-wrapper';
          userDiv.innerHTML = `
            <div class="message user-message"><span>🗣 ${chat[0]}</span></div>
            <div class="message bot-message"><span style="white-space: pre-wrap;">🤖 ${chat[1]}</span></div>
          `;
          chatBody.appendChild(userDiv);
        });
        textarea.value = '';
        hideLoading();
        scrollToBottom();
      } else {
        hideLoading();
        alert(response.message || 'Lỗi khi gửi tin nhắn. Vui lòng thử lại.');
      }
    }).fail(function(jqXHR, textStatus, errorThrown) {
      hideLoading();
      alert(`Lỗi kết nối đến server: ${textStatus}. Vui lòng thử lại.`);
      console.error('Lỗi AJAX trong sendMessage:', textStatus, errorThrown);
    });
  } else {
    alert('Vui lòng nhập câu hỏi.');
  }
}

function showLoading() {
  if (loading) {
    loading.style.display = 'flex';
    if (textarea) textarea.disabled = true;
  }
}

function hideLoading() {
  if (loading) {
    loading.style.display = 'none';
    if (textarea) textarea.disabled = false;
  }
}

function scrollToBottom() {
  if (chatBody) chatBody.scrollTop = chatBody.scrollHeight;
}

if (textarea) {
  textarea.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      showLoading();
      sendMessage();
    }
  });
}

window.addEventListener('load', function() {
  console.log('scripts.js được tải.');
  const theme = localStorage.getItem('theme');
  if (theme === 'dark') {
    document.body.classList.add('dark-mode');
    const moonIcon = document.querySelector('.theme-toggle i');
    if (moonIcon) {
      moonIcon.classList.remove('fa-moon');
      moonIcon.classList.add('fa-sun');
    }
  }
  hideLoading();
  scrollToBottom();
});