// MapLeads F&B Client Logic
let currentFilter = 'all';
let currentSearch = '';
let eventSource = null;
let isScanning = false;

// Default WhatsApp Pitch Templates (Optimized for Gunadarma Fresh Graduate Freelancer)
const PITCH_PRESETS = {
  website: `Halo kak, salam kenal! 👋

Perkenalkan saya {pengirim}, freelance web developer fresh graduate jurusan Informatika dari Universitas Gunadarma.

Saya melihat profil {nama} ({kategori}) di Google Maps {kota}. Tempatnya sangat menarik & ulasan pelanggan sangat positif! 

Saya perhatikan {nama} saat ini belum memiliki website profil & katalog menu online resmi untuk pelanggan yang mencari info lewat Google. 

Projek website ini saya kembangkan berdua bersama rekan partner saya. Untuk memberikan gambaran yang jelas dan membangun rasa percaya, kami telah menyiapkan rancangan beberapa fitur yang sangat bermanfaat untuk {nama}, yang kami lampirkan secara lengkap di dalam dokumen project plan.

Untuk melihat riwayat pendidikan & background profesional saya agar saling percaya, Kakak dapat mengunjungi profil LinkedIn saya di:
🔗 {linkedin}

Apakah boleh kami kirimkan draf project plan yang memuat rincian fitur-fitur tersebut secara gratis tanpa komitmen kak? 

Terima kasih banyak dan sukses selalu untuk {nama}! 🙏`,

  qr_menu: `Halo tim {nama}, salam kenal! 👋

Perkenalkan saya {pengirim}, freelance web developer fresh graduate Informatika Universitas Gunadarma.

Saya melihat usaha {kategori} {nama} di {kota} sangat potensial dan memiliki banyak pelanggan setia.

Projek ini saya kembangkan berdua bersama rekan partner saya. Untuk membangun rasa percaya dan transparansi, kami telah merancang beberapa fitur sistem menu praktis untuk operasional {nama}, yang kami lampirkan secara terstruktur di dalam dokumen project plan.

Untuk referensi kredibilitas dan background saya, silakan cek profil LinkedIn saya di sini:
🔗 {linkedin}

Boleh kami kirimkan draf project plan yang memuat rincian fitur-fiturnya secara singkat kak? Terima kasih banyak dan sukses selalu untuk {nama}! 🙏`,

  seo: `Halo tim {nama}, salam hangat! 👋

Saya {pengirim}, freelance web developer fresh graduate Informatika dari Universitas Gunadarma. Projek ini kami kerjakan berdua bersama rekan partner saya.

Saya melihat listing {nama} di Google Maps {kota} sudah memiliki reputasi ulasan yang sangat bagus, namun belum terhubung ke website profil resmi untuk mempermudah calon pelanggan melihat menu dan info lengkap.

Untuk membangun rasa percaya, kami telah menyiapkan rancangan beberapa fitur optimasi profil yang kami lampirkan secara rinci di dalam dokumen project plan.

Sebagai bahan pertimbangan dan referensi background profesional saya, Kakak dapat melihat profil LinkedIn saya di:
🔗 {linkedin}

Boleh kami kirimkan draf project plan yang memuat rancangan fiturnya secara gratis tanpa komitmen untuk {nama}? Terima kasih banyak! 🙏`
};

let userLinkedin = localStorage.getItem('userLinkedin') || 'https://www.linkedin.com/in/username-anda';
let userName = localStorage.getItem('userName') || 'Freelancer';

// Template initialization: upgrade legacy templates to Gunadarma features & project plan persona
let storedTemplate = localStorage.getItem('pitchTemplate');
if (!storedTemplate || storedTemplate.includes('Modern') || storedTemplate.includes('preview demo') || storedTemplate.includes('memiliki website profil dan katalog menu yang terhubung') || storedTemplate.includes('Kami dari agensi web development') || storedTemplate.includes('Halo manajer / owner {nama}')) {
  storedTemplate = PITCH_PRESETS.website;
  localStorage.setItem('pitchTemplate', storedTemplate);
}
let activePitchTemplate = storedTemplate;

