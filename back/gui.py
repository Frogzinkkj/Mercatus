import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.conexao import criar_conexao
from src.dao.produtoDAO import ProdutoDAO
from src.dao.clienteDAO import ClienteDAO
from src.dao.vendaDAO import VendaDAO
from src.models.produto import Produto
from src.models.cliente import Cliente
from src.models.item_venda import ItemVenda
from src.models.venda import Venda


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
    else:
      # fallback em memoria para apresentacao sem banco
      self.produto_dao = InMemoryProdutoDAO()
      self.cliente_dao = InMemoryClienteDAO()
      self.venda_dao = InMemoryVendaDAO(self.produto_dao)

    self.carrinho = []
    self.valor_total = Decimal("0.00")

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
    self.vendas_tab = ttk.Frame(notebook, padding=16)

    notebook.add(self.produtos_tab, text="Produtos")
    notebook.add(self.clientes_tab, text="Clientes")
    notebook.add(self.vendas_tab, text="Vendas")

    self._build_produtos_tab()
    self._build_clientes_tab()
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
      ("ID Fornecedor", self.fornecedor_produto),
    ]

    for idx, (label, var) in enumerate(fields):
      ttk.Label(form, text=label).grid(row=idx, column=0, sticky="w", pady=4, padx=6)
      ttk.Entry(form, textvariable=var, width=40).grid(row=idx, column=1, sticky="w", pady=4, padx=6)

    ttk.Button(form, text="Salvar Produto", command=self.salvar_produto).grid(row=len(fields), column=1, pady=10, sticky="w")

    busca = ttk.LabelFrame(self.produtos_tab, text="Buscar Produto", padding=12)
    busca.pack(fill="x", pady=(16, 0))

    self.busca_produto_id = tk.StringVar()
    ttk.Label(busca, text="ID").grid(row=0, column=0, padx=6, pady=4, sticky="w")
    ttk.Entry(busca, textvariable=self.busca_produto_id, width=12).grid(row=0, column=1, padx=6, pady=4, sticky="w")
    ttk.Button(busca, text="Buscar", command=self.buscar_produto).grid(row=0, column=2, padx=6, pady=4)

    self.resultado_produto = tk.StringVar()
    ttk.Label(busca, textvariable=self.resultado_produto, font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=3, sticky="w", padx=6, pady=6)

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

  def _build_vendas_tab(self):
    top = ttk.Frame(self.vendas_tab)
    top.pack(fill="x")

    self.venda_id_cliente = tk.StringVar()
    ttk.Label(top, text="ID do Cliente").grid(row=0, column=0, padx=6, pady=6, sticky="w")
    ttk.Entry(top, textvariable=self.venda_id_cliente, width=12).grid(row=0, column=1, padx=6, pady=6, sticky="w")

    self.venda_produto_id = tk.StringVar()
    self.venda_quantidade = tk.StringVar()
    ttk.Label(top, text="ID Produto").grid(row=1, column=0, padx=6, pady=6, sticky="w")
    ttk.Entry(top, textvariable=self.venda_produto_id, width=12).grid(row=1, column=1, padx=6, pady=6, sticky="w")
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

  def salvar_produto(self):
    try:
      preco = Decimal(self.preco_produto.get())
      estoque = int(self.estoque_produto.get())
      fornecedor = int(self.fornecedor_produto.get())
    except (InvalidOperation, ValueError):
      messagebox.showerror("Erro", "Preco, estoque e fornecedor devem ser numericos.")
      return

    novo = Produto(
      id=None,
      nome=self.nome_produto.get(),
      descricao=self.descricao_produto.get(),
      preco=preco,
      estoque=estoque,
      id_fornecedor=fornecedor
    )
    sucesso = self.produto_dao.salvar(novo)
    if sucesso:
      messagebox.showinfo("OK", f"Produto salvo com id {novo.id}")
      self.nome_produto.set("")
      self.descricao_produto.set("")
      self.preco_produto.set("")
      self.estoque_produto.set("")
      self.fornecedor_produto.set("")
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
    except Exception as e:
      messagebox.showerror("Erro", f"Falha ao salvar cliente: {e}")

  def adicionar_item(self):
    try:
      prod_id = int(self.venda_produto_id.get())
      qtd = int(self.venda_quantidade.get())
    except ValueError:
      messagebox.showerror("Erro", "ID de produto e quantidade devem ser numeros.")
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

    self.venda_produto_id.set("")
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
    try:
      id_cliente = int(self.venda_id_cliente.get())
    except ValueError:
      messagebox.showerror("Erro", "ID do cliente invalido.")
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
      self.venda_id_cliente.set("")
    else:
      messagebox.showerror("Erro", "Falha ao finalizar venda.")


if __name__ == "__main__":
  app = MercatusApp()
  app.mainloop()
