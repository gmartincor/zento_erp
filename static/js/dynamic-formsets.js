class DynamicFormsetManager {
    constructor(config) {
        this.container = document.getElementById(config.containerId);
        this.totalFormsInput = document.getElementById(config.totalFormsId);
        this.addButton = document.getElementById(config.addButtonId);
        this.formSelector = config.formSelector || '.formset-form';
        this.deleteButtonClass = config.deleteButtonClass || 'delete-form-btn';
        this.minForms = config.minForms || 1;
        this.prefix = config.prefix || 'items';
        
        this.init();
    }
    
    init() {
        if (!this.container || !this.totalFormsInput || !this.addButton) {
            console.error('DynamicFormsetManager: Required elements not found');
            return;
        }
        
        this.addButton.addEventListener('click', () => this.addForm());
        this.container.addEventListener('click', (e) => this.handleDeleteClick(e));
        this.updateDeleteButtons();
    }
    
    getVisibleForms() {
        return Array.from(this.container.querySelectorAll(this.formSelector))
            .filter(form => form.style.display !== 'none');
    }
    
    updateFormIndexes() {
        const visibleForms = this.getVisibleForms();
        visibleForms.forEach((form, index) => {
            form.setAttribute('data-form-index', index);
            
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                this.updateInputNames(input, index);
            });
            
            const labels = form.querySelectorAll('label');
            labels.forEach(label => {
                this.updateLabelFor(label, index);
            });
        });
    }
    
    updateInputNames(input, index) {
        if (input.name && input.name.includes(`${this.prefix}-`)) {
            input.name = input.name.replace(new RegExp(`${this.prefix}-\\d+`), `${this.prefix}-${index}`);
        }
        if (input.id && input.id.includes(`${this.prefix}-`)) {
            input.id = input.id.replace(new RegExp(`id_${this.prefix}-\\d+`), `id_${this.prefix}-${index}`);
        }
    }
    
    updateLabelFor(label, index) {
        const forAttr = label.getAttribute('for');
        if (forAttr && forAttr.includes(`${this.prefix}-`)) {
            label.setAttribute('for', forAttr.replace(new RegExp(`id_${this.prefix}-\\d+`), `id_${this.prefix}-${index}`));
        }
    }
    
    createDeleteButton() {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `absolute top-2 right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center text-sm font-bold ${this.deleteButtonClass}`;
        button.title = 'Eliminar línea';
        button.innerHTML = '×';
        return button;
    }
    
    updateDeleteButtons() {
        const visibleForms = this.getVisibleForms();
        visibleForms.forEach((form) => {
            const existingButton = form.querySelector(`.${this.deleteButtonClass}`);
            if (existingButton) {
                existingButton.remove();
            }
            
            if (visibleForms.length > this.minForms) {
                const deleteButton = this.createDeleteButton();
                form.appendChild(deleteButton);
            }
        });
    }
    
    addForm() {
        const visibleForms = this.getVisibleForms();
        const lastForm = visibleForms[visibleForms.length - 1];
        const newForm = lastForm.cloneNode(true);
        const newIndex = parseInt(this.totalFormsInput.value);
        
        this.clearFormData(newForm);
        this.updateNewFormIndexes(newForm, newIndex);
        
        this.container.appendChild(newForm);
        this.totalFormsInput.value = newIndex + 1;
        this.updateDeleteButtons();
    }
    
    updateNewFormIndexes(form, index) {
        form.setAttribute('data-form-index', index);
        
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            this.updateInputNames(input, index);
        });
        
        const labels = form.querySelectorAll('label');
        labels.forEach(label => {
            this.updateLabelFor(label, index);
        });
    }
    
    clearFormData(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.type === 'hidden' && input.name && input.name.includes('DELETE')) {
                input.checked = false;
                input.value = '';
            } else if (input.type !== 'hidden') {
                input.value = '';
                if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                }
            }
        });
        
        const errorDivs = form.querySelectorAll('.text-red-600');
        errorDivs.forEach(div => div.remove());
    }
    
    handleDeleteClick(e) {
        if (!e.target.classList.contains(this.deleteButtonClass)) {
            return;
        }
        
        const form = e.target.closest(this.formSelector);
        const deleteInput = form.querySelector('input[name*="DELETE"]');
        const isExistingForm = deleteInput && deleteInput.name.includes('-DELETE');
        
        if (isExistingForm) {
            deleteInput.checked = true;
            form.style.display = 'none';
        } else {
            form.remove();
        }
        
        this.updateFormIndexes();
        this.updateDeleteButtons();
    }
}

window.DynamicFormsetManager = DynamicFormsetManager;
