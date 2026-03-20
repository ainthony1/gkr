import os
import customtkinter as ctk
from datetime import datetime, date
from core.commission_engine import get_cap_year
from ui.theme import (
    get_colors, font_display, font_heading, font_body, font_caption,
    font_label, card, section_label, font_mono,
)


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_go_invoices=None, on_go_taxes=None,
                 on_go_agents=None, on_go_cap_tracker=None):
        c = get_colors()
        super().__init__(parent, fg_color=c['CONTENT_BG'])
        self.db = db
        self.on_go_invoices = on_go_invoices
        self.on_go_taxes = on_go_taxes
        self.on_go_agents = on_go_agents
        self.on_go_cap_tracker = on_go_cap_tracker
        self._build()

    def _build(self):
        c = get_colors()
        today = date.today()

        scroll = ctk.CTkScrollableFrame(self, fg_color=c['CONTENT_BG'])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Welcome Header ──
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 0))

        greeting = "Good morning" if datetime.now().hour < 12 else (
            "Good afternoon" if datetime.now().hour < 17 else "Good evening"
        )

        ctk.CTkLabel(
            header, text=f"{greeting}!",
            font=font_display(28),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        date_time_row = ctk.CTkFrame(header, fg_color="transparent")
        date_time_row.pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            date_time_row, text=today.strftime("%A, %B %d, %Y"),
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(side="left")

        ctk.CTkLabel(
            date_time_row, text="  \u2022  ",
            font=font_body(13),
            text_color=c['TEXT_MUTED'],
        ).pack(side="left")

        self._clock_label = ctk.CTkLabel(
            date_time_row, text=datetime.now().strftime("%#I:%M %p") if os.name == 'nt' else datetime.now().strftime("%-I:%M %p"),
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        )
        self._clock_label.pack(side="left")
        self._update_clock()

        # ── Key Metrics ──
        agents = self.db.get_real_agents()
        agent_count = len(agents)
        current_year = today.year

        txns = self.db.get_real_transactions()
        ytd_txns = [t for t in txns if t.closing_date and t.closing_date.startswith(str(current_year))]
        ytd_gross = sum(t.gross_commission for t in ytd_txns)
        ytd_office = sum(t.office_share for t in ytd_txns)
        ytd_agent_payouts = sum(t.total_payout for t in ytd_txns)
        ytd_count = len(ytd_txns)

        # Count capped agents
        capped_count = 0
        for agent in agents:
            if agent.split_type == 'transaction_fee':
                continue
            cap_amount = agent.cap_amount if agent.cap_amount is not None else 0
            if cap_amount == 0:
                capped_count += 1
                continue
            year_start, year_end = get_cap_year(agent.contract_date, today)
            cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
            manual_adj = self.db.get_cap_adjustment(agent.id, year_start)
            if (cap_ptd + manual_adj) >= cap_amount:
                capped_count += 1

        metrics_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=28, pady=(20, 0))
        metrics_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="metric")

        metrics = [
            ("Gross Commissions", f"${ytd_gross:,.0f}", f"YTD {current_year}", c['PRIMARY']),
            ("Office Revenue", f"${ytd_office:,.0f}", f"YTD {current_year}", c['SUCCESS']),
            ("Transactions", str(ytd_count), f"YTD {current_year}", '#8B5CF6'),
            ("Agents Capped", str(capped_count), f"of {agent_count} agents", '#D97706'),
        ]

        for i, (label, value, sub, accent) in enumerate(metrics):
            self._metric_card(metrics_frame, label, value, sub, accent, i, c)

        # ── Quick Actions ──
        sl = section_label(scroll, "Quick Actions")
        sl.pack(fill="x", padx=28, pady=(24, 10), anchor="w")

        actions_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        actions_frame.pack(fill="x", padx=28, pady=(0, 8))
        actions_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="action")

        actions = [
            ("New Invoice", "Create a commission\ninvoice for an agent", c['PRIMARY'], self.on_go_invoices),
            ("Cap Tracker", "Check agent cap\nprogress at a glance", '#8B5CF6', self.on_go_cap_tracker),
            ("Tax Documents", "Generate 1099-NEC\nforms for agents", '#D97706', self.on_go_taxes),
            ("Manage Agents", "Add, edit, or update\nagent information", c['SUCCESS'], self.on_go_agents),
        ]

        for i, (title, desc, accent, cmd) in enumerate(actions):
            self._action_card(actions_frame, title, desc, accent, cmd, i, c)

        # ── Recent Transactions ──
        sl2 = section_label(scroll, "Recent Transactions")
        sl2.pack(fill="x", padx=28, pady=(16, 10), anchor="w")

        recent_txns = ytd_txns[:8]
        if recent_txns:
            # Table header
            table_header = ctk.CTkFrame(scroll, fg_color=c['SECTION_BG'], corner_radius=8, height=32)
            table_header.pack(fill="x", padx=28, pady=(0, 2))
            table_header.pack_propagate(False)

            th_inner = ctk.CTkFrame(table_header, fg_color="transparent")
            th_inner.pack(fill="both", expand=True, padx=16, pady=4)

            headers = [("Invoice", 90), ("Property", 200), ("Agent", 120),
                       ("Date", 80), ("Gross", 90), ("Agent Payout", 100)]
            for h_text, h_width in headers:
                ctk.CTkLabel(
                    th_inner, text=h_text.upper(),
                    font=ctk.CTkFont(size=9, weight="bold"),
                    text_color=c['TEXT_MUTED'],
                    width=h_width, anchor="w",
                ).pack(side="left")

            for idx, txn in enumerate(recent_txns):
                self._txn_row(scroll, txn, idx, c)
        else:
            empty_card = ctk.CTkFrame(scroll, fg_color=c['CARD_BG'], corner_radius=10,
                                       border_width=1, border_color=c['CARD_BORDER'])
            empty_card.pack(fill="x", padx=28, pady=(0, 10))

            ctk.CTkLabel(
                empty_card,
                text="No transactions yet this year. Create your first invoice to get started.",
                font=font_body(13), text_color=c['TEXT_SECONDARY'],
            ).pack(padx=24, pady=24)

        # Bottom spacer
        ctk.CTkFrame(scroll, fg_color="transparent", height=20).pack()

    def _update_clock(self):
        try:
            self._clock_label.configure(text=datetime.now().strftime("%#I:%M %p") if os.name == 'nt' else datetime.now().strftime("%-I:%M %p"))
            self.after(30000, self._update_clock)
        except Exception:
            pass

    def _metric_card(self, parent, title, value, subtitle, accent, col, c):
        frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=12,
                              border_width=1, border_color=c['CARD_BORDER'])
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0 if col == 0 else 5, 5 if col < 3 else 0), pady=0)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        # Accent line at top
        ctk.CTkFrame(inner, width=32, height=3, fg_color=accent,
                      corner_radius=2).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            inner, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", pady=(4, 2))

        ctk.CTkLabel(
            inner, text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color=c['TEXT_MUTED'],
        ).pack(anchor="w")

    def _action_card(self, parent, title, description, accent, callback, col, c):
        frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=12,
                              border_width=1, border_color=c['CARD_BORDER'])
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0 if col == 0 else 5, 5 if col < 3 else 0), pady=0)

        # Make entire card clickable
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        # Colored circle indicator
        ctk.CTkFrame(inner, width=8, height=8, fg_color=accent,
                      corner_radius=4).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=description,
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
            justify="left",
        ).pack(anchor="w", pady=(4, 10))

        if callback:
            ctk.CTkButton(
                inner, text="Open \u2192",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=accent,
                hover_color=c['PRIMARY_HOVER'] if accent == c['PRIMARY'] else accent,
                text_color='#FFFFFF', corner_radius=14,
                height=28, width=80,
                command=callback,
            ).pack(anchor="w")

    def _txn_row(self, parent, txn, idx, c):
        bg = c['CARD_BG'] if idx % 2 == 0 else c['ROW_ALT']
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, height=40)
        row.pack(fill="x", padx=28, pady=1)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=6)

        font = ctk.CTkFont(size=12)
        muted = c['TEXT_SECONDARY']
        primary = c['TEXT_PRIMARY']

        # Invoice number
        ctk.CTkLabel(inner, text=txn.invoice_number, font=font,
                      text_color=c['PRIMARY'], width=90, anchor="w").pack(side="left")

        # Address (truncated)
        addr = txn.property_address[:28] + "..." if len(txn.property_address) > 28 else txn.property_address
        ctk.CTkLabel(inner, text=addr, font=font,
                      text_color=primary, width=200, anchor="w").pack(side="left")

        # Agent name
        agent_name = txn.agent_name or ""
        ctk.CTkLabel(inner, text=agent_name, font=font,
                      text_color=muted, width=120, anchor="w").pack(side="left")

        # Date
        ctk.CTkLabel(inner, text=txn.closing_date, font=ctk.CTkFont(size=11),
                      text_color=muted, width=80, anchor="w").pack(side="left")

        # Gross
        ctk.CTkLabel(inner, text=f"${txn.gross_commission:,.0f}",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color=primary, width=90, anchor="w").pack(side="left")

        # Agent payout
        ctk.CTkLabel(inner, text=f"${txn.total_payout:,.0f}",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color=c['SUCCESS'], width=100, anchor="w").pack(side="left")
