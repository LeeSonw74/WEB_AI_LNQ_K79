function toggleMenu() {
  const menu = document.querySelector('.navbar-menu');
  menu.classList.toggle('active');
}

function clearHistory() {
  if (confirm('Bạn có chắc muốn xóa lịch sử trò chuyện không?')) {
    $.post('/clear_history', function(response) {
      if (response.status === 'success') {
        location.reload();
      } else {
        alert(response.message || 'Lỗi khi xóa lịch sử trò chuyện.');
      }
    }).fail(function() {
      alert('Lỗi khi gửi yêu cầu xóa lịch sử. Vui lòng thử lại.');
    });
  }
}