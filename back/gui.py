import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.conexao import criar_conexao
from src.dao.produtoDAO import ProdutoDAO
from src.dao.clienteDAO import ClienteDAO
from src.dao.vendaDAO import VendaDAO
from src.dao.fornecedorDAO import FornecedorDAO
from src.models.produto import Produto
from src.models.cliente import Cliente
from src.models.item_venda import ItemVenda
from src.models.venda import Venda
from src.models.fornecedor import Fornecedor


class InMemoryProdutoDAO:
  def __init__(self):
    self._produtos = {}
    self._next_id = 1
    # Dados de exemplo para demonstracao
    self.salvar(Produto(None, "Cafe 250g", Decimal("15.00"), 30, 101, "Torrado e moido"))
    self.salvar(Produto(None, "Leite Integral 1L", Decimal("6.50"), 50, 102, "Caixa 1L"))

  def salvar(self, produto):
    if produto.id is None:
      produto.id = self._next_id
      self._next_id += 1
    self._produtos[produto.id] = produto
    return True

  def listar(self):
    return sorted(self._produtos.values(), key=lambda p: p.id)

  def deletar(self, id):
    return self._produtos.pop(id, None) is not None
  def buscar_id(self, id):
    return self._produtos.get(id)

  def baixar_estoque(self, id, quantidade):
    produto = self._produtos.get(id)
    if not produto or quantidade > produto.estoque:
      return False
    produto.estoque -= quantidade
    return True


class InMemoryClienteDAO:
  def __init__(self):
    self._clientes = {}
    self._next_id = 1
    self.salvar(Cliente(None, "Cliente Demo", "00011122233", "demo@mercatus.com", "Rua Exemplo, 123"))

  def salvar(self, cliente: Cliente):
    if cliente.id is None:
      cliente.id = self._next_id
      self._next_id += 1
    self._clientes[cliente.id] = cliente
    return True

  def listar(self):
    return sorted(self._clientes.values(), key=lambda c: c.id)

  def deletar(self, id):
    return self._clientes.pop(id, None) is not None


class InMemoryFornecedorDAO:
  def __init__(self):
    self._fornecedores = {}
    self._next_id = 1
    self.salvar(Fornecedor(None, "Fornecedor Demo", "11999990000"))

  def salvar(self, fornecedor: Fornecedor):
    if fornecedor.id is None:
      fornecedor.id = self._next_id
      self._next_id += 1
    self._fornecedores[fornecedor.id] = fornecedor
    return True

  def listar(self):
    return sorted(self._fornecedores.values(), key=lambda f: f.id)

  def deletar(self, id):
    return self._fornecedores.pop(id, None) is not None


class InMemoryVendaDAO:
  def __init__(self, produto_dao: InMemoryProdutoDAO):
    self._produtos = produto_dao
    self._vendas = []
    self._next_id = 1

  def realizar_venda(self, venda: Venda):
    try:
      venda.id = self._next_id
      self._next_id += 1
      for item in venda.itens:
        if not self._produtos.baixar_estoque(item.id_produto, item.quantidade):
          raise ValueError("Estoque insuficiente")
      self._vendas.append(venda)
      print(f"Venda (offline) #{venda.id} registrada.")
      return True
    except Exception as e:
      print(f"Erro offline: {e}")
      return False

  def listar(self):
    return list(self._vendas)

  def deletar(self, id):
    for idx, venda in enumerate(self._vendas):
      if venda.id == id:
        del self._vendas[idx]
        return True
    return False


