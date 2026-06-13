import sqlite3
from datetime import datetime

class FacturasModel:
    def __init__(self, db_path="datos_aduaneros.db"):
        self.db_path = db_path

    def conectar(self):
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    # =============================================
    #  GENERACIÓN DE NÚMEROS CORRELATIVOS
    # =============================================

    def generar_numero(self, prefijo):
        """Genera el siguiente número correlativo para facturas o pre-facturas.
        Prefijo: 'PRE' para pre-facturas, 'FAC' para facturas.
        Formato: PRE-00001 o FAC-00001
        """
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT numero_factura FROM facturas WHERE numero_factura LIKE ? ORDER BY id DESC LIMIT 1",
            (f"{prefijo}-%",)
        )
        ultimo = cursor.fetchone()
        conexion.close()

        if ultimo:
            try:
                ultimo_num = int(ultimo[0].split("-")[1])
                siguiente = ultimo_num + 1
            except (ValueError, IndexError):
                siguiente = 1
        else:
            siguiente = 1

        return f"{prefijo}-{siguiente:05d}"

    # =============================================
    #  CRUD DE FACTURAS (ENCABEZADO)
    # =============================================

    def crear_factura(self, cliente_id, fecha_emision, observaciones="", numero_control=""):
        try:
            numero = self.generar_numero("PRE")
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute('''
                INSERT INTO facturas (numero_factura, cliente_id, fecha_emision, estado, 
                                      subtotal, porcentaje_iva, monto_iva, total, observaciones, numero_control)
                VALUES (?, ?, ?, 'PRE-FACTURA', 0, 16.0, 0, 0, ?, ?)
            ''', (numero, cliente_id, fecha_emision, observaciones, numero_control))
            factura_id = cursor.lastrowid
            conexion.commit()
            conexion.close()
            return True, factura_id, f"Pre-factura {numero} creada con éxito."
        except Exception as e:
            return False, None, f"Error al crear pre-factura: {e}"

    def obtener_facturas(self, filtro_estado=None):
        """Retorna todas las facturas con el nombre del cliente.
        Si se pasa filtro_estado, filtra por 'PRE-FACTURA' o 'FACTURADA'.
        """
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        query = '''
            SELECT f.id, f.numero_factura, c.razon_social, f.fecha_emision, 
                   f.estado, f.subtotal, f.monto_iva, f.total, f.observaciones, f.numero_control
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
        '''
        params = ()
        if filtro_estado:
            query += " WHERE f.estado = ?"
            params = (filtro_estado,)
        
        query += " ORDER BY f.id DESC"
        
        cursor.execute(query, params)
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def obtener_factura_por_id(self, factura_id):
        """Retorna los datos completos de una factura por su ID."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT f.id, f.numero_factura, f.cliente_id, c.razon_social, f.fecha_emision, 
                   f.estado, f.subtotal, f.monto_iva, f.total, f.observaciones, f.numero_control
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = ?
        ''', (factura_id,))
        fila = cursor.fetchone()
        conexion.close()
        return fila

    def actualizar_factura(self, factura_id, cliente_id, observaciones, numero_control=""):
        """Actualiza los datos del encabezado de una pre-factura."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            # Verificar que sea PRE-FACTURA
            cursor.execute("SELECT estado FROM facturas WHERE id = ?", (factura_id,))
            estado = cursor.fetchone()
            if not estado or estado[0] != "PRE-FACTURA":
                conexion.close()
                return False, "Solo se pueden editar pre-facturas."
            
            cursor.execute('''
                UPDATE facturas 
                SET cliente_id = ?, observaciones = ?, numero_control = ?
                WHERE id = ?
            ''', (cliente_id, observaciones, numero_control, factura_id))
            conexion.commit()
            conexion.close()
            return True, "Pre-factura actualizada con éxito."
        except Exception as e:
            return False, f"Error al actualizar: {e}"

    def eliminar_factura(self, factura_id):
        """Elimina una factura (solo si es PRE-FACTURA). El CASCADE borra el detalle."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("SELECT estado, numero_factura FROM facturas WHERE id = ?", (factura_id,))
            resultado = cursor.fetchone()
            if not resultado:
                conexion.close()
                return False, "Factura no encontrada."
            if resultado[0] != "PRE-FACTURA":
                conexion.close()
                return False, "No se pueden eliminar facturas definitivas. Solo pre-facturas."
            
            cursor.execute("DELETE FROM facturas WHERE id = ?", (factura_id,))
            conexion.commit()
            conexion.close()
            return True, f"Pre-factura {resultado[1]} eliminada correctamente."
        except Exception as e:
            return False, f"Error al eliminar: {e}"

    def convertir_a_factura(self, factura_id):
        """Convierte una PRE-FACTURA en FACTURADA, asignando nuevo número FAC-XXXXX."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            cursor.execute("SELECT estado FROM facturas WHERE id = ?", (factura_id,))
            estado = cursor.fetchone()
            if not estado or estado[0] != "PRE-FACTURA":
                conexion.close()
                return False, "Solo se pueden convertir pre-facturas."

            # Verificar que tenga al menos una línea de detalle
            cursor.execute("SELECT COUNT(*) FROM detalle_factura WHERE factura_id = ?", (factura_id,))
            cant_lineas = cursor.fetchone()[0]
            if cant_lineas == 0:
                conexion.close()
                return False, "No se puede facturar sin líneas de detalle."

            nuevo_numero = self.generar_numero("FAC")
            cursor.execute('''
                UPDATE facturas 
                SET estado = 'FACTURADA', numero_factura = ?
                WHERE id = ?
            ''', (nuevo_numero, factura_id))
            conexion.commit()
            conexion.close()
            return True, f"Convertida a factura definitiva: {nuevo_numero}"
        except Exception as e:
            return False, f"Error al convertir: {e}"

    # =============================================
    #  CRUD DE LÍNEAS DE DETALLE
    # =============================================

    def agregar_linea(self, factura_id, concepto_id, descripcion_manual, cantidad, precio_unitario, aplica_iva):
        """Inserta una línea de detalle y recalcula los totales de la factura."""
        try:
            subtotal_linea = round(cantidad * precio_unitario, 2)
            conexion = self.conectar()
            cursor = conexion.cursor()
            
            # Verificar que la factura sea editable
            cursor.execute("SELECT estado FROM facturas WHERE id = ?", (factura_id,))
            estado = cursor.fetchone()
            if not estado or estado[0] != "PRE-FACTURA":
                conexion.close()
                return False, "Solo se pueden agregar líneas a pre-facturas."

            cursor.execute('''
                INSERT INTO detalle_factura (factura_id, concepto_id, descripcion_manual, 
                                             cantidad, precio_unitario, aplica_iva, subtotal_linea)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (factura_id, concepto_id, descripcion_manual, cantidad, precio_unitario, 
                  1 if aplica_iva else 0, subtotal_linea))
            conexion.commit()
            conexion.close()
            
            self.recalcular_totales(factura_id)
            return True, "Línea agregada con éxito."
        except Exception as e:
            return False, f"Error al agregar línea: {e}"

    def obtener_detalle(self, factura_id):
        """Retorna las líneas de detalle de una factura."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT d.id, cf.descripcion, d.descripcion_manual, d.cantidad, 
                   d.precio_unitario, d.aplica_iva, d.subtotal_linea, d.concepto_id
            FROM detalle_factura d
            JOIN conceptos_facturables cf ON d.concepto_id = cf.id
            WHERE d.factura_id = ?
            ORDER BY d.id
        ''', (factura_id,))
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def eliminar_linea(self, linea_id, factura_id):
        """Elimina una línea de detalle y recalcula totales."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            
            # Verificar que la factura sea editable
            cursor.execute("SELECT estado FROM facturas WHERE id = ?", (factura_id,))
            estado = cursor.fetchone()
            if not estado or estado[0] != "PRE-FACTURA":
                conexion.close()
                return False, "Solo se pueden modificar pre-facturas."

            cursor.execute("DELETE FROM detalle_factura WHERE id = ?", (linea_id,))
            conexion.commit()
            conexion.close()
            
            self.recalcular_totales(factura_id)
            return True, "Línea eliminada."
        except Exception as e:
            return False, f"Error al eliminar línea: {e}"

    def recalcular_totales(self, factura_id):
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            
            # Obtener el porcentaje de IVA actual de esta factura
            cursor.execute("SELECT porcentaje_iva FROM facturas WHERE id = ?", (factura_id,))
            porcentaje_iva = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(subtotal_linea), 0) FROM detalle_factura WHERE factura_id = ?", (factura_id,))
            subtotal = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(subtotal_linea), 0) FROM detalle_factura WHERE factura_id = ? AND aplica_iva = 1", (factura_id,))
            base_iva = cursor.fetchone()[0]
            
            # Calculamos con el IVA dinámico
            monto_iva = round(base_iva * (porcentaje_iva / 100.0), 2)
            total = round(subtotal + monto_iva, 2)
            
            cursor.execute('''
                UPDATE facturas SET subtotal = ?, monto_iva = ?, total = ? WHERE id = ?
            ''', (subtotal, monto_iva, total, factura_id))
            conexion.commit()
            conexion.close()
            return True
        except Exception as e:
            return False

    # =============================================
    #  UTILIDADES
    # =============================================

    def obtener_clientes_para_combo(self):
        """Retorna lista de (id, razon_social + RIF) para poblar un combo box."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, razon_social, rif FROM clientes ORDER BY razon_social")
        filas = cursor.fetchall()
        conexion.close()
        return [(f[0], f"{f[1]} ({f[2]})") for f in filas]

    def obtener_conceptos_para_combo(self):
        """Retorna lista de (id, descripcion, tipo, aplica_iva) para selección de conceptos."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, descripcion, tipo, aplica_iva FROM conceptos_facturables ORDER BY descripcion")
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def actualizar_porcentaje_iva(self, factura_id, nuevo_porcentaje):
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute("UPDATE facturas SET porcentaje_iva = ? WHERE id = ?", (nuevo_porcentaje, factura_id))
        conexion.commit()
        conexion.close()
        self.recalcular_totales(factura_id)
        return True
    
    # =============================================
    #  CONTROL DE PAGOS Y SALDOS
    # =============================================

    def registrar_pago(self, factura_id, monto, metodo_pago, referencia):
        """Registra un abono a una factura definitiva."""
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute('''
                INSERT INTO pagos_facturas (factura_id, fecha_pago, monto, metodo_pago, referencia)
                VALUES (?, ?, ?, ?, ?)
            ''', (factura_id, fecha, monto, metodo_pago, referencia))
            conexion.commit()
            conexion.close()
            return True, "Pago registrado exitosamente."
        except Exception as e:
            return False, f"Error al registrar pago: {e}"

    def obtener_pagos(self, factura_id):
        """Devuelve el historial de pagos de una factura."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        cursor.execute('''
            SELECT fecha_pago, monto, metodo_pago, referencia 
            FROM pagos_facturas WHERE factura_id = ? ORDER BY id ASC
        ''', (factura_id,))
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def obtener_saldo_pendiente(self, factura_id):
        """Calcula cuánto falta por pagar de la factura."""
        conexion = self.conectar()
        cursor = conexion.cursor()
        
        # Obtener Total de la Factura
        cursor.execute("SELECT total FROM facturas WHERE id = ?", (factura_id,))
        resultado_total = cursor.fetchone()
        total_factura = resultado_total[0] if resultado_total else 0

        # Obtener Total Pagado
        cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM pagos_facturas WHERE factura_id = ?", (factura_id,))
        total_pagado = cursor.fetchone()[0]
        
        conexion.close()
        return total_factura, total_pagado, round(total_factura - total_pagado, 2)