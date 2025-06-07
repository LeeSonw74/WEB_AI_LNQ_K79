function toggleMenu() {
  const menu = document.querySelector('.navbar-menu');
  menu.classList.toggle('active');
}

function clearHistory() {
  if (!confirm('Bạn có chắc muốn xóa lịch sử trò chuyện không?')) {
    return;
  }

  const historyContent = document.getElementById('history-content');
  const chatBody = document.getElementById('chat-body');
  const clearBtn = document.querySelector('.clear-history-btn');
  const loading = document.createElement('div');
  loading.className = 'loading';
  loading.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
  historyContent.appendChild(loading);

  $.ajax({
    url: '/clear_history',
    type: 'POST',
    timeout: 5000,
    success: function(response) {
      historyContent.removeChild(loading);
      if (response.status === 'success') {
        // Verify history is cleared
        $.ajax({
          url: '/get_history',
          type: 'GET',
          timeout: 5000,
          success: function(historyResponse) {
            if (historyResponse.status === 'success') {
              historyContent.innerHTML = `<p class="success-message">${response.message || 'Lịch sử trò chuyện đã được xóa thành công!'}</p>`;
              if (chatBody) {
                chatBody.innerHTML = '<div class="loading" id="loading" style="display: none;"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
              }
              if (clearBtn) {
                clearBtn.disabled = true;
              }
              console.log('Lịch sử trò chuyện đã được xóa thành công.');
              checkHistoryEmpty(); // Đảm bảo trạng thái nút được cập nhật
            } else {
              historyContent.innerHTML = `<p class="error-message">Lỗi: ${historyResponse.message || 'Không thể xác minh lịch sử đã xóa.'}</p>`;
              console.error('Lỗi khi xác minh lịch sử:', historyResponse.message);
            }
          },
          error: function(jqXHR, textStatus, errorThrown) {
            historyContent.removeChild(loading);
            let errorMessage = 'Lỗi khi kiểm tra lịch sử. Vui lòng thử lại.';
            if (textStatus === 'timeout') {
              errorMessage = 'Yêu cầu kiểm tra lịch sử mất quá nhiều thời gian.';
            } else if (jqXHR.status) {
              errorMessage = `Lỗi server (${jqXHR.status}): ${errorThrown}`;
            }
            historyContent.innerHTML = `<p class="error-message">${errorMessage}</p>`;
            console.error('Lỗi AJAX khi kiểm tra lịch sử:', textStatus, errorThrown, jqXHR);
          }
        });
      } else {
        historyContent.innerHTML = `<p class="error-message">${response.message || 'Lỗi khi xóa lịch sử trò chuyện.'}</p>`;
        console.error('Lỗi khi xóa lịch sử:', response.message);
      }
    },
    error: function(jqXHR, textStatus, errorThrown) {
      historyContent.removeChild(loading);
      let errorMessage = 'Lỗi khi gửi yêu cầu xóa lịch sử. Vui lòng thử lại.';
      if (textStatus === 'timeout') {
        errorMessage = 'Yêu cầu xóa lịch sử mất quá nhiều thời gian.';
      } else if (jqXHR.status) {
        errorMessage = `Lỗi server (${jqXHR.status}): ${errorThrown}`;
      }
      historyContent.innerHTML = `<p class="error-message">${errorMessage}</p>`;
      console.error('Lỗi AJAX trong clearHistory:', textStatus, errorThrown, jqXHR);
    }
  });
}

function filterHistory() {
  const searchInput = document.getElementById('search-input').value.toLowerCase();
  const dateFilter = document.getElementById('date-filter').value;
  const historyContent = document.getElementById('history-content');
  $.post('/filter_history', { search: searchInput, date: dateFilter }, function(response) {
    if (response.status === 'success') {
      historyContent.innerHTML = '';
      if (response.history.length > 0) {
        response.history.forEach(chat => {
          const wrapper = document.createElement('div');
          wrapper.className = 'message-wrapper';
          wrapper.innerHTML = `
            <div class="message user-message"><span>🗣 ${chat[0]}</span></div>
            <div class="datetime">${chat[2]}</div>
            <div class="message bot-message"><span style="white-space: pre-wrap;">🤖 ${chat[1]}</span></div>
            <div class="datetime">${chat[2]}</div>
            <hr>
          `;
          historyContent.appendChild(wrapper);
        });
      } else {
        historyContent.innerHTML = '<p>Không tìm thấy lịch sử phù hợp.</p>';
      }
      checkHistoryEmpty();
    } else {
      alert('Lỗi khi lọc lịch sử: ' + (response.message || 'Vui lòng thử lại.'));
    }
  }).fail(function() {
    alert('Lỗi kết nối server khi lọc lịch sử.');
  });
}

function checkHistoryEmpty() {
  const historyContent = document.getElementById('history-content');
  const chatBody = document.getElementById('chat-body');
  const clearBtn = document.querySelector('.clear-history-btn');
  const hasHistory = historyContent.querySelector('.message-wrapper') || (chatBody && chatBody.querySelector('.message-wrapper'));
  if (clearBtn) {
    clearBtn.disabled = !hasHistory;
    console.log('Nút xóa lịch sử:', hasHistory ? 'Bật' : 'Tắt');
  }
}

window.addEventListener('load', function() {
  checkHistoryEmpty();
  console.log('history.js được tải.');
});