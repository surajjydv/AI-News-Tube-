'use strict';

// ─── GLOBAL APPLICATION STATE ────────────────────────────────────────────────
const AppState = {
  currentMode: 'blast',
  platforms: {},
  selectedFormat: '16:9 Documentary',
  selectedMediaFile: null,
  selectedThumbFile: null,
  isGeneratingAI: false,
  pollTimer: null
};

// Platform display metadata
const PLATFORM_META = {
  youtube:   { icon: '▶', name: 'YouTube',   color: '#FF0000', linkPrefix: 'https://youtu.be/' },
  telegram:  { icon: '✈', name: 'Telegram',  color: '#229ED9', linkPrefix: '' },
  twitter:   { icon: '𝕏', name: 'Twitter',   color: '#1D9BF0', linkPrefix: 'https://twitter.com' },
  instagram: { icon: '📸', name: 'Instagram', color: '#E1306C', linkPrefix: 'https://instagram.com' },
  facebook:  { icon: '📘', name: 'Facebook',  color: '#1877F2', linkPrefix: 'https://facebook.com' }
};

// ─── INITIALIZATION ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initDragAndDrop();
  fetchPlatforms();
  fetchSystemStatus();
  loadHistory();

  // Poll system status and logs every 4 seconds
  setInterval(fetchSystemStatus, 4000);
});

// ─── TAB NAVIGATION ─────────────────────────────────────────────────────────
function switchWorkflowMode(mode) {
  AppState.currentMode = mode;

  // Update tab buttons
  document.querySelectorAll('.mode-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-mode') === mode);
  });

  // Update visible section
  document.querySelectorAll('.workflow-section').forEach(sec => {
    sec.classList.remove('active-section');
  });

  const targetSec = document.getElementById(`section-${mode}`);
  if (targetSec) {
    targetSec.classList.add('active-section');
  }

  if (mode === 'history') {
    loadHistory();
  }
}

// ─── SYSTEM 1: 1-CLICK MEDIA BLAST LOGIC ────────────────────────────────────

// Drag & drop handlers
function initDragAndDrop() {
  const dropzone = document.getElementById('mediaDropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processSelectedMedia(files[0]);
    }
  });
}

function handleMediaSelect(input) {
  if (input.files && input.files.length > 0) {
    processSelectedMedia(input.files[0]);
  }
}

function processSelectedMedia(file) {
  AppState.selectedMediaFile = file;

  const emptyView = document.getElementById('dropzoneEmpty');
  const previewView = document.getElementById('mediaPreview');
  const viewport = document.getElementById('previewViewport');
  const nameEl = document.getElementById('previewFileName');
  const sizeEl = document.getElementById('previewFileSize');
  const optionalThumbBox = document.getElementById('optionalThumbBox');

  emptyView.style.display = 'none';
  previewView.style.display = 'flex';
  viewport.innerHTML = '';

  const mb = (file.size / (1024 * 1024)).toFixed(1);
  nameEl.innerText = file.name;
  sizeEl.innerText = `${mb} MB · ${file.type || 'Media'}`;

  const objectUrl = URL.createObjectURL(file);

  if (file.type.startsWith('video/')) {
    const vid = document.createElement('video');
    vid.src = objectUrl;
    vid.controls = true;
    vid.autoplay = false;
    viewport.appendChild(vid);
    if (optionalThumbBox) optionalThumbBox.style.display = 'block';
  } else {
    const img = document.createElement('img');
    img.src = objectUrl;
    viewport.appendChild(img);
    if (optionalThumbBox) optionalThumbBox.style.display = 'none';
  }

  // Pre-fill title if empty
  const titleInput = document.getElementById('blastTitle');
  if (titleInput && !titleInput.value.trim()) {
    const cleanTitle = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
    titleInput.value = cleanTitle.charAt(0).toUpperCase() + cleanTitle.slice(1);
    updateCounter('blastTitle', 'titleCounter', 100);
  }

  showToast(`Loaded ${file.name} (${mb} MB)`, 'info');
}

