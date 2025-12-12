const $ = (sel) => document.querySelector(sel);

async function fetchQuota() {
  const userId = $('#userId').value.trim();
  const r = await fetch(`/api/quota?user_id=${encodeURIComponent(userId)}`);
  const j = await r.json();
  $('#quota').innerHTML = `Limit: ${j.limit_mb} MB<br/>Used: ${j.used_mb} MB<br/>Remaining: ${j.remaining_mb} MB`;
  $('#system').innerHTML = `Total: ${j.system_total_mb} MB<br/>Used: ${j.system_used_mb} MB<br/>Free: ${j.system_free_mb} MB`;
}

async function fetchList() {
  const userId = $('#userId').value.trim();
  const r = await fetch(`/api/list?user_id=${encodeURIComponent(userId)}`);
  const j = await r.json();
  const list = $('#filesList');
  list.innerHTML = '';
  (j.objects || []).forEach(o => {
    const row = document.createElement('div');
    row.className = 'file-row';
    const p = document.createElement('div'); p.textContent = o.path; row.appendChild(p);
    const s = document.createElement('div'); s.textContent = `${o.size_mb} MB`; row.appendChild(s);
    const a = document.createElement('div'); a.className = 'file-actions';
    const dl = document.createElement('button'); dl.textContent = 'Download';
    dl.onclick = () => window.location = `/api/download?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(o.path)}`;
    const del = document.createElement('button'); del.textContent = 'Delete';
    del.onclick = async () => {
      await fetch(`/api/object?user_id=${encodeURIComponent(userId)}&path=${encodeURIComponent(o.path)}`, { method: 'DELETE' });
      await fetchList(); await fetchQuota();
    };
    a.appendChild(dl); a.appendChild(del); row.appendChild(a);
    list.appendChild(row);
  });
}

function setupUpload() {
  const form = $('#uploadForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = $('#userId').value.trim();
    const file = $('#fileInput').files[0];
    if (!file) return;
    const path = $('#pathInput').value.trim();
    const dup = $('#dupInput').checked;
    const fd = new FormData();
    fd.append('user_id', userId);
    fd.append('file', file);
    fd.append('path', path);
    fd.append('allow_duplicate', dup ? 'true' : 'false');
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) {
        const percent = Math.round((evt.loaded / evt.total) * 100);
        $('#progressBar').style.width = percent + '%';
      }
    };
    xhr.onload = async () => {
      $('#progressBar').style.width = '0%';
      const res = JSON.parse(xhr.responseText);
      $('#uploadResult').textContent = `Result: ${res.result}, Path: ${res.path}, ${res.size_mb} MB`;
      await fetchList(); await fetchQuota();
    };
    xhr.send(fd);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  setupUpload();
  fetchQuota();
  fetchList();
  $('#userId').addEventListener('change', () => { fetchQuota(); fetchList(); });
});
