import psycopg2

def criar_conexao():
    try:
        conn = psycopg2.connect(
            database="mercatus_db",
            host="localhost",
            user="postgres",
            password="admin",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Erro na conexao: {e}")
        return None