// DOM Elements
const scanForm = document.getElementById('scanForm');
const btnStartScan = document.getElementById('btnStartScan');
const btnStopScan = document.getElementById('btnStopScan');
const scanTracker = document.getElementById('scanTracker');
const trackerText = document.getElementById('trackerText');
const trackerPercent = document.getElementById('trackerPercent');
const trackerBar = document.getElementById('trackerBar');
const terminalLogs = document.getElementById('terminalLogs');

const statTotal = document.getElementById('statTotal');
const statNoWeb = document.getElementById('statNoWeb');
const statSocialOnly = document.getElementById('statSocialOnly');
const statWhatsApp = document.getElementById('statWhatsApp');
const resultsCountBadge = document.getElementById('resultsCountBadge');

const leadsTableBody = document.getElementById('leadsTableBody');
const searchInput = document.getElementById('searchInput');
const filterTabs = document.querySelectorAll('.filter-tab');

const btnExportExcel = document.getElementById('btnExportExcel');
const btnExportCsv = document.getElementById('btnExportCsv');
const btnCopyAllWa = document.getElementById('btnCopyAllWa');
const btnClearAll = document.getElementById('btnClearAll');

const pitchModal = document.getElementById('pitchModal');
const btnOpenPitchModal = document.getElementById('btnOpenPitchModal');
const btnClosePitchModal = document.getElementById('btnClosePitchModal');
const pitchTemplateText = document.getElementById('pitchTemplateText');
const btnSaveTemplate = document.getElementById('btnSaveTemplate');
const toastEl = document.getElementById('toast');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initSSE();
  fetchStats();
  fetchLeads();
  initEventListeners();
  pitchTemplateText.value = activePitchTemplate;

  const userLinkedinInput = document.getElementById('userLinkedinInput');
  const userNameInput = document.getElementById('userNameInput');
  if (userLinkedinInput) userLinkedinInput.value = userLinkedin;
  if (userNameInput) userNameInput.value = userName;
});

// Toast Notification
function showToast(message, duration = 3000) {
  toastEl.textContent = message;
  toastEl.style.display = 'block';
  setTimeout(() => {
    toastEl.style.display = 'none';
  }, duration);
}

// SSE Connection for Live Progress
function initSSE() {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = new EventSource('/api/stream');

  eventSource.addEventListener('ping', (e) => {
    // console.log("SSE connected");
  });

  eventSource.addEventListener('log', (e) => {
    const data = JSON.parse(e.data);
    appendTerminalLog(data.message);
  });

  eventSource.addEventListener('status', (e) => {
    const data = JSON.parse(e.data);
    if (data.message) trackerText.textContent = data.message;
    if (typeof data.progress === 'number') {
      trackerPercent.textContent = `${data.progress}%`;
      trackerBar.style.width = `${data.progress}%`;
    }
  });

  eventSource.addEventListener('lead_found', (e) => {
    const lead = JSON.parse(e.data);
    // Prepend to table and refresh stats
    addLeadToTable(lead, true);
    fetchStats();
  });

  eventSource.addEventListener('completed', (e) => {
    const data = JSON.parse(e.data);
    isScanning = false;
    updateScanUI(false);
    appendTerminalLog(`✅ Pemindaian selesai! Berhasil menemukan ${data.total_found} tempat (${data.no_website_count} prospek tanpa website, ${data.with_wa_count} kontak WhatsApp).`);
    showToast(`Pemindaian selesai: ${data.total_found} tempat terdata!`);
    fetchStats();
    fetchLeads();
  });

  eventSource.addEventListener('error', (e) => {
    // Handle error or auto-reconnect
  });
}

function appendTerminalLog(message) {
  const line = document.createElement('div');
  line.className = 'log-line';
  const time = new Date().toLocaleTimeString('id-ID', { hour12: false });
  line.textContent = `[${time}] ${message}`;
  terminalLogs.appendChild(line);
  terminalLogs.scrollTop = terminalLogs.scrollHeight;
}

