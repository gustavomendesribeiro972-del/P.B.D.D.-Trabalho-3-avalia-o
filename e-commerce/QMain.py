import json
import sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QFrame, QFormLayout,
    QTextEdit, QGroupBox, QGridLayout
)

import bcrypt

from databases.supabase_client import supabase, testar_conexao
from databases.mongo import products_collection, teste_mongo
from databases.redis_client import redis_client

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "static" / "images" / "icon.ico"

# Estilo global refinado no padrão Figma Clean Blue
ESTILO = """
QMainWindow {
    background-color: #f0f9ff;
}
QLabel#title {
    font-size: 20px;
    font-weight: 700;
    color: #0369a1;
}
QLabel#subtitle {
    font-size: 13px;
    color: #0284c7;
}
QLineEdit, QTextEdit {
    padding: 10px;
    border: 1.5px solid #bae6fd;
    border-radius: 10px;
    background: #ffffff;
    color: #0f172a;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid #0284c7;
}
QPushButton {
    padding: 9px 16px;
    border-radius: 10px;
    border: none;
    background-color: #0284c7;
    color: white;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #0284c7;
}
QPushButton#nav_button {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #bae6fd;
}
QPushButton#nav_button:hover {
    background-color: #bae6fd;
}
QPushButton#danger {
    background-color: #ef4444;
}
QPushButton#danger:hover {
    background-color: #dc2626;
}
QTableWidget {
    background: #ffffff;
    border: 1.5px solid #bae6fd;
    border-radius: 12px;
    gridline-color: #e0f2fe;
}
QHeaderView::section {
    background-color: #e0f2fe;
    color: #0369a1;
    padding: 10px;
    border: none;
    font-weight: 600;
}
QGroupBox {
    background-color: #ffffff;
    border: 1.5px solid #bae6fd;
    border-radius: 12px;
    margin-top: 10px;
    font-weight: bold;
    color: #0369a1;
    padding: 15px;
}
QFrame#card {
    background: #ffffff;
    border: 1.5px solid #bae6fd;
    border-radius: 14px;
    padding: 24px;
}
QFrame#topbar {
    background: #ffffff;
    border: 1.5px solid #bae6fd;
    border-radius: 12px;
    padding: 8px 16px;
}
"""

def show_error(parent, message: str):
    QMessageBox.critical(parent, "Erro", message)

def show_info(parent, message: str):
    QMessageBox.information(parent, "Sucesso", message)


# ==============================
# TELA DE AUTENTICAÇÃO (Login / Cadastro)
# ==============================
class TelaAutenticacao(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)

        title = QLabel("CentroMercados")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Entre ou crie sua conta para continuar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome de usuário")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-mail")

        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Entrar")
        self.cadastrar_button = QPushButton("Criar conta")
        self.cadastrar_button.setObjectName("nav_button")

        self.login_button.clicked.connect(self.login)
        self.cadastrar_button.clicked.connect(self.cadastro)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(QLabel("Nome de usuário"))
        card_layout.addWidget(self.nome_input)
        card_layout.addWidget(QLabel("E-mail"))
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(QLabel("Senha"))
        card_layout.addWidget(self.senha_input)
        card_layout.addWidget(self.login_button)
        card_layout.addWidget(self.cadastrar_button)

        layout.addWidget(card)

    def login(self):
        email = self.email_input.text().strip()
        password = self.senha_input.text().strip()

        if not email or not password:
            show_error(self, "Preencha e-mail e senha.")
            return

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response.user:
                show_error(self, "Falha na autenticação.")
                return
            
            profile = (
                supabase.table("perfil")
                .select("*")
                .eq("email", email)
                .execute()
            )

            if not profile.data:
                supabase.auth.sign_out()
                show_error(self, "Perfil não encontrado. Verifique seu e-mail...")
                return

            self.main_window.current_user = profile.data[0] if isinstance(profile.data, list) else profile.data
            self.main_window.entrar_sistema()
            show_info(self, f"Bem-vindo, {self.main_window.current_user['nome_usuario']}!")

        except Exception as e:
            show_error(self, f"Falha no login:\n{e}")

    def cadastro(self):
        username = self.nome_input.text().strip()
        email = self.email_input.text().strip()
        senha = self.senha_input.text()

        if not email or not senha or not username:
            show_error(self, "Preencha todos os campos.")
            return

        if len(username) > 30:
            show_error(self, "O nome de usuário deve ter até 30 caracteres.")
            return

        try:
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": senha,
                "options":{ "data": {"nome_usuario": username}}
            })

            if not auth_response.user:
                show_error(self, "Não foi possível criar a conta.")
                return

            show_info(self, "Conta criada com sucesso! Seu perfil foi registrado automaticamente.")
            self.nome_input.clear()
            self.email_input.clear()
            self.senha_input.clear()

        except Exception as e:
            if "rate limit" in str(e).lower():
                show_error(self, "Limite de cadastros atingido. Tente novamente em alguns minutos.")
            else:
                show_error(self, f"Falha no cadastro:\n{e}")


