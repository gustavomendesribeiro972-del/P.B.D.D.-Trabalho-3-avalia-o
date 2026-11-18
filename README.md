# P.B.D.D. Trabalho para a 3 avaliação

## CentroMercados

Aplicação desktop desenvolvida em **Python** e **PyQt6** para o gerenciamento de um marketplace multi-empresa. O projeto integra bancos de dados relacionais, não-relacionais e em memória para oferecer autenticação segura, controle de acesso baseado em papéis (RBAC), catálogo dinâmico de produtos, upload de mídia em nuvem e finalização de pedidos via WhatsApp.

---

## Arquitetura Híbrida e Bancos de Dados

A aplicação utiliza uma arquitetura multi-banco para explorar as vantagens específicas de cada tecnologia:

* **Supabase (PostgreSQL + Auth + Storage):**
  * **Auth:** Autenticação de usuários via e-mail e senha.
  * **Banco Relacional:** Armazenamento estruturado de perfis de usuários (`perfil`), empresas (`empresa`) e relacionamentos entre perfis e empresas (`empresa_perfil`).
  * **Storage (Bucket `produtos-bucket`):** Hospedagem das imagens dos produtos enviadas localmente, gerando URLs públicas consumidas pelos cards da interface.
* **MongoDB (`products_collection`):**
  * Armazenamento orientado a documentos para o catálogo de produtos (`nome`, `preco`, `estoque`, `descricao`, `imagem`, `empresa_id` e `criado_em`), permitindo filtragem por empresa e buscas dinâmicas em tempo real via expressões regulares (`$regex`).
* **Redis (`redis_client`):**
  * Armazenamento em memória (cache) para controle de sessão ativa do usuário (`sessao_usuario:<id_perfil>`, com TTL de 1 hora) e registro temporário da última pesquisa realizada (`ultima_busca:<id_perfil>`, com TTL de 5 minutos).

---

## Controle de Acesso e Perfis (Empresário vs. Cliente)

Durante o cadastro (`TelaCadastro`), o usuário seleciona o seu tipo de conta (`tipo_conta`), definindo as permissões de acesso na interface:

| Perfil | Identificador no Banco | Permissões e Funcionalidades |
| :--- | :--- | :--- |
| **Cliente Comum** | `cliente` | • Visualizar o catálogo geral de produtos em grade dinâmica (6 colunas).<br>• Realizar buscas de produtos em tempo real.<br>• Navegar pelas empresas cadastradas e visualizar o catálogo individual de cada loja.<br>• Visualizar detalhes do produto, adicionar itens ao carrinho e finalizar pedidos via WhatsApp.<br>• Consultar os dados do próprio perfil. |
| **Empresário (Dono de Empresa)** | `empresario` | • Todas as funcionalidades do Cliente Comum.<br>• **Cadastrar Nova Empresa** (`TelaCadastrarEmpresa`), vinculando CNPJ, e-mail, telefone e descrição ao seu perfil.<br>• **Cadastrar Produtos na Empresa** (`TelaCadastrarProdutoEmpresa`) diretamente na página da loja selecionada, com upload de fotos locais (`.png`, `.jpg`, `.jpeg`, `.webp`) para o Supabase Storage. |

---

## Segurança Implementada

* **Criptografia de Senhas:** Utilização da biblioteca `bcrypt` para geração de *salt* e armazenamento exclusivo de hashes seguros (`senha_hash`) na tabela de perfis.
* **Controle de Sessão:** Gerenciamento de sessões ativas via **Redis** com expiração automática e encerramento explícito (`logout`) tanto no Redis quanto no Supabase Auth.
* **Controle de Acesso Baseado em Papéis (RBAC):** Restrição de exibição e execução de ações administrativas condicionada ao perfil `empresario`.

---

## Bibliotecas e Módulos Utilizados