// Fetch Leads from Backend
async function fetchLeads() {
  try {
    const params = new URLSearchParams();
    if (currentFilter === 'no_website') params.append('filter_no_website', 'true');
    if (currentFilter === 'whatsapp') params.append('only_with_whatsapp', 'true');
    if (currentSearch) params.append('search', currentSearch);

    const res = await fetch(`/api/leads?${params.toString()}`);
    const data = await res.json();
    renderLeads(data.leads);
    resultsCountBadge.textContent = `${data.count} Bisnis`;
  } catch (err) {
    console.error("Gagal memuat data leads:", err);
  }
}

// Fetch Stats from Backend
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    statTotal.textContent = data.total || 0;
    statNoWeb.textContent = data.no_website || 0;
    statSocialOnly.textContent = data.social_only || 0;
    statWhatsApp.textContent = data.with_whatsapp || 0;
  } catch (err) {
    console.error("Gagal memuat statistik:", err);
  }
}

// Render Leads Table
function renderLeads(leads) {
  cachedLeadsMap = {};
  if (!leads || leads.length === 0) {
    leadsTableBody.innerHTML = `
      <tr class="empty-row">
        <td colspan="6">
          <div class="empty-state">
            <i data-lucide="map-pin-off" class="empty-icon"></i>
            <h4>Tidak ada bisnis yang cocok</h4>
            <p>Belum ada data atau coba ubah kata kunci filter pencarian.</p>
          </div>
        </td>
      </tr>
    `;
    lucide.createIcons();
    return;
  }

  leadsTableBody.innerHTML = '';
  leads.forEach(lead => {
    if (lead.id) cachedLeadsMap[lead.id] = lead;
    leadsTableBody.appendChild(createLeadRow(lead));
  });
  lucide.createIcons();
}

function addLeadToTable(lead, prepend = false) {
  if (lead.id) cachedLeadsMap[lead.id] = lead;
  
  // Check if empty state is showing
  const emptyRow = leadsTableBody.querySelector('.empty-row');
  if (emptyRow) {
    leadsTableBody.innerHTML = '';
  }

  const row = createLeadRow(lead);
  if (prepend && leadsTableBody.firstChild) {
    leadsTableBody.insertBefore(row, leadsTableBody.firstChild);
  } else {
    leadsTableBody.appendChild(row);
  }
  lucide.createIcons();
}

