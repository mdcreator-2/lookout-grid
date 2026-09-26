// ===== NODE DATA (with coordinates for Jim Corbett / Ramnagar region) =====
    const nodes = [
      {
        id: 'LG-NODE-01', location: 'Devprayag Ridge', risk: 'low', riskLabel: 'LOW RISK',
        prob: 12, probColor: '#10b981', color: '#10b981', coords: [30.200, 78.640], radiusKm: 2,
        temp: 24.2, humidity: 62, wind: 8, windDir: 'SW', smoke: 22, fireRisk: 12, battery: 94, signal: -62,
        assessment: 'All readings within normal operating parameters. Temperature and humidity are stable. No smoke or thermal anomalies detected. Forest canopy moisture remains adequate. Node operating normally with strong battery and signal levels.'
      },
      {
        id: 'LG-NODE-02', location: 'Pauri SW Sector', risk: 'moderate', riskLabel: 'MODERATE',
        prob: 38, probColor: '#f59e0b', color: '#f59e0b', coords: [30.100, 78.630], radiusKm: 5,
        temp: 29.8, humidity: 44, wind: 14, windDir: 'W', smoke: 68, fireRisk: 38, battery: 87, signal: -71,
        assessment: 'Temperature trending above seasonal average. Moderate drying conditions observed with humidity dropping below 50%. Low-level smoke particles detected, possibly from agricultural burning in adjacent sectors. Situation is being monitored — no immediate threat but conditions are pre-disposed for escalation.'
      },
      {
        id: 'LG-NODE-03', location: 'Pauri Ridge Center', risk: 'high', riskLabel: 'HIGH RISK',
        prob: 64, probColor: '#f97316', color: '#f97316', coords: [30.140, 78.750], radiusKm: 8,
        temp: 33.5, humidity: 29, wind: 18, windDir: 'NW', smoke: 142, fireRisk: 64, battery: 79, signal: -68,
        assessment: 'Elevated temperatures with rapid humidity decline detected. Smoke readings have crossed the caution threshold at 142 ppm and are trending upward. Wind patterns from the northwest could carry embers from adjacent ridge sectors. Ground-level vegetation moisture is dropping. Recommend heightened surveillance and standby for ground crew deployment.'
      },
      {
        id: 'LG-NODE-04', location: 'Rajaji East Buffer', risk: 'critical', riskLabel: 'CRITICAL ALERT',
        prob: 87, probColor: '#dc2626', color: '#dc2626', coords: [30.070, 78.720], radiusKm: 10,
        temp: 42.1, humidity: 18, wind: 23, windDir: 'NW', smoke: 340, fireRisk: 87, battery: 72, signal: -78,
        assessment: 'Rapid temperature increase detected over the last 3 hours. Smoke levels have crossed the 200 ppm safety threshold and continue to rise. Humidity has dropped sharply into the critical dry zone. Wind speed and direction from NW may accelerate fire spread across the ridge. Predicted affected radius is approximately 10 km. Immediate evacuation is recommended for surrounding villages.'
      }
    ];

    // ===== MAP INITIALIZATION (Leaflet) =====
    const mapCenter = [30.125, 78.685]; // Garhwal region
    const map = L.map('realMap', { zoomControl: false }).setView(mapCenter, 11);
    L.control.zoom({ position: 'bottomright' }).addTo(map);


    // Using Esri Light Gray Base (highly permissive for local files, naturally clean/gray, no API key needed)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      maxZoom: 16
    }).addTo(map);

        const mapMarkers = [];

    nodes.forEach((n, idx) => {
      // 1. Draw Threat Radius Circle
      const radiusMeters = n.radiusKm * 1000;
      const circle = L.circle(n.coords, {
        radius: radiusMeters,
        color: n.color,
        fillColor: `url(#grad-${n.risk})`,
        fillOpacity: 1, // Opacity is handled by the gradient stops
        weight: 1.5,
        dashArray: '4,4'
      }).addTo(map);

      // 2. Draw Center Node Dot
      let dot;
      if (n.risk === 'critical') {
        const icon = L.divIcon({
          className: 'pulse-icon',
          html: `<div style="width:14px; height:14px; background:${n.color}; border-radius:50%; border:2px solid #fff;"></div>`,
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        });
        dot = L.marker(n.coords, { icon: icon }).addTo(map);
      } else {
        dot = L.circleMarker(n.coords, {
          radius: 6,
          fillColor: n.color,
          color: '#fff',
          weight: 2,
          fillOpacity: 1
        }).addTo(map);
      }

      // 3. Tooltip
      dot.bindTooltip(`<b>${n.id}</b><br><span style="color:${n.color}">${n.riskLabel}</span>`, {
        permanent: true,
        direction: 'right',
        className: 'node-tooltip',
        offset: [12, 0]
      });

      // 4. Click Events
      const onClick = () => selectNode(idx);
      const onHover = () => hoverNode(idx);
      const onOut = () => unhoverNode();
      circle.on('click', onClick);
      circle.on('mouseover', onHover);
      circle.on('mouseout', onOut);
      dot.on('click', onClick);
      dot.on('mouseover', onHover);
      dot.on('mouseout', onOut);

      mapMarkers.push({ circle, dot });
    });

    // ===== TIME SERIES DATA (24h, 8 data points) =====
    const timeLabels = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', 'Now'];

    const tempData = [
      [22, 21, 20.5, 22, 23.5, 24.2, 24, 24.2],
      [24, 23, 22.5, 25, 27.5, 29.8, 29, 29.8],
      [25, 24, 23.5, 27, 30, 33.5, 33, 33.5],
      [26, 25, 24, 28, 34, 40, 41.5, 42.1]
    ];
    const smokeData = [
      [15, 14, 12, 16, 18, 22, 20, 22],
      [20, 18, 16, 28, 45, 68, 60, 68],
      [22, 20, 18, 40, 80, 142, 135, 142],
      [25, 22, 20, 50, 120, 260, 310, 340]
    ];
    const humidityData = [
      [65, 66, 68, 65, 63, 62, 63, 62],
      [58, 60, 62, 55, 48, 44, 45, 44],
      [52, 54, 56, 45, 35, 29, 30, 29],
      [55, 58, 60, 45, 30, 20, 19, 18]
    ];
    const riskData = [
      [8, 7, 6, 8, 10, 12, 11, 12],
      [15, 14, 12, 20, 30, 38, 35, 38],
      [20, 18, 16, 35, 50, 64, 60, 64],
      [22, 20, 18, 40, 65, 82, 85, 87]
    ];

    const nodeColors = ['#10b981', '#f59e0b', '#f97316', '#dc2626'];
    const nodeNames = ['Node 01', 'Node 02', 'Node 03', 'Node 04'];

    // ===== CHART INSTANCES =====
    let charts = {};

    function createChart(canvasId, label, datasets, yUnit, thresholdLine) {
      const ctx = document.getElementById(canvasId).getContext('2d');
      const plugins = [];
      if (thresholdLine) {
        plugins.push({
          id: 'thresholdLine',
          afterDraw(chart) {
            const yScale = chart.scales.y;
            const y = yScale.getPixelForValue(thresholdLine.value);
            const ctx = chart.ctx;
            ctx.save();
            ctx.strokeStyle = thresholdLine.color || '#dc2626';
            ctx.lineWidth = 1;
            ctx.setLineDash([6, 4]);
            ctx.beginPath(); ctx.moveTo(chart.chartArea.left, y); ctx.lineTo(chart.chartArea.right, y); ctx.stroke();
            ctx.fillStyle = thresholdLine.color || '#dc2626';
            ctx.font = '9px JetBrains Mono';
            ctx.fillText(thresholdLine.label || '', chart.chartArea.right - 60, y - 5);
            ctx.restore();
          }
        });
      }

      return new Chart(ctx, {
        type: 'line',
        data: { labels: timeLabels, datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'nearest', intersect: false },
          plugins: {
            legend: {
              display: datasets.length > 1,
              position: 'bottom',
              labels: { boxWidth: 8, boxHeight: 8, padding: 10, font: { family: 'Inter', size: 10, weight: '500' }, usePointStyle: true, pointStyle: 'circle' }
            },
            tooltip: { titleFont: { family: 'JetBrains Mono', size: 11 }, bodyFont: { family: 'JetBrains Mono', size: 11 }, padding: 10, cornerRadius: 8, backgroundColor: 'rgba(15,23,42,0.9)' }
          },
          scales: {
            x: { grid: { display: false }, ticks: { font: { family: 'JetBrains Mono', size: 9, weight: '500' }, color: '#94a3b8' }, border: { display: false } },
            y: {
              grid: { color: 'rgba(226,232,240,0.5)', drawBorder: false },
              ticks: { font: { family: 'JetBrains Mono', size: 9, weight: '500' }, color: '#94a3b8', callback: v => v + yUnit },
              border: { display: false }
            }
          },
          elements: { point: { radius: 0, hoverRadius: 5 }, line: { tension: 0.35 } }
        },
        plugins
      });
    }

    // NOTE: fill is explicitly set to false here to remove background shading on plots
    function makeDataset(name, data, color, thick) {
      return {
        label: name, data, borderColor: color, backgroundColor: color + '18',
        borderWidth: thick ? 2.5 : 1.5, fill: false, pointRadius: 0, pointHoverRadius: 5
      };
    }

    function initCharts() {
      charts.temp = createChart('chartTemp', 'Temperature',
        nodeNames.map((n, i) => makeDataset(n, tempData[i], nodeColors[i], i === 3)),
        '°C', null
      );
      charts.smoke = createChart('chartSmoke', 'Smoke',
        nodeNames.map((n, i) => makeDataset(n, smokeData[i], nodeColors[i], i === 3)),
        ' ppm', { value: 200, color: '#dc2626', label: 'Danger: 200 ppm' }
      );
      charts.humidity = createChart('chartHumidity', 'Humidity',
        nodeNames.map((n, i) => makeDataset(n, humidityData[i], nodeColors[i], i === 3)),
        '%', { value: 20, color: '#f97316', label: 'Critical: 20%' }
      );
      charts.risk = createChart('chartRisk', 'Fire Risk',
        nodeNames.map((n, i) => makeDataset(n, riskData[i], nodeColors[i], i === 3)),
        '%', { value: 70, color: '#dc2626', label: 'Severe: 70%' }
      );
    }

    // ===== UPDATE UI FOR SELECTED NODE =====
    let selectedNode = -1; // -1 = all

    function selectNode(idx) {
      if (selectedNode === idx) {
        selectedNode = -1; // deselect
      unhoverNode();
      } else {
        selectedNode = idx;
        showModal(idx);
      }
      updateCharts();
      updateCardSelection();
      updateMapSelection();
      updateChartsLabel();
    }

    function updateCharts() {
      const allData = [tempData, smokeData, humidityData, riskData];
      const chartKeys = ['temp', 'smoke', 'humidity', 'risk'];

      chartKeys.forEach((key, ci) => {
        const chart = charts[key];
        if (selectedNode === -1) {
          chart.data.datasets = nodeNames.map((n, i) => makeDataset(n, allData[ci][i], nodeColors[i], i === 3));
          chart.options.plugins.legend.display = true;
        } else {
          const i = selectedNode;
          chart.data.datasets = [makeDataset(nodeNames[i], allData[ci][i], nodeColors[i], true)];
          chart.options.plugins.legend.display = false;
        }
        chart.update();
      });
    }

    function updateCardSelection() {
      document.querySelectorAll('.node-card').forEach((card, i) => {
        card.classList.toggle('selected', i === selectedNode);
      });
    }

    function updateMapSelection() {
      mapMarkers.forEach((m, i) => {
        if (selectedNode === -1) {
          m.circle.setStyle({ opacity: 1, fillOpacity: 0.15 });
          if (m.dot.setStyle) m.dot.setStyle({ opacity: 1, fillOpacity: 1 });
          else m.dot.setOpacity(1);
        } else {
          const isSel = (i === selectedNode);
          m.circle.setStyle({ opacity: isSel ? 1 : 0.2, fillOpacity: isSel ? 0.25 : 0.05 });
          if (m.dot.setStyle) m.dot.setStyle({ opacity: isSel ? 1 : 0.4, fillOpacity: isSel ? 1 : 0.4 });
          else m.dot.setOpacity(isSel ? 1 : 0.4);
        }
      });

      if (selectedNode !== -1) {
        map.flyTo(nodes[selectedNode].coords, 12, { duration: 0.6 });
      } else {
        map.flyTo(mapCenter, 11, { duration: 0.6 });
      }
    }

    function updateChartsLabel() {
      const label = document.getElementById('chartsLabel');
      if (selectedNode === -1) {
        label.textContent = 'All Nodes';
        label.style.color = '#0f172a';
      } else {
        label.textContent = nodes[selectedNode].id + ' — ' + nodes[selectedNode].location;
        label.style.color = nodes[selectedNode].color;
      }
    }

    // ===== RENDER NODE STATS CARDS =====
    function getStatColor(val, thresholds) {
      if (val <= thresholds.green) return 'green';
      if (val <= thresholds.amber) return 'amber';
      if (val <= thresholds.orange) return 'orange';
      return 'red';
    }
    function getHumidityColor(val) {
      if (val >= 50) return 'green';
      if (val >= 35) return 'amber';
      if (val >= 20) return 'orange';
      return 'red';
    }

    function renderStatsCards() {
      const grid = document.getElementById('statsGrid');
      grid.innerHTML = nodes.map((n, i) => {
        const badgeColors = {
          low: 'background:rgba(16,185,129,0.12);color:#059669',
          moderate: 'background:rgba(245,158,11,0.12);color:#d97706',
          high: 'background:rgba(249,115,22,0.12);color:#ea580c',
          critical: 'background:rgba(220,38,38,0.14);color:#dc2626'
        };
        const dotColors = { low: '#10b981', moderate: '#f59e0b', high: '#f97316', critical: '#dc2626' };
        const tempC = getStatColor(n.temp, { green: 28, amber: 33, orange: 38 });
        const smokeC = getStatColor(n.smoke, { green: 50, amber: 100, orange: 200 });
        const humC = getHumidityColor(n.humidity);
        const riskC = getStatColor(n.fireRisk, { green: 25, amber: 50, orange: 70 });
        const battC = n.battery > 80 ? 'green' : n.battery > 50 ? 'amber' : 'red';

        return `
      <div class="node-card" data-risk="${n.risk}" onclick="selectNode(${i})" onmouseenter="hoverNode(${i})" onmouseleave="unhoverNode()">
        <div class="card-top">
          <span class="card-node-id">${n.id}</span>
          <span class="card-risk-badge" style="${badgeColors[n.risk]}">
            <span class="bdot" style="background:${dotColors[n.risk]}"></span>
            ${n.riskLabel} · ${n.prob}%
          </span>
        </div>
        <div class="card-location">${n.location}</div>
        <div class="card-stats">
          <div class="stat-item"><span class="stat-label">🌡️ Temp</span><span class="stat-value ${tempC}">${n.temp}°C</span></div>
          <div class="stat-item"><span class="stat-label">💧 Humidity</span><span class="stat-value ${humC}">${n.humidity}%</span></div>
          <div class="stat-item"><span class="stat-label">💨 Wind</span><span class="stat-value normal">${n.wind} km/h ${n.windDir}</span></div>
          <div class="stat-item"><span class="stat-label">🌫️ Smoke</span><span class="stat-value ${smokeC}">${n.smoke} ppm</span></div>
          <div class="stat-item"><span class="stat-label">🔥 Fire Risk</span><span class="stat-value ${riskC}">${n.fireRisk}%</span></div>
          <div class="stat-item"><span class="stat-label">🔋 Battery</span><span class="stat-value ${battC}">${n.battery}%</span></div>
          <div class="stat-item"><span class="stat-label">📡 Signal</span><span class="stat-value normal">${n.signal} dBm</span></div>
          <div class="stat-item"><span class="stat-label">🧭 Dir</span><span class="stat-value normal">${n.windDir}</span></div>
        </div>
      </div>
    `;
      }).join('');
    }

    // ===== NODE MODAL =====
    let currentlyShowingModal = -1;
    function hoverNode(idx) { showModal(idx); }
    function unhoverNode() { if (selectedNode !== -1) { showModal(selectedNode); } else { hideModal(); } }

    function showModal(idx) {
      if (currentlyShowingModal === idx) return;
      const n = nodes[idx];
      const modal = document.getElementById('nodeModal');
      const badge = document.getElementById('modalBadge');
      const badgeText = document.getElementById('modalBadgeText');
      const dot = document.getElementById('modalPulseDot');

      modal.className = 'node-modal visible ' + n.risk;

      const badgeStyles = {
        critical: { bg: 'rgba(220,38,38,0.14)', color: '#dc2626', text: 'RED ALERT', dotColor: '#dc2626' },
        high: { bg: 'rgba(249,115,22,0.12)', color: '#ea580c', text: 'HIGH RISK', dotColor: '#f97316' },
        moderate: { bg: 'rgba(245,158,11,0.12)', color: '#d97706', text: 'WATCH', dotColor: '#f59e0b' },
        low: { bg: 'rgba(16,185,129,0.12)', color: '#059669', text: 'NORMAL', dotColor: '#10b981' }
      };
      const bs = badgeStyles[n.risk];
      badge.style.background = bs.bg;
      badge.style.color = bs.color;
      badgeText.textContent = bs.text;
      dot.style.background = bs.dotColor;

      document.getElementById('modalNodeId').textContent = n.id + ' • ' + n.location;
      document.getElementById('modalProb').textContent = n.prob + '%';
      document.getElementById('modalProb').style.color = n.probColor;
      document.getElementById('modalAssessment').textContent = n.assessment;
      currentlyShowingModal = idx;
    }

    function hideModal() {
      if (currentlyShowingModal === -1) return;
      document.getElementById('nodeModal').classList.remove('visible');
      currentlyShowingModal = -1;
    }
    
    function closeModalBtn() {
      selectedNode = -1;
      updateCharts();
      updateCardSelection();
      updateMapSelection();
      updateChartsLabel();
      hideModal();
    }

    // ===== LIVE CLOCK =====
    function updateClock() {
      const now = new Date();
      const opts = { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
      document.getElementById('navTime').textContent = now.toLocaleDateString('en-IN', opts).replace(',', '') + ' IST';
    }

    // ===== INIT =====
    renderStatsCards();
    initCharts();
    updateClock();
    setInterval(updateClock, 1000);
  

