
DROP VIEW IF EXISTS vw_produtos_fornecedores;
CREATE VIEW vw_produtos_fornecedores AS
SELECT
  p.id,
  p.nome,
  p.descricao,
  p.preco,
  p.estoque,
  p.id_fornecedor,
  f.nome_empresa AS fornecedor
FROM produtos p
LEFT JOIN fornecedores f ON f.id = p.id_fornecedor;

DROP VIEW IF EXISTS vw_vendas_resumo;
CREATE VIEW vw_vendas_resumo AS
SELECT
  v.id,
  v.data_venda,
  v.valor_total,
  v.status,
  v.id_cliente,
  c.nome AS cliente
FROM vendas v
LEFT JOIN clientes c ON c.id = v.id_cliente;

-- Functions
CREATE OR REPLACE FUNCTION fn_baixar_estoque(p_id_produto INT, p_qtd INT)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
  v_rows INT;
BEGIN
  IF p_qtd <= 0 THEN
    RAISE EXCEPTION 'Quantidade deve ser maior que zero';
  END IF;

  UPDATE produtos
  SET estoque = estoque - p_qtd
  WHERE id = p_id_produto
    AND estoque >= p_qtd;

  GET DIAGNOSTICS v_rows = ROW_COUNT;
  IF v_rows = 0 THEN
    RETURN FALSE;
  END IF;
  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION fn_finalizar_venda(p_id_cliente INT, p_itens JSONB)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  v_id_venda INT;
  v_total NUMERIC(12,2) := 0;
  v_item JSONB;
  v_id_prod INT;
  v_qtd INT;
  v_preco NUMERIC(12,2);
BEGIN
  IF p_itens IS NULL OR jsonb_array_length(p_itens) = 0 THEN
    RAISE EXCEPTION 'Carrinho vazio';
  END IF;

  INSERT INTO vendas (id_cliente, data_venda, valor_total, status)
  VALUES (p_id_cliente, NOW(), 0, 'FECHADO')
  RETURNING id INTO v_id_venda;

  FOR v_item IN SELECT * FROM jsonb_array_elements(p_itens) LOOP
    v_id_prod := (v_item ->> 'id_produto')::INT;
    v_qtd := (v_item ->> 'quantidade')::INT;
    v_preco := (v_item ->> 'preco_unitario')::NUMERIC;

    IF v_id_prod IS NULL THEN
      RAISE EXCEPTION 'Item sem id_produto';
    END IF;
    IF v_qtd IS NULL OR v_qtd <= 0 THEN
      RAISE EXCEPTION 'Quantidade invalida para produto %', v_id_prod;
    END IF;
    IF v_preco IS NULL OR v_preco < 0 THEN
      RAISE EXCEPTION 'Preco invalido para produto %', v_id_prod;
    END IF;

    IF NOT fn_baixar_estoque(v_id_prod, v_qtd) THEN
      RAISE EXCEPTION 'Estoque insuficiente para produto %', v_id_prod;
    END IF;

    INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario)
    VALUES (v_id_venda, v_id_prod, v_qtd, v_preco);

    v_total := v_total + (v_qtd * v_preco);
  END LOOP;

  UPDATE vendas SET valor_total = v_total WHERE id = v_id_venda;
  RETURN v_id_venda;

EXCEPTION
  WHEN OTHERS THEN
    IF v_id_venda IS NOT NULL THEN
      -- limpa insercoes desta venda antes de reerguer o erro
      DELETE FROM itens_venda WHERE id_venda = v_id_venda;
      DELETE FROM vendas WHERE id = v_id_venda;
    END IF;
    RAISE;
END;
$$;