# ==============================
# TELA PRINCIPAL (Conteúdo: Produtos e Listagens)
# ==============================
class TelaPrincipal(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.welcome_label = QLabel("Produtos disponíveis no MongoDB")
        self.welcome_label.setObjectName("title")

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Produto", "Descrição", "Preço", "Estoque", "Empresa ID"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        refresh_button = QPushButton("Atualizar lista de produtos")
        refresh_button.clicked.connect(self.carregar_produtos)

        layout.addWidget(self.welcome_label)
        layout.addWidget(self.products_table)
        layout.addWidget(refresh_button)

    def carregar_produtos(self, termo_busca=""):
        try:
            query = {}
            if termo_busca:
                query = {"nome": {"$regex": termo_busca, "$options": "i"}}

            products = list(products_collection.find(query).sort("criado_em", -1))
            self.products_table.setRowCount(0)

            for product in products:
                row = self.products_table.rowCount()
                self.products_table.insertRow(row)
                self.products_table.setItem(row, 0, QTableWidgetItem(str(product.get("nome", ""))))
                self.products_table.setItem(row, 1, QTableWidgetItem(str(product.get("descricao", ""))))
                self.products_table.setItem(row, 2, QTableWidgetItem(f"R$ {product.get('preco', 0):.2f}"))
                self.products_table.setItem(row, 3, QTableWidgetItem(str(product.get("estoque", 0))))
                self.products_table.setItem(row, 4, QTableWidgetItem(str(product.get("empresa_id", ""))))

        except Exception as e:
            show_error(self, f"Erro ao carregar produtos:\n{e}")


# ==============================
# TELA DE PERFIL
# ==============================
class ProfileWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Meu Perfil de Usuário")
        title.setObjectName("title")

        grid_layout = QGridLayout()
        
        card_esq = QFrame()
        card_esq.setObjectName("card")
        v_esq = QVBoxLayout(card_esq)
        v_esq.addWidget(QLabel("<b>Status da Conta</b>"))
        lbl_avatar = QLabel("👤 [Ativo no Sistema]")
        lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_esq.addWidget(lbl_avatar)
        v_esq.addStretch()

        card_dir = QFrame()
        card_dir.setObjectName("card")
        form = QFormLayout(card_dir)

        self.name_label = QLabel("-")
        self.email_label = QLabel("-")
        self.created_label = QLabel("-")

        form.addRow("Nome de usuário:", self.name_label)
        form.addRow("E-mail:", self.email_label)
        form.addRow("Criado em:", self.created_label)

        grid_layout.addWidget(card_esq, 0, 0)
        grid_layout.addWidget(card_dir, 0, 1)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 2)

        layout.addWidget(title)
        layout.addLayout(grid_layout)
        layout.addStretch()

    def load_profile(self):
        user = self.main_window.current_user
        if not user:
            return

        self.name_label.setText(user.get("nome_usuario", "-"))
        self.email_label.setText(user.get("email", "-"))
        self.created_label.setText(str(user.get("criado_em", "-")))


