import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="#Jenifer2007",
        database="DOE"
    )
    print("Conexão com MySQL OK")
    db.close()
except mysql.connector.Error as err:
    print("Erro ao conectar:", err)