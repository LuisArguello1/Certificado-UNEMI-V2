document.addEventListener('DOMContentLoaded', function () {
    // 1. Obtener datos desde el script JSON en el template
    const chartDataElement = document.getElementById('chart-data-source');
    if (!chartDataElement) return;

    const chartData = JSON.parse(chartDataElement.textContent);

    // Configuración de fuentes y colores profesionales
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    Chart.defaults.color = '#64748b'; // slate-500

    // Configuración común mejorada
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false // Ocultamos la leyenda para más espacio
            },
            tooltip: {
                enabled: true,
                backgroundColor: 'rgba(255, 255, 255, 0.96)',
                titleColor: '#1e293b',
                bodyColor: '#475569',
                borderColor: '#e2e8f0',
                borderWidth: 1,
                padding: 12,
                displayColors: false,
                titleFont: {
                    size: 13,
                    weight: '600'
                },
                bodyFont: {
                    size: 13
                },
                cornerRadius: 8,
                caretSize: 6,
                callbacks: {
                    title: function(context) {
                        // Formatear fecha de forma más legible
                        const label = context[0].label;
                        const date = new Date(label);
                        return date.toLocaleDateString('es-ES', { 
                            day: 'numeric', 
                            month: 'short',
                            year: 'numeric'
                        });
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#f1f5f9',
                    drawBorder: false
                },
                border: {
                    display: false
                },
                ticks: {
                    font: {
                        size: 11,
                        weight: '500'
                    },
                    color: '#94a3b8',
                    padding: 8,
                    precision: 0
                }
            },
            x: {
                grid: {
                    display: false,
                    drawBorder: false
                },
                border: {
                    display: false
                },
                ticks: {
                    font: {
                        size: 11,
                        weight: '500'
                    },
                    color: '#94a3b8',
                    padding: 8,
                    maxRotation: 0,
                    callback: function(value, index) {
                        // Mostrar solo día y mes
                        const label = this.getLabelForValue(value);
                        const date = new Date(label);
                        return date.toLocaleDateString('es-ES', { 
                            day: 'numeric', 
                            month: 'short'
                        });
                    }
                }
            }
        },
        interaction: {
            mode: 'index',
            intersect: false
        }
    };

    // 2. Gráfico de Correos Enviados
    const ctxEmails = document.getElementById('emailsChart');
    if (ctxEmails) {
        new Chart(ctxEmails, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Correos Enviados',
                    data: chartData.email_data,
                    borderColor: '#6366f1', // indigo-500
                    backgroundColor: function(context) {
                        const ctx = context.chart.ctx;
                        const gradient = ctx.createLinearGradient(0, 0, 0, 250);
                        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.1)');
                        gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
                        return gradient;
                    },
                    borderWidth: 3,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#4f46e5',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    tooltip: {
                        ...commonOptions.plugins.tooltip,
                        callbacks: {
                            ...commonOptions.plugins.tooltip.callbacks,
                            label: function(context) {
                                return 'Correos: ' + context.parsed.y;
                            }
                        }
                    }
                }
            }
        });
    }

    // 3. Gráfico de Certificados Generados
    const ctxCerts = document.getElementById('certsChart');
    if (ctxCerts) {
        new Chart(ctxCerts, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Certificados Generados',
                    data: chartData.cert_data,
                    borderColor: '#10b981', // emerald-500
                    backgroundColor: function(context) {
                        const ctx = context.chart.ctx;
                        const gradient = ctx.createLinearGradient(0, 0, 0, 250);
                        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.1)');
                        gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');
                        return gradient;
                    },
                    borderWidth: 3,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#059669',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    tooltip: {
                        ...commonOptions.plugins.tooltip,
                        callbacks: {
                            ...commonOptions.plugins.tooltip.callbacks,
                            label: function(context) {
                                return 'Certificados: ' + context.parsed.y;
                            }
                        }
                    }
                }
            }
        });
    }
});
