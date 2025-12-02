from src.models.venda import Venda

class VendaDAO:
    def __init__(self, conexao):
        self.conexao = conexao

    def realizar_venda(self, venda: Venda):
        """
        Recebe um objeto Venda preenchido (com cliente e lista de itens).
        Retorna True se sucesso, False se erro.
        """
        cursor = self.conexao.cursor()
        
        sql_venda = """
            INSERT INTO vendas (id_cliente, data_venda, valor_total, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        
        sql_item = """
            INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario)
            VALUES (%s, %s, %s, %s)
        """
        
        sql_baixa_estoque = """
            UPDATE produtos 
            SET estoque = estoque - %s 
            WHERE id = %s
        """

        try:
            cursor.execute(sql_venda, (
                venda.id_cliente, 
                venda.data_venda, 
                venda.valor_total, 
                venda.status
            ))
            
            id_venda_gerado = cursor.fetchone()[0]
            venda.id = id_venda_gerado 

            for item in venda.itens:
                
                cursor.execute(sql_item, (
                    id_venda_gerado,
                    item.id_produto,
                    item.quantidade,
                    item.preco_unitario
                ))
                cursor.execute(sql_baixa_estoque, (
                    item.quantidade, 
                    item.id_produto
                ))
            self.conexao.commit()
            print(f"Venda #{venda.id} realizada com sucesso!")
            return True

        except Exception as e:
            self.conexao.rollback()
            print(f"Erro na transação de venda: {e}")
            return False
            
        finally:
            cursor.close()

    def listar(self):
        cursor = self.conexao.cursor()
        sql = "SELECT id, id_cliente, data_venda, valor_total, status FROM vendas ORDER BY id"
        try:
            cursor.execute(sql)
            vendas = []
            for tupla in cursor.fetchall():
                vendas.append(
                    Venda(
                        id=tupla[0],
                        data_venda=tupla[2],
                        valor_total=tupla[3],
                        id_cliente=tupla[1],
                        status=tupla[4],
                    )
                )
            return vendas
        except Exception as e:
            print(f"Erro ao listar vendas: {e}")
            return []
        finally:
            cursor.close()

    def deletar(self, id):
        cursor = self.conexao.cursor()
        try:
            cursor.execute("DELETE FROM itens_venda WHERE id_venda = %s", (id,))
            cursor.execute("DELETE FROM vendas WHERE id = %s", (id,))
            self.conexao.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conexao.rollback()
            print(f"Erro ao excluir venda: {e}")
            return False
        finally:
            cursor.close()
