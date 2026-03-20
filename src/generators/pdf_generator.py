import os
from fpdf import FPDF
from core.models import Agent, CommissionResult
from core.constants import (
    COMPANY_NAME, COMPANY_ADDRESS, COMPANY_PHONE,
    NAVY_RGB, BLUE_RGB, DARK_TEXT_RGB, GRAY_TEXT_RGB,
    LIGHT_BG_RGB, ROW_ALT_RGB, WHITE_RGB, LOGO_PATH,
)


class InvoicePDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'Letter')
        self.set_auto_page_break(auto=False)
        self.set_margins(25, 20, 25)


def _fmt(amount: float) -> str:
    """Format dollar amount."""
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def generate_invoice(
    agent: Agent,
    result: CommissionResult,
    invoice_number: str,
    invoice_date: str,
    property_address: str,
    payment_method: str = '',
    include_cap_section: bool = True,
    output_path: str = '',
) -> str:
    pdf = InvoicePDF()
    pdf.add_page()

    page_w = 215.9  # Letter width mm
    margin = 25
    usable_w = page_w - 2 * margin

    # ===== HEADER: Logo + Title =====
    y_start = 15
    logo_h = 0
    if os.path.exists(LOGO_PATH):
        # Scale logo to 30mm wide and measure height
        logo_w = 30
        pdf.image(LOGO_PATH, x=margin, y=y_start, w=logo_w)
        # Estimate logo height (PNG is roughly square for this circular logo)
        from PIL import Image as PILImage
        with PILImage.open(LOGO_PATH) as img:
            w_px, h_px = img.size
            logo_h = logo_w * (h_px / w_px)

    # Title on the right side, vertically centered with logo
    title_y = y_start + max(0, (logo_h - 22) / 2)
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(*NAVY_RGB)
    pdf.set_xy(margin + usable_w - 80, title_y)
    pdf.cell(80, 8, 'COMMISSION', align='R')

    pdf.set_text_color(*BLUE_RGB)
    pdf.set_xy(margin + usable_w - 80, title_y + 12)
    pdf.cell(80, 8, 'INVOICE', align='R')

    # ===== Company Address Block + Invoice Meta =====
    # Start below the logo with some padding
    y_info = y_start + logo_h + 5

    # Company address (left)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*NAVY_RGB)
    pdf.set_xy(margin, y_info)
    pdf.cell(usable_w / 2, 5, COMPANY_NAME)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*DARK_TEXT_RGB)
    pdf.set_xy(margin, y_info + 6)
    pdf.cell(usable_w / 2, 4, '22260 Garrison St')
    pdf.set_xy(margin, y_info + 11)
    pdf.cell(usable_w / 2, 4, 'Dearborn, MI 48124')
    pdf.set_xy(margin, y_info + 16)
    pdf.cell(usable_w / 2, 4, COMPANY_PHONE)

    # Invoice meta (right side, label: value table)
    meta_x = margin + usable_w / 2 + 10
    meta_w_label = 40
    meta_w_value = usable_w / 2 - 10 - meta_w_label

    for i, (label, value) in enumerate([
        ('Invoice #:', invoice_number),
        ('Date:', invoice_date),
        ('Payment:', payment_method or 'N/A'),
    ]):
        y = y_info + i * 7
        # Label
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*BLUE_RGB)
        pdf.set_xy(meta_x, y)
        pdf.cell(meta_w_label, 5, label, align='R')
        # Value
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*DARK_TEXT_RGB)
        pdf.set_xy(meta_x + meta_w_label + 2, y)
        pdf.cell(meta_w_value, 5, value)

    # ===== BILL TO Section =====
    y_bill = y_info + 30
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*BLUE_RGB)
    pdf.set_xy(margin, y_bill)
    pdf.cell(usable_w, 5, 'BILL TO')

    # Bill-to box with light background
    y_bill_box = y_bill + 7
    pdf.set_fill_color(*LIGHT_BG_RGB)
    pdf.rect(margin, y_bill_box, usable_w, 14, 'F')

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*NAVY_RGB)
    pdf.set_xy(margin + 4, y_bill_box + 2)
    pdf.cell(usable_w / 2 - 4, 5, agent.name)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*DARK_TEXT_RGB)
    pdf.set_xy(margin + 4, y_bill_box + 8)
    pdf.cell(usable_w / 2 - 4, 5, property_address)

    # ===== PAYMENT DETAILS Section =====
    y_pay = y_bill_box + 22
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*BLUE_RGB)
    pdf.set_xy(margin, y_pay)
    pdf.cell(usable_w, 5, 'PAYMENT DETAILS')

    # Table header
    y_table = y_pay + 7
    row_h = 9
    col_desc_w = usable_w * 0.7
    col_amt_w = usable_w * 0.3

    pdf.set_fill_color(*NAVY_RGB)
    pdf.rect(margin, y_table, usable_w, row_h, 'F')
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*WHITE_RGB)
    pdf.set_xy(margin + 4, y_table + 2)
    pdf.cell(col_desc_w - 4, 5, 'DESCRIPTION')
    pdf.set_xy(margin + col_desc_w, y_table + 2)
    pdf.cell(col_amt_w - 4, 5, 'AMOUNT', align='R')

    # Table rows — skip any line where the amount is $0
    rows = []
    rows.append((f"Total Payment to {COMPANY_NAME} (ACH)", _fmt(result.gross_commission)))

    if result.compliance_to_office > 0:
        rows.append((f"Compliance Fee payable to {COMPANY_NAME}", _fmt(-result.compliance_to_office)))

    rows.append((f"Agent Commission payable to {agent.name}", _fmt(result.agent_share)))

    if result.compliance_to_agent != 0:
        rows.append((f"Compliance Fee payable to {agent.name}", _fmt(result.compliance_to_agent)))

    if agent.split_type != 'transaction_fee' and result.amount_toward_cap > 0:
        rows.append(("Amount Towards Cap", _fmt(result.amount_toward_cap)))

    for i, (desc, amt) in enumerate(rows):
        y_row = y_table + row_h + (i * row_h)
        if i % 2 == 0:
            pdf.set_fill_color(*WHITE_RGB)
        else:
            pdf.set_fill_color(*LIGHT_BG_RGB)
        pdf.rect(margin, y_row, usable_w, row_h, 'F')

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*DARK_TEXT_RGB)
        pdf.set_xy(margin + 4, y_row + 2)
        pdf.cell(col_desc_w - 4, 5, desc)
        pdf.set_xy(margin + col_desc_w, y_row + 2)
        pdf.cell(col_amt_w - 4, 5, amt, align='R')

    # Total Payout row
    y_total = y_table + row_h + (len(rows) * row_h)
    pdf.set_fill_color(*ROW_ALT_RGB)
    pdf.rect(margin, y_total, usable_w, row_h + 2, 'F')
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*NAVY_RGB)
    pdf.set_xy(margin + 4, y_total + 2)
    pdf.cell(col_desc_w - 4, 6, 'TOTAL PAYOUT')
    pdf.set_xy(margin + col_desc_w, y_total + 2)
    pdf.cell(col_amt_w - 4, 6, _fmt(result.total_payout), align='R')

    # ===== CAP STATUS Section (Internal only) =====
    y_cap = y_total + row_h + 10

    if include_cap_section and agent.split_type != 'transaction_fee':
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*BLUE_RGB)
        pdf.set_xy(margin, y_cap)
        pdf.cell(usable_w, 5, 'CAP STATUS')

        y_cap_table = y_cap + 7
        col_w = usable_w / 3

        # Header row
        pdf.set_fill_color(*NAVY_RGB)
        pdf.rect(margin, y_cap_table, usable_w, row_h, 'F')
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*WHITE_RGB)

        for j, header in enumerate(['Cap Amount', 'Cap Paid To Date', 'Remaining']):
            pdf.set_xy(margin + j * col_w + 4, y_cap_table + 2)
            pdf.cell(col_w - 8, 5, header, align='C')

        # Value row
        y_cap_val = y_cap_table + row_h
        pdf.set_fill_color(*LIGHT_BG_RGB)
        pdf.rect(margin, y_cap_val, usable_w, row_h, 'F')

        cap_amt = agent.cap_amount if agent.cap_amount else 0
        remaining = max(0, cap_amt - result.cap_after)

        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*NAVY_RGB)

        for j, val in enumerate([_fmt(cap_amt), _fmt(result.cap_after), _fmt(remaining)]):
            pdf.set_xy(margin + j * col_w + 4, y_cap_val + 2)
            pdf.cell(col_w - 8, 5, val, align='C')

        y_footer_start = y_cap_val + row_h + 15
    else:
        y_footer_start = y_cap + 5

    # ===== FOOTER =====
    # Thank you message
    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(*GRAY_TEXT_RGB)
    pdf.set_xy(margin, y_footer_start)
    pdf.cell(usable_w, 5, 'Thank you for your partnership!', align='C')

    # Company footer
    pdf.set_font('Helvetica', '', 8)
    pdf.set_xy(margin, y_footer_start + 8)
    pdf.cell(usable_w, 4, f"{COMPANY_NAME}  |  {COMPANY_ADDRESS}  |  {COMPANY_PHONE}", align='C')

    # Save
    pdf.output(output_path)
    return output_path


