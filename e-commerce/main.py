import sys, os, uuid, bcrypt, datetime
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap, QImage
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget,
    QMessageBox, QFrame, QFormLayout, QTextEdit, QGridLayout, 
    QGraphicsBlurEffect, QSpinBox, QScrollArea, QComboBox, QFileDialog
)
import urllib.request

from databases.supabase_client import supabase, testar_conexao
from databases.mongo import products_collection, teste_mongo
from databases.redis_client import redis_client

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "static" / "images" / "icon1.png"

load_dotenv(BASE_DIR / "config.env")
WHATSAPP_NUMERO = os.getenv("WHATSAPP_NUMERO", "")

# Estilo global com Helvetica e componentes estilizados:
ESTILO = """
QMainWindow {
    font-family: 'Helvetica', Arial, sans-serif;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #f8fafc,
        stop:0.45 #f1f5f9,
        stop:1 #e2e8f0
    );
}

QWidget#background {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #f1f5f9,
        stop:0.45 #e2e8f0,
        stop:1 #cbd5e1
    );
}

QFrame#topbar {
    background: #334155;
    border: 1px solid rgba(255, 255, 255, 40);
}

QFrame#card {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 18px;
}

QLabel {
    color: #1e293b;
    font-family: 'Helvetica', Arial, sans-serif;
}

QLabel#title {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
}

QLabel#subtitle {
    font-size: 13px;
    color: #64748b;
}

QLineEdit, QTextEdit, QSpinBox {
    padding: 8px 12px;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    background: #ffffff;
    color: #0f172a;
    selection-background-color: #475569;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid #0f172a;
    background: #ffffff;
}

QPushButton {
    padding: 9px 18px;
    border-radius: 12px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    color: #334155;
    font-weight: 700;
}

QPushButton:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
}

QPushButton#nav_button {
    background: #e2e8f0;
    color: #1e293b;
    border: 1px solid #cbd5e1;
}

QPushButton#nav_button:hover {
    background: #cbd5e1;
}

QPushButton#success {
    background: #1e293b;
    border: 1px solid #0f172a;
    color: #ffffff;
}

QPushButton#success:hover {
    background: #0f172a;
}

QPushButton#danger {
    background: #ef4444;
    border: 1px solid #5c2626;
    color: white;
}

QPushButton#danger:hover {
    background: #ac2626;
}

QPushButton#product_card {
    background-color: #ffffff;
    border: 2px solid #64748b;
    border-radius: 16px;
    text-align: left;
}

QPushButton#product_card:hover {
    background-color: #f8fafc;
    border: 2px solid #2563eb;
}

QPushButton#product_card:pressed {
    background-color: #f1f5f9;
    border: 2px solid #1d4ed8;
}

QTableWidget {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    gridline-color: #f1f5f9;
    alternate-background-color: #f8fafc;
}

QTableWidget::item {
    padding: 8px;
    color: #1e293b;
}

QTableWidget::item:selected {
    background: #334155;
    color: white;
}

QHeaderView::section {
    background: #f1f5f9;
    color: #334155;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #cbd5e1;
    font-weight: 700;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    margin-top: 14px;
    padding: 18px;
    font-weight: 700;
    color: #1e293b;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background: #94a3b8;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #64748b;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

def show_error(parent, message: str):
    QMessageBox.critical(parent, "Erro", message)

def show_info(parent, message: str):
    QMessageBox.information(parent, "Sucesso", message)

class ImageDownloader(QThread):
    finished = pyqtSignal(QPixmap)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            if not self.url:
                self.finished.emit(QPixmap())
                return
            data = urllib.request.urlopen(self.url, timeout=5).read()
            image = QImage.fromData(data)
            pixmap = QPixmap.fromImage(image)
            self.finished.emit(pixmap)
        except Exception:
            self.finished.emit(QPixmap())


class TelaLogin(QWidget):
    def __init__(self, main_window, ir_para_cadastro):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)


        title = QLabel("Entrar no CentroMercados")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Acesse sua conta com e-mail e senha")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-mail")

        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Entrar")
        self.login_button.setObjectName("success")
        self.login_button.clicked.connect(self.login)

        btn_ir_cadastro = QPushButton("Não tem uma conta? Cadastre-se")
        btn_ir_cadastro.setObjectName("nav_button")
        btn_ir_cadastro.clicked.connect(ir_para_cadastro)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(4)
        card_layout.addWidget(QLabel("E-mail:"))
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(QLabel("Senha:"))
        card_layout.addWidget(self.senha_input)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_button)
        card_layout.addWidget(btn_ir_cadastro)

        layout.addWidget(card)

    def login(self):
        email = self.email_input.text().strip()
        password = self.senha_input.text().strip()

        if not email or not password:
            show_error(self, "Preencha e-mail e senha.")
            return

        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if not response.user:
                show_error(self, "Falha na autenticação.")
                return

            profile = supabase.table("perfil").select("*").eq("email", email).execute()
            if not profile.data:
                supabase.auth.sign_out()
                show_error(self, "Perfil não encontrado.")
                return

            user_data = profile.data[0] if isinstance(profile.data, list) else profile.data
            stored_hash = user_data.get("senha_hash")

            if not stored_hash or not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                show_error(self, "E-mail ou senha incorretos.")
                return

            redis_client.set(f"sessao_usuario:{user_data.get('id_perfil')}", email, ex=3600)

            self.email_input.clear()
            self.senha_input.clear()
            self.main_window.current_user = user_data
            self.main_window.entrar_sistema()
            show_info(self, f"Bem-vindo, {user_data['nome_usuario']}!")

        except Exception as e:
            show_error(self, f"Falha no login:\n{e}")


class TelaCadastro(QWidget):
    def __init__(self, main_window, ir_para_login):
        super().__init__()
        self.main_window = main_window
        self.ir_para_login = ir_para_login

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)

        title = QLabel("Criar Nova Conta")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Preencha seus dados para se registrar")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome de usuário")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-mail")

        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.tipo_conta_combo = QComboBox()
        self.tipo_conta_combo.addItems(["Cliente Comum (Consumidor)", "Administrador (Dono de Empresa)"])
        self.tipo_conta_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                background: #ffffff;
                color: #0f172a;
            }
        """)

        self.cadastrar_button = QPushButton("Finalizar Cadastro")
        self.cadastrar_button.setObjectName("success")
        self.cadastrar_button.clicked.connect(self.cadastro)

        btn_ir_login = QPushButton("Já tem uma conta? Fazer Login")
        btn_ir_login.setObjectName("nav_button")
        btn_ir_login.clicked.connect(ir_para_login)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(QLabel("Nome de usuário:"))
        card_layout.addWidget(self.nome_input)
        card_layout.addWidget(QLabel("E-mail:"))
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(QLabel("Senha:"))
        card_layout.addWidget(self.senha_input)
        card_layout.addWidget(QLabel("Tipo de Perfil:"))
        card_layout.addWidget(self.tipo_conta_combo)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.cadastrar_button)
        card_layout.addWidget(btn_ir_login)

        layout.addWidget(card)

    def cadastro(self):
        username = self.nome_input.text().strip()
        email = self.email_input.text().strip()
        senha = self.senha_input.text()
        tipo = "admin" if self.tipo_conta_combo.currentIndex() == 1 else "cliente"

        if not email or not senha or not username:
            show_error(self, "Preencha todos os campos.")
            return

        if len(username) > 30:
            show_error(self, "O nome de usuário deve ter até 30 caracteres.")
            return

        try:
            salt = bcrypt.gensalt()
            senha_hash = bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")

            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": senha,
                "options": {"data": {"nome_usuario": username, "tipo_conta": tipo}}
            })

            if not auth_response.user:
                show_error(self, "Não foi possível criar a conta.")
                return

            supabase.table("perfil").update({
                "senha_hash": senha_hash,
                "tipo_conta": tipo
            }).eq("email", email).execute()

            show_info(self, f"Conta ({tipo.upper()}) criada com sucesso! Faça login para continuar.")
            self.nome_input.clear()
            self.email_input.clear()
            self.senha_input.clear()
            self.ir_para_login()  # Redireciona automaticamente para a tela de login após cadastrar

        except Exception as e:
            if "rate limit" in str(e).lower():
                show_error(self, "Limite de cadastros atingido. Tente novamente em alguns minutos.")
            else:
                show_error(self, f"Falha no cadastro:\n{e}")


