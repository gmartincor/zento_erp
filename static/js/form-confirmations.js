class FormConfirmationHandler {
    constructor(config = {}) {
        this.config = {
            serviceForm: {
                selector: 'form[data-service-form]',
                checkbox: '#id_is_active',
                title: 'Confirmar Desactivación del Servicio',
                message: this.getServiceDeactivationMessage(),
                confirmText: 'Desactivar Servicio',
                cancelText: 'Cancelar'
            },
            ...config
        };
        this.initializeHandlers();
    }

    getServiceDeactivationMessage() {
        return `
            <div class="space-y-3">
                <p class="text-gray-700">¿Estás seguro de que quieres desactivar este servicio?</p>
                <div class="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                    <h4 class="font-semibold text-red-800 mb-2">Acción Irreversible:</h4>
                    <p class="text-sm text-red-700">Una vez desactivado, NO podrás volver a editar este servicio.</p>
                </div>
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <h4 class="font-semibold text-yellow-800 mb-2">Esta acción:</h4>
                    <ul class="text-sm text-yellow-700 space-y-1">
                        <li>• Cancelará todos los períodos pendientes</li>
                        <li>• Ajustará la fecha de fin automáticamente</li>
                        <li>• El servicio dejará de aparecer como activo</li>
                        <li>• Bloqueará futuras ediciones del servicio</li>
                    </ul>
                </div>
                <p class="text-sm text-gray-600">Los períodos ya pagados se mantendrán intactos y el servicio aparecerá en el historial del cliente.</p>
            </div>
        `;
    }

    initializeHandlers() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupServiceDeactivationConfirmation();
        });
    }

    setupServiceDeactivationConfirmation() {
        const config = this.config.serviceForm;
        const form = document.querySelector(config.selector);
        const checkbox = document.querySelector(config.checkbox);
        
        if (!form || !checkbox) return;

        const originalValue = checkbox.checked;
        let confirmationShown = false;
        
        form.addEventListener('submit', (e) => {
            if (originalValue && !checkbox.checked && !confirmationShown) {
                e.preventDefault();
                confirmationShown = true;
                this.showConfirmation(config, () => {
                    confirmationShown = false;
                    form.submit();
                });
            }
        });
    }

    showConfirmation(config, onConfirm) {
        const modal = this.createModal(config);
        document.body.appendChild(modal);
        modal.style.display = 'flex';
        
        const cancelBtn = modal.querySelector('.cancel-btn');
        const confirmBtn = modal.querySelector('.confirm-btn');

        cancelBtn.addEventListener('click', () => this.closeModal(modal));
        confirmBtn.addEventListener('click', () => {
            this.closeModal(modal);
            onConfirm();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal(modal);
        });
    }

    createModal({ title, message, confirmText, cancelText }) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900">${title}</h3>
                </div>
                <div class="px-6 py-4">${message}</div>
                <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                    <button type="button" class="cancel-btn px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                        ${cancelText}
                    </button>
                    <button type="button" class="confirm-btn px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700">
                        ${confirmText}
                    </button>
                </div>
            </div>
        `;
        return modal;
    }

    closeModal(modal) {
        if (modal && modal.parentNode) {
            modal.parentNode.removeChild(modal);
        }
    }
}

new FormConfirmationHandler();
