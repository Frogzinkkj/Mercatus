class Venda:
  def __init__(self,id,data_venda,valor_total,id_cliente,status):
    self.itens = []
    self.id = id
    self.data_venda = data_venda
    self.valor_total = valor_total
    self.id_cliente = id_cliente
    self.status = status

