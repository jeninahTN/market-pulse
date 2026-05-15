(function () {
    const STORAGE_KEY = 'market_pulse_prediction_cache_v1';
    const OFFLINE_MODEL_KEY = 'market_pulse_offline_model_v1';
    const OFFLINE_SEED_KEY = 'market_pulse_offline_seed_v1';
    const OFFLINE_MODEL_URL = '/static/data/offline_model.json';
    const OFFLINE_SEED_URL = '/static/data/offline_seed.json';

    let offlineBundlePromise = null;

    function safeParseJson(raw, fallback) {
        if (!raw) {
            return fallback;
        }
        try {
            return JSON.parse(raw);
        } catch (error) {
            return fallback;
        }
    }

    function loadStoredJson(key) {
        try {
            return safeParseJson(localStorage.getItem(key), null);
        } catch (error) {
            return null;
        }
    }

    function saveStoredJson(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.warn('Could not save cached JSON:', error);
        }
    }

    function loadCache() {
        return loadStoredJson(STORAGE_KEY) || {};
    }

    function saveCache(cache) {
        saveStoredJson(STORAGE_KEY, cache);
    }

    function normalizeKeyPart(value) {
        return String(value || '').trim().toLowerCase();
    }

    function makeKey(cropId, region) {
        return `${normalizeKeyPart(cropId)}__${normalizeKeyPart(region)}`;
    }

    function escapeHtml(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function toNumber(value, fallback = 0) {
        const number = Number(value);
        return Number.isFinite(number) ? number : fallback;
    }

    function formatNumber(value) {
        const number = Math.round(toNumber(value, 0));
        try {
            return new Intl.NumberFormat('en-UG', { maximumFractionDigits: 0 }).format(number);
        } catch (error) {
            return String(number).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
    }

    function formatDateLabel(value) {
        if (!value) {
            return '';
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        try {
            return date.toLocaleString('en-UG', {
                dateStyle: 'medium',
                timeStyle: 'short',
            });
        } catch (error) {
            return date.toISOString();
        }
    }

    function t(key, fallback) {
        if (typeof window.marketPulseT === 'function') {
            return window.marketPulseT(key, fallback);
        }
        return fallback;
    }

    function getToastContainer() {
        let container = document.getElementById('app-toast-container');
        if (container) {
            return container;
        }

        container = document.createElement('div');
        container.id = 'app-toast-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '10px';
        container.style.pointerEvents = 'none';
        document.body.appendChild(container);
        return container;
    }

    function showToast(message, kind = 'info', timeout = 4200) {
        const container = getToastContainer();
        if (!container) {
            return null;
        }

        const palette = {
            success: { background: 'rgba(46, 204, 113, 0.14)', border: 'rgba(46, 204, 113, 0.34)', color: 'var(--text-dark)' },
            error: { background: 'rgba(231, 76, 60, 0.14)', border: 'rgba(231, 76, 60, 0.34)', color: 'var(--text-dark)' },
            warning: { background: 'rgba(243, 156, 18, 0.14)', border: 'rgba(243, 156, 18, 0.34)', color: 'var(--text-dark)' },
            info: { background: 'rgba(52, 152, 219, 0.14)', border: 'rgba(52, 152, 219, 0.34)', color: 'var(--text-dark)' },
        };
        const theme = palette[kind] || palette.info;

        const toast = document.createElement('div');
        toast.setAttribute('role', 'status');
        toast.style.minWidth = '240px';
        toast.style.maxWidth = '360px';
        toast.style.padding = '12px 14px';
        toast.style.borderRadius = '14px';
        toast.style.border = `1px solid ${theme.border}`;
        toast.style.background = theme.background;
        toast.style.color = theme.color;
        toast.style.boxShadow = '0 12px 30px rgba(0, 0, 0, 0.12)';
        toast.style.pointerEvents = 'auto';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-8px)';
        toast.style.transition = 'opacity 180ms ease, transform 180ms ease';
        toast.innerHTML = `<div style="font-weight: 600; font-size: 0.92rem; line-height: 1.4;">${escapeHtml(message)}</div>`;

        container.appendChild(toast);
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });

        window.setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-8px)';
            window.setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 220);
        }, timeout);

        return toast;
    }

    function updateConnectionBadge() {
        const badge = document.getElementById('connection-status-badge');
        if (!badge) {
            return;
        }

        const dot = badge.querySelector('[data-connection-dot]');
        const label = badge.querySelector('[data-connection-label]');
        const online = navigator.onLine;

        badge.style.borderColor = online ? 'rgba(46, 204, 113, 0.25)' : 'rgba(231, 76, 60, 0.28)';
        badge.style.background = online ? 'rgba(46, 204, 113, 0.12)' : 'rgba(231, 76, 60, 0.12)';
        badge.style.color = online ? 'var(--primary)' : '#e74c3c';
        if (dot) {
            dot.style.background = online ? 'var(--primary)' : '#e74c3c';
        }
        if (label) {
            label.textContent = online ? t('status_online', 'Online') : t('status_offline', 'Offline');
        }
        badge.title = online
            ? t('status_online_title', 'Live connection available')
            : t('status_offline_title', 'Offline mode. Cached predictions are available.');
    }

    function cacheSnapshot(snapshot) {
        if (!snapshot || !snapshot.id || !snapshot.region) {
            return null;
        }

        const cache = loadCache();
        const key = makeKey(snapshot.id, snapshot.region);
        const cachedAt = snapshot.cached_at || snapshot.data_freshness_timestamp || new Date().toISOString();
        cache[key] = { ...snapshot, cached_at: cachedAt };
        saveCache(cache);
        return cache[key];
    }

    function cacheSnapshots(snapshots) {
        if (!Array.isArray(snapshots)) {
            return [];
        }
        return snapshots.map(cacheSnapshot).filter(Boolean);
    }

    function getSnapshot(cropId, region) {
        const cache = loadCache();
        return cache[makeKey(cropId, region)] || null;
    }

    function getAllSnapshots() {
        const cache = loadCache();
        return Object.values(cache).filter(Boolean);
    }

    function readJsonScript(scriptId) {
        const script = document.getElementById(scriptId);
        if (!script || !script.textContent) {
            return null;
        }
        return safeParseJson(script.textContent, null);
    }

    function hydrateSnapshotsFromScript(scriptId) {
        const payload = readJsonScript(scriptId);
        if (!payload) {
            return [];
        }

        if (Array.isArray(payload)) {
            cacheSnapshots(payload);
            return payload;
        }

        cacheSnapshot(payload);
        return [payload];
    }

    async function loadJsonAsset(url, storageKey) {
        const stored = loadStoredJson(storageKey);
        if (stored) {
            return stored;
        }

        try {
            const response = await fetch(url, { credentials: 'same-origin' });
            if (response && response.ok) {
                const payload = await response.json();
                saveStoredJson(storageKey, payload);
                return payload;
            }
        } catch (error) {
            // Fall back to cache storage below.
        }

        if ('caches' in window) {
            try {
                const cachedResponse = await caches.match(url);
                if (cachedResponse) {
                    const payload = await cachedResponse.json();
                    saveStoredJson(storageKey, payload);
                    return payload;
                }
            } catch (error) {
                // Ignore cache lookup failures.
            }
        }

        return null;
    }

    async function loadOfflineModelPack() {
        return loadJsonAsset(OFFLINE_MODEL_URL, OFFLINE_MODEL_KEY);
    }

    async function loadOfflineSeedPack() {
        return loadJsonAsset(OFFLINE_SEED_URL, OFFLINE_SEED_KEY);
    }

    function findSeedSnapshot(seedPack, cropId, region) {
        const snapshots = Array.isArray(seedPack && seedPack.snapshots) ? seedPack.snapshots : [];
        if (!snapshots.length) {
            return null;
        }

        const targetCrop = normalizeKeyPart(cropId);
        const targetRegion = normalizeKeyPart(region);

        const exactMatch = snapshots.find((snapshot) => {
            return normalizeKeyPart(snapshot.id) === targetCrop && normalizeKeyPart(snapshot.region) === targetRegion;
        });

        return exactMatch || snapshots[0] || null;
    }

    function buildFeatureMap(featureNames, featureVector) {
        const featureMap = {};
        featureNames.forEach((name, index) => {
            featureMap[name] = featureVector[index];
        });
        return featureMap;
    }

    function formatPredictionCurrency(value) {
        return formatNumber(Math.round(toNumber(value, 0)));
    }

    function computeOfflinePrediction(baseSnapshot, modelPack) {
        if (!baseSnapshot) {
            return null;
        }

        const featureNames = Array.isArray(modelPack && modelPack.feature_names) && modelPack.feature_names.length
            ? modelPack.feature_names
            : (Array.isArray(baseSnapshot.feature_names) ? baseSnapshot.feature_names : []);
        const featureMap = baseSnapshot.feature_map && typeof baseSnapshot.feature_map === 'object'
            ? baseSnapshot.feature_map
            : {};
        const rawVector = Array.isArray(baseSnapshot.feature_vector) ? baseSnapshot.feature_vector : [];
        const coefficients = modelPack && typeof modelPack.coefficients === 'object' ? modelPack.coefficients : {};
        const intercept = toNumber(modelPack && modelPack.intercept, 0);

        let predicted = intercept;
        const alignedVector = [];

        featureNames.forEach((name, index) => {
            let value = rawVector[index];
            if (value === undefined || value === null || value === '') {
                value = featureMap[name];
            }
            const numericValue = toNumber(value, 0);
            alignedVector.push(numericValue);
            predicted += toNumber(coefficients[name], 0) * numericValue;
        });

        predicted = Math.max(0, predicted);
        const currentPriceRaw = toNumber(baseSnapshot.current_price_raw ?? baseSnapshot.current_price, 0);
        const currentPrice = formatPredictionCurrency(currentPriceRaw);
        const predictedPrice = formatPredictionCurrency(predicted);
        const delta = predicted - currentPriceRaw;
        const advice = delta >= 0 ? 'WAIT TO SELL' : 'SELL NOW';
        const adviceDesc = delta >= 0
            ? `The offline model expects a rise from ${currentPrice} UGX to ${predictedPrice} UGX.`
            : `The offline model expects a dip from ${currentPrice} UGX to ${predictedPrice} UGX.`;
        const generatedAt = modelPack && modelPack.generated_at
            ? modelPack.generated_at
            : (baseSnapshot.data_freshness_timestamp || new Date().toISOString());
        const freshnessLabel = `Offline bundle generated ${formatDateLabel(generatedAt)}`;
        const predictionSource = `${(modelPack && modelPack.model_label) || 'Linear Regression'} (offline bundle)`;

        return {
            ...baseSnapshot,
            current_price: currentPrice,
            current_price_raw: currentPriceRaw,
            predicted_price: predictedPrice,
            predicted_price_raw: predicted,
            prediction_source: predictionSource,
            feature_names: featureNames,
            feature_vector: alignedVector,
            feature_map: buildFeatureMap(featureNames, alignedVector),
            advice,
            advice_desc: adviceDesc,
            last_updated_label: baseSnapshot.last_updated_label || freshnessLabel,
            data_freshness_label: freshnessLabel,
            data_freshness_timestamp: generatedAt,
            cached_at: generatedAt,
            offline_prediction: true,
        };
    }

    async function preloadOfflineBundle() {
        if (!offlineBundlePromise) {
            offlineBundlePromise = (async () => {
                const [modelPack, seedPack] = await Promise.all([
                    loadOfflineModelPack(),
                    loadOfflineSeedPack(),
                ]);

                const cachedSnapshots = [];
                if (modelPack && seedPack && Array.isArray(seedPack.snapshots)) {
                    const computed = seedPack.snapshots
                        .map((snapshot) => computeOfflinePrediction(snapshot, modelPack))
                        .filter(Boolean);
                    cacheSnapshots(computed);
                    cachedSnapshots.push(...computed);
                }

                return {
                    modelPack,
                    seedPack,
                    cachedSnapshots,
                };
            })();
        }

        return offlineBundlePromise;
    }

    function renderSnapshotCard(snapshot, actionUrl) {
        const detailUrl = actionUrl || `/detail/${encodeURIComponent(snapshot.id)}/${encodeURIComponent(snapshot.region)}`;
        const currentPrice = escapeHtml(snapshot.current_price || snapshot.price || '');
        const predictedPrice = escapeHtml(snapshot.predicted_price || snapshot.price || '');
        const unit = escapeHtml(snapshot.unit || '');
        const freshness = escapeHtml(snapshot.data_freshness_label || snapshot.last_updated_label || snapshot.cached_at || 'Cached prediction');
        const advice = escapeHtml(snapshot.advice || 'No advice available');
        const source = escapeHtml(snapshot.prediction_source || 'Cached model result');
        const market = escapeHtml(snapshot.market || snapshot.region || '');
        const name = escapeHtml(snapshot.name || snapshot.id || 'Crop');

        return `
            <div class="card" style="padding: 20px; margin-bottom: 16px; border-left: 4px solid var(--primary);">
                <div style="display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; flex-wrap: wrap;">
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em;">${escapeHtml(t('cached_prediction_title', 'Cached Prediction'))}</div>
                        <h3 style="margin: 4px 0 8px 0; color: var(--text-dark);">${name} ${escapeHtml(t('text_in', 'in'))} ${market}</h3>
                        <div style="color: var(--text-muted); font-size: 0.9rem;">${freshness}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: var(--text-muted); font-size: 0.85rem;">${escapeHtml(t('current_label', 'Current'))}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-dark);">${currentPrice} ${unit}</div>
                        <div style="color: var(--primary); font-size: 0.85rem; margin-top: 8px;">${escapeHtml(t('forecast_label', 'Forecast'))}</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: var(--primary);">${predictedPrice} ${unit}</div>
                    </div>
                </div>
                <p style="margin-top: 12px; color: var(--text-muted);"><strong>${escapeHtml(t('advice_label', 'Advice:'))}</strong> ${advice}</p>
                <p style="margin: 8px 0 0 0; color: var(--text-muted); font-size: 0.85rem;">${source}</p>
                <div style="margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <a href="${detailUrl}" class="btn-primary" style="padding: 10px 16px; border-radius: 999px; text-decoration: none;">${escapeHtml(t('open_full_detail', 'Open Full Detail'))}</a>
                </div>
            </div>
        `;
    }

    function renderOfflinePanel(container, snapshot, selectedCrop, selectedRegion) {
        const snapshots = getAllSnapshots()
            .sort((a, b) => String(b.cached_at || b.data_freshness_timestamp || '').localeCompare(String(a.cached_at || a.data_freshness_timestamp || '')));

        const selectionText = selectedCrop && selectedRegion
            ? ` ${escapeHtml(t('text_for', 'for'))} ${escapeHtml(selectedCrop)} ${escapeHtml(t('text_in', 'in'))} ${escapeHtml(selectedRegion)}`
            : '';

        const introText = snapshot && snapshot.offline_prediction
            ? t('offline_intro_bundle', 'This browser computed the forecast locally from the bundled model and the cached weather, sentiment, and price seed data.')
            : t('offline_intro_synced', 'Market Pulse is showing the last saved prediction that was synced to this browser.');

        const selectedCard = snapshot
            ? renderSnapshotCard(snapshot)
            : `
                <div class="card" style="padding: 20px; margin-bottom: 16px; border-left: 4px solid var(--border-color);">
                    <h3 style="margin-top: 0; color: var(--text-dark);">${escapeHtml(t('no_cached_selection_title', 'No cached prediction for this selection yet'))}${selectionText}</h3>
                    <p style="color: var(--text-muted); margin-bottom: 0;">${escapeHtml(t('no_cached_selection_desc', 'Connect once to refresh the data for this crop and region, then reopen the app while offline.'))}</p>
                </div>
            `;

        const listMarkup = snapshots.length
            ? snapshots.map((item) => renderSnapshotCard(item)).join('')
            : `
                <div class="card" style="padding: 20px; border: 1px dashed var(--border-color);">
                    <p style="margin: 0; color: var(--text-muted);">${escapeHtml(t('no_saved_predictions', 'No saved predictions are available on this device yet.'))}</p>
                </div>
            `;

        container.innerHTML = `
            <div class="card" style="padding: 20px; margin-bottom: 24px; background: var(--bg-light); border: 1px solid var(--border-color);">
                <h3 style="margin-top: 0; color: var(--text-dark);">${escapeHtml(t('offline_prediction_ready', 'Offline Prediction Ready'))}</h3>
                <p style="margin-bottom: 0; color: var(--text-muted);">${escapeHtml(introText)}</p>
            </div>
            ${selectedCard}
            <h3 style="margin: 32px 0 16px 0; color: var(--text-dark);">${escapeHtml(t('saved_predictions_device', 'Saved Predictions on This Device'))}</h3>
            ${listMarkup}
        `;
    }

    async function renderOfflinePage() {
        const container = document.getElementById('offline-cached-prediction');
        if (!container) {
            return;
        }

        const params = new URLSearchParams(window.location.search);
        const cropId = params.get('crop') || params.get('crop_id') || '';
        const region = params.get('region') || '';
        const cachedSnapshot = cropId && region ? getSnapshot(cropId, region) : null;

        let selectedSnapshot = cachedSnapshot;
        try {
            const { modelPack, seedPack } = await preloadOfflineBundle();
            if (!selectedSnapshot && seedPack) {
                const selectedSeed = findSeedSnapshot(seedPack, cropId, region);
                if (selectedSeed) {
                    selectedSnapshot = modelPack ? computeOfflinePrediction(selectedSeed, modelPack) : selectedSeed;
                }
            }

            if (selectedSnapshot) {
                cacheSnapshot(selectedSnapshot);
            }
        } catch (error) {
            console.warn('Offline bundle could not be loaded:', error);
        }

        renderOfflinePanel(container, selectedSnapshot, cropId, region);
    }

    function updateOfflineBanner() {
        const banner = document.getElementById('offline-prediction-banner');
        if (!banner) {
            return;
        }
        banner.style.display = navigator.onLine ? 'none' : 'block';
    }

    function bindPredictionForm() {
        const form = document.getElementById('prediction-form');
        if (!form || form.dataset.offlineBound === '1') {
            return;
        }
        form.dataset.offlineBound = '1';

        form.addEventListener('submit', (event) => {
            updateOfflineBanner();
            if (navigator.onLine) {
                return;
            }

            event.preventDefault();
            const cropSelect = form.querySelector('[name="crop_id"]');
            const regionSelect = form.querySelector('[name="region"]');
            const cropId = cropSelect ? cropSelect.value : '';
            const region = regionSelect ? regionSelect.value : '';
            const params = new URLSearchParams();

            if (cropId) {
                params.set('crop', cropId);
            }
            if (region) {
                params.set('region', region);
            }

            showToast(t('toast_offline_redirect', 'You are offline. Showing the cached or bundled prediction.'), 'warning');
            window.location.href = `/offline?${params.toString()}`;
        });
    }

    function bindRefreshForm() {
        const form = document.getElementById('refresh-form') || document.querySelector('form[action="/refresh-now"]');
        if (!form || form.dataset.refreshBound === '1') {
            return;
        }
        form.dataset.refreshBound = '1';

        form.addEventListener('submit', async (event) => {
            updateOfflineBanner();
            if (!navigator.onLine) {
                event.preventDefault();
                showToast(t('toast_refresh_requires_connection', 'Refresh needs a connection. Cached predictions are still available.'), 'warning');
                return;
            }

            if (!window.fetch) {
                return;
            }

            event.preventDefault();
            const button = form.querySelector('button[type="submit"]');
            const originalLabel = button ? button.innerHTML : '';
            if (button) {
                button.disabled = true;
                button.style.opacity = '0.75';
                button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${escapeHtml(t('btn_refresh_data', 'Refresh Data'))}...`;
            }

            try {
                const response = await fetch(form.action || '/refresh-now', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });

                let payload = null;
                try {
                    payload = await response.json();
                } catch (error) {
                    payload = null;
                }

                if (response.status === 401) {
                    showToast((payload && payload.message) || t('toast_signin_refresh', 'Please sign in again to refresh data.'), 'error');
                    window.setTimeout(() => {
                        window.location.href = '/login';
                    }, 1200);
                    return;
                }

                if (!response.ok || (payload && payload.status === 'error')) {
                    throw new Error((payload && payload.message) || `${t('toast_refresh_failed', 'Refresh failed.')} (${response.status})`);
                }

                const kind = payload && payload.status === 'partial' ? 'warning' : 'success';
                showToast((payload && payload.message) || t('toast_refresh_completed', 'Refresh completed successfully.'), kind);
                window.setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } catch (error) {
                showToast(error && error.message ? error.message : t('toast_refresh_failed', 'Refresh failed.'), 'error');
            } finally {
                if (button) {
                    button.disabled = false;
                    button.style.opacity = '';
                    button.innerHTML = originalLabel;
                }
            }
        });
    }

    function prefetchDetailPages() {
        if (!navigator.onLine) {
            return;
        }

        const links = Array.from(document.querySelectorAll('a[data-offline-detail="1"]'));
        const uniqueUrls = Array.from(new Set(links.map((link) => link.href)));

        uniqueUrls.forEach((url) => {
            fetch(url, { credentials: 'same-origin' }).catch(() => {});
        });
    }

    function interceptOfflineDetailLinks() {
        document.addEventListener('click', (event) => {
            const link = event.target.closest('a[data-offline-detail="1"]');
            if (!link || navigator.onLine) {
                return;
            }

            event.preventDefault();
            const cropId = link.dataset.cropId || '';
            const region = link.dataset.region || '';
            const params = new URLSearchParams();
            if (cropId) {
                params.set('crop', cropId);
            }
            if (region) {
                params.set('region', region);
            }
            window.location.href = `/offline?${params.toString()}`;
        });
    }

    function preloadBundleInBackground() {
        preloadOfflineBundle().catch((error) => {
            console.warn('Could not preload offline bundle:', error);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        hydrateSnapshotsFromScript('detail-data');
        hydrateSnapshotsFromScript('dashboard-snapshots');
        updateConnectionBadge();
        bindPredictionForm();
        bindRefreshForm();
        renderOfflinePage().catch((error) => {
            console.warn('Could not render offline page:', error);
        });
        updateOfflineBanner();
        prefetchDetailPages();
        interceptOfflineDetailLinks();
        preloadBundleInBackground();
    });

    window.addEventListener('online', () => {
        updateConnectionBadge();
        updateOfflineBanner();
        preloadBundleInBackground();
        showToast(t('toast_connection_restored', 'Connection restored. Market Pulse will refresh cached data.'), 'success');
    });

    window.addEventListener('offline', () => {
        updateConnectionBadge();
        updateOfflineBanner();
        showToast(t('toast_you_are_offline', 'You are offline. Cached and bundled predictions are available.'), 'warning');
    });

    document.addEventListener('marketpulse:language-changed', () => {
        updateConnectionBadge();
        updateOfflineBanner();
        renderOfflinePage().catch(() => {});
    });

    window.MarketPulseOffline = {
        cacheSnapshot,
        cacheSnapshots,
        computeOfflinePrediction,
        getAllSnapshots,
        getSnapshot,
        loadOfflineModelPack,
        loadOfflineSeedPack,
        preloadOfflineBundle,
        renderOfflinePage,
        renderOfflinePanel,
        showToast,
        updateConnectionBadge,
        updateOfflineBanner,
    };
})();
