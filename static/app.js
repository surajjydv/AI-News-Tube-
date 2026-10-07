'use strict';

// ─── State ───────────────────────────────────────────────────
const State = { selectedFormat:'16:9 Documentary', platforms:{}, settings:{} };

const PMETA = {
  youtube:   { icon:'▶',  color:'#FF0000', cls:'yt', label:'YouTube',   interval:3   },
  telegram:  { icon:'✈',  color:'#26A5E4', cls:'tg', label:'Telegram',  interval:2   },
  twitter:   { icon:'𝕏',  color:'#1DA1F2', cls:'tw', label:'Twitter/X', interval:1.5 },
  facebook:  { icon:'📘', color:'#1877F2', cls:'fb', label:'Facebook',  interval:6   },
  instagram: { icon:'📸', color:'#E1306C', cls:'ig', label:'Instagram', interval:8   }
};
const PLATFORM_ORDER = ['youtube','telegram','twitter','facebook','instagram'];

// ─── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  fetchStatus();
  loadPlatforms();
  loadHistory();
  loadChannels();
  setInterval(fetchStatus, 4500);
});

// ─── Navigation ───────────────────────────────────────────────
function initNav() {
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab'), btn));
  });
}

function switchTab(tabId, btn) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active-page'));
  (btn || document.querySelector(`[data-tab="${tabId}"]`)).classList.add('active');
  const page = document.getElementById(`tab-${tabId}`);
  if (page) page.classList.add('active-page');
  if (tabId==='platforms') loadPlatforms();
  if (tabId==='analytics') loadHistory();
  if (tabId==='scheduler') renderScheduleGrid();
  if (tabId==='channels')  loadChannels();
}

// ─── Status ───────────────────────────────────────────────────
async function fetchStatus() {
  try {
    const r = await fetch('/api/status');
    if (!r.ok) return;
    const d = await r.json();
    const running = d.daemon_running;
    const tog = document.getElementById('globalAutopilotToggle');
    const dot = document.getElementById('sidebarDot');
    const stxt = document.getElementById('sidebarStatus');
    if (tog) tog.checked = !!running;
    dot.style.background = running ? '#00E676' : '#FF3366';
    stxt.innerText = running ? 'AUTOPILOT ON' : 'AUTOPILOT OFF';
    setTxt('dashServerTime', d.server_time_ist || '');
    setTxt('statNextPost', d.interval_hours ? d.interval_hours+'h' : '3h');
    if (d.log_snippet) {
      updateLog('logConsole', d.log_snippet);
      updateLog('analyticsLog', d.log_snippet);
      setTxt('logTimestamp', 'Updated: '+(d.server_time_ist||''));
    }
    buildActivityFeed(d);
    buildQueueList(d);
  } catch(e) { /* silent */ }
}

