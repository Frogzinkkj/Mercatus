class ItemVenda:
  def __init__(self, id, id_venda, id_produto, quantidade, preco_unitario):
    self.id = id
    self.id_venda = id_venda
    self.id_produto = id_produto
    self.quantidade = quantidade
    self.preco_unitario = preco_unitario

# Compatibilidade com código antigo
item_venda = ItemVenda
