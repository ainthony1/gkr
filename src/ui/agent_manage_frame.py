import json
import customtkinter as ctk
from tkinter import messagebox
from ui.theme import (
    get_colors, section_label, card, success_button, primary_button,
    secondary_button, danger_button, separator, badge,
    font_display, font_heading, font_subheading, font_body, font_caption,
)


class AgentManageFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_back=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_back = on_back
        self.selected_agent = None

        self._build_ui()

    def _build_ui(self):
        c = get_colors()
        # ── Page Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(28, 0))

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")

        ctk.CTkLabel(
            left_hdr, text="Manage Agents",
            font=font_display(24),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_hdr, text="Edit agent profiles, commission structures, and cap settings",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        success_button(
            header, "+ Add Agent", self._add_new_agent, width=140,
        ).pack(side="right", pady=(4, 0))

        # ── Agent Picker Card ──
        picker_card = card(self)
        picker_card.pack(fill="x", padx=30, pady=(16, 0))

        picker_inner = ctk.CTkFrame(picker_card, fg_color="transparent")
        picker_inner.pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(
            picker_inner, text="SELECT AGENT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_MUTED'],
        ).pack(side="left", padx=(0, 12))

        self.agents = self.db.get_all_agents()
        names = [f"{'[X] ' if not a.is_active else ''}{'[TEST] ' if a.is_test else ''}{a.name}" for a in self.agents]
        self.agent_var = ctk.StringVar(value="Choose an agent...")
        self.agent_dropdown = ctk.CTkComboBox(
            picker_inner, values=["Choose an agent..."] + names,
            variable=self.agent_var, width=320, height=36,
            font=font_body(13),
            corner_radius=8,
            border_width=1,
            border_color=c['CARD_BORDER'],
            button_color=c['PRIMARY'],
            button_hover_color=c['PRIMARY_HOVER'],
            command=self._on_agent_selected, state="readonly",
        )
        self.agent_dropdown.pack(side="left")

        # ── Scrollable Edit Form ──
        self.form_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.form_scroll.pack(fill="both", expand=True, padx=30, pady=(12, 20))

        # Empty state
        self.placeholder = ctk.CTkFrame(self.form_scroll, fg_color="transparent")
        self.placeholder.pack(fill="x", pady=40)

        ctk.CTkLabel(
            self.placeholder, text="No agent selected",
            font=font_heading(16),
            text_color=c['TEXT_SECONDARY'],
        ).pack()

        ctk.CTkLabel(
            self.placeholder, text="Choose an agent from the dropdown to edit their profile",
            font=font_body(12),
            text_color=c['TEXT_MUTED'],
        ).pack(pady=(4, 0))

        self.form_widgets = []

    def _on_agent_selected(self, display_name):
        if display_name == "Choose an agent...":
            self.selected_agent = None
            return

        clean_name = display_name.replace("[X] ", "").replace("[TEST] ", "")
        agent = self.db.get_agent_by_name(clean_name)
        if not agent:
            return
        self.selected_agent = agent
        self._build_edit_form()

    def _styled_entry(self, parent, label, default="", width=350, placeholder=""):
        c = get_colors()
        ctk.CTkLabel(parent, text=label, font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(8, 4))
        entry = ctk.CTkEntry(
            parent, width=width, height=38,
            font=font_body(13),
            corner_radius=8,
            border_width=1,
            border_color=c['CARD_BORDER'],
            fg_color=c['CARD_BG'],
            placeholder_text=placeholder,
        )
        entry.insert(0, default)
        entry.pack(anchor="w")
        return entry

    def _build_edit_form(self):
        c = get_colors()
        for w in self.form_scroll.winfo_children():
            w.destroy()
        self.form_widgets = []

        agent = self.selected_agent
        if not agent:
            return

        form = self.form_scroll

        # ── Tab Bar ──
        tab_bar = ctk.CTkFrame(form, fg_color="transparent")
        tab_bar.pack(fill="x", pady=(0, 0))

        self._current_tab = "profile"
        self.tab_buttons = {}
        self.tab_underlines = {}

        for tab_name, tab_label in [("profile", "Profile"), ("tax_info", "Tax Info")]:
            tab_wrapper = ctk.CTkFrame(tab_bar, fg_color="transparent")
            tab_wrapper.pack(side="left", padx=(0, 4))

            is_active = (tab_name == "profile")
            btn = ctk.CTkButton(
                tab_wrapper, text=tab_label, width=100, height=32,
                font=font_subheading(13),
                fg_color="transparent",
                text_color=c['PRIMARY'] if is_active else c['TEXT_SECONDARY'],
                hover_color=c['SECTION_BG'],
                corner_radius=0,
                command=lambda t=tab_name: self._switch_tab(t),
            )
            btn.pack()

            underline = ctk.CTkFrame(
                tab_wrapper, height=2,
                fg_color=c['PRIMARY'] if is_active else "transparent",
            )
            underline.pack(fill="x")

            self.tab_buttons[tab_name] = btn
            self.tab_underlines[tab_name] = underline

        # Divider line below tabs
        ctk.CTkFrame(form, height=1, fg_color=c['CARD_BORDER']).pack(fill="x", pady=(0, 12))

        self.tab_content_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.tab_content_frame.pack(fill="both", expand=True)

        self._build_profile_tab()

    def _switch_tab(self, tab_name):
        c = get_colors()
        self._current_tab = tab_name
        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.configure(text_color=c['PRIMARY'])
                self.tab_underlines[name].configure(fg_color=c['PRIMARY'])
            else:
                btn.configure(text_color=c['TEXT_SECONDARY'])
                self.tab_underlines[name].configure(fg_color="transparent")

        for w in self.tab_content_frame.winfo_children():
            w.destroy()

        if tab_name == "profile":
            self._build_profile_tab()
        elif tab_name == "tax_info":
            self._build_tax_info_tab()

    def _build_profile_tab(self):
        c = get_colors()
        agent = self.selected_agent
        if not agent:
            return

        form = self.tab_content_frame

        # ── Basic Info Card ──
        basic_card = card(form)
        basic_card.pack(fill="x", pady=(0, 12))

        basic_inner = ctk.CTkFrame(basic_card, fg_color="transparent")
        basic_inner.pack(fill="x", padx=24, pady=20)

        sl = section_label(basic_inner, "Basic Info")
        sl.pack(anchor="w", pady=(0, 4))

        self.name_entry = self._styled_entry(basic_inner, "Name", agent.name)
        self.license_entry = self._styled_entry(basic_inner, "License Number", agent.license_number or "")
        self.license_exp_entry = self._styled_entry(basic_inner, "License Expiration (YYYY-MM-DD)", agent.license_expiration or "", placeholder="2026-12-31")
        self.contract_entry = self._styled_entry(basic_inner, "Contract Date (YYYY-MM-DD)", agent.contract_date or "", placeholder="2024-01-15")

        # Active toggle
        toggle_row = ctk.CTkFrame(basic_inner, fg_color="transparent")
        toggle_row.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(toggle_row, text="Status", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(side="left", padx=(0, 12))

        self.active_var = ctk.BooleanVar(value=bool(agent.is_active))
        ctk.CTkSwitch(
            toggle_row, text="Active",
            variable=self.active_var,
            font=font_body(13),
            fg_color=c['TEXT_SECONDARY'],
            progress_color=c['SUCCESS'],
            button_color='#FFFFFF',
            button_hover_color=c['CARD_BORDER'],
        ).pack(side="left")

        # ── Commission Structure Card ──
        comm_card = card(form)
        comm_card.pack(fill="x", pady=(0, 12))

        comm_inner = ctk.CTkFrame(comm_card, fg_color="transparent")
        comm_inner.pack(fill="x", padx=24, pady=20)

        sl2 = section_label(comm_inner, "Commission Structure")
        sl2.pack(anchor="w", pady=(0, 8))

        # Split Type
        type_row = ctk.CTkFrame(comm_inner, fg_color="transparent")
        type_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(type_row, text="Split Type", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(side="left", padx=(0, 16))

        self.split_type_var = ctk.StringVar(value=agent.split_type)
        for val, text in [("percentage", "Percentage"), ("tiered", "Tiered"), ("transaction_fee", "Transaction Fee")]:
            ctk.CTkRadioButton(
                type_row, text=text, variable=self.split_type_var, value=val,
                font=font_body(12),
                fg_color=c['PRIMARY'], hover_color=c['PRIMARY_HOVER'],
                border_width_unchecked=2,
                border_color=c['CARD_BORDER'],
                command=self._on_split_type_change,
            ).pack(side="left", padx=(0, 16))

        # Container for split-type-specific fields
        self.split_fields_container = ctk.CTkFrame(comm_inner, fg_color="transparent")
        self.split_fields_container.pack(fill="x")

        # Percentage fields
        self.pct_frame = ctk.CTkFrame(self.split_fields_container, fg_color="transparent")

        pct_row = ctk.CTkFrame(self.pct_frame, fg_color="transparent")
        pct_row.pack(fill="x", pady=(4, 0))

        left_pct = ctk.CTkFrame(pct_row, fg_color="transparent")
        left_pct.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(left_pct, text="Agent Split %", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.agent_pct_entry = ctk.CTkEntry(
            left_pct, width=100, height=36, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.agent_pct_entry.insert(0, str(agent.agent_split_pct or ""))
        self.agent_pct_entry.pack(anchor="w")

        right_pct = ctk.CTkFrame(pct_row, fg_color="transparent")
        right_pct.pack(side="left")
        ctk.CTkLabel(right_pct, text="Office Split %", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.office_pct_entry = ctk.CTkEntry(
            right_pct, width=100, height=36, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.office_pct_entry.insert(0, str(agent.office_split_pct or ""))
        self.office_pct_entry.pack(anchor="w")

        # Transaction fee field
        self.fee_frame = ctk.CTkFrame(self.split_fields_container, fg_color="transparent")

        ctk.CTkLabel(self.fee_frame, text="Transaction Fee ($)", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(4, 4))
        self.txn_fee_entry = ctk.CTkEntry(
            self.fee_frame, width=160, height=36, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.txn_fee_entry.insert(0, str(agent.transaction_fee or ""))
        self.txn_fee_entry.pack(anchor="w")

        # Tiered rules
        self.tier_frame = ctk.CTkFrame(self.split_fields_container, fg_color="transparent")

        ctk.CTkLabel(
            self.tier_frame, text="Tier Configuration",
            font=font_caption(12), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(4, 8))

        # Parse existing tiers
        t1_agent, t1_office, t1_count, t2_agent, t2_office = "", "", "", "", ""
        if agent.tier_rules:
            try:
                rules = json.loads(agent.tier_rules)
                tiers = rules.get('tiers', [])
                if len(tiers) >= 2:
                    t1_agent = str(tiers[0].get('agent_pct', ''))
                    t1_office = str(tiers[0].get('office_pct', ''))
                    t1_count = str(tiers[0].get('max_txn_count', ''))
                    t2_agent = str(tiers[1].get('agent_pct', ''))
                    t2_office = str(tiers[1].get('office_pct', ''))
            except (json.JSONDecodeError, KeyError):
                pass

        tier_input_row = ctk.CTkFrame(self.tier_frame, fg_color="transparent")
        tier_input_row.pack(fill="x")

        f1 = ctk.CTkFrame(tier_input_row, fg_color="transparent")
        f1.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(f1, text="First split (agent/office)", font=ctk.CTkFont(size=10), text_color=c['TEXT_MUTED']).pack(anchor="w")
        tier_r1 = ctk.CTkFrame(f1, fg_color="transparent")
        tier_r1.pack(anchor="w", pady=(2, 0))
        self.tier1_agent = ctk.CTkEntry(
            tier_r1, width=50, height=32, font=font_body(12),
            corner_radius=6, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.tier1_agent.insert(0, t1_agent)
        self.tier1_agent.pack(side="left", padx=(0, 2))
        ctk.CTkLabel(tier_r1, text="/", font=font_body(12), text_color=c['TEXT_SECONDARY']).pack(side="left")
        self.tier1_office = ctk.CTkEntry(
            tier_r1, width=50, height=32, font=font_body(12),
            corner_radius=6, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.tier1_office.insert(0, t1_office)
        self.tier1_office.pack(side="left", padx=(2, 0))

        f2 = ctk.CTkFrame(tier_input_row, fg_color="transparent")
        f2.pack(side="left", padx=(0, 14))
        ctk.CTkLabel(f2, text="For first N deals", font=ctk.CTkFont(size=10), text_color=c['TEXT_MUTED']).pack(anchor="w")
        self.tier1_count = ctk.CTkEntry(
            f2, width=50, height=32, font=font_body(12),
            corner_radius=6, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.tier1_count.insert(0, t1_count)
        self.tier1_count.pack(anchor="w", pady=(2, 0))

        f3 = ctk.CTkFrame(tier_input_row, fg_color="transparent")
        f3.pack(side="left")
        ctk.CTkLabel(f3, text="Then (agent/office)", font=ctk.CTkFont(size=10), text_color=c['TEXT_MUTED']).pack(anchor="w")
        tier_r2 = ctk.CTkFrame(f3, fg_color="transparent")
        tier_r2.pack(anchor="w", pady=(2, 0))
        self.tier2_agent = ctk.CTkEntry(
            tier_r2, width=50, height=32, font=font_body(12),
            corner_radius=6, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.tier2_agent.insert(0, t2_agent)
        self.tier2_agent.pack(side="left", padx=(0, 2))
        ctk.CTkLabel(tier_r2, text="/", font=font_body(12), text_color=c['TEXT_SECONDARY']).pack(side="left")
        self.tier2_office = ctk.CTkEntry(
            tier_r2, width=50, height=32, font=font_body(12),
            corner_radius=6, border_width=1, border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.tier2_office.insert(0, t2_office)
        self.tier2_office.pack(side="left", padx=(2, 0))

        self._on_split_type_change()

        # ── Cap Card ──
        cap_card = card(form)
        cap_card.pack(fill="x", pady=(0, 12))

        cap_inner = ctk.CTkFrame(cap_card, fg_color="transparent")
        cap_inner.pack(fill="x", padx=24, pady=20)

        sl3 = section_label(cap_inner, "Cap Settings")
        sl3.pack(anchor="w", pady=(0, 4))

        self.cap_entry = self._styled_entry(cap_inner, "Cap Amount ($)", str(agent.cap_amount if agent.cap_amount is not None else ""), placeholder="16000")

        # Current cap info
        from core.commission_engine import get_cap_year
        from datetime import date
        today = date.today()
        ys, ye = get_cap_year(agent.contract_date, today)
        cap_ptd = self.db.get_cap_paid_to_date(agent.id, ys, ye)

        info_bar = ctk.CTkFrame(cap_inner, fg_color=c['SECTION_BG'], corner_radius=8)
        info_bar.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            info_bar,
            text=f"Current Cap Paid: ${cap_ptd:,.2f}  \u2022  Cap Year: {ys} to {ye}",
            font=font_caption(11), text_color=c['TEXT_SECONDARY'],
        ).pack(padx=14, pady=10, anchor="w")

        # Manual adjustment
        adj_label = ctk.CTkLabel(
            cap_inner,
            text="Manual Cap Adjustment (add pre-software amounts)",
            font=font_caption(11), text_color=c['TEXT_MUTED'],
        )
        adj_label.pack(anchor="w", pady=(12, 4))

        adj_row = ctk.CTkFrame(cap_inner, fg_color="transparent")
        adj_row.pack(fill="x")

        self.cap_adj_entry = ctk.CTkEntry(
            adj_row, width=160, height=36, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="0.00",
        )
        self.cap_adj_entry.pack(side="left", padx=(0, 10))

        primary_button(
            adj_row, "Add Adjustment", self._add_cap_adjustment, width=150,
        ).pack(side="left")

        # ── Notes Card ──
        notes_card = card(form)
        notes_card.pack(fill="x", pady=(0, 12))

        notes_inner = ctk.CTkFrame(notes_card, fg_color="transparent")
        notes_inner.pack(fill="x", padx=24, pady=20)

        sl4 = section_label(notes_inner, "Notes")
        sl4.pack(anchor="w", pady=(0, 8))

        self.notes_entry = ctk.CTkTextbox(
            notes_inner, height=70, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'],
            fg_color=c['CARD_BG'],
        )
        self.notes_entry.pack(fill="x")
        self.notes_entry.insert("1.0", agent.notes or "")

        # ── Error & Action Buttons ──
        self.error_label = ctk.CTkLabel(
            form, text="", text_color=c['DANGER'], font=font_body(12),
        )
        self.error_label.pack(anchor="w", pady=(4, 0))

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(12, 20))

        success_button(
            btn_frame, "Save Changes", self._save, width=180,
        ).pack(side="left", padx=(0, 12))

        danger_button(
            btn_frame, "Delete Agent", self._delete_agent, width=140,
        ).pack(side="right")

    def _on_split_type_change(self):
        stype = self.split_type_var.get()
        if stype == "percentage":
            self.pct_frame.pack(fill="x")
            self.fee_frame.pack_forget()
            self.tier_frame.pack_forget()
        elif stype == "transaction_fee":
            self.pct_frame.pack_forget()
            self.fee_frame.pack(fill="x")
            self.tier_frame.pack_forget()
        elif stype == "tiered":
            self.pct_frame.pack_forget()
            self.fee_frame.pack_forget()
            self.tier_frame.pack(fill="x")

    def _add_cap_adjustment(self):
        agent = self.selected_agent
        if not agent:
            return

        adj_str = self.cap_adj_entry.get().strip().replace(',', '').replace('$', '')
        try:
            adj_amount = float(adj_str)
            if adj_amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Enter a positive dollar amount.")
            return

        from core.commission_engine import get_cap_year
        from datetime import date
        today = date.today()
        ys, ye = get_cap_year(agent.contract_date, today)

        self.db.insert_transaction({
            'agent_id': agent.id,
            'invoice_number': self.db.get_next_invoice_number(),
            'property_address': 'CAP ADJUSTMENT',
            'gross_commission': 0,
            'closing_date': today.isoformat(),
            'is_company_lead': 0,
            'compliance_fee_amount': 0,
            'compliance_fee_payer': 'buyer',
            'office_share': adj_amount,
            'agent_share': 0,
            'amount_toward_cap': adj_amount,
            'cap_before_txn': self.db.get_cap_paid_to_date(agent.id, ys, ye) - adj_amount,
            'cap_after_txn': self.db.get_cap_paid_to_date(agent.id, ys, ye),
            'agent_pct_used': 0,
            'office_pct_used': 0,
            'payment_method': '',
            'total_payout': 0,
            'cap_year_start': ys,
            'cap_year_end': ye,
            'compliance_to_office': 0,
            'compliance_to_agent': 0,
            'notes': 'Manual cap adjustment',
        })

        messagebox.showinfo("Adjustment Added", f"${adj_amount:,.2f} added to cap paid for {agent.name}.")
        self.cap_adj_entry.delete(0, "end")
        self._build_edit_form()

    def _save(self):
        self.error_label.configure(text="")
        agent = self.selected_agent
        if not agent:
            return

        name = self.name_entry.get().strip()
        if not name:
            self.error_label.configure(text="Name is required.")
            return

        license_num = self.license_entry.get().strip() or None
        license_exp = self.license_exp_entry.get().strip() or None
        contract_date = self.contract_entry.get().strip() or None

        if license_exp:
            if not self._validate_date(license_exp):
                self.error_label.configure(text="License expiration must be YYYY-MM-DD format.")
                return
        if contract_date:
            if not self._validate_date(contract_date):
                self.error_label.configure(text="Contract date must be YYYY-MM-DD format.")
                return

        split_type = self.split_type_var.get()
        agent_pct = None
        office_pct = None
        txn_fee = None
        tier_rules = None

        if split_type == "percentage":
            try:
                agent_pct = float(self.agent_pct_entry.get().strip())
                office_pct = float(self.office_pct_entry.get().strip())
                if agent_pct + office_pct != 100:
                    self.error_label.configure(text="Agent % + Office % must equal 100.")
                    return
            except ValueError:
                self.error_label.configure(text="Enter valid percentages for agent and office split.")
                return

        elif split_type == "transaction_fee":
            try:
                txn_fee = float(self.txn_fee_entry.get().strip().replace(',', '').replace('$', ''))
                if txn_fee <= 0:
                    raise ValueError
            except ValueError:
                self.error_label.configure(text="Enter a valid transaction fee amount.")
                return

        elif split_type == "tiered":
            try:
                t1a = int(self.tier1_agent.get().strip())
                t1o = int(self.tier1_office.get().strip())
                t1c = int(self.tier1_count.get().strip())
                t2a = int(self.tier2_agent.get().strip())
                t2o = int(self.tier2_office.get().strip())
                if t1a + t1o != 100 or t2a + t2o != 100:
                    self.error_label.configure(text="Each tier: Agent % + Office % must equal 100.")
                    return
                tier_rules = json.dumps({
                    'tiers': [
                        {'max_txn_count': t1c, 'agent_pct': t1a, 'office_pct': t1o},
                        {'max_txn_count': None, 'agent_pct': t2a, 'office_pct': t2o},
                    ]
                })
                agent_pct = float(t1a)
                office_pct = float(t1o)
            except ValueError:
                self.error_label.configure(text="Fill in all tier fields with valid numbers.")
                return

        cap_str = self.cap_entry.get().strip().replace(',', '').replace('$', '')
        cap_amount = None
        if cap_str:
            try:
                cap_amount = float(cap_str)
                if cap_amount < 0:
                    raise ValueError
            except ValueError:
                self.error_label.configure(text="Enter a valid cap amount (0 or positive).")
                return

        is_active = 1 if self.active_var.get() else 0
        notes = self.notes_entry.get("1.0", "end").strip()

        self.db.conn.execute("""
            UPDATE agents SET
                name = ?, license_number = ?, license_expiration = ?,
                split_type = ?, agent_split_pct = ?, office_split_pct = ?,
                tier_rules = ?, transaction_fee = ?, cap_amount = ?,
                contract_date = ?, is_active = ?, notes = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            name, license_num, license_exp,
            split_type, agent_pct, office_pct,
            tier_rules, txn_fee, cap_amount,
            contract_date, is_active, notes,
            agent.id,
        ))
        self.db.conn.commit()

        messagebox.showinfo("Saved", f"Agent '{name}' updated successfully.")

        self.agents = self.db.get_all_agents()
        names = [f"{'[X] ' if not a.is_active else ''}{'[TEST] ' if a.is_test else ''}{a.name}" for a in self.agents]
        self.agent_dropdown.configure(values=["Choose an agent..."] + names)

        updated = self.db.get_agent(agent.id)
        if updated:
            self.selected_agent = updated
            display = f"{'[X] ' if not updated.is_active else ''}{'[TEST] ' if updated.is_test else ''}{updated.name}"
            self.agent_var.set(display)
            self._build_edit_form()

    def _delete_agent(self):
        c = get_colors()
        agent = self.selected_agent
        if not agent:
            return

        txns = self.db.get_transactions_for_agent(agent.id)
        if txns:
            messagebox.showwarning(
                "Cannot Delete",
                f"{agent.name} has {len(txns)} transaction(s). "
                "Deactivate the agent instead of deleting."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{agent.name}'?\nThis cannot be undone."
        )
        if not confirm:
            return

        self.db.conn.execute("DELETE FROM agents WHERE id = ?", (agent.id,))
        self.db.conn.commit()

        messagebox.showinfo("Deleted", f"Agent '{agent.name}' has been deleted.")

        self.selected_agent = None
        self.agents = self.db.get_all_agents()
        names = [f"{'[X] ' if not a.is_active else ''}{'[TEST] ' if a.is_test else ''}{a.name}" for a in self.agents]
        self.agent_dropdown.configure(values=["Choose an agent..."] + names)
        self.agent_var.set("Choose an agent...")

        for w in self.form_scroll.winfo_children():
            w.destroy()

        placeholder = ctk.CTkFrame(self.form_scroll, fg_color="transparent")
        placeholder.pack(fill="x", pady=40)

        ctk.CTkLabel(
            placeholder, text="No agent selected",
            font=font_heading(16),
            text_color=c['TEXT_SECONDARY'],
        ).pack()

        ctk.CTkLabel(
            placeholder, text="Choose an agent from the dropdown to edit their profile",
            font=font_body(12),
            text_color=c['TEXT_MUTED'],
        ).pack(pady=(4, 0))

    def _validate_date(self, s):
        import re
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', s))

    def _add_new_agent(self):
        from core.models import Agent

        base = "New Agent"
        name = base
        n = 1
        while self.db.get_agent_by_name(name):
            n += 1
            name = f"{base} {n}"

        agent = Agent(
            id=0, name=name,
            split_type='percentage',
            agent_split_pct=70.0,
            office_split_pct=30.0,
            cap_amount=16000.0,
            is_active=1,
        )
        new_id = self.db.insert_agent(agent)

        self.agents = self.db.get_all_agents()
        names = [f"{'[X] ' if not a.is_active else ''}{'[TEST] ' if a.is_test else ''}{a.name}" for a in self.agents]
        self.agent_dropdown.configure(values=["Choose an agent..."] + names)
        new_agent = next((a for a in self.agents if a.id == new_id), None)
        if new_agent:
            display = f"{'[X] ' if not new_agent.is_active else ''}{'[TEST] ' if new_agent.is_test else ''}{new_agent.name}"
            self.agent_var.set(display)
        else:
            self.agent_var.set(name)

        self.selected_agent = self.db.get_agent(new_id)
        self._build_edit_form()

        messagebox.showinfo("Agent Created", f"'{name}' created. Update the details and click Save.")

    # ── Tax Info Tab ──

    def _build_tax_info_tab(self):
        c = get_colors()
        agent = self.selected_agent
        if not agent:
            return

        form = self.tab_content_frame

        # ── TIN Card ──
        tin_card = card(form)
        tin_card.pack(fill="x", pady=(0, 12))

        tin_inner = ctk.CTkFrame(tin_card, fg_color="transparent")
        tin_inner.pack(fill="x", padx=24, pady=20)

        sl = section_label(tin_inner, "Taxpayer Identification Number (TIN)")
        sl.pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            tin_inner,
            text="SSN or EIN used for 1099-NEC filing. Stored securely.",
            font=font_caption(11), text_color=c['TEXT_MUTED'],
        ).pack(anchor="w", pady=(0, 8))

        tin_row = ctk.CTkFrame(tin_inner, fg_color="transparent")
        tin_row.pack(fill="x")

        self._tin_visible = False
        self._tin_raw = agent.tin or ""

        self.tin_entry = ctk.CTkEntry(
            tin_row, width=200, height=38,
            font=font_body(13),
            corner_radius=8, border_width=1,
            border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
            placeholder_text="XXX-XX-XXXX",
        )
        self.tin_entry.insert(0, self._mask_tin(self._tin_raw) if self._tin_raw else "")
        self.tin_entry.pack(side="left", padx=(0, 10))

        self.tin_toggle_btn = ctk.CTkButton(
            tin_row, text="Show", width=70, height=38,
            font=font_body(12),
            fg_color=c['SECTION_BG'], text_color=c['TEXT_PRIMARY'],
            hover_color=c['CARD_BORDER'], corner_radius=8,
            command=self._toggle_tin_visibility,
        )
        self.tin_toggle_btn.pack(side="left")

        # ── Mailing Address Card ──
        addr_card = card(form)
        addr_card.pack(fill="x", pady=(0, 12))

        addr_inner = ctk.CTkFrame(addr_card, fg_color="transparent")
        addr_inner.pack(fill="x", padx=24, pady=20)

        sl2 = section_label(addr_inner, "Mailing Address")
        sl2.pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            addr_inner,
            text="Address used on 1099-NEC forms.",
            font=font_caption(11), text_color=c['TEXT_MUTED'],
        ).pack(anchor="w", pady=(0, 8))

        self.street_entry = self._styled_entry(addr_inner, "Street Address", agent.street_address or "", placeholder="123 Main St")
        self.city_entry = self._styled_entry(addr_inner, "City", agent.city or "", placeholder="Dearborn")

        state_zip_row = ctk.CTkFrame(addr_inner, fg_color="transparent")
        state_zip_row.pack(fill="x", pady=(8, 0))

        left_col = ctk.CTkFrame(state_zip_row, fg_color="transparent")
        left_col.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(left_col, text="State", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.state_entry = ctk.CTkEntry(
            left_col, width=80, height=38,
            font=font_body(13),
            corner_radius=8, border_width=1,
            border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
        )
        self.state_entry.insert(0, agent.state or "MI")
        self.state_entry.pack(anchor="w")

        right_col = ctk.CTkFrame(state_zip_row, fg_color="transparent")
        right_col.pack(side="left")
        ctk.CTkLabel(right_col, text="ZIP Code", font=font_caption(12), text_color=c['TEXT_SECONDARY']).pack(anchor="w", pady=(0, 4))
        self.zip_entry = ctk.CTkEntry(
            right_col, width=120, height=38,
            font=font_body(13),
            corner_radius=8, border_width=1,
            border_color=c['CARD_BORDER'], fg_color=c['CARD_BG'],
            placeholder_text="48124",
        )
        self.zip_entry.insert(0, agent.zip_code or "")
        self.zip_entry.pack(anchor="w")

        # ── Filing Status Card ──
        status_card = card(form)
        status_card.pack(fill="x", pady=(0, 12))

        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=24, pady=20)

        sl3 = section_label(status_inner, "Filing Status")
        sl3.pack(anchor="w", pady=(0, 8))

        from datetime import date
        current_year = date.today().year
        tax_record = self.db.get_tax_record(agent.id, current_year)

        if tax_record:
            info_text = f"{current_year} Compensation: ${tax_record.effective_amount:,.2f}"
            if tax_record.filed:
                info_text += f"  |  Filed: {tax_record.filed_date or 'Yes'}"
        else:
            info_text = f"No tax records for {current_year}"

        info_bar = ctk.CTkFrame(status_inner, fg_color=c['SECTION_BG'], corner_radius=8)
        info_bar.pack(fill="x")

        ctk.CTkLabel(
            info_bar, text=info_text,
            font=font_caption(11), text_color=c['TEXT_SECONDARY'],
        ).pack(padx=14, pady=10, anchor="w")

        # Readiness indicators
        readiness_frame = ctk.CTkFrame(status_inner, fg_color="transparent")
        readiness_frame.pack(fill="x", pady=(10, 0))

        checks = [
            ("TIN on file", bool(agent.tin)),
            ("Mailing address", bool(agent.street_address)),
        ]

        for label_text, is_ok in checks:
            row = ctk.CTkFrame(readiness_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            icon = "OK" if is_ok else "  --"
            color = c['SUCCESS'] if is_ok else c['TEXT_SECONDARY']
            ctk.CTkLabel(
                row, text=f"  {icon}  {label_text}",
                font=font_caption(11), text_color=color,
            ).pack(anchor="w")

        # ── Save Button ──
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(16, 20))

        success_button(
            btn_frame, "Save Tax Info", self._save_tax_info, width=180,
        ).pack(side="left")

    def _mask_tin(self, tin: str) -> str:
        """Mask TIN for display, showing only last 4 digits."""
        clean = tin.replace("-", "").replace(" ", "")
        if len(clean) >= 4:
            return f"***-**-{clean[-4:]}"
        return tin

    def _toggle_tin_visibility(self):
        """Toggle between masked and raw TIN display."""
        current_value = self.tin_entry.get()

        if self._tin_visible:
            # Currently showing raw -> switch to masked
            # Save any edits the user made while visible
            self._tin_raw = current_value
            self.tin_entry.delete(0, "end")
            self.tin_entry.insert(0, self._mask_tin(self._tin_raw) if self._tin_raw else "")
            self.tin_toggle_btn.configure(text="Show")
            self._tin_visible = False
        else:
            # Currently masked -> switch to raw
            self.tin_entry.delete(0, "end")
            self.tin_entry.insert(0, self._tin_raw)
            self.tin_toggle_btn.configure(text="Hide")
            self._tin_visible = True

    def _save_tax_info(self):
        """Save tax-related fields for the selected agent."""
        agent = self.selected_agent
        if not agent:
            return

        # Get TIN value - use raw if visible, otherwise use stored raw
        if self._tin_visible:
            tin = self.tin_entry.get().strip()
        else:
            tin = self._tin_raw

        street = self.street_entry.get().strip()
        city_val = self.city_entry.get().strip()
        state_val = self.state_entry.get().strip()
        zip_val = self.zip_entry.get().strip()

        self.db.conn.execute("""
            UPDATE agents SET
                tin = ?, street_address = ?, city = ?,
                state = ?, zip_code = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (tin, street, city_val, state_val, zip_val, agent.id))
        self.db.conn.commit()

        # Refresh agent data
        self.selected_agent = self.db.get_agent(agent.id)
        self._tin_raw = tin

        messagebox.showinfo("Saved", f"Tax info for '{agent.name}' updated successfully.")
