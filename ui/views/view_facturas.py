from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView,
                             QComboBox, QMenu, QTextEdit, QDoubleSpinBox,
                             QSpinBox, QGroupBox, QSplitter, QFrame,
                             QCheckBox, QInputDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from models.facturas_model import FacturasModel
from datetime import datetime
from PyQt6.QtGui import QTextDocument, QPdfWriter
from PyQt6.QtWidgets import QFileDialog

class ViewFacturas(QWidget):
    def __init__(self):
        super().__init__()
        self.modelo = FacturasModel()
        self.factura_actual_id = None  # ID de la factura que se está editando/viendo
        self.modo_edicion = False
        self.init_ui()
        self.cargar_lista_facturas()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)

        # Usamos un QSplitter para dividir la pantalla arriba/abajo
        splitter = QSplitter(Qt.Orientation.Vertical)

        # ============================================================
        #  PANEL SUPERIOR: LISTA DE FACTURAS
        # ============================================================
        panel_superior = QWidget()
        layout_superior = QVBoxLayout(panel_superior)

        # Barra de herramientas
        barra_herramientas = QHBoxLayout()

        titulo = QLabel("<b style='font-size: 14px;'>📄 Facturas y Pre-facturas</b>")
        barra_herramientas.addWidget(titulo)

        barra_herramientas.addStretch()

        # Filtro por estado
        lbl_filtro = QLabel("Filtrar:")
        barra_herramientas.addWidget(lbl_filtro)

        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Todas", "Pre-facturas", "Facturadas"])
        self.combo_filtro.currentIndexChanged.connect(self.cargar_lista_facturas)
        self.combo_filtro.setMinimumWidth(140)
        barra_herramientas.addWidget(self.combo_filtro)

        # Botón nueva pre-factura
        self.btn_nueva = QPushButton("➕ Nueva Pre-factura")
        self.btn_nueva.setStyleSheet("background-color: #2E86C1; color: white; padding: 8px 16px; font-weight: bold;")
        self.btn_nueva.clicked.connect(self.nueva_prefactura)
        barra_herramientas.addWidget(self.btn_nueva)

        layout_superior.addLayout(barra_herramientas)

        # Tabla de facturas
        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.setColumnCount(8)
        self.tabla_facturas.setHorizontalHeaderLabels([
            "ID", "Nº Documento", "Cliente", "Fecha", "Estado", "Subtotal", "IVA", "Total"
        ])
        self.tabla_facturas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_facturas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_facturas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_facturas.setColumnHidden(0, True)  # Ocultar columna ID

        # Menú contextual
        self.tabla_facturas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_facturas.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        # Doble clic para ver detalle
        self.tabla_facturas.doubleClicked.connect(self.ver_detalle_factura)

        layout_superior.addWidget(self.tabla_facturas)

        # ============================================================
        #  PANEL INFERIOR: DETALLE / FORMULARIO DE FACTURA
        # ============================================================
        self.panel_inferior = QWidget()
        layout_inferior = QVBoxLayout(self.panel_inferior)

        # --- Encabezado del detalle ---
        grupo_encabezado = QGroupBox("Datos de la Factura")
        layout_encabezado = QHBoxLayout(grupo_encabezado)

        # Columna 1: Cliente y Número
        col1 = QVBoxLayout()
        
        lbl_numero = QLabel("Nº Documento:")
        col1.addWidget(lbl_numero)
        self.lbl_numero_valor = QLabel("<b>---</b>")
        self.lbl_numero_valor.setStyleSheet("font-size: 16px; color: #2E86C1;")
        col1.addWidget(self.lbl_numero_valor)

        lbl_estado = QLabel("Estado:")
        col1.addWidget(lbl_estado)
        self.lbl_estado_valor = QLabel("---")
        self.lbl_estado_valor.setStyleSheet("font-size: 13px; font-weight: bold;")
        col1.addWidget(self.lbl_estado_valor)
        
        layout_encabezado.addLayout(col1)

        # Columna 2: Cliente
        col2 = QVBoxLayout()
        lbl_cliente = QLabel("Cliente:")
        col2.addWidget(lbl_cliente)
        self.combo_cliente = QComboBox()
        self.combo_cliente.setMinimumWidth(250)
        col2.addWidget(self.combo_cliente)

        lbl_fecha = QLabel("Fecha de Emisión:")
        col2.addWidget(lbl_fecha)
        self.lbl_fecha_valor = QLabel(datetime.now().strftime("%d/%m/%Y"))
        self.lbl_fecha_valor.setStyleSheet("font-size: 13px;")
        col2.addWidget(self.lbl_fecha_valor)
        
        layout_encabezado.addLayout(col2)

        # Columna 3: Control y Observaciones
        col3 = QVBoxLayout()
        lbl_control = QLabel("Nº de Control (opcional):")
        col3.addWidget(lbl_control)
        self.input_control = QLineEdit()
        self.input_control.setPlaceholderText("Ej: 00-00000001")
        col3.addWidget(self.input_control)

        lbl_obs = QLabel("Observaciones:")
        col3.addWidget(lbl_obs)
        self.input_observaciones = QLineEdit()
        self.input_observaciones.setPlaceholderText("Notas adicionales...")
        col3.addWidget(self.input_observaciones)
        
        layout_encabezado.addLayout(col3)
        layout_inferior.addWidget(grupo_encabezado)

        # --- Sección de agregar líneas ---
        grupo_agregar = QGroupBox("Agregar Línea de Detalle")
        layout_agregar = QHBoxLayout(grupo_agregar)

        # Selector de concepto
        self.combo_concepto = QComboBox()
        self.combo_concepto.setMinimumWidth(200)
        self.combo_concepto.currentIndexChanged.connect(self.concepto_seleccionado)
        layout_agregar.addWidget(QLabel("Concepto:"))
        layout_agregar.addWidget(self.combo_concepto)

        # Descripción editable
        self.input_desc_linea = QLineEdit()
        self.input_desc_linea.setPlaceholderText("Descripción")
        self.input_desc_linea.setMinimumWidth(150)
        layout_agregar.addWidget(self.input_desc_linea)

        # Cantidad
        self.spin_cantidad = QDoubleSpinBox()
        self.spin_cantidad.setMinimum(0.01)
        self.spin_cantidad.setMaximum(999999)
        self.spin_cantidad.setValue(1)
        self.spin_cantidad.setDecimals(2)
        layout_agregar.addWidget(QLabel("Cant:"))
        layout_agregar.addWidget(self.spin_cantidad)

        # Precio unitario
        self.spin_precio = QDoubleSpinBox()
        self.spin_precio.setMinimum(0.01)
        self.spin_precio.setMaximum(99999999)
        self.spin_precio.setDecimals(2)
        self.spin_precio.setPrefix("$ ")
        layout_agregar.addWidget(QLabel("Precio:"))
        layout_agregar.addWidget(self.spin_precio)

        # Checkbox IVA
        self.chk_iva_linea = QCheckBox("IVA")
        layout_agregar.addWidget(self.chk_iva_linea)

        # Botón agregar
        self.btn_agregar_linea = QPushButton("➕ Agregar")
        self.btn_agregar_linea.setStyleSheet("background-color: #27AE60; color: white; padding: 6px 12px;")
        self.btn_agregar_linea.clicked.connect(self.agregar_linea)
        layout_agregar.addWidget(self.btn_agregar_linea)

        layout_inferior.addWidget(grupo_agregar)

        # --- Tabla de detalle ---
        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(7)
        self.tabla_detalle.setHorizontalHeaderLabels([
            "ID", "Concepto", "Descripción", "Cantidad", "Precio Unit.", "IVA", "Subtotal"
        ])
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_detalle.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_detalle.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_detalle.setColumnHidden(0, True)  # Ocultar ID de línea

        # Menú contextual para eliminar líneas
        self.tabla_detalle.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_detalle.customContextMenuRequested.connect(self.menu_linea_detalle)

        layout_inferior.addWidget(self.tabla_detalle)

        # ==========================================
        # SECCIÓN DE TOTALES (REEMPLAZA TODO ESTO)
        # ==========================================
        layout_totales = QVBoxLayout()
        estilo_total = "font-size: 14px; font-weight: bold;"

        self.lbl_subtotal = QLabel("Subtotal: $ 0.00")
        self.lbl_subtotal.setStyleSheet(estilo_total)

        # --- NUEVO BLOQUE DE IVA DINÁMICO ---
        layout_iva = QHBoxLayout()
        self.lbl_iva = QLabel("IVA:")
        self.lbl_iva.setStyleSheet(estilo_total)
        
        self.spin_iva_factura = QDoubleSpinBox()
        self.spin_iva_factura.setSuffix(" %")
        self.spin_iva_factura.setValue(16.0)
        self.spin_iva_factura.setDecimals(1)
        self.spin_iva_factura.valueChanged.connect(self.cambiar_porcentaje_iva)
        
        self.lbl_monto_iva = QLabel("$ 0.00")
        self.lbl_monto_iva.setStyleSheet(estilo_total)
        
        layout_iva.addWidget(self.lbl_iva)
        layout_iva.addWidget(self.spin_iva_factura)
        layout_iva.addWidget(self.lbl_monto_iva)
        # ------------------------------------

        self.lbl_total = QLabel("TOTAL: $ 0.00")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #27AE60;")
        # --- NUEVO: CONTROL DE SALDO ---
        self.lbl_pagado = QLabel("Pagado: $ 0.00")
        self.lbl_pagado.setStyleSheet("font-size: 14px; font-weight: bold; color: #2980B9;")
        
        self.lbl_saldo_pendiente = QLabel("SALDO PENDIENTE: $ 0.00")
        self.lbl_saldo_pendiente.setStyleSheet("font-size: 16px; font-weight: bold; color: #C0392B;")
        
        layout_totales.addWidget(self.lbl_pagado)
        layout_totales.addWidget(self.lbl_saldo_pendiente)

        # Ahora sí, agregamos todo al layout en orden:
        layout_totales.addWidget(self.lbl_subtotal)
        layout_totales.addLayout(layout_iva)
        layout_totales.addWidget(self.lbl_total)

        # --- Botones de acción del formulario ---
        layout_acciones = QHBoxLayout()
        layout_acciones.addStretch()

        self.btn_guardar_factura = QPushButton("💾 Guardar Cambios")
        self.btn_guardar_factura.setStyleSheet("background-color: #2E86C1; color: white; padding: 8px 20px; font-weight: bold;")
        self.btn_guardar_factura.clicked.connect(self.guardar_cambios_encabezado)
        layout_acciones.addWidget(self.btn_guardar_factura)

        self.btn_convertir = QPushButton("✅ Convertir a Factura Definitiva")
        self.btn_convertir.setStyleSheet("background-color: #8E44AD; color: white; padding: 8px 20px; font-weight: bold;")
        self.btn_convertir.clicked.connect(self.convertir_a_factura)
        layout_acciones.addWidget(self.btn_convertir)

        self.btn_cerrar_detalle = QPushButton("🔙 Cerrar Detalle")
        self.btn_cerrar_detalle.setStyleSheet("background-color: #7F8C8D; color: white; padding: 8px 20px;")
        self.btn_cerrar_detalle.clicked.connect(self.cerrar_panel_detalle)
        layout_acciones.addWidget(self.btn_cerrar_detalle)

        self.btn_registrar_pago = QPushButton("💳 Registrar Abono / Pago")
        self.btn_registrar_pago.setStyleSheet("background-color: #F39C12; color: white; padding: 8px 20px; font-weight: bold;")
        self.btn_registrar_pago.clicked.connect(self.dialogo_registrar_pago)
        layout_acciones.addWidget(self.btn_registrar_pago)

        self.btn_pdf = QPushButton("📄 Exportar a PDF")
        self.btn_pdf.setStyleSheet("background-color: #E74C3C; color: white; padding: 8px 20px; font-weight: bold;")
        self.btn_pdf.clicked.connect(self.exportar_pdf)
        layout_acciones.addWidget(self.btn_pdf)

        layout_inferior.addLayout(layout_acciones)

        # Ocultar panel inferior al inicio
        self.panel_inferior.hide()

        # Agregar paneles al splitter
        splitter.addWidget(panel_superior)
        splitter.addWidget(self.panel_inferior)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout_principal.addWidget(splitter)

    # ============================================================
    #  CARGA DE DATOS
    # ============================================================

    def cargar_lista_facturas(self):
        """Carga la tabla principal de facturas según el filtro seleccionado."""
        filtro = self.combo_filtro.currentText()
        filtro_estado = None
        if filtro == "Pre-facturas":
            filtro_estado = "PRE-FACTURA"
        elif filtro == "Facturadas":
            filtro_estado = "FACTURADA"

        facturas = self.modelo.obtener_facturas(filtro_estado)
        self.tabla_facturas.setRowCount(0)

        for fila_idx, datos in enumerate(facturas):
            self.tabla_facturas.insertRow(fila_idx)
            # datos: id, numero_factura, razon_social, fecha, estado, subtotal, iva, total, obs, control
            id_val, numero, cliente, fecha, estado, subtotal, iva, total, obs, control = datos

            self.tabla_facturas.setItem(fila_idx, 0, QTableWidgetItem(str(id_val)))
            self.tabla_facturas.setItem(fila_idx, 1, QTableWidgetItem(numero))
            self.tabla_facturas.setItem(fila_idx, 2, QTableWidgetItem(cliente))
            self.tabla_facturas.setItem(fila_idx, 3, QTableWidgetItem(fecha))

            # Estado con color
            item_estado = QTableWidgetItem(estado)
            if estado == "PRE-FACTURA":
                item_estado.setForeground(QColor("#D35400"))
            else:
                item_estado.setForeground(QColor("#27AE60"))
            item_estado.setFont(QFont("", -1, QFont.Weight.Bold))
            self.tabla_facturas.setItem(fila_idx, 4, item_estado)

            self.tabla_facturas.setItem(fila_idx, 5, QTableWidgetItem(f"$ {subtotal:,.2f}"))
            self.tabla_facturas.setItem(fila_idx, 6, QTableWidgetItem(f"$ {iva:,.2f}"))
            
            item_total = QTableWidgetItem(f"$ {total:,.2f}")
            item_total.setFont(QFont("", -1, QFont.Weight.Bold))
            self.tabla_facturas.setItem(fila_idx, 7, item_total)

    def cargar_combos(self):
        """Carga los combo box de clientes y conceptos."""
        # Clientes
        self.combo_cliente.clear()
        clientes = self.modelo.obtener_clientes_para_combo()
        for cid, texto in clientes:
            self.combo_cliente.addItem(texto, cid)

        # Conceptos
        self.combo_concepto.clear()
        conceptos = self.modelo.obtener_conceptos_para_combo()
        for concepto in conceptos:
            cid, descripcion, tipo, aplica_iva = concepto
            self.combo_concepto.addItem(f"{descripcion} [{tipo}]", (cid, descripcion, aplica_iva))

    def cargar_detalle(self, factura_id):
        """Carga las líneas de detalle de una factura."""
        lineas = self.modelo.obtener_detalle(factura_id)
        self.tabla_detalle.setRowCount(0)

        for fila_idx, datos in enumerate(lineas):
            self.tabla_detalle.insertRow(fila_idx)
            # datos: id, concepto_desc, desc_manual, cantidad, precio_unit, aplica_iva, subtotal, concepto_id
            lid, concepto_desc, desc_manual, cantidad, precio, aplica_iva, subtotal, concepto_id = datos

            self.tabla_detalle.setItem(fila_idx, 0, QTableWidgetItem(str(lid)))
            self.tabla_detalle.setItem(fila_idx, 1, QTableWidgetItem(concepto_desc))
            self.tabla_detalle.setItem(fila_idx, 2, QTableWidgetItem(desc_manual if desc_manual else concepto_desc))
            self.tabla_detalle.setItem(fila_idx, 3, QTableWidgetItem(f"{cantidad:,.2f}"))
            self.tabla_detalle.setItem(fila_idx, 4, QTableWidgetItem(f"$ {precio:,.2f}"))
            self.tabla_detalle.setItem(fila_idx, 5, QTableWidgetItem("Sí" if aplica_iva else "No"))
            
            item_sub = QTableWidgetItem(f"$ {subtotal:,.2f}")
            item_sub.setFont(QFont("", -1, QFont.Weight.Bold))
            self.tabla_detalle.setItem(fila_idx, 6, item_sub)

    def actualizar_totales_ui(self, factura_id):
        """Actualiza las etiquetas de totales en la UI."""
        factura = self.modelo.obtener_factura_por_id(factura_id)
        if factura:
            # factura: id, numero, cliente_id, razon_social, fecha, estado, subtotal, iva, total, obs, control
            subtotal = factura[6]
            iva = factura[7]
            total = factura[8]
            self.lbl_subtotal.setText(f"Subtotal: $ {subtotal:,.2f}")
            self.lbl_iva.setText(f"IVA (16%): $ {iva:,.2f}")
            self.lbl_total.setText(f"TOTAL: $ {total:,.2f}")

            # Añade esto al final de actualizar_totales_ui
            if factura[5] == "FACTURADA":
                total, pagado, pendiente = self.modelo.obtener_saldo_pendiente(factura_id)
                self.lbl_pagado.setText(f"Pagado: $ {pagado:,.2f}")
                self.lbl_saldo_pendiente.setText(f"SALDO PENDIENTE: $ {pendiente:,.2f}")
                
                # Si ya está pagada completa, lo ponemos en verde
                if pendiente <= 0:
                    self.lbl_saldo_pendiente.setText("✅ FACTURA PAGADA")
                    self.lbl_saldo_pendiente.setStyleSheet("font-size: 16px; font-weight: bold; color: #27AE60;")
                    self.btn_registrar_pago.setEnabled(False)
                else:
                    self.lbl_saldo_pendiente.setStyleSheet("font-size: 16px; font-weight: bold; color: #C0392B;")
                    self.btn_registrar_pago.setEnabled(True)
            else:
                self.lbl_pagado.setText("")
                self.lbl_saldo_pendiente.setText("")

    # ============================================================
    #  ACCIONES PRINCIPALES
    # ============================================================

    def nueva_prefactura(self):
        """Crea una nueva pre-factura y abre el panel de detalle."""
        self.cargar_combos()

        if self.combo_cliente.count() == 0:
            QMessageBox.warning(self, "Advertencia", 
                "No hay clientes registrados.\nPrimero registra al menos un cliente en la pestaña 'Clientes'.")
            return

        if self.combo_concepto.count() == 0:
            QMessageBox.warning(self, "Advertencia", 
                "No hay conceptos facturables registrados.\nPrimero registra al menos un concepto en la pestaña 'Conceptos Facturables'.")
            return

        cliente_id = self.combo_cliente.currentData()
        fecha = datetime.now().strftime("%Y-%m-%d")

        exito, factura_id, mensaje = self.modelo.crear_factura(cliente_id, fecha)
        if exito:
            self.factura_actual_id = factura_id
            self.abrir_panel_detalle(factura_id, es_nueva=True)
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def ver_detalle_factura(self):
        """Abre el detalle de la factura seleccionada (doble clic)."""
        fila = self.tabla_facturas.currentRow()
        if fila >= 0:
            factura_id = int(self.tabla_facturas.item(fila, 0).text())
            self.cargar_combos()
            self.abrir_panel_detalle(factura_id, es_nueva=False)

    def abrir_panel_detalle(self, factura_id, es_nueva=False):
        """Configura y muestra el panel inferior con los datos de la factura."""
        self.factura_actual_id = factura_id
        factura = self.modelo.obtener_factura_por_id(factura_id)
        
        if not factura:
            QMessageBox.critical(self, "Error", "No se encontró la factura.")
            return

        # factura: id, numero, cliente_id, razon_social, fecha, estado, subtotal, iva, total, obs, control
        _, numero, cliente_id, razon_social, fecha, estado, subtotal, iva, total, obs, control = factura

        # Llenar encabezado
        self.lbl_numero_valor.setText(f"<b>{numero}</b>")
        self.lbl_fecha_valor.setText(fecha)

        # Estado con color
        if estado == "PRE-FACTURA":
            self.lbl_estado_valor.setText("🟠 PRE-FACTURA (Borrador)")
            self.lbl_estado_valor.setStyleSheet("font-size: 13px; font-weight: bold; color: #D35400;")
        else:
            self.lbl_estado_valor.setText("🟢 FACTURADA (Definitiva)")
            self.lbl_estado_valor.setStyleSheet("font-size: 13px; font-weight: bold; color: #27AE60;")

        # Seleccionar cliente en combo
        for i in range(self.combo_cliente.count()):
            if self.combo_cliente.itemData(i) == cliente_id:
                self.combo_cliente.setCurrentIndex(i)
                break

        self.input_control.setText(control if control else "")
        self.input_observaciones.setText(obs if obs else "")

        # Cargar detalle y totales
        self.cargar_detalle(factura_id)
        self.actualizar_totales_ui(factura_id)

        # Reemplaza el bloque de "Habilitar/deshabilitar según estado" por esto:
        es_editable = (estado == "PRE-FACTURA")
        self.combo_cliente.setEnabled(es_editable)
        self.input_control.setEnabled(es_editable)
        self.input_observaciones.setEnabled(es_editable)
        self.btn_agregar_linea.setEnabled(es_editable)
        self.combo_concepto.setEnabled(es_editable)
        self.input_desc_linea.setEnabled(es_editable)
        self.spin_cantidad.setEnabled(es_editable)
        self.spin_precio.setEnabled(es_editable)
        self.chk_iva_linea.setEnabled(es_editable)
        self.spin_iva_factura.setEnabled(es_editable)
        
        self.btn_guardar_factura.setVisible(es_editable)
        self.btn_convertir.setVisible(es_editable)
        
        # El botón de pagos solo es visible si la factura ya es definitiva
        self.btn_registrar_pago.setVisible(not es_editable)

        # Mostrar panel
        self.panel_inferior.show()

    def cerrar_panel_detalle(self):
        """Cierra el panel de detalle inferior."""
        self.panel_inferior.hide()
        self.factura_actual_id = None
        self.cargar_lista_facturas()

    # ============================================================
    #  LÍNEAS DE DETALLE
    # ============================================================

    def concepto_seleccionado(self):
        """Cuando se selecciona un concepto, autocompleta descripción e IVA."""
        data = self.combo_concepto.currentData()
        if data:
            concepto_id, descripcion, aplica_iva = data
            self.input_desc_linea.setText(descripcion)
            self.chk_iva_linea.setChecked(bool(aplica_iva))

    def agregar_linea(self):
        """Agrega una línea de detalle a la factura actual."""
        if not self.factura_actual_id:
            return

        data_concepto = self.combo_concepto.currentData()
        if not data_concepto:
            QMessageBox.warning(self, "Advertencia", "Selecciona un concepto facturable.")
            return

        concepto_id, _, _ = data_concepto
        descripcion = self.input_desc_linea.text().strip()
        cantidad = self.spin_cantidad.value()
        precio = self.spin_precio.value()
        aplica_iva = self.chk_iva_linea.isChecked()

        if not descripcion:
            QMessageBox.warning(self, "Advertencia", "La descripción no puede estar vacía.")
            return

        if precio <= 0:
            QMessageBox.warning(self, "Advertencia", "El precio debe ser mayor a cero.")
            return

        exito, mensaje = self.modelo.agregar_linea(
            self.factura_actual_id, concepto_id, descripcion, cantidad, precio, aplica_iva
        )

        if exito:
            self.cargar_detalle(self.factura_actual_id)
            self.actualizar_totales_ui(self.factura_actual_id)
            self.cargar_lista_facturas()
            # Resetear campos
            self.spin_cantidad.setValue(1)
            self.spin_precio.setValue(0.01)
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def menu_linea_detalle(self, posicion):
        """Menú contextual para eliminar líneas de detalle."""
        fila = self.tabla_detalle.rowAt(posicion.y())
        if fila >= 0 and self.factura_actual_id:
            # Verificar que la factura sea editable
            factura = self.modelo.obtener_factura_por_id(self.factura_actual_id)
            if factura and factura[5] != "PRE-FACTURA":
                return  # No mostrar menú si es factura definitiva

            menu = QMenu()
            accion_eliminar = menu.addAction("🗑️ Eliminar Línea")
            accion = menu.exec(self.tabla_detalle.viewport().mapToGlobal(posicion))

            if accion == accion_eliminar:
                linea_id = int(self.tabla_detalle.item(fila, 0).text())
                respuesta = QMessageBox.question(
                    self, "Confirmar", "¿Eliminar esta línea de detalle?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if respuesta == QMessageBox.StandardButton.Yes:
                    exito, mensaje = self.modelo.eliminar_linea(linea_id, self.factura_actual_id)
                    if exito:
                        self.cargar_detalle(self.factura_actual_id)
                        self.actualizar_totales_ui(self.factura_actual_id)
                        self.cargar_lista_facturas()
                    else:
                        QMessageBox.critical(self, "Error", mensaje)

    # ============================================================
    #  OPERACIONES DE ENCABEZADO
    # ============================================================

    def guardar_cambios_encabezado(self):
        """Guarda cambios en el cliente, observaciones y número de control."""
        if not self.factura_actual_id:
            return

        cliente_id = self.combo_cliente.currentData()
        observaciones = self.input_observaciones.text().strip()
        numero_control = self.input_control.text().strip()

        exito, mensaje = self.modelo.actualizar_factura(
            self.factura_actual_id, cliente_id, observaciones, numero_control
        )

        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
            self.cargar_lista_facturas()
            # Recargar para refrescar nombre de cliente
            self.abrir_panel_detalle(self.factura_actual_id, es_nueva=False)
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def convertir_a_factura(self):
        """Convierte la pre-factura actual en factura definitiva."""
        if not self.factura_actual_id:
            return

        respuesta = QMessageBox.question(
            self, "Confirmar Conversión",
            "⚠️ ¿Estás seguro de convertir esta pre-factura en factura definitiva?\n\n"
            "Una vez convertida, NO se podrá editar ni eliminar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            # Primero guardar cambios pendientes del encabezado
            cliente_id = self.combo_cliente.currentData()
            observaciones = self.input_observaciones.text().strip()
            numero_control = self.input_control.text().strip()
            self.modelo.actualizar_factura(self.factura_actual_id, cliente_id, observaciones, numero_control)

            exito, mensaje = self.modelo.convertir_a_factura(self.factura_actual_id)
            if exito:
                QMessageBox.information(self, "Éxito", f"🎉 {mensaje}")
                self.cargar_lista_facturas()
                self.abrir_panel_detalle(self.factura_actual_id, es_nueva=False)
            else:
                QMessageBox.critical(self, "Error", mensaje)

    # ============================================================
    #  MENÚ CONTEXTUAL DE LA TABLA PRINCIPAL
    # ============================================================

    def mostrar_menu_contextual(self, posicion):
        """Menú contextual en la tabla principal de facturas."""
        fila = self.tabla_facturas.rowAt(posicion.y())
        if fila >= 0:
            factura_id = int(self.tabla_facturas.item(fila, 0).text())
            estado = self.tabla_facturas.item(fila, 4).text()

            menu = QMenu()
            accion_ver = menu.addAction("👁️ Ver Detalle")

            accion_editar = None
            accion_convertir = None
            accion_eliminar = None

            if estado == "PRE-FACTURA":
                accion_editar = menu.addAction("✏️ Editar Pre-factura")
                accion_convertir = menu.addAction("✅ Convertir a Factura")
                menu.addSeparator()
                accion_eliminar = menu.addAction("🗑️ Eliminar Pre-factura")

            accion = menu.exec(self.tabla_facturas.viewport().mapToGlobal(posicion))

            if accion == accion_ver:
                self.cargar_combos()
                self.abrir_panel_detalle(factura_id, es_nueva=False)
            elif accion_editar and accion == accion_editar:
                self.cargar_combos()
                self.abrir_panel_detalle(factura_id, es_nueva=False)
            elif accion_convertir and accion == accion_convertir:
                self.factura_actual_id = factura_id
                self.cargar_combos()
                self.convertir_a_factura()
            elif accion_eliminar and accion == accion_eliminar:
                respuesta = QMessageBox.question(
                    self, "Confirmar", "¿Seguro que deseas eliminar esta pre-factura y todo su detalle?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if respuesta == QMessageBox.StandardButton.Yes:
                    exito, mensaje = self.modelo.eliminar_factura(factura_id)
                    if exito:
                        self.cargar_lista_facturas()
                        if self.factura_actual_id == factura_id:
                            self.cerrar_panel_detalle()
                        QMessageBox.information(self, "Éxito", mensaje)
                    else:
                        QMessageBox.critical(self, "Error", mensaje)

    def cambiar_porcentaje_iva(self):
        """Se ejecuta cuando el usuario cambia el porcentaje del IVA en la interfaz."""
        if not self.factura_actual_id: return
        nuevo_iva = self.spin_iva_factura.value()
        self.modelo.actualizar_porcentaje_iva(self.factura_actual_id, nuevo_iva)
        self.actualizar_totales_ui(self.factura_actual_id)
        self.cargar_lista_facturas()

    def exportar_pdf(self):
        if not self.factura_actual_id: return
        
        factura = self.modelo.obtener_factura_por_id(self.factura_actual_id)
        lineas = self.modelo.obtener_detalle(self.factura_actual_id)
        
        # _, numero, cliente_id, razon_social, fecha, estado, subtotal, iva, total, obs, control
        numero, cliente, fecha, control, obs = factura[1], factura[3], factura[4], factura[10], factura[9]
        
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Factura PDF", f"{numero}.pdf", "PDF Files (*.pdf)")
        if not ruta: return

        # Plantilla HTML para el PDF (Super elegante y fácil de modificar)
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #2E86C1; color: white; }}
                .totales {{ text-align: right; margin-top: 20px; font-size: 16px; }}
            </style>
        </head>
        <body>
            <h1>Aduanera Transmundial</h1>
            <p><b>Documento:</b> {numero} &nbsp;&nbsp;&nbsp; <b>Nº Control:</b> {control if control else 'N/A'}</p>
            <p><b>Cliente:</b> {cliente}<br><b>Fecha:</b> {fecha}</p>
            
            <table>
                <tr><th>Descripción</th><th>Cantidad</th><th>Precio Unit.</th><th>Subtotal</th></tr>
        """
        
        for l in lineas:
            # l = (lid, concepto_desc, desc_manual, cantidad, precio, aplica_iva, subtotal_linea, concepto_id)
            html += f"<tr><td>{l[2]}</td><td>{l[3]}</td><td>${l[4]:,.2f}</td><td>${l[6]:,.2f}</td></tr>"
            
        html += f"""
            </table>
            <div class="totales">
                <p><b>Subtotal:</b> ${factura[6]:,.2f}</p>
                <p><b>IVA:</b> ${factura[7]:,.2f}</p>
                <p><b style="color: #27AE60;">TOTAL: ${factura[8]:,.2f}</b></p>
            </div>
            <p><small><b>Observaciones:</b> {obs if obs else 'Ninguna'}</small></p>
        </body>
        </html>
        """

        # Generar el PDF usando las herramientas nativas de PyQt6
        documento = QTextDocument()
        documento.setHtml(html)
        
        impresora = QPdfWriter(ruta)
        documento.print(impresora)
        
        QMessageBox.information(self, "Éxito", "Factura exportada a PDF correctamente.")

    def dialogo_registrar_pago(self):
        if not self.factura_actual_id: return
        
        total, pagado, pendiente = self.modelo.obtener_saldo_pendiente(self.factura_actual_id)
        
        # Pedir monto
        monto, ok = QInputDialog.getDouble(self, "Registrar Pago", 
                                          f"Saldo pendiente: $ {pendiente:,.2f}\nIngrese monto a abonar:", 
                                          pendiente, 0.01, pendiente, 2)
        if not ok: return
        
        # Pedir método de pago
        metodos = ["Transferencia Nacional", "Pago Móvil", "Zelle", "Efectivo Divisas", "Efectivo Bs"]
        metodo, ok = QInputDialog.getItem(self, "Método de Pago", "Seleccione el método:", metodos, 0, False)
        if not ok: return
        
        # Pedir referencia
        referencia, ok = QInputDialog.getText(self, "Referencia", "Número de referencia (opcional):")
        if not ok: return

        exito, msj = self.modelo.registrar_pago(self.factura_actual_id, monto, metodo, referencia)
        if exito:
            QMessageBox.information(self, "Éxito", msj)
            self.actualizar_totales_ui(self.factura_actual_id)
        else:
            QMessageBox.critical(self, "Error", msj)