class MercatusApp(tk.Tk):
  def __init__(self):
    super().__init__()
    self.title("Mercatus - PDV")
    self.geometry("1000x640")
    self.configure(bg="#0f172a")

    self.conexao = criar_conexao()
    self.modo_offline = not bool(self.conexao)

    if self.conexao:
      self.produto_dao = ProdutoDAO(self.conexao)
      self.cliente_dao = ClienteDAO(self.conexao)
      self.venda_dao = VendaDAO(self.conexao)
      self.fornecedor_dao = FornecedorDAO(self.conexao)
    else:
      # fallback em memoria para apresentacao sem banco
      self.produto_dao = InMemoryProdutoDAO()
      self.cliente_dao = InMemoryClienteDAO()
      self.venda_dao = InMemoryVendaDAO(self.produto_dao)
      self.fornecedor_dao = InMemoryFornecedorDAO()

    self.carrinho = []
    self.valor_total = Decimal("0.00")
    self.fornecedores_cache = []
    self.clientes_cache = []
    self.produtos_cache = []

    self._build_ui()

  def _build_ui(self):
    wrapper = ttk.Frame(self, padding=20)
    wrapper.pack(fill="both", expand=True)

    header = ttk.Frame(wrapper)
    header.pack(fill="x", pady=(0, 10))

    title = ttk.Label(
      header,
      text="Mercatus",
      font=("Segoe UI", 20, "bold")
    )
    title.pack(side="left")

    status_text = "Conectado" if not self.modo_offline else "Demo offline"
    status_color = "#0ea5e9" if not self.modo_offline else "#f97316"
    status = tk.Label(
      header,
      text=status_text,
      bg=status_color,
      fg="white",
      padx=12,
      pady=6
    )
    status.pack(side="right")

    notebook = ttk.Notebook(wrapper)
    notebook.pack(fill="both", expand=True)

    self.produtos_tab = ttk.Frame(notebook, padding=16)
    self.clientes_tab = ttk.Frame(notebook, padding=16)
    self.fornecedores_tab = ttk.Frame(notebook, padding=16)
    self.vendas_tab = ttk.Frame(notebook, padding=16)

    notebook.add(self.produtos_tab, text="Produtos")
    notebook.add(self.clientes_tab, text="Clientes")
    notebook.add(self.fornecedores_tab, text="Fornecedores")
    notebook.add(self.vendas_tab, text="Vendas")

    self._build_produtos_tab()
    self._build_clientes_tab()
    self._build_fornecedores_tab()
    self._build_vendas_tab()

  def _build_produtos_tab(self):
    form = ttk.LabelFrame(self.produtos_tab, text="Cadastrar Produto", padding=12)
    form.pack(fill="x")

    self.nome_produto = tk.StringVar()
    self.descricao_produto = tk.StringVar()
    self.preco_produto = tk.StringVar()
    self.estoque_produto = tk.StringVar()
    self.fornecedor_produto = tk.StringVar()

    fields = [
      ("Nome", self.nome_produto),
      ("Descricao", self.descricao_produto),
      ("Preco", self.preco_produto),
      ("Estoque", self.estoque_produto),
    ]

    for idx, (label, var) in enumerate(fields):
      ttk.Label(form, text=label).grid(row=idx, column=0, sticky="w", pady=4, padx=6)
      ttk.Entry(form, textvariable=var, width=40).grid(row=idx, column=1, sticky="w", pady=4, padx=6)

    fornecedor_row = len(fields)
    ttk.Label(form, text="Fornecedor").grid(row=fornecedor_row, column=0, sticky="w", pady=4, padx=6)
    self.fornecedor_produto_combo = ttk.Combobox(form, textvariable=self.fornecedor_produto, state="readonly", width=37)
    self.fornecedor_produto_combo.grid(row=fornecedor_row, column=1, sticky="w", pady=4, padx=6)

    ttk.Label(form, text="ID do produto gerado automaticamente.").grid(row=fornecedor_row+1, column=0, columnspan=2, sticky="w", padx=6, pady=(4, 0))

    ttk.Button(form, text="Salvar Produto", command=self.salvar_produto).grid(row=fornecedor_row+2, column=1, pady=10, sticky="w")

    busca = ttk.LabelFrame(self.produtos_tab, text="Buscar Produto", padding=12)
    busca.pack(fill="x", pady=(16, 0))

    self.busca_produto_id = tk.StringVar()
    ttk.Label(busca, text="ID").grid(row=0, column=0, padx=6, pady=4, sticky="w")
    ttk.Entry(busca, textvariable=self.busca_produto_id, width=12).grid(row=0, column=1, padx=6, pady=4, sticky="w")
    ttk.Button(busca, text="Buscar", command=self.buscar_produto).grid(row=0, column=2, padx=6, pady=4)

    self.resultado_produto = tk.StringVar()
    ttk.Label(busca, textvariable=self.resultado_produto, font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=6)

    listagem = ttk.LabelFrame(self.produtos_tab, text="Produtos cadastrados", padding=12)
    listagem.pack(fill="both", expand=True, pady=(16, 0))

    colunas = ("id", "nome", "preco", "estoque", "fornecedor")
    self.produtos_tree = ttk.Treeview(listagem, columns=colunas, show="headings", height=10)
    self.produtos_tree.heading("id", text="ID")
    self.produtos_tree.heading("nome", text="Nome")
    self.produtos_tree.heading("preco", text="Preco")
    self.produtos_tree.heading("estoque", text="Estoque")
    self.produtos_tree.heading("fornecedor", text="Fornecedor")
    self.produtos_tree.column("id", width=60, anchor="center")
    self.produtos_tree.column("nome", width=220)
    self.produtos_tree.column("preco", width=100, anchor="e")
    self.produtos_tree.column("estoque", width=80, anchor="center")
    self.produtos_tree.column("fornecedor", width=100, anchor="center")
    scrollbar = ttk.Scrollbar(listagem, orient="vertical", command=self.produtos_tree.yview)
    self.produtos_tree.configure(yscrollcommand=scrollbar.set)
    self.produtos_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    actions = ttk.Frame(self.produtos_tab)
    actions.pack(fill="x", pady=8)
    ttk.Button(actions, text="Excluir selecionado", command=self.excluir_produto).pack(side="left")

    self._carregar_fornecedores()
    self._carregar_produtos()

  def _build_clientes_tab(self):
    form = ttk.LabelFrame(self.clientes_tab, text="Cadastrar Cliente", padding=12)
    form.pack(fill="x")

    self.nome_cliente = tk.StringVar()
    self.cpf_cliente = tk.StringVar()
    self.email_cliente = tk.StringVar()
    self.endereco_cliente = tk.StringVar()

    fields = [
      ("Nome", self.nome_cliente),
      ("CPF", self.cpf_cliente),
      ("Email", self.email_cliente),
      ("Endereco", self.endereco_cliente),
    ]

    for idx, (label, var) in enumerate(fields):
      ttk.Label(form, text=label).grid(row=idx, column=0, sticky="w", pady=4, padx=6)
      ttk.Entry(form, textvariable=var, width=40).grid(row=idx, column=1, sticky="w", pady=4, padx=6)

    ttk.Button(form, text="Salvar Cliente", command=self.salvar_cliente).grid(row=len(fields), column=1, pady=10, sticky="w")

    listagem = ttk.LabelFrame(self.clientes_tab, text="Clientes cadastrados", padding=12)
    listagem.pack(fill="both", expand=True, pady=(12, 0))

    colunas = ("id", "nome", "cpf", "email", "endereco")
    self.clientes_tree = ttk.Treeview(listagem, columns=colunas, show="headings", height=10)
    for col, texto, largura, anchor in [
      ("id", "ID", 60, "center"),
      ("nome", "Nome", 180, "w"),
      ("cpf", "CPF", 110, "center"),
      ("email", "Email", 200, "w"),
      ("endereco", "Endereco", 220, "w"),
    ]:
      self.clientes_tree.heading(col, text=texto)
      self.clientes_tree.column(col, width=largura, anchor=anchor)
    scrollbar = ttk.Scrollbar(listagem, orient="vertical", command=self.clientes_tree.yview)
    self.clientes_tree.configure(yscrollcommand=scrollbar.set)
    self.clientes_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    actions = ttk.Frame(self.clientes_tab)
    actions.pack(fill="x", pady=8)
    ttk.Button(actions, text="Excluir selecionado", command=self.excluir_cliente).pack(side="left")

    self._carregar_clientes()

  def _build_fornecedores_tab(self):
    form = ttk.LabelFrame(self.fornecedores_tab, text="Cadastrar Fornecedor", padding=12)
    form.pack(fill="x")

    self.nome_fornecedor = tk.StringVar()
    self.telefone_fornecedor = tk.StringVar()

    ttk.Label(form, text="Nome da Empresa").grid(row=0, column=0, sticky="w", pady=4, padx=6)
    ttk.Entry(form, textvariable=self.nome_fornecedor, width=40).grid(row=0, column=1, sticky="w", pady=4, padx=6)
    ttk.Label(form, text="Telefone").grid(row=1, column=0, sticky="w", pady=4, padx=6)
    ttk.Entry(form, textvariable=self.telefone_fornecedor, width=40).grid(row=1, column=1, sticky="w", pady=4, padx=6)
    ttk.Button(form, text="Salvar Fornecedor", command=self.salvar_fornecedor).grid(row=2, column=1, pady=10, sticky="w")

    listagem = ttk.LabelFrame(self.fornecedores_tab, text="Fornecedores cadastrados", padding=12)
    listagem.pack(fill="both", expand=True, pady=(12, 0))

    colunas = ("id", "nome", "telefone")
    self.fornecedores_tree = ttk.Treeview(listagem, columns=colunas, show="headings", height=10)
    self.fornecedores_tree.heading("id", text="ID")
    self.fornecedores_tree.heading("nome", text="Nome")
    self.fornecedores_tree.heading("telefone", text="Telefone")
    self.fornecedores_tree.column("id", width=60, anchor="center")
    self.fornecedores_tree.column("nome", width=260)
    self.fornecedores_tree.column("telefone", width=140, anchor="center")
    scrollbar = ttk.Scrollbar(listagem, orient="vertical", command=self.fornecedores_tree.yview)
    self.fornecedores_tree.configure(yscrollcommand=scrollbar.set)
    self.fornecedores_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    actions = ttk.Frame(self.fornecedores_tab)
    actions.pack(fill="x", pady=8)
    ttk.Button(actions, text="Excluir selecionado", command=self.excluir_fornecedor).pack(side="left")

    self._carregar_fornecedores()

  def _build_vendas_tab(self):
    top = ttk.Frame(self.vendas_tab)
    top.pack(fill="x")

    self.venda_cliente = tk.StringVar()
    ttk.Label(top, text="Cliente").grid(row=0, column=0, padx=6, pady=6, sticky="w")
    self.venda_cliente_combo = ttk.Combobox(top, textvariable=self.venda_cliente, state="readonly", width=40)
    self.venda_cliente_combo.grid(row=0, column=1, padx=6, pady=6, sticky="w")

    self.venda_produto = tk.StringVar()
    self.venda_quantidade = tk.StringVar()
    ttk.Label(top, text="Produto").grid(row=1, column=0, padx=6, pady=6, sticky="w")
    self.venda_produto_combo = ttk.Combobox(top, textvariable=self.venda_produto, state="readonly", width=40)
    self.venda_produto_combo.grid(row=1, column=1, padx=6, pady=6, sticky="w")
    ttk.Label(top, text="Quantidade").grid(row=1, column=2, padx=6, pady=6, sticky="w")
    ttk.Entry(top, textvariable=self.venda_quantidade, width=12).grid(row=1, column=3, padx=6, pady=6, sticky="w")
    ttk.Button(top, text="Adicionar item", command=self.adicionar_item).grid(row=1, column=4, padx=6, pady=6)

    self.tree = ttk.Treeview(self.vendas_tab, columns=("produto", "qtd", "preco", "subtotal"), show="headings", height=10)
    self.tree.heading("produto", text="Produto")
    self.tree.heading("qtd", text="Qtd")
    self.tree.heading("preco", text="Preco")
    self.tree.heading("subtotal", text="Subtotal")
    self.tree.column("produto", width=360)
    self.tree.column("qtd", width=60, anchor="center")
    self.tree.column("preco", width=100, anchor="e")
    self.tree.column("subtotal", width=120, anchor="e")
    self.tree.pack(fill="both", expand=True, pady=10)

    bottom = ttk.Frame(self.vendas_tab)
    bottom.pack(fill="x")

    self.total_label = ttk.Label(bottom, text="Total: R$ 0.00", font=("Segoe UI", 12, "bold"))
    self.total_label.pack(side="left", padx=6, pady=6)

    ttk.Button(bottom, text="Finalizar Venda", command=self.finalizar_venda).pack(side="right", padx=6, pady=6)
    ttk.Button(bottom, text="Limpar Carrinho", command=self.limpar_carrinho).pack(side="right", padx=6, pady=6)

    lista_vendas = ttk.LabelFrame(self.vendas_tab, text="Vendas registradas", padding=12)
    lista_vendas.pack(fill="both", expand=True, pady=(12, 0))
    cols = ("id", "cliente", "data", "valor", "status")
    self.vendas_tree = ttk.Treeview(lista_vendas, columns=cols, show="headings", height=8)
    self.vendas_tree.heading("id", text="ID")
    self.vendas_tree.heading("cliente", text="Cliente")
    self.vendas_tree.heading("data", text="Data")
    self.vendas_tree.heading("valor", text="Valor")
    self.vendas_tree.heading("status", text="Status")
    self.vendas_tree.column("id", width=60, anchor="center")
    self.vendas_tree.column("cliente", width=120)
    self.vendas_tree.column("data", width=160)
    self.vendas_tree.column("valor", width=100, anchor="e")
    self.vendas_tree.column("status", width=100, anchor="center")
    vendas_scroll = ttk.Scrollbar(lista_vendas, orient="vertical", command=self.vendas_tree.yview)
    self.vendas_tree.configure(yscrollcommand=vendas_scroll.set)
    self.vendas_tree.pack(side="left", fill="both", expand=True)
    vendas_scroll.pack(side="right", fill="y")

    actions = ttk.Frame(self.vendas_tab)
    actions.pack(fill="x", pady=8)
    ttk.Button(actions, text="Excluir venda selecionada", command=self.excluir_venda).pack(side="left")

    self._carregar_clientes()
    self._carregar_produtos()
    self._carregar_vendas()

  def salvar_produto(self):
    try:
      preco = Decimal(self.preco_produto.get())
      estoque = int(self.estoque_produto.get())
    except (InvalidOperation, ValueError):
      messagebox.showerror("Erro", "Preco e estoque devem ser numericos.")
      return

    if not self.fornecedor_produto.get():
      messagebox.showerror("Erro", "Selecione um fornecedor.")
      return
    try:
      fornecedor_id = int(self.fornecedor_produto.get().split(" - ")[0])
    except Exception:
      messagebox.showerror("Erro", "Fornecedor selecionado invalido.")
      return

    novo = Produto(
      id=None,
      nome=self.nome_produto.get(),
      descricao=self.descricao_produto.get(),
      preco=preco,
      estoque=estoque,
      id_fornecedor=fornecedor_id
    )
    sucesso = self.produto_dao.salvar(novo)
    if sucesso:
      messagebox.showinfo("OK", f"Produto salvo com id {novo.id}")
      self.nome_produto.set("")
      self.descricao_produto.set("")
      self.preco_produto.set("")
      self.estoque_produto.set("")
      self.fornecedor_produto.set("")
      self._carregar_produtos()
    else:
      messagebox.showerror("Erro", "Nao foi possivel salvar o produto.")

  def buscar_produto(self):
    try:
      prod_id = int(self.busca_produto_id.get())
    except ValueError:
      messagebox.showerror("Erro", "ID invalido.")
      return

    produto = self.produto_dao.buscar_id(prod_id)
    if produto:
      self.resultado_produto.set(
        f"{produto.nome} | R$ {produto.preco} | Estoque: {produto.estoque} | Fornecedor: {produto.id_fornecedor}"
      )
    else:
      self.resultado_produto.set("Produto nao encontrado.")

  def _get_selected_id(self, tree):
    selecionados = tree.selection()
    if not selecionados:
      return None
    valores = tree.item(selecionados[0], "values")
    if not valores:
      return None
    try:
      return int(valores[0])
    except Exception:
      return None

  def excluir_produto(self):
    prod_id = self._get_selected_id(self.produtos_tree)
    if not prod_id:
      messagebox.showwarning("Selecione", "Selecione um produto na tabela.")
      return
    if not messagebox.askyesno("Confirmar", f"Excluir produto {prod_id}?"):
      return
    sucesso = self.produto_dao.deletar(prod_id)
    if sucesso:
      self._carregar_produtos()
      messagebox.showinfo("OK", "Produto excluido.")
    else:
      messagebox.showerror("Erro", "Nao foi possivel excluir o produto.")

  def excluir_cliente(self):
    cliente_id = self._get_selected_id(self.clientes_tree)
    if not cliente_id:
      messagebox.showwarning("Selecione", "Selecione um cliente na tabela.")
      return
    if not messagebox.askyesno("Confirmar", f"Excluir cliente {cliente_id}?"):
      return
    sucesso = self.cliente_dao.deletar(cliente_id)
    if sucesso:
      self._carregar_clientes()
      messagebox.showinfo("OK", "Cliente excluido.")
    else:
      messagebox.showerror("Erro", "Nao foi possivel excluir o cliente.")

  def excluir_fornecedor(self):
    fornecedor_id = self._get_selected_id(self.fornecedores_tree)
    if not fornecedor_id:
      messagebox.showwarning("Selecione", "Selecione um fornecedor na tabela.")
      return
    if not messagebox.askyesno("Confirmar", f"Excluir fornecedor {fornecedor_id}?"):
      return
    sucesso = self.fornecedor_dao.deletar(fornecedor_id)
    if sucesso:
      self._carregar_fornecedores()
      self._carregar_produtos()
      messagebox.showinfo("OK", "Fornecedor excluido.")
    else:
      messagebox.showerror("Erro", "Nao foi possivel excluir o fornecedor. Verifique se nao ha dependencias.")

  def excluir_venda(self):
    venda_id = self._get_selected_id(self.vendas_tree)
    if not venda_id:
      messagebox.showwarning("Selecione", "Selecione uma venda na tabela.")
      return
    if not messagebox.askyesno("Confirmar", f"Excluir venda {venda_id}?"):
      return
    sucesso = self.venda_dao.deletar(venda_id)
    if sucesso:
      self._carregar_vendas()
      messagebox.showinfo("OK", "Venda excluida.")
    else:
      messagebox.showerror("Erro", "Nao foi possivel excluir a venda.")

  def _carregar_produtos(self):
    if not hasattr(self, "produtos_tree"):
      return
    try:
      produtos = self.produto_dao.listar()
    except Exception:
      produtos = []
    self.produtos_cache = produtos
    for item in self.produtos_tree.get_children():
      self.produtos_tree.delete(item)
    fornecedor_nome = {f.id: f.nome_empresa for f in self.fornecedores_cache}
    for produto in produtos:
      fornecedor_display = fornecedor_nome.get(produto.id_fornecedor, produto.id_fornecedor)
      self.produtos_tree.insert(
        "",
        "end",
        values=(
          produto.id,
          produto.nome,
          f"R$ {produto.preco}",
          produto.estoque,
          fornecedor_display,
        ),
      )
    if hasattr(self, "venda_produto_combo"):
      options = [f"{p.id} - {p.nome}" for p in produtos]
      self.venda_produto_combo["values"] = options
      if options and not self.venda_produto_combo.get():
        self.venda_produto_combo.current(0)

  def _carregar_clientes(self):
    try:
      clientes = self.cliente_dao.listar()
    except Exception:
      clientes = []
    self.clientes_cache = clientes

    if hasattr(self, "clientes_tree"):
      for item in self.clientes_tree.get_children():
        self.clientes_tree.delete(item)
      for cliente in clientes:
        self.clientes_tree.insert(
          "",
          "end",
          values=(
            cliente.id,
            cliente.nome,
            cliente.cpf,
            cliente.email,
            cliente.endereco,
          ),
        )

    if hasattr(self, "venda_cliente_combo"):
      options = [f"{c.id} - {c.nome}" for c in clientes]
      self.venda_cliente_combo["values"] = options
      if options and not self.venda_cliente_combo.get():
        self.venda_cliente_combo.current(0)

  def _carregar_vendas(self):
    if not hasattr(self, "vendas_tree"):
      return
    try:
      vendas = self.venda_dao.listar()
    except Exception:
      vendas = []
    for item in self.vendas_tree.get_children():
      self.vendas_tree.delete(item)
    clientes_nome = {c.id: c.nome for c in self.clientes_cache}
    for venda in vendas:
      cliente = clientes_nome.get(venda.id_cliente, venda.id_cliente)
      data_str = str(venda.data_venda) if hasattr(venda, "data_venda") else str(venda.data)
      self.vendas_tree.insert(
        "",
        "end",
        values=(venda.id, cliente, data_str, f"R$ {venda.valor_total}", venda.status),
      )

  def salvar_cliente(self):
    novo = Cliente(
      id=None,
      nome=self.nome_cliente.get(),
      cpf=self.cpf_cliente.get(),
      email=self.email_cliente.get(),
      endereco=self.endereco_cliente.get()
    )
    try:
      self.cliente_dao.salvar(novo)
      messagebox.showinfo("OK", f"Cliente salvo com id {novo.id}")
      self.nome_cliente.set("")
      self.cpf_cliente.set("")
      self.email_cliente.set("")
      self.endereco_cliente.set("")
      self._carregar_clientes()
    except Exception as e:
      messagebox.showerror("Erro", f"Falha ao salvar cliente: {e}")

  def salvar_fornecedor(self):
    if not self.nome_fornecedor.get().strip():
      messagebox.showerror("Erro", "Informe o nome da empresa.")
      return
    novo = Fornecedor(
      id=None,
      nome_empresa=self.nome_fornecedor.get(),
      telefone=self.telefone_fornecedor.get(),
    )
    sucesso = self.fornecedor_dao.salvar(novo)
    if sucesso:
      messagebox.showinfo("OK", f"Fornecedor salvo com id {novo.id}")
      self.nome_fornecedor.set("")
      self.telefone_fornecedor.set("")
      self._carregar_fornecedores()
      self._carregar_produtos()
    else:
      messagebox.showerror("Erro", "Nao foi possivel salvar o fornecedor.")

  def _carregar_fornecedores(self):
    try:
      fornecedores = self.fornecedor_dao.listar()
    except Exception:
      fornecedores = []
    self.fornecedores_cache = fornecedores

    if hasattr(self, "fornecedores_tree"):
      for item in self.fornecedores_tree.get_children():
        self.fornecedores_tree.delete(item)
      for fornecedor in fornecedores:
        self.fornecedores_tree.insert(
          "",
          "end",
          values=(fornecedor.id, fornecedor.nome_empresa, fornecedor.telefone or ""),
        )

    if hasattr(self, "fornecedor_produto_combo"):
      options = [f"{f.id} - {f.nome_empresa}" for f in fornecedores]
      self.fornecedor_produto_combo["values"] = options
      if options and not self.fornecedor_produto_combo.get():
        self.fornecedor_produto_combo.current(0)

  def adicionar_item(self):
    if not self.venda_produto.get():
      messagebox.showerror("Erro", "Selecione um produto.")
      return
    try:
      prod_id = int(self.venda_produto.get().split(" - ")[0])
      qtd = int(self.venda_quantidade.get())
    except ValueError:
      messagebox.showerror("Erro", "Produto e quantidade devem ser validos.")
      return
    if qtd <= 0:
      messagebox.showerror("Erro", "Quantidade deve ser maior que zero.")
      return

    produto = self.produto_dao.buscar_id(prod_id)
    if not produto:
      messagebox.showerror("Erro", "Produto nao encontrado.")
      return
    if qtd > produto.estoque:
      messagebox.showwarning("Estoque insuficiente", f"Disponivel: {produto.estoque}")
      return

    item = ItemVenda(
      id=None,
      id_venda=None,
      id_produto=produto.id,
      quantidade=qtd,
      preco_unitario=produto.preco
    )
    self.carrinho.append(item)
    subtotal = produto.preco * qtd
    self.valor_total += subtotal
    self.tree.insert("", "end", values=(produto.nome, qtd, f"R$ {produto.preco}", f"R$ {subtotal}"))
    self.total_label.config(text=f"Total: R$ {self.valor_total}")

    self.venda_produto.set("")
    self.venda_quantidade.set("")

  def limpar_carrinho(self):
    self.carrinho.clear()
    self.valor_total = Decimal("0.00")
    for item in self.tree.get_children():
      self.tree.delete(item)
    self.total_label.config(text="Total: R$ 0.00")

  def finalizar_venda(self):
    if not self.carrinho:
      messagebox.showwarning("Carrinho vazio", "Adicione itens antes de finalizar.")
      return
    if not self.venda_cliente.get():
      messagebox.showerror("Erro", "Selecione um cliente.")
      return
    try:
      id_cliente = int(self.venda_cliente.get().split(" - ")[0])
    except Exception:
      messagebox.showerror("Erro", "Cliente selecionado invalido.")
      return

    nova_venda = Venda(
      id=None,
      data_venda=datetime.now(),
      valor_total=self.valor_total,
      id_cliente=id_cliente,
      status="FECHADO"
    )
    nova_venda.itens = self.carrinho

    sucesso = self.venda_dao.realizar_venda(nova_venda)
    if sucesso:
      messagebox.showinfo("Sucesso", f"Venda #{nova_venda.id} finalizada.")
      self.limpar_carrinho()
      self.venda_cliente.set("")
      self._carregar_vendas()
    else:
      messagebox.showerror("Erro", "Falha ao finalizar venda.")


if __name__ == "__main__":
  app = MercatusApp()
  app.mainloop()
