import sqlite3, os
import customtkinter as ctk
from tkinter import messagebox as mb

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

VERDE, FUNDO, CARD = "#16A085", "#14171d", "#242a35"
telas, botoes = {}, {}

conexao = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sistema.db"))
cursor = conexao.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS produtos (nome TEXT, preco REAL, quantidade INTEGER)")


def executar(sql, params=()):
    cursor.execute(sql, params)
    conexao.commit()


def botao(pai, texto, comando, **kw):
    estilo = {"fg_color": VERDE, "hover_color": "#12806a", **kw}
    return ctk.CTkButton(pai, text=texto, command=comando, height=42, corner_radius=10,
                         font=("Segoe UI", 15, "bold"), **estilo)


def campo(pai, rotulo, dica):
    ctk.CTkLabel(pai, text=rotulo, font=("Segoe UI", 13, "bold"), anchor="w").pack(fill="x", padx=60, pady=(12, 2))
    entrada = ctk.CTkEntry(pai, height=40, corner_radius=10, placeholder_text=dica)
    entrada.pack(fill="x", padx=60)
    return entrada


def nova_tela(chave, titulo, subtitulo):
    tela = telas[chave] = ctk.CTkFrame(janela, corner_radius=18, fg_color=CARD)
    ctk.CTkLabel(tela, text=titulo, font=("Segoe UI", 26, "bold")).pack(pady=(30, 0))
    ctk.CTkLabel(tela, text=subtitulo, font=("Segoe UI", 14), text_color="gray70").pack(pady=(2, 15))
    return tela


def mostrar(nome):
    for chave, tela in telas.items():
        tela.pack_forget()
        botoes[chave].configure(fg_color=VERDE if chave == nome else "transparent")
    telas[nome].pack(side="right", fill="both", expand=True, padx=(0, 15), pady=15)
    if nome == "consulta":
        atualizar_lista_produtos()
    if nome == "venda":
        atualizar_combo_venda()


def cadastrar_produto():
    nome, preco, qtd = entry_nome.get(), entry_preco.get(), entry_quantidade.get()
    if not (nome and preco and qtd):
        return mb.showwarning("Aviso", "Preencha todos os campos!")
    try:
        executar("INSERT INTO produtos VALUES (?, ?, ?)", (nome, float(preco.replace(",", ".")), int(qtd)))
    except ValueError:
        return mb.showerror("Erro", "Preço e quantidade devem ser números!")
    mb.showinfo("Sucesso", f"Produto '{nome}' cadastrado!")
    for e in (entry_nome, entry_preco, entry_quantidade):
        e.delete(0, "end")
    atualizar_lista_produtos()


def atualizar_lista_produtos():
    itens = cursor.execute("SELECT * FROM produtos").fetchall()
    caixa.configure(state="normal")
    caixa.delete("1.0", "end")
    caixa._textbox.tag_configure("baixo", foreground="#ff6b6b")
    label_total.configure(text=f"{len(itens)} produto(s) cadastrado(s)")
    for nome, preco, qtd in itens:
        aviso = "   ⚠ estoque baixo" if qtd <= 5 else ""
        caixa.insert("end", f"🍔  {nome}\n     Preço: R$ {preco:.2f}\n     Quantidade: {qtd}{aviso}\n{'─' * 40}\n",
                     "baixo" if qtd <= 5 else None)
    if not itens:
        caixa.insert("end", "Nenhum produto cadastrado.")
    caixa.configure(state="disabled")


def atualizar_combo_venda():
    nomes = obter_nomes_produtos() or ["Sem produtos"]
    combo_venda.configure(values=nomes)
    combo_venda.set(nomes[0])


def vender_produto():
    nome = combo_venda.get()
    try:
        qtd = int(entry_qtd_venda.get())
        if qtd <= 0:
            raise ValueError
    except ValueError:
        return mb.showerror("Erro", "Digite uma quantidade inteira maior que 0!")
    resultado = cursor.execute("SELECT quantidade FROM produtos WHERE nome = ?", (nome,)).fetchone()
    if resultado is None:
        return mb.showwarning("Aviso", "Produto não encontrado!")
    if resultado[0] < qtd:
        return mb.showwarning("Aviso", f"Estoque insuficiente! Disponível: {resultado[0]}")
    executar("UPDATE produtos SET quantidade = quantidade - ? WHERE nome = ?", (qtd, nome))
    atualizar_lista_produtos()
    mb.showinfo("Venda", f"Venda realizada!\n\nProduto: {nome}\nQuantidade vendida: {qtd}\n"
                         f"Estoque anterior: {resultado[0]}\nEstoque atual: {resultado[0] - qtd}")
    entry_qtd_venda.delete(0, "end")
    entry_qtd_venda.insert(0, "1")


def obter_nomes_produtos():
    return [linha[0] for linha in cursor.execute("SELECT DISTINCT nome FROM produtos")]


