import sys
from datetime import datetime
from decimal import Decimal

from src.conexao import criar_conexao

from src.models.produto import Produto
from src.models.cliente import Cliente
from src.models.venda import Venda
from src.models.item_venda import ItemVenda

from src.dao.produtoDAO import ProdutoDAO
from src.dao.clienteDAO import ClienteDAO
from src.dao.vendaDAO import VendaDAO

def exibir_menu():
    print("\n=== SISTEMA MERCATUS ===")
    print("1. Cadastrar Produto")
    print("2. Cadastrar Cliente")
    print("3. Realizar Venda (CARRINHO)")
    print("4. Consultar Estoque")
    print("0. Sair")

def cadastrar_produto_ui(conexao):
    print("\n--- NOVO PRODUTO ---")
    nome = input("Nome: ")
    descricao = input("Descrição: ")
    try:
        preco = Decimal(input("Preço: "))
        estoque = int(input("Estoque Inicial: "))
        id_fornecedor = int(input("ID do Fornecedor: "))
        
        novo_prod = Produto(
            id=None, 
            nome=nome, 
            descricao=descricao, 
            preco=preco, 
            estoque=estoque, 
            id_fornecedor=id_fornecedor
        )
        
        dao = ProdutoDAO(conexao)
        dao.salvar(novo_prod)
        print("Produto cadastrado com sucesso")
        
    except ValueError:
        print("Erro: Preço ou Estoque devem ser números")

def realizar_venda_ui(conexao):
    print("\n--- NOVA VENDA ---")
    produto_dao = ProdutoDAO(conexao)
    venda_dao = VendaDAO(conexao)

    try:
        id_cliente = int(input("ID do Cliente: "))
    except ValueError:
        print("ID inválido")
        return

    carrinho_itens = []
    valor_total_venda = Decimal('0.00')

    while True:
        print("\n--- ADICIONAR ITEM (Digite 0 no ID para fechar a conta) ---")
        try:
            id_prod = int(input("ID do Produto: "))
            if id_prod == 0:
                break
            
            produto = produto_dao.buscar_id(id_prod)
            
            if not produto:
                print("Produto não encontrado")
                continue
            
            print(f"Produto: {produto.nome} | Preço: R$ {produto.preco} | Estoque: {produto.estoque}")
            
            qtd = int(input("Quantidade: "))
            
            if qtd > produto.estoque:
                print(f"Estoque insuficiente. Disponível: {produto.estoque}")
                continue
            
            if qtd <= 0:
                print("Quantidade inválida")
                continue

            item = ItemVenda(
                id=None,
                id_venda=None,
                id_produto=produto.id,
                quantidade=qtd,
                preco_unitario=produto.preco
            )
            
            carrinho_itens.append(item)
            subtotal = produto.preco * qtd
            valor_total_venda += subtotal
            print(f"Item adicionado. Subtotal: R$ {subtotal}")

        except ValueError:
            print("Digite apenas números")

    if not carrinho_itens:
        print("Carrinho vazio. Venda cancelada")
        return

    print(f"\nValor Total da Venda: R$ {valor_total_venda}")
    confirmar = input("Confirmar venda? (S/N): ")

    if confirmar.upper() == 'S':
        nova_venda = Venda(
            id=None,
            id_cliente=id_cliente,
            data_venda=datetime.now(),
            valor_total=valor_total_venda,
            status="FECHADO"
        )
        nova_venda.itens = carrinho_itens
        
        sucesso = venda_dao.realizar_venda(nova_venda)
        
        if sucesso:
            print("Venda finalizada com sucesso")
        else:
            print("Erro ao finalizar venda")
    else:
        print("Venda cancelada pelo usuário")

if __name__ == "__main__":
    conn = criar_conexao()
    
    if not conn:
        print("Falha ao conectar no banco. Encerrando")
        sys.exit()

    while True:
        exibir_menu()
        opcao = input("Escolha: ")

        if opcao == '1':
            cadastrar_produto_ui(conn)
        elif opcao == '2':
            pass 
        elif opcao == '3':
            realizar_venda_ui(conn)
        elif opcao == '4':
            pass
        elif opcao == '0':
            print("Saindo...")
            conn.close()
            break
        else:
            print("Opção inválida")