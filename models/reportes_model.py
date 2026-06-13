import sqlite3

class ReportesModel:
    def __init__(self, db_path="datos_aduaneros.db"):
        self.db_path = db_path

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def obtener_metricas_dashboard(self):
        """Devuelve las métricas clave para el panel principal."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        # Total de clientes
        cursor.execute("SELECT COUNT(*) FROM clientes")
        clientes = cursor.fetchone()[0]
        
        # Expedientes Abiertos
        cursor.execute("SELECT COUNT(*) FROM expedientes WHERE estado = 'ABIERTO'")
        expedientes_abiertos = cursor.fetchone()[0]
        
        # Facturación Total (Facturas definitivas)
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM facturas WHERE estado = 'FACTURADA'")
        total_facturado = cursor.fetchone()[0]
        
        # Total de Gastos Reales (De la conciliación)
        cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM transacciones_expediente WHERE tipo = 'GASTO'")
        total_gastos = cursor.fetchone()[0]
        
        conexion.close()
        return clientes, expedientes_abiertos, total_facturado, total_gastos

    def obtener_datos_facturacion(self):
        """Obtiene todas las facturas para exportarlas a Excel."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT f.numero_factura, c.razon_social, f.fecha_emision, f.estado, f.subtotal, f.total 
            FROM facturas f JOIN clientes c ON f.cliente_id = c.id
        ''')
        columnas = [desc[0] for desc in cursor.description]
        filas = cursor.fetchall()
        conexion.close()
        return columnas, filas