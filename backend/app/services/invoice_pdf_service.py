from datetime import datetime
from fpdf import FPDF


def generate_invoice_pdf(
    invoice_number: str,
    org_name: str,
    org_email: str,
    plan_name: str,
    amount_cents: int,
    currency: str = "USD",
    billing_address: str = "",
    tax_vat: str = "",
    status: str = "paid",
    period_start: str = "",
    period_end: str = "",
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header
    pdf.set_fill_color(20, 30, 50)
    pdf.rect(0, 0, pdf.w, 50, "F")
    pdf.set_y(14)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(147, 197, 253)
    pdf.cell(0, 12, "AURA", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 6, "Enterprise Intelligence Platform", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)

    # Invoice title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(0, 10, "INVOICE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"Invoice #{invoice_number}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Issued: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Bill to
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(0, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, org_name, new_x="LMARGIN", new_y="NEXT")
    if org_email:
        pdf.cell(0, 5, org_email, new_x="LMARGIN", new_y="NEXT")
    if billing_address:
        pdf.cell(0, 5, billing_address[:60], new_x="LMARGIN", new_y="NEXT")
    if tax_vat:
        pdf.cell(0, 5, f"VAT: {tax_vat}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    # Invoice table
    col_w = [90, 30, 30, 40]
    headers = ["Description", "Period", "Amount", "Status"]
    pdf.set_fill_color(20, 30, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1, fill=True, align="C")
    pdf.ln()

    symbol = "$" if currency == "USD" else currency + " "
    amount_str = f"{symbol}{amount_cents / 100:.2f}"

    pdf.set_fill_color(245, 247, 250)
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(col_w[0], 7, f"  {plan_name} Plan - AURA Enterprise", border=1, fill=True)
    pdf.cell(col_w[1], 7, f" {period_start[:10]} to {period_end[:10]}" if period_start and period_end else "  Monthly", border=1, fill=True, align="C")
    pdf.cell(col_w[2], 7, amount_str, border=1, fill=True, align="C")
    pdf.cell(col_w[3], 7, f"  {status.upper()}", border=1, fill=True, align="C")
    pdf.ln()

    # Totals
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(150, 7, "Total:", align="R")
    pdf.cell(40, 7, amount_str, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(20)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "AURA Enterprise Intelligence Platform", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Invoice #{invoice_number}", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
