document.addEventListener('DOMContentLoaded', () => {
  // No longer used: GWA Feedback logic

  // Navigation Logic (SIS Style)
  const sidebarLinks = document.querySelectorAll('.sidebar-link');
  const viewSections = document.querySelectorAll('.view-section');
  const viewTitle = document.getElementById('viewTitle');

  const views = {
    overview: 'Dashboard Overview',
    grades: 'My Evaluation',
    social: 'Student Feed',
    handbook: 'Student Handbook'
  };

  // Mobile Menu Logic
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const closeSidebar = document.getElementById('closeSidebar');
  const sidebar = document.getElementById('sidebar');
  const mobileOverlay = document.getElementById('mobileSidebarOverlay');

  function toggleSidebar(show) {
    if (show) {
      sidebar.classList.remove('hidden');
      // Force reflow
      sidebar.offsetHeight;
      sidebar.classList.remove('-translate-x-full');
      sidebar.classList.add('translate-x-0', 'flex');
      mobileOverlay.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
    } else {
      sidebar.classList.add('-translate-x-full');
      sidebar.classList.remove('translate-x-0');
      mobileOverlay.classList.add('hidden');
      document.body.style.overflow = '';
      setTimeout(() => {
        if (window.innerWidth < 768 && sidebar.classList.contains('-translate-x-full')) {
          sidebar.classList.add('hidden');
          sidebar.classList.remove('flex');
        }
      }, 300);
    }
  }

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => toggleSidebar(true));
  }

  if (closeSidebar) {
    closeSidebar.addEventListener('click', () => toggleSidebar(false));
  }

  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', () => toggleSidebar(false));
  }

  // Close sidebar when clicking a link on mobile
  sidebarLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 768) {
        toggleSidebar(false);
      }
      
      const viewId = link.dataset.view;
      
      // Update UI
      sidebarLinks.forEach(l => {
        if (l.classList) {
          l.classList.remove('active', 'bg-blue-600', 'text-white');
          l.classList.add('text-slate-600');
        }
      });
      if (link.classList) {
        link.classList.add('active', 'bg-blue-600', 'text-white');
        link.classList.remove('text-slate-600');
      }

      viewSections.forEach(s => {
        if (s.classList) s.classList.add('hidden');
      });
      const targetView = document.getElementById(`view-${viewId}`);
      if (targetView && targetView.classList) targetView.classList.remove('hidden');
      
      if (viewTitle) viewTitle.textContent = views[viewId];

      // Special init for views
      if (viewId === 'overview') initGwaChart();
      if (viewId === 'social') refreshPosts();
      if (viewId === 'handbook') {
        // Scroll to top when opening handbook
        const main = document.querySelector('main');
        if (main) main.scrollTop = 0;
      }
    });
  });

  // GWA Chart Logic
  let gwaChart;
  async function initGwaChart() {
    const canvas = document.getElementById('gwaChart');
    if (!canvas) return;

    const res = await fetch(`/api/analytics/user-timeline?user_id=${window.userId}`);
    if (!res.ok) return;
    const data = await res.json();

    const ctx = canvas.getContext('2d');
    const labels = data.timeline.map(item => new Date(item.timestamp).toLocaleDateString());
    const values = data.timeline.map(item => item.gwa);

    if (gwaChart) gwaChart.destroy();

    gwaChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'GWA over time',
          data: values,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 6,
          pointHoverRadius: 8,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#fff',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index',
        },
        scales: {
          y: {
            beginAtZero: false,
            reverse: true,
            suggestedMin: 1.0,
            suggestedMax: 5.0,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              font: { weight: 'bold' }
            }
          },
          x: {
            grid: { display: false },
            ticks: {
              font: { weight: 'bold' }
            }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1e293b',
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 12,
            cornerRadius: 12,
            callbacks: {
              label: function(context) {
                return ` GWA: ${context.parsed.y.toFixed(3)}`;
              },
              afterBody: function(context) {
                return '\nClick point to view details';
              }
            }
          }
        },
        onClick: (e, elements) => {
          if (elements.length > 0) {
            const index = elements[0].index;
            const timestamp = data.timeline[index].timestamp;
            // Highlight relevant grade in the list if needed
            console.log('Clicked point at', timestamp);
          }
        }
      }
    });
  }

  // Initial UI Setup
  const gwaEl = document.getElementById('gwa');
  const overviewGwaSpan = document.getElementById('overview-gwa');

  if (gwaEl || overviewGwaSpan) {
    initGwaChart();
    refreshPosts();
  }

  // Post elements
  const postBtn = document.getElementById('postBtn');
  const refreshFeedBtn = document.getElementById('refreshFeed');
  const postContent = document.getElementById('postContent');
  const postsDiv = document.getElementById('posts');

  let postsPage = 1;
  let loadingPosts = false;
  let allPostsLoaded = false;

  async function refreshPosts(force = false) {
    if (!postsDiv) return;
    if (force) {
      postsPage = 1;
      allPostsLoaded = false;
      postsDiv.innerHTML = '';
    }
    
    if (loadingPosts || allPostsLoaded) return;
    loadingPosts = true;

    // Show skeleton loader for first page
    if (postsPage === 1) {
      postsDiv.innerHTML = `
        <div class="skeleton-loader space-y-6">
          <div class="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm animate-pulse">
            <div class="flex items-center gap-3 mb-4"><div class="w-10 h-10 bg-slate-100 rounded-xl"></div><div class="space-y-2"><div class="h-3 bg-slate-100 rounded w-24"></div><div class="h-2 bg-slate-100 rounded w-16"></div></div></div>
            <div class="h-4 bg-slate-50 rounded w-full mb-2"></div><div class="h-4 bg-slate-50 rounded w-3/4"></div>
          </div>
        </div>`;
    }

    try {
      const res = await fetch(`/api/posts?page=${postsPage}&limit=10`);
      if (!res.ok) throw new Error('Failed to fetch posts');
      const data = await res.json();
      
      if (postsPage === 1) postsDiv.innerHTML = '';
      
      if (data.length < 10) {
        allPostsLoaded = true;
      }

      if (data.length === 0 && postsPage === 1) {
        postsDiv.innerHTML = '<div class="text-center p-12 text-slate-400 font-medium italic">No posts yet. Be the first to share!</div>';
      } else {
        data.forEach(p => postsDiv.appendChild(renderPost(p)));
        postsPage++;
      }
      
      // Add a small end of feed indicator
      if (allPostsLoaded && postsDiv.children.length > 0) {
        const endMsg = document.createElement('div');
        endMsg.className = 'text-center p-8 text-slate-400 text-xs font-bold uppercase tracking-widest';
        endMsg.textContent = 'You have reached the end of the feed';
        postsDiv.appendChild(endMsg);
      }

    } catch (err) {
      console.error(err);
      if (postsPage === 1) {
        postsDiv.innerHTML = '<div class="text-center p-8 text-slate-400 font-medium">Failed to load feed. Please try again.</div>';
      }
    } finally {
      loadingPosts = false;
    }
  }

  // Infinite Scroll for Social Feed
  const mainContent = document.querySelector('main');
  if (mainContent) {
    mainContent.addEventListener('scroll', () => {
      const viewSocial = document.getElementById('view-social');
      if (viewSocial && !viewSocial.classList.contains('hidden')) {
        const { scrollTop, scrollHeight, clientHeight } = mainContent;
        if (scrollTop + clientHeight >= scrollHeight - 100) {
          refreshPosts();
        }
      }
    });
  }

  if (refreshFeedBtn) {
    refreshFeedBtn.addEventListener('click', () => {
      refreshFeedBtn.classList.add('animate-spin');
      refreshPosts(true).finally(() => {
        setTimeout(() => refreshFeedBtn.classList.remove('animate-spin'), 500);
      });
    });
  }

  function renderPost(p) {
    const article = document.createElement('article');
    // Check if it's a special achievement post
    const isAchievement = p.content.includes('🎉 ACHIEVEMENT:') || p.content.includes('academic milestone');
    
    article.className = `p-6 rounded-3xl border shadow-sm space-y-4 transition-all ${
      isAchievement 
        ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-100 ring-1 ring-blue-200' 
        : 'bg-white border-slate-200'
    }`;
    article.dataset.id = p.id;

    const reactionTypes = ['like', 'love', 'wow'];
    const reactionButtons = reactionTypes.map(t => {
      const count = p.reactions && p.reactions[t] ? p.reactions[t] : 0;
      const emoji = t === 'like' ? '👍' : t === 'love' ? '❤️' : '😮';
      return `<button class="react px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-xl text-sm font-medium transition-all" data-type="${t}">${emoji} <span class="count">${count}</span></button>`;
    }).join(' ');

    article.innerHTML = `
      <div class="flex justify-between items-start">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-blue-500/20">${(p.author || '?').charAt(0)}</div>
          <div>
            <div class="font-bold text-black text-sm">${p.author}</div>
            <div class="text-[10px] text-gray-400 font-medium uppercase tracking-wider">${new Date(p.timestamp).toLocaleString()}</div>
          </div>
        </div>
      </div>
      <p class="text-gray-700 leading-relaxed text-base">${escapeHtml(p.content)}</p>
      <div class="pt-4 border-t border-black/5 flex flex-wrap gap-2">
        ${reactionButtons}
        <button class="commentToggle px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-xl text-sm font-medium transition-all text-gray-500 ml-auto">💬 ${p.comments.length} Comments</button>
      </div>
      <div class="comments hidden pt-4 space-y-4">
        <div class="commentList space-y-2">
          ${p.comments.map(c => `<div class="bg-gray-50 p-3 rounded-xl text-sm"><strong class="text-blue-600">${escapeHtml(c.user)}</strong>: <span class="text-gray-600">${escapeHtml(c.content)}</span></div>`).join('')}
        </div>
        <div class="flex gap-2">
          <input class="commentBox flex-1 px-4 py-2 bg-gray-50 border border-gray-100 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500" placeholder="Write a comment...">
          <button class="commentBtn px-4 py-2 bg-blue-600 text-white font-bold rounded-xl text-sm hover:bg-blue-700 transition-colors">Post</button>
        </div>
      </div>
    `;

    article.querySelectorAll('.react').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = article.dataset.id; const type = btn.dataset.type;
        const res = await fetch(`/api/posts/${id}/react`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type }) });
        if (!res.ok) return;
        const json = await res.json();
        article.querySelectorAll('.react').forEach(b => {
          const t = b.dataset.type; const c = json.reactions && json.reactions[t] ? json.reactions[t] : 0;
          const countSpan = b.querySelector('.count');
          if (countSpan) countSpan.innerText = c;
        });
      });
    });

    const toggle = article.querySelector('.commentToggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const c = article.querySelector('.comments');
        if (c) c.classList.toggle('hidden');
      });
    }

    const cBtn = article.querySelector('.commentBtn');
    if (cBtn) {
      cBtn.addEventListener('click', async () => {
        const id = article.dataset.id; const box = article.querySelector('.commentBox'); const content = (box ? box.value : '').trim();
        if (!content) return;
        const res = await fetch(`/api/posts/${id}/comments`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content }) });
        if (res.ok) {
      const json = await res.json();
      const list = article.querySelector('.commentList');
      if (list) list.insertAdjacentHTML('beforeend', `<div class="bg-gray-50 p-3 rounded-xl text-sm animate-in slide-in-from-bottom-2 duration-300"><strong class="text-blue-600">${escapeHtml(json.user)}</strong>: <span class="text-gray-600">${escapeHtml(json.content)}</span></div>`);
      if (box) box.value = '';
    } else {
      console.error('Comment failed');
    }
      });
    }

    return article;
  }

  if (postBtn) {
    postBtn.addEventListener('click', async () => {
      const content = postContent.value.trim(); if (!content) return;
      postBtn.disabled = true;
      postBtn.textContent = 'Sharing...';
      
      const res = await fetch('/api/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content }) });
      if (res.ok) { 
        postContent.value = ''; 
        await refreshPosts(true); 
      }
      else { alert('Post failed'); }
      
      postBtn.disabled = false;
      postBtn.textContent = 'Share Post';
    });
  }

  // Grades Logic
  const addGrade = document.getElementById('addGrade');
  const subjectInp = document.getElementById('subject');
  const unitsInp = document.getElementById('units');
  const gradeInp = document.getElementById('grade');
  const gradeList = document.getElementById('gradeList');
  const gwaSpan = document.getElementById('gwa');

  const toggleGrades = document.getElementById('toggleGrades');
  const gradesContent = document.getElementById('gradesContent');
  const chevronIcon = document.getElementById('chevronIcon');

  if (toggleGrades && gradesContent && chevronIcon) {
    toggleGrades.onclick = () => {
      const isHidden = gradesContent.classList.toggle('hidden');
      chevronIcon.style.transform = isHidden ? 'rotate(-90deg)' : 'rotate(0deg)';
    };
  }

  if (addGrade) {
    addGrade.addEventListener('click', async () => {
      const subject = subjectInp.value.trim();
      const units = unitsInp.value;
      const grade = gradeInp.value;
      const year = document.getElementById('year').value;
      const semester = document.getElementById('semester').value;

      if (!subject || !grade) return alert('Enter subject and grade');
      const res = await fetch('/api/grades', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject, units, grade, year, semester })
      });

      if (res.ok) {
        const json = await res.json();
        if (gradeList) {
          const li = document.createElement('li');
          li.dataset.id = json.id;
          li.className = 'py-4 flex justify-between items-center group animate-in zoom-in-95 duration-300';
          li.innerHTML = `
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 bg-slate-50 rounded-xl flex flex-col items-center justify-center border border-slate-100">
                <span class="text-[8px] font-black text-slate-400 leading-none">YR</span>
                <span class="text-xs font-black text-slate-800">${json.year}</span>
              </div>
              <div>
                <div class="font-bold text-slate-800">${escapeHtml(json.subject)}</div>
                <div class="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">SEM ${json.semester} • ${json.units} UNITS</div>
              </div>
            </div>
            <div class="flex items-center gap-6">
              <div class="text-right">
                <div class="text-lg font-black ${json.grade > 3.0 ? 'text-red-500' : 'text-blue-600'} tracking-tighter">${json.grade}</div>
                <div class="text-[8px] font-black uppercase text-slate-300">Mark</div>
              </div>
              <button class="editGrade p-2 text-slate-200 hover:text-slate-900 transition-colors opacity-0 group-hover:opacity-100">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
              </button>
            </div>
          `;
          gradeList.prepend(li);
        }
        if (gwaSpan) gwaSpan.textContent = json.gwa || '—';
        if (json.gwa) {
          initGwaChart();
        }
        // Refresh honors status (reload or fetch)
        location.reload(); 

        if (subjectInp) subjectInp.value = '';
        if (gradeInp) gradeInp.value = '';
      } else { alert('Could not add grade'); }
    });
  }

  // Theme Toggle Logic
  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;

  // Load saved theme
  if (localStorage.getItem('high-contrast') === 'true') {
    body.classList.add('high-contrast');
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const isHighContrast = body.classList.toggle('high-contrast');
      localStorage.setItem('high-contrast', isHighContrast);
      
      // Accessibility announcement
      const announcement = isHighContrast ? 'High contrast mode enabled' : 'High contrast mode disabled';
      const liveRegion = document.getElementById('a11y-announcer') || createAnnouncer();
      liveRegion.textContent = announcement;
    });
  }

  function createAnnouncer() {
    const announcer = document.createElement('div');
    announcer.id = 'a11y-announcer';
    announcer.setAttribute('aria-live', 'polite');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
    return announcer;
  }

  // Export CSV Logic
  const exportCsvBtn = document.getElementById('exportCsv');
  
  // Admin Elements
  const adminBtn = document.getElementById('adminBtn');
  const adminModal = document.getElementById('adminModal');
  const adminError = document.getElementById('adminError');
  const adminCancel = document.getElementById('adminCancel');
  const adminBackdrop = document.getElementById('adminBackdrop');
  const adminSubmit = document.getElementById('adminSubmit');

  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      const grades = [];
      const items = document.querySelectorAll('#gradeList li');
      items.forEach(li => {
        const subject = li.querySelector('.font-bold.text-slate-800').textContent;
        const info = li.querySelector('.text-[10px].text-slate-400').textContent;
        const unitsMatch = info.match(/(\d+\.?\d*)\s*UNITS/i);
        const units = unitsMatch ? unitsMatch[1] : '3.0';
        const grade = li.querySelector('.font-black.tracking-tighter').textContent;
        grades.push({ subject, units, grade });
      });

      if (grades.length === 0) return alert('No grades to export');

      let csv = 'Subject,Units,Grade\n';
      grades.forEach(g => {
        csv += `"${g.subject.replace(/"/g, '""')}",${g.units},${g.grade}\n`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `gwa_report_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  }

  // Focus Management for Admin Modal
  let lastFocusedElement;

  if (adminBtn && adminModal && adminError) {
    adminBtn.onclick = () => {
      lastFocusedElement = document.activeElement;
      adminModal.classList.remove('hidden');
      adminError.classList.add('hidden');
      const sidInp = document.getElementById('admin_school_id');
      if (sidInp) sidInp.focus();
    };
  }

  const hideAdminModal = () => { 
    if (adminModal) {
      adminModal.classList.add('hidden');
      if (lastFocusedElement) lastFocusedElement.focus();
    }
  };

  if (adminCancel) adminCancel.onclick = hideAdminModal;
  if (adminBackdrop) adminBackdrop.onclick = hideAdminModal;

  if (adminSubmit && adminError) {
    adminSubmit.onclick = async () => {
      const sidEl = document.getElementById('admin_school_id');
      const pwdEl = document.getElementById('admin_password');
      const sid = sidEl ? sidEl.value.trim() : '';
      const pwd = pwdEl ? pwdEl.value : '';
      adminError.classList.add('hidden');
      if (!sid || !pwd) {
        adminError.textContent = 'Enter school id and password';
        adminError.classList.remove('hidden');
        return;
      }
      const res = await fetch('/api/login', { 
        method: 'POST', 
        headers: { 
          'Content-Type': 'application/x-www-form-urlencoded'
        }, 
        body: `school_id=${encodeURIComponent(sid)}&password=${encodeURIComponent(pwd)}` 
      });
      let j;
      try {
        j = await res.json();
      } catch (e) {
        adminError.textContent = 'Server error: invalid response';
        adminError.classList.remove('hidden');
        console.error('Login error:', e);
        return;
      }
      if (res.ok && j.success && j.redirect) { 
        window.location.href = j.redirect; 
      } else {
        adminError.textContent = j.error || 'Authentication failed';
        adminError.classList.remove('hidden');
      }
    };
  }

  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !adminModal.classList.contains('hidden')) {
      hideAdminModal();
    }
    
    // Trap focus in modal
    if (e.key === 'Tab' && !adminModal.classList.contains('hidden')) {
      const focusableElements = adminModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  });

  function escapeHtml(s) { return (s + '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": "&#39;" }[c])); }

  refreshPosts();
});