# ==============================
# TELA DE EMPRESAS
# ==============================
class CompaniesWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Gerenciamento de Empresas")
        title.setObjectName("title")

        subtitle = QLabel("Cadastre uma empresa e vincule-a ao seu perfil.")
        subtitle.setObjectName("subtitle")

        form_group = QGroupBox("Cadastrar nova empresa")
        form = QFormLayout(form_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome fantasia")

        self.cnpj_input = QLineEdit()
        self.cnpj_input.setPlaceholderText("CNPJ, apenas números (14 dígitos)")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-mail da empresa")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Telefone")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descrição da empresa")
        self.description_input.setMaximumHeight(70)

        save_button = QPushButton("Salvar empresa")
        save_button.clicked.connect(self.save_company)

        form.addRow("Nome fantasia:", self.name_input)
        form.addRow("CNPJ:", self.cnpj_input)
        form.addRow("E-mail:", self.email_input)
        form.addRow("Telefone:", self.phone_input)
        form.addRow("Descrição:", self.description_input)
        form.addRow(save_button)

        self.companies_table = QTableWidget()
        self.companies_table.setColumnCount(5)
        self.companies_table.setHorizontalHeaderLabels([
            "Nome", "CNPJ", "E-mail", "Telefone", "Descrição"
        ])
        self.companies_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.companies_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(form_group)
        layout.addWidget(self.companies_table)

    def load_companies(self):
        try:
            response = (
                supabase.table("empresa")
                .select("*")
                .order("criado_em", desc=True)
                .execute()
            )

            companies = response.data or []
            self.companies_table.setRowCount(0)

            for company in companies:
                row = self.companies_table.rowCount()
                self.companies_table.insertRow(row)

                self.companies_table.setItem(row, 0, QTableWidgetItem(company.get("nomefantasia_empresa", "")))
                self.companies_table.setItem(row, 1, QTableWidgetItem(company.get("cnpj_empresa", "")))
                self.companies_table.setItem(row, 2, QTableWidgetItem(company.get("email", "")))
                self.companies_table.setItem(row, 3, QTableWidgetItem(company.get("telefone") or ""))
                self.companies_table.setItem(row, 4, QTableWidgetItem(company.get("descricao_empresa") or ""))

        except Exception as e:
            show_error(self, f"Erro ao carregar empresas:\n{e}")

    def save_company(self):
        user = self.main_window.current_user

        if not user:
            show_error(self, "Faça login antes de cadastrar uma empresa.")
            return

        name = self.name_input.text().strip()
        cnpj = self.cnpj_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        description = self.description_input.toPlainText().strip()

        if not name or not cnpj or not email:
            show_error(self, "Preencha nome fantasia, CNPJ e e-mail.")
            return

        if len(cnpj) != 14 or not cnpj.isdigit():
            show_error(self, "O CNPJ deve conter exatamente 14 números.")
            return

        try:
            # Correção do erro single() aplicando .execute() direto e lendo o retorno da lista
            response = (
                supabase.table("empresa")
                .insert({
                    "nomefantasia_empresa": name,
                    "cnpj_empresa": cnpj,
                    "email": email,
                    "telefone": phone,
                    "descricao_empresa": description or None
                })
                .execute()
            )

            inserted_data = response.data
            if isinstance(inserted_data, list) and len(inserted_data) > 0:
                company_id = inserted_data[0]["id_empresa"]
            else:
                raise Exception("Não foi possível recuperar o ID da empresa recém-criada.")

            supabase.table("empresa_perfil").insert({
                "empresa_id": company_id,
                "perfil_id": user["id_perfil"]
            }).execute()

            self.name_input.clear()
            self.cnpj_input.clear()
            self.email_input.clear()
            self.phone_input.clear()
            self.description_input.clear()

            self.load_companies()
            show_info(self, "Empresa cadastrada e vinculada ao seu perfil.")

        except Exception as e:
            show_error(self, f"Erro ao salvar empresa:\n{e}")