def editar_estoque_dialog():                                                   # Bloco A
    produtos_cadastrados = obter_nomes_produtos()                              # Bloco B
    if not produtos_cadastrados:                                               # Bloco C
        return mb.showinfo("Vazio", "Não há produtos cadastrados para editar.")
    dialog = ctk.CTkToplevel(janela)                                           # Bloco D
    dialog.title("Atualizar Saldo")
    dialog.geometry("350x250")
    dialog.attributes("-topmost", True)                                        # Bloco E
    dialog.grab_set()
    combo_produtos = ctk.CTkOptionMenu(dialog, values=produtos_cadastrados, width=200)   # Bloco F
    combo_produtos.pack(pady=5)
    entry_nova_qtd = ctk.CTkEntry(dialog, width=200, placeholder_text="Nova quantidade")
    entry_nova_qtd.pack(pady=5)

    def salvar():
        try:
            executar("UPDATE produtos SET quantidade = ? WHERE nome = ?",
                     (int(entry_nova_qtd.get()), combo_produtos.get()))
        except ValueError:
            return mb.showerror("Erro", "Digite um número inteiro!", parent=dialog)
        atualizar_lista_produtos()
        dialog.destroy()

    botao(dialog, "Salvar", salvar, width=200).pack(pady=10)


def abrir_sistema_principal():
    global janela, entry_nome, entry_preco, entry_quantidade, combo_venda, entry_qtd_venda, caixa, label_total
    janela_login.destroy()
    janela = ctk.CTk()
    janela.geometry("950x620")
    janela.configure(fg_color=FUNDO)
    janela.title("Lanchonete Ennius Muniz - Senac DF")

    menu = ctk.CTkFrame(janela, width=240, corner_radius=0, fg_color="#1b1f27")
    menu.pack(side="left", fill="y")
    menu.pack_propagate(False)
    ctk.CTkLabel(menu, text="🍔\nLanchonete\nEnnius Muniz", font=("Segoe UI", 20, "bold")).pack(pady=(35, 30))
    transparente = {"anchor": "w", "fg_color": "transparent", "hover_color": "#2c3340"}
    for chave, texto in [("cadastro", "➕  Cadastrar Produto"), ("consulta", "📋  Consultar Produtos"),
                         ("venda", "🛒  Realizar Venda")]:
        botoes[chave] = botao(menu, "  " + texto, lambda c=chave: mostrar(c), **transparente)
        botoes[chave].pack(fill="x", pady=5, padx=15)
    botao(menu, "  ✏️  Editar Estoque", editar_estoque_dialog, **transparente).pack(fill="x", pady=5, padx=15)
    botao(menu, "Sair", janela.destroy, fg_color="#c0392b", hover_color="#962d22").pack(side="bottom", fill="x", padx=15, pady=25)

    tela = nova_tela("cadastro", "Cadastro de Produtos", "Adicione novos itens ao estoque")
    entry_nome = campo(tela, "Nome do produto", "Ex.: Coxinha")
    entry_preco = campo(tela, "Preço (R$)", "Ex.: 7.50")
    entry_quantidade = campo(tela, "Quantidade", "Ex.: 20")
    botao(tela, "Salvar produto", cadastrar_produto).pack(fill="x", padx=60, pady=30)

    tela = nova_tela("consulta", "Produtos Cadastrados", "Itens com 5 unidades ou menos aparecem em vermelho")
    caixa = ctk.CTkTextbox(tela, corner_radius=12, font=("Consolas", 14))
    caixa.pack(fill="both", expand=True, padx=30, pady=(0, 10))
    label_total = ctk.CTkLabel(tela, text="", text_color="gray70")
    label_total.pack()
    botao(tela, "🔄  Atualizar lista", atualizar_lista_produtos).pack(pady=15)

    tela = nova_tela("venda", "Realizar Venda", "Escolha o produto e a quantidade")
    ctk.CTkLabel(tela, text="Produto", font=("Segoe UI", 13, "bold"), anchor="w").pack(fill="x", padx=60, pady=(12, 2))
    combo_venda = ctk.CTkOptionMenu(tela, height=40, values=["Sem produtos"])
    combo_venda.pack(fill="x", padx=60)
    entry_qtd_venda = campo(tela, "Quantidade", "Ex.: 2")
    entry_qtd_venda.insert(0, "1")
    botao(tela, "Vender produto", vender_produto).pack(fill="x", padx=60, pady=30)

    mostrar("cadastro")
    janela.mainloop()


def validar_login():
    if entry_user.get() == "admin" and entry_senha.get() == "1234":
        abrir_sistema_principal()
    else:
        mb.showwarning("Aviso", "Usuário ou senha incorretos!")


janela_login = ctk.CTk()
janela_login.geometry("380x470")
janela_login.resizable(False, False)
janela_login.configure(fg_color=FUNDO)
janela_login.title("Login")

card = ctk.CTkFrame(janela_login, corner_radius=20, fg_color=CARD)
card.pack(fill="both", expand=True, padx=25, pady=25)
ctk.CTkLabel(card, text="🍔\nLanchonete\nEnnius Muniz", font=("Segoe UI", 24, "bold")).pack(pady=(25, 20))
entry_user = ctk.CTkEntry(card, height=40, placeholder_text="Usuário")
entry_user.pack(fill="x", padx=35, pady=8)
entry_senha = ctk.CTkEntry(card, height=40, placeholder_text="Senha", show="*")
entry_senha.pack(fill="x", padx=35, pady=8)
entry_senha.bind("<Return>", lambda evento: validar_login())
botao(card, "Autenticar", validar_login).pack(fill="x", padx=35, pady=25)

janela_login.mainloop()