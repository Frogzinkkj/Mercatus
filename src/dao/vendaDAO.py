from venda import Venda

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