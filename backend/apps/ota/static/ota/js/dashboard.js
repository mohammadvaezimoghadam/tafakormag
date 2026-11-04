    const BASE_PATH = window.location.pathname.startsWith('/ota') ? '/ota' : (window.location.pathname.startsWith('/patcher') ? '/patcher' : '');

    let currentAppId = '{{ current_app.app_id|default:"" }}';
    let appsList = [];
    let selectedFile = null;
    let allPatchesData = [];

    const VIEWS = {
      dashboard: { title: 'داشبورد و وضعیت زنده', icon: 'dashboard', pageTitle: 'داشبورد و وضعیت زنده' },
      publisher: { title: 'انتشار پچ جدید فلاتر', icon: 'cloud_upload', pageTitle: 'انتشار پچ جدید' },
      rollback: { title: 'تاریخچه نسخه‌ها و رول‌بک', icon: 'history', pageTitle: 'تاریخچه و رول‌بک' },
      releases: { title: 'انتشار و مدیریت ریلیزهای APK', icon: 'android', pageTitle: 'مدیریت ریلیزهای APK' },
      apps: { title: 'مدیریت اپلیکیشن‌ها', icon: 'apps', pageTitle: 'مدیریت اپلیکیشن‌ها' }
    };

    function switchView(viewName, updateHistory = true) {
      if (!VIEWS[viewName]) viewName = 'dashboard';

      // 1. Hide all view containers
      document.querySelectorAll('.view-tab').forEach(el => {
        el.classList.add('hidden');
      });

      // 2. Show the targeted view
      const target = document.getElementById('view-' + viewName);
      if (target) {
        target.classList.remove('hidden');
      }

      // 3. Highlight the active link in the sidebar
      document.querySelectorAll('#sidebar-nav .nav-link').forEach(btn => {
        const v = btn.getAttribute('data-view');
        if (v === viewName) {
          btn.className = 'nav-link flex items-center justify-between px-3 py-2.5 rounded-xl bg-blue-600 text-white shadow-xs font-bold text-xs text-right w-full transition-all';
        } else {
          btn.className = 'nav-link flex items-center justify-between px-3 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-xs font-semibold text-right w-full';
        }
      });

      // 4. Update Header Badge & Document Title
      const pageBadge = document.getElementById('current-page-badge');
      if (pageBadge) {
        pageBadge.innerHTML = `<span class="material-symbols-outlined text-[19px] text-blue-600">${VIEWS[viewName].icon}</span><span>${VIEWS[viewName].title}</span>`;
      }
      document.title = `فلاتر او‌تی‌ای | ${VIEWS[viewName].pageTitle}`;

      // 5. Update URL Hash / History
      if (updateHistory) {
        try {
          history.replaceState(null, '', '#' + viewName);
        } catch (e) {
          window.location.hash = viewName;
        }
      }

      // 6. Close mobile drawer if opened
      const sb = document.getElementById('main-sidebar');
      if (sb && !sb.classList.contains('translate-x-full')) {
        sb.classList.add('translate-x-full');
      }

      // 7. Smoothly scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });

      // 8. Refresh view-specific contents
      if (viewName === 'rollback') {
        loadPatches();
      } else if (viewName === 'releases') {
        if(typeof loadReleases === 'function') loadReleases();
      } else if (viewName === 'apps') {
        renderAppsCards();
      }
    }

    function resolveInitialView() {
      const hash = window.location.hash.replace('#', '').trim();
      if (hash && VIEWS[hash]) return hash;

      const pathSegments = window.location.pathname.split('/').filter(Boolean);
      const last = pathSegments.length > 0 ? pathSegments[pathSegments.length - 1] : '';
      if (last && VIEWS[last]) return last;

      return 'dashboard';
    }

    // Toast Notification System
    function showToast(msg, type = 'info') {
      const container = document.getElementById('toast-container');
      if (!container) return;
      const t = document.createElement('div');
      const bg = type === 'success' 
        ? 'bg-slate-900 text-emerald-400 border-emerald-500/50' 
        : type === 'error' 
        ? 'bg-red-700 text-white border-red-800' 
        : 'bg-slate-900 text-white border-slate-700';
      const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
      t.className = `pointer-events-auto px-4 py-2.5 rounded-xl shadow-lg border text-xs flex items-center gap-2 transition-all duration-300 ${bg}`;
      t.innerHTML = `<span class="material-symbols-outlined text-[18px]">${icon}</span><span>${msg}</span>`;
      container.appendChild(t);
      setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 300);
      }, 3500);
    }

    // Lifecycle Init
    window.addEventListener('DOMContentLoaded', () => {
      loadStatus();
      loadApps();
      setupDragDrop();
      setupReleaseDragDrop();

      const initView = resolveInitialView();
      switchView(initView, false);

      window.addEventListener('hashchange', () => {
        const h = window.location.hash.replace('#', '').trim();
        if (h && VIEWS[h]) {
          switchView(h, false);
        }
      });
    });

    function setupDragDrop() {
      const dz = document.getElementById('drop-zone');
      if (!dz) return;
      dz.addEventListener('dragover', (e) => {
        e.preventDefault();
        dz.classList.add('bg-blue-50/70', 'border-blue-400');
      });
      dz.addEventListener('dragleave', () => {
        dz.classList.remove('bg-blue-50/70', 'border-blue-400');
      });
      dz.addEventListener('drop', (e) => {
        e.preventDefault();
        dz.classList.remove('bg-blue-50/70', 'border-blue-400');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleFileChange(e.dataTransfer.files);
        }
      });
    }

    function handleFileChange(files) {
      if (!files || files.length === 0) return;
      selectedFile = files[0];
      const badge = document.getElementById('selected-file-badge');
      const nameEl = document.getElementById('selected-file-name');
      const sizeEl = document.getElementById('selected-file-size');
      nameEl.textContent = selectedFile.name;
      sizeEl.textContent = `سایز: ${(selectedFile.size / (1024 * 1024)).toFixed(2)} مگابایت`;
      badge.style.display = 'flex';

      // تشخیص هوشمند نام فایل برای پیشنهاد خودکار دستگاه مقصد
      const fname = selectedFile.name.toLowerCase();
      const abiSelect = document.getElementById('select-target-abi');
      if (abiSelect) {
        if (fname.includes('x86_64') || fname.includes('emulator')) {
          abiSelect.value = 'x86_64';
        } else if (fname.includes('arm64')) {
          abiSelect.value = 'arm64-v8a';
        } else if (fname.includes('armeabi')) {
          abiSelect.value = 'armeabi-v7a';
        } else if (fname.includes('multi')) {
          abiSelect.value = 'multi';
        }
      }
      showToast(`فایل ${selectedFile.name} با موفقیت انتخاب شد.`, 'success');
    }

    async function loadStatus() {
      try {
        const res = await fetch(`${BASE_PATH}/api/status`);
        const data = await res.json();
        const hostIp = (data.ips && data.ips.length > 0) ? data.ips[0] : '127.0.0.1';
        document.getElementById('serverHostInfo').textContent = `Host: ${hostIp}:${data.port}`;
      } catch (e) {
        console.error('Failed to load status', e);
      }
    }

    async function loadApps() {
      try {
        const res = await fetch(`${BASE_PATH}/api/apps`);
        appsList = await res.json();
        
        // Ensure currentAppId exists
        if (!appsList.find(a => a.app_id === currentAppId) && appsList.length > 0) {
          currentAppId = appsList[0].app_id;
        }

        renderCurrentAppBanner();
        loadPatches();
        renderAppsCards();
      } catch (e) {
        showToast('خطا در دریافت لیست برنامه‌ها: ' + e, 'error');
      }
    }

    function resolveAppIcon(app) {
      if (!app) return '';
      let icon = app.icon_url || '';
      if (icon && icon.startsWith('/') && BASE_PATH) {
        icon = BASE_PATH + icon;
      }
      return icon;
    }

    function renderCurrentAppBanner() {
      const app = appsList.find(a => a.app_id === currentAppId) || (appsList.length > 0 ? appsList[0] : null);
      if (!app) {
        const hName = document.getElementById('header-app-name');
        if (hName) hName.textContent = 'برنامه‌ای ثبت نشده';
        const rName = document.getElementById('ribbon-app-name');
        if (rName) rName.textContent = 'هیچ برنامه‌ای ثبت نشده است';
        const rPkg = document.getElementById('ribbon-app-pkg');
        if (rPkg) rPkg.textContent = '';
        const rId = document.getElementById('ribbon-app-id');
        if (rId) rId.textContent = '-';
        const sName = document.getElementById('sidebar-app-name');
        if (sName) sName.textContent = 'برنامه‌ای ثبت نشده';
        const sPkg = document.getElementById('sidebar-app-pkg');
        if (sPkg) sPkg.textContent = '-';
        const testLink = document.getElementById('stat-test-link');
        if (testLink) {
          testLink.href = '#';
          testLink.textContent = '-';
        }
        const ribbonAvatar = document.getElementById('active-app-avatar');
        if (ribbonAvatar) ribbonAvatar.innerHTML = '<span class="material-symbols-outlined text-[24px] text-slate-400">apps</span>';
        const sAvatar = document.getElementById('sidebar-app-avatar');
        if (sAvatar) sAvatar.innerHTML = '<span class="material-symbols-outlined text-[18px] text-slate-400">apps</span>';
        return;
      }

      const iconSrc = resolveAppIcon(app);
      document.getElementById('header-app-name').textContent = app.name;

      const ribbonAvatar = document.getElementById('active-app-avatar');
      if (ribbonAvatar) {
        if (iconSrc) {
          ribbonAvatar.innerHTML = `<img src="${iconSrc}" alt="${app.name}" class="app-icon-img" style="width: 100%; height: 100%; object-fit: cover; display: block; border-radius: inherit;">`;
        } else {
          ribbonAvatar.textContent = app.name.substring(0, 2);
        }
      }

      const sAvatar = document.getElementById('sidebar-app-avatar');
      if (sAvatar) {
        if (iconSrc) {
          sAvatar.innerHTML = `<img src="${iconSrc}" alt="${app.name}" class="app-icon-img" style="width: 100%; height: 100%; object-fit: cover; display: block; border-radius: inherit;">`;
        } else {
          sAvatar.textContent = app.name.substring(0, 2);
        }
      }

      document.getElementById('ribbon-app-name').textContent = app.name;
      document.getElementById('ribbon-app-pkg').textContent = `(${app.package_name})`;
      document.getElementById('ribbon-app-id').textContent = app.app_id;
      document.getElementById('ribbon-total-patches').textContent = `${app.total_patches || 0} نسخه`;
      document.getElementById('stat-patch-count').textContent = app.total_patches || 0;

      // Update Sidebar App Info
      const sName = document.getElementById('sidebar-app-name');
      if (sName) sName.textContent = app.name;
      const sPkg = document.getElementById('sidebar-app-pkg');
      if (sPkg) sPkg.textContent = app.package_name;

      // Update test link
      const testLink = document.getElementById('stat-test-link');
      testLink.href = `${BASE_PATH}/check?app_id=${app.app_id}`;
      testLink.textContent = `/check?app_id=${app.app_id}`;
    }

    function toggleSidebar() {
      const sb = document.getElementById('main-sidebar');
      if (!sb) return;
      sb.classList.toggle('translate-x-full');
    }

    function filterPatchesTable() {
      const q = (document.getElementById('search-patches')?.value || '').trim().toLowerCase();
      const filtered = allPatchesData.filter(p => {
        if (!q) return true;
        return (p.version && p.version.toLowerCase().includes(q)) ||
               (p.release_notes && p.release_notes.toLowerCase().includes(q)) ||
               (p.md5 && p.md5.toLowerCase().includes(q)) ||
               String(p.target_version_code).includes(q);
      });
      renderPatchesTable(filtered);
    }

    function getAbiBadge(abi) {
      if (abi === 'arm64-v8a') {
        return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200 inline-flex items-center gap-1">📱 گوشی واقعی (ARM64)</span>`;
      } else if (abi === 'x86_64') {
        return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200 inline-flex items-center gap-1">💻 امولاتور (x86_64)</span>`;
      } else if (abi === 'armeabi-v7a') {
        return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200 inline-flex items-center gap-1">📱 ۳۲بیتی (ARMv7)</span>`;
      } else {
        return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1">🌐 همه دستگاه‌ها (Multi)</span>`;
      }
    }

    function renderDashboardRecentTable(patches) {
      const tbody = document.getElementById('dashboard-recent-table');
      if (!tbody) return;
      if (!patches || patches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400">هنوز هیچ پچی برای این برنامه ثبت نشده است.</td></tr>';
        return;
      }
      const recents = patches.slice(0, 5);
      tbody.innerHTML = recents.map(p => {
        const isActive = p.is_active === 1;
        const statusBadge = isActive 
          ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">فعال (Live)</span>`
          : `<span class="px-2 py-0.5 rounded text-[10px] text-slate-500 bg-slate-100 border border-slate-200">آرشیو</span>`;
        const policyBadge = p.is_force === 1
          ? `<span class="text-red-600 font-bold">اجباری</span>`
          : `<span class="text-slate-500">اختیاری</span>`;
        const sizeKb = (p.size_bytes / 1024).toFixed(1);

        return `
          <tr class="hover:bg-slate-50/70 transition-colors">
            <td class="py-2.5 px-3 font-mono font-bold text-blue-600" dir="ltr">v${p.version}</td>
            <td class="py-2.5 px-3 text-center">${statusBadge}</td>
            <td class="py-2.5 px-3 text-center">${getAbiBadge(p.target_abi)}</td>
            <td class="py-2.5 px-3 text-center">${policyBadge}</td>
            <td class="py-2.5 px-3 text-center font-mono">${p.target_version_code} (${sizeKb} KB)</td>
            <td class="py-2.5 px-3 text-slate-500 whitespace-nowrap">${p.created_at}</td>
            <td class="py-2.5 px-3 text-slate-600 truncate max-w-xs">${p.release_notes || '-'}</td>
          </tr>
        `;
      }).join('');
    }

    function renderPatchesTable(patches) {
      const tbody = document.getElementById('patches-table-body');
      if (!tbody) return;

      if (!patches || patches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-400">هیچ پچی یافت نشد. از تب «انتشار پچ جدید» اولین پچ را بارگذاری کنید.</td></tr>';
        return;
      }

      tbody.innerHTML = patches.map(p => {
        const isActive = p.is_active === 1;
        const isForce = p.is_force === 1;
        const sizeKb = (p.size_bytes / 1024).toFixed(1);
        const rowClass = isActive ? "bg-blue-50/40 font-semibold" : "hover:bg-slate-50";

        const statusBadge = isActive 
          ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>فعال</span>`
          : `<span class="px-2 py-0.5 rounded text-[11px] text-slate-500 bg-slate-100 border border-slate-200">آرشیو</span>`;

        const policyBadge = isForce 
          ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-red-100 text-red-700">اجباری</span>`
          : `<span class="px-2 py-0.5 rounded text-[11px] text-slate-600 bg-slate-100">اختیاری</span>`;

        return `
          <tr class="${rowClass} transition-colors">
            <td class="py-3 px-4">
              <div class="flex items-center gap-2">
                <span class="font-mono font-bold text-sm text-blue-600" dir="ltr">v${p.version}</span>
                ${statusBadge}
              </div>
            </td>
            <td class="py-3 px-3 text-center">
              <span class="font-mono text-slate-800 font-bold">بیلد ${p.target_version_code}</span>
              <span class="text-slate-400 text-[11px] block font-mono" dir="ltr">${sizeKb} KB</span>
            </td>
            <td class="py-3 px-3 text-center">${getAbiBadge(p.target_abi)}</td>
            <td class="py-3 px-3 text-center">${policyBadge}</td>
            <td class="py-3 px-4">
              <span class="text-slate-400 text-[11px] block">${p.created_at}</span>
              <span class="text-slate-700 truncate max-w-sm block" title="${p.release_notes || ''}">${p.release_notes || '-'}</span>
            </td>
            <td class="py-3 px-4 text-left whitespace-nowrap" dir="ltr">
              <div class="flex items-center gap-1.5 justify-end">
                ${!isActive ? `
                  <button class="h-7 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors flex items-center gap-1" onclick="activatePatch(${p.id})">
                    <span class="material-symbols-outlined text-[15px]">history</span>
                    <span>رول‌بک به این نسخه</span>
                  </button>
                ` : `
                  <span class="h-7 px-2.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-bold inline-flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                    <span>نسخه فعال جاری</span>
                  </span>
                `}
                <button class="h-7 px-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded-lg text-xs transition-colors" onclick="toggleForce(${p.id})">
                  ${isForce ? 'تغییر به اختیاری' : 'تغییر به اجباری'}
                </button>
                <button class="h-7 px-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" onclick="deletePatch(${p.id})" title="حذف پچ">
                  <span class="material-symbols-outlined text-[17px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    async function loadPatches() {
      const tbody = document.getElementById('patches-table-body');
      if (!currentAppId) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-400">ابتدا یک برنامه ثبت یا انتخاب کنید.</td></tr>';
        renderDashboardRecentTable([]);
        const countEl = document.getElementById('table-patch-count');
        if (countEl) countEl.textContent = '0 نسخه ثبت‌شده';
        const statCount = document.getElementById('stat-patch-count');
        if (statCount) statCount.textContent = 0;
        return;
      }
      if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center py-8 text-slate-400">در حال بارگذاری نسخه‌ها...</td></tr>';

      try {
        const res = await fetch(`${BASE_PATH}/api/patches?app_id=${currentAppId}`);
        const patches = await res.json();
        allPatchesData = patches;

        const countEl = document.getElementById('table-patch-count');
        if (countEl) countEl.textContent = `${patches.length} نسخه ثبت‌شده`;
        const statCount = document.getElementById('stat-patch-count');
        if (statCount) statCount.textContent = patches.length;

        const activePatch = patches.find(p => p.is_active === 1);

        // Update Hero/Card info
        const patchVerEl = document.getElementById('current-patch-version');
        const liveChip = document.getElementById('live-status-chip');
        const policyChip = document.getElementById('policy-chip');
        const metaTarget = document.getElementById('meta-target-code');
        const metaDate = document.getElementById('meta-date');
        const metaNotesText = document.getElementById('meta-notes-text');

        if (activePatch) {
          if (patchVerEl) patchVerEl.textContent = `v${activePatch.version}`;
          if (liveChip) {
            liveChip.className = "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200";
            liveChip.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span><span>فعال در کلاینت‌ها</span>`;
          }
          if (policyChip) {
            policyChip.textContent = activePatch.is_force ? "اجباری (Force Update)" : "اختیاری (Optional)";
          }
          if (metaTarget) metaTarget.textContent = activePatch.target_version_code;
          if (metaDate) metaDate.textContent = activePatch.created_at;
          if (metaNotesText) metaNotesText.textContent = activePatch.release_notes || 'بدون یادداشت فنی';
        } else {
          if (patchVerEl) patchVerEl.textContent = "نسخه خام استور";
          if (liveChip) {
            liveChip.className = "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-500 border border-slate-200";
            liveChip.innerHTML = `<span>بدون پچ فعال</span>`;
          }
          if (policyChip) policyChip.textContent = "پیش‌فرض استور";
          if (metaTarget) metaTarget.textContent = "-";
          if (metaDate) metaDate.textContent = "-";
          if (metaNotesText) metaNotesText.textContent = "کاربران هم‌اکنون به نسخه اصلی استور متصل هستند.";
        }

        renderDashboardRecentTable(patches);
        filterPatchesTable();

      } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-red-600">خطا در بارگذاری جدول: ${e}</td></tr>`;
      }
    }

    async function uploadPatch() {
      if (!currentAppId) {
        showToast('لطفاً ابتدا یک برنامه ثبت یا انتخاب کنید.', 'error');
        return;
      }
      if (!selectedFile) {
        showToast('لطفاً ابتدا فایل پچ (.zip یا .bundle) را انتخاب فرمایید.', 'error');
        return;
      }
      const version = document.getElementById('input-patch-version').value.trim();
      if (!version) {
        showToast('لطفاً شماره نسخه پچ (SemVer) را وارد کنید.', 'error');
        return;
      }
      const targetCode = document.getElementById('input-target-build').value || 1;
      const isForce = document.getElementById('select-policy').value === 'force' ? 1 : 0;
      const activate = document.getElementById('auto-deploy').checked ? 1 : 0;
      const notes = encodeURIComponent(document.getElementById('textarea-notes').value.trim());

      const btn = document.getElementById('btn-deploy-patch');
      const origText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">refresh</span><span>در حال بارگذاری باینری و محاسبه هش MD5...</span>`;

      try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('app_id', currentAppId);
        formData.append('target_abi', document.getElementById('select-target-abi') ? document.getElementById('select-target-abi').value : 'multi');
        formData.append('version', version);
        formData.append('target_version_code', targetCode);
        formData.append('is_force', isForce ? '1' : '0');
        formData.append('activate', activate ? '1' : '0');
        formData.append('notes', document.getElementById('textarea-notes').value.trim());
        formData.append('filename', selectedFile.name);

        const url = `${BASE_PATH}/api/patches/upload`;
        
        const res = await fetch(url, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();

        if (data.ok) {
          showToast(`پچ نسخه ${version} با موفقیت بارگذاری و فعال گردید!`, 'success');
          document.getElementById('input-patch-version').value = '';
          document.getElementById('textarea-notes').value = '';
          selectedFile = null;
          document.getElementById('selected-file-badge').style.display = 'none';
          await loadApps();
          setTimeout(() => switchView('rollback'), 600);
        } else {
          showToast('خطا در سرور: ' + (data.error || 'ناشناخته'), 'error');
        }
      } catch (e) {
        showToast('خطای شبکه در هنگام آپلود: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
      }
    }

    async function activatePatch(patchId) {
      if (!confirm('آیا از فعال‌سازی و رول‌بک به این نسخه اطمینان دارید؟ کلاینت‌های این برنامه فوراً به این نسخه متصل خواهند شد.')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/activate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: currentAppId, patch_id: patchId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('عملیات رول‌بک با موفقیت انجام شد.', 'success');
          await loadApps();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    async function toggleForce(patchId) {
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/toggle_force`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patch_id: patchId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('سیاست پچ به‌روزرسانی شد.', 'info');
          await loadPatches();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    async function deletePatch(patchId) {
      if (!confirm('آیا از حذف دائمی این پچ از سرور اطمینان دارید؟')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/patches/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patch_id: patchId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('پچ با موفقیت حذف گردید.', 'info');
          await loadApps();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    function renderAppsCards() {
      const grid = document.getElementById('apps-cards-grid');
      if (!grid) return;
      const addCardHtml = `
        <div onclick="openNewAppModal()" class="border-2 border-dashed border-slate-200 hover:border-blue-500 rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all min-h-[220px]">
          <div class="w-14 h-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
            <span class="material-symbols-outlined text-[28px]">add</span>
          </div>
          <span class="text-sm font-bold text-slate-800">ثبت برنامه جدید</span>
          <span class="text-xs text-slate-400 mt-1">اتصال پروژه فلاتر دیگر</span>
        </div>
      `;
      if (!appsList || appsList.length === 0) {
        grid.innerHTML = addCardHtml;
        return;
      }
      
      const cardsHtml = appsList.map(a => {
        const isCurrent = a.app_id === currentAppId;
        const activeVerText = a.active_version ? `v${a.active_version}` : 'بدون پچ فعال';
        const activeVerClass = a.active_version ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-slate-100 text-slate-600 border-slate-200';
        const cardBorder = isCurrent ? 'border-2 border-emerald-500 shadow-md ring-4 ring-emerald-50' : 'border border-slate-200 hover:border-slate-300 hover:shadow-xs';
        const iconSrc = resolveAppIcon(a);
        const avatarHtml = iconSrc 
          ? `<div class="w-11 h-11 rounded-xl overflow-hidden shrink-0 shadow-xs border border-slate-200 flex items-center justify-center" style="width: 44px; height: 44px; min-width: 44px; min-height: 44px;"><img src="${iconSrc}" alt="${a.name}" class="app-icon-img" style="width: 100%; height: 100%; object-fit: cover; display: block; border-radius: inherit;"></div>`
          : `<div class="w-11 h-11 rounded-xl bg-blue-600 text-white font-black flex items-center justify-center text-sm shadow-xs shrink-0" style="width: 44px; height: 44px; min-width: 44px; min-height: 44px;">${a.name.substring(0, 2)}</div>`;
        const encodedApp = encodeURIComponent(JSON.stringify(a));
        
        return `
          <div class="bg-white rounded-2xl p-5 ${cardBorder} flex flex-col justify-between transition-all">
            <div>
              <div class="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div class="flex items-center gap-3">
                  ${avatarHtml}
                  <div>
                    <h3 class="text-sm font-bold text-slate-900">${a.name}</h3>
                    <span class="text-[11px] font-mono text-slate-400 block" dir="ltr">${a.package_name}</span>
                  </div>
                </div>
                <div class="flex items-center gap-1">
                  ${isCurrent ? '<span class="text-[10px] bg-emerald-600 text-white font-extrabold px-2.5 py-0.5 rounded-full mr-1">برنامه فعال</span>' : ''}
                  <button class="h-6 w-6 flex items-center justify-center text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded" onclick="openEditAppModal(decodeURIComponent('${encodedApp}'))" title="ویرایش">
                    <span class="material-symbols-outlined text-[15px]">edit</span>
                  </button>
                  <button class="h-6 w-6 flex items-center justify-center text-slate-400 hover:text-red-600 hover:bg-red-50 rounded" onclick="deleteApp('${a.app_id}', '${a.name}')" title="حذف">
                    <span class="material-symbols-outlined text-[15px]">delete</span>
                  </button>
                </div>
              </div>

              <div class="text-xs text-slate-600 mb-4 leading-relaxed">${a.description || 'بدون توضیحات ثبت‌شده'}</div>

              <div class="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4">
                <div>
                  <span class="text-slate-400 block text-[10px]">شناسه:</span>
                  <span class="font-mono text-blue-600 font-bold" dir="ltr">${a.app_id}</span>
                </div>
                <div>
                  <span class="text-slate-400 block text-[10px]">کل پچ‌ها:</span>
                  <span class="font-bold text-slate-800">${a.total_patches || 0} نسخه</span>
                </div>
                <div class="col-span-2 pt-2 border-t border-slate-200/60 flex items-center justify-between">
                  <span class="text-slate-400 text-[10px]">نسخه جاری کلاینت‌ها:</span>
                  <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${activeVerClass}">${activeVerText}</span>
                </div>
              </div>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span class="text-[10px] text-slate-400 font-mono" dir="ltr">${a.created_at}</span>
              ${!isCurrent ? `
                <button onclick="selectApp('${a.app_id}'); switchView('dashboard');" class="h-8 px-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all shadow-xs flex items-center gap-1">
                  <span>ورود به این برنامه</span>
                  <span class="material-symbols-outlined text-[15px]">arrow_back</span>
                </button>
              ` : `
                <button onclick="switchView('dashboard')" class="h-8 px-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-all border border-slate-200 flex items-center gap-1">
                  <span>مشاهده داشبورد</span>
                  <span class="material-symbols-outlined text-[15px]">arrow_back</span>
                </button>
              `}
            </div>
          </div>
        `;
      }).join('');
      grid.innerHTML = cardsHtml + addCardHtml;
    }

    // Modal Handlers
    function openAppModal() {
      const modal = document.getElementById('app-switcher-modal');
      const list = document.getElementById('modal-apps-list');
      if (!appsList || appsList.length === 0) {
        list.innerHTML = '<div class="text-center py-6 text-slate-400 text-xs">هیچ برنامه‌ای ثبت نشده است. از دکمه زیر می‌توانید برنامه جدید اضافه کنید.</div>';
        modal.classList.remove('hidden');
        return;
      }
      list.innerHTML = appsList.map(a => {
        const isCurrent = a.app_id === currentAppId;
        const border = isCurrent ? "border-emerald-500 bg-emerald-50/50" : "border-slate-200 hover:bg-slate-50";
        const vText = a.active_version ? `v${a.active_version}` : 'بدون پچ';
        const iconSrc = resolveAppIcon(a);
        const avatarHtml = iconSrc 
          ? `<div class="w-10 h-10 rounded-lg overflow-hidden shrink-0 shadow-xs border border-slate-200 flex items-center justify-center" style="width: 40px; height: 40px; min-width: 40px; min-height: 40px;"><img src="${iconSrc}" alt="${a.name}" class="app-icon-img" style="width: 100%; height: 100%; object-fit: cover; display: block; border-radius: inherit;"></div>`
          : `<div class="w-10 h-10 rounded-lg bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow-xs shrink-0" style="width: 40px; height: 40px; min-width: 40px; min-height: 40px;">${a.name.substring(0, 2)}</div>`;

        return `
          <div class="flex items-center justify-between p-3 rounded-xl border ${border} cursor-pointer transition-all" onclick="selectApp('${a.app_id}')">
            <div class="flex items-center gap-3">
              ${avatarHtml}
              <div>
                <div class="text-xs font-bold text-slate-900">${a.name}</div>
                <div class="font-mono text-[11px] text-slate-500" dir="ltr">${a.package_name}</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[11px] text-slate-500 font-mono">${vText}</span>
              ${isCurrent ? '<span class="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">انتخاب شده</span>' : ''}
            </div>
          </div>
        `;
      }).join('');
      modal.classList.remove('hidden');
    }

    function closeAppModal() {
      document.getElementById('app-switcher-modal').classList.add('hidden');
    }

    function selectApp(appId) {
      currentAppId = appId;
      closeAppModal();
      renderCurrentAppBanner();
      loadPatches();
      if (typeof loadReleases === 'function') loadReleases();
      renderAppsCards();
      showToast(`برنامه فعال به ${appId} تغییر یافت.`, 'info');
    }

    function openNewAppModal() {
      document.getElementById('new-app-modal').classList.remove('hidden');
    }

    function closeNewAppModal() {
      document.getElementById('new-app-modal').classList.add('hidden');
    }

    function handleNewAppIconSelect(input) {
      if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
          document.getElementById('new-app-icon-preview').innerHTML = `<img src="${e.target.result}" class="w-full h-full object-cover">`;
        }
        reader.readAsDataURL(input.files[0]);
      }
    }

    async function submitNewApp(e) {
      e.preventDefault();
      const appId = document.getElementById('input-new-app-id').value.trim();
      const name = document.getElementById('input-new-app-name').value.trim();
      const pkg = document.getElementById('input-new-app-pkg').value.trim();
      const desc = document.getElementById('input-new-app-desc').value.trim();
      const iconInput = document.getElementById('input-new-app-icon');
      const iconFile = iconInput.files && iconInput.files[0];

      if (!appId || !name || !pkg) {
        showToast('لطفاً فیلدهای الزامی را پر کنید.', 'error');
        return;
      }

      try {
        const formData = new FormData();
        formData.append('app_id', appId);
        formData.append('name', name);
        formData.append('package_name', pkg);
        formData.append('description', desc);
        if (iconFile) {
          formData.append('icon', iconFile);
        }

        const res = await fetch(`${BASE_PATH}/api/apps`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`برنامه ${name} با موفقیت افزوده شد.`, 'success');
          closeNewAppModal();
          currentAppId = appId;
          document.getElementById('input-new-app-id').value = '';
          document.getElementById('input-new-app-name').value = '';
          document.getElementById('input-new-app-pkg').value = '';
          document.getElementById('input-new-app-desc').value = '';
          document.getElementById('input-new-app-icon').value = '';
          document.getElementById('new-app-icon-preview').innerHTML = '<span class="material-symbols-outlined text-slate-400 text-[24px]">image</span>';
          await loadApps();
          renderCurrentAppBanner();
          switchView('apps');
        } else {
          showToast('خطا: ' + (data.error || 'ناشناخته'), 'error');
        }
      } catch (e) {
        showToast('خطا در ثبت برنامه: ' + e, 'error');
      }
    }

    function openEditAppModal(appStr) {
      const app = JSON.parse(appStr);
      document.getElementById('input-edit-app-id').value = app.app_id;
      document.getElementById('input-edit-app-name').value = app.name;
      document.getElementById('input-edit-app-pkg').value = app.package_name;
      document.getElementById('input-edit-app-desc').value = app.description || '';
      document.getElementById('edit-app-modal').classList.remove('hidden');
    }

    function closeEditAppModal() {
      document.getElementById('edit-app-modal').classList.add('hidden');
    }

    async function submitEditApp(e) {
      e.preventDefault();
      const appId = document.getElementById('input-edit-app-id').value;
      const name = document.getElementById('input-edit-app-name').value.trim();
      const pkg = document.getElementById('input-edit-app-pkg').value.trim();
      const desc = document.getElementById('input-edit-app-desc').value.trim();

      try {
        const res = await fetch(`${BASE_PATH}/api/apps`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: appId, name, package_name: pkg, description: desc })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('تغییرات برنامه با موفقیت ذخیره شد.', 'success');
          closeEditAppModal();
          await loadApps();
          if(currentAppId === appId) renderCurrentAppBanner();
        } else {
          showToast('خطا: ' + data.error, 'error');
        }
      } catch (e) {
        showToast('خطا در ذخیره تغییرات.', 'error');
      }
    }

    async function deleteApp(appId, appName) {
      if (!confirm(`آیا از حذف دائمی برنامه «${appName || appId}» اطمینان دارید؟\nتمام پچ‌ها و فایل‌های APK متعلق به این برنامه نیز برای همیشه از سرور پاک خواهند شد!`)) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/apps/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: appId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`برنامه ${appName || appId} با موفقیت حذف گردید.`, 'info');
          if (currentAppId === appId) {
            currentAppId = '';
          }
          await loadApps();
        } else {
          showToast('خطا در حذف برنامه: ' + (data.error || 'ناشناخته'), 'error');
        }
      } catch (e) {
        showToast('خطای شبکه در هنگام حذف برنامه: ' + e, 'error');
      }
    }

    async function loadReleases() {
      if (!currentAppId) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/releases?app_id=${currentAppId}`);
        const data = await res.json();
        allReleasesData = Array.isArray(data) ? data : (data.releases || []);
        
        const tbody = document.getElementById('releases-table-body');
        if (!tbody) return;
        
        document.getElementById('table-release-count').textContent = allReleasesData.length + ' نسخه';
        
        if (allReleasesData.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-slate-400">هیچ فایل APK برای این برنامه ثبت نشده است.</td></tr>';
          return;
        }

        tbody.innerHTML = allReleasesData.map(r => {
          const isActive = r.is_active;
          const bgClass = isActive ? 'bg-blue-50/50' : 'hover:bg-slate-50/80';
          const badgeHtml = isActive 
            ? '<span class="text-[10px] bg-blue-600 text-white px-2 py-0.5 rounded font-bold">فعال (زنده)</span>'
            : '<span class="text-[10px] bg-slate-200 text-slate-600 px-2 py-0.5 rounded font-bold">غیرفعال</span>';
          
          return `
            <tr class="${bgClass} transition-colors">
              <td class="py-3 px-3">
                <div class="flex flex-col">
                  <span class="font-bold text-slate-900 font-mono text-sm" dir="ltr">v${r.version_name}</span>
                  <span class="text-[10px] text-slate-400 font-mono" dir="ltr">build ${r.version_code}</span>
                </div>
              </td>
              <td class="py-3 px-3 text-center">
                ${badgeHtml}
              </td>
              <td class="py-3 px-3 text-center text-xs">
                <div class="flex flex-col items-center gap-1">
                  <span class="font-bold text-slate-700" dir="ltr">${r.formatted_size}</span>
                  <span class="text-[10px] text-slate-400 flex items-center gap-0.5"><span class="material-symbols-outlined text-[12px]">download</span>${r.download_count} دانلود</span>
                </div>
              </td>
              <td class="py-3 px-3">
                <div class="flex flex-col">
                  <span class="text-[11px] text-slate-500 font-mono" dir="ltr">${r.created_at}</span>
                  <span class="text-[10px] text-slate-400 truncate max-w-[120px]" title="${r.release_notes || 'بدون یادداشت'}">${r.release_notes || '-'}</span>
                </div>
              </td>
              <td class="py-3 px-3 text-center">
                <div class="flex items-center justify-center gap-1.5">
                  <a href="${r.download_url}" target="_blank" class="h-7 w-7 bg-slate-100 hover:bg-emerald-50 text-slate-600 hover:text-emerald-600 rounded flex items-center justify-center transition-colors border border-slate-200" title="دانلود APK">
                    <span class="material-symbols-outlined text-[16px]">download</span>
                  </a>
                  ${!isActive ? `
                  <button onclick="activateRelease(${r.id})" class="h-7 px-2 bg-white hover:bg-blue-50 text-slate-600 hover:text-blue-600 rounded flex items-center gap-1 transition-colors border border-slate-200" title="انتخاب به عنوان نسخه فعال">
                    <span class="material-symbols-outlined text-[16px]">task_alt</span>
                    <span class="text-[10px] font-bold">فعال‌سازی</span>
                  </button>
                  ` : ''}
                  <button onclick="deleteRelease(${r.id})" class="h-7 w-7 bg-white hover:bg-red-50 text-slate-400 hover:text-red-500 rounded flex items-center justify-center transition-colors border border-slate-200" title="حذف دائم">
                    <span class="material-symbols-outlined text-[16px]">delete</span>
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join('');

      } catch(e) {
        console.error('loadReleases error:', e);
      }
    }

    async function activateRelease(releaseId) {
      if(!confirm('آیا مطمئن هستید که می‌خواهید این فایل APK را به عنوان نسخه زنده (فعال) برای کاربران تنظیم کنید؟')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/releases/activate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_id: currentAppId, release_id: releaseId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('نسخه APK با موفقیت فعال شد.', 'success');
          await loadReleases();
        } else {
          showToast('خطا: ' + data.error, 'error');
        }
      } catch(e) {
        showToast('خطای شبکه', 'error');
      }
    }

    async function deleteRelease(releaseId) {
      if(!confirm('آیا از حذف این فایل APK اطمینان دارید؟')) return;
      try {
        const res = await fetch(`${BASE_PATH}/api/releases/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ release_id: releaseId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('فایل APK حذف شد.', 'info');
          await loadReleases();
        } else {
          showToast('خطا: ' + data.error, 'error');
        }
      } catch(e) {
        showToast('خطای شبکه', 'error');
      }
    }


    let selectedApkFile = null;

    function handleApkFileChange(files) {
      if (!files || files.length === 0) return;
      selectedApkFile = files[0];
      const badge = document.getElementById('selected-apk-badge');
      const nameEl = document.getElementById('selected-apk-name');
      const sizeEl = document.getElementById('selected-apk-size');
      if (nameEl) nameEl.textContent = selectedApkFile.name;
      if (sizeEl) sizeEl.textContent = `سایز: ${(selectedApkFile.size / (1024 * 1024)).toFixed(2)} مگابایت`;
      if (badge) badge.style.display = 'flex';
      showToast(`فایل ${selectedApkFile.name} با موفقیت انتخاب شد.`, 'success');
    }

    function handleReleaseFileSelect(input) {
      if (input && input.files) {
        handleApkFileChange(input.files);
      }
    }

    function setupReleaseDragDrop() {
      const dropZone = document.getElementById('apk-drop-zone');
      const input = document.getElementById('real-apk-file-input');
      if (!dropZone || !input) return;

      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
      });
      
      ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('border-blue-500', 'bg-blue-50'), false);
      });
      ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('border-blue-500', 'bg-blue-50'), false);
      });

      dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
          if (files[0].name.endsWith('.apk')) {
            handleApkFileChange(files);
          } else {
            showToast('فقط فایل‌های APK (.apk) مجاز هستند.', 'error');
          }
        }
      });
    }

    async function toggleForceRelease(releaseId) {
      try {
        const res = await fetch(`${BASE_PATH}/api/releases/toggle_force`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ release_id: releaseId })
        });
        const data = await res.json();
        if (data.ok) {
          showToast('سیاست نسخه APK به‌روزرسانی شد.', 'info');
          await loadReleases();
        }
      } catch (e) {
        showToast('خطا: ' + e, 'error');
      }
    }

    async function uploadRelease() {
      if (!currentAppId) {
        showToast('لطفاً ابتدا یک برنامه ثبت یا انتخاب کنید.', 'error');
        return;
      }
      if (!selectedApkFile) {
        showToast('لطفاً ابتدا فایل APK (.apk) را انتخاب فرمایید.', 'error');
        return;
      }
      const verName = document.getElementById('input-release-vername').value.trim();
      const verCode = document.getElementById('input-release-vercode').value.trim();
      if (!verName || !verCode) {
        showToast('نام نسخه (Version Name) و کد بیلد (Version Code) هر دو الزامی هستند.', 'error');
        return;
      }
      const isForce = document.getElementById('select-release-policy').value === 'force' ? '1' : '0';
      const activate = document.getElementById('auto-deploy-release').checked ? '1' : '0';
      const notes = document.getElementById('textarea-release-notes').value.trim();

      const btn = document.getElementById('btn-deploy-release');
      const origText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined text-[17px] animate-spin">refresh</span><span>در حال بارگذاری APK و محاسبه هش...</span>';

      try {
        const formData = new FormData();
        formData.append('file', selectedApkFile);
        formData.append('app_id', currentAppId);
        formData.append('version_name', verName);
        formData.append('version_code', verCode);
        formData.append('is_force', isForce);
        formData.append('activate', activate);
        formData.append('notes', notes);
        formData.append('filename', selectedApkFile.name);

        const res = await fetch(`${BASE_PATH}/api/releases/upload`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`نسخه APK v${verName} (بیلد ${verCode}) با موفقیت ثبت شد!`, 'success');
          document.getElementById('input-release-vername').value = '';
          document.getElementById('input-release-vercode').value = '';
          document.getElementById('textarea-release-notes').value = '';
          selectedApkFile = null;
          const badge = document.getElementById('selected-apk-badge');
          if(badge) badge.style.display = 'none';
          
          await loadApps();
          await loadReleases();
        } else {
          showToast('خطا در سرور: ' + (data.error || 'ناشناخته'), 'error');
        }
      } catch (e) {
        showToast('خطای شبکه در هنگام آپلود APK: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
      }
    }

  
    function copyCliCommand() {
      const cmd = "python tool/publish_patch.py --version 1.0.2 --server http://localhost --skip-build";
      navigator.clipboard.writeText(cmd).then(() => {
        showToast("دستور CLI در حافظه کپی شد!", "success");
        const btn = document.getElementById("btn-copy-cli");
        if (btn) {
          const orig = btn.innerHTML;
          btn.innerHTML = '<span class="material-symbols-outlined text-[16px]">check</span><span>کپی شد</span>';
          setTimeout(() => { btn.innerHTML = orig; }, 2000);
        }
      }).catch(err => {
        prompt("دستور را کپی کنید:", cmd);
      });
    }

    let selectedBundleFile = null;

    function handleBundleChange(files) {
      if (!files || files.length === 0) return;
      selectedBundleFile = files[0];
      const badge = document.getElementById("selected-file-badge");
      const nameEl = document.getElementById("selected-file-name");
      const sizeEl = document.getElementById("selected-file-size");
      if (nameEl) nameEl.textContent = selectedBundleFile.name;
      if (sizeEl) sizeEl.textContent = `${(selectedBundleFile.size / (1024 * 1024)).toFixed(2)} MB`;
      if (badge) badge.style.display = "flex";
      showToast(`بسته ${selectedBundleFile.name} انتخاب شد.`, "info");
    }

    async function uploadBundle() {
      if (!selectedBundleFile) {
        showToast("لطفاً ابتدا فایل patch_bundle_vX.zip را انتخاب کنید.", "error");
        return;
      }
      const btn = document.getElementById("btn-deploy-patch");
      const orig = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="material-symbols-outlined text-[18px] animate-spin">refresh</span><span>در حال استقرار بسته...</span>';

      try {
        const formData = new FormData();
        formData.append("bundle", selectedBundleFile);
        formData.append("channel", "stable");

        const res = await fetch("/api/v1/ota/publish/", {
          method: "POST",
          body: formData
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`پچ v${data.version} با ${data.artifacts.length} معماری با موفقیت مستقر شد!`, "success");
          selectedBundleFile = null;
          document.getElementById("selected-file-badge").style.display = "none";
          await loadPatches();
          switchTab("patches");
        } else {
          showToast("خطا در استقرار: " + (data.error || "نامشخص"), "error");
        }
      } catch (err) {
        showToast("خطای شبکه: " + err, "error");
      } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
      }
    }
</script>
