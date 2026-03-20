import os
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from core.constants import get_output_dir
from ui.theme import (
    get_colors,
    section_label, card, success_button, primary_button, secondary_button,
    danger_button, separator, badge, font_display, font_heading,
    font_subheading, font_body, font_caption,
)

BADGE_BLUE = '#2563EB'
BADGE_YELLOW = '#D97706'
BADGE_GRAY = '#9CA3AF'
BADGE_GREEN = '#16A34A'

FILING_THRESHOLD = 600.0  # $600 for 2025+


class TaxesFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_back=None):
        c = get_colors()
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_back = on_back
        self._adjustment_window = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        c = get_colors()
        # ── Page Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(28, 0))

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")

        ctk.CTkLabel(
            left_hdr, text="1099-NEC Tax Tracking",
            font=font_display(28),
            text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_hdr, text="Compensation is tracked automatically from invoices — generate 1099s when ready",
            font=font_body(13),
            text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(2, 0))

        # ── Controls Card ──
        ctrl_card = card(self)
        ctrl_card.pack(fill="x", padx=30, pady=(16, 0))

        ctrl_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_inner.pack(fill="x", padx=20, pady=14)

        # Year selector
        ctk.CTkLabel(
            ctrl_inner, text="TAX YEAR",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_MUTED'],
        ).pack(side="left", padx=(0, 8))

        current_year = datetime.now().year
        previous_year = current_year - 1
        # Always include current year and 2 previous years
        years = {str(current_year), str(previous_year), str(previous_year - 1)}
        db_years = self.db.get_tax_years()
        for y in db_years:
            years.add(str(y))
        years = sorted(years, reverse=True)

        self.year_var = ctk.StringVar(value=str(current_year))
        self.year_dropdown = ctk.CTkComboBox(
            ctrl_inner, values=years, variable=self.year_var,
            width=120, height=36,
            font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'],
            button_color=c['PRIMARY'], button_hover_color=c['PRIMARY_HOVER'],
            command=self._on_year_change, state="readonly",
        )
        self.year_dropdown.pack(side="left", padx=(0, 20))

        # Company EIN
        ctk.CTkLabel(
            ctrl_inner, text="COMPANY EIN",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c['TEXT_MUTED'],
        ).pack(side="left", padx=(0, 8))

        self.ein_var = ctk.StringVar(value=self.db.get_setting('company_ein', ''))
        self.ein_entry = ctk.CTkEntry(
            ctrl_inner, textvariable=self.ein_var,
            width=140, height=36, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="XX-XXXXXXX",
        )
        self.ein_entry.pack(side="left", padx=(0, 8))

        secondary_button(
            ctrl_inner, "Save EIN", self._save_ein, width=90,
        ).pack(side="left")

        # Bulk generate button
        success_button(
            ctrl_inner, "Generate All 1099s", self._generate_all, width=180,
        ).pack(side="right")

        # ── Summary Bar ──
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=30, pady=(12, 0))

        self.summary_label = ctk.CTkLabel(
            self.summary_frame, text="",
            font=font_caption(11), text_color=c['TEXT_SECONDARY'],
        )
        self.summary_label.pack(anchor="w")

        # ── Table Area ──
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=30, pady=(8, 20))

    def refresh(self):
        c = get_colors()
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        tax_year = int(self.year_var.get())
        records = self.db.get_tax_records_for_year(tax_year)

        # Build lookup of existing records by agent_id
        record_map = {rec.agent_id: rec for rec in records}

        # Get all active agents so every agent shows up
        all_agents = self.db.get_active_agents()

        if not all_agents:
            self._show_empty()
            return

        # ── Table Header ──
        headers = ["Agent", "Compensation", "Adjustment", "1099 Amount", "Status", "Actions"]
        col_widths = [140, 110, 100, 110, 110, 180]

        hdr_frame = ctk.CTkFrame(self.table_frame, fg_color=c['SIDEBAR_BG'], corner_radius=8)
        hdr_frame.pack(fill="x", pady=(0, 4))

        for h, w in zip(headers, col_widths):
            ctk.CTkLabel(
                hdr_frame, text=h.upper(), width=w,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=c['TEXT_SECONDARY'],
            ).pack(side="left", padx=3, pady=8)

        # ── Data Rows ──
        total_comp = 0
        agents_above = 0
        agents_missing = 0
        row_count = 0

        for i, agent in enumerate(all_agents):
            rec = record_map.get(agent.id)
            bg = c['CARD_BG'] if i % 2 == 0 else c['ROW_ALT']
            row = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", pady=1)

            compensation = rec.total_compensation if rec else 0.0
            adjustment = rec.manual_adjustment if rec else 0.0
            effective = rec.effective_amount if rec else 0.0
            status, status_color = self._get_status(rec, agent)

            # Agent name (with [TEST] indicator)
            display_name = f"{agent.name}  [TEST]" if agent.is_test else agent.name
            ctk.CTkLabel(
                row, text=display_name, width=col_widths[0],
                font=font_body(12), text_color=c['TEXT_PRIMARY'], anchor="w",
            ).pack(side="left", padx=3, pady=7)

            # Compensation
            ctk.CTkLabel(
                row, text=f"${compensation:,.2f}", width=col_widths[1],
                font=font_caption(11), text_color=c['TEXT_PRIMARY'], anchor="w",
            ).pack(side="left", padx=3, pady=7)

            # Adjustment
            adj_text = f"${adjustment:,.2f}" if adjustment != 0 else "$0.00"
            ctk.CTkLabel(
                row, text=adj_text, width=col_widths[2],
                font=font_caption(11), text_color=c['TEXT_PRIMARY'], anchor="w",
            ).pack(side="left", padx=3, pady=7)

            # 1099 Amount
            ctk.CTkLabel(
                row, text=f"${effective:,.2f}", width=col_widths[3],
                font=font_caption(11), text_color=c['TEXT_PRIMARY'], anchor="w",
            ).pack(side="left", padx=3, pady=7)

            # Status badge
            badge(row, status, color=status_color).pack(side="left", padx=3, pady=7)

            # Action buttons
            action_frame = ctk.CTkFrame(row, fg_color="transparent", width=col_widths[5])
            action_frame.pack(side="left", padx=3, pady=4)

            ctk.CTkButton(
                action_frame, text="Adjust", width=70, height=28,
                font=ctk.CTkFont(size=11), fg_color="transparent",
                hover_color=c['SECTION_BG'], text_color=c['TEXT_SECONDARY'],
                border_width=1, border_color=c['CARD_BORDER'], corner_radius=6,
                command=lambda a=agent.id, y=tax_year: self._show_adjustment(a, y),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                action_frame, text="Generate", width=80, height=28,
                font=ctk.CTkFont(size=11), fg_color=c['PRIMARY'],
                hover_color=c['PRIMARY_HOVER'], text_color='#FFFFFF', corner_radius=6,
                command=lambda a=agent.id, y=tax_year: self._generate_single(a, y),
            ).pack(side="left")

            # Exclude test agents from summary totals
            if not agent.is_test:
                total_comp += effective
                if effective >= FILING_THRESHOLD:
                    agents_above += 1
                if not agent.tin or not agent.street_address:
                    agents_missing += 1
                row_count += 1

        # Summary
        self.summary_label.configure(
            text=f"{row_count} agent(s)  \u2022  "
                 f"Total compensation: ${total_comp:,.2f}  \u2022  "
                 f"Above threshold: {agents_above}  \u2022  "
                 f"Missing tax info: {agents_missing}"
        )

    def _show_empty(self):
        c = get_colors()
        empty = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        empty.pack(fill="x", pady=40)

        ctk.CTkLabel(
            empty, text="No tax records found",
            font=font_heading(16), text_color=c['TEXT_SECONDARY'],
        ).pack()

        ctk.CTkLabel(
            empty, text="Tax records are created automatically when invoices are generated",
            font=font_body(12), text_color=c['TEXT_MUTED'],
        ).pack(pady=(4, 0))

        self.summary_label.configure(text="")

    def _get_status(self, record, agent):
        """Return (status_text, status_color) based on priority."""
        if not record or record.effective_amount == 0:
            return "No Sales", BADGE_GRAY
        if record.effective_amount < FILING_THRESHOLD:
            return "Below $600", BADGE_GRAY
        if agent and not agent.tin:
            return "Missing TIN", BADGE_YELLOW
        if agent and not agent.street_address:
            return "Missing Address", BADGE_YELLOW
        return "Ready", BADGE_GREEN

    def _save_ein(self):
        ein = self.ein_var.get().strip()
        self.db.set_setting('company_ein', ein)
        messagebox.showinfo("Saved", "Company EIN updated.")

    def _on_year_change(self, value):
        self.refresh()

    def _show_adjustment(self, agent_id, tax_year):
        """Show a toplevel window for manual adjustment."""
        c = get_colors()
        if self._adjustment_window and self._adjustment_window.winfo_exists():
            self._adjustment_window.destroy()

        agent = self.db.get_agent(agent_id)
        if not agent:
            return
        record = self.db.get_tax_record(agent_id, tax_year)
        if not record:
            # Create a blank record so adjustments can be made even without sales
            self.db.upsert_tax_record(agent_id, tax_year, 0.0)
            record = self.db.get_tax_record(agent_id, tax_year)

        win = ctk.CTkToplevel(self)
        win.title(f"Adjust 1099 \u2014 {agent.name}")
        win.geometry("420x340")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        self._adjustment_window = win

        inner = ctk.CTkFrame(win, fg_color=c['CONTENT_BG'])
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            inner, text=f"Adjust 1099 for {agent.name}",
            font=font_heading(16), text_color=c['TEXT_PRIMARY'],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            inner, text=f"Auto-tracked compensation: ${record.total_compensation:,.2f}",
            font=font_body(13), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            inner, text=f"Current adjustment: ${record.manual_adjustment:,.2f}",
            font=font_body(13), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            inner, text="New Adjustment Amount ($)",
            font=font_caption(12), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 4))

        adj_entry = ctk.CTkEntry(
            inner, width=200, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="0.00",
        )
        adj_entry.insert(0, str(record.manual_adjustment))
        adj_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            inner, text="Reason (required)",
            font=font_caption(12), text_color=c['TEXT_SECONDARY'],
        ).pack(anchor="w", pady=(0, 4))

        note_entry = ctk.CTkEntry(
            inner, width=350, height=38, font=font_body(13),
            corner_radius=8, border_width=1, border_color=c['CARD_BORDER'],
            fg_color=c['CARD_BG'], placeholder_text="e.g., Outside payment not in system",
        )
        note_entry.insert(0, record.adjustment_note)
        note_entry.pack(anchor="w", pady=(0, 16))

        def save_adjustment():
            try:
                amt = float(adj_entry.get().strip().replace(',', '').replace('$', ''))
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid dollar amount.", parent=win)
                return
            note = note_entry.get().strip()
            if not note and amt != 0:
                messagebox.showerror("Required", "Please provide a reason for the adjustment.", parent=win)
                return

            self.db.update_tax_record_adjustment(agent_id, tax_year, amt, note)
            win.destroy()
            self.refresh()

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")

        success_button(btn_frame, "Save", save_adjustment, width=120).pack(side="left", padx=(0, 8))
        secondary_button(btn_frame, "Cancel", win.destroy, width=90).pack(side="left")

    def _generate_single(self, agent_id, tax_year):
        """Generate a 1099-NEC for a single agent."""
        from generators.tax_generator import generate_1099, get_warnings

        agent = self.db.get_agent(agent_id)
        record = self.db.get_tax_record(agent_id, tax_year)
        if not agent:
            messagebox.showerror("Error", "Agent not found.")
            return
        if not record or record.effective_amount == 0:
            messagebox.showinfo("No Data", f"No commission sales recorded for {agent.name} in {tax_year}.")
            return

        company_ein = self.db.get_setting('company_ein', '')
        warnings = get_warnings(agent, company_ein)

        if warnings:
            msg = "The following data is missing:\n\n"
            msg += "\n".join(f"\u2022 {w}" for w in warnings)
            msg += "\n\nThe 1099 will be generated with blank fields. Continue?"
            if not messagebox.askyesno("Missing Data", msg):
                return

        output_dir = get_output_dir()

        try:
            path = generate_1099(agent, record, company_ein, output_dir=output_dir)
            self.refresh()

            messagebox.showinfo(
                "1099 Generated",
                f"1099-NEC for {agent.name} ({tax_year}) saved to:\n\n{path}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate 1099:\n{e}")

    def _generate_all(self):
        """Generate 1099s for all agents above the filing threshold."""
        from generators.tax_generator import generate_1099, get_warnings

        tax_year = int(self.year_var.get())
        records = self.db.get_tax_records_for_year(tax_year)
        company_ein = self.db.get_setting('company_ein', '')

        eligible = [r for r in records if r.effective_amount >= FILING_THRESHOLD]
        if not eligible:
            messagebox.showinfo("No Eligible Agents", "No agents above the $600 filing threshold.")
            return

        confirm = messagebox.askyesno(
            "Generate All",
            f"Generate 1099-NEC forms for {len(eligible)} agent(s) for {tax_year}?"
        )
        if not confirm:
            return

        output_dir = get_output_dir()

        generated = 0
        errors = []

        for rec in eligible:
            agent = self.db.get_agent(rec.agent_id)
            if not agent:
                continue
            try:
                generate_1099(agent, rec, company_ein, output_dir=output_dir)
                generated += 1
            except Exception as e:
                errors.append(f"{rec.agent_name}: {e}")

        self.refresh()

        out_dir = os.path.join(output_dir, "1099", str(tax_year))
        msg = f"Generated {generated} of {len(eligible)} 1099-NEC forms.\n\nSaved to: {out_dir}"
        if errors:
            msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors)

        messagebox.showinfo("Bulk Generation Complete", msg)
