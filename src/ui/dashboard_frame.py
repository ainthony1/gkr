import customtkinter as ctk
from datetime import datetime
from ui.theme import (
    get_colors, font_display, font_heading, font_body, font_caption,
    card, primary_button, section_label,
)


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_go_invoices=None, on_go_taxes=None, on_go_agents=None):
        c = get_colors()
        super().__init__(parent, fg_color=c['CONTENT_BG'])
        self.db = db
        self.on_go_invoices = on_go_invoices
        self.on_go_taxes = on_go_taxes
        self.on_go_agents = on_go_agents
        self._build()

    def _build(self):
        c = get_colors()

        scroll = ctk.CTkScrollableFrame(self, fg_color=c['CONTENT_BG'])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(
            header, text="Dashboard",
            font=font_display(24),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Overview of your commission tracking",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        # Stats cards row
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", padx=24, pady=(20, 0))
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="stat")

        agents = self.db.get_real_agents()
        agent_count = len(agents)

        current_year = datetime.now().year
        txns = self.db.get_real_transactions()
        ytd_total = sum(
            t.gross_commission for t in txns
            if t.closing_date and t.closing_date.startswith(str(current_year))
        )

        previous_year = current_year - 1
        tax_records = self.db.get_tax_records_for_year(previous_year)
        test_agent_ids = {a.id for a in self.db.get_active_agents() if a.is_test}
        pending_1099 = sum(
            1 for r in tax_records
            if r.agent_id not in test_agent_ids
            and (r.total_compensation + r.manual_adjustment) >= 600 and not r.filed
        )
        pending_label = f"{pending_1099} pending" if pending_1099 > 0 else "All filed"

        self._stat_card(stats_frame, "Active Agents", str(agent_count), c['PRIMARY'], 0, c)
        self._stat_card(stats_frame, f"Gross Commissions {current_year}", f"${ytd_total:,.2f}", c['SUCCESS'], 1, c)
        self._stat_card(stats_frame, f"1099s ({previous_year})", pending_label,
                        '#D97706' if pending_1099 > 0 else c['SUCCESS'], 2, c)

        # Quick actions
        sl = section_label(scroll, "Quick Actions")
        sl.pack(fill="x", padx=24, pady=(24, 8), anchor="w")

        actions_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_frame.pack(fill="x", padx=24, pady=(0, 16))
        actions_frame.columnconfigure((0, 1, 2), weight=1, uniform="action")

        self._action_card(actions_frame, "New Invoice",
                          "Create a commission invoice for an agent",
                          "Go to Invoices", self.on_go_invoices, 0, c)
        self._action_card(actions_frame, "Tax Documents",
                          "Generate 1099-NEC forms for filing",
                          "Go to Taxes", self.on_go_taxes, 1, c)
        self._action_card(actions_frame, "Manage Agents",
                          "Add, edit, or update agent information",
                          "Go to Agents", self.on_go_agents, 2, c)

        # Recent transactions
        sl2 = section_label(scroll, "Recent Transactions")
        sl2.pack(fill="x", padx=24, pady=(8, 8), anchor="w")

        recent_txns = txns[:5]
        if recent_txns:
            for txn in recent_txns:
                self._txn_row(scroll, txn, c)
        else:
            empty_card = ctk.CTkFrame(scroll, fg_color=c['CARD_BG'], corner_radius=10,
                                       border_width=1, border_color=c['CARD_BORDER'])
            empty_card.pack(fill="x", padx=24, pady=(0, 10))
            ctk.CTkLabel(
                empty_card, text="No transactions yet. Create your first invoice to get started.",
                font=font_body(13), text_color=c['TEXT_SECONDARY'],
            ).pack(padx=20, pady=20)

    def _stat_card(self, parent, title, value, accent_color, col, c):
        card_frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=10,
                                   border_width=1, border_color=c['CARD_BORDER'])
        card_frame.grid(row=0, column=col, sticky="nsew",
                        padx=(0 if col == 0 else 6, 0 if col == 2 else 6), pady=0)

        # Accent bar
        ctk.CTkFrame(card_frame, width=4, height=36, fg_color=accent_color,
                      corner_radius=2).place(x=12, y=14)

        ctk.CTkLabel(
            card_frame, text=title,
            font=font_caption(11), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", padx=(28, 16), pady=(14, 0))

        ctk.CTkLabel(
            card_frame, text=value,
            font=ctk.CTkFont(size=20, weight="bold"), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", padx=(28, 16), pady=(2, 14))

    def _action_card(self, parent, title, description, button_text, callback, col, c):
        card_frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=10,
                                   border_width=1, border_color=c['CARD_BORDER'])
        card_frame.grid(row=0, column=col, sticky="nsew",
                        padx=(0 if col == 0 else 6, 0 if col == 2 else 6), pady=0)

        ctk.CTkLabel(
            card_frame, text=title,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", padx=20, pady=(18, 2))

        ctk.CTkLabel(
            card_frame, text=description,
            font=font_caption(12), text_color=c['TEXT_SECONDARY'],
            wraplength=200,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        if callback:
            ctk.CTkButton(
                card_frame, text=button_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=c['PRIMARY'], hover_color=c['PRIMARY_HOVER'],
                text_color='#FFFFFF', corner_radius=17,
                height=32, width=130,
                command=callback,
            ).pack(anchor="w", padx=20, pady=(0, 18))

    def _txn_row(self, parent, txn, c):
        row = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=8,
                           border_width=1, border_color=c['CARD_BORDER'], height=46)
        row.pack(fill="x", padx=24, pady=(0, 3))
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=6)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left, text=f"{txn.invoice_number}  \u2022  {txn.property_address}",
            font=font_body(12), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        agent_name = txn.agent_name or ""
        ctk.CTkLabel(
            left, text=f"{agent_name}  \u2022  {txn.closing_date}",
            font=font_caption(10), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=f"${txn.gross_commission:,.2f}",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=c['TEXT_PRIMARY'],
        ).pack(side="right", anchor="e")
