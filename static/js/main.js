document.addEventListener('DOMContentLoaded', () => {
  // GWA Feedback Logic
  function updateGwaFeedback(gwa) {
    const feedbackBox = document.getElementById('gwaFeedback');
    const gwaEmoji = document.getElementById('gwaEmoji');
    const gwaLevel = document.getElementById('gwaLevel');
    const gwaQuote = document.getElementById('gwaQuote');
    const gVal = parseFloat(gwa);

    if (!feedbackBox || isNaN(gVal)) return;

    feedbackBox.classList.remove('hidden');
    let config = {};

    if (gVal >= 1.0 && gVal <= 1.5) {
      config = {
        emoji: '🏆', level: 'Excellent',
        quotes: ['“Excellence is not an act, it’s a habit.”', '“Your hard work truly paid off—keep aiming high.”'],
        theme: 'bg-yellow-50 border-yellow-100 text-yellow-700'
      };
    } else if (gVal > 1.5 && gVal <= 1.75) {
      config = {
        emoji: '🥇', level: 'Very Good',
        quotes: ['“Great job! You’re closer to excellence than you think.”', '“Consistency is turning your effort into success.”'],
        theme: 'bg-blue-50 border-blue-100 text-blue-700'
      };
    } else if (gVal > 1.75 && gVal <= 2.25) {
      config = {
        emoji: '🥈', level: 'Good',
        quotes: ['“Good work—keep pushing, you’re on the right path.”', '“This is progress. Don’t stop improving."'],
        theme: 'bg-indigo-50 border-indigo-100 text-indigo-700'
      };
    } else if (gVal > 2.25 && gVal <= 2.75) {
      config = {
        emoji: '🥉', level: 'Satisfactory',
        quotes: ['“You passed, and that means you’re moving forward.”', '“There’s room to grow—and you can do better next time.”'],
        theme: 'bg-green-50 border-green-100 text-green-700'
      };
    } else if (gVal > 2.75 && gVal <= 3.0) {
      config = {
        emoji: '⚠️', level: 'Passing',
        quotes: ['“Passing is still winning—never give up.”', '“This grade does not define your potential.”'],
        theme: 'bg-orange-50 border-orange-100 text-orange-700'
      };
    } else if (gVal >= 5.0) {
      config = {
        emoji: '❌', level: 'Failing',
        quotes: ['“Failure is not the opposite of success; it’s part of it.”', '“Stand up, learn from it, and try again stronger.”'],
        theme: 'bg-red-50 border-red-100 text-red-700'
      };
    } else {
      feedbackBox.classList.add('hidden');
      return;
    }

    feedbackBox.className = `p-5 rounded-2xl border transition-all duration-500 animate-in fade-in slide-in-from-top-2 ${config.theme}`;
    gwaEmoji.textContent = config.emoji;
    gwaLevel.textContent = `${config.level} (${gVal.toFixed(3)})`;
    gwaQuote.innerHTML = config.quotes.join('<br>');
  }

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
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: false,
            reverse: true, // Philippine GWA: 1.0 is best, 5.0 is failing
            suggestedMin: 1.0,
            suggestedMax: 5.0
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // Initial GWA Call
  const gwaEl = document.getElementById('gwa');
  if (gwaEl) {
      const initialGwa = gwaEl.textContent;
      if (initialGwa && initialGwa !== '—') updateGwaFeedback(initialGwa);
    }
    initGwaChart();

    // Post elements
  const postBtn = document.getElementById('postBtn');
  const postContent = document.getElementById('postContent');
  const postsDiv = document.getElementById('posts');

  async function refreshPosts() {
    if (!postsDiv) return;
    const res = await fetch('/api/posts');
    const data = await res.json();
    postsDiv.innerHTML = '';
    data.forEach(p => postsDiv.appendChild(renderPost(p)));
  }

  function renderPost(p) {
    const article = document.createElement('article');
    article.className = 'bg-white p-6 rounded-2xl border border-black/5 shadow-sm space-y-4';
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
        const json = await res.json();
        const list = article.querySelector('.commentList');
        if (list) list.insertAdjacentHTML('beforeend', `<div class="bg-gray-50 p-3 rounded-xl text-sm animate-in slide-in-from-bottom-2 duration-300"><strong class="text-blue-600">${escapeHtml(json.user)}</strong>: <span class="text-gray-600">${escapeHtml(json.content)}</span></div>`);
        if (box) box.value = '';
      });
    }

    return article;
  }

  if (postBtn) {
    postBtn.addEventListener('click', async () => {
      const content = postContent.value.trim(); if (!content) return;
      const res = await fetch('/api/posts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content }) });
      if (res.ok) { postContent.value = ''; refreshPosts(); }
      else { alert('Post failed'); }
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
      const subject = subjectInp.value.trim(); const units = unitsInp.value; const grade = gradeInp.value;
      if (!subject || !grade) return alert('Enter subject and grade');
      const res = await fetch('/api/grades', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ subject, units, grade }) });
      if (res.ok) {
        const json = await res.json();
        if (gradeList) {
          const li = document.createElement('li');
          li.dataset.id = json.id;
          li.className = 'flex justify-between items-center bg-gray-50/50 p-3 rounded-xl border border-black/5 animate-in zoom-in-95 duration-300';
          li.innerHTML = `
              <div>
                <div class="font-bold text-sm">${escapeHtml(json.subject)}</div>
                <div class="text-xs text-gray-400">${json.units} units</div>
              </div>
              <div class="flex items-center gap-3">
                <span class="font-bold text-blue-600">${json.grade}</span>
                <button class="editGrade text-gray-300 hover:text-black transition-colors">✎</button>
              </div>
            `;
          gradeList.appendChild(li);
        }
        if (gwaSpan) gwaSpan.textContent = json.gwa || '—';
        if (json.gwa) {
          updateGwaFeedback(json.gwa);
          initGwaChart();
        }
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
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      const grades = [];
      const items = document.querySelectorAll('#gradeList li');
      items.forEach(li => {
        const subject = li.querySelector('.font-bold.text-sm').textContent;
        const units = li.querySelector('.text-xs.text-gray-400').textContent.replace(' units', '');
        const grade = li.querySelector('.font-bold.text-blue-600').textContent;
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
      const res = await fetch('/admin-auth', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ school_id: sid, password: pwd }) });
      const j = await res.json();
      if (res.ok && j.redirect) { window.location = j.redirect; }
      else {
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
