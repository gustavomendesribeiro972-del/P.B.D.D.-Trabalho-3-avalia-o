import json, sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QFrame, QFormLayout,
    QTextEdit, QGroupBox    
)

import bcrypt

from databases.supabase_client import ( supabase, testar_conexao )
from databases.mongo import (products_collection, teste_mongo)
from databases.redis_client import redis_client

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "static" / "images" / "icone.ico"

#Estilo:
ESTILO = """
QMainWindow {
    background-color: #f4f6f8;
}
QLabel#title {
    font-size: 26px;
    font-weight: 700;
    color: #1f2937;
}
QLabel#subtitle {
    font-size: 14px;
    color: #6b7280;
}
QLineEdit, QTextEdit {
    padding: 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background: white;
}
QPushButton {
    padding: 10px 16px;
    border-radius: 8px;
    border: none;
    background-color: #2563eb;
    color: white;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton#secondary {
    background-color: #e5e7eb;
    color: #111827;
}
QPushButton#danger {
    background-color: #dc2626;
}
QTableWidget {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    gridline-color: #e5e7eb;
}
QHeaderView::section {
    background-color: #f9fafb;
    padding: 10px;
    border: none;
    font-weight: 600;
}
"""

#funções:

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


def show_error(parent, message: str):
    QMessageBox.critical(parent, "Erro", message)


def show_info(parent, message: str):
    QMessageBox.information(parent, "Sucesso", message)

