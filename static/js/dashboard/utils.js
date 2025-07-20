window.dashboardUtils = {
    formatCurrency: function(value) {
        return new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR'
        }).format(parseFloat(value) || 0);
    },

    formatPercentage: function(value) {
        return parseFloat(value || 0).toFixed(1) + '%';
    },

    parseFloatSafe: function(value) {
        return parseFloat(value) || 0;
    },

    generateColors: function(count) {
        const baseColors = [
            '#3B82F6', '#10B981', '#EF4444', '#F59E0B', 
            '#06B6D4', '#8B5CF6', '#EC4899', '#84CC16'
        ];
        
        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }
        return colors;
    },

    destroyChart: function(chartId) {
        if (window.chartInstances && window.chartInstances[chartId]) {
            window.chartInstances[chartId].destroy();
            delete window.chartInstances[chartId];
        }
    },

    setupFilterButtons: function(chartType, updateFunction) {
        document.querySelectorAll(`[data-chart="${chartType}"]`).forEach(button => {
            button.addEventListener('click', function() {
                document.querySelectorAll(`[data-chart="${chartType}"]`).forEach(btn => {
                    btn.classList.remove('bg-blue-500', 'text-white');
                    btn.classList.add('bg-gray-300', 'text-gray-700');
                });
                
                this.classList.remove('bg-gray-300', 'text-gray-700');
                this.classList.add('bg-blue-500', 'text-white');
                
                const period = this.dataset.period;
                const level = document.getElementById(`${chartType}-level-filter`)?.value || null;
                updateFunction(period, level);
            });
        });
    }
};

window.chartInstances = {};
