try:
    import psycopg2
except ImportError:
    psycopg2 = None
    print("psycopg2 nao encontrado; a interface abrira em modo offline.")


def criar_conexao():
    if not psycopg2:
        return None
    try:
        conn = psycopg2.connect(
            database="Mercatus",
            host="localhost",
            user="postgres",
            password="admin",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Erro na conexao: {e}")
        return None