def generate_both_invoices(
    agent: Agent,
    result: CommissionResult,
    invoice_number: str,
    invoice_date: str,
    property_address: str,
    payment_method: str,
    output_dir: str,
) -> tuple[str, str]:
    """Generate both internal (with cap) and agent (without cap) invoices.
    Returns (internal_path, agent_path).
    """
    # Clean filename parts
    safe_name = agent.name.replace(' ', '-')
    safe_addr = property_address.replace(' ', '-').replace(',', '').replace('.', '')[:40]

    internal_filename = f"{invoice_number}_{safe_name}_{safe_addr}_INTERNAL.pdf"
    agent_filename = f"{invoice_number}_{safe_name}_{safe_addr}.pdf"

    # Auto-organize into subfolders
    internal_dir = os.path.join(output_dir, "invoices", "internal")
    agent_dir = os.path.join(output_dir, "invoices", "agent")
    os.makedirs(internal_dir, exist_ok=True)
    os.makedirs(agent_dir, exist_ok=True)

    internal_path = os.path.join(internal_dir, internal_filename)
    agent_path = os.path.join(agent_dir, agent_filename)

    generate_invoice(
        agent=agent, result=result,
        invoice_number=invoice_number, invoice_date=invoice_date,
        property_address=property_address, payment_method=payment_method,
        include_cap_section=True, output_path=internal_path,
    )

    generate_invoice(
        agent=agent, result=result,
        invoice_number=invoice_number, invoice_date=invoice_date,
        property_address=property_address, payment_method=payment_method,
        include_cap_section=False, output_path=agent_path,
    )

    return internal_path, agent_path
