class DashboardCharts {
    constructor() {
        this.charts = {};
        this.initialized = false;
    }

    init(data) {
        if (this.initialized) {
            this.destroy();
        }
        
        try {
            if (!this.validateDependencies()) {
                console.error('DashboardCharts: Dependencias no disponibles');
                return false;
            }
            
            const sanitizedData = this.sanitizeData(data);
            
            this.createTemporalChart(sanitizedData.temporal);
            this.createExpensesChart(sanitizedData.expenses);
            this.createMarginChart(sanitizedData.temporal);
            this.createBusinessLinesChart(sanitizedData.businessLines);
            
            this.initialized = true;
            return true;
        } catch (error) {
            console.error('Error inicializando gráficos:', error);
            return false;
        }
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
        if (!canvas) {
            console.warn('Canvas temporalChart no encontrado');
            return;
        }
        
        if (!temporalData || !temporalData.length) {
            console.warn('Datos temporales vacíos');
            return;
        }

        try {
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
        } catch (error) {
            console.error('Error creando gráfico temporal:', error);
        }
    }

    createExpensesChart(expensesData) {
        const canvas = DashboardUtils.getCanvasElement('expensesChart');
        if (!canvas) {
            console.warn('Canvas expensesChart no encontrado');
            return;
        }
        
        if (!expensesData || !expensesData.length) {
            console.warn('Datos de gastos vacíos');
            return;
        }

        try {
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
        } catch (error) {
            console.error('Error creando gráfico de gastos:', error);
        }
    }

    createMarginChart(temporalData) {
        const canvas = DashboardUtils.getCanvasElement('marginChart');
        if (!canvas) {
            console.warn('Canvas marginChart no encontrado');
            return;
        }
        
        if (!temporalData || !temporalData.length) {
            console.warn('Datos temporales para margen vacíos');
            return;
        }

        try {
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
        } catch (error) {
            console.error('Error creando gráfico de margen:', error);
        }
    }

    createBusinessLinesChart(businessData) {
        const canvas = DashboardUtils.getCanvasElement('businessLinesChart');
        if (!canvas) {
            console.warn('Canvas businessLinesChart no encontrado');
            return;
        }
        
        if (!businessData || !businessData.length) {
            console.warn('Datos de líneas de negocio vacíos');
            return;
        }

        try {
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
        } catch (error) {
            console.error('Error creando gráfico de líneas de negocio:', error);
        }
    }

    destroy() {
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
    }
}

window.DashboardCharts = DashboardCharts;
