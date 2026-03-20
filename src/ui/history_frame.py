import customtkinter as ctk
from ui.theme import (
    get_colors,
    section_label, card, secondary_button, separator,
    font_display, font_heading, font_subheading, font_body, font_caption,
)


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, parent, db, agent=None, on_back=None, on_regenerate=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.agent = agent
        self.on_back = on_back
        self.on_regenerate = on_regenerate
        self.transactions = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        c = get_colors()
        # ── Page Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(28, 0))

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")

        title_text = f"Transaction History" if not self.agent else f"History \u2014 {self.agent.name}"
        ctk.CTkLabel(
            left_hdr, text=title_text,
            font=font_display(28),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_hdr, text="View and filter past commission transactions",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        if self.on_back:
            secondary_button(header, "Back", self.on_back, width=80).pack(side="right", pady=(4, 0))

        # ── Filter Card ──
        filter_card = card(self)
        filter_card.pack(fill="x", padx=30, pady=(16, 0))

        filter_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_inner.pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(
            filter_inner, text="FILTER BY AGENT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_MUTED'],
        ).pack(side="left", padx=(0, 12))

        self.filter_var = ctk.StringVar(value="All Agents")
        agents = self.db.get_active_agents()
        agent_names = ["All Agents"] + [a.name for a in agents]

        if self.agent:
            self.filter_var.set(self.agent.name)

        self.filter_dropdown = ctk.CTkComboBox(
            filter_inner, values=agent_names, variable=self.filter_var,
            width=280, height=36,
            font=font_body(13),
            corner_radius=8,
            border_width=1,
            border_color=c['CARD_BORDER'],
            button_color=c['PRIMARY'],
            button_hover_color=c['PRIMARY_HOVER'],
            command=self._on_filter_change,
            state="readonly",
        )
        self.filter_dropdown.pack(side="left")

        # ── Summary Bar ──
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=30, pady=(12, 0))

        self.summary_label = ctk.CTkLabel(
            self.summary_frame, text="",
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
        )
        self.summary_label.pack(anchor="w")

        # ── Table Area ──
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=30, pady=(8, 20))

    def refresh(self):
        c = get_colors()
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        filter_name = self.filter_var.get()

        if filter_name == "All Agents":
            self.transactions = self.db.get_all_transactions()
        else:
            agent = self.db.get_agent_by_name(filter_name)
            if agent:
                self.transactions = self.db.get_transactions_for_agent(agent.id)
            else:
                self.transactions = []

        if not self.transactions:
            empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            empty.pack(fill="x", pady=40)

            ctk.CTkLabel(
                empty, text="No transactions found",
                font=font_heading(16),
                text_color=c['TEXT_SECONDARY'],
            ).pack()

            ctk.CTkLabel(
                empty, text="Transactions will appear here after you generate invoices",
                font=font_body(12),
                text_color=c['TEXT_MUTED'],
            ).pack(pady=(4, 0))

            self.summary_label.configure(text="")
            return

        # ── Table Header ──
        headers = ["Invoice", "Agent", "Property", "Date", "Commission", "Office", "Agent", "Payout"]
        col_widths = [75, 110, 160, 80, 90, 80, 80, 85]

        hdr_frame = ctk.CTkFrame(self.table_frame, fg_color=c['SIDEBAR_BG'], corner_radius=8)
        hdr_frame.pack(fill="x", pady=(0, 4))

        for header, w in zip(headers, col_widths):
            ctk.CTkLabel(
                hdr_frame, text=header.upper(), width=w,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=c['TEXT_SECONDARY'],
            ).pack(side="left", padx=3, pady=8)

        # ── Data Rows ──
        total_office = 0
        total_agent_payout = 0

        for i, txn in enumerate(self.transactions):
            bg = c['CARD_BG'] if i % 2 == 0 else c['ROW_ALT']
            row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)

            property_display = txn.property_address
            if len(property_display) > 28:
                property_display = property_display[:28] + "..."

            values = [
                txn.invoice_number,
                txn.agent_name or "?",
                property_display,
                txn.closing_date,
                f"${txn.gross_commission:,.2f}",
                f"${txn.office_share:,.2f}",
                f"${txn.agent_share:,.2f}",
                f"${txn.total_payout:,.2f}",
            ]

            for val, w in zip(values, col_widths):
                ctk.CTkLabel(
                    row, text=val, width=w,
                    font=font_caption(11),
                    text_color=c['TEXT_PRIMARY'], anchor="w",
                ).pack(side="left", padx=3, pady=12)

            total_office += txn.office_share
            total_agent_payout += txn.total_payout

        # ── Summary ──
        self.summary_label.configure(
            text=f"{len(self.transactions)} transaction(s)  \u2022  "
                 f"Office Revenue: ${total_office:,.2f}  \u2022  "
                 f"Agent Payouts: ${total_agent_payout:,.2f}"
        )

    def _on_filter_change(self, value):
        self.refresh()
