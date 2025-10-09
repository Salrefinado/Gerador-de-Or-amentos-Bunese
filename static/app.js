document.addEventListener('DOMContentLoaded', () => {
    const orcForm = document.getElementById('orc-form');
    const itemsListContainer = document.getElementById('items-list-container');
    const hiddenItemsInput = document.getElementById('hidden-items-input');
    const previewIframe = document.getElementById('preview');
    const numeroInput = document.getElementById('numero');
    
    const LAST_ORC_KEY = 'lastOrcNumber';

    const lastNumber = localStorage.getItem(LAST_ORC_KEY);
    numeroInput.value = lastNumber || "669"; 
    numeroInput.addEventListener('input', () => {
        localStorage.setItem(LAST_ORC_KEY, numeroInput.value.trim());
        updatePreviewDebounced();
    });
    
    const itemDefinitions = JSON.parse(itemsListContainer.dataset.itemDefinitions || '{}');
    const defaultItemsText = itemsListContainer.querySelector('.default-text');

    /**
     * MODIFICADO: Adiciona um marcador especial para os títulos (etapas)
     * antes de enviar para o backend. Isso torna a identificação 100% confiável.
     */
    function renderSelectedItems() {
        const selectedItems = [];
        const itemElements = itemsListContainer.querySelectorAll('.selected-item');
        
        itemElements.forEach(el => {
            const editableSpan = el.querySelector('span[contenteditable="true"]');
            if (editableSpan) {
                let formattedHtml = editableSpan.innerHTML.trim();
                
                // Se o item for um separador de etapa, adiciona o marcador
                if (el.classList.contains('stage-separator')) {
                    formattedHtml = `@@ETAPA_START@@${formattedHtml}`;
                }
                selectedItems.push(formattedHtml);
            }
        });

        if (defaultItemsText) {
             defaultItemsText.style.display = (selectedItems.length === 0) ? 'block' : 'none';
        }

        hiddenItemsInput.value = selectedItems.join('\n');
    }

    /**
     * Adiciona um novo item à lista, com span editável.
     */
    window.addItemFromSearch = function() {
        const searchInput = document.getElementById('item-input-search');
        let itemCode = searchInput.value.trim();
        if (!itemCode) return;

        let itemDescription = itemDefinitions[itemCode] || itemCode; 
        
        const newItemDiv = document.createElement('div');
        newItemDiv.className = 'selected-item flex items-center mb-2 p-2 bg-white border rounded';
        
        newItemDiv.innerHTML = `
            <span class="flex-grow p-1" contenteditable="true" oninput="renderSelectedItems(); updatePreviewDebounced();">${itemDescription}</span>
            <button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none" onclick="removeItem(this)">×</button>
        `;
        
        itemsListContainer.appendChild(newItemDiv);
        searchInput.value = '';
        renderSelectedItems();
        updatePreview();
    }

    /**
     * Adiciona separador de etapa, com span editável.
     */
    window.addEtapaSeparator = function(stageNumber) {
        let stageText;
        if (stageNumber === 1) stageText = "Etapa 1 Estrutural:";
        else if (stageNumber === 2) stageText = "Etapa 2 Equipamentos:";
        else if (stageNumber === 3) stageText = "";
        else return;

        const newItemDiv = document.createElement('div');
        newItemDiv.className = 'selected-item stage-separator flex items-center mb-2 p-2 bg-yellow-100 border-yellow-300 border rounded font-bold';

        newItemDiv.innerHTML = `
            <span class="flex-grow p-1" contenteditable="true" oninput="renderSelectedItems(); updatePreviewDebounced();">${stageText}</span>
            <button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none" onclick="removeItem(this)">×</button>
        `;
        
        itemsListContainer.appendChild(newItemDiv);
        renderSelectedItems();
        updatePreview();
    }

    /**
     * Função para formatar o texto selecionado (Negrito, Grifado).
     */
    window.formatText = function(command, value = null) {
        document.execCommand(command, false, value);
        renderSelectedItems();
        updatePreviewDebounced();
    }

    window.removeItem = function(button) {
        button.closest('.selected-item').remove();
        renderSelectedItems();
        updatePreview();
    }
    
    let previewTimer;
    window.updatePreviewDebounced = function() {
        clearTimeout(previewTimer);
        previewTimer = setTimeout(updatePreview, 500);
    }

    function updatePreview() {
        renderSelectedItems(); 
        const formData = new FormData(orcForm);
        
        if (orcForm.dataset.isGenerating === 'true') {
             return;
        }
        orcForm.dataset.isGenerating = 'true';
        previewIframe.style.opacity = '0.5'; 

        fetch('/generate', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (response.ok) {
                return response.blob().then(blob => {
                    const pdfUrl = URL.createObjectURL(blob);
                    const finalUrl = `${pdfUrl}#navpanes=0&toolbar=1`; 
                    previewIframe.src = finalUrl;
                    
                    previewIframe.onload = () => {
                        URL.revokeObjectURL(pdfUrl);
                        previewIframe.onload = null;
                        previewIframe.style.opacity = '1';
                        orcForm.dataset.isGenerating = 'false';
                    };
                });
            } else {
                previewIframe.style.opacity = '1';
                orcForm.dataset.isGenerating = 'false';
            }
        })
        .catch(error => {
            console.error('Erro de rede:', error);
            previewIframe.style.opacity = '1';
            orcForm.dataset.isGenerating = 'false';
        });
    }

    document.getElementById('item-input-search').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); 
            addItemFromSearch();
        }
    });

    document.querySelectorAll('#orc-form input:not(#hidden-items-input), #orc-form select, #orc-form textarea').forEach(input => {
        if (input.type === 'button' || input.id === 'item-input-search') return; 
        
        if (['data', 'cliente', 'numero'].includes(input.id)) {
            input.addEventListener('change', updatePreview); 
        } else {
             input.addEventListener('blur', updatePreview);
        }
    });
    
    renderSelectedItems();
    updatePreview();
});