### Interface Gráfica (`PyQt6`)
* **`PyQt6.QtWidgets`:** `QApplication`, `QMainWindow`, `QWidget`, `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QFormLayout`, `QStackedWidget`, `QScrollArea`, `QFrame`, `QLabel`, `QLineEdit`, `QTextEdit`, `QSpinBox`, `QComboBox`, `QPushButton`, `QMessageBox`, `QFileDialog`, `QGraphicsBlurEffect`.
* **`PyQt6.QtCore`:** `Qt`, `QUrl`, `QThread`, `pyqtSignal`, `QSize`.
* **`PyQt6.QtGui`:** `QIcon`, `QDesktopServices`, `QPixmap`, `QImage`.

### Utilitários, Segurança e Integrações
* **`bcrypt`:** Hashing e verificação de senhas.
* **`python-dotenv` (`load_dotenv`):** Carregamento de variáveis de ambiente a partir do arquivo `config.env`.
* **`urllib.request` e `urllib.parse`:** Download assíncrono de imagens públicas do Supabase Storage e codificação de URLs para integração com o WhatsApp.
* **`uuid`, `datetime`, `os`, `sys`, `pathlib.Path`, `platform`, `ctypes`:** Geração de identificadores únicos para arquivos no bucket, carimbos de data/hora ISO 8601, manipulação de caminhos e integração com o sistema operacional.

### Módulos Internos (`databases/`)
* **`databases.supabase_client`:** Instância `supabase` e verificação `testar_conexao()`.
* **`databases.mongo`:** Coleção `products_collection` e verificação `teste_mongo()`.
* **`databases.redis_client`:** Instância `redis_client`.

---

## Estrutura de Classes e Telas

1. **`ImageDownloader(QThread)`:** Thread dedicada ao carregamento assíncrono das imagens dos produtos via URL pública, evitando bloqueios na thread principal da interface.
2. **`TelaAutenticacao` / `TelaLogin` / `TelaCadastro`:** Gerencia a alternância entre login e registro de novos usuários (`cliente` ou `empresario`) por meio de um `QStackedWidget` interno.
3. **`TelaPrincipal` & `ProductCard`:** Renderiza o catálogo completo do MongoDB em uma grade de 6 colunas (`row = i // 6`, `col = i % 6`) com cards estilizados contendo foto redimensionada proporcionalmente, nome, descrição resumida, preço e estoque.
4. **`TelaEmpresasLista`:** Lista todas as empresas cadastradas no Supabase em grade de 3 colunas e disponibiliza o botão **Cadastrar Nova Empresa** para usuários `empresario`.
5. **`TelaEmpresaProdutos`:** Exibe os produtos filtrados pelo `empresa_id` da empresa selecionada e libera o botão **Cadastrar Produto Nesta Empresa** para usuários `empresario`.
6. **`TelaCadastrarEmpresa`:** Formulário com validação de CNPJ (14 dígitos numéricos) que registra a empresa e cria o vínculo na tabela `empresa_perfil`.
7. **`TelaCadastrarProdutoEmpresa`:** Permite selecionar arquivos de imagem locais via `QFileDialog`, realiza o upload com identificador UUID único no Supabase Storage e insere o produto no MongoDB.
8. **`TelaDetalheProduto`:** Exibe a foto ampliada, descrição completa, estoque disponível e seletor de quantidade (`QSpinBox`) para adição ao carrinho.
9. **`CarrinhoWindow` & `CartItemCard`:** Gerencia os itens adicionados, agrupa quantidades de produtos iguais, calcula subtotais/total e redireciona para o WhatsApp (`QDesktopServices.openUrl`) com o resumo estruturado do pedido.
10. **`ProfileWindow`:** Apresenta os dados cadastrais do usuário autenticado.
11. **`App(QMainWindow)`:** Janela raiz que coordena a barra superior (`topbar`), a busca em tempo real no MongoDB, a navegação entre telas e o encerramento de sessão (`logout`).

---

## Como Executar o Projeto

1. Certifique-se de que o arquivo `config.env` está na raiz do projeto com as credenciais do Supabase, MongoDB, Redis e a variável `WHATSAPP_NUMERO`.
2. Instale as dependências necessárias:
   ```bash
   pip install PyQt6 python-dotenv bcrypt supabase pymongo redis
