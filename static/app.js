document.addEventListener('DOMContentLoaded', () => {
    // Seleção de elementos do DOM
    const orcForm = document.getElementById('orc-form');
    const itemsListContainer = document.getElementById('items-list-container');
    const hiddenItemsInput = document.getElementById('hidden-items-input');
    const previewIframe = document.getElementById('preview');
    const numeroInput = document.getElementById('numero');
    const defaultItemsText = itemsListContainer.querySelector('.default-text');
    const itemDefinitions = JSON.parse(itemsListContainer.dataset.itemDefinitions || '{}');

    // --- Funções Principais ---

    /**
     * Lê todos os "itens" (texto, etapas e imagens) da lista
     * e os formata em uma string única para o backend.
     */
    function renderSelectedItems() {
        const selectedItems = [];
        const itemElements = itemsListContainer.querySelectorAll('.selected-item, .selected-image-item');
        
        itemElements.forEach(el => {
            if (el.classList.contains('selected-image-item')) {
                const imagePath = el.dataset.imagePath;
                const title = el.dataset.title; // Pega o título do placeholder
                if (imagePath) {
                    // Usa um separador | para incluir o título
                    selectedItems.push(`@@IMAGE_START@@${imagePath}|${title}`);
                }
            } else {
                const editableSpan = el.querySelector('span[contenteditable="true"]');
                if (editableSpan) {
                    let formattedHtml = editableSpan.innerHTML.trim();
                    if (el.classList.contains('stage-separator')) {
                        formattedHtml = `@@ETAPA_START@@${formattedHtml}`;
                    }
                    selectedItems.push(formattedHtml);
                }
            }
        });

        if (defaultItemsText) {
             defaultItemsText.style.display = (itemElements.length === 0) ? 'block' : 'none';
        }

        hiddenItemsInput.value = selectedItems.join('\n');
    }
    
    /**
     * Adiciona um placeholder de imagem na lista de itens no DOM.
     */
    function addImageToDom(imageName, imagePath, title) {
        const newImageDiv = document.createElement('div');
        newImageDiv.className = 'selected-image-item flex items-center mb-2 p-2 bg-gray-200 border rounded';
        newImageDiv.dataset.imagePath = imagePath;
        newImageDiv.dataset.title = title; // Armazena o título no elemento
        newImageDiv.innerHTML = `
            <span class="flex-grow p-1 italic text-gray-600">Imagem: ${imageName} (${title})</span>
            <button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none">×</button>
        `;
        // Adiciona o evento de remoção diretamente ao botão criado
        newImageDiv.querySelector('button').addEventListener('click', () => {
            newImageDiv.remove();
            renderSelectedItems();
            updatePreview();
        });

        itemsListContainer.appendChild(newImageDiv);
        renderSelectedItems();
        updatePreview();
    }

    /**
     * Faz o upload de uma nova imagem e a adiciona na lista.
     */
    function uploadAndAddImage(event) {
        const fileInput = event.target;
        const file = fileInput.files[0];
        if (!file) return;

        // Pede ao usuário para inserir um título
        const title = prompt("Digite um título para a imagem:", "Foto referência");
        if (title === null) { // Se o usuário cancelar
            fileInput.value = '';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload-image', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro no servidor: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.filePath) {
                addImageToDom(file.name, data.filePath, title); // Passa o título
            } else {
                alert('Erro: O servidor não retornou o caminho do arquivo.');
            }
        })
        .catch(error => {
            console.error('Erro no upload da imagem:', error);
            alert(`Falha no upload da imagem: ${error.message}`);
        });
        
        fileInput.value = '';
    }

    // --- Configuração dos Event Listeners ---

    // Botões de imagem pré-definida com seus títulos
    document.getElementById('btn-add-porta').addEventListener('click', () => {
        addImageToDom('Fotos Porta.png', '/static/Referencia/Fotos Porta.png', 'Fotos referência: Estrutura porta guilhotina');
    });

    document.getElementById('btn-add-inox').addEventListener('click', () => {
        addImageToDom('Foto Bancada Inox.png', '/static/Referencia/Foto Bancada Inox.png', 'Fotos referência: Equipamentos bancada inox');
    });

    document.getElementById('btn-add-pedra').addEventListener('click', () => {
        addImageToDom('Fotos Bancada Pedra.png', '/static/Referencia/Fotos Bancada Pedra.png', 'Fotos referência: Equipamentos bancada Pedra');
    });

    // Input de upload de imagem
    document.getElementById('image-upload-input').addEventListener('change', uploadAndAddImage);


    // --- Funções e Lógica Legada (mantidas como globais por causa do onclick) ---

    let previewTimer;
    function updatePreviewDebounced() {
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
                console.error('Erro ao gerar o preview.');
            }
        })
        .catch(error => {
            console.error('Erro de rede:', error);
            previewIframe.style.opacity = '1';
            orcForm.dataset.isGenerating = 'false';
        });
    }
    
    window.updatePreview = updatePreview;
    window.updatePreviewDebounced = updatePreviewDebounced;

    window.addEtapaSeparator = function(stageNumber) {
        let stageText;
        if (stageNumber === 1) stageText = "Etapa 1 Estrutural:";
        else if (stageNumber === 2) stageText = "Etapa 2 Equipamentos:";
        else if (stageNumber === 3) stageText = "";
        else return;

        const newItemDiv = document.createElement('div');
        newItemDiv.className = 'selected-item stage-separator flex items-center mb-2 p-2 bg-yellow-100 border-yellow-300 border rounded font-bold';
        newItemDiv.innerHTML = `<span class="flex-grow p-1" contenteditable="true">${stageText}</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none">×</button>`;
        newItemDiv.querySelector('span').addEventListener('input', () => { renderSelectedItems(); updatePreviewDebounced(); });
        newItemDiv.querySelector('button').addEventListener('click', () => { newItemDiv.remove(); renderSelectedItems(); updatePreview(); });
        itemsListContainer.appendChild(newItemDiv);
        renderSelectedItems();
        updatePreview();
    }

    window.addItemFromSearch = function() {
        const searchInput = document.getElementById('item-input-search');
        let itemCode = searchInput.value.trim();
        if (!itemCode) return;
        let itemDescription = itemDefinitions[itemCode] || itemCode; 
        const newItemDiv = document.createElement('div');
        newItemDiv.className = 'selected-item flex items-center mb-2 p-2 bg-white border rounded';
        newItemDiv.innerHTML = `<span class="flex-grow p-1" contenteditable="true">${itemDescription}</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none">×</button>`;
        newItemDiv.querySelector('span').addEventListener('input', () => { renderSelectedItems(); updatePreviewDebounced(); });
        newItemDiv.querySelector('button').addEventListener('click', () => { newItemDiv.remove(); renderSelectedItems(); updatePreview(); });
        itemsListContainer.appendChild(newItemDiv);
        searchInput.value = '';
        renderSelectedItems();
        updatePreview();
    }

    window.formatText = function(command, value = null) {
        document.execCommand(command, false, value);
        renderSelectedItems();
        updatePreviewDebounced();
    }
    
    // --- Inicialização ---

    // Gatilho inicial para carregar o preview
    updatePreview();
});
