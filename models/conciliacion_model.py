import sqlite3
from datetime import datetime

class ConciliacionModel:
    def __init__(self, db_path="datos_aduaneros.db"):
        self.db_path = db_path

    def conectar(self):
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def obtener_expedientes_combo(self):
        """Obtiene los expedientes abiertos para el combobox."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, numero_expediente FROM expedientes ORDER BY id DESC")
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def registrar_transaccion(self, expediente_id, tipo, descripcion, monto):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT INTO transacciones_expediente (expediente_id, tipo, descripcion, monto, fecha)
                VALUES (?, ?, ?, ?, ?)
            ''', (expediente_id, tipo, descripcion, monto, fecha))
            conexion.commit()
            conexion.close()
            return True, "Transacción registrada."
        except Exception as e:
            return False, f"Error: {e}"

    def obtener_transacciones(self, expediente_id):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT id, fecha, tipo, descripcion, monto 
            FROM transacciones_expediente 
            WHERE expediente_id = ? ORDER BY id DESC
        ''', (expediente_id,))
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def obtener_resumen(self, expediente_id):
        """Calcula el total de anticipos, gastos y el saldo."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM transacciones_expediente WHERE expediente_id = ? AND tipo = 'ANTICIPO'", (expediente_id,))
        total_anticipos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM transacciones_expediente WHERE expediente_id = ? AND tipo = 'GASTO'", (expediente_id,))
        total_gastos = cursor.fetchone()[0]
        
        conexion.close()
        saldo = total_anticipos - total_gastos
        return total_anticipos, total_gastos, saldo
    
    def eliminar_transaccion(self, transaccion_id):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM transacciones_expediente WHERE id = ?", (transaccion_id,))
            conexion.commit()
            conexion.close()
            return True, "Transacción eliminada."
        except Exception as e:
            return False, f"Error al eliminar: {e}"