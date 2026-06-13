from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView, QMenu)
from PyQt6.QtCore import Qt
from models.clientes_model import ClientesModel

class ViewClientes(QWidget):
    def __init__(self):
        super().__init__()
        self.modelo = ClientesModel()
        self.id_cliente_editando = None # Variable para saber si estamos guardando o editando
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)

        # --- PANEL IZQUIERDO: FORMULARIO ---
        panel_formulario = QVBoxLayout()
        titulo = QLabel("<b>Registro de Clientes</b>")
        panel_formulario.addWidget(titulo)

        self.input_razon = QLineEdit()
        self.input_razon.setPlaceholderText("Razón Social (Ej: Importaciones C.A.)")
        panel_formulario.addWidget(self.input_razon)

        self.input_rif = QLineEdit()
        self.input_rif.setPlaceholderText("RIF (Ej: J-12345678-9)")
        panel_formulario.addWidget(self.input_rif)

        self.input_direccion = QLineEdit()
        self.input_direccion.setPlaceholderText("Dirección Fiscal")
        panel_formulario.addWidget(self.input_direccion)

        self.input_telefono = QLineEdit()
        self.input_telefono.setPlaceholderText("Teléfono de Contacto")
        panel_formulario.addWidget(self.input_telefono)

        self.btn_guardar = QPushButton("💾 Guardar Cliente")
        self.btn_guardar.setStyleSheet("background-color: #2E86C1; color: white; padding: 8px;")
        self.btn_guardar.clicked.connect(self.procesar_formulario)
        panel_formulario.addWidget(self.btn_guardar)

        # Botón para cancelar edición (oculto por defecto)
        self.btn_cancelar = QPushButton("❌ Cancelar Edición")
        self.btn_cancelar.setStyleSheet("background-color: #7F8C8D; color: white; padding: 8px;")
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)
        self.btn_cancelar.hide()
        panel_formulario.addWidget(self.btn_cancelar)

        panel_formulario.addStretch() 

        # --- PANEL DERECHO: TABLA ---
        self.tabla_clientes = QTableWidget()
        self.tabla_clientes.setColumnCount(5)
        self.tabla_clientes.setHorizontalHeaderLabels(["ID", "Razón Social", "RIF", "Dirección", "Teléfono"])
        self.tabla_clientes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_clientes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Seleccionar fila completa
        self.tabla_clientes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Evitar que editen escribiendo directo en la tabla

        # Activar el menú de clic derecho
        self.tabla_clientes.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_clientes.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        layout_principal.addLayout(panel_formulario, stretch=1)
        layout_principal.addWidget(self.tabla_clientes, stretch=3)

    def mostrar_menu_contextual(self, posicion):
        """Muestra el menú de Editar/Eliminar al hacer clic derecho en la tabla."""
        fila_seleccionada = self.tabla_clientes.rowAt(posicion.y())
        if fila_seleccionada >= 0:
            menu = QMenu()
            accion_editar = menu.addAction("✏️ Editar Cliente")
            accion_eliminar = menu.addAction("🗑️ Eliminar Cliente")

            accion = menu.exec(self.tabla_clientes.viewport().mapToGlobal(posicion))
            
            id_cliente = self.tabla_clientes.item(fila_seleccionada, 0).text()

            if accion == accion_editar:
                self.preparar_edicion(fila_seleccionada)
            elif accion == accion_eliminar:
                self.eliminar_cliente(id_cliente)

    def preparar_edicion(self, fila):
        """Carga los datos de la tabla al formulario izquierdo."""
        self.id_cliente_editando = self.tabla_clientes.item(fila, 0).text()
        self.input_razon.setText(self.tabla_clientes.item(fila, 1).text())
        self.input_rif.setText(self.tabla_clientes.item(fila, 2).text())
        
        # Manejar posibles valores nulos en dirección y teléfono
        dir_item = self.tabla_clientes.item(fila, 3)
        self.input_direccion.setText(dir_item.text() if dir_item and dir_item.text() != "None" else "")
        
        tel_item = self.tabla_clientes.item(fila, 4)
        self.input_telefono.setText(tel_item.text() if tel_item and tel_item.text() != "None" else "")

        # Cambiar el aspecto del botón
        self.btn_guardar.setText("🔄 Actualizar Cliente")
        self.btn_guardar.setStyleSheet("background-color: #D35400; color: white; padding: 8px;")
        self.btn_cancelar.show()

    def eliminar_cliente(self, id_cliente):
        respuesta = QMessageBox.question(self, "Confirmar", "¿Seguro que deseas eliminar este cliente?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, mensaje = self.modelo.eliminar_cliente(id_cliente)
            if exito:
                self.cargar_datos()
                self.limpiar_formulario()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def procesar_formulario(self):
        razon = self.input_razon.text().strip()
        rif = self.input_rif.text().strip().upper()
        dir = self.input_direccion.text().strip()
        tel = self.input_telefono.text().strip()

        if not razon or not rif:
            QMessageBox.warning(self, "Advertencia", "La Razón Social y el RIF son obligatorios.")
            return

        # Si hay un ID guardado, significa que estamos editando. Si no, estamos creando.
        if self.id_cliente_editando:
            exito, mensaje = self.modelo.actualizar_cliente(self.id_cliente_editando, razon, rif, dir, tel)
        else:
            exito, mensaje = self.modelo.agregar_cliente(razon, rif, dir, tel)
        
        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
            self.limpiar_formulario()
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def limpiar_formulario(self):
        self.input_razon.clear()
        self.input_rif.clear()
        self.input_direccion.clear()
        self.input_telefono.clear()
        self.id_cliente_editando = None
        self.btn_guardar.setText("💾 Guardar Cliente")
        self.btn_guardar.setStyleSheet("background-color: #2E86C1; color: white; padding: 8px;")
        self.btn_cancelar.hide()

    def cargar_datos(self):
        self.tabla_clientes.setRowCount(0)
        clientes = self.modelo.obtener_clientes()
        
        for fila_idx, datos_fila in enumerate(clientes):
            self.tabla_clientes.insertRow(fila_idx)
            for col_idx, dato in enumerate(datos_fila):
                self.tabla_clientes.setItem(fila_idx, col_idx, QTableWidgetItem(str(dato)))