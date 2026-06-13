from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView, QComboBox, 
                             QDoubleSpinBox, QGroupBox, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from models.conciliacion_model import ConciliacionModel

class ViewConciliacion(QWidget):
    def __init__(self):
        super().__init__()
        self.modelo = ConciliacionModel()
        self.init_ui()
        self.cargar_expedientes()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)

        # --- PANEL SUPERIOR: SELECTOR Y RESUMEN ---
        panel_top = QGroupBox("Selección y Resumen del Expediente")
        layout_top = QHBoxLayout(panel_top)

        # Selector
        layout_selector = QVBoxLayout()
        layout_selector.addWidget(QLabel("Expediente a Conciliar:"))
        self.combo_expediente = QComboBox()
        self.combo_expediente.setMinimumWidth(200)
        self.combo_expediente.currentIndexChanged.connect(self.cargar_datos_expediente)
        layout_selector.addWidget(self.combo_expediente)
        layout_top.addLayout(layout_selector)

        layout_top.addStretch()

        # Etiquetas de Resumen
        fuente_resumen = "font-size: 16px; font-weight: bold; padding: 5px;"
        
        self.lbl_anticipos = QLabel("Anticipos Recibidos: $ 0.00")
        self.lbl_anticipos.setStyleSheet(f"{fuente_resumen} color: #2E86C1;")
        layout_top.addWidget(self.lbl_anticipos)

        self.lbl_gastos = QLabel("Gastos Reales: $ 0.00")
        self.lbl_gastos.setStyleSheet(f"{fuente_resumen} color: #E74C3C;")
        layout_top.addWidget(self.lbl_gastos)

        self.lbl_saldo = QLabel("Saldo: $ 0.00")
        self.lbl_saldo.setStyleSheet(f"{fuente_resumen} color: #27AE60; background-color: #EAEDED; border-radius: 5px;")
        layout_top.addWidget(self.lbl_saldo)

        layout_principal.addWidget(panel_top)

        # --- PANEL INFERIOR: FORMULARIO Y TABLA ---
        panel_bottom = QHBoxLayout()

        # Formulario (Izquierda)
        form_layout = QVBoxLayout()
        
        form_layout.addWidget(QLabel("Tipo de Transacción:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["ANTICIPO", "GASTO"])
        form_layout.addWidget(self.combo_tipo)

        form_layout.addWidget(QLabel("Descripción / Concepto:"))
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Ej: Pago SENIAT / Anticipo Inicial")
        form_layout.addWidget(self.input_desc)

        form_layout.addWidget(QLabel("Monto ($):"))
        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, 9999999.99)
        self.spin_monto.setDecimals(2)
        form_layout.addWidget(self.spin_monto)

        self.btn_guardar = QPushButton("💾 Registrar Transacción")
        self.btn_guardar.setStyleSheet("background-color: #2E86C1; color: white; padding: 8px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.registrar_transaccion)
        form_layout.addWidget(self.btn_guardar)

        form_layout.addStretch()
        panel_bottom.addLayout(form_layout, 1)

        # Tabla (Derecha)
        self.tabla_transacciones = QTableWidget()
        self.tabla_transacciones.setColumnCount(5)
        self.tabla_transacciones.setHorizontalHeaderLabels(["ID", "Fecha", "Tipo", "Descripción", "Monto"])
        self.tabla_transacciones.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_transacciones.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_transacciones.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_transacciones.setColumnHidden(0, True)

        # Menú contextual (Clic derecho para eliminar)
        self.tabla_transacciones.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_transacciones.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        panel_bottom.addWidget(self.tabla_transacciones, 3)

        layout_principal.addLayout(panel_bottom)

    def cargar_expedientes(self):
        self.combo_expediente.clear()
        for exp in self.modelo.obtener_expedientes_combo():
            self.combo_expediente.addItem(exp[1], userData=exp[0])

    def cargar_datos_expediente(self):
        exp_id = self.combo_expediente.currentData()
        if not exp_id: return

        # 1. Actualizar Resumen
        anticipos, gastos, saldo = self.modelo.obtener_resumen(exp_id)
        self.lbl_anticipos.setText(f"Anticipos Recibidos: $ {anticipos:,.2f}")
        self.lbl_gastos.setText(f"Gastos Reales: $ {gastos:,.2f}")
        
        texto_saldo = f"Saldo a Favor Cliente: $ {saldo:,.2f}" if saldo >= 0 else f"Saldo Pendiente por Cobrar: $ {abs(saldo):,.2f}"
        color_saldo = "#27AE60" if saldo >= 0 else "#C0392B" # Verde si sobra, Rojo si falta
        self.lbl_saldo.setText(texto_saldo)
        self.lbl_saldo.setStyleSheet(f"font-size: 16px; font-weight: bold; padding: 5px; color: {color_saldo}; background-color: #EAEDED;")

        # 2. Actualizar Tabla
        self.tabla_transacciones.setRowCount(0)
        for fila_idx, datos in enumerate(self.modelo.obtener_transacciones(exp_id)):
            self.tabla_transacciones.insertRow(fila_idx)
            # datos: id, fecha, tipo, descripcion, monto
            self.tabla_transacciones.setItem(fila_idx, 0, QTableWidgetItem(str(datos[0])))
            self.tabla_transacciones.setItem(fila_idx, 1, QTableWidgetItem(datos[1]))
            
            item_tipo = QTableWidgetItem(datos[2])
            item_tipo.setForeground(QColor("#2E86C1") if datos[2] == "ANTICIPO" else QColor("#E74C3C"))
            item_tipo.setFont(QFont("", -1, QFont.Weight.Bold))
            self.tabla_transacciones.setItem(fila_idx, 2, item_tipo)
            
            self.tabla_transacciones.setItem(fila_idx, 3, QTableWidgetItem(datos[3]))
            self.tabla_transacciones.setItem(fila_idx, 4, QTableWidgetItem(f"$ {datos[4]:,.2f}"))

    def registrar_transaccion(self):
        exp_id = self.combo_expediente.currentData()
        if not exp_id:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un expediente.")
            return

        tipo = self.combo_tipo.currentText()
        desc = self.input_desc.text().strip()
        monto = self.spin_monto.value()

        if not desc:
            QMessageBox.warning(self, "Aviso", "La descripción es obligatoria.")
            return

        exito, msj = self.modelo.registrar_transaccion(exp_id, tipo, desc, monto)
        if exito:
            self.input_desc.clear()
            self.spin_monto.setValue(0.01)
            self.cargar_datos_expediente() # Refresca tabla y totales
        else:
            QMessageBox.critical(self, "Error", msj)

    def mostrar_menu_contextual(self, posicion):
        menu = QMenu()
        accion_eliminar = menu.addAction("🗑️ Eliminar Transacción")
        accion = menu.exec(self.tabla_transacciones.viewport().mapToGlobal(posicion))
        
        if accion == accion_eliminar:
            fila = self.tabla_transacciones.currentRow()
            t_id = self.tabla_transacciones.item(fila, 0).text()
            if QMessageBox.question(self, "Eliminar", "¿Seguro que deseas eliminar este registro?") == QMessageBox.StandardButton.Yes:
                self.modelo.eliminar_transaccion(t_id)
                self.cargar_datos_expediente()