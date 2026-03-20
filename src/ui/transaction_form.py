import customtkinter as ctk
from datetime import date
from ui.theme import (
    get_colors,
    page_title, section_label, card, primary_button, secondary_button,
    separator, badge, font_display, font_heading, font_subheading,
    font_body, font_caption,
)


class TransactionForm(ctk.CTkFrame):
    def __init__(self, parent, agent, on_calculate, on_cancel):
        super().__init__(parent, fg_color="transparent")
        self.agent = agent
        self.on_calculate = on_calculate
        self.on_cancel = on_cancel

        self._build_ui()

    def _build_ui(self):
        c = get_colors()

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Page Header ──
        header_area = ctk.CTkFrame(scroll, fg_color="transparent")
        header_area.pack(fill="x", padx=30, pady=(28, 0))

        ctk.CTkLabel(
            header_area, text="New Transaction",
            font=font_display(24),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        # ── Agent Info Bar ──
        agent_bar = ctk.CTkFrame(scroll, fg_color=c['SIDEBAR_BG'], corner_radius=10)
        agent_bar.pack(fill="x", padx=30, pady=(16, 0))

        bar_inner = ctk.CTkFrame(agent_bar, fg_color="transparent")
        bar_inner.pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(
            bar_inner, text=self.agent.name,
            font=font_heading(16),
            text_color="#FFFFFF",
        ).pack(side="left")

        # Split info
        if self.agent.split_type == 'transaction_fee':
            split_text = f"Transaction Fee: ${self.agent.transaction_fee:,.0f}"
        elif self.agent.split_type == 'tiered':
            split_text = "Tiered: 60/40 first 4, then 70/30"
        else:
            split_text = f"Split: {self.agent.agent_split_pct:.0f}/{self.agent.office_split_pct:.0f}"

        ctk.CTkLabel(
            bar_inner, text=split_text,
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(side="right")

        # ── Form Card ──
        form_card = card(scroll)
        form_card.pack(fill="x", padx=30, pady=(16, 0))

        form = ctk.CTkFrame(form_card, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=24)

        # ── Property Address ──
        sl = section_label(form, "Property Details")
        sl.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(form, text="Property Address", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.address_entry = ctk.CTkEntry(
            form, width=500, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="123 Main St, City, MI 48124",
        )
        self.address_entry.pack(anchor="w")

        # ── Commission Calculation Row ──
        sep1 = separator(form)
        sep1.pack(fill="x", pady=(20, 16))

        sl2 = section_label(form, "Commission")
        sl2.pack(anchor="w", pady=(0, 10))

        calc_row = ctk.CTkFrame(form, fg_color="transparent")
        calc_row.pack(fill="x")

        # Sale Price
        col1 = ctk.CTkFrame(calc_row, fg_color="transparent")
        col1.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(col1, text="Sale Price ($)", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.sale_price_entry = ctk.CTkEntry(
            col1, width=180, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="350,000",
        )
        self.sale_price_entry.pack(anchor="w")
        self.sale_price_entry.bind("<KeyRelease>", self._update_gross)

        # Commission %
        col2 = ctk.CTkFrame(calc_row, fg_color="transparent")
        col2.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(col2, text="Commission %", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.comm_pct_entry = ctk.CTkEntry(
            col2, width=120, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="3",
        )
        self.comm_pct_entry.pack(anchor="w")
        self.comm_pct_entry.bind("<KeyRelease>", self._update_gross)

        # Gross Commission Display
        col3 = ctk.CTkFrame(calc_row, fg_color="transparent")
        col3.pack(side="left", padx=(0, 0))
        ctk.CTkLabel(col3, text="Gross Commission", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))

        gross_bg = ctk.CTkFrame(col3, fg_color=c['SECTION_BG'], corner_radius=8, height=38)
        gross_bg.pack(anchor="w")
        gross_bg.pack_propagate(False)

        self.gross_label = ctk.CTkLabel(
            gross_bg, text="$0.00",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c['PRIMARY'],
            width=160, height=38,
        )
        self.gross_label.pack(padx=12)

        # ── Date & Options ──
        sep2 = separator(form)
        sep2.pack(fill="x", pady=(20, 16))

        sl3 = section_label(form, "Transaction Details")
        sl3.pack(anchor="w", pady=(0, 10))

        options_row = ctk.CTkFrame(form, fg_color="transparent")
        options_row.pack(fill="x")

        # Closing Date
        date_col = ctk.CTkFrame(options_row, fg_color="transparent")
        date_col.pack(side="left", padx=(0, 30))
        ctk.CTkLabel(date_col, text="Closing Date (MM/DD/YYYY)", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        today = date.today().strftime("%m/%d/%Y")
        self.date_entry = ctk.CTkEntry(
            date_col, width=200, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text=today,
        )
        self.date_entry.insert(0, today)
        self.date_entry.pack(anchor="w")

        # Company Lead
        lead_col = ctk.CTkFrame(options_row, fg_color="transparent")
        lead_col.pack(side="left")

        ctk.CTkLabel(lead_col, text="Lead Source", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))

        self.company_lead_var = ctk.BooleanVar(value=False)
        self.company_lead_check = ctk.CTkCheckBox(
            lead_col,
            text="Company-Generated Lead",
            font=font_body(13),
            variable=self.company_lead_var,
            checkbox_width=20, checkbox_height=20,
            corner_radius=6,
            border_width=2,
            border_color=c['INPUT_BORDER'],
            fg_color=c['PRIMARY'],
            hover_color=c['PRIMARY_HOVER'],
        )
        self.company_lead_check.pack(anchor="w", pady=(4, 0))

        # ── Compliance Fee ──
        sep3 = separator(form)
        sep3.pack(fill="x", pady=(20, 16))

        sl4 = section_label(form, "Compliance Fee")
        sl4.pack(anchor="w", pady=(0, 10))

        fee_row = ctk.CTkFrame(form, fg_color="transparent")
        fee_row.pack(fill="x")

        left_fee = ctk.CTkFrame(fee_row, fg_color="transparent")
        left_fee.pack(side="left", padx=(0, 30))
        ctk.CTkLabel(left_fee, text="Fee Amount ($)", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.fee_entry = ctk.CTkEntry(
            left_fee, width=160, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="0.00",
        )
        self.fee_entry.insert(0, "0")
        self.fee_entry.pack(anchor="w")

        right_fee = ctk.CTkFrame(fee_row, fg_color="transparent")
        right_fee.pack(side="left")
        ctk.CTkLabel(right_fee, text="Who Pays?", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))

        self.payer_var = ctk.StringVar(value="buyer")
        payer_frame = ctk.CTkFrame(right_fee, fg_color="transparent")
        payer_frame.pack(anchor="w")
        for val, text in [("buyer", "Buyer"), ("seller", "Seller"), ("agent_waived", "Agent Waived")]:
            ctk.CTkRadioButton(
                payer_frame, text=text, variable=self.payer_var, value=val,
                font=font_body(13),
                fg_color=c['PRIMARY'], hover_color=c['PRIMARY_HOVER'],
                border_width_unchecked=2,
                border_color=c['INPUT_BORDER'],
            ).pack(side="left", padx=(0, 18))

        # ── Payment Method ──
        sep4 = separator(form)
        sep4.pack(fill="x", pady=(20, 16))

        sl5 = section_label(form, "Payment")
        sl5.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(form, text="Payment Method (optional)", font=font_caption(11), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.payment_entry = ctk.CTkEntry(
            form, width=320, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="ACH, Check #1234, etc.",
        )
        self.payment_entry.pack(anchor="w")

        # ── Error Label ──
        self.error_label = ctk.CTkLabel(
            form, text="", text_color=c['DANGER'],
            font=font_body(12),
        )
        self.error_label.pack(anchor="w", pady=(14, 0))

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(20, 30))

        primary_button(
            btn_frame, "Calculate & Preview", self._calculate, width=220,
        ).pack(side="left", padx=(0, 12))

        secondary_button(
            btn_frame, "Cancel", self.on_cancel, width=120,
        ).pack(side="left")

    def _update_gross(self, event=None):
        try:
            price = float(self.sale_price_entry.get().strip().replace(',', '').replace('$', ''))
            pct = float(self.comm_pct_entry.get().strip().replace('%', ''))
            gross = price * (pct / 100)
            self.gross_label.configure(text=f"${gross:,.2f}")
        except (ValueError, ZeroDivisionError):
            self.gross_label.configure(text="$0.00")

    def _get_gross_commission(self) -> float | None:
        price_str = self.sale_price_entry.get().strip().replace(',', '').replace('$', '')
        pct_str = self.comm_pct_entry.get().strip().replace('%', '')

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError
        except ValueError:
            self.error_label.configure(text="Enter a valid sale price (positive number).")
            return None

        try:
            pct = float(pct_str)
            if pct <= 0 or pct > 100:
                raise ValueError
        except ValueError:
            self.error_label.configure(text="Enter a valid commission percentage (e.g. 3, 5, 2.5).")
            return None

        return round(price * (pct / 100), 2)

    def _calculate(self):
        self.error_label.configure(text="")

        address = self.address_entry.get().strip()
        if not address:
            self.error_label.configure(text="Property address is required.")
            return

        gross_commission = self._get_gross_commission()
        if gross_commission is None:
            return

        date_str = self.date_entry.get().strip()
        try:
            from datetime import datetime
            closing_date = datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            self.error_label.configure(text="Enter a valid date in MM/DD/YYYY format.")
            return

        fee_str = self.fee_entry.get().strip().replace(',', '').replace('$', '')
        try:
            compliance_fee = float(fee_str) if fee_str else 0.0
            if compliance_fee < 0:
                raise ValueError
        except ValueError:
            self.error_label.configure(text="Enter a valid compliance fee (0 or positive).")
            return

        self.on_calculate(
            agent=self.agent,
            property_address=address,
            gross_commission=gross_commission,
            closing_date=closing_date,
            is_company_lead=self.company_lead_var.get(),
            compliance_fee=compliance_fee,
            compliance_fee_payer=self.payer_var.get(),
            payment_method=self.payment_entry.get().strip(),
            sale_price=self.sale_price_entry.get().strip().replace(',', '').replace('$', ''),
            comm_pct=self.comm_pct_entry.get().strip().replace('%', ''),
        )
