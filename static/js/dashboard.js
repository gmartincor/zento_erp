class DashboardCharts {
    constructor() {
        this.charts = {};
    }

    init(data) {
        if (!this.validateDependencies()) return;
        
        const sanitizedData = this.sanitizeData(data);
        
        this.createTemporalChart(sanitizedData.temporal);
        this.createExpensesChart(sanitizedData.expenses);
        this.createMarginChart(sanitizedData.temporal);
        this.createBusinessLinesChart(sanitizedData.businessLines);
    }

    validateDependencies() {
        const required = ['Chart', 'CHART_CONFIG', 'ChartFactory', 'DashboardUtils'];
        return required.every(dep => {
            if (typeof window[dep] === 'undefined') {
                console.error(`${dep} no está disponible`);
                return false;
            }
            return true;
        });
    }

    sanitizeData(data) {
        return {
            temporal: DashboardUtils.sanitizeChartData(data.temporal || []),
            expenses: DashboardUtils.sanitizeChartData(data.expenses || []),
            businessLines: DashboardUtils.sanitizeChartData(data.businessLines || [])
        };
    }

    createTemporalChart(temporalData) {
        const canvas = DashboardUtils.getCanvasElement('temporalChart');
        if (!canvas || !temporalData.length) return;

        const datasets = [{
            label: 'Ingresos',
            data: temporalData.map(d => d.ingresos),
            borderColor: CHART_CONFIG.colors.success,
            backgroundColor: CHART_CONFIG.colors.success + '20',
            tension: 0.4
        }, {
            label: 'Gastos',
            data: temporalData.map(d => d.gastos),
            borderColor: CHART_CONFIG.colors.danger,
            backgroundColor: CHART_CONFIG.colors.danger + '20',
            tension: 0.4
        }, {
            label: 'Beneficio',
            data: temporalData.map(d => d.beneficio),
            borderColor: CHART_CONFIG.colors.primary,
            backgroundColor: CHART_CONFIG.colors.primary + '20',
            tension: 0.4
        }];

        const options = {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: CHART_CONFIG.formatters.currency }
                }
            }
        };

        this.charts.temporal = ChartFactory.createLineChart(canvas, {
            labels: temporalData.map(d => d.month),
            datasets
        }, options);
    }

    createExpensesChart(expensesData) {
        const canvas = DashboardUtils.getCanvasElement('expensesChart');
        if (!canvas || !expensesData.length) return;

        const options = {
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: context => `${context.label}: ${DashboardUtils.formatCurrency(context.parsed)}`
                    }
                }
            }
        };

        this.charts.expenses = ChartFactory.createDoughnutChart(canvas, {
            labels: expensesData.map(c => c.name),
            datasets: [{
                data: expensesData.map(c => c.total),
                backgroundColor: CHART_CONFIG.colors.palette
            }]
        }, options);
    }

    createMarginChart(temporalData) {
        const canvas = DashboardUtils.getCanvasElement('marginChart');
        if (!canvas || !temporalData.length) return;

        const marginData = temporalData.map(d => 
            DashboardUtils.calculateMargin(d.beneficio, d.ingresos)
        );

        const options = {
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: value => DashboardUtils.formatPercentage(value) }
                }
            }
        };

        this.charts.margin = ChartFactory.createBarChart(canvas, {
            labels: temporalData.map(d => d.month),
            datasets: [{
                label: 'Margen %',
                data: marginData,
                backgroundColor: marginData.map(m => 
                    m >= 0 ? CHART_CONFIG.colors.success + 'CC' : CHART_CONFIG.colors.danger + 'CC'
                )
            }]
        }, options);
    }

    createBusinessLinesChart(businessData) {
        const canvas = DashboardUtils.getCanvasElement('businessLinesChart');
        if (!canvas || !businessData.length) return;

        const options = {
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { callback: CHART_CONFIG.formatters.currency }
                }
            }
        };

        this.charts.businessLines = ChartFactory.createBarChart(canvas, {
            labels: businessData.map(l => l.name),
            datasets: [{
                label: 'Ingresos',
                data: businessData.map(l => l.ingresos),
                backgroundColor: CHART_CONFIG.colors.primary + 'CC'
            }]
        }, options);
    }

    destroy() {
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
    }
}

window.DashboardCharts = DashboardCharts;
