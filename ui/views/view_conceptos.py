from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QHeaderView,
                             QComboBox, QCheckBox, QMenu)
from PyQt6.QtCore import Qt
from models.conceptos_model import ConceptosModel

class ViewConceptos(QWidget):
    def __init__(self):
        super().__init__()
        self.modelo = ConceptosModel()
        self.id_concepto_editando = None # Controla si estamos creando o editando
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)

        # --- PANEL IZQUIERDO: FORMULARIO ---
        panel_formulario = QVBoxLayout()
        
        titulo = QLabel("<b>Catálogo de Conceptos</b>")
        panel_formulario.addWidget(titulo)

        self.input_descripcion = QLineEdit()
        self.input_descripcion.setPlaceholderText("Descripción (Ej: Nacionalización)")
        panel_formulario.addWidget(self.input_descripcion)

        self.input_tipo = QComboBox()
        self.input_tipo.addItems(["Honorarios (Ingreso Agencia)", "Reintegro (Pago a Terceros)", "Impuesto / Tasa"])
        panel_formulario.addWidget(self.input_tipo)

        self.input_iva = QCheckBox("Aplica IVA (16%)")
        panel_formulario.addWidget(self.input_iva)

        self.btn_guardar = QPushButton("💾 Guardar Concepto")
        self.btn_guardar.setStyleSheet("background-color: #27AE60; color: white; padding: 8px;")
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
        self.tabla_conceptos = QTableWidget()
        self.tabla_conceptos.setColumnCount(4)
        self.tabla_conceptos.setHorizontalHeaderLabels(["ID", "Descripción", "Tipo", "Aplica IVA"])
        self.tabla_conceptos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_conceptos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_conceptos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Menú contextual (clic derecho)
        self.tabla_conceptos.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_conceptos.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        layout_principal.addLayout(panel_formulario, stretch=1)
        layout_principal.addWidget(self.tabla_conceptos, stretch=3)

    def mostrar_menu_contextual(self, posicion):
        fila_seleccionada = self.tabla_conceptos.rowAt(posicion.y())
        if fila_seleccionada >= 0:
            menu = QMenu()
            accion_editar = menu.addAction("✏️ Editar Concepto")
            accion_eliminar = menu.addAction("🗑️ Eliminar Concepto")

            accion = menu.exec(self.tabla_conceptos.viewport().mapToGlobal(posicion))
            id_concepto = self.tabla_conceptos.item(fila_seleccionada, 0).text()

            if accion == accion_editar:
                self.preparar_edicion(fila_seleccionada)
            elif accion == accion_eliminar:
                self.eliminar_concepto(id_concepto)

    def preparar_edicion(self, fila):
        self.id_concepto_editando = self.tabla_conceptos.item(fila, 0).text()
        self.input_descripcion.setText(self.tabla_conceptos.item(fila, 1).text())
        
        # Ajustar el desplegable
        tipo_texto = self.tabla_conceptos.item(fila, 2).text()
        self.input_tipo.setCurrentText(tipo_texto)
        
        # Ajustar la casilla de IVA
        aplica_iva_texto = self.tabla_conceptos.item(fila, 3).text()
        self.input_iva.setChecked(True if aplica_iva_texto == "Sí" else False)

        # Cambiar el botón a modo edición
        self.btn_guardar.setText("🔄 Actualizar Concepto")
        self.btn_guardar.setStyleSheet("background-color: #D35400; color: white; padding: 8px;")
        self.btn_cancelar.show()

    def eliminar_concepto(self, id_concepto):
        respuesta = QMessageBox.question(self, "Confirmar", "¿Seguro que deseas eliminar este concepto?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, mensaje = self.modelo.eliminar_concepto(id_concepto)
            if exito:
                self.cargar_datos()
                self.limpiar_formulario()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def procesar_formulario(self):
        descripcion = self.input_descripcion.text().strip()
        tipo = self.input_tipo.currentText()
        aplica_iva = self.input_iva.isChecked()

        if not descripcion:
            QMessageBox.warning(self, "Advertencia", "La descripción es obligatoria.")
            return

        # Convertimos el booleano del CheckBox (True/False) a entero (1/0) para SQLite
        valor_iva = 1 if aplica_iva else 0

        if self.id_concepto_editando:
            exito, mensaje = self.modelo.actualizar_concepto(self.id_concepto_editando, descripcion, tipo, valor_iva)
        else:
            exito, mensaje = self.modelo.agregar_concepto(descripcion, tipo, valor_iva)
        
        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
            self.limpiar_formulario()
            self.cargar_datos()
        else:
            QMessageBox.critical(self, "Error", mensaje)

    def limpiar_formulario(self):
        self.input_descripcion.clear()
        self.input_tipo.setCurrentIndex(0) # Vuelve a la primera opción
        self.input_iva.setChecked(False)
        self.id_concepto_editando = None
        
        # Restaurar aspecto del botón
        self.btn_guardar.setText("💾 Guardar Concepto")
        self.btn_guardar.setStyleSheet("background-color: #27AE60; color: white; padding: 8px;")
        self.btn_cancelar.hide()

    def cargar_datos(self):
        self.tabla_conceptos.setRowCount(0)
        conceptos = self.modelo.obtener_conceptos()
        
        for fila_idx, datos_fila in enumerate(conceptos):
            self.tabla_conceptos.insertRow(fila_idx)
            
            id_concepto, descripcion, tipo, aplica_iva = datos_fila
            texto_iva = "Sí" if aplica_iva == 1 else "No"
            
            self.tabla_conceptos.setItem(fila_idx, 0, QTableWidgetItem(str(id_concepto)))
            self.tabla_conceptos.setItem(fila_idx, 1, QTableWidgetItem(descripcion))
            self.tabla_conceptos.setItem(fila_idx, 2, QTableWidgetItem(tipo))
            self.tabla_conceptos.setItem(fila_idx, 3, QTableWidgetItem(texto_iva))