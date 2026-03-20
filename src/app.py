import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import date

from core.constants import APP_NAME, DB_PATH, LOGO_PATH
from core.database import Database
from core.commission_engine import calculate_commission, get_cap_year
from generators.pdf_generator import generate_both_invoices
from utils.import_agents import import_from_excel
from ui.theme import (
    get_colors, get_theme_manager, load_nav_icon,
    font_display, font_heading, font_body, font_caption,
)


SIDEBAR_WIDTH = 60
TOP_BAR_HEIGHT = 48


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1050x750")
        self.minsize(950, 650)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.db = Database(DB_PATH)
        self._ensure_agents_imported()

        # State
        self._pending_agent = None
        self._pending_result = None
        self._pending_invoice_num = None
        self._pending_invoice_date = None
        self._pending_address = None
        self._pending_payment = None
        self._pending_form_data = None

        # Sidebar state
        self._sidebar_expanded = False
        self._current_sidebar_width = SIDEBAR_WIDTH
        self._current_page = None
        self._current_nav = "home"

        # Theme
        self._tm = get_theme_manager()
        saved_mode = self.db.get_setting('theme_mode', 'light')
        if saved_mode == 'dark':
            self._tm.mode = 'dark'
            ctk.set_appearance_mode("dark")

        # Icon cache — load all nav icons once
        self._icon_cache = {}
        for icon_name in ('home', 'document', 'clock', 'people', 'calculator',
                          'chart_bar', 'moon', 'sun'):
            icon = load_nav_icon(icon_name)
            if icon:
                self._icon_cache[icon_name] = icon

        self._build_layout()
        self.show_dashboard()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ── Agent Import ──

    def _ensure_agents_imported(self):
        if self.db.agent_count() == 0:
            excel_path = self._find_excel()
            if excel_path:
                count = import_from_excel(self.db, excel_path)
                print(f"Imported {count} agents from Excel")
            else:
                messagebox.showwarning(
                    "No Agent Data",
                    "Could not find agent_info.xlsx. Place it next to the application."
                )

    def _find_excel(self) -> str | None:
        candidates = [
            get_resource_path(os.path.join('assets', 'agent_info.xlsx')),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent_info.xlsx'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_info.xlsx'),
            os.path.join(os.getcwd(), 'agent_info.xlsx'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        path = filedialog.askopenfilename(
            title="Select agent_info.xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )
        return path if path else None

    # ── Layout ──

    def _build_layout(self):
        c = get_colors()

        # Grid: col 0 = sidebar, col 1 = main
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──
        self.sidebar = ctk.CTkFrame(self, fg_color=c['SIDEBAR_BG'], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)
        self.sidebar.configure(width=SIDEBAR_WIDTH)

        self._build_sidebar(c)

        # ── Right column: top bar + content ──
        self.right_col = ctk.CTkFrame(self, fg_color=c['CONTENT_BG'], corner_radius=0)
        self.right_col.grid(row=0, column=1, sticky="nsew")
        self.right_col.grid_rowconfigure(1, weight=1)
        self.right_col.grid_columnconfigure(0, weight=1)

        # Top bar
        self.top_bar = ctk.CTkFrame(self.right_col, fg_color=c['CARD_BG'], height=TOP_BAR_HEIGHT, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)

        self.top_bar_border = ctk.CTkFrame(self.right_col, fg_color=c['CARD_BORDER'], height=1, corner_radius=0)
        self.top_bar_border.grid(row=0, column=0, sticky="sew")

        self._build_top_bar(c)

        # Apply collapsed layout
        self._repack_sidebar()

        # Content area
        self.content = ctk.CTkFrame(self.right_col, fg_color=c['CONTENT_BG'], corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")

    # ── Sidebar ──

    def _build_sidebar(self, c):
        for w in self.sidebar.winfo_children():
            w.destroy()

        # Always build expanded form, store references for repack

        # Brand block
        self._brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._brand_frame.pack(fill="x", padx=12, pady=(20, 0))

        # Expanded brand widgets with their pack kwargs
        accent = ctk.CTkFrame(self._brand_frame, width=28, height=3, fg_color=c['PRIMARY'], corner_radius=1)
        lbl_gotkeyd = ctk.CTkLabel(
            self._brand_frame, text="GOT KEY'D",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color='#FFFFFF',
        )
        lbl_realty = ctk.CTkLabel(
            self._brand_frame, text="REALTY",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=c['PRIMARY'],
        )
        lbl_tracker = ctk.CTkLabel(
            self._brand_frame, text="Commission Tracker",
            font=ctk.CTkFont(size=10),
            text_color=c['SIDEBAR_TEXT'],
        )
        self._brand_expanded_widgets = [
            (accent, {"anchor": "w", "pady": (0, 8)}),
            (lbl_gotkeyd, {"anchor": "w"}),
            (lbl_realty, {"anchor": "w", "pady": (0, 2)}),
            (lbl_tracker, {"anchor": "w"}),
        ]
        for w, kwargs in self._brand_expanded_widgets:
            w.pack(**kwargs)

        # Collapsed brand label (created but hidden)
        self._brand_collapsed_label = ctk.CTkLabel(
            self._brand_frame, text="GK",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c['PRIMARY'],
        )
        # Don't pack — starts hidden

        # Nav section
        self._nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._nav_frame.pack(fill="x", padx=8, pady=(24, 0))

        self._nav_header = ctk.CTkLabel(
            self._nav_frame, text="NAVIGATION",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=c['SIDEBAR_TEXT'],
        )
        self._nav_header.pack(anchor="w", padx=4, pady=(0, 6))

        self.nav_buttons = {}
        self._nav_label_map = {}
        nav_items = [
            ("home", "Dashboard", "home", self.show_dashboard),
            ("invoices", "Invoices", "document", self.show_invoices),
            ("cap_tracker", "Cap Tracker", "chart_bar", self.show_cap_tracker),
            ("history", "History", "clock", self.show_all_history),
            ("agents", "Agents", "people", self.show_agent_manager),
            ("taxes", "Taxes", "calculator", self.show_taxes),
        ]

        for name, label, icon_name, cmd in nav_items:
            is_active = (name == self._current_nav)
            icon = self._icon_cache.get(icon_name)
            self._nav_label_map[name] = label

            btn = ctk.CTkButton(
                self._nav_frame, text=f"  {label}",
                image=icon,
                font=ctk.CTkFont(size=13),
                fg_color=c['SIDEBAR_HOVER'] if is_active else "transparent",
                text_color=c['SIDEBAR_TEXT_ACTIVE'] if is_active else c['SIDEBAR_TEXT'],
                hover_color=c['SIDEBAR_HOVER'],
                anchor="w", height=38,
                corner_radius=8,
                command=cmd,
                compound="left",
            )
            btn.pack(fill="x", pady=1, anchor="w")
            self.nav_buttons[name] = btn

        # Spacer
        self._spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._spacer.pack(fill="both", expand=True)

        # Bottom frame
        self._bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._bottom_frame.pack(fill="x", padx=8, pady=(0, 8))

        # Theme button (always built as expanded)
        theme_icon = self._icon_cache.get('moon') if self._tm.mode == 'light' else self._icon_cache.get('sun')
        theme_text = "Dark Mode" if self._tm.mode == 'light' else "Light Mode"
        self.theme_btn = ctk.CTkButton(
            self._bottom_frame, text=f"  {theme_text}",
            image=theme_icon,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=c['SIDEBAR_TEXT'],
            hover_color=c['SIDEBAR_HOVER'],
            anchor="w", height=36, corner_radius=8,
            command=self._toggle_theme,
            compound="left",
        )
        self.theme_btn.pack(fill="x", pady=1, anchor="w")


        # Version footer
        self._version_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._version_footer.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkFrame(self._version_footer, height=1, fg_color=c['SIDEBAR_HOVER']).pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(self._version_footer, text="v1.0.0", font=ctk.CTkFont(size=9), text_color=c['SIDEBAR_TEXT']).pack(anchor="w")

    def _repack_sidebar(self):
        """Re-pack sidebar in collapsed (icon-only) layout."""
        for child in self.sidebar.winfo_children():
            child.pack_forget()

        # Brand
        self._brand_frame.pack(fill="x", padx=4, pady=(20, 0))
        for w in self._brand_frame.winfo_children():
            w.pack_forget()
        self._brand_collapsed_label.pack(pady=(4, 0))

        # Nav
        self._nav_frame.pack(fill="x", padx=8, pady=(16, 0))
        for w in self._nav_frame.winfo_children():
            w.pack_forget()
        for name, btn in self.nav_buttons.items():
            btn.configure(text="", width=40, anchor="center", height=40, compound="top")
            btn.pack(fill=None, pady=1, anchor="center")

        # Spacer
        self._spacer.pack(fill="both", expand=True)

        # Bottom frame
        self._bottom_frame.pack(fill="x", padx=8, pady=(0, 8))
        for w in self._bottom_frame.winfo_children():
            w.pack_forget()

        # Theme button
        theme_icon = self._icon_cache.get('moon') if self._tm.mode == 'light' else self._icon_cache.get('sun')
        self.theme_btn.configure(text="", width=40, anchor="center",
                                 compound="top", image=theme_icon)
        self.theme_btn.pack(fill=None, pady=1, anchor="center")

        # Top bar pills always visible
        self.top_nav_frame.pack(side="right", pady=8)

    def _build_top_bar(self, c):
        for w in self.top_bar.winfo_children():
            w.destroy()

        inner = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16)

        # Page title (always shown)
        self.top_bar_title = ctk.CTkLabel(
            inner, text="Dashboard",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c['TEXT_PRIMARY'],
        )
        self.top_bar_title.pack(side="left", pady=8)

        # Nav pills (only when sidebar collapsed)
        self.top_nav_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.top_nav_pills = {}

        nav_items = [
            ("home", "Dashboard", self.show_dashboard),
            ("invoices", "Invoices", self.show_invoices),
            ("cap_tracker", "Cap Tracker", self.show_cap_tracker),
            ("history", "History", self.show_all_history),
            ("agents", "Agents", self.show_agent_manager),
            ("taxes", "Taxes", self.show_taxes),
        ]

        for name, label, cmd in nav_items:
            is_active = (name == self._current_nav)
            pill = ctk.CTkButton(
                self.top_nav_frame, text=label,
                font=ctk.CTkFont(size=12),
                fg_color=c['PRIMARY'] if is_active else "transparent",
                text_color='#FFFFFF' if is_active else c['TEXT_SECONDARY'],
                hover_color=c['PRIMARY_LIGHT'],
                height=30, corner_radius=15,
                width=80,
                command=cmd,
            )
            pill.pack(side="left", padx=2)
            self.top_nav_pills[name] = pill

        if not self._sidebar_expanded:
            self.top_nav_frame.pack(side="right", pady=8)

    def _update_top_bar_title(self, title):
        try:
            self.top_bar_title.configure(text=title)
        except Exception:
            pass

    # ── Theme Toggle ──

    def _toggle_theme(self):
        colors = self._tm.toggle()
        mode = self._tm.mode
        ctk.set_appearance_mode(mode)
        self.db.set_setting('theme_mode', mode)

        # Rebuild shell
        self.sidebar.configure(fg_color=colors['SIDEBAR_BG'])
        self._build_sidebar(colors)
        self._repack_sidebar()
        self.right_col.configure(fg_color=colors['CONTENT_BG'])
        self.top_bar.configure(fg_color=colors['CARD_BG'])
        self.top_bar_border.configure(fg_color=colors['CARD_BORDER'])
        self.content.configure(fg_color=colors['CONTENT_BG'])
        self._build_top_bar(colors)

        # Re-show current page (frames will pick up new colors)
        nav_to_show = {
            'home': self.show_dashboard,
            'invoices': self.show_invoices,
            'cap_tracker': self.show_cap_tracker,
            'history': self.show_all_history,
            'agents': self.show_agent_manager,
            'taxes': self.show_taxes,
        }
        show_fn = nav_to_show.get(self._current_nav, self.show_dashboard)
        show_fn()

    # ── Navigation Helpers ──

    def _highlight_nav(self, active):
        self._current_nav = active
        c = get_colors()
        for name, btn in self.nav_buttons.items():
            if name == active:
                btn.configure(fg_color=c['SIDEBAR_HOVER'], text_color=c['SIDEBAR_TEXT_ACTIVE'])
            else:
                btn.configure(fg_color="transparent", text_color=c['SIDEBAR_TEXT'])

        # Update top bar pills
        for name, pill in self.top_nav_pills.items():
            if name == active:
                pill.configure(fg_color=c['PRIMARY'], text_color='#FFFFFF')
            else:
                pill.configure(fg_color="transparent", text_color=c['TEXT_SECONDARY'])

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self._current_page = None

    # ===== Screen Navigation =====

    def show_dashboard(self):
        from ui.dashboard_frame import DashboardFrame
        self._clear_content()
        self._highlight_nav("home")
        self._update_top_bar_title("Dashboard")
        frame = DashboardFrame(
            self.content, self.db,
            on_go_invoices=self.show_invoices,
            on_go_taxes=self.show_taxes,
            on_go_agents=self.show_agent_manager,
            on_go_cap_tracker=self.show_cap_tracker,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_cap_tracker(self):
        from ui.cap_tracker_frame import CapTrackerFrame
        self._clear_content()
        self._highlight_nav("cap_tracker")
        self._update_top_bar_title("Cap Tracker")
        frame = CapTrackerFrame(self.content, self.db)
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_invoices(self):
        from ui.agent_select_frame import AgentSelectFrame
        self._clear_content()
        self._highlight_nav("invoices")
        self._update_top_bar_title("Invoices")
        frame = AgentSelectFrame(
            self.content, self.db,
            on_new_transaction=self._show_transaction_form,
            on_view_history=self._show_agent_history,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def _show_transaction_form(self, agent, prefill=None):
        from ui.transaction_form import TransactionForm
        self._clear_content()
        self._highlight_nav("invoices")
        self._update_top_bar_title("New Transaction")
        form = TransactionForm(
            self.content, agent,
            on_calculate=self._on_calculate,
            on_cancel=self.show_invoices,
        )
        form.pack(fill="both", expand=True)
        self._current_page = form

        if prefill:
            form.address_entry.delete(0, "end")
            form.address_entry.insert(0, prefill.get('address', ''))
            form.sale_price_entry.delete(0, "end")
            form.sale_price_entry.insert(0, str(prefill.get('sale_price', '')))
            form.comm_pct_entry.delete(0, "end")
            form.comm_pct_entry.insert(0, str(prefill.get('comm_pct', '')))
            form._update_gross()
            form.date_entry.delete(0, "end")
            form.date_entry.insert(0, prefill.get('date', ''))
            form.company_lead_var.set(prefill.get('company_lead', False))
            form.fee_entry.delete(0, "end")
            form.fee_entry.insert(0, str(prefill.get('fee', '0')))
            form.payer_var.set(prefill.get('payer', 'buyer'))
            form.payment_entry.delete(0, "end")
            form.payment_entry.insert(0, prefill.get('payment', ''))

    def _on_calculate(self, agent, property_address, gross_commission, closing_date,
                      is_company_lead, compliance_fee, compliance_fee_payer, payment_method,
                      sale_price='', comm_pct=''):
        year_start, year_end = get_cap_year(agent.contract_date, closing_date)
        cap_ptd = self.db.get_cap_paid_to_date(agent.id, year_start, year_end)
        txn_count = self.db.get_txn_count_in_period(agent.id, year_start, year_end)

        result = calculate_commission(
            agent=agent,
            gross_commission=gross_commission,
            is_company_lead=is_company_lead,
            compliance_fee_amount=compliance_fee,
            compliance_fee_payer=compliance_fee_payer,
            cap_paid_to_date=cap_ptd,
            txn_count_in_period=txn_count,
        )

        invoice_date = closing_date.strftime("%m/%d/%Y")

        self._pending_agent = agent
        self._pending_result = result
        self._pending_invoice_date = invoice_date
        self._pending_address = property_address
        self._pending_payment = payment_method
        self._pending_form_data = {
            'address': property_address,
            'commission': gross_commission,
            'sale_price': sale_price,
            'comm_pct': comm_pct,
            'date': invoice_date,
            'company_lead': is_company_lead,
            'fee': compliance_fee,
            'payer': compliance_fee_payer,
            'payment': payment_method,
            'closing_date': closing_date,
            'year_start': year_start,
            'year_end': year_end,
        }

        self._show_review(agent, result, "(pending)", invoice_date, property_address, payment_method)

    def _show_review(self, agent, result, invoice_number, invoice_date, property_address, payment_method):
        from ui.review_frame import ReviewFrame
        self._clear_content()
        self._update_top_bar_title("Invoice Preview")
        frame = ReviewFrame(
            self.content, agent, result,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            property_address=property_address,
            payment_method=payment_method,
            on_generate=self._generate_invoice,
            on_edit=self._edit_transaction,
            on_cancel=self.show_invoices,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def _edit_transaction(self):
        if self._pending_agent and self._pending_form_data:
            self._show_transaction_form(self._pending_agent, prefill=self._pending_form_data)

    def _generate_invoice(self):
        if not self._pending_agent or not self._pending_result:
            return

        agent = self._pending_agent
        result = self._pending_result
        fd = self._pending_form_data

        from core.constants import get_output_dir
        output_dir = get_output_dir()

        invoice_number = self.db.get_next_invoice_number()

        self.db.insert_transaction({
            'agent_id': agent.id,
            'invoice_number': invoice_number,
            'property_address': fd['address'],
            'gross_commission': fd['commission'],
            'closing_date': fd['closing_date'].isoformat(),
            'is_company_lead': 1 if fd['company_lead'] else 0,
            'compliance_fee_amount': fd['fee'],
            'compliance_fee_payer': fd['payer'],
            'office_share': result.office_share,
            'agent_share': result.agent_share,
            'amount_toward_cap': result.amount_toward_cap,
            'cap_before_txn': result.cap_before,
            'cap_after_txn': result.cap_after,
            'agent_pct_used': result.agent_split_pct_used,
            'office_pct_used': result.office_split_pct_used,
            'payment_method': fd['payment'],
            'total_payout': result.total_payout,
            'cap_year_start': fd['year_start'],
            'cap_year_end': fd['year_end'],
            'compliance_to_office': result.compliance_to_office,
            'compliance_to_agent': result.compliance_to_agent,
        })

        tax_year = fd['closing_date'].year
        self.db.upsert_tax_record(agent.id, tax_year, result.agent_share)

        try:
            internal_path, agent_path = generate_both_invoices(
                agent=agent, result=result,
                invoice_number=invoice_number,
                invoice_date=self._pending_invoice_date,
                property_address=fd['address'],
                payment_method=fd['payment'],
                output_dir=output_dir,
            )

            messagebox.showinfo(
                "Invoices Generated",
                f"Invoice {invoice_number} saved!\n\n"
                f"Internal: invoices/internal/{os.path.basename(internal_path)}\n"
                f"Agent copy: invoices/agent/{os.path.basename(agent_path)}\n\n"
                f"Location: {output_dir}"
            )
        except Exception as e:
            messagebox.showerror("PDF Error", f"Transaction saved but PDF generation failed:\n{e}")

        self._pending_agent = None
        self._pending_result = None
        self._pending_form_data = None
        self.show_invoices()

    def _show_agent_history(self, agent):
        from ui.history_frame import HistoryFrame
        self._clear_content()
        self._highlight_nav("history")
        self._update_top_bar_title(f"History — {agent.name}")
        frame = HistoryFrame(
            self.content, self.db, agent=agent,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_all_history(self):
        from ui.history_frame import HistoryFrame
        self._clear_content()
        self._highlight_nav("history")
        self._update_top_bar_title("Transaction History")
        frame = HistoryFrame(
            self.content, self.db,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_agent_manager(self):
        from ui.agent_manage_frame import AgentManageFrame
        self._clear_content()
        self._highlight_nav("agents")
        self._update_top_bar_title("Manage Agents")
        frame = AgentManageFrame(
            self.content, self.db,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def show_taxes(self):
        from ui.taxes_frame import TaxesFrame
        self._clear_content()
        self._highlight_nav("taxes")
        self._update_top_bar_title("1099-NEC Tax Tracking")
        frame = TaxesFrame(
            self.content, self.db,
            on_back=self.show_dashboard,
        )
        frame.pack(fill="both", expand=True)
        self._current_page = frame

    def on_closing(self):
        self.db.close()
        self.destroy()
