import sqlite3

class ClientesModel:
    def __init__(self, db_path="datos_aduaneros.db"):
        self.db_path = db_path

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def agregar_cliente(self, razon_social, rif, direccion, telefono):
        """Inserta un nuevo cliente en la base de datos."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO clientes (razon_social, rif, direccion, telefono)
                VALUES (?, ?, ?, ?)
            ''', (razon_social, rif, direccion, telefono))
            conexion.commit()
            conexion.close()
            return True, "Cliente agregado con éxito."
        except sqlite3.IntegrityError:
            return False, "Error: El RIF ya está registrado."
        except Exception as e:
            return False, f"Error inesperado: {e}"

    def obtener_clientes(self):
        """Devuelve una lista con todos los clientes."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, razon_social, rif, direccion, telefono FROM clientes")
        filas = cursor.fetchall()
        conexion.close()
        return filas
    
    def actualizar_cliente(self, cliente_id, razon_social, rif, direccion, telefono):
        """Actualiza los datos de un cliente existente."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute('''
                UPDATE clientes 
                SET razon_social = ?, rif = ?, direccion = ?, telefono = ?
                WHERE id = ?
            ''', (razon_social, rif, direccion, telefono, cliente_id))
            conexion.commit()
            conexion.close()
            return True, "Cliente actualizado con éxito."
        except sqlite3.IntegrityError:
            return False, "Error: El RIF ya está registrado en otro cliente."
        except Exception as e:
            return False, f"Error inesperado: {e}"

    def eliminar_cliente(self, cliente_id):
        """Elimina un cliente por su ID."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            conexion.commit()
            conexion.close()
            return True, "Cliente eliminado correctamente."
        except Exception as e:
            return False, f"Error al eliminar: {e}"