function createLeadRow(lead) {
  const tr = document.createElement('tr');
  tr.id = `lead-${lead.id || 'new'}`;

  // Website status badge
  let statusBadgeHtml = '';
  if (lead.website_type === 'none') {
    statusBadgeHtml = `<span class="status-badge status-none"><i data-lucide="x-circle"></i> Belum Ada Website</span>`;
  } else if (lead.website_type === 'social_only') {
    statusBadgeHtml = `
      <span class="status-badge status-social"><i data-lucide="alert-circle"></i> Hanya Medsos</span>
      <a href="${lead.website_url}" target="_blank" class="web-link">${escapeHtml(lead.website_url.substring(0, 30))}...</a>
    `;
  } else {
    statusBadgeHtml = `
      <span class="status-badge status-website"><i data-lucide="check-circle-2"></i> Ada Website</span>
      <a href="${lead.website_url}" target="_blank" class="web-link">${escapeHtml(lead.website_url.substring(0, 30))}...</a>
    `;
  }

  // Phone / WhatsApp
  let phoneHtml = '';
  if (lead.is_mobile && lead.whatsapp_number) {
    phoneHtml = `
      <div class="phone-box">
        <span class="phone-number">${formatIndoPhone(lead.whatsapp_number)}</span>
        <span class="wa-active-pill"><i data-lucide="check"></i> WA Aktif</span>
      </div>
    `;
  } else if (lead.phone_raw) {
    phoneHtml = `
      <div class="phone-box">
        <span class="phone-number">${escapeHtml(lead.phone_raw)}</span>
        <span class="no-phone-text">Telp Kantor</span>
      </div>
    `;
  } else {
    phoneHtml = `<span class="no-phone-text">Tidak ada nomor</span>`;
  }

  // Rating
  const ratingScore = lead.rating ? lead.rating.toFixed(1) : '-';
  const reviewsCount = lead.reviews_count ? `(${lead.reviews_count.toLocaleString('id-ID')} ulasan)` : '';
  const ratingHtml = `
    <div class="rating-box">
      <i data-lucide="star" class="star-icon"></i>
      <span class="rating-score">${ratingScore}</span>
      <span class="review-count">${reviewsCount}</span>
    </div>
  `;

  // WhatsApp Pitch Link
  let waActionHtml = '';
  if (lead.is_mobile && lead.whatsapp_number) {
    const personalizedPitch = generatePitchMessage(lead);
    const waUrl = `https://wa.me/${lead.whatsapp_number}?text=${encodeURIComponent(personalizedPitch)}`;
    const demoUrl = `/demo?name=${encodeURIComponent(lead.name || '')}&category=${encodeURIComponent(lead.category || '')}&city=${encodeURIComponent(lead.city || '')}&phone=${encodeURIComponent(lead.whatsapp_number || lead.phone_raw || '')}&address=${encodeURIComponent(lead.address || '')}`;

    // AI Pitch Button
    const aiDraftBtn = `
      <button onclick="handleOpenAiStudio(${lead.id || 0})" class="btn-ai-draft" title="Buat Draf Pesan Unik dengan AI">
        <i data-lucide="sparkles"></i>
        <span>AI Draft</span>
      </button>
    `;

    const demoBtn = `
      <a href="${demoUrl}" target="_blank" class="btn-demo-web" title="Lihat Contoh Website Demo Khusus Kafe Ini">
        <i data-lucide="globe"></i>
        <span>Demo Web</span>
      </a>
    `;

    waActionHtml = `
      <div style="display: inline-flex; gap: 6px; align-items: center;">
        ${demoBtn}
        ${aiDraftBtn}
        <a href="${waUrl}" target="_blank" class="btn-wa-direct" title="Kirim Chat WhatsApp Langsung">
          <i data-lucide="message-circle"></i>
          <span>Chat WA</span>
        </a>
      </div>
    `;
  } else {
    waActionHtml = `
      <button class="btn-wa-direct btn-wa-disabled" disabled title="Nomor WhatsApp tidak tersedia">
        <i data-lucide="message-circle"></i>
        <span>Chat WA</span>
      </button>
    `;
  }

  tr.innerHTML = `
    <td>
      <div class="lead-title-box">
        <span class="lead-name">${escapeHtml(lead.name)}</span>
        <span class="lead-cat-pill">${escapeHtml(lead.category || 'F&B')}</span>
      </div>
    </td>
    <td>${statusBadgeHtml}</td>
    <td>${phoneHtml}</td>
    <td>${ratingHtml}</td>
    <td>
      <span class="address-text" title="${escapeHtml(lead.address || '')}">
        ${escapeHtml(lead.address || 'Alamat tidak tersedia')}
      </span>
    </td>
    <td>
      <div class="action-group">
        ${waActionHtml}
        ${lead.maps_url ? `
          <a href="${lead.maps_url}" target="_blank" class="btn-icon-link" title="Buka di Google Maps">
            <i data-lucide="external-link"></i>
          </a>
        ` : ''}
        ${lead.id ? `
          <button onclick="handleDeleteLead(${lead.id})" class="btn-icon-link text-danger" title="Hapus profil">
            <i data-lucide="trash"></i>
          </button>
        ` : ''}
      </div>
    </td>
  `;

  return tr;
}

