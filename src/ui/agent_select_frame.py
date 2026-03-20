import customtkinter as ctk
from ui.theme import (
    get_colors, page_title, section_label, card, primary_button, secondary_button,
    stat_block, separator, badge, font_display, font_heading,
    font_subheading, font_body, font_caption,
)


class AgentSelectFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_new_transaction, on_view_history):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_new_transaction = on_new_transaction
        self.on_view_history = on_view_history
        self.selected_agent = None
        self.agents = []

        self._build_ui()
        self.refresh_agents()

    def _build_ui(self):
        c = get_colors()
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Page Header ──
        header_area = ctk.CTkFrame(scroll, fg_color="transparent")
        header_area.pack(fill="x", padx=30, pady=(28, 0))

        title = ctk.CTkLabel(
            header_area, text="Invoices",
            font=font_display(24),
            text_color=c['TEXT_PRIMARY'],
        )
        title.pack(anchor="w")

        ctk.CTkLabel(
            header_area, text="Select an agent to begin a new transaction",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        # ── Agent Selector Card ──
        selector_card = card(scroll)
        selector_card.pack(fill="x", padx=30, pady=(20, 0))

        selector_inner = ctk.CTkFrame(selector_card, fg_color="transparent")
        selector_inner.pack(fill="x", padx=24, pady=20)

        # Label row
        label_row = ctk.CTkFrame(selector_inner, fg_color="transparent")
        label_row.pack(fill="x", pady=(0, 8))

        sl = section_label(label_row, "Select Agent")
        sl.pack(side="left")

        # Dropdown
        self.agent_var = ctk.StringVar(value="Choose an agent...")
        self.agent_dropdown = ctk.CTkComboBox(
            selector_inner,
            variable=self.agent_var,
            values=["Choose an agent..."],
            width=380,
            height=40,
            font=font_body(14),
            dropdown_font=font_body(13),
            corner_radius=8,
            border_width=1,
            border_color=c['CARD_BORDER'],
            button_color=c['PRIMARY'],
            button_hover_color=c['PRIMARY_HOVER'],
            command=self._on_agent_selected,
            state="readonly",
        )
        self.agent_dropdown.pack(anchor="w")

        # ── Agent Detail Card ──
        self.detail_card = card(scroll)
        self.detail_card.pack(fill="x", padx=30, pady=(16, 0))

        self.detail_inner = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        self.detail_inner.pack(fill="x", padx=24, pady=20)

        # Empty state
        self.empty_state = ctk.CTkFrame(self.detail_inner, fg_color="transparent")
        self.empty_state.pack(fill="x")

        ctk.CTkLabel(
            self.empty_state,
            text="No agent selected",
            font=font_heading(14),
            text_color=c['TEXT_SECONDARY'],
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self.empty_state,
            text="Choose an agent from the dropdown above to view their details",
            font=font_body(12),
            text_color=c['TEXT_MUTED'],
        ).pack(pady=(0, 20))

        # Agent info (hidden initially)
        self.info_frame = ctk.CTkFrame(self.detail_inner, fg_color="transparent")

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(20, 30))

        self.new_txn_btn = primary_button(
            btn_frame, "New Transaction", self._start_new_transaction, width=200,
        )
        self.new_txn_btn.configure(state="disabled")
        self.new_txn_btn.pack(side="left", padx=(0, 12))

        self.history_btn = secondary_button(
            btn_frame, "View History", self._view_history, width=160,
        )
        self.history_btn.configure(state="disabled")
        self.history_btn.pack(side="left")

    def refresh_agents(self):
        self.agents = self.db.get_active_agents()
        names = [f"{a.name}  [TEST]" if a.is_test else a.name for a in self.agents]
        self.agent_dropdown.configure(values=["Choose an agent..."] + names)
        self.agent_var.set("Choose an agent...")
        self.selected_agent = None
        self.new_txn_btn.configure(state="disabled")
        self.history_btn.configure(state="disabled")

    def _on_agent_selected(self, name):
        if name == "Choose an agent...":
            self.selected_agent = None
            self._show_empty_state()
            self.new_txn_btn.configure(state="disabled")
            self.history_btn.configure(state="disabled")
            return

        clean_name = name.replace("  [TEST]", "")
        agent = self.db.get_agent_by_name(clean_name)
        if not agent:
            return
        self.selected_agent = agent
        self.new_txn_btn.configure(state="normal")
        self.history_btn.configure(state="normal")
        self._show_agent_info(agent)

    def _show_empty_state(self):
        self.info_frame.pack_forget()
        self.empty_state.pack(fill="x")

    def _show_agent_info(self, agent):
        c = get_colors()
        self.empty_state.pack_forget()

        # Clear previous info
        for w in self.info_frame.winfo_children():
            w.destroy()

        self.info_frame.pack(fill="x")

        from core.commission_engine import get_cap_year
        from datetime import date
        today = date.today()

        # ── Agent Header Row ──
        header_row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            header_row, text=agent.name,
            font=font_heading(16),
            text_color=c['TEXT_PRIMARY'],
        ).pack(side="left")

        # Split type badge
        if agent.split_type == 'transaction_fee':
            type_text = f"TXN FEE  ${agent.transaction_fee:,.0f}"
        elif agent.split_type == 'tiered':
            type_text = "TIERED"
        else:
            type_text = f"{agent.agent_split_pct:.0f}/{agent.office_split_pct:.0f} SPLIT"

        badge(header_row, type_text, color=c['PRIMARY']).pack(side="left", padx=(12, 0))

        # ── Separator ──
        separator(self.info_frame).pack(fill="x", pady=(0, 16))

        # ── Stats Row ──
        stats_row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 12))

        # Cap info
        if agent.split_type == 'transaction_fee':
            cap_display = "N/A"
            ptd_display = "N/A"
            remaining_display = "N/A"
        elif agent.cap_amount == 0:
            cap_display = "CAPPED"
            ptd_display = "---"
            remaining_display = "$0"
        elif agent.cap_amount and agent.cap_amount > 0:
            year_start, year_end = get_cap_year(agent.contract_date, today)
            cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
            remaining = max(0, agent.cap_amount - cap_ptd)
            cap_display = f"${agent.cap_amount:,.0f}"
            ptd_display = f"${cap_ptd:,.2f}"
            remaining_display = f"${remaining:,.2f}"
        else:
            cap_display = "Not Set"
            ptd_display = "---"
            remaining_display = "---"

        txn_count = len(self.db.get_transactions_for_agent(agent.id))

        stats = [
            ("Cap Amount", cap_display),
            ("Paid to Date", ptd_display),
            ("Remaining", remaining_display),
            ("Transactions", str(txn_count)),
        ]

        for label, value in stats:
            s = stat_block(stats_row, label, value, c['TEXT_PRIMARY'])
            s.pack(side="left", padx=(0, 40))

        # ── Additional Details ──
        details_frame = ctk.CTkFrame(self.info_frame, fg_color=c['SECTION_BG'], corner_radius=8)
        details_frame.pack(fill="x", pady=(4, 0))

        details_inner = ctk.CTkFrame(details_frame, fg_color="transparent")
        details_inner.pack(padx=16, pady=12)

        detail_items = []
        if agent.contract_date:
            detail_items.append(f"Contract: {agent.contract_date}")
        else:
            detail_items.append("Contract: Not Set (calendar year)")

        if agent.cap_amount and agent.cap_amount > 0 and agent.split_type != 'transaction_fee':
            year_start, year_end = get_cap_year(agent.contract_date, today)
            detail_items.append(f"Cap Year: {year_start} to {year_end}")

        if agent.cap_amount == 0 and agent.split_type != 'transaction_fee':
            detail_items.append("Status: Perpetually Capped (100% to agent)")

        ctk.CTkLabel(
            details_inner,
            text="  \u2022  ".join(detail_items),
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w")

        # ── Cap Progress Bar ──
        if (agent.cap_amount and agent.cap_amount > 0
                and agent.split_type != 'transaction_fee'):
            year_start, year_end = get_cap_year(agent.contract_date, today)
            cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
            progress = min(1.0, cap_ptd / agent.cap_amount)

            bar_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
            bar_frame.pack(fill="x", pady=(12, 0))

            ctk.CTkLabel(
                bar_frame,
                text=f"Cap Progress  \u2014  {progress:.0%}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=c['TEXT_MUTED'],
            ).pack(anchor="w", pady=(0, 4))

            bar = ctk.CTkProgressBar(
                bar_frame, width=500, height=8,
                progress_color=c['PRIMARY'],
                fg_color=c['CARD_BORDER'],
                corner_radius=4,
            )
            bar.set(progress)
            bar.pack(anchor="w")

    def _start_new_transaction(self):
        if self.selected_agent:
            self.on_new_transaction(self.selected_agent)

    def _view_history(self):
        if self.selected_agent:
            self.on_view_history(self.selected_agent)
