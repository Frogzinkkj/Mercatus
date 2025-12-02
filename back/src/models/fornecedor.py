class Fornecedor:
  def __init__(self, id, nome_empresa, telefone=None):
    self.id = id
    self.nome_empresa = nome_empresa
    self.telefone = telefone

# Alias para compatibilidade com possiveis usos anteriores
fornecedor = Fornecedor
