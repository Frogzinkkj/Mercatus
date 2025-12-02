from src.models.fornecedor import Fornecedor


class FornecedorDAO:
    def __init__(self, conexao):
        self.conexao = conexao

    def salvar(self, fornecedor: Fornecedor):
        cursor = self.conexao.cursor()
        sql = """
            INSERT INTO fornecedores (nome_empresa, telefone)
            VALUES (%s, %s)
            RETURNING id
        """
        try:
            cursor.execute(sql, (fornecedor.nome_empresa, fornecedor.telefone))
            fornecedor.id = cursor.fetchone()[0]
            self.conexao.commit()
            return True
        except Exception:
            self.conexao.rollback()
            return False
        finally:
            cursor.close()

    def listar(self):
        cursor = self.conexao.cursor()
        sql = "SELECT id, nome_empresa, telefone FROM fornecedores ORDER BY id"
        try:
            cursor.execute(sql)
            fornecedores = []
            for tupla in cursor.fetchall():
                fornecedores.append(
                    Fornecedor(
                        id=tupla[0],
                        nome_empresa=tupla[1],
                        telefone=tupla[2],
                    )
                )
            return fornecedores
        except Exception:
            return []
        finally:
            cursor.close()

    def deletar(self, id):
        cursor = self.conexao.cursor()
        try:
            cursor.execute("DELETE FROM fornecedores WHERE id = %s", (id,))
            self.conexao.commit()
            return cursor.rowcount > 0
        except Exception:
            self.conexao.rollback()
            return False
        finally:
            cursor.close()
