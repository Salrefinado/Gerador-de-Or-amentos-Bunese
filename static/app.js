document.addEventListener('DOMContentLoaded', () => {
    // --- Variáveis Globais e Seleção de Elementos ---
    const orcForm = document.getElementById('orc-form');
    const previewIframe = document.getElementById('preview');
    const wrapper = document.getElementById('items-editor-wrapper');
    const itemDefinitions = JSON.parse(wrapper.dataset.itemDefinitions || '{}');
    const itemDefinitionsProducao = JSON.parse(wrapper.dataset.itemDefinitionsProducao || '{}');
    const btnSaveOrcamento = document.getElementById('btn-save-orcamento');
    const savedOrcamentosList = document.getElementById('saved-orcamentos-list');
    const toggleSavedOrcamentosBtn = document.getElementById('toggle-saved-orcamentos');
    const savedOrcamentosContainer = document.getElementById('saved-orcamentos-container');
    const searchOrcamentoInput = document.getElementById('search-orcamento');
    const btnUpdatePreview = document.getElementById('btn-update-preview');

    const btnCliente = document.getElementById('orcamento-cliente-btn');
    const btnProducao = document.getElementById('orcamento-producao-btn');
    const pageTabsContainer = document.getElementById('page-tabs');
    const editorContainer = document.querySelector('#items-editor-wrapper');
    const btnAddPage = document.getElementById('btn-add-page');

    let itemsCliente = { 1: [] };
    let itemsProducao = { 1: [] };
    let currentPage = 1;
    let currentMode = 'cliente'; // 'cliente' ou 'producao'
    let previewTimer;

    // --- Lógica para Menus Suspensos (Dropdowns) ---
    document.querySelectorAll('.dropdown-trigger').forEach(trigger => {
        trigger.addEventListener('click', (event) => {
            event.stopPropagation();
            const menu = trigger.nextElementSibling;
            const arrow = trigger.querySelector('svg');
            
            document.querySelectorAll('.dropdown-menu').forEach(otherMenu => {
                if (otherMenu !== menu) {
                    otherMenu.classList.add('hidden');
                    if (otherMenu.previousElementSibling.querySelector('svg')) {
                       otherMenu.previousElementSibling.querySelector('svg').style.transform = 'rotate(0deg)';
                    }
                }
            });

            menu.classList.toggle('hidden');
            if(arrow) arrow.style.transform = menu.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
        });
    });

    window.addEventListener('click', () => {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.classList.add('hidden');
            if (menu.previousElementSibling.querySelector('svg')) {
                menu.previousElementSibling.querySelector('svg').style.transform = 'rotate(0deg)';
            }
        });
    });
    
    // --- Funções de Gerenciamento de Orçamento (Modo) ---
    function switchMode(newMode) {
        syncDomToData(); // Salva o estado atual do DOM na variável JS
        currentMode = newMode;

        if (currentMode === 'cliente') {
            btnCliente.classList.add('bg-indigo-600', 'text-white');
            btnCliente.classList.remove('bg-gray-200', 'text-gray-700');
            btnProducao.classList.add('bg-gray-200', 'text-gray-700');
            btnProducao.classList.remove('bg-indigo-600', 'text-white');
        } else {
            btnProducao.classList.add('bg-indigo-600', 'text-white');
            btnProducao.classList.remove('bg-gray-200', 'text-gray-700');
            btnCliente.classList.add('bg-gray-200', 'text-gray-700');
            btnCliente.classList.remove('bg-indigo-600', 'text-white');
        }
        
        renderEditorFromData();
        updatePreview();
    }
    
    // --- Sincronização de DADOS e DOM ---

    function syncDomToData() {
        const dataTarget = currentMode === 'cliente' ? itemsCliente : itemsProducao;
        document.querySelectorAll('.items-list-container').forEach(container => {
            const pageNum = parseInt(container.id.split('-').pop());
            if (!dataTarget[pageNum]) dataTarget[pageNum] = [];
            
            dataTarget[pageNum] = []; // Limpa para reconstruir
            container.querySelectorAll('.selected-item, .selected-image-item').forEach(el => {
                dataTarget[pageNum].push({
                    html: el.querySelector('span[contenteditable="true"]')?.innerHTML || el.innerHTML,
                    isSeparator: el.classList.contains('stage-separator'),
                    isImage: el.classList.contains('selected-image-item'),
                    imagePath: el.dataset.imagePath,
                    imageTitle: el.dataset.title,
                    imageName: el.dataset.imageName
                });
            });
        });
    }

    function renderEditorFromData() {
        const dataSource = currentMode === 'cliente' ? itemsCliente : itemsProducao;
        const pageNumbers = Object.keys(dataSource);

        pageTabsContainer.innerHTML = '';
        editorContainer.querySelectorAll('.items-list-container').forEach(c => c.remove());

        let maxPage = Math.max(1, ...pageNumbers.map(n => parseInt(n)));

        for(let i = 1; i <= maxPage; i++) {
            if(!dataSource[i]) dataSource[i] = [];
            
            const newTab = document.createElement('button');
            newTab.type = 'button';
            newTab.className = 'page-tab flex items-center px-4 py-2 rounded-md font-semibold'; // Estilo base do botão
            newTab.dataset.page = i;

            const tabText = document.createElement('span');
            tabText.textContent = `Página ${i}`;
            newTab.appendChild(tabText);

            if (i > 1) {
                const deleteBtn = document.createElement('span');
                deleteBtn.className = 'ml-2 text-red-400 hover:text-red-600 delete-page';
                deleteBtn.innerHTML = '&#128465;';
                deleteBtn.dataset.pageToDelete = i;
                newTab.appendChild(deleteBtn);
            }
            pageTabsContainer.appendChild(newTab);
            
            const newContainer = document.createElement('div');
            newContainer.className = 'items-list-container';
            newContainer.id = `items-list-container-${i}`;
            editorContainer.appendChild(newContainer);
            
            if (dataSource[i] && dataSource[i].length > 0) {
                 dataSource[i].forEach(itemData => {
                    const el = createDomItem(itemData);
                    newContainer.appendChild(el);
                });
            } else {
                newContainer.innerHTML = `<p class="text-sm text-gray-500 italic mt-1 default-text">Nenhum item adicionado.</p>`;
            }
        }
        switchPage(currentPage > maxPage ? maxPage : currentPage);
    }
    
    function createDomItem(itemData) {
        const div = document.createElement('div');
        let editableSpan;

        if(itemData.isImage) {
            div.className = 'selected-image-item flex items-center mb-2 p-2 bg-gray-200 border rounded';
            div.dataset.imagePath = itemData.imagePath;
            div.dataset.title = itemData.imageTitle;
            div.dataset.imageName = itemData.imageName;
            div.innerHTML = `<span class="flex-grow p-1 italic text-gray-600 text-sm">Img: ${itemData.imageName} (${itemData.imageTitle})</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold">×</button>`;
        } else {
             div.className = itemData.isSeparator 
                ? 'selected-item stage-separator flex items-center mb-2 p-2 bg-yellow-100 border-yellow-300 rounded font-bold'
                : 'selected-item flex items-center mb-2 p-2 bg-white border rounded';
            div.innerHTML = `<span class="flex-grow p-1" contenteditable="true">${itemData.html}</span><button type="button" class="ml-2 text-red-500 hover:text-red-700 font-bold">×</button>`;
            editableSpan = div.querySelector('span');
        }

        div.querySelector('button').addEventListener('click', () => {
            div.remove(); 
            syncDomToData();
            updatePreviewDebounced(); 
        });
        
        if(editableSpan) {
            editableSpan.addEventListener('input', () => { 
                syncDomToData();
                updatePreviewDebounced(); 
            });
        }
        
        return div;
    }

    function updateHiddenInputs() {
        syncDomToData(); // Garante que os dados JS estão atualizados com o DOM
        
        ['cliente', 'producao'].forEach(mode => {
            const dataSource = mode === 'cliente' ? itemsCliente : itemsProducao;
            const input = document.getElementById(`hidden-items-input-${mode}`);
            const allPagesContent = [];

            Object.keys(dataSource).sort((a, b) => a - b).forEach(pageNum => {
                const itemsOnPage = (dataSource[pageNum] || []).map(item => {
                    if (item.isImage) {
                        return `@@IMAGE_START@@${item.imagePath}|${item.imageTitle}`;
                    }
                    let formattedHtml = item.html.trim();
                    return item.isSeparator ? `@@ETAPA_START@@${formattedHtml}` : formattedHtml;
                });
                allPagesContent.push(itemsOnPage.join('\n'));
            });
            input.value = allPagesContent.join('\n@@PAGE_BREAK@@\n');
        });
    }

    function updatePreview() {
        updateHiddenInputs();
        const formData = new FormData(orcForm);
        formData.append('mode', currentMode);
        
        const items = currentMode === 'cliente' 
            ? formData.get('items_cliente') 
            : formData.get('items_producao');
        formData.append('items', items);

        fetch('/generate', { method: 'POST', body: formData })
            .then(response => response.ok ? response.blob() : Promise.reject('Erro ao gerar preview.'))
            .then(blob => {
                const url = URL.createObjectURL(blob);
                previewIframe.src = `${url}#toolbar=0&navpanes=0`;
            })
            .catch(error => {
                console.error(error);
                previewIframe.src = 'about:blank';
            });
    }

    function updatePreviewDebounced() {
        clearTimeout(previewTimer);
        previewTimer = setTimeout(updatePreview, 500);
    }
    
    // --- Funções de Gerenciamento de Página ---
    function switchPage(targetPage) {
        currentPage = targetPage;
        document.querySelectorAll('.page-tab').forEach(tab => {
            const isTarget = parseInt(tab.dataset.page) === currentPage;
            tab.classList.toggle('bg-indigo-600', isTarget);
            tab.classList.toggle('text-white', isTarget);
            tab.classList.toggle('bg-gray-200', !isTarget);
            tab.classList.toggle('text-gray-700', !isTarget);
            tab.classList.toggle('hover:bg-gray-300', !isTarget);
        });
        document.querySelectorAll('.items-list-container').forEach(container => {
            container.classList.toggle('active', parseInt(container.id.split('-').pop()) === currentPage);
        });
    }
    
    function addNewPage() {
        syncDomToData();
        const maxPage = Math.max(0, ...Object.keys(itemsCliente).map(n => parseInt(n)));
        if(maxPage >= 3) {
            alert("O número máximo de páginas é 3.");
            return;
        }
        const newPageNum = maxPage + 1;
        itemsCliente[newPageNum] = [];
        itemsProducao[newPageNum] = [];
        currentPage = newPageNum;
        renderEditorFromData();
        updatePreview();
    }

    function deletePage(pageToDelete) {
        if (pageToDelete <= 1) return;
        syncDomToData();

        delete itemsCliente[pageToDelete];
        delete itemsProducao[pageToDelete];

        // Re-indexar páginas
        const reIndex = (items) => {
            const newItems = {};
            let newPage = 1;
            Object.keys(items).sort((a,b) => a-b).forEach(oldPage => {
                if(parseInt(oldPage) !== pageToDelete) {
                    newItems[newPage] = items[oldPage];
                    newPage++;
                }
            });
            return newItems;
        };

        itemsCliente = reIndex(itemsCliente);
        itemsProducao = reIndex(itemsProducao);
        
        if (currentPage >= pageToDelete) {
            currentPage--;
        }

        renderEditorFromData();
        updatePreview();
    }
    
    // --- Funções de Adição de Conteúdo ---
    function addItemToActiveDom(element) {
        const activeContainer = document.querySelector(`.items-list-container.active`);
        if(!activeContainer) return;
        const defaultText = activeContainer.querySelector('.default-text');
        if (defaultText) defaultText.style.display = 'none';
        activeContainer.appendChild(element);
    }

    function addContent(itemDataCliente, itemDataProducao) {
        syncDomToData();

        if (!itemsCliente[currentPage]) itemsCliente[currentPage] = [];
        if (!itemsProducao[currentPage]) itemsProducao[currentPage] = [];

        itemsCliente[currentPage].push(itemDataCliente);
        itemsProducao[currentPage].push(itemDataProducao);

        const domItem = createDomItem(currentMode === 'cliente' ? itemDataCliente : itemDataProducao);
        addItemToActiveDom(domItem);

        updatePreviewDebounced();
    }

    window.addItemFromSearch = () => {
        const searchInput = document.getElementById('item-input-search');
        const itemCode = searchInput.value.trim();
        if (!itemCode) return;

        const descCliente = itemDefinitions[itemCode] || itemCode;
        const descProducao = itemDefinitionsProducao[itemCode] || itemDefinitions[itemCode] || itemCode;
        
        addContent(
            { html: descCliente, isSeparator: false },
            { html: descProducao, isSeparator: false }
        );
        searchInput.value = '';
    };

    window.addEtapaSeparator = (stageNumber) => {
        const stageText = { "1": "<b>Etapa 1 Estrutural:</b>", "2": "<b>Etapa 2 Equipamentos:</b>", "3": "" }[stageNumber] || "";
        addContent(
            { html: stageText, isSeparator: true },
            { html: stageText, isSeparator: true }
        );
        if(!stageText) {
             setTimeout(() => document.querySelector('.items-list-container.active').lastChild.querySelector('span').focus(), 0);
        }
    };
    
    function addImageToDom(imageName, imagePath, title) {
        const commonData = {
            isImage: true,
            imagePath: imagePath,
            imageTitle: title,
            imageName: imageName
        };
        addContent(commonData, commonData);
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

    window.formatText = (command, value = null) => {
        document.execCommand(command, false, value);
        const activeContainer = document.querySelector(`.items-list-container.active`);
        if (document.getSelection().anchorNode && activeContainer.contains(document.getSelection().anchorNode.parentElement)) {
            syncDomToData();
            updatePreviewDebounced();
        }
    };
    
    // --- Funções de Banco de Dados ---
    function saveOrcamento() {
        updateHiddenInputs();
        const formData = new FormData(orcForm);

        fetch('/orcamentos', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                alert(`Orçamento ${data.status === 'updated' ? 'atualizado' : 'salvo'} com sucesso!`);
                loadSavedOrcamentos();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocorreu um erro ao salvar o orçamento.');
            });
    }

    function loadSavedOrcamentos() {
        fetch('/orcamentos')
            .then(response => response.json())
            .then(data => {
                savedOrcamentosList.innerHTML = '';
                data.forEach(orcamento => {
                    const div = document.createElement('div');
                    div.className = 'orcamento-item flex justify-between items-center p-2 border rounded';
                    div.innerHTML = `
                        <span class="orcamento-info">${orcamento.numero} - ${orcamento.cliente} (${new Date(orcamento.data_atualizacao).toLocaleDateString()})</span>
                        <div class="flex items-center">
                            <button type="button" class="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600" onclick="loadOrcamento(${orcamento.id})">Carregar</button>
                            <button type="button" class="text-red-500 hover:text-red-700 ml-2" onclick="showDeleteConfirmation(${orcamento.id})">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    `;
                    savedOrcamentosList.appendChild(div);
                });
            });
    }
    
    window.showDeleteConfirmation = (id) => {
        const modal = document.getElementById('delete-confirmation-modal');
        const confirmBtn = document.getElementById('confirm-delete-btn');
        const cancelBtn = document.getElementById('cancel-delete-btn');
        const confirmationInput = document.getElementById('delete-confirmation-input');

        confirmationInput.value = '';
        modal.classList.remove('hidden');

        const confirmHandler = () => {
            if (confirmationInput.value === '0000') {
                deleteOrcamento(id);
                closeModal();
            } else {
                alert('Código de confirmação incorreto.');
            }
        };

        const cancelHandler = () => {
            closeModal();
        };
        
        const closeModal = () => {
            modal.classList.add('hidden');
            confirmBtn.removeEventListener('click', confirmHandler);
            cancelBtn.removeEventListener('click', cancelHandler);
        };

        confirmBtn.addEventListener('click', confirmHandler);
        cancelBtn.addEventListener('click', cancelHandler);
    };

    function deleteOrcamento(id) {
        fetch(`/orcamentos/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'deleted') {
                    alert('Orçamento apagado com sucesso!');
                    loadSavedOrcamentos();
                } else {
                    alert('Falha ao apagar o orçamento.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocorreu um erro ao apagar o orçamento.');
            });
    }

    window.loadOrcamento = (id) => {
        fetch(`/orcamentos/${id}`)
            .then(response => response.json())
            .then(data => {
                const orcamentoData = data.dados;
                for (const key in orcamentoData) {
                    const input = document.getElementById(key);
                    if (input) {
                        input.value = orcamentoData[key];
                    }
                }
                
                const parseItems = (itemsString) => {
                    if (!itemsString) return { 1: [] };
                    const pages = itemsString.split('@@PAGE_BREAK@@');
                    const itemsByPage = {};
                    pages.forEach((pageContent, index) => {
                        const pageNum = index + 1;
                        itemsByPage[pageNum] = [];
                        const lines = pageContent.trim().split('\n');
                        lines.forEach(line => {
                            if (line.startsWith('@@IMAGE_START@@')) {
                                const [path, title] = line.replace('@@IMAGE_START@@', '').split('|');
                                itemsByPage[pageNum].push({
                                    isImage: true,
                                    imagePath: path,
                                    imageTitle: title,
                                    imageName: path.split('/').pop()
                                });
                            } else if (line.startsWith('@@ETAPA_START@@')) {
                                itemsByPage[pageNum].push({
                                    html: line.replace('@@ETAPA_START@@', ''),
                                    isSeparator: true
                                });
                            } else if(line) {
                                itemsByPage[pageNum].push({ html: line, isSeparator: false });
                            }
                        });
                    });
                    return itemsByPage;
                };

                itemsCliente = parseItems(orcamentoData.items_cliente || '');
                itemsProducao = parseItems(orcamentoData.items_producao || '');
                
                renderEditorFromData();
                updatePreview();
                alert('Orçamento carregado!');

                // Recolher o accordion
                const arrow = document.getElementById('accordion-arrow');
                const content = savedOrcamentosContainer;
                content.style.maxHeight = null;
                arrow.style.transform = 'rotate(0deg)';
            });
    };

    function filterOrcamentos() {
        const filter = searchOrcamentoInput.value.toUpperCase();
        const items = savedOrcamentosList.getElementsByClassName('orcamento-item');
        for (let i = 0; i < items.length; i++) {
            const info = items[i].getElementsByClassName('orcamento-info')[0];
            const txtValue = info.textContent || info.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                items[i].style.display = "";
            } else {
                items[i].style.display = "none";
            }
        }
    }

    // --- Event Listeners ---
    btnCliente.addEventListener('click', () => switchMode('cliente'));
    btnProducao.addEventListener('click', () => switchMode('producao'));
    btnSaveOrcamento.addEventListener('click', saveOrcamento);
    searchOrcamentoInput.addEventListener('keyup', filterOrcamentos);
    btnUpdatePreview.addEventListener('click', updatePreview);

    toggleSavedOrcamentosBtn.addEventListener('click', () => {
        const arrow = document.getElementById('accordion-arrow');
        const content = savedOrcamentosContainer;
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
            arrow.style.transform = 'rotate(0deg)';
        } else {
            content.style.maxHeight = content.scrollHeight + "px";
            arrow.style.transform = 'rotate(180deg)';
        }
    });

    pageTabsContainer.addEventListener('click', (e) => {
        const tab = e.target.closest('.page-tab');
        if (tab) {
            if (e.target.classList.contains('delete-page')) {
                const pageNum = parseInt(e.target.dataset.pageToDelete);
                if (confirm(`Tem certeza que deseja excluir a Página ${pageNum}?`)) {
                    deletePage(pageNum);
                }
            } else {
                syncDomToData();
                switchPage(parseInt(tab.dataset.page));
            }
        }
    });
    
    orcForm.addEventListener('submit', (e) => {
        e.preventDefault();
        updateHiddenInputs();
        const formData = new FormData(orcForm);

        const downloadPdf = (base64, filename) => {
            const byteCharacters = atob(base64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const file = new Blob([byteArray], { type: 'application/pdf' });
            const fileURL = URL.createObjectURL(file);
            
            const link = document.createElement('a');
            link.href = fileURL;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        };
        
        fetch('/generate-pdfs', { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => {
                if (data.cliente && data.producao) {
                    downloadPdf(data.cliente, data.filename_cliente);
                    downloadPdf(data.producao, data.filename_producao);
                } else {
                    alert('Erro ao gerar os PDFs.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocorreu um erro inesperado.');
            });
    });

    btnAddPage.addEventListener('click', addNewPage);
    document.getElementById('btn-add-porta').addEventListener('click', () => addImageToDom('Fotos Porta.png', '/static/Referencia/Fotos Porta.png', 'Fotos referência: Estrutura porta guilhotina'));
    document.getElementById('btn-add-inox').addEventListener('click', () => addImageToDom('Foto Bancada Inox.png', '/static/Referencia/Foto Bancada Inox.png', 'Fotos referência: Equipamentos bancada inox'));
    document.getElementById('btn-add-pedra').addEventListener('click', () => addImageToDom('Fotos Bancada Pedra.png', '/static/Referencia/Fotos Bancada Pedra.png', 'Fotos referência: Equipamentos bancada Pedra'));
    document.getElementById('image-upload-input').addEventListener('change', uploadAndAddImage);

    orcForm.querySelectorAll('input[type="text"], input[type="date"]').forEach(input => {
        input.addEventListener('input', updatePreviewDebounced);
    });

    // --- Inicialização ---
    renderEditorFromData(); // Renderiza o estado inicial
    updatePreview();
    loadSavedOrcamentos();
});