function formatIndoPhone(num) {
  if (!num) return '-';
  // 6281234567890 -> +62 812-3456-7890
  const s = String(num);
  if (s.startsWith('628')) {
    return `+62 ${s.substring(2, 5)}-${s.substring(5, 9)}-${s.substring(9)}`;
  }
  return s;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function generatePitchMessage(lead) {
  let text = activePitchTemplate;
  text = text.replace(/\{nama\}/g, lead.name || 'Bapak/Ibu');
  text = text.replace(/\{kategori\}/g, lead.category || 'kuliner');
  text = text.replace(/\{kota\}/g, lead.city || 'kota Anda');
  text = text.replace(/\{linkedin\}/g, userLinkedin);
  text = text.replace(/\{pengirim\}/g, userName);
  return text;
}

// Event Listeners
function initEventListeners() {
  // Start Scan
  scanForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isScanning) return;

    const keyword = document.getElementById('keyword').value.trim();
    const city = document.getElementById('city').value.trim();
    const maxResults = parseInt(document.getElementById('maxResults').value, 10);
    const filterNoWebOnly = document.getElementById('filterNoWebOnly').checked;

    if (!keyword) {
      alert("Masukkan kategori F&B!");
      return;
    }

    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword,
          city,
          max_results: maxResults,
          filter_no_website_only: filterNoWebOnly
        })
      });

      if (!res.ok) {
        const data = await res.json();
        alert(data.error || "Gagal memulai scanning.");
        return;
      }

      isScanning = true;
      updateScanUI(true);
      terminalLogs.innerHTML = '';
      appendTerminalLog(`🚀 Memulai pemindaian Google Maps untuk "${keyword} di ${city}"...`);
      showToast(`Deteksi dimulai untuk ${city}...`);
    } catch (err) {
      console.error(err);
      alert("Terjadi kesalahan saat memicu scan.");
    }
  });

  // Stop Scan
  btnStopScan.addEventListener('click', async () => {
    try {
      await fetch('/api/stop', { method: 'POST' });
      isScanning = false;
      updateScanUI(false);
      showToast("Pemindaian dihentikan.");
    } catch (err) {
      console.error(err);
    }
  });

  // Filter Tabs
  filterTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      filterTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentFilter = tab.dataset.filter;
      fetchLeads();
    });
  });

  // Search Input (Debounced)
  let debounceTimer;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      currentSearch = e.target.value.trim();
      fetchLeads();
    }, 300);
  });

  // Export Excel
  btnExportExcel.addEventListener('click', () => {
    const params = new URLSearchParams();
    if (currentFilter === 'no_website') params.append('filter_no_website', 'true');
    if (currentFilter === 'whatsapp') params.append('only_with_whatsapp', 'true');
    window.location.href = `/api/export/excel?${params.toString()}`;
    showToast("Mengunduh spreadsheet Excel...");
  });

  // Export CSV
  btnExportCsv.addEventListener('click', () => {
    const params = new URLSearchParams();
    if (currentFilter === 'no_website') params.append('filter_no_website', 'true');
    if (currentFilter === 'whatsapp') params.append('only_with_whatsapp', 'true');
    window.location.href = `/api/export/csv?${params.toString()}`;
    showToast("Mengunduh data CSV...");
  });

  // Copy All WhatsApp Numbers
  btnCopyAllWa.addEventListener('click', async () => {
    try {
      const params = new URLSearchParams();
      if (currentFilter === 'no_website') params.append('filter_no_website', 'true');
      params.append('only_with_whatsapp', 'true');
      if (currentSearch) params.append('search', currentSearch);

      const res = await fetch(`/api/leads?${params.toString()}`);
      const data = await res.json();
      const numbers = data.leads
        .filter(l => l.whatsapp_number && l.is_mobile)
        .map(l => l.whatsapp_number);

      if (numbers.length === 0) {
        showToast("Tidak ada nomor WhatsApp yang valid.");
        return;
      }

      await navigator.clipboard.writeText(numbers.join('\n'));
      showToast(`Berhasil menyalin ${numbers.length} nomor WhatsApp ke clipboard!`);
    } catch (err) {
      console.error(err);
      showToast("Gagal menyalin nomor WhatsApp.");
    }
  });

  // Clear Database
  btnClearAll.addEventListener('click', async () => {
    if (confirm("Apakah Anda yakin ingin menghapus seluruh data hasil scan?")) {
      await fetch('/api/leads/clear', { method: 'POST' });
      fetchStats();
      fetchLeads();
      showToast("Database berhasil dikosongkan.");
    }
  });

  // Pitch Modal
  btnOpenPitchModal.addEventListener('click', () => {
    pitchModal.style.display = 'flex';
  });

  btnClosePitchModal.addEventListener('click', () => {
    pitchModal.style.display = 'none';
  });

  pitchModal.addEventListener('click', (e) => {
    if (e.target === pitchModal) pitchModal.style.display = 'none';
  });

  // Preset Buttons
  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const presetKey = btn.dataset.preset;
      if (PITCH_PRESETS[presetKey]) {
        pitchTemplateText.value = PITCH_PRESETS[presetKey];
      }
    });
  });

  // Save Template, Profile & Gemini API Key
  btnSaveTemplate.addEventListener('click', () => {
    activePitchTemplate = pitchTemplateText.value.trim();
    localStorage.setItem('pitchTemplate', activePitchTemplate);
    
    const linkedinInput = document.getElementById('userLinkedinInput');
    if (linkedinInput) {
      userLinkedin = linkedinInput.value.trim() || 'https://www.linkedin.com/in/username-anda';
      localStorage.setItem('userLinkedin', userLinkedin);
    }

    const nameInput = document.getElementById('userNameInput');
    if (nameInput) {
      userName = nameInput.value.trim() || 'Freelancer';
      localStorage.setItem('userName', userName);
    }

    const geminiKey = document.getElementById('geminiApiKeyInput').value.trim();
    localStorage.setItem('geminiApiKey', geminiKey);
    
    pitchModal.style.display = 'none';
    showToast("Profil, LinkedIn, dan template berhasil disimpan!");
    fetchLeads();
  });

  // Reset Template to Default Gunadarma Persona
  const btnReset = document.getElementById('btnResetPitchTemplate');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      pitchTemplateText.value = PITCH_PRESETS.website;
      document.querySelectorAll('.preset-buttons .btn-preset').forEach(b => b.classList.remove('active'));
      const defaultBtn = document.querySelector('.preset-buttons .btn-preset[data-preset="website"]');
      if (defaultBtn) defaultBtn.classList.add('active');
      showToast("Template direset ke persona Fresh Graduate Gunadarma.");
    });
  }

  // Load saved Gemini Key if exists
  const savedGeminiKey = localStorage.getItem('geminiApiKey') || '';
  const geminiInput = document.getElementById('geminiApiKeyInput');
  if (geminiInput) geminiInput.value = savedGeminiKey;

  // AI Modal Controls
  initAiStudioEvents();
}

