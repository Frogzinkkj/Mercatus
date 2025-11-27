import decimal


class produto:
  def __init__(self,id,nome,preco,estoque,id_fornecedor):
    self.id = id
    self.preco = preco
    self.estoque = estoque
    self.id_fornecedor = id_fornecedor
    self.nome = nome