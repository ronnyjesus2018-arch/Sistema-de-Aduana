from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGroupBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument, QPdfWriter
import pandas as pd
from models.reportes_model import ReportesModel
from datetime import datetime

class ViewReportes(QWidget):
    def __init__(self):
        super().__init__()
        self.modelo = ReportesModel()
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)

        # --- PANEL SUPERIOR: TARJETAS DE MÉTRICAS ---
        layout_cards = QHBoxLayout()
        
        self.lbl_clientes = self.crear_tarjeta(layout_cards, "Clientes Registrados", "#8E44AD")
        self.lbl_expedientes = self.crear_tarjeta(layout_cards, "Expedientes Activos", "#2980B9")
        self.lbl_facturacion = self.crear_tarjeta(layout_cards, "Total Facturado", "#27AE60")
        self.lbl_gastos = self.crear_tarjeta(layout_cards, "Gastos Operativos", "#C0392B")
        
        layout_principal.addLayout(layout_cards)

        # Botón para refrescar el Dashboard manualmente
        btn_actualizar = QPushButton("🔄 Actualizar Métricas")
        btn_actualizar.setStyleSheet("padding: 5px; font-weight: bold;")
        btn_actualizar.clicked.connect(self.cargar_metricas)
        layout_principal.addWidget(btn_actualizar, alignment=Qt.AlignmentFlag.AlignRight)

        # --- PANEL INFERIOR: EXPORTACIÓN ---
        grupo_exportar = QGroupBox("Exportación de Datos")
        layout_exportar = QHBoxLayout(grupo_exportar)

        btn_excel = QPushButton("📊 Exportar Resumen a Excel")
        btn_excel.setStyleSheet("background-color: #1D8348; color: white; padding: 15px; font-weight: bold; font-size: 14px;")
        btn_excel.clicked.connect(self.exportar_excel)
        layout_exportar.addWidget(btn_excel)

        btn_pdf = QPushButton("📄 Generar Reporte PDF")
        btn_pdf.setStyleSheet("background-color: #C0392B; color: white; padding: 15px; font-weight: bold; font-size: 14px;")
        btn_pdf.clicked.connect(self.exportar_pdf)
        layout_exportar.addWidget(btn_pdf)

        layout_principal.addWidget(grupo_exportar)
        layout_principal.addStretch()

        # Cargar los datos al iniciar
        self.cargar_metricas()

    def crear_tarjeta(self, layout, titulo, color_fondo):
        """Crea una 'tarjeta' visual para los números grandes."""
        tarjeta = QGroupBox()
        tarjeta.setStyleSheet(f"background-color: {color_fondo}; border-radius: 10px; color: white;")
        vbox = QVBoxLayout(tarjeta)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_valor = QLabel("0")
        lbl_valor.setStyleSheet("font-size: 24px; font-weight: bold;")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        vbox.addWidget(lbl_titulo)
        vbox.addWidget(lbl_valor)
        layout.addWidget(tarjeta)
        
        return lbl_valor

    def cargar_metricas(self):
        """Consulta la base de datos y actualiza los números grandes."""
        cli, exp, fact, gast = self.modelo.obtener_metricas_dashboard()
        self.lbl_clientes.setText(str(cli))
        self.lbl_expedientes.setText(str(exp))
        self.lbl_facturacion.setText(f"$ {fact:,.2f}")
        self.lbl_gastos.setText(f"$ {gast:,.2f}")

    def exportar_excel(self):
        """Exporta el historial de facturación a un archivo Excel usando Pandas."""
        columnas, filas = self.modelo.obtener_datos_facturacion()
        if not filas:
            QMessageBox.warning(self, "Aviso", "No hay datos de facturación para exportar.")
            return

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", "Reporte_Aduanas.xlsx", "Excel Files (*.xlsx)")
        if ruta:
            try:
                df = pd.DataFrame(filas, columns=columnas)
                df.to_excel(ruta, index=False, sheet_name="Facturación")
                QMessageBox.information(self, "Éxito", "Reporte de Excel generado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al exportar a Excel: {e}")

    def exportar_pdf(self):
        """Genera un reporte gerencial en PDF."""
        cli, exp, fact, gast = self.modelo.obtener_metricas_dashboard()
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte PDF", "Dashboard_Gerencial.pdf", "PDF Files (*.pdf)")
        if not ruta: return

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #2E86C1; }}
                table {{ width: 80%; margin-top: 20px; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; font-size: 14px; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Reporte Gerencial - Aduanera Transmundial</h1>
            <p><b>Fecha de generación:</b> {fecha}</p>
            <hr>
            <table>
                <tr><th>Métrica</th><th>Valor</th></tr>
                <tr><td>Clientes Registrados</td><td>{cli}</td></tr>
                <tr><td>Expedientes Activos</td><td>{exp}</td></tr>
                <tr><td>Total Facturado (Definitivo)</td><td>$ {fact:,.2f}</td></tr>
                <tr><td>Total Gastos Operativos</td><td>$ {gast:,.2f}</td></tr>
                <tr><td><b>Balance Neto Operativo</b></td><td><b>$ {(fact - gast):,.2f}</b></td></tr>
            </table>
        </body>
        </html>
        """

        try:
            documento = QTextDocument()
            documento.setHtml(html)
            impresora = QPdfWriter(ruta)
            documento.print(impresora)
            QMessageBox.information(self, "Éxito", "Reporte PDF gerencial generado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al crear PDF: {e}")