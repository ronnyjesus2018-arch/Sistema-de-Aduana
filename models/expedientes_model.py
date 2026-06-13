import sqlite3
from datetime import datetime

class ExpedientesModel:
    def __init__(self, db_path="datos_aduaneros.db"):
        self.db_path = db_path

    def conectar(self):
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def obtener_clientes_combo(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, razon_social FROM clientes ORDER BY razon_social")
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def agregar_expediente(self, numero, cliente_id, tipo, aduana, bl, contenedores, mercancia):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT INTO expedientes (numero_expediente, cliente_id, tipo_operacion, aduana, bl_guia, contenedores, mercancia, fecha_apertura)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (numero, cliente_id, tipo, aduana, bl, contenedores, mercancia, fecha))
            conexion.commit()
            conexion.close()
            return True, "Expediente registrado con éxito."
        except sqlite3.IntegrityError:
            return False, "Error: El número de expediente ya existe."
        except Exception as e:
            return False, f"Error: {e}"

    def obtener_expedientes(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT e.id, e.numero_expediente, c.razon_social, e.tipo_operacion, 
                   e.aduana, e.bl_guia, e.estado, e.fecha_apertura
            FROM expedientes e
            JOIN clientes c ON e.cliente_id = c.id
            ORDER BY e.id DESC
        ''')
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def eliminar_expediente(self, exp_id):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM expedientes WHERE id = ?", (exp_id,))
            conexion.commit()
            conexion.close()
            return True, "Expediente eliminado."
        except Exception as e:
            return False, f"Error: {e}"