function updateLog(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<pre style="white-space:pre-wrap;word-break:break-all;">${escHtml(text)}</pre>`;
  el.scrollTop = el.scrollHeight;
}

function buildActivityFeed(d) {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;
  const lines = (d.log_snippet||'').split('\n').filter(l =>
    /PUBLISHED|Published|Upload|SUCCESS|Telegram|Twitter|Facebook/i.test(l)
  );
  if (!lines.length) return;
  feed.innerHTML = lines.slice(-8).reverse().map(line => `
    <div class="feed-item">
      <div class="feed-icon">${getFeedIcon(line)}</div>
      <div class="feed-body">
        <div class="feed-title">${escHtml(line.substring(0,90))}</div>
        <div class="feed-meta">Auto-published · SRJ UNDERRATED</div>
      </div>
    </div>`).join('');
}

function getFeedIcon(line) {
  if (/Telegram/i.test(line)) return '✈';
  if (/Twitter/i.test(line)) return '𝕏';
  if (/Facebook/i.test(line)) return '📘';
  if (/Instagram/i.test(line)) return '📸';
  return '▶';
}

function buildQueueList(d) {
  const el = document.getElementById('queueList');
  if (!el) return;
  el.innerHTML = PLATFORM_ORDER.filter(pid => {
    const c = State.platforms[pid]||{};
    return c.enabled && c.connected;
  }).map(pid => {
    const m = PMETA[pid];
    const c = State.platforms[pid]||{};
    const hrs = c.interval_hours || m.interval;
    return `<div class="queue-item">
      <div class="queue-platform ${m.cls}">${m.icon}</div>
      <div class="queue-body">
        <div class="queue-name">${m.label}</div>
        <div class="queue-eta">Every ${hrs}h · Night quiet 12AM–6AM</div>
      </div>
      <div class="queue-badge">${hrs}h</div>
    </div>`;
  }).join('') || '<div class="loading-text" style="padding:12px;">Connect platforms to see queue</div>';
}
z
// ─── Platform Status Row ──────────────────────────────────────
async function loadPlatforms() {
  try {
    const r = await fetch('/api/platforms');
    const d = r.ok ? await r.json() : {platforms:{}};
    State.platforms = d.platforms||{};
  } catch {}
  renderPlatformStatusRow();
  renderPlatformCards();
  updateConnectedBadge();
}

function updateConnectedBadge() {
  const count = Object.values(State.platforms).filter(p=>p.connected).length;
  setTxt('connectedBadge', count);
  setTxt('statConnected', count);
}

function renderPlatformStatusRow() {
  const row = document.getElementById('platformStatusRow');
  if (!row) return;
  row.innerHTML = PLATFORM_ORDER.map(pid => {
    const m = PMETA[pid];
    const c = State.platforms[pid]||{};
    return `<div class="plat-status-card ${c.connected?'connected':''} ${!c.enabled?'disabled':''}"
      onclick="switchTab('platforms')" title="Click to manage">
      <div class="plat-icon ${m.cls}">${m.icon}</div>
      <div class="plat-info">
        <div class="plat-name">${m.label}</div>
        <div class="plat-status-txt">${c.connected?'✅ Connected':'❌ Not connected'}</div>
      </div>
      <div class="plat-conn-dot ${c.connected?'on':'off'}"></div>
    </div>`;
  }).join('');
}

function renderPlatformCards() {
  const grid = document.getElementById('platformsGrid');
  if (!grid) return;

  grid.innerHTML = PLATFORM_ORDER.map(pid => {
    const m = PMETA[pid];
    const c = State.platforms[pid]||{};
    const connected = c.connected;

    let helpText = '';
    let fields = '';

    if (pid==='youtube') {
      helpText = '✅ Connected automatically via OAuth token.json on EC2. To switch channels, use the YouTube Channel tab.';
      fields = '';
    } else if (pid==='telegram') {
      helpText = `Bot <b>@Tcvip1_bot</b> is ${connected?'✅ <b>Connected</b>':'❌ not connected'}. Your posts go to your personal Telegram chat. To use a channel instead, add the bot as Admin and enter the channel ID below.`;
      fields = `
        <div class="platform-fields">
          <input type="password" id="tg_bot_token" placeholder="Bot Token (7318976676:AAF...)" value="${c.bot_token||''}">
          <input type="text" id="tg_channel_id" placeholder="Channel ID (@mychannel or -1001234567890)" value="${c.channel_id||''}">
        </div>`;
    } else if (pid==='twitter') {
      helpText = 'Requires a Twitter Developer App with read &amp; write permissions. Create at <b>developer.twitter.com</b>';
      fields = `
        <div class="platform-fields">
          <input type="password" id="tw_api_key" placeholder="API Key (Consumer Key)">
          <input type="password" id="tw_api_secret" placeholder="API Key Secret">
          <input type="password" id="tw_access_token" placeholder="Access Token">
          <input type="password" id="tw_access_secret" placeholder="Access Token Secret">
        </div>`;
    } else if (pid==='facebook') {
      helpText = 'Requires a Facebook Page and a Page Access Token from <b>developers.facebook.com → Tools → Graph API Explorer</b>';
      fields = `
        <div class="platform-fields">
          <input type="password" id="fb_token" placeholder="Page Access Token">
          <input type="text" id="fb_page_id" placeholder="Facebook Page ID (numeric)">
        </div>`;
    } else if (pid==='instagram') {
      helpText = '⚠️ Requires Instagram <b>Business or Creator</b> account linked to a Facebook Page. Personal accounts cannot post programmatically.';
      fields = `
        <div class="platform-fields">
          <input type="password" id="ig_token" placeholder="Long-lived Access Token">
          <input type="text" id="ig_page_id" placeholder="Instagram Business Account ID">
        </div>`;
    }

    return `
    <div class="platform-connect-card ${connected?'connected':''}" id="platcard-${pid}">
      <div class="platform-card-header">
        <div class="platform-icon-big plat-icon ${m.cls}" style="background:${m.color}20;">${m.icon}</div>
        <div style="flex:1;">
          <div class="platform-card-title">${m.label}</div>
          <div class="platform-card-sub">${(c.content_types||[]).join(' · ')}</div>
        </div>
        <div class="platform-conn-status ${connected?'status-connected':'status-disconnected'}">
          ${connected?'✅ Connected':'❌ Disconnected'}
        </div>
      </div>

      <p class="platform-help">${helpText}</p>
      ${fields}

      <div class="platform-actions">
        ${pid!=='youtube'?`<button class="btn btn-primary btn-sm" onclick="connectPlatform('${pid}')">💾 Save &amp; Connect</button>`:''}
        ${pid==='telegram'?`<button class="btn btn-outline btn-sm" onclick="sendTestMessage()">🔔 Test Message</button>`:''}
        <div style="margin-left:auto;display:flex;align-items:center;gap:8px;">
          <label class="switch">
            <input type="checkbox" id="toggle-${pid}" ${c.enabled?'checked':''} onchange="togglePlatform('${pid}',this.checked)">
            <span class="slider round"></span>
          </label>
          <span style="font-size:11px;color:var(--text-muted);">${c.enabled?'Enabled':'Disabled'}</span>
        </div>
      </div>
    </div>`;
  }).join('');
}

async function connectPlatform(pid) {
  const creds = {};
  if (pid==='telegram') {
    creds.bot_token  = val('tg_bot_token');
    creds.channel_id = val('tg_channel_id');
  } else if (pid==='twitter') {
    creds.api_key            = val('tw_api_key');
    creds.api_secret         = val('tw_api_secret');
    creds.access_token       = val('tw_access_token');
    creds.access_token_secret= val('tw_access_secret');
  } else if (pid==='instagram') {
    creds.token   = val('ig_token');
    creds.page_id = val('ig_page_id');
  } else if (pid==='facebook') {
    creds.token   = val('fb_token');
    creds.page_id = val('fb_page_id');
  }

  try {
    const r = await fetch('/api/platforms/connect', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({platform:pid, credentials:creds})
    });
    const d = await r.json();
    if (d.status==='success') {
      showToast(`${PMETA[pid].label} ${d.connected?'connected':'saved'}!`, 'success');
      await loadPlatforms();
    } else {
      showToast(d.message||'Connection failed', 'error');
    }
  } catch(e) { showToast('Error: '+e.message, 'error'); }
}

async function togglePlatform(pid, enabled) {
  await fetch('/api/platforms/toggle', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({platform:pid, enabled})
  }).catch(()=>{});
  await loadPlatforms();
}

async function sendTestMessage() {
  const token = val('tg_bot_token') || (State.platforms.telegram||{}).bot_token || '';
  const channel = val('tg_channel_id') || (State.platforms.telegram||{}).channel_id || '';
  if (!token) { showToast('Enter bot token first', 'error'); return; }
  try {
    const msg = encodeURIComponent('AI Social Manager - Test message! Your news videos will be delivered here automatically.');
    const r = await fetch(`https://api.telegram.org/bot${token}/sendMessage?chat_id=${channel||'5802349554'}&text=${msg}`);
    const d = await r.json();
    if (d.ok) showToast('Test message sent to Telegram!', 'success');
    else showToast('Failed: '+d.description, 'error');
  } catch(e) { showToast('Error: '+e.message, 'error'); }
}

