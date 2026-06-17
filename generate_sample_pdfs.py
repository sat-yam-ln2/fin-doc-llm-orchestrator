from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
import os

styles = getSampleStyleSheet()

# ── Shared Styles ──────────────────────────────────────────────────────────────
title_style = ParagraphStyle(
    "custom_title",
    parent=styles["Title"],
    fontSize=16,
    spaceAfter=6,
    textColor=colors.HexColor("#003366")
)
header_style = ParagraphStyle(
    "header",
    parent=styles["Normal"],
    fontSize=9,
    textColor=colors.grey,
    spaceAfter=4
)
bold_style = ParagraphStyle(
    "bold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10
)
body_style = ParagraphStyle(
    "body",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    spaceAfter=6
)
small_style = ParagraphStyle(
    "small",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.grey,
    spaceAfter=4
)
red_style = ParagraphStyle(
    "red",
    parent=styles["Normal"],
    fontSize=9,
    textColor=colors.red,
    spaceAfter=4
)

os.makedirs("sample_pdfs", exist_ok=True)


def make_bank_statement():
    doc = SimpleDocTemplate(
        "sample_pdfs/sample_bank_statement.pdf", pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch
    )
    story = []

    story.append(Paragraph("FIRST NATIONAL BANK", ParagraphStyle(
        "bank", parent=styles["Title"], fontSize=20,
        textColor=colors.HexColor("#003366"))))
    story.append(Paragraph(
        "123 Finance Street, New York, NY 10001  |  www.fnbank.com", header_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#003366")))
    story.append(Spacer(1, 10))
    story.append(Paragraph("ACCOUNT STATEMENT", title_style))

    info = [
        ["Account Holder:", "John A. Meyers"],
        ["Account Number:", "4821-0093-2211"],
        ["Account Type:", "Business Checking"],
        ["Statement Period:", "March 1, 2024 - March 31, 2024"],
    ]
    info_table = Table(info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 6))
    story.append(Paragraph("TRANSACTION HISTORY", bold_style))
    story.append(Spacer(1, 6))

    txn_header = [["Date", "Description", "Debit ($)", "Credit ($)"]]
    txn_data = txn_header + [
        ["03/02", "ATM Withdrawal", "500.00", ""],
        ["03/07", "Wire Transfer Out - Acct 9900-1122", "12,000.00", ""],
        ["03/10", "Payroll Deposit", "", "3,200.00"],
        ["03/15", "International Wire Transfer - FLAGGED", "8,750.00", ""],
        ["03/22", "POS Purchase", "45.00", ""],
        ["03/28", "Cash Withdrawal", "2,000.00", ""],
    ]
    txn_table = Table(txn_data, colWidths=[0.8*inch, 3.5*inch, 1.2*inch, 1.2*inch])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(txn_table)
    story.append(Spacer(1, 12))

    summary = [
        ["SUMMARY", ""],
        ["Total Credits", "$3,200.00"],
        ["Total Debits", "$23,295.00"],
    ]
    sum_table = Table(summary, colWidths=[3*inch, 2*inch])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "* One or more transactions flagged for compliance review.", red_style))

    doc.build(story)
    print("Created: sample_pdfs/sample_bank_statement.pdf")


def make_invoice():
    doc = SimpleDocTemplate(
        "sample_pdfs/sample_invoice.pdf", pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch
    )
    story = []

    story.append(Paragraph("INVOICE", ParagraphStyle(
        "inv_title", parent=styles["Title"], fontSize=24,
        textColor=colors.HexColor("#1a1a2e"))))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 10))

    info = [
        ["Invoice Number:", "INV-20240415"],
        ["Vendor:", "Rapid Logistics Ltd"],
        ["Buyer:", "Nexus Trading Co."],
        ["Invoice Date:", "April 15, 2024"],
        ["Due Date:", "May 15, 2024"],
        ["Payment Terms:", "Wire Transfer Only"],
    ]
    info_table = Table(info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))
    story.append(Paragraph("LINE ITEMS", bold_style))
    story.append(Spacer(1, 6))

    line_data = [
        ["Description", "Amount ($)"],
        ["Freight Services Q1", "14,000.00"],
        ["Handling Fee", "1,200.00"],
        ["Customs Clearance", "800.00"],
        ["TOTAL DUE", "16,000.00"],
    ]
    line_table = Table(line_data, colWidths=[4.5*inch, 2*inch])
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f4f8")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(line_table)

    doc.build(story)
    print("Created: sample_pdfs/sample_invoice.pdf")


