import sqlite3

class ConceptosModel:
    def __init__(self, db_path="datos_aduaneros.db"):
        self.db_path = db_path

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def agregar_concepto(self, descripcion, tipo, aplica_iva):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO conceptos_facturables (descripcion, tipo, aplica_iva)
                VALUES (?, ?, ?)
            ''', (descripcion, tipo, aplica_iva))
            conexion.commit()
            conexion.close()
            return True, "Concepto registrado con éxito."
        except Exception as e:
            return False, f"Error inesperado: {e}"

    def obtener_conceptos(self):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, descripcion, tipo, aplica_iva FROM conceptos_facturables")
        filas = cursor.fetchall()
        conexion.close()
        return filas
    
    def actualizar_concepto(self, concepto_id, descripcion, tipo, aplica_iva):
        """Actualiza los datos de un concepto existente."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE conceptos_facturables 
                SET descripcion = ?, tipo = ?, aplica_iva = ?
                WHERE id = ?
            ''', (descripcion, tipo, aplica_iva, concepto_id))
            conexion.commit()
            conexion.close()
            return True, "Concepto actualizado con éxito."
        except Exception as e:
            return False, f"Error inesperado: {e}"

    def eliminar_concepto(self, concepto_id):
        """Elimina un concepto por su ID."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM conceptos_facturables WHERE id = ?", (concepto_id,))
            conexion.commit()
            conexion.close()
            return True, "Concepto eliminado correctamente."
        except Exception as e:
            return False, f"Error al eliminar: {e}"