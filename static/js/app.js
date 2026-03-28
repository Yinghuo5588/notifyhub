/**
 * NotifyHub 全局 JavaScript
 */

/**
 * 显示 Toast 通知
 * @param {string} message - 消息内容
 * @param {string} type - 类型: success / error / warning / info
 * @param {number} duration - 显示时长(毫秒)
 */
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-indigo-500',
    };

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️',
    };

    const toast = document.createElement('div');
    toast.className = `${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 min-w-64 max-w-sm text-sm toast-enter`;
    toast.innerHTML = `
        <span>${icons[type] || icons.info}</span>
        <span class="flex-1">${message}</span>
        <button onclick="dismissToast(this.parentElement)" class="text-white/80 hover:text-white ml-2 text-lg leading-none">&times;</button>
    `;

    container.appendChild(toast);

    // 自动消失
    setTimeout(() => dismissToast(toast), duration);
}

/**
 * 关闭 Toast
 */
function dismissToast(el) {
    if (!el || !el.parentElement) return;
    el.classList.remove('toast-enter');
    el.classList.add('toast-exit');
    setTimeout(() => {
        if (el.parentElement) el.remove();
    }, 300);
}

/**
 * 确认删除弹窗
 */
function confirmDelete(msg) {
    return confirm(msg || '确定要删除吗？此操作不可撤销。');
}