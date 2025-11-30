from src.models.cliente import Cliente

class ClienteDAO:
  def __init__(self,conexao):
    self.conexao = conexao
  
  def salvar(self,cliente:Cliente):
    cursor = self.conexao.cursor()

    sql= """"
    INSERT INTO clientes (nome,cpf,email,endereco)
    VALUES(%s,%s,%s,%s)
    RETURNING id;
    """
    valores = (cliente.nome,cliente.cpf,cliente.email,cliente.endereco)
    try:
      cursor.execute(sql,valores)
      id_gerado = cursor.fetchone()[0]
      cliente.id = id_gerado
      self.conexao.commit()
      
      print(f"Cliente {cliente.nome} salvo com id {cliente.id}")
    except Exception as e:
      self.conexao.rollback()
      print(f"erro {e} ao salvar cliente")
    
    finally:
      cursor.close()