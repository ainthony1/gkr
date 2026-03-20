"""
1099-NEC PDF generator for Got Key'd Realty Commission Tracker.
Fills the IRS 1099-NEC fillable PDF template using PyMuPDF (fitz).
"""
import os
import re
import fitz  # PyMuPDF
from core.models import Agent, TaxRecord
from core.constants import COMPANY_NAME, COMPANY_ADDRESS, get_resource_path, get_data_dir


# Page indices in the 1099-NEC PDF template (6 pages total)
# Page 0 = Instructions (no fields)
# Page 1 = Copy A (IRS)
# Page 2 = Copy 1 (State)
# Page 3 = Copy B (Recipient) - we fill this
# Page 4 = Instructions (no fields)
# Page 5 = Copy 2 (Payer records) - we fill this
COPY_B_PAGE = 3
COPY_2_PAGE = 5


# 1099-NEC field mapping by short suffix
# These suffixes appear in the fully-qualified field names on each page
FIELD_MAPPING = {
    "f2_1": "year",         # Calendar year
    "f2_2": "payer_info",   # Payer name, address, phone
    "f2_3": "payer_tin",    # Payer's TIN (EIN)
    "f2_4": "recip_tin",    # Recipient's TIN (SSN/EIN)
    "f2_5": "recip_name",   # Recipient's name
    "f2_6": "recip_street", # Street address
    "f2_7": "recip_city",   # City, state, ZIP
    "f2_9": "box1_amount",  # Box 1: Nonemployee compensation
}


def _get_output_dir(tax_year: int) -> str:
    """Get (and create) the output directory for 1099 PDFs."""
    out_dir = os.path.join(get_data_dir(), "1099", str(tax_year))
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _safe_filename(name: str) -> str:
    """Sanitize agent name for use in filenames."""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name).strip()


def _get_field_suffix(field_name: str) -> str:
    """Extract the short field suffix (e.g., 'f2_1') from a fully-qualified name."""
    match = re.search(r'(f\d+_\d+)\[0\]$', field_name)
    return match.group(1) if match else ""


def _build_values(agent: Agent, tax_year: int, company_ein: str, amount: float) -> dict:
    """Build the value map for field suffixes."""
    city_state_zip = ""
    parts = []
    if agent.city:
        parts.append(agent.city)
    if agent.state:
        parts.append(agent.state)
    if parts:
        city_state_zip = ", ".join(parts)
    if agent.zip_code:
        city_state_zip += f" {agent.zip_code}" if city_state_zip else agent.zip_code

    return {
        "year": str(tax_year),
        "payer_info": f"{COMPANY_NAME}\n{COMPANY_ADDRESS}",
        "payer_tin": company_ein,
        "recip_tin": agent.tin if agent.tin else "",
        "recip_name": agent.name,
        "recip_street": agent.street_address if agent.street_address else "",
        "recip_city": city_state_zip,
        "box1_amount": f"{amount:,.2f}",
    }


def _fill_page(page, agent: Agent, tax_year: int, company_ein: str, amount: float):
    """Fill form fields on a single 1099-NEC page."""
    values = _build_values(agent, tax_year, company_ein, amount)

    for widget in page.widgets():
        suffix = _get_field_suffix(widget.field_name)
        if suffix in FIELD_MAPPING:
            key = FIELD_MAPPING[suffix]
            value = values.get(key, "")
            if value:
                widget.field_value = value
                widget.update()


def generate_1099(agent: Agent, tax_record: TaxRecord, company_ein: str,
                   output_dir: str = None) -> str:
    """Generate a 1099-NEC PDF for an agent.

    Fills Copy B (recipient) and Copy 2 (payer records) pages.
    If output_dir is provided, saves into output_dir/1099/{year}/.
    Otherwise falls back to app data directory.
    Returns the path to the generated PDF.
    """
    template_path = get_resource_path(os.path.join('assets', 'f1099nec.pdf'))
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"1099-NEC template not found at {template_path}")

    doc = fitz.open(template_path)
    amount = tax_record.effective_amount

    # Fill Copy B and Copy 2
    for page_idx in [COPY_B_PAGE, COPY_2_PAGE]:
        if page_idx < len(doc):
            _fill_page(doc[page_idx], agent, tax_record.tax_year, company_ein, amount)

    # Extract only Copy B and Copy 2 into output
    output_doc = fitz.open()
    for page_idx in [COPY_B_PAGE, COPY_2_PAGE]:
        if page_idx < len(doc):
            output_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

    # Save
    if output_dir:
        out_dir = os.path.join(output_dir, "1099", str(tax_record.tax_year))
        os.makedirs(out_dir, exist_ok=True)
    else:
        out_dir = _get_output_dir(tax_record.tax_year)
    safe_name = _safe_filename(agent.name)
    out_path = os.path.join(out_dir, f"{safe_name}_1099NEC_{tax_record.tax_year}.pdf")
    output_doc.save(out_path)
    output_doc.close()
    doc.close()

    return out_path


def get_warnings(agent: Agent, company_ein: str) -> list[str]:
    """Return a list of warnings about missing data for 1099 generation."""
    warnings = []
    if not company_ein:
        warnings.append("Company EIN is not set")
    if not agent.tin:
        warnings.append(f"Missing TIN for {agent.name}")
    if not agent.street_address:
        warnings.append(f"Missing mailing address for {agent.name}")
    return warnings
