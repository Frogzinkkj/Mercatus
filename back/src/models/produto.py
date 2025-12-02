class Produto:
  def __init__(self, id, nome, preco, estoque, id_fornecedor, descricao=None):
    self.id = id
    self.nome = nome
    self.descricao = descricao
    self.preco = preco
    self.estoque = estoque
    self.id_fornecedor = id_fornecedor

# Compatibilidade com código antigo que usava nome minúsculo
produto = Produto
