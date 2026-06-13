from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, QMenu)
from PyQt6.QtCore import Qt
from models.expedientes_model import ExpedientesModel

class ViewExpedientes(QWidget):
    def __init__(self):
        super().__init__()
        self.modelo = ExpedientesModel()
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)

        # --- PANEL IZQUIERDO: FORMULARIO ---
        panel_formulario = QVBoxLayout()
        panel_formulario.addWidget(QLabel("<b>Registro de Expediente</b>"))

        self.input_numero = QLineEdit()
        self.input_numero.setPlaceholderText("Nº Expediente (Ej: EXP-2026-001)")
        panel_formulario.addWidget(self.input_numero)

        self.combo_cliente = QComboBox()
        self.cargar_clientes()
        panel_formulario.addWidget(QLabel("Cliente:"))
        panel_formulario.addWidget(self.combo_cliente)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Importación", "Exportación", "Tránsito"])
        panel_formulario.addWidget(QLabel("Tipo de Operación:"))
        panel_formulario.addWidget(self.combo_tipo)

        self.input_aduana = QLineEdit()
        self.input_aduana.setPlaceholderText("Aduana (Ej: Marítima de La Guaira)")
        panel_formulario.addWidget(self.input_aduana)

        self.input_bl = QLineEdit()
        self.input_bl.setPlaceholderText("BL / Guía Aérea")
        panel_formulario.addWidget(self.input_bl)

        self.input_contenedores = QLineEdit()
        self.input_contenedores.setPlaceholderText("Contenedores (Ej: HLXU1234567)")
        panel_formulario.addWidget(self.input_contenedores)

        self.input_mercancia = QLineEdit()
        self.input_mercancia.setPlaceholderText("Descripción de Mercancía")
        panel_formulario.addWidget(self.input_mercancia)

        self.btn_guardar = QPushButton("💾 Registrar Expediente")
        self.btn_guardar.setStyleSheet("background-color: #2E86C1; color: white; padding: 8px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar_expediente)
        panel_formulario.addWidget(self.btn_guardar)

        panel_formulario.addStretch()
        layout_principal.addLayout(panel_formulario, 1)

        # --- PANEL DERECHO: TABLA ---
        self.tabla_expedientes = QTableWidget()
        self.tabla_expedientes.setColumnCount(8)
        self.tabla_expedientes.setHorizontalHeaderLabels(
            ["ID", "Expediente", "Cliente", "Tipo", "Aduana", "BL/Guía", "Estado", "Fecha"]
        )
        self.tabla_expedientes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_expedientes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_expedientes.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_expedientes.customContextMenuRequested.connect(self.mostrar_menu_contextual)
        
        layout_principal.addWidget(self.tabla_expedientes, 3)

    def cargar_clientes(self):
        self.combo_cliente.clear()
        for cliente in self.modelo.obtener_clientes_combo():
            self.combo_cliente.addItem(cliente[1], userData=cliente[0]) # Texto, Dato oculto(ID)

    def guardar_expediente(self):
        numero = self.input_numero.text().strip()
        cliente_id = self.combo_cliente.currentData()
        tipo = self.combo_tipo.currentText()
        aduana = self.input_aduana.text().strip()
        bl = self.input_bl.text().strip()
        contenedores = self.input_contenedores.text().strip()
        mercancia = self.input_mercancia.text().strip()

        if not numero or not aduana or not cliente_id:
            QMessageBox.warning(self, "Aviso", "Número de expediente, Cliente y Aduana son obligatorios.")
            return

        exito, msj = self.modelo.agregar_expediente(numero, cliente_id, tipo, aduana, bl, contenedores, mercancia)
        
        if exito:
            QMessageBox.information(self, "Éxito", msj)
            self.limpiar_form()
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", msj)

    def limpiar_form(self):
        self.input_numero.clear()
        self.input_aduana.clear()
        self.input_bl.clear()
        self.input_contenedores.clear()
        self.input_mercancia.clear()

    def cargar_datos(self):
        self.tabla_expedientes.setRowCount(0)
        for fila_idx, datos in enumerate(self.modelo.obtener_expedientes()):
            self.tabla_expedientes.insertRow(fila_idx)
            for col_idx, valor in enumerate(datos):
                self.tabla_expedientes.setItem(fila_idx, col_idx, QTableWidgetItem(str(valor)))

    def mostrar_menu_contextual(self, posicion):
        menu = QMenu()
        accion_eliminar = menu.addAction("🗑️ Eliminar")
        accion = menu.exec(self.tabla_expedientes.viewport().mapToGlobal(posicion))
        
        if accion == accion_eliminar:
            fila = self.tabla_expedientes.currentRow()
            exp_id = self.tabla_expedientes.item(fila, 0).text()
            if QMessageBox.question(self, "Eliminar", "¿Seguro que deseas eliminar este expediente?") == QMessageBox.StandardButton.Yes:
                self.modelo.eliminar_expediente(exp_id)
                self.cargar_datos()