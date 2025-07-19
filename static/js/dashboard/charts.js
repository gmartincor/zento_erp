window.dashboardCharts = {
    data: null,

    init: function(dashboardData) {
        this.data = dashboardData;
        this.createTemporalChart();
        this.createExpensesChart();
        this.createMarginChart();
        this.createBusinessLinesChart();
        this.setupEventListeners();
    },

    createTemporalChart: function() {
        const ctx = document.getElementById('temporalChart');
        if (!ctx) return;

        window.dashboardUtils.destroyChart('temporal');

        const data = this.data.temporal_data;
        
        window.chartInstances.temporal = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.fecha),
                datasets: [
                    {
                        label: 'Ingresos',
                        data: data.map(d => window.dashboardUtils.parseFloatSafe(d.ingresos)),
                        borderColor: window.dashboardConfig.colors.success,
                        backgroundColor: window.dashboardConfig.colors.success + '20',
                        tension: 0.4
                    },
                    {
                        label: 'Gastos',
                        data: data.map(d => window.dashboardUtils.parseFloatSafe(d.gastos)),
                        borderColor: window.dashboardConfig.colors.danger,
                        backgroundColor: window.dashboardConfig.colors.danger + '20',
                        tension: 0.4
                    },
                    {
                        label: 'Beneficio',
                        data: data.map(d => window.dashboardUtils.parseFloatSafe(d.beneficio)),
                        borderColor: window.dashboardConfig.colors.primary,
                        backgroundColor: window.dashboardConfig.colors.primary + '20',
                        tension: 0.4
                    }
                ]
            },
            options: {
                ...window.dashboardConfig.chartDefaults,
                plugins: {
                    ...window.dashboardConfig.chartDefaults.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + 
                                       window.dashboardUtils.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });
    },

    createExpensesChart: function() {
        const ctx = document.getElementById('expensesChart');
        if (!ctx) return;

        window.dashboardUtils.destroyChart('expenses');

        const data = this.data.expenses_data;
        if (!data || data.length === 0) return;

        window.chartInstances.expenses = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.categoria),
                datasets: [{
                    data: data.map(d => window.dashboardUtils.parseFloatSafe(d.total)),
                    backgroundColor: window.dashboardUtils.generateColors(data.length)
                }]
            },
            options: {
                ...window.dashboardConfig.chartDefaults,
                plugins: {
                    ...window.dashboardConfig.chartDefaults.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = window.dashboardUtils.formatCurrency(context.parsed);
                                const percentage = data[context.dataIndex].porcentaje;
                                return context.label + ': ' + value + 
                                       ' (' + window.dashboardUtils.formatPercentage(percentage) + ')';
                            }
                        }
                    }
                }
            }
        });
    },

    createMarginChart: function() {
        const ctx = document.getElementById('marginChart');
        if (!ctx) return;

        window.dashboardUtils.destroyChart('margin');

        const data = this.data.temporal_data;
        
        window.chartInstances.margin = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.fecha),
                datasets: [{
                    label: 'Margen (%)',
                    data: data.map(d => {
                        const ingresos = window.dashboardUtils.parseFloatSafe(d.ingresos);
                        const beneficio = window.dashboardUtils.parseFloatSafe(d.beneficio);
                        return ingresos > 0 ? ((beneficio / ingresos) * 100) : 0;
                    }),
                    backgroundColor: data.map(d => {
                        const beneficio = window.dashboardUtils.parseFloatSafe(d.beneficio);
                        return beneficio >= 0 ? window.dashboardConfig.colors.success : window.dashboardConfig.colors.danger;
                    })
                }]
            },
            options: {
                ...window.dashboardConfig.chartDefaults,
                plugins: {
                    ...window.dashboardConfig.chartDefaults.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Margen: ' + window.dashboardUtils.formatPercentage(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });
    },

    createBusinessLinesChart: function() {
        const ctx = document.getElementById('businessLinesChart');
        if (!ctx) return;

        window.dashboardUtils.destroyChart('businessLines');

        const data = this.data.business_lines_data;
        if (!data || data.length === 0) return;

        window.chartInstances.businessLines = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(d => d.nombre),
                datasets: [{
                    data: data.map(d => window.dashboardUtils.parseFloatSafe(d.ingresos)),
                    backgroundColor: window.dashboardUtils.generateColors(data.length)
                }]
            },
            options: {
                ...window.dashboardConfig.chartDefaults,
                plugins: {
                    ...window.dashboardConfig.chartDefaults.plugins,
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = window.dashboardUtils.formatCurrency(context.parsed);
                                const percentage = data[context.dataIndex].porcentaje;
                                return context.label + ': ' + value + 
                                       ' (' + window.dashboardUtils.formatPercentage(percentage) + ')';
                            }
                        }
                    }
                }
            }
        });
    },

    setupEventListeners: function() {
        window.dashboardUtils.setupFilterButtons('expenses', (period) => {
            console.log('Filtering expenses by period:', period);
        });

        window.dashboardUtils.setupFilterButtons('business-lines', (period) => {
            console.log('Filtering business lines by period:', period);
        });
    }
};
