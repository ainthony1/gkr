import customtkinter as ctk
from core.constants import COMPANY_NAME
from ui.theme import (
    get_colors,
    section_label, card, success_button, primary_button, secondary_button,
    separator, stat_block, badge, font_display, font_heading,
    font_subheading, font_body, font_caption,
)


class ReviewFrame(ctk.CTkFrame):
    def __init__(self, parent, agent, result, invoice_number, invoice_date,
                 property_address, payment_method, on_generate, on_edit, on_cancel):
        c = get_colors()
        super().__init__(parent, fg_color="transparent")
        self.agent = agent
        self.result = result
        self.invoice_number = invoice_number
        self.on_generate = on_generate
        self.on_edit = on_edit
        self.on_cancel = on_cancel

        self._build_ui(invoice_date, property_address, payment_method)

    def _fmt(self, amount):
        if amount < 0:
            return f"-${abs(amount):,.2f}"
        return f"${amount:,.2f}"

    def _build_ui(self, invoice_date, property_address, payment_method):
        c = get_colors()
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Page Header ──
        header_area = ctk.CTkFrame(scroll, fg_color="transparent")
        header_area.pack(fill="x", padx=30, pady=(28, 0))

        ctk.CTkLabel(
            header_area, text="Invoice Preview",
            font=font_display(28),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_area, text="Review the commission breakdown before generating the PDF",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        # ── Invoice Header Card ──
        header_card = card(scroll)
        header_card.pack(fill="x", padx=30, pady=(20, 0))

        hdr_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=24, pady=20)

        # Left: invoice meta
        left = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        left.pack(side="left")

        inv_row = ctk.CTkFrame(left, fg_color="transparent")
        inv_row.pack(anchor="w")

        ctk.CTkLabel(
            inv_row, text=self.invoice_number,
            font=font_heading(18),
            text_color=c['TEXT_PRIMARY'],
        ).pack(side="left")

        if self.invoice_number == "(pending)":
            badge(inv_row, "DRAFT", color=c['TEXT_SECONDARY']).pack(side="left", padx=(10, 0))

        meta_items = [
            f"Date: {invoice_date}",
            f"Payment: {payment_method or 'N/A'}",
        ]
        ctk.CTkLabel(
            left, text="  \u2022  ".join(meta_items),
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(4, 0))

        # Right: agent info
        right = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkLabel(
            right, text=self.agent.name,
            font=font_subheading(14),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="e")

        ctk.CTkLabel(
            right, text=property_address,
            font=font_caption(12),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="e", pady=(2, 0))

        # ── Payment Breakdown Card ──
        breakdown_card = card(scroll)
        breakdown_card.pack(fill="x", padx=30, pady=(12, 0))

        bd_inner = ctk.CTkFrame(breakdown_card, fg_color="transparent")
        bd_inner.pack(fill="x", padx=24, pady=20)

        sl = section_label(bd_inner, "Payment Breakdown")
        sl.pack(anchor="w", pady=(0, 12))

        r = self.result
        compliance_display = -r.compliance_to_office if r.compliance_to_office > 0 else 0

        rows = [
            (f"Total Payment to {COMPANY_NAME}", self._fmt(r.gross_commission), False),
            (f"Compliance Fee to {COMPANY_NAME}", self._fmt(compliance_display) if r.compliance_fee_amount > 0 else "$0.00", False),
            (f"Agent Commission to {self.agent.name}", self._fmt(r.agent_share), False),
            (f"Compliance Fee to {self.agent.name}", self._fmt(r.compliance_to_agent) if r.compliance_to_agent != 0 else "$0.00", False),
            ("Amount Towards Cap", self._fmt(r.amount_toward_cap) if self.agent.split_type != 'transaction_fee' else "N/A", False),
        ]

        # Table header
        hdr_row = ctk.CTkFrame(bd_inner, fg_color=c['SECTION_BG'], corner_radius=6)
        hdr_row.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            hdr_row, text="Description",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=c['TEXT_MUTED'], anchor="w",
        ).pack(side="left", padx=14, pady=8)

        ctk.CTkLabel(
            hdr_row, text="Amount",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=c['TEXT_MUTED'], anchor="e",
        ).pack(side="right", padx=14, pady=8)

        # Data rows
        for i, (desc, amt, is_total) in enumerate(rows):
            bg = "transparent" if i % 2 == 0 else c['SECTION_BG']
            row_frame = ctk.CTkFrame(bd_inner, fg_color=bg, corner_radius=4)
            row_frame.pack(fill="x")

            ctk.CTkLabel(
                row_frame, text=desc,
                font=font_body(12), text_color=c['TEXT_SECONDARY'], anchor="w",
            ).pack(side="left", padx=14, pady=6)

            ctk.CTkLabel(
                row_frame, text=amt,
                font=font_body(12), text_color=c['TEXT_PRIMARY'], anchor="e",
            ).pack(side="right", padx=14, pady=6)

        # Total payout row
        total_frame = ctk.CTkFrame(bd_inner, fg_color=c['SIDEBAR_BG'], corner_radius=8)
        total_frame.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            total_frame, text="TOTAL PAYOUT",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=c['PRIMARY'], anchor="w",
        ).pack(side="left", padx=14, pady=10)

        ctk.CTkLabel(
            total_frame, text=self._fmt(r.total_payout),
            font=ctk.CTkFont(size=16, weight="bold"), text_color='#FFFFFF', anchor="e",
        ).pack(side="right", padx=14, pady=10)

        # ── Cap Status Card ──
        if self.agent.split_type != 'transaction_fee':
            cap_card = card(scroll)
            cap_card.pack(fill="x", padx=30, pady=(12, 0))

            cap_inner = ctk.CTkFrame(cap_card, fg_color="transparent")
            cap_inner.pack(fill="x", padx=24, pady=20)

            sl2 = section_label(cap_inner, "Cap Status")
            sl2.pack(anchor="w", pady=(0, 14))

            cap_amt = self.agent.cap_amount or 0
            remaining = max(0, cap_amt - r.cap_after)

            stats_row = ctk.CTkFrame(cap_inner, fg_color="transparent")
            stats_row.pack(fill="x")

            stats = [
                ("Cap Amount", self._fmt(cap_amt)),
                ("Paid to Date", self._fmt(r.cap_after)),
                ("Remaining", self._fmt(remaining)),
            ]

            for label, val in stats:
                s = stat_block(stats_row, label, val, c['TEXT_PRIMARY'])
                s.pack(side="left", padx=(0, 50))

            # Progress bar
            if cap_amt > 0:
                progress = min(1.0, r.cap_after / cap_amt)

                bar_frame = ctk.CTkFrame(cap_inner, fg_color="transparent")
                bar_frame.pack(fill="x", pady=(16, 0))

                ctk.CTkLabel(
                    bar_frame,
                    text=f"Progress  \u2014  {progress:.0%}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=c['TEXT_MUTED'],
                ).pack(anchor="w", pady=(0, 4))

                bar = ctk.CTkProgressBar(
                    bar_frame, width=450, height=8,
                    progress_color=c['PRIMARY'],
                    fg_color=c['CARD_BORDER'],
                    corner_radius=4,
                )
                bar.set(progress)
                bar.pack(anchor="w")

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(24, 30))

        success_button(
            btn_frame, "Generate Invoice PDF", self.on_generate, width=230,
        ).pack(side="left", padx=(0, 12))

        primary_button(
            btn_frame, "Edit", self.on_edit, width=100,
        ).pack(side="left", padx=(0, 12))

        secondary_button(
            btn_frame, "Cancel", self.on_cancel, width=100,
        ).pack(side="left")