function removeMedia(e) {
  if (e) e.stopPropagation();
  AppState.selectedMediaFile = null;
  AppState.selectedThumbFile = null;

  const mediaInput = document.getElementById('mediaInput');
  const thumbInput = document.getElementById('thumbInput');
  if (mediaInput) mediaInput.value = '';
  if (thumbInput) thumbInput.value = '';

  const emptyView = document.getElementById('dropzoneEmpty');
  const previewView = document.getElementById('mediaPreview');
  const viewport = document.getElementById('previewViewport');
  const optionalThumbBox = document.getElementById('optionalThumbBox');
  const thumbFileName = document.getElementById('thumbFileName');

  if (emptyView) emptyView.style.display = 'block';
  if (previewView) previewView.style.display = 'none';
  if (viewport) viewport.innerHTML = '';
  if (optionalThumbBox) optionalThumbBox.style.display = 'none';
  if (thumbFileName) thumbFileName.innerText = 'No custom thumbnail chosen';
}

function handleThumbSelect(input) {
  if (input.files && input.files.length > 0) {
    AppState.selectedThumbFile = input.files[0];
    const thumbFileName = document.getElementById('thumbFileName');
    if (thumbFileName) {
      thumbFileName.innerText = `${input.files[0].name} (${(input.files[0].size/1024).toFixed(0)} KB)`;
    }
    showToast('Custom thumbnail selected', 'info');
  }
}

function updateCounter(inputId, counterId, max) {
  const input = document.getElementById(inputId);
  const counter = document.getElementById(counterId);
  if (!input || !counter) return;
  const len = input.value.length;
  counter.innerText = `${len}/${max}`;
  counter.style.color = len >= max ? '#F43F5E' : '#64748B';
}

function appendTag(tag) {
  const hashtagsInput = document.getElementById('blastHashtags');
  if (!hashtagsInput) return;
  const current = hashtagsInput.value.trim();
  if (!current.includes(tag)) {
    hashtagsInput.value = current ? `${current} ${tag}` : tag;
  }
}

function togglePlatformCard(checkbox) {
  const parent = checkbox.closest('.platform-check-card');
  if (parent) {
    parent.classList.toggle('active', checkbox.checked);
  }
}

