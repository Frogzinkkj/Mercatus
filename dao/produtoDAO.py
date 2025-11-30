from src.models.produto import Produto

class ProdutoDAO:
  def __init__(self,conexao):
    self.conexao = conexao

  def buscarId(self, id):
    cursor = self.conexao.cursor()
    sql= """
    SELECT id, nome, descricao, preco, estoque, id_fornecedor FROM produtos WHERE id = %s
    """
    try:
      cursor.execute(sql,(id,))
      produto_gerado = cursor.fetchone()
      if produto_gerado:
        novo_produto = Produto(
          id=produto_gerado[0],
          nome=produto_gerado[1],
          descricao=produto_gerado[2],
          preco = produto_gerado[3],
          estoque= produto_gerado[4],
          id_fornecedor=produto_gerado[5]
        )
        return novo_produto
      else:
        return None
    except Exception as e:
      print(f"Erro ao buscar produto: {e}")
      return None
    finally:
      cursor.close();

  def baixar_estoque(self,id,quantidade):
    cursor = self.conexao.cursor()
    sql= """
    UPDATE produtos
    set estoque = estoque-%s
    WHERE id = %s
    """
    try:
      cursor.execute(sql,(quantidade,id,))
      self.conexao.commit()
      return True
    except Exception as e:
      print(f"Erro ao mudar estque do produto: {e}")
      return False
    finally:
      cursor.close();