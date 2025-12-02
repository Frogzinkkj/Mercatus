from src.models.cliente import Cliente

class ClienteDAO:
  def __init__(self,conexao):
    self.conexao = conexao
  
  def salvar(self,cliente:Cliente):
    cursor = self.conexao.cursor()

    sql = """
    INSERT INTO clientes (nome, cpf, email, endereco)
    VALUES (%s, %s, %s, %s)
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

  def listar(self):
    cursor = self.conexao.cursor()
    sql = "SELECT id, nome, cpf, email, endereco FROM clientes ORDER BY id"
    try:
      cursor.execute(sql)
      clientes = []
      for tupla in cursor.fetchall():
        clientes.append(
          Cliente(
            id=tupla[0],
            nome=tupla[1],
            cpf=tupla[2],
            email=tupla[3],
            endereco=tupla[4],
          )
        )
      return clientes
    except Exception as e:
      print(f"erro {e} ao listar clientes")
      return []
    finally:
      cursor.close()

  def deletar(self, id):
    cursor = self.conexao.cursor()
    try:
      cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
      self.conexao.commit()
      return cursor.rowcount > 0
    except Exception as e:
      self.conexao.rollback()
      print(f"erro {e} ao excluir cliente")
      return False
    finally:
      cursor.close()
