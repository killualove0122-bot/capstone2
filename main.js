document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // --- Korea Historical Fire Database ---
  const FIRE_DATABASE = [
    { id: 'okgye_2022', name: "2022 강릉-동해(옥계) 대형 산불", lat: 37.6120, lng: 129.0340, dates: ["2022-03-05", "2019-04-04", "2004-03-10"], region: "okgye", desc: "피해면적 4,000 ha" },
    { id: 'uljin_2022', name: "2022 울진·삼척 대형 산불", lat: 37.0583, lng: 129.3514, dates: ["2022-03-04", "2000-04-07"], region: "uljin", desc: "피해면적 16,302 ha (최대)" },
    { id: 'goseong_2019', name: "2019 고성·속초 산불", lat: 38.2012, lng: 128.5123, dates: ["2019-04-04", "2020-05-01"], region: "goseong", desc: "피해면적 1,260 ha" },
    { id: 'gangneung_2023', name: "2023 강릉 난곡동 산불", lat: 37.7942, lng: 128.8878, dates: ["2023-04-11"], region: "gangneung", desc: "도심 산불 (379 ha)" },
    { id: 'andong_2020', name: "2020 안동 풍천면 산불", lat: 36.6342, lng: 128.6789, dates: ["2020-04-24", "2021-02-21"], region: "andong", desc: "피해면적 1,944 ha" },
    { id: 'miryang_2022', name: "2022 밀양 부북면 산불", lat: 35.5342, lng: 128.7512, dates: ["2022-05-31"], region: "miryang", desc: "피해면적 761 ha" },
    { id: 'hapcheon_2023', name: "2023 합천 룡주면 산불", lat: 35.5210, lng: 128.1120, dates: ["2023-03-08"], region: "hapcheon", desc: "피해면적 163 ha" },
    { id: 'inwang_2023', name: "2023 서울 인왕산 산불", lat: 37.5850, lng: 126.9530, dates: ["2023-04-02"], region: "inwang", desc: "도심 산불 (15 ha)" }
  ];

  // Nationwide Initial View (No pre-selected region, No pre-selected date)
  const initialLat = 36.3;
  const initialLng = 127.8;
  const initialZoom = 7;
  let activeMode = 'single';

  let selectedLat = null;
  let selectedLng = null;
  let selectedFireDate = null;

  const map = L.map('map', { center: [initialLat, initialLng], zoom: initialZoom, zoomControl: true });
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18 }).addTo(map);

  const mapLeft = L.map('mapLeft', { center: [initialLat, initialLng], zoom: initialZoom, zoomControl: false });
  const mapRight = L.map('mapRight', { center: [initialLat, initialLng], zoom: initialZoom, zoomControl: false });

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18 }).addTo(mapLeft);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18 }).addTo(mapRight);

  mapLeft.on('move', () => { if (activeMode === 'compare') mapRight.setView(mapLeft.getCenter(), mapLeft.getZoom(), { animate: false }); });
  mapRight.on('move', () => { if (activeMode === 'compare') mapLeft.setView(mapRight.getCenter(), mapRight.getZoom(), { animate: false }); });

  let clickMarker = null;
  let singleOverlay = null;
  let leftOverlay = null;
  let rightOverlay = null;
  let severityChart = null;
  let currentAnalysisResults = null;

  // --- Region Select Event Handler (Map Click or Search) ---
  async function onMapClick(lat, lng) {
    selectedLat = lat;
    selectedLng = lng;

    if (clickMarker) map.removeLayer(clickMarker);
    clickMarker = L.marker([lat, lng]).addTo(map);

    // Auto zoom-in to Level 11 to keep overlay aligned
    map.setView([lat, lng], 11, { animate: true });
    mapLeft.setView([lat, lng], 11);
    mapRight.setView([lat, lng], 11);

    document.getElementById('selectedRegionTitle').textContent = `위치 확인 중... (${lat.toFixed(3)}, ${lng.toFixed(3)})`;
    document.getElementById('selectedRegionCoords').textContent = `위도: ${lat.toFixed(4)}, 경도: ${lng.toFixed(4)}`;

    // Reverse Geocoding
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=12`);
      const data = await res.json();
      if (data && data.display_name) {
        const parts = data.display_name.split(', ');
        const placeName = parts.slice(0, 3).reverse().join(' ');
        document.getElementById('selectedRegionTitle').textContent = placeName || data.display_name;
      } else {
        document.getElementById('selectedRegionTitle').textContent = `선택 위치 (${lat.toFixed(3)}, ${lng.toFixed(3)})`;
      }
    } catch {
      document.getElementById('selectedRegionTitle').textContent = `선택 위치 (${lat.toFixed(3)}, ${lng.toFixed(3)})`;
    }

    // Populate Historical Fire Dates for Selected Location
    loadFireHistoryForLocation(lat, lng);
  }

  map.on('click', (e) => onMapClick(e.latlng.lat, e.latlng.lng));

  // Region Preset Dropdown Handler
  document.getElementById('koreaProvinceSelect').addEventListener('change', (e) => {
    const regKey = e.target.value;
    if (!regKey) return;

    const matched = FIRE_DATABASE.find(f => f.region === regKey);
    if (matched) {
      onMapClick(matched.lat, matched.lng);
    }
  });

  // Search Button Handler
  document.getElementById('btnSearchRegion').addEventListener('click', () => {
    const query = document.getElementById('regionSearch').value.trim();
    if (!query) return;
    showLoader(true, `'${query}' 검색 중...`);

    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        showLoader(false);
        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat);
          const lon = parseFloat(data[0].lon);
          onMapClick(lat, lon);
        } else {
          alert('해당 지명을 찾을 수 없습니다.');
        }
      })
      .catch(() => { showLoader(false); alert('검색 실패'); });
  });

  // --- Load & Display Historical Fire Dates for Selected Location ---
  function loadFireHistoryForLocation(lat, lng) {
    document.getElementById('fireDatesPlaceholder').style.display = 'none';
    const listContainer = document.getElementById('fireHistoryList');
    listContainer.style.display = 'flex';
    listContainer.innerHTML = '';
    document.getElementById('customDateBox').style.display = 'flex';

    // Find fires near selected lat/lng
    const nearbyFires = FIRE_DATABASE.map(f => {
      const dist = Math.sqrt(Math.pow(f.lat - lat, 2) + Math.pow(f.lng - lng, 2));
      return { ...f, dist };
    }).sort((a, b) => a.dist - b.dist);

    const closest = nearbyFires[0];
    let datesToDisplay = [];

    if (closest.dist < 0.4) {
      // Near known major fire region
      datesToDisplay = closest.dates.map(d => ({ date: d, desc: closest.name }));
    } else {
      // Generic location: provide recent representative fire seasons
      datesToDisplay = [
        { date: "2024-04-01", desc: "2024년 봄철 산불 특별대책기간" },
        { date: "2023-04-11", desc: "2023년 강풍 동반 동해안 산불" },
        { date: "2022-03-05", desc: "2022년 동해안 대형 산불" },
        { date: "2020-04-24", desc: "2020년 안동 대형 산불" }
      ];
    }

    datesToDisplay.forEach((item, idx) => {
      const el = document.createElement('div');
      el.className = 'fire-history-item';
      el.innerHTML = `
        <div>
          <div class="fire-date">${item.date}</div>
          <div class="fire-desc">${item.desc}</div>
        </div>
        <i data-lucide="chevron-right" style="width:16px;height:16px;"></i>
      `;

      el.onclick = () => {
        document.querySelectorAll('.fire-history-item').forEach(i => i.classList.remove('active'));
        el.classList.add('active');
        selectedFireDate = item.date;
        document.getElementById('targetDate').value = item.date;
        document.getElementById('btnCalculate').disabled = false;
        
        // Auto-run analysis when fire date is selected!
        runRealSTACAnalysis();
      };

      listContainer.appendChild(el);
    });

    if (window.lucide) lucide.createIcons();

    // Enable custom date selection
    document.getElementById('targetDate').onchange = (e) => {
      selectedFireDate = e.target.value;
      if (selectedFireDate) {
        document.getElementById('btnCalculate').disabled = false;
      }
    };
  }

  // View Mode Switcher
  document.getElementById('btnSingleView').addEventListener('click', () => {
    activeMode = 'single';
    document.getElementById('btnSingleView').classList.add('active');
    document.getElementById('btnCompareView').classList.remove('active');
    document.getElementById('singleMapContainer').style.display = 'flex';
    document.getElementById('compareMapContainer').style.display = 'none';
    map.invalidateSize();
  });

  document.getElementById('btnCompareView').addEventListener('click', () => {
    activeMode = 'compare';
    document.getElementById('btnCompareView').classList.add('active');
    document.getElementById('btnSingleView').classList.remove('active');
    document.getElementById('singleMapContainer').style.display = 'none';
    document.getElementById('compareMapContainer').style.display = 'flex';
    mapLeft.invalidateSize();
    mapRight.invalidateSize();
    mapLeft.setView(map.getCenter(), map.getZoom());
    mapRight.setView(map.getCenter(), map.getZoom());
  });

  document.getElementById('btnCalculate').addEventListener('click', () => {
    if (!selectedLat || !selectedLng) {
      alert('먼저 지도에서 분석할 지역을 클릭하세요.');
      return;
    }
    selectedFireDate = document.getElementById('targetDate').value;
    if (!selectedFireDate) {
      alert('산불 발생 날짜를 선택하세요.');
      return;
    }
    runRealSTACAnalysis();
  });

  // --- Real STAC API Satellite Engine for Selected Region & Date ---
  async function runRealSTACAnalysis() {
    if (!selectedLat || !selectedLng || !selectedFireDate) return;

    const sensorOption = document.getElementById('satelliteSensor').value;
    const delta = 0.12;
    const bbox = [selectedLng - delta, selectedLat - delta, selectedLng + delta, selectedLat + delta];

    showLoader(true, `위성 서버에서 (${selectedLat.toFixed(3)}, ${selectedLng.toFixed(3)}) ${selectedFireDate} 산불 영상 탐색 중...`);

    try {
      const targetDate = new Date(selectedFireDate);
      const preStart = new Date(targetDate.getTime() - 35 * 86400000).toISOString().split('T')[0];
      const preEnd = selectedFireDate;
      const postStart = selectedFireDate;
      const postEnd = new Date(targetDate.getTime() + 40 * 86400000).toISOString().split('T')[0];

      let primaryColl = sensorOption === 'L8' ? 'landsat-c2-l2' : (sensorOption === 'S2' ? 'sentinel-2-l2a' : 'sentinel-2-l2a');
      let secondaryColl = primaryColl === 'sentinel-2-l2a' ? 'landsat-c2-l2' : 'sentinel-2-l2a';

      let preItem = await fetchSTACScene(primaryColl, bbox, preStart, preEnd);
      let postItem = await fetchSTACScene(primaryColl, bbox, postStart, postEnd);
      let usedCollection = primaryColl;

      if (!postItem && sensorOption === 'auto') {
        const altPost = await fetchSTACScene(secondaryColl, bbox, postStart, postEnd);
        if (altPost) {
          const altPre = await fetchSTACScene(secondaryColl, bbox, preStart, preEnd);
          if (altPre) {
            preItem = altPre; postItem = altPost; usedCollection = secondaryColl;
          }
        }
      }

      if (!preItem || !postItem) throw new Error("선택하신 좌표 및 날짜 주변 구름 조건에 맞는 위성 영상을 찾지 못했습니다.");

      document.getElementById('lblPreFireDate').textContent = `${preItem.properties.datetime.slice(0,10)} (정상일)`;
      document.getElementById('lblPostFireDate').textContent = `${postItem.properties.datetime.slice(0,10)} (비교일 dNBR)`;

      const nirKey = usedCollection === 'landsat-c2-l2' ? 'nir08' : 'B08';
      const swirKey = usedCollection === 'landsat-c2-l2' ? 'swir22' : 'B12';

      const analysisBounds = L.latLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);

      const [preNIR, preSWIR, postNIR, postSWIR] = await Promise.all([
        fetchPreviewRaster(usedCollection, preItem.id, nirKey, bbox),
        fetchPreviewRaster(usedCollection, preItem.id, swirKey, bbox),
        fetchPreviewRaster(usedCollection, postItem.id, nirKey, bbox),
        fetchPreviewRaster(usedCollection, postItem.id, swirKey, bbox)
      ]);

      const analysis = processDNBR(preNIR, preSWIR, postNIR, postSWIR, analysisBounds);
      currentAnalysisResults = analysis;

      renderOverlays(analysis);
      renderSeverityTable(analysis);
      renderChart(analysis);
      renderExecutiveSummary(analysis, selectedFireDate, preItem.id, postItem.id, usedCollection);

      map.fitBounds(analysisBounds);
      mapLeft.fitBounds(analysisBounds);
      mapRight.fitBounds(analysisBounds);

      document.getElementById('resultsSection').style.display = 'grid';
      document.getElementById('btnExportCSV').disabled = false;
      document.getElementById('btnPrintReport').disabled = false;

      showLoader(false);
      document.querySelector('.results-grid').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showLoader(false);
      console.error(err);
      alert(`위성 연산 중 오류: ${err.message}`);
    }
  }

  async function fetchSTACScene(collection, bbox, startDate, endDate) {
    const res = await fetch('https://planetarycomputer.microsoft.com/api/stac/v1/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collections: [collection],
        bbox: bbox,
        datetime: `${startDate}/${endDate}`,
        query: { "eo:cloud_cover": { "lt": 40 } }
      })
    });
    const data = await res.json();
    if (data.features && data.features.length > 0) {
      data.features.sort((a, b) => a.properties['eo:cloud_cover'] - b.properties['eo:cloud_cover']);
      return data.features[0];
    }
    return null;
  }

  function fetchPreviewRaster(collection, itemId, assetName, bbox) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'Anonymous';
      const cropUrl = `https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/${bbox[0]},${bbox[1]},${bbox[2]},${bbox[3]}.png?collection=${collection}&item=${itemId}&assets=${assetName}&crs=EPSG:4326&width=512&height=512`;
      img.src = cropUrl;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width; canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const data = ctx.getImageData(0, 0, img.width, img.height).data;
        const gray = new Float32Array(img.width * img.height);
        for (let i = 0; i < gray.length; i++) gray[i] = data[i * 4];
        resolve({ data: gray, width: img.width, height: img.height });
      };
      img.onerror = () => reject(new Error(`Failed asset ${assetName}`));
    });
  }

  function processDNBR(preNIR, preSWIR, postNIR, postSWIR, bounds) {
    const width = preNIR.width, height = preNIR.height;
    const dnbrGrid = new Float32Array(width * height);
    const nbrPreGrid = new Float32Array(width * height);
    const isNoDataGrid = new Uint8Array(width * height);

    const counts = { high_regrowth: 0, unburned: 0, low: 0, mod_low: 0, mod_high: 0, high: 0 };

    for (let i = 0; i < width * height; i++) {
      const n1 = preNIR.data[i], s1 = preSWIR.data[i];
      const n2 = postNIR.data[i], s2 = postSWIR.data[i];

      // NoData Check: 궤도 외곽 0 픽셀만 마스킹 (식생 화소 보존)
      if (n1 === 0 && s1 === 0) {
        isNoDataGrid[i] = 1;
        dnbrGrid[i] = -9999;
        continue;
      }

      const nbrPre = (n1 - s1) / Math.max(n1 + s1, 1.0);
      const nbrPost = (n2 - s2) / Math.max(n2 + s2, 1.0);

      nbrPreGrid[i] = nbrPre;
      const dnbrVal = (nbrPre - nbrPost) * 1000.0;
      dnbrGrid[i] = dnbrVal;

      if (dnbrVal < -500) counts.high_regrowth++;
      else if (dnbrVal <= 99) counts.unburned++;
      else if (dnbrVal <= 269) counts.low++;
      else if (dnbrVal <= 439) counts.mod_low++;
      else if (dnbrVal <= 650) counts.mod_high++;
      else counts.high++;
    }

    const sw = bounds.getSouthWest(), ne = bounds.getNorthEast();
    const latDist = (ne.lat - sw.lat) * 111;
    const lngDist = (ne.lng - sw.lng) * 111 * Math.cos(bounds.getCenter().lat * Math.PI / 180);
    const totalAreaHa = Math.abs(latDist * lngDist) * 100;
    const haPerPixel = totalAreaHa / (width * height);

    return { grid: dnbrGrid, nbrPreGrid, isNoDataGrid, width, height, bounds, counts, totalPixels: width * height, totalAreaHa, haPerPixel };
  }

  function renderOverlays(res) {
    if (singleOverlay) map.removeLayer(singleOverlay);
    if (leftOverlay) mapLeft.removeLayer(leftOverlay);
    if (rightOverlay) mapRight.removeLayer(rightOverlay);

    const canvasDNBR = document.createElement('canvas');
    canvasDNBR.width = res.width; canvasDNBR.height = res.height;
    const ctxD = canvasDNBR.getContext('2d');
    const imgDataD = ctxD.createImageData(res.width, res.height);

    for (let i = 0; i < res.grid.length; i++) {
      const idx = i * 4;
      const val = res.grid[i];

      if (val < 100 || res.isNoDataGrid[i] === 1) {
        imgDataD.data[idx] = 0; imgDataD.data[idx+1] = 0; imgDataD.data[idx+2] = 0; imgDataD.data[idx+3] = 0;
        continue;
      }

      let r = 255, g = 255, b = 0, a = 210;
      if (val <= 269) { r = 255; g = 255; b = 0; a = 210; }
      else if (val <= 439) { r = 255; g = 153; b = 0; a = 220; }
      else if (val <= 650) { r = 255; g = 51; b = 0; a = 230; }
      else { r = 122; g = 0; b = 153; a = 240; }

      imgDataD.data[idx] = r; imgDataD.data[idx+1] = g; imgDataD.data[idx+2] = b; imgDataD.data[idx+3] = a;
    }
    ctxD.putImageData(imgDataD, 0, 0);

    const canvasPre = document.createElement('canvas');
    canvasPre.width = res.width; canvasPre.height = res.height;
    const ctxP = canvasPre.getContext('2d');
    const imgDataP = ctxP.createImageData(res.width, res.height);

    for (let i = 0; i < res.nbrPreGrid.length; i++) {
      const idx = i * 4;
      if (res.isNoDataGrid[i] === 1 || res.nbrPreGrid[i] < 0.1) {
        imgDataP.data[idx+3] = 0;
        continue;
      }
      imgDataP.data[idx] = 16; imgDataP.data[idx+1] = 185; imgDataP.data[idx+2] = 129; imgDataP.data[idx+3] = 140;
    }
    ctxP.putImageData(imgDataP, 0, 0);

    singleOverlay = L.imageOverlay(canvasDNBR.toDataURL(), res.bounds, { opacity: 0.9 }).addTo(map);
    leftOverlay = L.imageOverlay(canvasPre.toDataURL(), res.bounds, { opacity: 0.75 }).addTo(mapLeft);
    rightOverlay = L.imageOverlay(canvasDNBR.toDataURL(), res.bounds, { opacity: 0.9 }).addTo(mapRight);
  }

  function renderSeverityTable(res) {
    const tbody = document.getElementById('severityTableBody');
    const tfoot = document.getElementById('severityTableFoot');
    tbody.innerHTML = ''; tfoot.innerHTML = '';

    const SEVERITY_CLASSES = [
      { name: "Enhanced Regrowth (고식생 회복)", min: -9999, max: -501, color: "#006600", key: "high_regrowth" },
      { name: "Unburned / Normal (미피해/정상)", min: -500, max: 99, color: "#33cc33", key: "unburned" },
      { name: "Low Severity (경도 피해)", min: 100, max: 269, color: "#ffff00", key: "low" },
      { name: "Moderate-Low Severity (중경도 피해)", min: 270, max: 439, color: "#ff9900", key: "mod_low" },
      { name: "Moderate-High Severity (중중도 피해)", min: 440, max: 650, color: "#ff3300", key: "mod_high" },
      { name: "High Severity (중증 피해)", min: 651, max: 9999, color: "#7a0099", key: "high" }
    ];

    let sumHa = 0, sumKm2 = 0, sumPct = 0;

    SEVERITY_CLASSES.forEach(cls => {
      const count = res.counts[cls.key] || 0;
      const ha = count * res.haPerPixel;
      const km2 = ha / 100;
      const pct = (count / res.totalPixels) * 100;

      sumHa += ha; sumKm2 += km2; sumPct += pct;
      const rangeStr = cls.min === -9999 ? `< -500` : (cls.max === 9999 ? `> +650` : `+${cls.min} ~ +${cls.max}`);

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="badge" style="background:${cls.color}; margin-right:8px; display:inline-block; width:12px; height:12px; border-radius:2px;"></span> ${cls.name}</td>
        <td><code>${rangeStr}</code></td>
        <td><strong>${ha.toFixed(1).toLocaleString()} ha</strong></td>
        <td>${km2.toFixed(2)} km²</td>
        <td>${pct.toFixed(2)}%</td>
      `;
      tbody.appendChild(tr);
    });

    tfoot.innerHTML = `
      <tr>
        <td colspan="2">합계 (Total Area)</td>
        <td>${sumHa.toFixed(1).toLocaleString()} ha</td>
        <td>${sumKm2.toFixed(2)} km²</td>
        <td>100.00%</td>
      </tr>
    `;
  }

  function renderChart(res) {
    const ctx = document.getElementById('severityChart').getContext('2d');
    if (severityChart) severityChart.destroy();

    const SEVERITY_CLASSES = [
      { name: "고식생 회복", color: "#006600", key: "high_regrowth" },
      { name: "정상/미피해", color: "#33cc33", key: "unburned" },
      { name: "경도 피해", color: "#ffff00", key: "low" },
      { name: "중경도 피해", color: "#ff9900", key: "mod_low" },
      { name: "중중도 피해", color: "#ff3300", key: "mod_high" },
      { name: "중증 피해", color: "#7a0099", key: "high" }
    ];

    severityChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: SEVERITY_CLASSES.map(c => c.name),
        datasets: [{
          data: SEVERITY_CLASSES.map(c => (res.counts[c.key] * res.haPerPixel).toFixed(1)),
          backgroundColor: SEVERITY_CLASSES.map(c => c.color),
          borderWidth: 2, borderColor: '#1f293d'
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { color: '#d1d5db', font: { family: 'Pretendard', size: 11 } } } }
      }
    });
  }

  function renderExecutiveSummary(res, targetDateStr, preId, postId, collection) {
    const totalBurnedCount = res.counts.low + res.counts.mod_low + res.counts.mod_high + res.counts.high;
    const totalBurnedHa = totalBurnedCount * res.haPerPixel;
    const burnedPct = (totalBurnedCount / res.totalPixels) * 100;
    const sensorName = collection === 'sentinel-2-l2a' ? 'Sentinel-2' : 'Landsat';

    document.getElementById('summaryParagraph').innerHTML = `
      선택하신 지점에 대하여 <strong>${targetDateStr}</strong> 전후 수집된 <strong>${sensorName}</strong> 위성 영상(Pre: <code>${preId}</code>, Post: <code>${postId}</code>) 정밀 대조 연산 결과입니다.<br><br>
      분석 구역 전체 <strong>${res.totalAreaHa.toFixed(1)} ha</strong> 중 정상 식생 대비 변화 발생 영역은 <strong>${totalBurnedHa.toFixed(1)} ha (${burnedPct.toFixed(1)}%)</strong>로 나타납니다.
    `;
  }

  document.getElementById('btnExportCSV').addEventListener('click', () => {
    if (!currentAnalysisResults) return;
    let csvContent = "data:text/csv;charset=utf-8,USGS Class,Area (ha),Area (km2),Percentage (%)\n";
    const keys = ["high_regrowth", "unburned", "low", "mod_low", "mod_high", "high"];
    keys.forEach(k => {
      const count = currentAnalysisResults.counts[k] || 0;
      const ha = (count * currentAnalysisResults.haPerPixel).toFixed(2);
      const km2 = (ha / 100).toFixed(3);
      const pct = ((count / currentAnalysisResults.totalPixels) * 100).toFixed(2);
      csvContent += `"${k}",${ha},${km2},${pct}\n`;
    });
    const link = document.createElement('a');
    link.href = encodeURI(csvContent);
    link.download = `Korea_AllRegion_dNBR_${selectedFireDate}.csv`;
    link.click();
  });

  document.getElementById('btnPrintReport').addEventListener('click', () => window.print());

  function showLoader(show, text = "") {
    const loader = document.getElementById('loader');
    if (show) {
      document.getElementById('loaderStatusText').textContent = text;
      loader.style.display = 'flex';
    } else {
      loader.style.display = 'none';
    }
  }
});
