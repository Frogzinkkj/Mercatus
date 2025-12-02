from src.models.produto import Produto

class ProdutoDAO:
    def __init__(self, conexao):
        self.conexao = conexao

    def salvar(self, produto):
        cursor = self.conexao.cursor()
        sql = """
            INSERT INTO produtos (nome, descricao, preco, estoque, id_fornecedor)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        valores = (produto.nome, produto.descricao, produto.preco, produto.estoque, produto.id_fornecedor)
        
        try:
            cursor.execute(sql, valores)
            id_gerado = cursor.fetchone()[0]
            produto.id = id_gerado
            self.conexao.commit()
            return True
        except Exception:
            self.conexao.rollback()
            return False
        finally:
            cursor.close()

    def buscar_id(self, id):
        cursor = self.conexao.cursor()
        sql = "SELECT id, nome, descricao, preco, estoque, id_fornecedor FROM produtos WHERE id = %s"
        
        try:
            cursor.execute(sql, (id,))
            tupla = cursor.fetchone()
            
            if tupla:
                novo_produto = Produto(
                    id=tupla[0],
                    nome=tupla[1],
                    descricao=tupla[2],
                    preco=tupla[3],
                    estoque=tupla[4],
                    id_fornecedor=tupla[5]
                )
                return novo_produto
            else:
                return None
        except Exception:
            return None
        finally:
            cursor.close()

    def listar(self):
        cursor = self.conexao.cursor()
        sql = "SELECT id, nome, descricao, preco, estoque, id_fornecedor FROM produtos ORDER BY id"
        try:
            cursor.execute(sql)
            produtos = []
            for tupla in cursor.fetchall():
                produtos.append(
                    Produto(
                        id=tupla[0],
                        nome=tupla[1],
                        descricao=tupla[2],
                        preco=tupla[3],
                        estoque=tupla[4],
                        id_fornecedor=tupla[5],
                    )
                )
            return produtos
        except Exception:
            return []
        finally:
            cursor.close()
    
    def baixar_estoque(self, id, quantidade):
        cursor = self.conexao.cursor()
        sql = "UPDATE produtos SET estoque = estoque - %s WHERE id = %s"
        try:
            cursor.execute(sql, (quantidade, id))
            self.conexao.commit()
            return True
        except Exception:
            self.conexao.rollback()
            return False
        finally:
            cursor.close()

    def deletar(self, id):
        cursor = self.conexao.cursor()
        try:
            cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
            self.conexao.commit()
            return cursor.rowcount > 0
        except Exception:
            self.conexao.rollback()
            return False
        finally:
            cursor.close()