def make_dispute_letter():
    doc = SimpleDocTemplate(
        "sample_pdfs/sample_dispute_letter.pdf", pagesize=letter,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        leftMargin=inch, rightMargin=inch
    )
    story = []

    story.append(Paragraph("FORMAL DISPUTE LETTER", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 12))
    story.append(Paragraph("To Whom It May Concern,", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "I am writing to formally dispute a charge on my account number 7731-4492. "
        "On February 10, 2024, a transaction of $3,450 was posted to my account that I did not authorize. "
        "I have no record of this purchase and have not received any goods or services for this amount.",
        body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "I am requesting an immediate investigation and full reversal of this charge. "
        "Please contact me at your earliest convenience.",
        body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Paragraph("Angela Torres", bold_style))

    doc.build(story)
    print("Created: sample_pdfs/sample_dispute_letter.pdf")


def make_news_snippet():
    doc = SimpleDocTemplate(
        "sample_pdfs/sample_news_snippet.pdf", pagesize=letter,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        leftMargin=inch, rightMargin=inch
    )
    story = []

    story.append(Paragraph("FINANCIAL NEWS ALERT", ParagraphStyle(
        "news", parent=styles["Title"], fontSize=18,
        textColor=colors.HexColor("#8b0000"))))
    story.append(Paragraph("March 28, 2024", header_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#8b0000")))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Regulators have flagged Omega Capital Partners for potential money laundering activities. "
        "According to sources familiar with the matter, the firm processed over $40 million in suspicious "
        "cross-border transfers in Q1 2024. CEO David Lau has denied wrongdoing. "
        "The Financial Crimes Enforcement Network (FinCEN) has opened a formal investigation.",
        body_style))

    doc.build(story)
    print("Created: sample_pdfs/sample_news_snippet.pdf")


def make_bank_statement_month(month_name: str, month_num: str, credits: str, debits: str,
                               transactions: list, filename: str, has_flag: bool = False):
    doc = SimpleDocTemplate(
        filename, pagesize=letter,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
        leftMargin=0.7*inch, rightMargin=0.7*inch
    )
    story = []

    story.append(Paragraph("FIRST NATIONAL BANK", ParagraphStyle("bank", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#003366"))))
    story.append(Paragraph("123 Finance Street, New York, NY 10001  |  www.fnbank.com", header_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#003366")))
    story.append(Spacer(1, 10))
    story.append(Paragraph("ACCOUNT STATEMENT", title_style))

    info = [
        ["Account Holder:", "John A. Meyers"],
        ["Account Number:", "4821-0093-2211"],
        ["Account Type:", "Business Checking"],
        ["Statement Period:", f"{month_name} 1, 2024 - {month_name} 28, 2024"],
    ]
    info_table = Table(info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 6))
    story.append(Paragraph("TRANSACTION HISTORY", bold_style))
    story.append(Spacer(1, 6))

    txn_header = [["Date", "Description", "Debit ($)", "Credit ($)"]]
    txn_data = txn_header + transactions
    txn_table = Table(txn_data, colWidths=[0.8*inch, 3.5*inch, 1.2*inch, 1.2*inch])
    txn_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("ALIGN", (2,0), (-1,-1), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(txn_table)
    story.append(Spacer(1, 12))

    summary = [
        ["SUMMARY", ""],
        ["Total Credits", credits],
        ["Total Debits", debits],
    ]
    sum_table = Table(summary, colWidths=[3*inch, 2*inch])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(sum_table)

    if has_flag:
        story.append(Spacer(1, 8))
        story.append(Paragraph("* One or more transactions flagged for compliance review.", red_style))

    doc.build(story)
    print(f"Created: {filename}")


def make_ambiguous_document():
    doc = SimpleDocTemplate(
        "sample_pdfs/sample_ambiguous.pdf", pagesize=letter,
        topMargin=0.7*inch, bottomMargin=0.7*inch,
        leftMargin=inch, rightMargin=inch
    )
    story = []

    story.append(Paragraph("INTERNAL MEMO — COMPLIANCE REVIEW", ParagraphStyle(
        "memo", parent=styles["Title"], fontSize=16, textColor=colors.HexColor("#5a0000"))))
    story.append(Paragraph("Ref: CMP-2024-0391 | Prepared by: Risk Operations Team | Date: April 2, 2024", header_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#5a0000")))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "This memo documents a formal complaint received from account holder Marcus Webb (Account No. 5593-8821) "
        "regarding a disputed transaction of $7,200 on March 29, 2024. The account holder states the charge "
        "was unauthorized.",
        body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Separately, our adverse media team flagged news reports this week linking the merchant — "
        "Trident Payment Solutions — to an ongoing FinCEN investigation into cross-border wire fraud "
        "and money laundering. CEO Raymond Holt of Trident Payment Solutions denied the allegations "
        "in a public statement.",
        body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Risk Operations recommends escalation of this case to the Senior Fraud Committee given "
        "the overlap between the customer dispute and the regulatory investigation into the merchant.",
        body_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph("CONFIDENTIAL — FOR INTERNAL USE ONLY. Do not distribute outside compliance department.", small_style))

    doc.build(story)
    print("Created: sample_pdfs/sample_ambiguous.pdf")


if __name__ == "__main__":
    make_bank_statement()
    make_invoice()
    make_dispute_letter()
    make_news_snippet()

    # 4 monthly bank statements for trend view — same account, escalating risk
    make_bank_statement_month(
        "January", "01", "$5,200.00", "$3,100.00",
        [
            ["01/05", "Payroll Deposit", "", "3,200.00"],
            ["01/10", "Rent Payment", "1,500.00", ""],
            ["01/18", "Utility Bills", "800.00", ""],
            ["01/25", "ATM Withdrawal", "800.00", ""],
        ],
        "sample_pdfs/sample_bank_jan.pdf", has_flag=False
    )
    make_bank_statement_month(
        "February", "02", "$5,200.00", "$4,800.00",
        [
            ["02/05", "Payroll Deposit", "", "5,200.00"],
            ["02/08", "Rent Payment", "1,500.00", ""],
            ["02/14", "Transfer to Savings", "1,800.00", ""],
            ["02/20", "ATM Withdrawal", "1,500.00", ""],
        ],
        "sample_pdfs/sample_bank_feb.pdf", has_flag=False
    )
    make_bank_statement_month(
        "March", "03", "$3,200.00", "$23,295.00",
        [
            ["03/02", "ATM Withdrawal", "500.00", ""],
            ["03/07", "Wire Transfer Out - Acct 9900-1122", "12,000.00", ""],
            ["03/10", "Payroll Deposit", "", "3,200.00"],
            ["03/15", "Intl Wire Transfer - FLAGGED", "8,750.00", ""],
            ["03/28", "Cash Withdrawal", "2,000.00", ""],
        ],
        "sample_pdfs/sample_bank_mar.pdf", has_flag=True
    )
    make_bank_statement_month(
        "April", "04", "$5,200.00", "$6,100.00",
        [
            ["04/05", "Payroll Deposit", "", "5,200.00"],
            ["04/10", "Rent Payment", "1,500.00", ""],
            ["04/17", "ATM Withdrawal", "600.00", ""],
            ["04/22", "Online Transfer", "4,000.00", ""],
        ],
        "sample_pdfs/sample_bank_apr.pdf", has_flag=False
    )

    make_ambiguous_document()
    print("\nAll PDFs created successfully.")
