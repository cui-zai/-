// 全局工具函数
class MusicRecApp {
    constructor() {
        this.baseUrl = '';
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    // 显示Toast消息
    showToast(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast fade show bg-${type} text-white`;
        toast.setAttribute('role', 'alert');
        toast.style.minWidth = '250px';
        
        toast.innerHTML = `
            <div class="toast-body d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close btn-close-white" onclick="document.getElementById('${toastId}').remove()"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // 自动移除
        setTimeout(() => {
            if (document.getElementById(toastId)) {
                document.getElementById(toastId).remove();
            }
        }, duration);
        
        return toastId;
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
        return container;
    }

    // AJAX请求封装
    async fetchJSON(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };

        if (this.csrfToken && !options.method || options.method === 'GET') {
            defaultOptions.headers['X-CSRF-Token'] = this.csrfToken;
        }

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ message: '请求失败' }));
                throw new Error(error.message || `HTTP错误: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('请求失败:', error);
            this.showToast(error.message || '网络请求失败', 'danger');
            throw error;
        }
    }

    // 格式化时间
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // 格式化日期
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return '刚刚';
        if (diffMins < 60) return `${diffMins}分钟前`;
        if (diffHours < 24) return `${diffHours}小时前`;
        if (diffDays < 7) return `${diffDays}天前`;
        
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // 生成星级评分HTML
    renderStars(rating, maxStars = 5) {
        let stars = '';
        const fullStar = '<i class="fas fa-star text-warning"></i>';
        const halfStar = '<i class="fas fa-star-half-alt text-warning"></i>';
        const emptyStar = '<i class="far fa-star text-warning"></i>';
        
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        
        for (let i = 0; i < fullStars; i++) {
            stars += fullStar;
        }
        
        if (hasHalfStar) {
            stars += halfStar;
        }
        
        const remainingStars = maxStars - fullStars - (hasHalfStar ? 1 : 0);
        for (let i = 0; i < remainingStars; i++) {
            stars += emptyStar;
        }
        
        return stars;
    }

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// 初始化应用实例
window.musicRecApp = new MusicRecApp();

// 系统检查功能
async function checkSystemStatus() {
    const dbStatus = document.getElementById('db-status');
    const flaskStatus = document.getElementById('flask-status');
    const recStatus = document.getElementById('rec-status');
    
    try {
        // 检查健康状态
        const health = await musicRecApp.fetchJSON('/api/health');
        if (health.status === 'healthy') {
            flaskStatus.className = 'badge bg-success';
            flaskStatus.textContent = '运行中';
            musicRecApp.showToast('Flask服务运行正常', 'success');
        }
        
        // 检查数据库
        const dbResult = await musicRecApp.fetchJSON('/api/test_db');
        if (dbResult.status === 'success') {
            dbStatus.className = 'badge bg-success';
            dbStatus.textContent = '已连接';
            musicRecApp.showToast('数据库连接正常', 'success');
        }
    } catch (error) {
        musicRecApp.showToast('系统检查失败: ' + error.message, 'danger');
    }
}

// 音乐播放器模拟
class MusicPlayer {
    constructor() {
        this.currentSong = null;
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        this.volume = 0.8;
        this.playlist = [];
        this.currentIndex = -1;
        
        this.initializePlayer();
    }
    
    initializePlayer() {
        // 创建播放器DOM元素
        if (!document.getElementById('music-player')) {
            const playerHTML = `
                <div id="music-player" class="fixed-bottom bg-dark text-white p-3" style="display: none;">
                    <div class="container">
                        <div class="row align-items-center">
                            <div class="col-md-3">
                                <div class="d-flex align-items-center">
                                    <img id="player-album-art" src="/static/images/default-song.jpg" 
                                         class="rounded" width="50" height="50">
                                    <div class="ms-3">
                                        <div id="player-title" class="fw-bold">未选择歌曲</div>
                                        <div id="player-artist" class="text-muted small">未知艺术家</div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="d-flex align-items-center justify-content-center">
                                    <button class="btn btn-link text-white" onclick="window.player.previous()">
                                        <i class="fas fa-step-backward"></i>
                                    </button>
                                    <button id="play-btn" class="btn btn-light mx-3 rounded-circle" 
                                            onclick="window.player.togglePlay()" style="width: 40px; height: 40px;">
                                        <i class="fas fa-play"></i>
                                    </button>
                                    <button class="btn btn-link text-white" onclick="window.player.next()">
                                        <i class="fas fa-step-forward"></i>
                                    </button>
                                </div>
                                <div class="mt-2">
                                    <div class="d-flex justify-content-between small">
                                        <span id="player-current-time">0:00</span>
                                        <span id="player-duration">0:00</span>
                                    </div>
                                    <input type="range" id="player-progress" class="form-range" min="0" max="100" value="0">
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="d-flex align-items-center justify-content-end">
                                    <i class="fas fa-volume-up me-2"></i>
                                    <input type="range" id="player-volume" class="form-range w-50" 
                                           min="0" max="100" value="80">
                                    <button class="btn btn-link text-white ms-3" onclick="window.player.close()">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', playerHTML);
        }
        
        // 绑定事件
        document.getElementById('player-progress').addEventListener('input', (e) => {
            this.seek(e.target.value);
        });
        
        document.getElementById('player-volume').addEventListener('input', (e) => {
            this.setVolume(e.target.value / 100);
        });
        
        // 模拟播放进度
        setInterval(() => {
            if (this.isPlaying && this.currentSong) {
                this.currentTime++;
                this.updateProgress();
            }
        }, 1000);
    }
    
    play(song) {
        if (!song) return;
        
        this.currentSong = song;
        this.currentTime = 0;
        this.duration = song.duration || 180;
        this.isPlaying = true;
        
        // 更新UI
        document.getElementById('music-player').style.display = 'block';
        document.getElementById('player-title').textContent = song.title;
        document.getElementById('player-artist').textContent = song.artist;
        document.getElementById('play-btn').innerHTML = '<i class="fas fa-pause"></i>';
        document.getElementById('player-duration').textContent = musicRecApp.formatDuration(this.duration);
        
        this.updateProgress();
        
        // 记录播放历史
        this.recordPlayHistory(song.id);
        
        musicRecApp.showToast(`正在播放: ${song.title}`, 'info');
    }
    
    togglePlay() {
        if (!this.currentSong) return;
        
        this.isPlaying = !this.isPlaying;
        const playBtn = document.getElementById('play-btn');
        
        if (this.isPlaying) {
            playBtn.innerHTML = '<i class="fas fa-pause"></i>';
            musicRecApp.showToast('继续播放', 'info');
        } else {
            playBtn.innerHTML = '<i class="fas fa-play"></i>';
            musicRecApp.showToast('已暂停', 'warning');
        }
    }
    
    stop() {
        this.isPlaying = false;
        this.currentTime = 0;
        document.getElementById('play-btn').innerHTML = '<i class="fas fa-play"></i>';
        this.updateProgress();
    }
    
    next() {
        if (this.playlist.length > 0) {
            this.currentIndex = (this.currentIndex + 1) % this.playlist.length;
            this.play(this.playlist[this.currentIndex]);
        }
    }
    
    previous() {
        if (this.playlist.length > 0) {
            this.currentIndex = (this.currentIndex - 1 + this.playlist.length) % this.playlist.length;
            this.play(this.playlist[this.currentIndex]);
        }
    }
    
    seek(percent) {
        if (!this.currentSong) return;
        this.currentTime = (percent / 100) * this.duration;
        this.updateProgress();
    }
    
    setVolume(volume) {
        this.volume = volume;
    }
    
    updateProgress() {
        const percent = (this.currentTime / this.duration) * 100 || 0;
        document.getElementById('player-progress').value = percent;
        document.getElementById('player-current-time').textContent = 
            musicRecApp.formatDuration(this.currentTime);
    }
    
    async recordPlayHistory(songId) {
        try {
            await musicRecApp.fetchJSON(`/api/songs/${songId}/play`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('记录播放历史失败:', error);
        }
    }
    
    close() {
        document.getElementById('music-player').style.display = 'none';
        this.stop();
    }
    
    addToPlaylist(song) {
        this.playlist.push(song);
        musicRecApp.showToast(`已添加到播放列表: ${song.title}`, 'success');
    }
    
    clearPlaylist() {
        this.playlist = [];
        this.currentIndex = -1;
        musicRecApp.showToast('播放列表已清空', 'info');
    }
}