// ─── Scheduler ───────────────────────────────────────────────
function renderScheduleGrid() {
  const grid = document.getElementById('scheduleGrid');
  if (!grid) return;
  grid.innerHTML = PLATFORM_ORDER.map(pid => {
    const m = PMETA[pid];
    const c = State.platforms[pid]||{};
    const hrs = c.interval_hours || m.interval;
    return `
    <div class="schedule-card">
      <div class="schedule-card-header">
        <div style="display:flex;align-items:center;gap:9px;">
          <span class="plat-icon ${m.cls}" style="width:30px;height:30px;font-size:14px;border-radius:7px;display:flex;align-items:center;justify-content:center;">${m.icon}</span>
          <span class="schedule-plat-name">${m.label}</span>
        </div>
        <label class="switch">
          <input type="checkbox" ${c.enabled?'checked':''} onchange="togglePlatform('${pid}',this.checked)">
          <span class="slider round"></span>
        </label>
      </div>
      <div class="form-group">
        <label>Post every <b id="int-lbl-${pid}">${hrs}</b> hours</label>
        <input type="range" min="0.5" max="24" step="0.5" value="${hrs}"
          oninput="document.getElementById('int-lbl-${pid}').innerText=this.value"
          onchange="updatePlatformInterval('${pid}',this.value)">
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:5px;">
        ${(c.content_types||[m.label.toLowerCase()]).map(t=>`<span style="background:rgba(255,255,255,0.06);border-radius:4px;padding:2px 7px;font-size:10.5px;">${t}</span>`).join('')}
      </div>
    </div>`;
  }).join('');
}

async function updatePlatformInterval(pid, hours) {
  await fetch('/api/platforms/connect',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({platform:pid,credentials:{interval_hours:parseFloat(hours)}})
  }).catch(()=>{});
}

