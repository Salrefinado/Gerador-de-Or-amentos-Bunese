document.addEventListener('DOMContentLoaded', () => {
    // --- Variáveis Globais e Seleção de Elementos ---
    const orcForm = document.getElementById('orc-form');
    const hiddenItemsInput = document.getElementById('hidden-items-input');
    const previewIframe = document.getElementById('preview');
    const itemDefinitions = JSON.parse(document.getElementById('items-editor-wrapper').dataset.itemDefinitions || '{}');
    
    const pageTabsContainer = document.getElementById('page-tabs');
    const itemsEditorWrapper = document.getElementById('items-editor-wrapper');
    const btnAddPage = document.getElementById('btn-add-page');
    
    let currentPage = 1;
    let totalPages = 1;
    let previewTimer;

    // --- Funções de Gerenciamento de Página ---

    function switchPage(targetPage) {
        currentPage = targetPage;
        // Atualiza abas
        document.querySelectorAll('.page-tab').forEach(tab => {
            tab.classList.toggle('active', parseInt(tab.dataset.page) === currentPage);
        });
        // Atualiza containers de itens
        document.querySelectorAll('.items-list-container').forEach(container => {
            container.classList.toggle('active', parseInt(container.id.split('-').pop()) === currentPage);
        });
    }

    function addNewPage() {
        totalPages++;
        // Cria nova aba
        const newTab = document.createElement('button');
        newTab.type = 'button';
        newTab.className = 'page-tab flex items-center';
        newTab.dataset.page = totalPages;
        newTab.innerHTML = `Página ${totalPages} <span class="ml-2 text-red-400 hover:text-red-600 delete-page" data-page-to-delete="${totalPages}">&#128465;</span>`;
        pageTabsContainer.appendChild(newTab);

        // Cria novo container de itens
        const newContainer = document.createElement('div');
        newContainer.className = 'items-list-container';
        newContainer.id = `items-list-container-${totalPages}`;
        newContainer.innerHTML = `<p class="text-sm text-gray-500 italic mt-1 default-text">Nenhum item selecionado.</p>`;
        itemsEditorWrapper.appendChild(newContainer);

        switchPage(totalPages);
    }

    function deletePage(pageToDelete) {
        if (pageToDelete <= 1) return; // Não permite deletar a primeira página

        // Remove a aba e o container
        document.querySelector(`.page-tab[data-page="${pageToDelete}"]`).remove();
        document.getElementById(`items-list-container-${pageToDelete}`).remove();

        // Se a página deletada era a ativa, volta para a anterior
        if (currentPage === pageToDelete) {
            switchPage(pageToDelete - 1);
        }
        
        // Renumera as páginas restantes (abas e containers)
        totalPages--;
        document.querySelectorAll('.page-tab').forEach((tab, index) => {
            const newPageNum = index + 1;
            tab.dataset.page = newPageNum;
            const textNode = Array.from(tab.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
            if(textNode) textNode.nodeValue = `Página ${newPageNum}`;
            const deleteBtn = tab.querySelector('.delete-page');
            if(deleteBtn) deleteBtn.dataset.pageToDelete = newPageNum;
        });
        document.querySelectorAll('.items-list-container').forEach((container, index) => {
            const newPageNum = index + 1;
            container.id = `items-list-container-${newPageNum}`;
        });

        renderSelectedItems();
        updatePreview();
    }

    // --- Funções de Renderização e Atualização ---

    function renderSelectedItems() {
        const allPagesContent = [];
        document.querySelectorAll('.items-list-container').forEach((container, index) => {
            const itemsOnPage = [];
            container.querySelectorAll('.selected-item, .selected-image-item').forEach(el => {
                const itemHtml = getItemHtml(el);
                if (itemHtml) itemsOnPage.push(itemHtml);
            });
            allPagesContent.push(itemsOnPage.join('\n'));
            // Atualiza texto padrão
            const defaultText = container.querySelector('.default-text');
            if (defaultText) defaultText.style.display = (itemsOnPage.length === 0) ? 'block' : 'none';
        });
        hiddenItemsInput.value = allPagesContent.join('\n@@PAGE_BREAK@@\n');
    }

    function getItemHtml(element) {
        if (element.classList.contains('selected-image-item')) {
            return `@@IMAGE_START@@${element.dataset.imagePath}|${element.dataset.title}`;
        } else {
            const editableSpan = element.querySelector('span[contenteditable="true"]');
            if (editableSpan) {
                let formattedHtml = editableSpan.innerHTML.trim();
                return element.classList.contains('stage-separator') ? `@@ETAPA_START@@${formattedHtml}` : formattedHtml;
            }
        }
        return null;
    }

    function updatePreview() {
        renderSelectedItems();
        const formData = new FormData(orcForm);
        if (orcForm.dataset.isGenerating === 'true') return;
        
        orcForm.dataset.isGenerating = 'true';
        previewIframe.style.opacity = '0.5';

        fetch('/generate', { method: 'POST', body: formData })
            .then(response => response.ok ? response.blob() : Promise.reject('Erro ao gerar preview.'))
            .then(blob => {
                const url = URL.createObjectURL(blob);
                previewIframe.src = `${url}#navpanes=0&toolbar=1`;
                previewIframe.onload = () => { URL.revokeObjectURL(url); previewIframe.style.opacity = '1'; orcForm.dataset.isGenerating = 'false'; };
            })
            .catch(error => {
                console.error(error);
                previewIframe.style.opacity = '1';
                orcForm.dataset.isGenerating = 'false';
            });
    }

    function updatePreviewDebounced() {
        clearTimeout(previewTimer);
        previewTimer = setTimeout(updatePreview, 500);
    }
    
    // --- Funções de Adição de Conteúdo (Itens, Imagens) ---

    function addItemToActiveDom(element) {
        document.querySelector(`.items-list-container.active`).appendChild(element);
        renderSelectedItems();
        updatePreview();
    }

    function addImageToDom(imageName, imagePath, title) {
        const newImageDiv = document.createElement('div');
        newImageDiv.className = 'selected-image-item flex items-center mb-2 p-2 bg-gray-200 border rounded';
        newImageDiv.dataset.imagePath = imagePath;
        newImageDiv.dataset.title = title;
        newImageDiv.innerHTML = `<span class="flex-grow p-1 italic text-gray-600">Imagem: ${imageName} (${title})</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold">×</button>`;
        newImageDiv.querySelector('button').addEventListener('click', () => {
            newImageDiv.remove(); renderSelectedItems(); updatePreview();
        });
        addItemToActiveDom(newImageDiv);
    }

    function uploadAndAddImage(event) {
        const file = event.target.files[0];
        if (!file) return;
        const title = prompt("Digite um título para a imagem:", "Foto referência");
        if (title === null) { event.target.value = ''; return; }

        const formData = new FormData();
        formData.append('file', file);
        fetch('/upload-image', { method: 'POST', body: formData })
            .then(res => res.ok ? res.json() : Promise.reject('Falha no upload'))
            .then(data => { if (data.filePath) addImageToDom(file.name, data.filePath, title); })
            .catch(err => alert(err));
        event.target.value = '';
    }

    // --- Event Listeners ---

    pageTabsContainer.addEventListener('click', (e) => {
        if (e.target.closest('.page-tab')) {
            const tab = e.target.closest('.page-tab');
            if (e.target.classList.contains('delete-page')) {
                const pageNum = parseInt(e.target.dataset.pageToDelete);
                if (confirm(`Tem certeza que deseja excluir a Página ${pageNum}?`)) {
                    deletePage(pageNum);
                }
            } else {
                switchPage(parseInt(tab.dataset.page));
            }
        }
    });

    btnAddPage.addEventListener('click', addNewPage);
    document.getElementById('btn-add-porta').addEventListener('click', () => addImageToDom('Fotos Porta.png', '/static/Referencia/Fotos Porta.png', 'Fotos referência: Estrutura porta guilhotina'));
    document.getElementById('btn-add-inox').addEventListener('click', () => addImageToDom('Foto Bancada Inox.png', '/static/Referencia/Foto Bancada Inox.png', 'Fotos referência: Equipamentos bancada inox'));
    document.getElementById('btn-add-pedra').addEventListener('click', () => addImageToDom('Fotos Bancada Pedra.png', '/static/Referencia/Fotos Bancada Pedra.png', 'Fotos referência: Equipamentos bancada Pedra'));
    document.getElementById('image-upload-input').addEventListener('change', uploadAndAddImage);

    // --- Funções Globais para `onclick` ---
    window.addEtapaSeparator = (stageNumber) => {
        let stageText = {"1": "Etapa 1 Estrutural:", "2": "Etapa 2 Equipamentos:", "3": ""}[stageNumber] || "";
        const newItemDiv = document.createElement('div');
        newItemDiv.className = 'selected-item stage-separator flex items-center mb-2 p-2 bg-yellow-100 border-yellow-300 rounded font-bold';
        newItemDiv.innerHTML = `<span class="flex-grow p-1" contenteditable="true">${stageText}</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold">×</button>`;
        newItemDiv.querySelector('span').addEventListener('input', () => { renderSelectedItems(); updatePreviewDebounced(); });
        newItemDiv.querySelector('button').addEventListener('click', () => { newItemDiv.remove(); renderSelectedItems(); updatePreview(); });
        addItemToActiveDom(newItemDiv);
    };

    window.addItemFromSearch = () => {
        const searchInput = document.getElementById('item-input-search');
        const itemCode = searchInput.value.trim();
        if (!itemCode) return;
        const itemDescription = itemDefinitions[itemCode] || itemCode;
        const newItemDiv = document.createElement('div');
        newItemDiv.className = 'selected-item flex items-center mb-2 p-2 bg-white border rounded';
        newItemDiv.innerHTML = `<span class="flex-grow p-1" contenteditable="true">${itemDescription}</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold">×</button>`;
        newItemDiv.querySelector('span').addEventListener('input', () => { renderSelectedItems(); updatePreviewDebounced(); });
        newItemDiv.querySelector('button').addEventListener('click', () => { newItemDiv.remove(); renderSelectedItems(); updatePreview(); });
        addItemToActiveDom(newItemDiv);
        searchInput.value = '';
    };

    window.formatText = (command, value = null) => {
        document.execCommand(command, false, value);
        const activeContainer = document.querySelector(`.items-list-container.active`);
        if (document.getSelection().anchorNode && activeContainer.contains(document.getSelection().anchorNode)) {
             renderSelectedItems();
             updatePreviewDebounced();
        }
    };
    
    // --- Inicialização ---
    updatePreview();
});
