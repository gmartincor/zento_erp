class DynamicFormsetManager {
    constructor(config) {
        this.container = document.getElementById(config.containerId);
        this.totalFormsInput = document.getElementById(config.totalFormsId);
        this.addButton = document.getElementById(config.addButtonId);
        this.formSelector = config.formSelector || '.formset-form';
        this.deleteButtonClass = config.deleteButtonClass || 'delete-form-btn';
        this.minForms = config.minForms || 1;
        
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
    
    updateFormIndexes() {
        const forms = this.container.querySelectorAll(this.formSelector);
        forms.forEach((form, index) => {
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
        this.totalFormsInput.value = forms.length;
    }
    
    updateInputNames(input, index) {
        if (input.name && input.name.includes('-')) {
            const parts = input.name.split('-');
            if (parts.length >= 3) {
                parts[1] = index;
                input.name = parts.join('-');
            }
        }
        if (input.id && input.id.includes('-')) {
            const parts = input.id.split('-');
            if (parts.length >= 3) {
                parts[1] = index;
                input.id = parts.join('-');
            }
        }
    }
    
    updateLabelFor(label, index) {
        const forAttr = label.getAttribute('for');
        if (forAttr && forAttr.includes('-')) {
            const parts = forAttr.split('-');
            if (parts.length >= 3) {
                parts[1] = index;
                label.setAttribute('for', parts.join('-'));
            }
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
        const forms = this.container.querySelectorAll(this.formSelector);
        forms.forEach((form, index) => {
            const existingButton = form.querySelector(`.${this.deleteButtonClass}`);
            if (existingButton) {
                existingButton.remove();
            }
            
            if (forms.length > this.minForms) {
                const deleteButton = this.createDeleteButton();
                form.appendChild(deleteButton);
            }
        });
    }
    
    addForm() {
        const forms = this.container.querySelectorAll(this.formSelector);
        const lastForm = forms[forms.length - 1];
        const newForm = lastForm.cloneNode(true);
        
        this.clearFormData(newForm);
        this.container.appendChild(newForm);
        this.updateFormIndexes();
        this.updateDeleteButtons();
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
        
        if (deleteInput) {
            deleteInput.checked = true;
            form.style.display = 'none';
        } else {
            form.remove();
            this.updateFormIndexes();
        }
        this.updateDeleteButtons();
    }
}

window.DynamicFormsetManager = DynamicFormsetManager;