async function saveSchedulerSettings() {
  const updates = {
    night_quiet_start_hour: parseInt(document.getElementById('nightStart').value,10)||0,
    night_quiet_end_hour:   parseInt(document.getElementById('nightEnd').value,10)||6,
    groq_script_model:      document.getElementById('modelSelect').value,
    voice_id:               document.getElementById('schedVoice').value,
    target_script_minutes:  parseFloat(document.getElementById('schedLength').value)||7.5
  };
  try {
    const r = await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(updates)});
    if (r.ok) showToast('Schedule saved!','success');
    else showToast('Save failed','error');
  } catch(e) { showToast('Error: '+e.message,'error'); }
}

// ─── Channels ────────────────────────────────────────────────
async function loadChannels() {
  try {
    const r = await fetch('/api/channels');
    const d = r.ok ? await r.json() : {channels:[]};
    const list = document.getElementById('channelList');
    if (!list) return;
    if (!d.channels||!d.channels.length) { list.innerHTML='<div class="loading-text">No channels configured</div>'; return; }
    list.innerHTML = d.channels.map(ch => `
      <div class="channel-item ${ch.is_active?'active-ch':''}" onclick="setActiveChannel('${ch.name}','${ch.id}')">
        <div style="width:34px;height:34px;border-radius:9px;background:rgba(255,0,0,0.15);display:flex;align-items:center;justify-content:center;font-size:16px;">▶</div>
        <div>
          <div style="font-weight:700;font-size:13px;">${escHtml(ch.name)}</div>
          <div style="font-size:10px;color:var(--text-muted);">${ch.id}</div>
        </div>
        ${ch.is_active?'<span style="margin-left:auto;" class="status-connected" style="font-size:10px;padding:2px 8px;">Active</span>':''}
      </div>`).join('');

    const active = d.channels.find(c=>c.is_active)||d.channels[0];
    if (active) {
      setTxt('activeChName', active.name);
      setTxt('activeChId', active.id);
    }
  } catch { /* silent */ }
}

async function switchChannel() {
  const name  = val('switchChName');
  const id    = val('switchChId');
  const token = val('switchChToken');
  if (!name||!id) { showToast('Enter channel name and ID','error'); return; }
  try {
    const r = await fetch('/api/channels/switch',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({channel_name:name,channel_id:id,token_json_str:token||null})
    });
    if (r.ok) { showToast('Channel switched to '+name,'success'); loadChannels(); }
    else showToast('Switch failed','error');
  } catch(e) { showToast('Error: '+e.message,'error'); }
}

// ─── Studio ──────────────────────────────────────────────────
function selectFormat(btn) {
  document.querySelectorAll('.format-pills .pill-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  State.selectedFormat = btn.getAttribute('data-format');
  updatePreviewCards();
}

function updatePreviewCards() {
  const topic = val('studioTopic') || 'Your topic here';
  setTxt('prevYtTitle', topic.substring(0,80));
  setTxt('prevTgCaption', `📍 ${topic.substring(0,60)}\n\nWatch: youtube.com/... #BreakingNews`);
  setTxt('prevTwCaption', `🔴 ${topic.substring(0,160)} #IndiaNews #BreakingNews`);
  setTxt('prevFbCaption', `🔴 ${topic.substring(0,120)}\n\nFull video on YouTube:`);
}

document.addEventListener('input', e => { if (e.target.id==='studioTopic') updatePreviewCards(); });

async function studioPublish() {
  const topic = val('studioTopic').trim();
  if (!topic) { showToast('Enter a topic or URL','error'); return; }
  const platforms = Array.from(document.querySelectorAll('#studioPublishTo input:checked')).map(c=>c.value);
  const btn = document.getElementById('studioPublishBtn');
  btn.disabled = true; btn.innerText = 'Generating & Publishing...';
  try {
    const r = await fetch('/api/generate/custom',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        topic,
        video_format: State.selectedFormat,
        voice_id: val('studioVoice'),
        target_minutes: parseFloat(document.getElementById('studioLength').value),
        target_platforms: platforms
      })
    });
    const d = await r.json();
    if (r.ok) { showToast('Production started! '+d.message,'success'); document.getElementById('studioTopic').value=''; }
    else showToast(d.detail||'Failed','error');
  } catch(e) { showToast('Error: '+e.message,'error'); }
  finally { btn.disabled=false; btn.innerText='🚀 Generate & Publish to Selected Platforms'; }
}