# ==============================
# JANELA PRINCIPAL COM BARRA PERMANENTE DO FIGMA
# ==============================
class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CentroMercados")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1150, 720)
        self.setStyleSheet(ESTILO)

        self.current_user = None

        if not testar_conexao() and teste_mongo():
            QMessageBox.warning(
                self, "Atenção",
                "Alguns serviços (MongoDB/Redis) podem estar indisponíveis."
            )

        # Widget central raiz contendo a barra permanente + o StackedWidget das telas
        central_widget = QWidget()
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # -------------------------------------------------------------
        # BARRA SUPERIOR PERMANENTE (Estilo Figma)
        # -------------------------------------------------------------
        self.top_bar = QFrame()
        self.top_bar.setObjectName("topbar")
        top_layout_bar = QHBoxLayout(self.top_bar)
        top_layout_bar.setContentsMargins(8, 4, 8, 4)

        # 1. Logo / Ícone do App + Nome
        logo_layout = QHBoxLayout()
        self.logo_icon_label = QLabel()
        if ICON_PATH.exists():
            self.logo_icon_label.setPixmap(QIcon(str(ICON_PATH)).pixmap(28, 28))
        logo_title = QLabel("CentroMercados")
        logo_title.setObjectName("title")
        logo_layout.addWidget(self.logo_icon_label)
        logo_layout.addWidget(logo_title)

        # 2. Barra de Pesquisa Centralizada (MongoDB)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar produtos no MongoDB...")
        self.search_input.setFixedWidth(320)
        self.search_input.textChanged.connect(self.executar_pesquisa_mongodb)

        # 3. Botões de Navegação e Ações
        nav_buttons_layout = QHBoxLayout()
        
        self.btn_produtos = QPushButton("Produtos")
        self.btn_produtos.setObjectName("nav_button")
        self.btn_produtos.clicked.connect(lambda: self.mudar_pagina(1))

        self.btn_empresas = QPushButton("Empresas")
        self.btn_empresas.setObjectName("nav_button")
        self.btn_empresas.clicked.connect(lambda: self.mudar_pagina(3))

        self.btn_perfil = QPushButton("Meu Perfil")
        self.btn_perfil.setObjectName("nav_button")
        self.btn_perfil.clicked.connect(lambda: self.mudar_pagina(2))

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.setObjectName("danger")
        self.btn_sair.clicked.connect(self.logout)

        nav_buttons_layout.addWidget(self.btn_produtos)
        nav_buttons_layout.addWidget(self.btn_empresas)
        nav_buttons_layout.addWidget(self.btn_perfil)
        nav_buttons_layout.addWidget(self.btn_sair)

        top_layout_bar.addLayout(logo_layout)
        top_layout_bar.addStretch()
        top_layout_bar.addWidget(self.search_input)
        top_layout_bar.addStretch()
        top_layout_bar.addLayout(nav_buttons_layout)

        # Inicialmente oculta a barra superior na tela de login
        self.top_bar.setVisible(False)

        # -------------------------------------------------------------
        # PILHA DE TELAS (QStackedWidget)
        # -------------------------------------------------------------
        self.stack = QStackedWidget()

        self.auth_window = TelaAutenticacao(self)
        self.main_window = TelaPrincipal(self)
        self.profile_window = ProfileWindow(self)
        self.companies_window = CompaniesWindow(self)

        self.stack.addWidget(self.auth_window)      # Índice 0: Login
        self.stack.addWidget(self.main_window)      # Índice 1: Principal (Produtos)
        self.stack.addWidget(self.profile_window)   # Índice 2: Perfil
        self.stack.addWidget(self.companies_window) # Índice 3: Empresas

        root_layout.addWidget(self.top_bar)
        root_layout.addWidget(self.stack)
        self.setCentralWidget(central_widget)

    def entrar_sistema(self):
        """Exibe a barra superior e vai para a tela principal"""
        self.top_bar.setVisible(True)
        self.main_window.carregar_produtos()
        self.stack.setCurrentIndex(1)

    def mudar_pagina(self, index):
        """Controla a navegação pelos botões da barra superior permanente"""
        if index == 1:
            self.main_window.carregar_produtos()
        elif index == 2:
            self.profile_window.load_profile()
        elif index == 3:
            self.companies_window.load_companies()
        
        self.stack.setCurrentIndex(index)

    def executar_pesquisa_mongodb(self, texto):
        """Dispara a busca em tempo real no MongoDB direto pela barra de pesquisa fixa"""
        # Se estivermos na tela de produtos (índice 1), atualiza a tabela com o filtro
        if self.stack.currentIndex() == 1:
            self.main_window.carregar_produtos(termo_busca=texto)

    def logout(self):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        self.current_user = None
        self.top_bar.setVisible(False)
        self.stack.setCurrentIndex(0)


def main():
    import platform

    app = QApplication(sys.argv)
    icon = QIcon(str(ICON_PATH))

    if icon.isNull():
        print(f"Erro: ícone não encontrado em {ICON_PATH}")
    else:
        app.setWindowIcon(icon)

    if platform.system() == "Windows":
        import ctypes
        myappid = "unifsa.centromercados.v.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    window = App()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()