#AS TELAS:
#Autenticação:
class TelaAutenticacao(QWidget):
    def __init__(self, stack, main_window):
        super().__init__()
        self.stack = stack
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 14px;
                padding: 28px;
            }
        """)

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
        self.cadastrar_button.setObjectName("secundario")

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

            user = response.user
            profile = (
                supabase.table("perfil")
                .select("*")
                .eq("email", email)
                .single()
                .execute()
            )

            if profile.data is None:
                show_error(self, "Perfil não encontrado. Verifique seu e-mail...")
                return

            self.main_window.current_user = profile.data
            self.main_window.go_main()
            show_info(self, f"Bem-vindo, {profile.data['nome_usuario']}!")

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
                "password": senha
            })

            if auth_response:
                supabase.table("perfil").insert({
                    "nome_usuario": username,
                    "email": email
                }).execute()

                show_info(
                    self,
                    "Conta criada com sucesso!"
                )
            else:
                print("Deu erro: ", auth_response)

        except Exception as e:
            if "rate limit" in str(e).lower():
                show_error(self, "Limite de cadastros atingido. Tente novamente em alguns minutos.")
            else:
                show_error(self, f"Falha no cadastro:\n{e}")



#Tela Principal:
class TelaPrincipal(QWidget):
    def __init__(self, stack, main_window):
        super().__init__()
        self.stack = stack
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("CentroMercados")
        title.setObjectName("title")

        self.welcome_label = QLabel("Produtos disponíveis")
        self.welcome_label.setObjectName("subtitle")

        title_box.addWidget(title)
        title_box.addWidget(self.welcome_label)

        buttons = QHBoxLayout()

        profile_button = QPushButton("Meu perfil")
        company_button = QPushButton("Empresas")
        logout_button = QPushButton("Sair")
        logout_button.setObjectName("danger")

        profile_button.clicked.connect(self.main_window.go_profile)
        company_button.clicked.connect(self.main_window.go_companies)
        logout_button.clicked.connect(self.logout)

        buttons.addWidget(profile_button)
        buttons.addWidget(company_button)
        buttons.addWidget(logout_button)

        header.addLayout(title_box)
        header.addStretch()
        header.addLayout(buttons)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Produto", "Descrição", "Preço", "Estoque", "Empresa"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.products_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.products_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        refresh_button = QPushButton("Atualizar produtos")
        refresh_button.clicked.connect(self.carregar_produtos)

        layout.addLayout(header)
        layout.addWidget(self.products_table)
        layout.addWidget(refresh_button)

    def logout(self):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        self.main_window.current_user = None
        self.welcome_label.setText("Produtos disponíveis")
        self.stack.setCurrentIndex(0)

    def carregar_produtos(self):
        try:
            # FIX: força refresh limpando o cache
            redis_client.delete("centro_mercados:produtos")

            response = products_collection.find().sort("criado_em", -1)  # FIX: sem ()

            products = []
            for product in response:
                products.append({
                    "nome": product.get("nome", ""),
                    "descricao": product.get("descricao", ""),
                    "preco": product.get("preco", 0),
                    "estoque": product.get("estoque", 0),
                    "empresa_id": product.get("empresa_id")
                })

            # FIX: removido default=str (inútil)
            redis_client.set(
                "centro_mercados:produtos",
                json.dumps(products),
                ex=60
            )

            self._preencher_tabela(products)

        except Exception as e:
            show_error(self, f"Erro ao carregar produtos:\n{e}")

    def _preencher_tabela(self, products):
        self.products_table.setRowCount(0)
        for product in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product.get("nome", ""))))
            self.products_table.setItem(row, 1, QTableWidgetItem(str(product.get("descricao", ""))))
            self.products_table.setItem(row, 2, QTableWidgetItem(f"R$ {product.get('preco', 0):.2f}"))
            self.products_table.setItem(row, 3, QTableWidgetItem(str(product.get("estoque", 0))))
            self.products_table.setItem(row, 4, QTableWidgetItem(str(product.get("empresa_id", ""))))



# ==============================
# TELA DE PRODUTOS
# ==============================

class ProductsWindow(QWidget):
    def __init__(self, stack, main_window):
        super().__init__()
        self.stack = stack
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Produtos")
        title.setObjectName("title")

        subtitle = QLabel(
            "Consulta dos produtos cadastrados no MongoDB, com cache no Redis."
        )
        subtitle.setObjectName("subtitle")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar produto pelo nome...")

        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.search_products)

        back_button = QPushButton("Voltar")
        back_button.setObjectName("secondary")
        back_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        search_row = QHBoxLayout()
        search_row.addWidget(self.search_input)
        search_row.addWidget(search_button)
        search_row.addWidget(back_button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Produto", "Descrição", "Preço", "Estoque", "Empresa"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(search_row)
        layout.addWidget(self.table)

    def search_products(self):
        term = self.search_input.text().strip()

        try:
            query = {}

            if term:
                query = {"nome": {"$regex": term, "$options": "i"}}

            products = list(products_collection.find(query).sort("nome", 1))

            self.table.setRowCount(0)

            for product in products:
                row = self.table.rowCount()
                self.table.insertRow(row)

                self.table.setItem(
                    row, 0, QTableWidgetItem(product.get("nome", ""))
                )
                self.table.setItem(
                    row, 1, QTableWidgetItem(product.get("descricao", ""))
                )
                self.table.setItem(
                    row, 2, QTableWidgetItem(f"R$ {product.get('preco', 0):.2f}")
                )
                self.table.setItem(
                    row, 3, QTableWidgetItem(str(product.get("estoque", 0)))
                )
                self.table.setItem(
                    row, 4, QTableWidgetItem(str(product.get("empresa_id", "")))
                )

        except Exception as e:
            show_error(self, f"Erro ao buscar produtos:\n{e}")


# ==============================
# TELA DE PERFIL
# ==============================

class ProfileWindow(QWidget):
    def __init__(self, stack, main_window):
        super().__init__()
        self.stack = stack
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Meu perfil")
        title.setObjectName("title")

        self.info_group = QGroupBox("Dados do perfil")
        form = QFormLayout(self.info_group)

        self.name_label = QLabel("-")
        self.email_label = QLabel("-")
        self.created_label = QLabel("-")

        form.addRow("Nome de usuário:", self.name_label)
        form.addRow("E-mail:", self.email_label)
        form.addRow("Criado em:", self.created_label)

        back_button = QPushButton("Voltar")
        back_button.setObjectName("secondary")
        back_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        layout.addWidget(title)
        layout.addWidget(self.info_group)
        layout.addStretch()
        layout.addWidget(back_button)

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
    def __init__(self, stack, main_window):
        super().__init__()
        self.stack = stack
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Empresas")
        title.setObjectName("title")

        subtitle = QLabel("Cadastre uma empresa e vincule-a ao seu perfil.")
        subtitle.setObjectName("subtitle")

        form_group = QGroupBox("Cadastrar empresa")
        form = QFormLayout(form_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome fantasia")

        self.cnpj_input = QLineEdit()
        self.cnpj_input.setPlaceholderText("CNPJ, apenas números")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-mail da empresa")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Telefone")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descrição da empresa")
        self.description_input.setMaximumHeight(90)

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
        self.companies_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        back_button = QPushButton("Voltar")
        back_button.setObjectName("secondary")
        back_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(form_group)
        layout.addWidget(self.companies_table)
        layout.addWidget(back_button)

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

                self.companies_table.setItem(
                    row, 0, QTableWidgetItem(company.get("nomefantasia_empresa", ""))
                )
                self.companies_table.setItem(
                    row, 1, QTableWidgetItem(company.get("cnpj_empresa", ""))
                )
                self.companies_table.setItem(
                    row, 2, QTableWidgetItem(company.get("email", ""))
                )
                self.companies_table.setItem(
                    row, 3, QTableWidgetItem(company.get("telefone") or "")
                )
                self.companies_table.setItem(
                    row, 4, QTableWidgetItem(company.get("descricao_empresa") or "")
                )

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
            response = (
                supabase.table("empresa")
                .insert({
                    "nomefantasia_empresa": name,
                    "cnpj_empresa": cnpj,
                    "email": email,
                    "telefone": phone,
                    "descricao_empresa": description or None
                })
                .select("id_empresa")
                .single()
                .execute()
            )

            company_id = response.data["id_empresa"]

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
# JANELA PRINCIPAL
# ==============================

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CentroMercados")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1100, 700)
        self.setStyleSheet(ESTILO)

        self.current_user = None

        if not testar_conexao() and teste_mongo():
            QMessageBox.warning(
                self, "Atenção",
                "Alguns serviços (MongoDB/Redis) podem estar indisponíveis."
            )

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.auth_window = TelaAutenticacao(self.stack, self)
        self.main_window = TelaPrincipal(self.stack, self)
        self.products_window = ProductsWindow(self.stack, self)
        self.profile_window = ProfileWindow(self.stack, self)
        self.companies_window = CompaniesWindow(self.stack, self)

        self.stack.addWidget(self.auth_window)
        self.stack.addWidget(self.main_window)
        self.stack.addWidget(self.products_window)
        self.stack.addWidget(self.profile_window)
        self.stack.addWidget(self.companies_window)

    def go_main(self):
        self.main_window.carregar_produtos()
        self.stack.setCurrentIndex(1)

    def go_products(self):
        self.products_window.search_products()
        self.stack.setCurrentIndex(2)

    def go_profile(self):
        self.profile_window.load_profile()
        self.stack.setCurrentIndex(3)

    def go_companies(self):
        self.companies_window.load_companies()
        self.stack.setCurrentIndex(4)


def main():
    import platform

    if platform.system() == "Windows":
        import ctypes
        myappid = "unifsa.centromercados.v.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication([])
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    window = App()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