// ─── Dashboard Actions ────────────────────────────────────────
async function triggerImmediatePost() {
  try {
    const r = await fetch('/api/generate/custom',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic:'AUTO_TRENDING_TOP_1',video_format:'16:9 Breaking Bulletin',voice_id:'hi-IN-MadhurNeural',target_minutes:3.0})});
    const d = await r.json();
    if (r.ok) showToast('Immediate publish triggered! '+d.message,'success');
    else showToast(d.detail,'error');
  } catch(e) { showToast('Error: '+e.message,'error'); }
}

async function toggleGlobalAutopilot() {
  const isOn = document.getElementById('globalAutopilotToggle').checked;
  await fetch('/api/daemon/control',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:isOn?'start':'stop'})}).catch(()=>{});
  fetchStatus();
}

// ─── Strategy ────────────────────────────────────────────────
async function saveStrategy() {
  const updates = { narrative_style: document.getElementById('stratNarrative').value };
  await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(updates)}).catch(()=>{});
  showToast('AI Strategy saved!','success');
}

// ─── History / Analytics ─────────────────────────────────────
async function loadHistory() {
  try {
    const r = await fetch('/api/history');
    if (!r.ok) return;
    const d = await r.json();
    const items = d.published_videos||[];
    renderHistory(items);
    updateAnalyticsSummary(items);
  } catch { /* silent */ }
}

function renderHistory(items) {
  const el = document.getElementById('historyTable');
  if (!el) return;
  if (!items.length) { el.innerHTML='<div class="loading-text">No history yet — posts appear here once published</div>'; return; }
  el.innerHTML = items.slice(0,40).map(v => {
    const platDots = PLATFORM_ORDER.map(pid => {
      const plats = v.platforms||{};
      const ok = plats[pid]&&plats[pid].success;
      if (!ok) return '';
      return `<span class="plat-dot plat-icon ${PMETA[pid].cls}" title="${PMETA[pid].label} OK">${PMETA[pid].icon}</span>`;
    }).join('');
    const ytUrl = v.youtube_url||'';
    const ts = (v.timestamp||'').substring(0,16).replace('T',' ');
    return `
    <div class="history-row">
      <div class="feed-icon">▶</div>
      <div class="history-title-txt">${escHtml((v.title||v.type||'Trending Video').substring(0,80))}</div>
      <div class="platform-dots">${platDots}</div>
      <div class="history-time-txt">${ts}</div>
      ${ytUrl?`<a href="${ytUrl}" target="_blank" class="btn btn-sm btn-outline" style="white-space:nowrap;">Watch ↗</a>`:''}
    </div>`;
  }).join('');
}

function updateAnalyticsSummary(items) {
  const today = new Date().toISOString().substring(0,10);
  setTxt('sumTotal', items.length);
  setTxt('sumToday', items.filter(v=>(v.timestamp||'').startsWith(today)).length);
  setTxt('sumYT', items.filter(v=>v.youtube_url).length);
  setTxt('sumTG', items.filter(v=>v.platforms&&v.platforms.telegram&&v.platforms.telegram.success).length);
  setTxt('statPostsToday', items.filter(v=>(v.timestamp||'').startsWith(today)).length || '0');
}

async function refreshDashboard() { fetchStatus(); loadPlatforms(); }

// ─── Toast Notification ───────────────────────────────────────
function showToast(message, type='info') {
  const existing = document.getElementById('toast-container');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.id = 'toast-container';
  const bg = type==='success'?'rgba(0,230,118,0.15)':type==='error'?'rgba(255,51,102,0.15)':'rgba(0,212,255,0.15)';
  const border = type==='success'?'rgba(0,230,118,0.4)':type==='error'?'rgba(255,51,102,0.4)':'rgba(0,212,255,0.4)';
  const color = type==='success'?'#00E676':type==='error'?'#FF3366':'#00D4FF';
  toast.style.cssText = `position:fixed;bottom:24px;right:24px;background:${bg};border:1px solid ${border};color:${color};border-radius:10px;padding:12px 20px;font-size:13px;font-weight:700;z-index:9999;max-width:340px;box-shadow:0 8px 30px rgba(0,0,0,0.5);animation:fadeIn 0.2s ease;`;
  toast.innerHTML = `${type==='success'?'✅':type==='error'?'❌':'ℹ️'} ${escHtml(message)}`;
  document.body.appendChild(toast);
  setTimeout(()=>{ toast.style.opacity='0'; toast.style.transition='opacity 0.3s'; setTimeout(()=>toast.remove(),400); },4000);
}

// ─── Utils ───────────────────────────────────────────────────
function setTxt(id,val){ const e=document.getElementById(id); if(e)e.innerText=val; }
function val(id){ const e=document.getElementById(id); return e?e.value.trim():''; }
function escHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