class TelaAutenticacao(QWidget):
    def __init__(self, main_window):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sub_stack = QStackedWidget()
        self.tela_login = TelaLogin(main_window, lambda: self.sub_stack.setCurrentIndex(1))
        self.tela_cadastro = TelaCadastro(main_window, lambda: self.sub_stack.setCurrentIndex(0))

        self.sub_stack.addWidget(self.tela_login)     # Índice 0: Login
        self.sub_stack.addWidget(self.tela_cadastro)  # Índice 1: Cadastro

        layout.addWidget(self.sub_stack)

class ProductCard(QPushButton):
    def __init__(self, produto, callback_clique):
        super().__init__()
        self.produto = produto
        self.callback_clique = callback_clique
        self.setObjectName("product_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 340)

        self.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #64748b;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border: 2px solid #2563eb;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(232, 150)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setStyleSheet("background-color: transparent; border-radius: 8px; border: none;")
        self.img_lbl.setText("Carregando foto...")
        self.img_lbl.setScaledContents(False)

        imagem_path = produto.get("imagem")
        if imagem_path:
            try:
                public_url = supabase.storage.from_("produtos-bucket").get_public_url(imagem_path)
                self.downloader = ImageDownloader(public_url)
                self.downloader.finished.connect(self.atualizar_imagem)
                self.downloader.start()
            except Exception:
                self.img_lbl.setText("Sem imagem")
        else:
            self.img_lbl.setText("Sem imagem")

        self.nome_lbl = QLabel(str(produto.get("nome", "Produto")))
        self.nome_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a; background: transparent;")
        self.nome_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.nome_lbl.setWordWrap(True)
        
        descricao = str(produto.get("descricao", ""))
        if len(descricao) > 40:
            descricao = descricao[:37] + "..."

        self.desc_lbl = QLabel(descricao)
        self.desc_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent;")
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.desc_lbl.setWordWrap(True)
        
        preco = float(produto.get("preco", 0))
        self.preco_lbl = QLabel(f"R$ {preco:.2f}")
        self.preco_lbl.setStyleSheet("font-size: 17px; font-weight: 800; color: #1e293b; background: transparent;")
        self.preco_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        estoque = produto.get("estoque", 0)
        self.estoque_lbl = QLabel(f"Estoque: {estoque}")
        self.estoque_lbl.setStyleSheet("font-size: 11px; color: #64748b; background: transparent;")

        for label in (self.img_lbl, self.nome_lbl, self.desc_lbl, self.preco_lbl, self.estoque_lbl):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(self.img_lbl)
        layout.addWidget(self.nome_lbl)
        layout.addWidget(self.desc_lbl)
        layout.addStretch()
        layout.addWidget(self.preco_lbl)
        layout.addWidget(self.estoque_lbl)

        self.setLayout(layout)
        self.clicked.connect(lambda: self.callback_clique(self.produto))

    def atualizar_imagem(self, pixmap):
        self.img_lbl.setStyleSheet("background-color: #f1f5f9; border-radius: 8px; border: none;")
        if pixmap is None or pixmap.isNull():
            self.img_lbl.setPixmap(QPixmap())
            self.img_lbl.setText("Sem imagem")
            return

        largura = self.img_lbl.width()
        altura = self.img_lbl.height()
        pixmap_redimensionado = pixmap.scaled(
            QSize(largura, altura),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.img_lbl.setPixmap(pixmap_redimensionado)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setText("")


class TelaPrincipal(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        self.welcome_label = QLabel("Catálogo de Produtos:")
        self.welcome_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #000000;")

        info_lbl = QLabel("Dica: Clique em qualquer produto para ver detalhes e comprar.")
        info_lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #000000;")
        
        header_layout.addWidget(self.welcome_label)
        header_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.container_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.container_widget)

        refresh_button = QPushButton("Atualizar Catálogo")
        refresh_button.clicked.connect(lambda: self.carregar_produtos())

        layout.addLayout(header_layout)
        layout.addWidget(info_lbl)
        layout.addWidget(self.scroll_area)
        layout.addWidget(refresh_button)

    def carregar_produtos(self, termo_busca=""):
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            query = {}
            if termo_busca.strip():
                query = {"nome": {"$regex": termo_busca.strip(), "$options": "i"}}

            produtos = list(products_collection.find(query).sort("criado_em", -1))

            if not produtos:
                vazio = QLabel("Nenhum produto cadastrado ou encontrado.")
                vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vazio.setStyleSheet("font-size: 18px; color: #64748b; padding: 40px;")
                self.grid_layout.addWidget(vazio, 0, 0)
                return

            # Matriz 6 colunas por N linhas (6x3 ou mais)
            for i, produto in enumerate(produtos):
                row = i // 6
                col = i % 6

                card = ProductCard(produto, self.main_window.abrir_detalhe_produto)
                self.grid_layout.addWidget(card, row, col)

        except Exception as e:
            print(f"Erro MongoDB: {e}")
            show_error(self, f"Erro ao carregar produtos:\n{e}")


class TelaEmpresasLista(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Lista de Empresas Cadastradas")
        title.setObjectName("title")

        subtitle = QLabel("Selecione uma empresa para ver seus produtos ou cadastre uma nova.")
        subtitle.setObjectName("subtitle")

        btn_layout = QHBoxLayout()
        self.btn_cadastrar_empresa = QPushButton("➕ Cadastrar Nova Empresa")
        self.btn_cadastrar_empresa.setObjectName("success")
        self.btn_cadastrar_empresa.clicked.connect(lambda: self.main_window.mudar_pagina(6))

        btn_layout.addWidget(self.btn_cadastrar_empresa)
        btn_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: transparent;")
        self.grid_empresas = QGridLayout(self.container_widget)
        self.grid_empresas.setSpacing(16)
        self.grid_empresas.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_area.setWidget(self.container_widget)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(btn_layout)
        layout.addWidget(self.scroll_area)

    def carregar_empresas(self):
        user = self.main_window.current_user
        eh_empresario = (user and user.get("tipo_conta") == "empresario")
        self.btn_cadastrar_empresa.setVisible(bool(eh_empresario))
        try:
            while self.grid_empresas.count():
                item = self.grid_empresas.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            response = supabase.table("empresa").select("*").order("criado_em", desc=True).execute()
            empresas = response.data or []

            if not empresas:
                vazio = QLabel("Nenhuma empresa cadastrada no momento.")
                vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vazio.setStyleSheet("font-size: 16px; color: #64748b; padding: 30px;")
                self.grid_empresas.addWidget(vazio, 0, 0)
                return

            for i, empresa in enumerate(empresas):
                row = i // 3
                col = i % 3

                card = QFrame()
                card.setObjectName("card")
                card.setFixedSize(320, 180)
                card_layout = QVBoxLayout(card)
                card_layout.setSpacing(8)
                card.setStyleSheet("""
                    QWidget {
                        background-color: #ffffff;
                        border: 2px solid #64748b;
                        border-radius: 8px;
                        text-align: left;
                    }
                    QWidget:hover {
                        background-color: #f8fafc;
                        border: 2px solid #2563eb;
                    }
                    QLabel {
                        background-color: transparent;
                        border:none;
                    }
                    QLabel:hover {
                        border:none;
                    }
                    QPushButton {
                        border:none;
                    }
                """)

                nome_empresa = QLabel(str(empresa.get("nomefantasia_empresa", "Empresa")))
                nome_empresa.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")
                nome_empresa.setWordWrap(True)

                cnpj_empresa = QLabel(f"CNPJ: {empresa.get('cnpj_empresa', '-')}")
                cnpj_empresa.setStyleSheet("font-size: 12px; color: #64748b;")

                email_empresa = QLabel(f"E-mail: {empresa.get('email', '-')}")
                email_empresa.setStyleSheet("font-size: 12px; color: #64748b;")

                btn_ver_produtos = QPushButton("Ver Produtos da Empresa")
                btn_ver_produtos.setObjectName("success")
                btn_ver_produtos.setStyleSheet("font-size: 12px; color: #64748b;")
                btn_ver_produtos.clicked.connect(lambda checked=False, e=empresa: self.main_window.abrir_produtos_empresa(e))

                card_layout.addWidget(nome_empresa)
                card_layout.addWidget(cnpj_empresa)
                card_layout.addWidget(email_empresa)
                card_layout.addStretch()
                card_layout.addWidget(btn_ver_produtos)

                self.grid_empresas.addWidget(card, row, col)

        except Exception as e:
            show_error(self, f"Erro ao carregar empresas:\n{e}")


class TelaEmpresaProdutos(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.empresa_atual = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_bar = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar para Empresas")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.setFixedWidth(180)
        btn_voltar.clicked.connect(lambda: self.main_window.mudar_pagina(3))
        self.btn_cadastrar_prod = QPushButton("➕ Cadastrar Produto Nesta Empresa")
        self.btn_cadastrar_prod.setObjectName("success")
        self.btn_cadastrar_prod.clicked.connect(self.ir_para_cadastro_produto)

        top_bar.addWidget(btn_voltar)
        top_bar.addWidget(self.btn_cadastrar_prod)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        self.titulo_empresa = QLabel("Produtos da Empresa")
        self.titulo_empresa.setObjectName("title")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.container_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_area.setWidget(self.container_widget)

        layout.addWidget(self.titulo_empresa)
        layout.addWidget(self.scroll_area)

    def carregar_por_empresa(self, empresa):
        self.empresa_atual = empresa
        usuario = self.main_window.current_user

        eh_empresario = (usuario and usuario.get("tipo_conta") == "empresario")
        self.btn_cadastrar_prod.setVisible(bool(eh_empresario))

        nome = empresa.get("nomefantasia_empresa", "Empresa")
        empresa_id = empresa.get("id_empresa")
        self.titulo_empresa.setText(f"Produtos de: {nome}")

        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Busca no MongoDB produtos vinculados a este id de empresa (suporta string ou int)
            produtos = list(products_collection.find({"empresa_id": str(empresa_id)}))
            if not produtos:
                produtos = list(products_collection.find({"empresa_id": empresa_id}))

            if not produtos:
                vazio = QLabel("Esta empresa ainda não possui produtos cadastrados.")
                vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vazio.setStyleSheet("font-size: 18px; color: #64748b; padding: 40px;")
                self.grid_layout.addWidget(vazio, 0, 0)
                return

            for i, produto in enumerate(produtos):
                row = i // 6
                col = i % 6
                card = ProductCard(produto, self.main_window.abrir_detalhe_produto)
                self.grid_layout.addWidget(card, row, col)

        except Exception as e:
            show_error(self, f"Erro ao carregar produtos da empresa:\n{e}")

    def ir_para_cadastro_produto(self):
        if not self.empresa_atual:
            return
        # Abre a tela de cadastro passando a empresa atual
        self.main_window.abrir_cadastro_produto_empresa(self.empresa_atual)


class TelaCadastrarEmpresa(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(500, 520)
        form_layout = QVBoxLayout(card)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(30, 30, 30, 30)

        top_bar = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.setFixedWidth(90)
        btn_voltar.clicked.connect(lambda: self.main_window.mudar_pagina(3))
        top_bar.addWidget(btn_voltar)
        top_bar.addStretch()

        title = QLabel("Cadastrar Nova Empresa")
        title.setObjectName("title")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome fantasia")

        self.cnpj_input = QLineEdit()
        self.cnpj_input.setPlaceholderText("CNPJ (14 dígitos)")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-mail da empresa")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Telefone")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descrição da empresa")
        self.description_input.setMaximumHeight(60)

        save_button = QPushButton("Salvar Empresa")
        save_button.setObjectName("success")
        save_button.clicked.connect(self.save_company)

        form_layout.addLayout(top_bar)
        form_layout.addWidget(title)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.cnpj_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(self.description_input)
        form_layout.addWidget(save_button)

        layout.addWidget(card)

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
            response = supabase.table("empresa").insert({
                "nomefantasia_empresa": name,
                "cnpj_empresa": cnpj,
                "email": email,
                "telefone": phone,
                "descricao_empresa": description or None
            }).execute()

            if not response.data:
                raise Exception("Não foi possível cadastrar a empresa")

            company_id = response.data[0]["id_empresa"]
            supabase.table("empresa_perfil").insert({
                "empresa_id": company_id,
                "perfil_id": user["id_perfil"]
            }).execute()

            self.name_input.clear()
            self.cnpj_input.clear()
            self.email_input.clear()
            self.phone_input.clear()
            self.description_input.clear()

            show_info(self, "Empresa cadastrada com sucesso!")
            self.main_window.mudar_pagina(3)

        except Exception as e:
            show_error(self, f"Erro ao salvar empresa:\n{e}")


class TelaCadastrarProdutoEmpresa(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.caminho_imagem_local = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(500, 560)
        form_layout = QVBoxLayout(card)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(30, 30, 30, 30)

        top_bar = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.setFixedWidth(90)
        btn_voltar.clicked.connect(lambda: self.main_window.abrir_produtos_empresa(self.empresa_alvo) if self.empresa_alvo else self.main_window.mudar_pagina(3))
        top_bar.addWidget(btn_voltar)
        top_bar.addStretch()

        self.titulo = QLabel("Cadastrar Produto na Empresa")
        self.titulo.setObjectName("title")

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome do produto")

        self.preco_input = QLineEdit()
        self.preco_input.setPlaceholderText("Preço (ex: 150.00)")

        self.estoque_input = QSpinBox()
        self.estoque_input.setRange(0, 10000)
        self.estoque_input.setValue(10)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descrição do produto")
        self.desc_input.setMaximumHeight(60)

        self.img_layout = QHBoxLayout()
        self.imagem_input = QPushButton("📁 Escolher Foto...")
        self.imagem_input.clicked.connect(self.selecionar_foto)
        self.lbl_arquivo_selecionado = QLabel("Nenhuma foto selecionada")
        self.lbl_arquivo_selecionado.setStyleSheet("color: #64748b; font-size: 12px;")
        self.img_layout.addWidget(self.imagem_input)
        self.img_layout.addWidget(self.lbl_arquivo_selecionado, 1)

        save_button = QPushButton("Salvar Produto")
        save_button.setObjectName("success")
        save_button.clicked.connect(self.salvar_produto)

        form_layout.addLayout(top_bar)
        form_layout.addWidget(self.titulo)
        form_layout.addWidget(self.nome_input)
        form_layout.addWidget(self.preco_input)
        form_layout.addWidget(QLabel("Quantidade em Estoque:"))
        form_layout.addWidget(self.estoque_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addLayout(self.img_layout)
        form_layout.addWidget(save_button)
        layout.addWidget(card)

    def preparar_cadastro(self, empresa):
        self.empresa_alvo = empresa
        nome_empresa = empresa.get("nomefantasia_empresa", "")
        self.titulo.setText(f"Cadastrar em: {nome_empresa}")

    def selecionar_foto(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem do Produto", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
        if arquivo:
            self.caminho_imagem_local = arquivo
            self.lbl_arquivo_selecionado.setText(os.path.basename(arquivo))

    def salvar_produto(self):
        user = self.main_window.current_user
        if not user or user.get("tipo_conta") != "empresario":
            show_error(self, "Apenas administradores vinculados á empresas podem cadastrar produtos.")
            return

        try:
            empresa_id = self.empresa_alvo.get("id_empresa")
            nome = self.nome_input.text().strip()
            preco_str = self.preco_input.text().strip().replace(",", ".")
            estoque = self.estoque_input.value()
            desc = self.desc_input.toPlainText().strip()

            if not nome or not preco_str:
                show_error(self, "Preencha o nome e o preço do produto.")
                return

            preco = float(preco_str)
            caminho_no_bucket = ""

            if self.caminho_imagem_local:
                ext = os.path.splitext(self.caminho_imagem_local)[1].lower()
                nome_unico = f"{uuid.uuid4().hex}{ext}"
                caminho_no_bucket = f"{nome_unico}"
                content_type = "image/png" if ext == ".png" else "image/jpeg"

                with open(self.caminho_imagem_local, "rb") as f:
                    file_bytes = f.read()

                supabase.storage.from_("produtos-bucket").upload(
                    path=caminho_no_bucket,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "true"}
                )

            novo_produto = {
                "nome": nome,
                "preco": preco,
                "estoque": estoque,
                "descricao": desc,
                "imagem": caminho_no_bucket,
                "empresa_id": str(empresa_id),
                "criado_em": datetime.datetime.utcnow().isoformat()
            }

            products_collection.insert_one(novo_produto)
            show_info(self, "Produto cadastrado com sucesso!")

            self.nome_input.clear()
            self.preco_input.clear()
            self.desc_input.clear()
            self.caminho_imagem_local = None
            self.lbl_arquivo_selecionado.setText("Nenhuma foto selecionada")
            
            # Retorna para a tela de produtos daquela empresa específica
            self.main_window.abrir_produtos_empresa(self.empresa_alvo)

        except Exception as e:
            show_error(self, f"Erro ao salvar produto:\n{e}")


class TelaDetalheProduto(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.produto_atual = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(520, 480)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(30, 30, 30, 30)

        top_bar_detalhe = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.setFixedWidth(90)
        btn_voltar.clicked.connect(lambda: self.main_window.mudar_pagina(1))
        top_bar_detalhe.addWidget(btn_voltar)
        top_bar_detalhe.addStretch()

        self.img_detalhe_lbl = QLabel("Carregando imagem...")
        self.img_detalhe_lbl.setFixedSize(460, 160)
        self.img_detalhe_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nome_lbl = QLabel("Nome do Produto")
        self.nome_lbl.setObjectName("title")
        
        self.desc_lbl = QLabel("Descrição detalhada do produto...")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet("color: #000000; font-size: 14px;")

        self.preco_lbl = QLabel("R$ 0,00")
        self.preco_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b;")

        self.estoque_lbl = QLabel("Estoque disponível: 0")
        self.estoque_lbl.setStyleSheet("color: #000000; font-size: 13px;")

        self.empresa_lbl = QLabel("Empresa ID: -")
        self.empresa_lbl.setStyleSheet("color: #000000; font-size: 13px;")

        qtd_layout = QHBoxLayout()
        self.spin_qtd = QSpinBox()
        self.spin_qtd.setRange(1, 100)
        self.spin_qtd.setValue(1)
        
        btn_adicionar = QPushButton("Adicionar ao Carrinho")
        btn_adicionar.setObjectName("success")
        btn_adicionar.clicked.connect(self.adicionar_ao_carrinho)

        qtd_layout.addWidget(QLabel("Quantidade:"))
        qtd_layout.addWidget(self.spin_qtd)
        qtd_layout.addWidget(btn_adicionar)

        card_layout.addLayout(top_bar_detalhe)
        card_layout.addWidget(self.img_detalhe_lbl)
        card_layout.addWidget(self.nome_lbl)
        card_layout.addWidget(self.desc_lbl)
        card_layout.addWidget(self.preco_lbl)
        card_layout.addWidget(self.estoque_lbl)
        card_layout.addWidget(self.empresa_lbl)
        card_layout.addSpacing(10)
        card_layout.addStretch()
        card_layout.addLayout(qtd_layout)

        layout.addWidget(card)

    def carregar_produto(self, produto):
        self.produto_atual = produto
        self.nome_lbl.setText(produto.get("nome", ""))
        self.desc_lbl.setText(produto.get("descricao", "Sem descrição informada."))
        self.preco_lbl.setText(f"R$ {float(produto.get('preco', 0)):.2f}")
        self.estoque_lbl.setText(f"Estoque disponível: {produto.get('estoque', 0)}")
        self.empresa_lbl.setText(f"ID da Empresa: {produto.get('empresa_id', 'N/A')}")
        self.spin_qtd.setValue(1)

        self.img_detalhe_lbl.clear()
        self.img_detalhe_lbl.setText("Carregando imagem...")

        imagem_path = produto.get("imagem")
        if not imagem_path:
            self.img_detalhe_lbl.setText("Sem imagem")
            return

        try:
            public_url = supabase.storage.from_("produtos-bucket").get_public_url(imagem_path)
            self.downloader_detalhe = ImageDownloader(public_url)
            self.downloader_detalhe.finished.connect(self.atualizar_imagem_detalhe)
            self.downloader_detalhe.start()
        except Exception:
            self.img_detalhe_lbl.setText("Erro ao carregar imagem")

    def adicionar_ao_carrinho(self):
        if not self.produto_atual:
            return
        qtd = self.spin_qtd.value()
        self.main_window.carrinho_window.adicionar_item(self.produto_atual, qtd)
        show_info(self, f"Adicionado ao carrinho: {qtd}x {self.produto_atual.get('nome')}")

    def atualizar_imagem_detalhe(self, pixmap):
        if pixmap is None or pixmap.isNull():
            self.img_detalhe_lbl.clear()
            self.img_detalhe_lbl.setText("Sem imagem")
            return
        largura = self.img_detalhe_lbl.width()
        altura = self.img_detalhe_lbl.height()
        imagem = pixmap.scaled(QSize(largura, altura), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_detalhe_lbl.setPixmap(imagem)
        self.img_detalhe_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)


class CartItemCard(QFrame):
    def __init__(self, item, callback_remover):
        super().__init__()
        self.item = item
        self.callback_remover = callback_remover
        self.setFixedHeight(125)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #cbd5e1;
                border-radius: 14px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(15)

        produto = item["produto"]
        quantidade = item["quantidade"]
        try:
            preco = float(produto.get("preco", 0) or 0)
        except (ValueError, TypeError):
            preco = 0.0

        subtotal = preco * quantidade
        info_layout = QVBoxLayout()

        nome = QLabel(str(produto.get("nome", "Produto")))
        nome.setStyleSheet("font-size: 17px; font-weight: bold; color: #0f172a;")

        detalhes = QLabel(f"Quantidade: {quantidade} | Preço unitário: R$ {preco:.2f}")
        detalhes.setStyleSheet("font-size: 12px; color: #64748b;")

        info_layout.addWidget(nome)
        info_layout.addWidget(detalhes)

        subtotal_label = QLabel(f"R$ {subtotal:.2f}")
        subtotal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtotal_label.setMinimumWidth(120)
        subtotal_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #15803d;")

        btn_remover = QPushButton("Remover")
        btn_remover.setFixedSize(105, 42)
        btn_remover.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 9px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        btn_remover.clicked.connect(lambda: self.callback_remover(self.item))

        layout.addLayout(info_layout, 3)
        layout.addStretch()
        layout.addWidget(subtotal_label)
        layout.addWidget(btn_remover)


class CarrinhoWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.itens_carrinho = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_bar = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.setFixedWidth(100)
        btn_voltar.clicked.connect(lambda: self.main_window.mudar_pagina(1))

        top_bar.addWidget(btn_voltar)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        title = QLabel("Seu Carrinho de Compras")
        title.setObjectName("title")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: transparent;")
        self.v_layout_cards = QVBoxLayout(self.container_widget)
        self.v_layout_cards.setSpacing(12)
        self.v_layout_cards.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.container_widget)

        footer_layout = QHBoxLayout()
        self.total_label = QLabel("Total: R$ 0.00")
        self.total_label.setObjectName("title")

        btn_whatsapp = QPushButton("Finalizar Pedido via WhatsApp")
        btn_whatsapp.setStyleSheet("""
            QPushButton {
                background-color: #15803d;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #166534;
            }
        """)
        btn_whatsapp.clicked.connect(self.enviar_whatsapp)

        footer_layout.addWidget(self.total_label)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_whatsapp)

        layout.addWidget(title)
        layout.addWidget(self.scroll_area)
        layout.addLayout(footer_layout)

    def adicionar_item(self, produto, quantidade):
        encontrado = False
        for item in self.itens_carrinho:
            if str(item["produto"].get("_id")) == str(produto.get("_id")):
                item["quantidade"] += quantidade
                encontrado = True
                break
        
        if not encontrado:
            self.itens_carrinho.append({"produto": produto, "quantidade": quantidade})
        
        self.atualizar_lista()

    def remover_item(self, item):
        if item in self.itens_carrinho:
            self.itens_carrinho.remove(item)
        self.atualizar_lista()

    def atualizar_lista(self):
        while self.v_layout_cards.count():
            item = self.v_layout_cards.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total_geral = 0.0
        if not self.itens_carrinho:
            vazio = QLabel("Seu carrinho está vazio.")
            vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vazio.setStyleSheet("font-size: 18px; font-weight: bold; color: #64748b; padding: 40px;")
            self.v_layout_cards.addWidget(vazio)
        else:
            for item in self.itens_carrinho:
                prod = item["produto"]
                qtd = item["quantidade"]
                preco = float(prod.get("preco", 0))
                subtotal = preco * qtd
                total_geral += subtotal
                card = CartItemCard(item, self.remover_item)
                self.v_layout_cards.addWidget(card)

            self.total_label.setText(f"Total: R$ {total_geral:.2f}")

    def enviar_whatsapp(self):
        if not self.itens_carrinho:
            show_error(self, "Seu carrinho está vazio!")
            return

        texto_msg = "Olá, gostaria de pedir:\n"
        total_geral = 0.0

        for item in self.itens_carrinho:
            prod = item["produto"]
            qtd = item["quantidade"]
            preco = float(prod.get("preco", 0))
            subtotal = preco * qtd
            total_geral += subtotal
            texto_msg += f"- {qtd}x {prod.get('nome')} (R$ {subtotal:.2f})\n"

        texto_msg += f"\nTotal: R$ {total_geral:.2f}"
        msg_codificada = urllib.parse.quote(texto_msg)
        url_whatsapp = f"https://wa.me/{WHATSAPP_NUMERO}?text={msg_codificada}"

        QDesktopServices.openUrl(QUrl(url_whatsapp))
        show_info(self, "Redirecionando para o WhatsApp...")


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
        lbl_avatar = QLabel("[Ativo no Sistema]")
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


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CentroMercados")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1350, 780)
        self.setStyleSheet(ESTILO)

        self.current_user = None

        self.background = QWidget(self)
        self.background.setObjectName("background")
        self.background.setGeometry(self.rect())

        self.background_effect = QGraphicsBlurEffect()
        self.background_effect.setBlurRadius(24)
        self.background.setGraphicsEffect(self.background_effect)
        self.background.lower()

        if not testar_conexao() and teste_mongo():
            QMessageBox.warning(self, "Atenção", "Alguns serviços (MongoDB/Redis) podem estar indisponíveis.")

        central_widget = QWidget()
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0,0,0,0)
        root_layout.setSpacing(0)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("topbar")
        top_layout_bar = QHBoxLayout(self.top_bar)
        top_layout_bar.setContentsMargins(16, 16, 16, 16)

        self.logo_icon_label = QLabel()
        if ICON_PATH.exists():
            self.logo_icon_label.setPixmap(QIcon(str(BASE_DIR / "static" / "images" / "icon2.png")).pixmap(60, 60))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar produtos no MongoDB...")
        self.search_input.setFixedWidth(320)
        self.search_input.textChanged.connect(self.executar_pesquisa_mongodb)

        nav_buttons_layout = QHBoxLayout()
        nav_buttons_layout.setSpacing(8)

        self.btn_produtos = QPushButton("Produtos")
        self.btn_produtos.setObjectName("nav_button")
        self.btn_produtos.clicked.connect(lambda: self.mudar_pagina(1))

        self.btn_empresas = QPushButton("Empresas")
        self.btn_empresas.setObjectName("nav_button")
        self.btn_empresas.clicked.connect(lambda: self.mudar_pagina(3))

        self.btn_carrinho = QPushButton("🛒 Carrinho")
        self.btn_carrinho.setObjectName("success")
        self.btn_carrinho.clicked.connect(lambda: self.mudar_pagina(4))

        self.btn_perfil = QPushButton("Meu Perfil")
        self.btn_perfil.setObjectName("nav_button")
        self.btn_perfil.clicked.connect(lambda: self.mudar_pagina(2))

        self.btn_sair = QPushButton("Sair")
        self.btn_sair.setObjectName("danger")
        self.btn_sair.clicked.connect(self.logout)

        nav_buttons_layout.addWidget(self.btn_produtos)
        nav_buttons_layout.addWidget(self.btn_empresas)
        nav_buttons_layout.addWidget(self.btn_carrinho)
        nav_buttons_layout.addWidget(self.btn_perfil)
        nav_buttons_layout.addWidget(self.btn_sair)

        top_layout_bar.addWidget(self.logo_icon_label)
        top_layout_bar.addWidget(self.search_input)
        top_layout_bar.addStretch(1)
        top_layout_bar.addLayout(nav_buttons_layout)

        top_layout_bar.setAlignment(self.logo_icon_label, Qt.AlignmentFlag.AlignVCenter)
        top_layout_bar.setAlignment(self.search_input, Qt.AlignmentFlag.AlignVCenter)

        self.top_bar.setVisible(False)

        self.stack = QStackedWidget()

        self.auth_window = TelaAutenticacao(self)
        self.main_window = TelaPrincipal(self)
        self.profile_window = ProfileWindow(self)
        self.empresas_lista_window = TelaEmpresasLista(self)
        self.carrinho_window = CarrinhoWindow(self)
        self.detalhe_window = TelaDetalheProduto(self)
        self.empresa_produtos_window = TelaEmpresaProdutos(self)
        self.cadastrar_empresa_window = TelaCadastrarEmpresa(self)
        self.cadastrar_produto_empresa_window = TelaCadastrarProdutoEmpresa(self)

        self.stack.addWidget(self.auth_window)                   # 0: Login
        self.stack.addWidget(self.main_window)                   # 1: Catálogo Principal (6xN)
        self.stack.addWidget(self.profile_window)                # 2: Perfil
        self.stack.addWidget(self.empresas_lista_window)         # 3: Lista de Empresas
        self.stack.addWidget(self.carrinho_window)               # 4: Carrinho
        self.stack.addWidget(self.detalhe_window)                # 5: Detalhe do Produto
        self.stack.addWidget(self.cadastrar_empresa_window)      # 6: Cadastrar Empresa
        self.stack.addWidget(self.cadastrar_produto_empresa_window) # 7: Cadastrar Produto Empresa
        self.stack.addWidget(self.empresa_produtos_window)       # 8: Produtos da Empresa Específica

        root_layout.addWidget(self.top_bar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(central_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'background'):
            self.background.setGeometry(self.rect())

    def entrar_sistema(self):
        self.top_bar.setVisible(True)
        self.main_window.carregar_produtos()
        self.stack.setCurrentIndex(1)

    def mudar_pagina(self, index):
        if index == 1:
            self.main_window.carregar_produtos()
        elif index == 2:
            self.profile_window.load_profile()
        elif index == 3:
            self.empresas_lista_window.carregar_empresas()
        elif index == 4:
            self.carrinho_window.atualizar_lista()
        self.stack.setCurrentIndex(index)

    def abrir_detalhe_produto(self, produto):
        self.detalhe_window.carregar_produto(produto)
        self.stack.setCurrentIndex(5)

    def abrir_produtos_empresa(self, empresa):
        self.empresa_produtos_window.carregar_por_empresa(empresa)
        self.stack.setCurrentIndex(8)

    def abrir_cadastro_produto_empresa(self, empresa):
        self.cadastrar_produto_empresa_window.preparar_cadastro(empresa)
        self.stack.setCurrentIndex(7) # Índice da tela de cadastro de produto da empresa

    def executar_pesquisa_mongodb(self, texto):
        if self.stack.currentIndex() == 1:
            if self.current_user:
                redis_client.set(f"ultima_busca:{self.current_user.get('id_perfil')}", texto, ex=300)
            self.main_window.carregar_produtos(termo_busca=texto)

    def logout(self):
        try:
            if self.current_user:
                redis_client.delete(f"sessao_usuario:{self.current_user.get('id_perfil')}")
            supabase.auth.sign_out()
        except Exception:
            pass

        self.current_user = None
        self.top_bar.setVisible(False)
        self.auth_window.sub_stack.setCurrentIndex(0)
        self.stack.setCurrentIndex(0)


def main():
    import platform
    app = QApplication(sys.argv)
    icon = QIcon(str(ICON_PATH))

    if not icon.isNull():
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
