// 主要 JavaScript 功能

// 显示通知消息
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 5秒后自动隐藏
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// 文件大小格式化
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 验证文件类型
function validateFileType(file) {
    const allowedTypes = [
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ];
    return allowedTypes.includes(file.type) || 
           file.name.toLowerCase().endsWith('.ppt') || 
           file.name.toLowerCase().endsWith('.pptx');
}

// 验证文件大小（50MB 限制）
function validateFileSize(file) {
    const maxSize = 50 * 1024 * 1024; // 50MB
    return file.size <= maxSize;
}

// 文件上传验证
function validateFile(file) {
    if (!validateFileType(file)) {
        showNotification('请选择有效的 PPT 文件（.ppt 或 .pptx）', 'danger');
        return false;
    }
    
    if (!validateFileSize(file)) {
        showNotification('文件大小不能超过 50MB', 'danger');
        return false;
    }
    
    return true;
}

// 文件上传处理
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('pptFile');
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!validateFile(file)) {
                    e.target.value = '';
                    return;
                }
                
                // 显示文件信息
                const fileInfo = document.getElementById('fileInfo');
                if (fileInfo) {
                    fileInfo.innerHTML = `
                        <small class="text-muted">
                            已选择: ${file.name} (${formatFileSize(file.size)})
                        </small>
                    `;
                }
            }
        });
    }
    
    // 拖拽上传功能
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (validateFile(file)) {
                    fileInput.files = files;
                    fileInput.dispatchEvent(new Event('change'));
                }
            }
        });
    }
});

// 页面加载时的动画效果
window.addEventListener('load', function() {
    document.body.classList.add('loaded');
});

// CSRF Token 获取函数
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return null;
} 