// 初始化播放器
window.player = new MusicPlayer();

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 绑定全局事件
    bindGlobalEvents();
    
    // 检查系统状态
    setTimeout(checkSystemStatus, 1000);
});

// 绑定全局事件
function bindGlobalEvents() {
    // 音乐卡片点击事件
    document.addEventListener('click', function(e) {
        const playBtn = e.target.closest('.play-song-btn');
        if (playBtn) {
            const songId = playBtn.dataset.songId;
            const songTitle = playBtn.dataset.songTitle;
            const songArtist = playBtn.dataset.songArtist;
            
            window.player.play({
                id: parseInt(songId),
                title: songTitle,
                artist: songArtist
            });
        }
        
        // 添加到播放列表
        const addBtn = e.target.closest('.add-to-playlist-btn');
        if (addBtn) {
            const songId = addBtn.dataset.songId;
            const songTitle = addBtn.dataset.songTitle;
            const songArtist = addBtn.dataset.songArtist;
            
            window.player.addToPlaylist({
                id: parseInt(songId),
                title: songTitle,
                artist: songArtist
            });
        }
        
        // 评分
        const rateBtn = e.target.closest('.rate-song-btn');
        if (rateBtn) {
            const songId = rateBtn.dataset.songId;
            const rating = rateBtn.dataset.rating;
            
            rateSong(songId, rating);
        }
    });
    
    // 搜索功能
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        const debouncedSearch = musicRecApp.debounce(async function() {
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                await performSearch(query);
            }
        }, 300);
        
        searchInput.addEventListener('input', debouncedSearch);
    }
}

