document.addEventListener('DOMContentLoaded', async () => {
  const studentsTable = document.getElementById('studentsTable');
  const studentDetails = document.getElementById('studentDetails');
  const studentCount = document.getElementById('studentCount');

  // Modal elements
  const studentModal = document.getElementById('studentModal');
  const addStudentBtn = document.getElementById('addStudentBtn');
  const studentCancel = document.getElementById('studentCancel');
  const studentSubmit = document.getElementById('studentSubmit');
  const studentForm = document.getElementById('studentForm');
  const studentBackdrop = document.getElementById('studentBackdrop');
  const studentModalTitle = document.getElementById('studentModalTitle');
  const studentModalError = document.getElementById('studentModalError');

  function createSVG(w, h) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    return svg;
  }

  function clearEl(el) { while (el && el.firstChild) el.removeChild(el.firstChild); }

  function renderBarChart(containerId, labels, values, opts = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    clearEl(container);
    if (!values || values.length === 0) return;
    const width = 420, height = 200, padding = 40;
    const svg = createSVG(width, height);
    const max = Math.max(...values, 0.001);
    const barW = (width - padding * 2) / values.length * 0.7;

    values.forEach((v, i) => {
      const x = padding + i * ((width - padding * 2) / values.length) + ((width - padding * 2) / values.length - barW) / 2;
      const h = (v / max) * (height - padding * 2);
      const y = height - padding - h;

      const rect = document.createElementNS(svg.namespaceURI, 'rect');
      rect.setAttribute('x', x); rect.setAttribute('y', y); rect.setAttribute('width', barW); rect.setAttribute('height', h);
      rect.setAttribute('fill', opts.fill || '#3b82f6'); rect.setAttribute('rx', '4');
      svg.appendChild(rect);

      const text = document.createElementNS(svg.namespaceURI, 'text');
      text.setAttribute('x', x + barW / 2); text.setAttribute('y', height - 15);
      text.setAttribute('text-anchor', 'middle'); text.setAttribute('font-size', '10'); text.setAttribute('fill', '#9ca3af');
      text.textContent = labels[i].slice(0, 8);
      svg.appendChild(text);
    });
    container.appendChild(svg);
  }

  function renderLineChart(containerId, timeline, opts = {}) {
    const container = document.getElementById(containerId); if (!container) return; clearEl(container);
    if (!timeline || timeline.length === 0) { container.innerHTML = '<div class="text-gray-300 italic">No history available</div>'; return; }
    const width = 520, height = 200, padding = 40;
    const svg = createSVG(width, height);
    const values = timeline.map(t => t.gwa);
    const min = Math.min(...values), max = Math.max(...values);
    const range = (max - min) || 1;

    const points = values.map((v, i) => {
      const x = padding + i * ((width - padding * 2) / (values.length - 1 || 1));
      const y = padding + (1 - (v - min) / range) * (height - padding * 2);
      return [x, y];
    });

    const pathD = points.map((p, i) => (i === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`)).join(' ');
    const path = document.createElementNS(svg.namespaceURI, 'path');
    path.setAttribute('d', pathD); path.setAttribute('fill', 'none'); path.setAttribute('stroke', '#3b82f6'); path.setAttribute('stroke-width', '3');
    path.setAttribute('stroke-linecap', 'round');
    svg.appendChild(path);

    points.forEach((p, i) => {
      const c = document.createElementNS(svg.namespaceURI, 'circle');
      c.setAttribute('cx', p[0]); c.setAttribute('cy', p[1]); c.setAttribute('r', 5);
      c.setAttribute('fill', '#fff'); c.setAttribute('stroke', '#3b82f6'); c.setAttribute('stroke-width', 3);
      svg.appendChild(c);
    });
    container.appendChild(svg);
  }

  async function loadStudents() {
    const res = await fetch('/api/admin/students');
    const data = await res.json();
    if (!data) return;

    studentCount.textContent = `${data.length} Student${data.length === 1 ? '' : 's'} Registered`;

    const table = document.createElement('table');
    table.className = 'w-full text-left border-collapse';
    table.innerHTML = `
      <thead class="bg-gray-50/50 text-gray-400 text-xs font-black uppercase tracking-widest">
        <tr>
          <th class="px-6 py-4">Student</th>
          <th class="px-6 py-4 text-center">GPA</th>
          <th class="px-6 py-4 text-center">Status</th>
          <th class="px-6 py-4 text-right">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-black/5"></tbody>
    `;

    const tbody = table.querySelector('tbody');
    data.forEach(u => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-gray-50/30 transition-colors';
      const statusClass = u.failed_count > 0 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600';
      const statusText = u.failed_count > 0 ? `${u.failed_count} Deficient` : 'In Good Standing';

      tr.innerHTML = `
        <td class="px-6 py-4">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center font-bold text-gray-400 text-sm">${u.name.charAt(0)}</div>
            <div>
              <div class="font-bold text-black">${u.name}</div>
              <div class="text-xs text-gray-400 font-medium">${u.school_id} · ${u.department || 'General'}</div>
            </div>
          </div>
        </td>
        <td class="px-6 py-4 text-center">
          <span class="font-black text-blue-600 text-lg">${u.gwa || '—'}</span>
        </td>
        <td class="px-6 py-4 text-center">
          <span class="px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider ${statusClass}">${statusText}</span>
        </td>
        <td class="px-6 py-4 text-right flex justify-end gap-2">
          <button class="editStudent px-3 py-2 bg-gray-100 text-gray-700 text-xs font-bold rounded-lg hover:bg-gray-200 transition-all active:scale-95" data-user='${JSON.stringify(u)}'>Edit</button>
          <button class="viewStudent px-3 py-2 bg-black text-white text-xs font-bold rounded-lg hover:bg-gray-800 transition-all active:scale-95" data-id="${u.id}">Review</button>
          <button class="deleteStudent px-3 py-2 bg-red-50 text-red-600 text-xs font-bold rounded-lg hover:bg-red-100 transition-all active:scale-95" data-id="${u.id}">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    studentsTable.innerHTML = '';
    studentsTable.appendChild(table);

    // Event listeners for dynamic rows
    document.querySelectorAll('.viewStudent').forEach(btn => {
      btn.onclick = () => {
        const id = btn.dataset.id;
        document.getElementById('detailsSection').classList.remove('hidden');
        document.getElementById('detailsSection').scrollIntoView({ behavior: 'smooth' });
        loadStudentDetails(id);
      };
    });

    document.querySelectorAll('.editStudent').forEach(btn => {
      btn.onclick = () => {
        const u = JSON.parse(btn.dataset.user);
        openStudentModal(u);
      };
    });

    document.querySelectorAll('.deleteStudent').forEach(btn => {
      btn.onclick = async () => {
        if (!confirm('Are you sure you want to delete this student and all their data? This cannot be undone.')) return;
        const id = btn.dataset.id;
        const res = await fetch(`/api/admin/student/${id}`, { method: 'DELETE' });
        if (res.ok) {
          loadStudents();
          loadAnalytics();
        } else {
          const json = await res.json();
          alert(json.error || 'Failed to delete student');
        }
      };
    });
  }

  async function loadStudentDetails(id) {
    const res = await fetch(`/api/admin/student/${id}`);
    const json = await res.json();

    document.getElementById('detailsTitle').textContent = json.name;
    document.getElementById('detailsSub').textContent = `${json.school_id} · ${json.course}`;
    document.getElementById('detailsAvatar').textContent = json.name.charAt(0);

    studentDetails.innerHTML = `
      <div class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <div class="p-4 bg-gray-50 rounded-2xl border border-black/5">
            <div class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Current GWA</div>
            <div class="text-3xl font-black text-blue-600">${json.gwa || '—'}</div>
          </div>
          <div class="p-4 bg-gray-50 rounded-2xl border border-black/5">
            <div class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Total Posts</div>
            <div class="text-3xl font-black text-black">${json.posts.length}</div>
          </div>
        </div>
        <div class="space-y-2">
          <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest">Grades Breakdown</h4>
          <div class="space-y-1">
            ${json.grades.map(g => `
              <div class="flex justify-between items-center p-3 bg-white border border-black/5 rounded-xl shadow-sm">
                <span class="font-bold text-sm text-gray-600">${g.subject}</span>
                <span class="font-black text-gray-800">${g.grade}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    const trendRes = await fetch(`/api/analytics/gwa_trends?user_id=${id}`);
    if (trendRes.ok) {
      const tjson = await trendRes.json();
      renderLineChart('studentTrendChart', tjson.timeline);
    }
  }

  // Analytics
  async function loadAnalytics() {
    const deptRes = await fetch('/api/analytics/department_avg');
    const deptJson = await deptRes.json();
    renderBarChart('deptAvgChart', Object.keys(deptJson), Object.values(deptJson).map(v => v || 0));

    const failRes = await fetch('/api/analytics/failure_rates');
    const failJson = await failRes.json();
    const subjs = Object.keys(failJson);
    renderBarChart('failureRateChart', subjs, subjs.map(s => failJson[s].failure_rate || 0), { fill: '#f87171' });
  }

  // Modal handlers
  function openStudentModal(u = null) {
    studentModal.classList.remove('hidden');
    studentModalError.classList.add('hidden');
    studentForm.reset();

    if (u) {
      studentModalTitle.textContent = 'Edit Student';
      document.getElementById('student_id').value = u.id;
      document.getElementById('student_name').value = u.name;
      document.getElementById('student_school_id').value = u.school_id;
      document.getElementById('student_dept').value = u.department || 'COTE';
      document.getElementById('student_course').value = u.course || '';
      document.getElementById('student_password').placeholder = '•••••••• (leave blank to keep current)';
    } else {
      studentModalTitle.textContent = 'Add New Student';
      document.getElementById('student_id').value = '';
      document.getElementById('student_password').placeholder = '••••••••';
    }
  }

  addStudentBtn.onclick = () => openStudentModal();
  studentCancel.onclick = () => studentModal.classList.add('hidden');
  studentBackdrop.onclick = () => studentModal.classList.add('hidden');

  studentSubmit.onclick = async () => {
    const id = document.getElementById('student_id').value;
    const name = document.getElementById('student_name').value;
    const school_id = document.getElementById('student_school_id').value;
    const password = document.getElementById('student_password').value;
    const department = document.getElementById('student_dept').value;
    const course = document.getElementById('student_course').value;

    if (!name || !school_id || (!id && !password)) {
      studentModalError.textContent = 'Please fill in all required fields';
      studentModalError.classList.remove('hidden');
      return;
    }

    const payload = { name, school_id, department, course };
    if (password) payload.password = password;

    const url = id ? `/api/admin/student/${id}` : '/api/admin/students';
    const method = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      studentModal.classList.add('hidden');
      loadStudents();
      loadAnalytics();
    } else {
      const json = await res.json();
      studentModalError.textContent = json.error || 'Failed to save student';
      studentModalError.classList.remove('hidden');
    }
  };

  await loadStudents();
  await loadAnalytics();
});