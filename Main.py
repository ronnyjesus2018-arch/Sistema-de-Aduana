import sys
import sqlite3
import shutil
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QFileDialog, QMessageBox)
from PyQt6.QtGui import QAction
from ui.views.view_clientes import ViewClientes
from ui.views.view_conceptos import ViewConceptos
from ui.views.view_facturas import ViewFacturas
from ui.views.view_expedientes import ViewExpedientes
from ui.views.view_conciliacion import ViewConciliacion
from ui.views.view_reportes import ViewReportes

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Conciliación y Facturación Aduanera")
        self.setGeometry(100, 100, 1024, 600)

        self.inicializar_db()
        self.crear_menu_superior()

        # Crear el sistema de pestañas
        pestañas = QTabWidget()
        self.vista_clientes = ViewClientes()
        self.vista_conceptos = ViewConceptos()
        self.vista_expedientes = ViewExpedientes()
        pestañas.addTab(self.vista_expedientes, "📁 Expedientes")
        self.vista_conciliacion = ViewConciliacion()
        pestañas.addTab(self.vista_conciliacion, "⚖️ Conciliación")
        pestañas.addTab(self.vista_clientes, "👥 Clientes")
        pestañas.addTab(self.vista_conceptos, "📋 Conceptos Facturables")
        self.setCentralWidget(pestañas)
        self.vista_facturas = ViewFacturas()
        pestañas.addTab(self.vista_facturas, "📄 Facturación")
        self.vista_reportes = ViewReportes()
        pestañas.addTab(self.vista_reportes, "📊 Dashboard")

    def inicializar_db(self):
        conexion = sqlite3.connect("datos_aduaneros.db")
        cursor = conexion.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                razon_social TEXT NOT NULL,
                rif TEXT UNIQUE NOT NULL,
                direccion TEXT,
                telefono TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conceptos_facturables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                tipo TEXT NOT NULL,
                aplica_iva BOOLEAN NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT NOT NULL,
                numero_control TEXT,
                cliente_id INTEGER,
                fecha_emision TEXT,
                estado TEXT,
                subtotal REAL,
                porcentaje_iva REAL DEFAULT 16.0,
                monto_iva REAL,
                total REAL,
                observaciones TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_factura (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura_id INTEGER,
                concepto_id INTEGER,
                descripcion_manual TEXT,
                cantidad REAL,
                precio_unitario REAL,
                aplica_iva BOOLEAN,
                subtotal_linea REAL,
                FOREIGN KEY(factura_id) REFERENCES facturas(id) ON DELETE CASCADE
            )
        ''')
        # NUEVA TABLA: HISTORIAL DE PAGOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagos_facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura_id INTEGER,
                fecha_pago TEXT NOT NULL,
                monto REAL NOT NULL,
                metodo_pago TEXT,
                referencia TEXT,
                FOREIGN KEY(factura_id) REFERENCES facturas(id) ON DELETE CASCADE
            )
        ''')
        # NUEVA TABLA DE EXPEDIENTES / OPERACIONES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expedientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_expediente TEXT UNIQUE NOT NULL,
                cliente_id INTEGER,
                tipo_operacion TEXT,
                aduana TEXT,
                bl_guia TEXT,
                contenedores TEXT,
                mercancia TEXT,
                fecha_apertura TEXT,
                estado TEXT DEFAULT 'ABIERTO',
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        ''')
        # NUEVA TABLA: TRANSACCIONES (Anticipos vs Gastos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transacciones_expediente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expediente_id INTEGER,
                tipo TEXT NOT NULL,       -- 'ANTICIPO' o 'GASTO'
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY(expediente_id) REFERENCES expedientes(id) ON DELETE CASCADE
            )
        ''')
        conexion.commit()
        conexion.close()

    def crear_menu_superior(self):
        menu_bar = self.menuBar()
        menu_archivo = menu_bar.addMenu("📁 Archivo (Respaldos)")

        accion_respaldo = QAction("💾 Crear Copia de Seguridad", self)
        accion_respaldo.triggered.connect(self.crear_respaldo)
        menu_archivo.addAction(accion_respaldo)

        accion_restaurar = QAction("♻️ Restaurar desde Respaldo", self)
        accion_restaurar.triggered.connect(self.restaurar_respaldo)
        menu_archivo.addAction(accion_restaurar)

    def crear_respaldo(self):
        ruta_destino, _ = QFileDialog.getSaveFileName(
            self, "Guardar Respaldo", "Respaldo_Aduana.db", "Base de Datos SQLite (*.db)"
        )
        if ruta_destino:
            try:
                shutil.copy2("datos_aduaneros.db", ruta_destino)
                QMessageBox.information(self, "Éxito", "Copia de seguridad creada correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el respaldo:\n{e}")

    def restaurar_respaldo(self):
        ruta_origen, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Respaldo a Cargar", "", "Base de Datos SQLite (*.db)"
        )
        if ruta_origen:
            respuesta = QMessageBox.question(
                self, "Confirmar Restauración", 
                "⚠️ ¿Estás seguro? Esto reemplazará todos los datos actuales con los del respaldo.", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.Yes:
                try:
                    shutil.copy2(ruta_origen, "datos_aduaneros.db")
                    QMessageBox.information(self, "Éxito", "Sistema restaurado. Por favor, cierra y vuelve a abrir el programa para ver los cambios.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo restaurar:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())