// Global state for AI Studio
let activeAiLead = null;
let currentAiGoal = 'website';
let cachedLeadsMap = {};

function initAiStudioEvents() {
  const aiModal = document.getElementById('aiPitchModal');
  const btnCloseAi = document.getElementById('btnCloseAiModal');
  const btnCopyAi = document.getElementById('btnCopyAiDraft');
  const btnRegenAi = document.getElementById('btnRegenerateAi');
  const goalButtons = document.querySelectorAll('.ai-goal-btn');

  btnCloseAi.addEventListener('click', () => {
    aiModal.style.display = 'none';
  });

  aiModal.addEventListener('click', (e) => {
    if (e.target === aiModal) aiModal.style.display = 'none';
  });

  goalButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      goalButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentAiGoal = btn.dataset.goal;
      triggerGenerateAiPitch();
    });
  });

  btnRegenAi.addEventListener('click', () => {
    triggerGenerateAiPitch();
  });

  btnCopyAi.addEventListener('click', async () => {
    const text = document.getElementById('aiDraftResult').value;
    if (text) {
      await navigator.clipboard.writeText(text);
      showToast("Pesan AI berhasil disalin ke clipboard!");
    }
  });

  // When text is edited, update the direct WA link
  document.getElementById('aiDraftResult').addEventListener('input', (e) => {
    updateSendToWaLink(e.target.value);
  });
}

