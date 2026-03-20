import customtkinter as ctk
from datetime import date
from tkinter import messagebox
from core.commission_engine import get_cap_year
from ui.theme import (
    get_colors, font_display, font_heading, font_body, font_caption,
    font_label, card, section_label, badge,
)


class CapTrackerFrame(ctk.CTkFrame):
    def __init__(self, parent, db):
        c = get_colors()
        super().__init__(parent, fg_color=c['CONTENT_BG'])
        self.db = db
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_cards())
        self._agent_cards = []
        self._build()

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._agent_cards = []
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter_cards())
        self._build()

    def _build(self):
        c = get_colors()
        today = date.today()

        scroll = ctk.CTkScrollableFrame(self, fg_color=c['CONTENT_BG'])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        self._scroll = scroll

        # Header row
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 0))

        ctk.CTkLabel(
            header, text="Cap Tracker",
            font=font_display(26),
            text_color=c['TEXT_PRIMARY'],
        ).pack(side="left", anchor="w")

        # Search bar
        self._search_entry = ctk.CTkEntry(
            header, width=240, height=36,
            placeholder_text="Search agents...",
            font=font_body(13),
            corner_radius=18,
            border_width=1,
            border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'],
            textvariable=self._search_var,
        )
        self._search_entry.pack(side="right")

        # Gather agent data
        agents = self.db.get_real_agents()
        cap_agents = []
        fee_agents = []
        capped_count = 0
        total_office_cap_revenue = 0.0

        for agent in agents:
            if agent.split_type == 'transaction_fee':
                fee_agents.append(agent)
                continue

            year_start, year_end = get_cap_year(agent.contract_date, today)
            cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
            manual_adj = self.db.get_cap_adjustment(agent.id, year_start)
            adj_note = self.db.get_cap_adjustment_note(agent.id, year_start)
            effective_ptd = cap_ptd + manual_adj
            txn_count = self.db.get_txn_count_in_period(agent.id, year_start, year_end)
            cap_amount = agent.cap_amount if agent.cap_amount is not None else 0

            is_zero_cap = cap_amount == 0
            is_capped = is_zero_cap or (cap_amount > 0 and effective_ptd >= cap_amount)
            if is_capped:
                capped_count += 1

            total_office_cap_revenue += effective_ptd

            cap_agents.append({
                'agent': agent,
                'cap_amount': cap_amount,
                'cap_ptd': cap_ptd,
                'manual_adj': manual_adj,
                'adj_note': adj_note,
                'effective_ptd': effective_ptd,
                'txn_count': txn_count,
                'year_start': year_start,
                'year_end': year_end,
                'is_zero_cap': is_zero_cap,
                'is_capped': is_capped,
            })

        # Sort: uncapped first (by progress desc), then capped
        cap_agents.sort(key=lambda x: (x['is_capped'], -(x['effective_ptd'] / max(x['cap_amount'], 1))))

        # Summary stats
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", padx=28, pady=(20, 0))
        stats_frame.columnconfigure((0, 1, 2), weight=1, uniform="stat")

        self._summary_stat(stats_frame, "Tracked Agents", str(len(cap_agents)),
                           c['PRIMARY'], 0, c)
        self._summary_stat(stats_frame, "Agents Capped", str(capped_count),
                           c['SUCCESS'] if capped_count > 0 else c['TEXT_MUTED'], 1, c)
        self._summary_stat(stats_frame, "Office Cap Revenue",
                           f"${total_office_cap_revenue:,.0f}",
                           '#D97706', 2, c)

        # Agent cards section
        sl = section_label(scroll, "Agent Cap Progress")
        sl.pack(fill="x", padx=28, pady=(24, 12), anchor="w")

        cards_container = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_container.pack(fill="x", padx=28, pady=(0, 8))
        cards_container.columnconfigure((0, 1), weight=1, uniform="agentcard")

        self._agent_cards = []
        row = 0
        col = 0
        for data in cap_agents:
            card_frame = self._agent_cap_card(cards_container, data, c)
            card_frame.grid(row=row, column=col, sticky="nsew",
                           padx=(0 if col == 0 else 6, 6 if col == 0 else 0),
                           pady=6)
            self._agent_cards.append((data['agent'], card_frame))
            col += 1
            if col > 1:
                col = 0
                row += 1

        # Transaction fee agents
        if fee_agents:
            sl2 = section_label(scroll, "Flat Fee Agents (No Cap)")
            sl2.pack(fill="x", padx=28, pady=(16, 8), anchor="w")

            fee_container = ctk.CTkFrame(scroll, fg_color="transparent")
            fee_container.pack(fill="x", padx=28, pady=(0, 20))

            for agent in fee_agents:
                fee_row = self._fee_agent_row(fee_container, agent, today, c)
                fee_row.pack(fill="x", pady=2)
                self._agent_cards.append((agent, fee_row))

    def _summary_stat(self, parent, title, value, accent, col, c):
        frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=12,
                              border_width=1, border_color=c['CARD_BORDER'])
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0 if col == 0 else 6, 0 if col == 2 else 6), pady=0)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        dot_frame = ctk.CTkFrame(inner, fg_color="transparent")
        dot_frame.pack(anchor="w")
        ctk.CTkFrame(dot_frame, width=8, height=8, fg_color=accent,
                      corner_radius=4).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            dot_frame, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_SECONDARY'],
        ).pack(side="left")

        ctk.CTkLabel(
            inner, text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", pady=(6, 0))

    def _agent_cap_card(self, parent, data, c):
        agent = data['agent']
        cap_amount = data['cap_amount']
        effective_ptd = data['effective_ptd']
        manual_adj = data['manual_adj']
        adj_note = data['adj_note']
        is_zero_cap = data['is_zero_cap']
        is_capped = data['is_capped']
        txn_count = data['txn_count']
        year_start = data['year_start']
        year_end = data['year_end']

        frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=12,
                              border_width=1, border_color=c['CARD_BORDER'])

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        # Top row: name + badge + edit button
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top, text=agent.name,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        ).pack(side="left", anchor="w")

        # Edit button
        edit_btn = ctk.CTkButton(
            top, text="Edit",
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=c['SECTION_BG'],
            text_color=c['PRIMARY'],
            border_width=1,
            border_color=c['PRIMARY'],
            width=44, height=22, corner_radius=11,
            command=lambda a=agent, ys=year_start, ye=year_end, adj=manual_adj, note=adj_note:
                self._show_edit_dialog(a, ys, ye, adj, note),
        )
        edit_btn.pack(side="right", padx=(6, 0))

        # Status badge
        if is_zero_cap:
            badge_text, badge_color = "No Cap", c['TEXT_MUTED']
        elif is_capped:
            badge_text, badge_color = "CAPPED", c['SUCCESS']
        else:
            badge_text, badge_color = "Active", c['PRIMARY']

        ctk.CTkLabel(
            top, text=f"  {badge_text}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color='#FFFFFF',
            fg_color=badge_color,
            corner_radius=10,
            height=22,
        ).pack(side="right")

        # Split type
        if agent.split_type == 'percentage':
            split_text = f"{agent.agent_split_pct:.0f}/{agent.office_split_pct:.0f} Split"
        elif agent.split_type == 'tiered':
            split_text = "Tiered Split"
        else:
            split_text = "Flat Fee"

        ctk.CTkLabel(
            inner, text=split_text,
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        if is_zero_cap:
            ctk.CTkLabel(
                inner, text="Perpetually capped \u2014 agent keeps 100%",
                font=font_body(12),
                text_color=c['TEXT_MUTED'],
            ).pack(anchor="w", pady=(10, 0))
            ctk.CTkLabel(
                inner, text=f"{txn_count} transaction{'s' if txn_count != 1 else ''} this period",
                font=font_caption(11),
                text_color=c['TEXT_SECONDARY'],
            ).pack(anchor="w", pady=(4, 0))
        else:
            progress_pct = min(effective_ptd / cap_amount, 1.0) if cap_amount > 0 else 0
            pct_display = int(progress_pct * 100)

            # Amount row
            amt_frame = ctk.CTkFrame(inner, fg_color="transparent")
            amt_frame.pack(fill="x", pady=(10, 4))

            ctk.CTkLabel(
                amt_frame, text=f"${effective_ptd:,.0f}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=c['SUCCESS'] if is_capped else c['TEXT_PRIMARY'],
            ).pack(side="left")

            ctk.CTkLabel(
                amt_frame, text=f"of ${cap_amount:,.0f}",
                font=font_body(13),
                text_color=c['TEXT_SECONDARY'],
            ).pack(side="left", padx=(4, 0))

            ctk.CTkLabel(
                amt_frame, text=f"{pct_display}%",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=c['SUCCESS'] if is_capped else c['PRIMARY'],
            ).pack(side="right")

            # Progress bar
            bar_bg = ctk.CTkFrame(inner, height=10, fg_color=c['SECTION_BG'],
                                   corner_radius=5)
            bar_bg.pack(fill="x", pady=(0, 6))

            bar_color = c['SUCCESS'] if is_capped else c['PRIMARY']
            bar_fill = ctk.CTkFrame(bar_bg, height=10, fg_color=bar_color,
                                     corner_radius=5)
            bar_fill.place(relx=0, rely=0, relwidth=max(progress_pct, 0.02), relheight=1.0)

            # Bottom stats
            stats = ctk.CTkFrame(inner, fg_color="transparent")
            stats.pack(fill="x")

            remaining = max(cap_amount - effective_ptd, 0)
            ctk.CTkLabel(
                stats,
                text=f"${remaining:,.0f} remaining" if not is_capped else "Cap reached!",
                font=font_caption(11),
                text_color=c['SUCCESS'] if is_capped else c['TEXT_SECONDARY'],
            ).pack(side="left")

            ctk.CTkLabel(
                stats, text=f"{txn_count} txn{'s' if txn_count != 1 else ''}",
                font=font_caption(11),
                text_color=c['TEXT_SECONDARY'],
            ).pack(side="right")

            # Manual adjustment indicator
            if manual_adj != 0:
                adj_text = f"Manual adjustment: ${manual_adj:+,.0f}"
                if adj_note:
                    adj_text += f" \u2014 {adj_note}"
                ctk.CTkLabel(
                    inner, text=adj_text,
                    font=ctk.CTkFont(size=10, slant="italic"),
                    text_color='#D97706',
                ).pack(anchor="w", pady=(4, 0))

        # Cap year period
        ctk.CTkLabel(
            inner,
            text=f"Cap year: {year_start} to {year_end}",
            font=ctk.CTkFont(size=10),
            text_color=c['TEXT_MUTED'],
        ).pack(anchor="w", pady=(6, 0))

        return frame

    def _fee_agent_row(self, parent, agent, today, c):
        frame = ctk.CTkFrame(parent, fg_color=c['CARD_BG'], corner_radius=8,
                              border_width=1, border_color=c['CARD_BORDER'], height=44)
        frame.pack_propagate(False)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=6)

        ctk.CTkLabel(
            inner, text=agent.name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        ).pack(side="left")

        fee_text = f"${agent.transaction_fee:,.0f}/txn" if agent.transaction_fee else "Flat Fee"
        ctk.CTkLabel(
            inner, text=fee_text,
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
        ).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            inner, text="N/A",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_MUTED'],
            fg_color=c['SECTION_BG'],
            corner_radius=8,
            height=20,
            width=40,
        ).pack(side="right")

        return frame

    def _show_edit_dialog(self, agent, year_start, year_end, current_adj, current_note):
        c = get_colors()

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Cap \u2014 {agent.name}")
        dialog.geometry("420x320")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - 210
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - 160
        dialog.geometry(f"+{x}+{y}")

        content = ctk.CTkFrame(dialog, fg_color=c['CONTENT_BG'])
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content, text=f"Adjust Cap for {agent.name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            content,
            text=f"Cap year: {year_start} to {year_end}",
            font=font_caption(11),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 12))

        # Current cap info
        cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
        cap_amount = agent.cap_amount or 0
        ctk.CTkLabel(
            content,
            text=f"From transactions: ${cap_ptd:,.2f}  |  Cap: ${cap_amount:,.0f}",
            font=font_body(12),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 10))

        # Manual adjustment field
        ctk.CTkLabel(
            content, text="Manual Adjustment ($)",
            font=font_label(12),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 4))

        adj_entry = ctk.CTkEntry(
            content, width=200, height=36,
            font=font_body(13),
            corner_radius=8,
            border_width=1,
            border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'],
            placeholder_text="e.g. 5000 or -2000",
        )
        adj_entry.pack(anchor="w")
        if current_adj != 0:
            adj_entry.insert(0, str(current_adj))

        ctk.CTkLabel(
            content,
            text="Positive = add to paid, Negative = subtract from paid",
            font=ctk.CTkFont(size=10),
            text_color=c['TEXT_MUTED'],
        ).pack(anchor="w", pady=(2, 8))

        # Note field
        ctk.CTkLabel(
            content, text="Note (optional)",
            font=font_label(12),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 4))

        note_entry = ctk.CTkEntry(
            content, width=360, height=36,
            font=font_body(13),
            corner_radius=8,
            border_width=1,
            border_color=c['INPUT_BORDER'],
            fg_color=c['CARD_BG'],
            placeholder_text="Reason for adjustment...",
        )
        note_entry.pack(anchor="w")
        if current_note:
            note_entry.insert(0, current_note)

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(16, 0))

        def save():
            try:
                adj_text = adj_entry.get().strip()
                adj_val = float(adj_text) if adj_text else 0.0
            except ValueError:
                messagebox.showerror("Invalid", "Please enter a valid number for the adjustment.")
                return
            note_val = note_entry.get().strip()
            self.db.upsert_cap_adjustment(agent.id, year_start, year_end, adj_val, note_val)
            dialog.destroy()
            self.refresh()

        def clear():
            self.db.upsert_cap_adjustment(agent.id, year_start, year_end, 0.0, "")
            dialog.destroy()
            self.refresh()

        ctk.CTkButton(
            btn_frame, text="Save",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c['PRIMARY'], hover_color=c['PRIMARY_HOVER'],
            text_color='#FFFFFF', height=34, width=100, corner_radius=17,
            command=save,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Clear",
            font=font_body(12),
            fg_color="transparent", hover_color=c['SECTION_BG'],
            text_color=c['DANGER'], border_width=1, border_color=c['DANGER'],
            height=32, width=80, corner_radius=16,
            command=clear,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Cancel",
            font=font_body(12),
            fg_color="transparent", hover_color=c['SECTION_BG'],
            text_color=c['TEXT_SECONDARY'],
            height=32, width=80, corner_radius=16,
            command=dialog.destroy,
        ).pack(side="right", padx=(0, 8))

    def _filter_cards(self):
        query = self._search_var.get().lower().strip()
        for agent, card_frame in self._agent_cards:
            if query == "" or query in agent.name.lower():
                try:
                    card_frame.grid()
                except Exception:
                    try:
                        card_frame.pack(fill="x", pady=2)
                    except Exception:
                        pass
            else:
                if card_frame.winfo_manager() == "grid":
                    card_frame.grid_remove()
                elif card_frame.winfo_manager() == "pack":
                    card_frame.pack_forget()
