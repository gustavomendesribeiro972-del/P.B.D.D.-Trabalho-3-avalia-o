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
ICON_PATH = BASE_DIR / "static" / "images" / "icon.ico"

load_dotenv(BASE_DIR / "config.env")
WHATSAPP_NUMERO = os.getenv("WHATSAPP_NUMERO", "")


def show_error(parent, message: str):
    QMessageBox.critical(parent, "Erro", message)

def show_info(parent, message: str):
    QMessageBox.information(parent, "Sucesso", message)


# As Telas:

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


class ProductCard(QFrame):
    def __init__(self, produto, callback_clique):
        super().__init__()
        self.produto = produto
        self.callback_clique = callback_clique
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(260, 180)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.nome_lbl = QLabel(produto.get("nome", "Produto"))
        self.nome_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #075985;")
        
        desc_text = produto.get("descricao", "")
        if len(desc_text) > 55:
            desc_text = desc_text[:52] + "..."
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet("font-size: 12px; color: #334155;")
        
        preco = float(produto.get("preco", 0))
        self.preco_lbl = QLabel(f"R$ {preco:.2f}")
        self.preco_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #16a34a;")
        
        estoque = produto.get("estoque", 0)
        self.estoque_lbl = QLabel(f"Estoque: {estoque}")
        self.estoque_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        
        layout.addWidget(self.nome_lbl)
        layout.addWidget(self.desc_lbl)
        layout.addStretch()
        layout.addWidget(self.preco_lbl)
        layout.addWidget(self.estoque_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback_clique(self.produto)


class TelaPrincipal(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        self.welcome_label = QLabel("Catálogo de Produtos:")
        self.welcome_label.setObjectName("title")
        
        info_lbl = QLabel("Dica: Clique em qualquer produto para ver detalhes e comprar.")
        info_lbl.setObjectName("subtitle")

        header_layout.addWidget(self.welcome_label)
        header_layout.addStretch()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: #ffffff")
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

    def carregar_produtos(self, termo_busca="", forcar_refresh=False):
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            produtos = []
            cache_key = "catalogo_produtos_cache"

            if not termo_busca and not forcar_refresh:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    produtos = json.loads(cached_data)

            if not produtos:
                query = {}
                if termo_busca:
                    query = {"nome": {"$regex": termo_busca, "$options": "i"}}

                produtos = list(products_collection.find(query).sort("criado_em", -1))
                for p in produtos:
                    if "_id" in p:
                        p["_id"] = str(p["_id"])

                if not termo_busca:
                    redis_client.setex(cache_key, 60, json.dumps(produtos))

            for i, produto in enumerate(produtos):
                row = i // 3
                col = i % 3
                card = ProductCard(produto, self.main_window.abrir_detalhe_produto)
                self.grid_layout.addWidget(card, row, col)

        except Exception as e:
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

        self.nome_lbl = QLabel("Nome do Produto")
        self.nome_lbl.setObjectName("title")
        
        self.desc_lbl = QLabel("Descrição detalhada do produto...")
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet("color: #334155; font-size: 14px;")

        self.preco_lbl = QLabel("R$ 0,00")
        self.preco_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #16a34a;")

        self.estoque_lbl = QLabel("Estoque disponível: 0")
        self.estoque_lbl.setStyleSheet("color: #64748b; font-size: 13px;")

        self.empresa_lbl = QLabel("Empresa ID: -")
        self.empresa_lbl.setStyleSheet("color: #64748b; font-size: 13px;")

        # Seção de quantidade e carrinho
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

        btn_voltar = QPushButton("Voltar ao Catálogo")
        btn_voltar.setObjectName("nav_button")
        btn_voltar.clicked.connect(lambda: self.main_window.mudar_pagina(1))

        card_layout.addWidget(self.nome_lbl)
        card_layout.addWidget(self.desc_lbl)
        card_layout.addWidget(self.preco_lbl)
        card_layout.addWidget(self.estoque_lbl)
        card_layout.addWidget(self.empresa_lbl)
        card_layout.addSpacing(10)
        card_layout.addLayout(qtd_layout)
        card_layout.addStretch()
        card_layout.addWidget(btn_voltar)

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


class CarrinhoWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.itens_carrinho = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Seu Carrinho de Compras")
        title.setObjectName("title")

        self.carrinho_table = QTableWidget()
        self.carrinho_table.setColumnCount(4)
        self.carrinho_table.setHorizontalHeaderLabels([
            "Produto", "Preço Unitário", "Quantidade", "Subtotal"
        ])
        self.carrinho_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.carrinho_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        footer_layout = QHBoxLayout()
        self.total_label = QLabel("Total: R$ 0.00")
        self.total_label.setObjectName("title")

        btn_remover = QPushButton("Remover Item")
        btn_remover.setObjectName("danger")
        btn_remover.clicked.connect(self.remover_item)

        btn_whatsapp = QPushButton("Finalizar Pedido via WhatsApp")
        btn_whatsapp.setObjectName("success")
        btn_whatsapp.clicked.connect(self.enviar_whatsapp)

        footer_layout.addWidget(self.total_label)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_remover)
        footer_layout.addWidget(btn_whatsapp)

        layout.addWidget(title)
        layout.addWidget(self.carrinho_table)
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
        
        self.atualizar_tabela()

    def remover_item(self):
        selected_row = self.carrinho_table.currentRow()
        if selected_row < 0:
            show_error(self, "Selecione um item no carrinho para remover.")
            return

        del self.itens_carrinho[selected_row]
        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.carrinho_table.setRowCount(0)
        total_geral = 0.0

        for item in self.itens_carrinho:
            prod = item["produto"]
            qtd = item["quantidade"]
            preco = float(prod.get("preco", 0))
            subtotal = preco * qtd
            total_geral += subtotal

            row = self.carrinho_table.rowCount()
            self.carrinho_table.insertRow(row)
            self.carrinho_table.setItem(row, 0, QTableWidgetItem(str(prod.get("nome", ""))))
            self.carrinho_table.setItem(row, 1, QTableWidgetItem(f"R$ {preco:.2f}"))
            self.carrinho_table.setItem(row, 2, QTableWidgetItem(str(qtd)))
            self.carrinho_table.setItem(row, 3, QTableWidgetItem(f"R$ {subtotal:.2f}"))

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


#App:
class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CentroMercados")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1200, 750)

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
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("topbar")
        top_layout_bar = QHBoxLayout(self.top_bar)
        top_layout_bar.setContentsMargins(12, 6, 12, 6)


        self.logo_icon_label = QLabel()
        if ICON_PATH.exists():
            self.logo_icon_label.setPixmap(QIcon(str(ICON_PATH)).pixmap(30, 30))

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
        top_layout_bar.addStretch(1)
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
        root_layout.addWidget(self.stack)
        self.setCentralWidget(central_widget)

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
        
        self.stack.setCurrentIndex(index)

    def abrir_detalhe_produto(self, produto):
        self.detalhe_window.carregar_produto(produto)
        self.stack.setCurrentIndex(5)

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