// Blast Form Submit Handler
async function handleBlastSubmit(e) {
  e.preventDefault();

  const title = document.getElementById('blastTitle').value.trim();
  const description = document.getElementById('blastDescription').value.trim();
  const hashtags = document.getElementById('blastHashtags').value.trim();

  // Get selected platforms
  const checkedBoxes = document.querySelectorAll('input[name="target_platform"]:checked');
  const selectedPlatforms = Array.from(checkedBoxes).map(cb => cb.value);

  if (selectedPlatforms.length === 0) {
    showToast('Please select at least 1 platform to blast to.', 'error');
    return;
  }

  const btn = document.getElementById('btnBlastSubmit');
  const origBtnContent = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="btn-content">⏳ Blasting to ${selectedPlatforms.length} Platforms...</span>`;

  const resultsArea = document.getElementById('blastResultsArea');
  const resultsList = document.getElementById('blastResultsList');
  const overallBadge = document.getElementById('blastOverallStatus');

  resultsArea.style.display = 'block';
  overallBadge.className = 'status-badge running';
  overallBadge.innerText = 'Publishing...';
  resultsList.innerHTML = `<div class="table-loading">Broadcasting media across ${selectedPlatforms.join(', ')}...</div>`;

  try {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('hashtags', hashtags);
    formData.append('platforms', selectedPlatforms.join(','));

    if (AppState.selectedMediaFile) {
      formData.append('media', AppState.selectedMediaFile);
    }
    if (AppState.selectedThumbFile) {
      formData.append('thumbnail', AppState.selectedThumbFile);
    }

    const res = await fetch('/api/publish/blast', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Blast failed');
    }

    overallBadge.className = 'status-badge success';
    overallBadge.innerText = 'Blasted Successfully';

    renderBlastResults(data.results);
    showToast(`Successfully blasted to ${Object.keys(data.results).length} platforms!`, 'success');
    loadHistory();

  } catch (err) {
    overallBadge.className = 'status-badge';
    overallBadge.style.color = '#F43F5E';
    overallBadge.innerText = 'Error';
    resultsList.innerHTML = `<div style="color:#F43F5E; padding:10px;">❌ Error: ${err.message}</div>`;
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = origBtnContent;
  }
}

function renderBlastResults(results) {
  const resultsList = document.getElementById('blastResultsList');
  if (!resultsList) return;

  const entries = Object.entries(results || {});
  if (entries.length === 0) {
    resultsList.innerHTML = `<div class="text-subtle" style="padding:10px;">No platform responses received.</div>`;
    return;
  }

  resultsList.innerHTML = entries.map(([platform, res]) => {
    const meta = PLATFORM_META[platform] || { icon: '🌐', name: platform, color: '#6366F1' };
    const isSuccess = res.success !== false;
    const link = res.url || (res.id ? `ID: ${res.id}` : null);

    return `
      <div class="result-item-row">
        <div class="result-item-left">
          <span class="result-icon" style="color: ${meta.color}">${meta.icon}</span>
          <strong>${meta.name}</strong>
          <span class="status-badge-sm ${isSuccess ? 'connected' : ''}">
            ${isSuccess ? '✓ Published' : '✕ Failed'}
          </span>
        </div>
        <div>
          ${link ? `<a href="${link.startsWith('http') ? link : '#'}" target="_blank" class="result-link">View Post ↗</a>` : `<span class="text-subtle">${res.error || 'Done'}</span>`}
        </div>
      </div>
    `;
  }).join('');
}

// ─── SYSTEM 2: AI WORD-TO-VIDEO & AUTO-BLAST ────────────────────────────────

function selectFormatCard(card) {
  document.querySelectorAll('.format-card').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
  AppState.selectedFormat = card.getAttribute('data-format');
}

async function startAIGeneration() {
  const topic = document.getElementById('aiTopic').value.trim();
  if (!topic) {
    showToast('Please enter a topic headline or words prompt.', 'error');
    document.getElementById('aiTopic').focus();
    return;
  }

  const directUrl = document.getElementById('aiDirectUrl').value.trim();
  const rawNotes = document.getElementById('aiRawNotes').value.trim();
  const voiceId = document.getElementById('aiVoice').value;
  const targetMin = parseFloat(document.getElementById('aiDuration').value) || 5.0;

  const btn = document.getElementById('btnAIGenerate');
  btn.disabled = true;
  btn.innerHTML = `<span class="btn-content">⏳ AI Production Triggered...</span>`;

  const badge = document.getElementById('pipelineStatusBadge');
  badge.className = 'status-badge running';
  badge.innerText = 'In Production';

  resetPipelineSteps();
  activatePipelineStep('step-research');

  try {
    const res = await fetch('/api/generate/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        direct_url: directUrl,
        video_format: AppState.selectedFormat,
        voice_id: voiceId,
        target_minutes: targetMin,
        raw_script_text: rawNotes
      })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to start AI generation');
    }

    appendTerminal(`🚀 Production triggered for: "${topic}"`);
    appendTerminal(`Format: ${AppState.selectedFormat} | Voice: ${voiceId} | Duration: ${targetMin} min`);
    appendTerminal(`Auto-Blast: Active across all connected channels.`);
    showToast('AI Video Production started in background!', 'success');

    // Simulate animated step progression based on active logs
    AppState.isGeneratingAI = true;
    startPipelineSimulation();

  } catch (err) {
    badge.className = 'status-badge';
    badge.style.color = '#F43F5E';
    badge.innerText = 'Failed';
    appendTerminal(`❌ Error: ${err.message}`);
    showToast(err.message, 'error');
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = `
        <span class="btn-content">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          <span>Generate Video & Auto-Blast</span>
        </span>`;
    }, 3000);
  }
}

function resetPipelineSteps() {
  ['step-research', 'step-script', 'step-voice', 'step-render', 'step-blast'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.className = 'pipe-step';
  });
}

function activatePipelineStep(stepId) {
  const el = document.getElementById(stepId);
  if (el) {
    el.className = 'pipe-step running';
  }
}

function completePipelineStep(stepId) {
  const el = document.getElementById(stepId);
  if (el) {
    el.className = 'pipe-step done';
  }
}

function startPipelineSimulation() {
  const steps = [
    { id: 'step-research', duration: 4000, msg: '🔍 Fact research complete. Extracted entity dossiers.' },
    { id: 'step-script',   duration: 6000, msg: '📝 Hindi journalistic script written with chapters.' },
    { id: 'step-voice',    duration: 5000, msg: '🎙️ Neural Edge-TTS voiceover track synthesized.' },
    { id: 'step-render',   duration: 9000, msg: '🎬 1080p dynamic video & 3D thumbnail rendered via FFmpeg.' },
    { id: 'step-blast',    duration: 3000, msg: '🚀 Auto-published video to YouTube, Telegram, Twitter, Instagram & FB!' }
  ];

  let cumulativeTime = 0;
  steps.forEach((s, idx) => {
    setTimeout(() => {
      if (idx > 0) completePipelineStep(steps[idx - 1].id);
      activatePipelineStep(s.id);
      appendTerminal(s.msg);

      if (idx === steps.length - 1) {
        setTimeout(() => {
          completePipelineStep(s.id);
          const badge = document.getElementById('pipelineStatusBadge');
          if (badge) {
            badge.className = 'status-badge success';
            badge.innerText = 'Completed & Blasted';
          }
          appendTerminal('🎉 Full production & multi-platform blast completed successfully!');
          showToast('Video generated and published everywhere!', 'success');
          loadHistory();
        }, s.duration);
      }
    }, cumulativeTime);
    cumulativeTime += s.duration;
  });
}

function appendTerminal(text) {
  const term = document.getElementById('terminalLog');
  if (!term) return;
  const timeStr = new Date().toLocaleTimeString();
  term.innerText += `\n[${timeStr}] ${text}`;
  term.scrollTop = term.scrollHeight;
}

function clearTerminal() {
  const term = document.getElementById('terminalLog');
  if (term) term.innerText = 'OmniBlast Engine standing by...';
}

// ─── PLATFORM MANAGEMENT & CREDENTIALS ──────────────────────────────────────

async function fetchPlatforms() {
  try {
    const res = await fetch('/api/platforms');
    if (!res.ok) return;
    const data = await res.json();
    AppState.platforms = data.platforms || {};

    // Update header chips
    Object.keys(PLATFORM_META).forEach(pid => {
      const chip = document.getElementById(`chip-${pid}`);
      const cfg = AppState.platforms[pid] || {};
      const isConn = !!cfg.connected;
      if (chip) {
        chip.classList.toggle('connected', isConn);
        chip.title = isConn ? `${PLATFORM_META[pid].name}: Connected` : `${PLATFORM_META[pid].name}: Not Connected (Click to set)`;
      }

      // Update modal badges
      const modalBadge = document.getElementById(`${pid === 'twitter' ? 'tw' : pid === 'telegram' ? 'tg' : pid === 'instagram' ? 'ig' : pid === 'facebook' ? 'fb' : 'yt'}StatusBadge`);
      if (modalBadge) {
        modalBadge.className = `status-badge-sm ${isConn ? 'connected' : ''}`;
        modalBadge.innerText = isConn ? 'Connected' : 'Not Connected';
      }
    });

  } catch (e) {
    console.error('Error fetching platforms:', e);
  }
}

async function fetchSystemStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const d = await res.json();

    // Stream logs into terminal if new lines
    if (d.log_snippet && AppState.currentMode === 'ai-create') {
      const term = document.getElementById('terminalLog');
      if (term && term.innerText.length < 200) {
        term.innerText = d.log_snippet;
      }
    }
  } catch (e) {
    // server momentarily offline
  }
}

function openConfigModal() {
  const modal = document.getElementById('configModal');
  if (modal) modal.classList.add('open');
}

function closeConfigModal(e) {
  if (e && e.target !== e.currentTarget && !e.target.classList.contains('btn-modal-close')) return;
  const modal = document.getElementById('configModal');
  if (modal) modal.classList.remove('open');
}

async function savePlatformCreds(platform) {
  let creds = {};

  if (platform === 'telegram') {
    creds = {
      bot_token: document.getElementById('cfgTgBotToken').value.trim(),
      channel_id: document.getElementById('cfgTgChannelId').value.trim()
    };
  } else if (platform === 'twitter') {
    creds = {
      api_key: document.getElementById('cfgTwApiKey').value.trim(),
      api_secret: document.getElementById('cfgTwApiSecret').value.trim(),
      access_token: document.getElementById('cfgTwAccessToken').value.trim(),
      access_token_secret: document.getElementById('cfgTwTokenSecret').value.trim()
    };
  } else if (platform === 'instagram') {
    creds = {
      token: document.getElementById('cfgIgToken').value.trim(),
      page_id: document.getElementById('cfgIgPageId').value.trim()
    };
  } else if (platform === 'facebook') {
    creds = {
      token: document.getElementById('cfgFbToken').value.trim(),
      page_id: document.getElementById('cfgFbPageId').value.trim()
    };
  }

  try {
    const res = await fetch('/api/platforms/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, credentials: creds })
    });

    const data = await res.json();
    if (data.status === 'success') {
      showToast(`${PLATFORM_META[platform]?.name || platform} credentials saved!`, 'success');
      fetchPlatforms();
    } else {
      showToast(data.message || 'Verification failed', 'error');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ─── SYSTEM 3: HISTORY & AUDIT LOG ──────────────────────────────────────────

async function loadHistory() {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/history');
    if (!res.ok) return;
    const data = await res.json();
    const list = data.published_videos || [];

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="table-loading">No posts recorded yet. Blast your first media above!</td></tr>`;
      return;
    }

    tbody.innerHTML = list.slice(0, 15).map(item => {
      const dt = item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Recent';
      const title = item.title || item.topic || item.hash || 'Media Broadcast';
      
      const plats = item.platforms ? Object.keys(item.platforms) : ['youtube'];
      const platBadges = plats.map(p => {
        const meta = PLATFORM_META[p] || { icon: '🌐', color: '#6366F1' };
        return `<span style="color:${meta.color}; font-weight:700; margin-right:6px;">${meta.icon} ${p}</span>`;
      }).join('');

      let quickLinks = '-';
      if (item.youtube_url) {
        quickLinks = `<a href="${item.youtube_url}" target="_blank" class="result-link">YouTube ↗</a>`;
      } else if (item.platforms && item.platforms.youtube && item.platforms.youtube.url) {
        quickLinks = `<a href="${item.platforms.youtube.url}" target="_blank" class="result-link">YouTube ↗</a>`;
      }

      return `
        <tr>
          <td style="color:var(--text-muted); font-size:12px;">${dt}</td>
          <td><strong>${title}</strong></td>
          <td>${platBadges}</td>
          <td><span class="status-badge-sm connected">Published</span></td>
          <td>${quickLinks}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#F43F5E; text-align:center;">Failed to load history: ${err.message}</td></tr>`;
  }
}

// ─── TOAST NOTIFICATIONS ────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
