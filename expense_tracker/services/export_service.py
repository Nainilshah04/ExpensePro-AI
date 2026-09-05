import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ExportService:
    """
    Generates downloadable PDF Financial Reports and Excel (.xlsx) Workbooks.
    """

    def generate_excel(self, expenses, user):
        output = io.BytesIO()
        data = [{
            "Date": e.date.strftime("%Y-%m-%d"),
            "Category": e.category,
            "Amount (₹)": e.amount,
            "Payment Method": getattr(e, 'payment_method', 'UPI'),
            "Note": e.note or ""
        } for e in expenses]

        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=["Date", "Category", "Amount (₹)", "Payment Method", "Note"])

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Transactions", index=False)
            
            # Summary Sheet
            if not df.empty:
                summary_df = df.groupby("Category")["Amount (₹)"].agg(["count", "sum"]).reset_index()
                summary_df.columns = ["Category", "Transaction Count", "Total Spent (₹)"]
                summary_df.to_excel(writer, sheet_name="Category Summary", index=False)

        output.seek(0)
        return output

    def generate_pdf(self, expenses, user, total_spent, budget_data):
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#1E293B')
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B')
        )
        heading2_style = ParagraphStyle(
            'Heading2Style',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=18,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6,
            spaceBefore=12
        )

        # Header Banner
        elements.append(Paragraph("ExpensePro | Financial Statement", title_style))
        elements.append(Paragraph(f"Account: <b>{user.username}</b> ({user.email}) | Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", subtitle_style))
        elements.append(Spacer(1, 14))

        # KPI Metrics Table
        kpi_data = [
            [
                Paragraph("<b>Total Expenditure</b>", subtitle_style),
                Paragraph("<b>Total Transactions</b>", subtitle_style),
                Paragraph("<b>Active Month</b>", subtitle_style)
            ],
            [
                Paragraph(f"<font size=14 color='#2563EB'><b>₹{total_spent:,.2f}</b></font>", styles['Normal']),
                Paragraph(f"<font size=14 color='#0F172A'><b>{len(expenses)}</b></font>", styles['Normal']),
                Paragraph(f"<font size=14 color='#0F172A'><b>{datetime.now().strftime('%B %Y')}</b></font>", styles['Normal'])
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[180, 180, 180])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # Category Budget Performance Table
        if budget_data:
            elements.append(Paragraph("Budget vs Actual Performance", heading2_style))
            b_headers = [["Category", "Spent (₹)", "Budget Limit (₹)", "Status"]]
            for b in budget_data:
                status = f"{b['percent']:.0f}% used" if b['spent'] <= b['limit'] else f"OVER (+₹{b['spent'] - b['limit']:,.0f})"
                b_headers.append([
                    b['name'],
                    f"₹{b['spent']:,.0f}",
                    f"₹{b['limit']:,.0f}",
                    status
                ])
            b_table = Table(b_headers, colWidths=[135, 135, 135, 135])
            b_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,1), (-1,-1), 8.5),
            ]))
            elements.append(b_table)
            elements.append(Spacer(1, 14))

        # Recent Transactions Table
        elements.append(Paragraph("Transaction History", heading2_style))
        tx_rows = [["Date", "Category", "Note", "Amount (₹)"]]
        for e in expenses[:30]: # Up to 30 recent records for clean page fit
            tx_rows.append([
                e.date.strftime('%d-%b-%Y'),
                e.category,
                (e.note or "-")[:35],
                f"₹{e.amount:,.2f}"
            ])

        tx_table = Table(tx_rows, colWidths=[90, 100, 240, 110])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F1F5F9')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('FONTSIZE', (0,1), (-1,-1), 8.5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(tx_table)

        doc.build(elements)
        output.seek(0)
        return output

export_service = ExportService()