async function handleOpenAiStudio(leadId) {
  // Find lead in current table or cached map
  const lead = cachedLeadsMap[leadId];
  if (!lead) return;

  activeAiLead = lead;
  const aiModal = document.getElementById('aiPitchModal');
  const targetLabel = document.getElementById('aiTargetBusiness');
  
  targetLabel.textContent = `Menulis untuk: ${lead.name} (${lead.category || 'F&B'}) • ${lead.city || ''}`;
  
  // Set demo link button inside AI Studio
  const demoUrl = `/demo?name=${encodeURIComponent(lead.name || '')}&category=${encodeURIComponent(lead.category || '')}&city=${encodeURIComponent(lead.city || '')}&phone=${encodeURIComponent(lead.whatsapp_number || lead.phone_raw || '')}&address=${encodeURIComponent(lead.address || '')}`;
  const btnViewDemo = document.getElementById('btnAiViewDemo');
  if (btnViewDemo) {
    btnViewDemo.href = demoUrl;
  }

  // Update LinkedIn preview in AI Modal
  const aiLinkedinText = document.getElementById('aiActiveLinkedinText');
  if (aiLinkedinText) {
    aiLinkedinText.textContent = userLinkedin;
    aiLinkedinText.title = userLinkedin;
  }

  aiModal.style.display = 'flex';
  lucide.createIcons();

  triggerGenerateAiPitch();
}

async function triggerGenerateAiPitch() {
  if (!activeAiLead) return;

  const overlay = document.getElementById('aiLoadingOverlay');
  const textarea = document.getElementById('aiDraftResult');
  const apiKey = localStorage.getItem('geminiApiKey') || '';

  overlay.style.display = 'flex';

  try {
    const res = await fetch('/api/ai/pitch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lead: activeAiLead,
        api_key: apiKey,
        goal: currentAiGoal,
        linkedin_url: userLinkedin,
        sender_name: userName
      })
    });

    const data = await res.json();
    textarea.value = data.pitch || '';
    updateSendToWaLink(data.pitch || '');
  } catch (err) {
    console.error("Gagal generate AI pitch:", err);
    textarea.value = generatePitchMessage(activeAiLead);
    updateSendToWaLink(textarea.value);
  } finally {
    overlay.style.display = 'none';
  }
}

function updateSendToWaLink(messageText) {
  const btnSend = document.getElementById('btnSendAiToWa');
  if (!activeAiLead || !activeAiLead.whatsapp_number) {
    btnSend.style.display = 'none';
    return;
  }
  btnSend.style.display = 'inline-flex';
  const url = `https://wa.me/${activeAiLead.whatsapp_number}?text=${encodeURIComponent(messageText)}`;
  btnSend.href = url;
}

function updateScanUI(scanning) {
  if (scanning) {
    btnStartScan.style.display = 'none';
    btnStopScan.style.display = 'inline-flex';
    scanTracker.style.display = 'block';
    trackerPercent.textContent = '0%';
    trackerBar.style.width = '0%';
    trackerText.textContent = 'Menghubungkan ke Google Maps...';
  } else {
    btnStartScan.style.display = 'inline-flex';
    btnStopScan.style.display = 'none';
  }
}

async function handleDeleteLead(leadId) {
  if (confirm("Hapus data bisnis ini?")) {
    try {
      await fetch(`/api/leads/${leadId}`, { method: 'DELETE' });
      const row = document.getElementById(`lead-${leadId}`);
      if (row) row.remove();
      delete cachedLeadsMap[leadId];
      fetchStats();
      showToast("Profil berhasil dihapus.");
    } catch (err) {
      console.error(err);
    }
  }
}

function insertVariable(varName) {
  const textarea = pitchTemplateText;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const val = textarea.value;
  textarea.value = val.substring(0, start) + varName + val.substring(end);
  textarea.focus();
  textarea.selectionStart = textarea.selectionEnd = start + varName.length;
}