// 搜索函数
async function performSearch(query) {
    try {
        const results = await musicRecApp.fetchJSON(`/api/search?q=${encodeURIComponent(query)}`);
        displaySearchResults(results);
    } catch (error) {
        musicRecApp.showToast('搜索失败: ' + error.message, 'danger');
    }
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="alert alert-info">未找到相关结果</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    results.forEach(song => {
        html += `
            <div class="list-group-item list-group-item-action music-card">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="music-title">${song.title}</div>
                        <div class="music-artist">${song.artist}</div>
                        <div class="mt-1">
                            <span class="music-genre">${song.genre || '未知流派'}</span>
                            <span class="text-muted small">${musicRecApp.formatDuration(song.duration || 0)}</span>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary play-song-btn me-2"
                                data-song-id="${song.id}"
                                data-song-title="${song.title}"
                                data-song-artist="${song.artist}">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-success add-to-playlist-btn"
                                data-song-id="${song.id}"
                                data-song-title="${song.title}"
                                data-song-artist="${song.artist}">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultsContainer.innerHTML = html;
}

// 评分函数
async function rateSong(songId, rating) {
    try {
        const result = await musicRecApp.fetchJSON(`/api/songs/${songId}/rate`, {
            method: 'POST',
            body: JSON.stringify({ rating: parseFloat(rating) })
        });
        
        musicRecApp.showToast('评分成功', 'success');
        
        // 更新UI
        const ratingElement = document.querySelector(`.song-rating[data-song-id="${songId}"]`);
        if (ratingElement) {
            ratingElement.innerHTML = musicRecApp.renderStars(result.new_rating);
        }
    } catch (error) {
        musicRecApp.showToast('评分失败: ' + error.message, 'danger');
    }
}

// 推荐系统交互
async function loadRecommendations(type = 'personalized') {
    const loadingElement = document.getElementById('recommendations-loading');
    const container = document.getElementById('recommendations-container');
    
    if (loadingElement) loadingElement.style.display = 'block';
    if (container) container.innerHTML = '';
    
    try {
        const recommendations = await musicRecApp.fetchJSON(`/api/recommendations/${type}`);
        displayRecommendations(recommendations, type);
    } catch (error) {
        musicRecApp.showToast('加载推荐失败: ' + error.message, 'danger');
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

function displayRecommendations(recommendations, type) {
    const container = document.getElementById('recommendations-container');
    if (!container) return;
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<div class="alert alert-info">暂无推荐内容</div>';
        return;
    }
    
    let html = '<div class="row">';
    recommendations.forEach((song, index) => {
        html += `
            <div class="col-md-4 mb-3">
                <div class="card music-card h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-title music-title">${index + 1}. ${song.title}</h6>
                                <p class="card-text music-artist">${song.artist}</p>
                            </div>
                            <span class="badge bg-primary">${song.score ? song.score.toFixed(1) : '推荐'}</span>
                        </div>
                        <div class="mt-2">
                            <span class="music-genre">${song.genre || '未知流派'}</span>
                            <span class="text-muted small ms-2">
                                <i class="fas fa-clock"></i> ${musicRecApp.formatDuration(song.duration || 0)}
                            </span>
                        </div>
                        <div class="mt-3 d-flex justify-content-between">
                            <button class="btn btn-sm btn-outline-primary play-song-btn"
                                    data-song-id="${song.id}"
                                    data-song-title="${song.title}"
                                    data-song-artist="${song.artist}">
                                <i class="fas fa-play me-1"></i>播放
                            </button>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-secondary rate-song-btn" 
                                        data-song-id="${song.id}" data-rating="3">
                                    <i class="fas fa-star"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-secondary rate-song-btn"
                                        data-song-id="${song.id}" data-rating="4">
                                    <i class="fas fa-star"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-secondary rate-song-btn"
                                        data-song-id="${song.id}" data-rating="5">
                                    <i class="fas fa-star"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}