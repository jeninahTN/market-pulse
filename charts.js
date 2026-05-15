// Market Pulse - Charting Logic

function renderPriceChart(canvasId, historyData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        return;
    }

    if (typeof Chart === 'undefined') {
        const fallback = document.createElement('div');
        fallback.className = 'card';
        fallback.style.padding = '20px';
        fallback.style.border = '1px solid var(--border-color)';
        fallback.style.background = 'var(--bg-light)';
        fallback.innerHTML = `
            <div style="font-weight: 700; margin-bottom: 10px; color: var(--text-dark);">Chart unavailable offline</div>
            <div style="color: var(--text-muted); margin-bottom: 12px;">The browser could not load the chart library, so here is the latest price history instead.</div>
            <div style="display: grid; gap: 6px;">
                ${(historyData || []).slice(-8).map(item => `
                    <div style="display: flex; justify-content: space-between; gap: 12px;">
                        <span style="color: var(--text-dark);">${item.date}</span>
                        <span style="font-weight: 600; color: var(--primary);">${item.price}</span>
                    </div>
                `).join('')}
            </div>
        `;
        canvas.parentNode.replaceChild(fallback, canvas);
        return;
    }

    const ctx = canvas.getContext('2d');

    const labels = historyData.map(d => d.date);
    const data = historyData.map(d => d.price);

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(46, 204, 113, 0.2)');
    gradient.addColorStop(1, 'rgba(46, 204, 113, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price (UGX)',
                data: data,
                borderColor: '#2ecc71',
                backgroundColor: gradient,
                borderWidth: 3,
                pointRadius: 0,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#2c3e50',
                    bodyColor: '#2c3e50',
                    borderColor: '#eee',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        display: false // Hide x-axis labels for cleaner look like screenshot
                    }
                },
                y: {
                    grid: {
                        color: '#f0f0f0'
                    },
                    beginAtZero: false
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}
