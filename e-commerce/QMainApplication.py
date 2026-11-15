import json, sys, os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QFrame, QFormLayout,
    QTextEdit, QGroupBox, QGridLayout, QGraphicsBlurEffect, QSpinBox,
    QScrollArea
)

import bcrypt

from databases.supabase_client import supabase, testar_conexao
from databases.mongo import products_collection, teste_mongo
from databases.redis_client import redis_client

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "static" / "images" / "icon1.png"

load_dotenv(BASE_DIR / "config.env")
WHATSAPP_NUMERO = os.getenv("WHATSAPP_NUMERO", "")

# Estilo usado no aplicativo:
ESTILO = """
QMainWindow {
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
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 16px;
    text-align: left;
}

QPushButton#product_card:hover {
    background-color: #e2e8f0;
    border: 2px solid #c0d0e0;
}

QLabel#nome_produto {
    font-size: 16px;
    font-weight: 800;
    color: #0f172a;
}

QLabel#descricao_produto {
    font-size: 12px;
    color: #64748b;
}

QLabel#preco_produto {
    font-size: 19px;
    font-weight: 800;
    color: #1e293b;
}

QLabel#estoque_produto {
    font-size: 11px;
    color: #64748b;
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


class TelaAutenticacao(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        auth = QFrame()
        auth.setObjectName("auth")
        auth.setFixedWidth(420)

        auth_layout = QVBoxLayout(auth)
        auth_layout.setSpacing(14)

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
        # Botões com a mesma cor/estilo padrão

        self.login_button.clicked.connect(self.login)
        self.cadastrar_button.clicked.connect(self.cadastro)

        auth_layout.addWidget(title)
        auth_layout.addWidget(subtitle)
        auth_layout.addWidget(QLabel("Nome de usuário"))
        auth_layout.addWidget(self.nome_input)
        auth_layout.addWidget(QLabel("E-mail"))
        auth_layout.addWidget(self.email_input)
        auth_layout.addWidget(QLabel("Senha"))
        auth_layout.addWidget(self.senha_input)
        auth_layout.addWidget(self.login_button)
        auth_layout.addWidget(self.cadastrar_button)

        layout.addWidget(auth)

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

            user_data = profile.data[0] if isinstance(profile.data, list) else profile.data
            stored_hash = user_data.get("senha_hash")

            if not stored_hash or not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                show_error(self, "E-mail ou senha incorretos.")
                return

            redis_client.set(f"sessao_usuario:{user_data.get('id_perfil')}", email, ex=3600)

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
            salt = bcrypt.gensalt()
            senha_hash = bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")

            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": senha,
                "options":{ "data": {"nome_usuario": username}}
            })

            if not auth_response.user:
                show_error(self, "Não foi possível criar a conta.")
                return

            supabase.table("perfil").update({
                "senha_hash": senha_hash
            }).eq("email", email).execute()

            show_info(self, "Conta criada com sucesso! Seu perfil foi registrado automaticamente.")
            self.nome_input.clear()
            self.email_input.clear()
            self.senha_input.clear()

        except Exception as e:
            if "rate limit" in str(e).lower():
                show_error(self, "Limite de cadastros atingido. Tente novamente em alguns minutos.")
            else:
                show_error(self, f"Falha no cadastro:\n{e}")


class ProductCard(QPushButton):
    def __init__(self, produto, callback_clique):
        super().__init__()
        self.produto = produto
        self.callback_clique = callback_clique
        self.setObjectName("product_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        
        self.nome_lbl = QLabel(str(produto.get("nome", "Produto")))
        self.nome_lbl.setStyleSheet("nome_produto")
        self.nome_lbl.setWordWrap(True)
        
        descricao = str(produto.get("descricao", ""))
        if len(descricao) > 55:
            descricao = descricao[:52] + "..."

        self.desc_lbl = QLabel(descricao)
        self.desc_lbl.setStyleSheet("desc_produto")
        self.desc_lbl.setWordWrap(True)
        
        preco = float(produto.get("preco", 0))
        self.preco_lbl = QLabel(f"R$ {preco:.2f}")
        self.preco_lbl.setStyleSheet("preco_produto")
        
        estoque = produto.get("estoque", 0)
        self.estoque_lbl = QLabel(f"Estoque: {estoque}")
        self.estoque_lbl.setStyleSheet("estoque_produto")

        for label in (
            self.nome_lbl,
            self.desc_lbl,
            self.preco_lbl,
            self.estoque_lbl
        ):
            label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
        
        layout.addWidget(self.nome_lbl)
        layout.addWidget(self.desc_lbl)
        layout.addStretch()
        layout.addWidget(self.preco_lbl)
        layout.addWidget(self.estoque_lbl)

        self.setLayout(layout)
        self.setMinimumSize(222, 160)

        self.clicked.connect(
            lambda: self.callback_clique(self.produto)
        )


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
        self.container_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
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
            # Limpa os produtos exibidos anteriormente
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()

                if widget:
                    widget.deleteLater()

            # Busca diretamente no MongoDB
            query = {}

            if termo_busca.strip():
                query = {
                    "nome": {
                        "$regex": termo_busca.strip(),
                        "$options": "i"
                    }
                }

            produtos = list(
                products_collection.find(query).sort("criado_em", -1)
            )

            print(f"Produtos encontrados: {len(produtos)}")

            if not produtos:
                vazio = QLabel("Nenhum produto cadastrado ou encontrado.")
                vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vazio.setStyleSheet("""
                    font-size: 18px;
                    color: #64748b;
                    padding: 40px;
                """)

                self.grid_layout.addWidget(vazio, 0, 0)
                return

            # Exibe os produtos
            for i, produto in enumerate(produtos):
                row = i // 3
                col = i % 3

                card = QPushButton(
                    f"{produto.get('imagem', 'img')}\n"
                    f"{produto.get('nome', 'Produto')}\n{produto.get('descricao', 'Descrição...')}\n\n"
                    f"R$ {float(produto.get('preco', 0)):.2f}\n"
                    f"Estoque: {produto.get('estoque', 0)}\n"
                    f"Categoria: {produto.get('categoria', 'categoria...')}"
                )

                card.setFixedSize(260, 180)

                card.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #0f172a;
                        border: 2px solid #cbd5e1;
                        border-radius: 15px;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 12px;
                    }

                    QPushButton:hover {
                        background-color: #cbd5e1;
                    }
                """)

                card.clicked.connect(
                    lambda checked=False, p=produto:
                    self.main_window.abrir_detalhe_produto(p)
                )

                self.grid_layout.addWidget(card, row, col)

        except Exception as e:
            print(f"Erro MongoDB: {e}")
            show_error(self, f"Erro ao carregar produtos:\n{e}")


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

        # Botão de voltar no topo esquerdo (seta)
        top_bar_detalhe = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.setFixedWidth(90)
        btn_voltar.clicked.connect(lambda: self.main_window.mudar_pagina(1))
        top_bar_detalhe.addWidget(btn_voltar)
        top_bar_detalhe.addStretch()

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

        # Seção de quantidade e botão Adicionar ao Carrinho na parte inferior
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

    def adicionar_ao_carrinho(self):
        if not self.produto_atual:
            return
        qtd = self.spin_qtd.value()
        self.main_window.carrinho_window.adicionar_item(self.produto_atual, qtd)
        show_info(self, f"Adicionado ao carrinho: {qtd}x {self.produto_atual.get('nome')}")


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

        # Informações do produto
        info_layout = QVBoxLayout()

        nome = QLabel(str(produto.get("nome", "Produto")))
        nome.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
            color: #0f172a;
        """)

        detalhes = QLabel(
            f"Quantidade: {quantidade} | "
            f"Preço unitário: R$ {preco:.2f}"
        )

        detalhes.setStyleSheet("""
            font-size: 12px;
            color: #64748b;
        """)

        info_layout.addWidget(nome)
        info_layout.addWidget(detalhes)

        # Subtotal
        subtotal_label = QLabel(
            f"R$ {subtotal:.2f}"
        )

        subtotal_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtotal_label.setMinimumWidth(120)

        subtotal_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #15803d;
        """)

        # Botão remover
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

        btn_remover.clicked.connect(
            lambda: self.callback_remover(self.item)
        )

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
            self.itens_carrinho.append({
                "produto": produto,
                "quantidade": quantidade
            })
        
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
            vazio.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #64748b;
                padding: 40px;
            """)
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
            auth_user = supabase.auth.get_user().user

            if not auth_user:
                show_error(self, "Sessão expirada. Faça login novamente...")
                return
            
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

            if not response.data:
                raise Exception("Não foi possivel cadastrar a empresa")

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

            self.load_companies()
            show_info(self, "Empresa cadastrada e vinculada ao seu perfil.")

        except Exception as e:
            show_error(self, f"Erro ao salvar empresa:\n{e}")


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CentroMercados")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1200, 750)
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
            QMessageBox.warning(
                self, "Atenção",
                "Alguns serviços (MongoDB/Redis) podem estar indisponíveis."
            )

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
        self.companies_window = CompaniesWindow(self)
        self.carrinho_window = CarrinhoWindow(self)
        self.detalhe_window = TelaDetalheProduto(self)

        self.stack.addWidget(self.auth_window)      # Índice 0: Login
        self.stack.addWidget(self.main_window)      # Índice 1: Principal (Catálogo Grid 3x3)
        self.stack.addWidget(self.profile_window)   # Índice 2: Perfil
        self.stack.addWidget(self.companies_window) # Índice 3: Empresas
        self.stack.addWidget(self.carrinho_window)  # Índice 4: Carrinho / WhatsApp
        self.stack.addWidget(self.detalhe_window)   # Índice 5: Página de Produto Individual

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
            self.companies_window.load_companies()
        elif index == 4:
            self.carrinho_window.atualizar_lista()
        self.stack.setCurrentIndex(index)

    def abrir_detalhe_produto(self, produto):
        self.detalhe_window.carregar_produto(produto)
        self.stack.setCurrentIndex(5)

        print("Produto selecionado:")
        print(produto)

        print("Nome:", produto.get("nome"))
        print("Preço:", produto.get("preco"))
        print("Descrição:", produto.get("descricao"))

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