import sqlite3
from typing import Optional
from core.models import Agent, Transaction


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate_schema()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                name                TEXT NOT NULL UNIQUE,
                license_number      TEXT,
                license_expiration  TEXT,
                split_type          TEXT NOT NULL DEFAULT 'percentage',
                agent_split_pct     REAL,
                office_split_pct    REAL,
                tier_rules          TEXT,
                transaction_fee     REAL,
                cap_amount          REAL,
                contract_date       TEXT,
                is_active           INTEGER DEFAULT 1,
                notes               TEXT,
                created_at          TEXT DEFAULT (datetime('now')),
                updated_at          TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id              INTEGER NOT NULL REFERENCES agents(id),
                invoice_number        TEXT NOT NULL UNIQUE,
                property_address      TEXT NOT NULL,
                gross_commission      REAL NOT NULL,
                closing_date          TEXT NOT NULL,
                is_company_lead       INTEGER DEFAULT 0,
                compliance_fee_amount REAL DEFAULT 0,
                compliance_fee_payer  TEXT DEFAULT 'buyer',
                office_share          REAL NOT NULL,
                agent_share           REAL NOT NULL,
                amount_toward_cap     REAL NOT NULL,
                cap_before_txn        REAL NOT NULL,
                cap_after_txn         REAL NOT NULL,
                agent_pct_used        REAL,
                office_pct_used       REAL,
                payment_method        TEXT DEFAULT '',
                total_payout          REAL NOT NULL,
                cap_year_start        TEXT,
                cap_year_end          TEXT,
                compliance_to_office  REAL DEFAULT 0,
                compliance_to_agent   REAL DEFAULT 0,
                notes                 TEXT,
                created_at            TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS tax_records (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id            INTEGER NOT NULL REFERENCES agents(id),
                tax_year            INTEGER NOT NULL,
                total_compensation  REAL DEFAULT 0.0,
                manual_adjustment   REAL DEFAULT 0.0,
                adjustment_note     TEXT DEFAULT '',
                filed               INTEGER DEFAULT 0,
                filed_date          TEXT,
                UNIQUE(agent_id, tax_year)
            );
        """)
        self.conn.commit()

    def _migrate_schema(self):
        """Add new columns to existing tables if they don't exist yet."""
        existing = {row[1] for row in self.conn.execute("PRAGMA table_info(agents)").fetchall()}
        migrations = [
            ("tin", "TEXT DEFAULT ''"),
            ("street_address", "TEXT DEFAULT ''"),
            ("city", "TEXT DEFAULT ''"),
            ("state", "TEXT DEFAULT 'MI'"),
            ("zip_code", "TEXT DEFAULT ''"),
            ("is_test", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_def in migrations:
            if col_name not in existing:
                self.conn.execute(f"ALTER TABLE agents ADD COLUMN {col_name} {col_def}")
        # Auto-detect existing test agent by name
        self.conn.execute(
            "UPDATE agents SET is_test = 1 WHERE LOWER(name) LIKE '%test%' AND is_test = 0"
        )
        self.conn.commit()

    # --- Agent Methods ---

    def get_active_agents(self) -> list[Agent]:
        rows = self.conn.execute(
            "SELECT * FROM agents WHERE is_active = 1 ORDER BY name"
        ).fetchall()
        return [self._row_to_agent(r) for r in rows]

    def get_all_agents(self) -> list[Agent]:
        rows = self.conn.execute("SELECT * FROM agents ORDER BY name").fetchall()
        return [self._row_to_agent(r) for r in rows]

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        row = self.conn.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return self._row_to_agent(row) if row else None

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        row = self.conn.execute(
            "SELECT * FROM agents WHERE name = ?", (name,)
        ).fetchone()
        return self._row_to_agent(row) if row else None

    def insert_agent(self, agent: Agent) -> int:
        cursor = self.conn.execute("""
            INSERT OR REPLACE INTO agents
            (name, license_number, license_expiration, split_type,
             agent_split_pct, office_split_pct, tier_rules, transaction_fee,
             cap_amount, contract_date, is_active, is_test, notes,
             tin, street_address, city, state, zip_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent.name, agent.license_number, agent.license_expiration,
            agent.split_type, agent.agent_split_pct, agent.office_split_pct,
            agent.tier_rules, agent.transaction_fee, agent.cap_amount,
            agent.contract_date, agent.is_active, agent.is_test, agent.notes,
            agent.tin, agent.street_address, agent.city, agent.state, agent.zip_code,
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_agent_contract_date(self, agent_id: int, contract_date: str):
        self.conn.execute(
            "UPDATE agents SET contract_date = ?, updated_at = datetime('now') WHERE id = ?",
            (contract_date, agent_id)
        )
        self.conn.commit()

    def agent_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]

    def get_real_agents(self) -> list[Agent]:
        """Active agents excluding test profiles. Used for aggregate stats."""
        rows = self.conn.execute(
            "SELECT * FROM agents WHERE is_active = 1 AND is_test = 0 ORDER BY name"
        ).fetchall()
        return [self._row_to_agent(r) for r in rows]

    def get_real_transactions(self) -> list['Transaction']:
        """All transactions excluding those from test agents. Used for aggregate stats."""
        rows = self.conn.execute("""
            SELECT t.*, a.name as agent_name
            FROM transactions t
            JOIN agents a ON t.agent_id = a.id
            WHERE a.is_test = 0
            ORDER BY t.closing_date DESC, t.id DESC
        """).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    # --- Transaction Methods ---

    def insert_transaction(self, data: dict) -> int:
        cursor = self.conn.execute("""
            INSERT INTO transactions
            (agent_id, invoice_number, property_address, gross_commission,
             closing_date, is_company_lead, compliance_fee_amount, compliance_fee_payer,
             office_share, agent_share, amount_toward_cap, cap_before_txn, cap_after_txn,
             agent_pct_used, office_pct_used, payment_method, total_payout,
             cap_year_start, cap_year_end, compliance_to_office, compliance_to_agent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['agent_id'], data['invoice_number'], data['property_address'],
            data['gross_commission'], data['closing_date'], data['is_company_lead'],
            data['compliance_fee_amount'], data['compliance_fee_payer'],
            data['office_share'], data['agent_share'], data['amount_toward_cap'],
            data['cap_before_txn'], data['cap_after_txn'],
            data['agent_pct_used'], data['office_pct_used'],
            data['payment_method'], data['total_payout'],
            data['cap_year_start'], data['cap_year_end'],
            data.get('compliance_to_office', 0), data.get('compliance_to_agent', 0),
            data.get('notes', '')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_transactions_for_agent(self, agent_id: int) -> list[Transaction]:
        rows = self.conn.execute("""
            SELECT t.*, a.name as agent_name
            FROM transactions t
            JOIN agents a ON t.agent_id = a.id
            WHERE t.agent_id = ?
            ORDER BY t.closing_date DESC, t.id DESC
        """, (agent_id,)).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    def get_all_transactions(self) -> list[Transaction]:
        rows = self.conn.execute("""
            SELECT t.*, a.name as agent_name
            FROM transactions t
            JOIN agents a ON t.agent_id = a.id
            ORDER BY t.closing_date DESC, t.id DESC
        """).fetchall()
        return [self._row_to_transaction(r) for r in rows]

    def get_transaction_by_id(self, txn_id: int) -> Optional[Transaction]:
        row = self.conn.execute("""
            SELECT t.*, a.name as agent_name
            FROM transactions t
            JOIN agents a ON t.agent_id = a.id
            WHERE t.id = ?
        """, (txn_id,)).fetchone()
        return self._row_to_transaction(row) if row else None

    def get_cap_paid_to_date(self, agent_id: int, year_start: str, year_end: str) -> float:
        row = self.conn.execute("""
            SELECT COALESCE(SUM(amount_toward_cap), 0)
            FROM transactions
            WHERE agent_id = ?
              AND closing_date >= ?
              AND closing_date <= ?
        """, (agent_id, year_start, year_end)).fetchone()
        return row[0]

    def get_txn_count_in_period(self, agent_id: int, year_start: str, year_end: str) -> int:
        row = self.conn.execute("""
            SELECT COUNT(*)
            FROM transactions
            WHERE agent_id = ?
              AND closing_date >= ?
              AND closing_date <= ?
        """, (agent_id, year_start, year_end)).fetchone()
        return row[0]

    # --- Settings Methods ---

    def get_setting(self, key: str, default: str = '') -> str:
        row = self.conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def get_next_invoice_number(self) -> str:
        num_str = self.get_setting('next_invoice_number', '1')
        num = int(num_str)
        invoice = f"INV-{num:04d}"
        self.set_setting('next_invoice_number', str(num + 1))
        return invoice

    # --- Tax Record Methods ---

    def get_tax_record(self, agent_id: int, tax_year: int):
        from core.models import TaxRecord
        row = self.conn.execute("""
            SELECT tr.*, a.name as agent_name
            FROM tax_records tr
            JOIN agents a ON tr.agent_id = a.id
            WHERE tr.agent_id = ? AND tr.tax_year = ?
        """, (agent_id, tax_year)).fetchone()
        if not row:
            return None
        return self._row_to_tax_record(row)

    def get_tax_records_for_year(self, tax_year: int) -> list:
        rows = self.conn.execute("""
            SELECT tr.*, a.name as agent_name
            FROM tax_records tr
            JOIN agents a ON tr.agent_id = a.id
            WHERE tr.tax_year = ?
            ORDER BY a.name
        """, (tax_year,)).fetchall()
        return [self._row_to_tax_record(r) for r in rows]

    def upsert_tax_record(self, agent_id: int, tax_year: int, compensation_to_add: float):
        """Add compensation amount to an agent's tax record for a given year."""
        self.conn.execute("""
            INSERT INTO tax_records (agent_id, tax_year, total_compensation)
            VALUES (?, ?, ?)
            ON CONFLICT(agent_id, tax_year)
            DO UPDATE SET total_compensation = total_compensation + ?
        """, (agent_id, tax_year, compensation_to_add, compensation_to_add))
        self.conn.commit()

    def update_tax_record_adjustment(self, agent_id: int, tax_year: int,
                                      adjustment: float, note: str):
        """Set the manual adjustment for an agent's tax record."""
        self.conn.execute("""
            INSERT INTO tax_records (agent_id, tax_year, manual_adjustment, adjustment_note, filed)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(agent_id, tax_year)
            DO UPDATE SET manual_adjustment = ?, adjustment_note = ?, filed = 0
        """, (agent_id, tax_year, adjustment, note, adjustment, note))
        self.conn.commit()

    def mark_tax_record_filed(self, agent_id: int, tax_year: int):
        """Mark a tax record as filed with current timestamp."""
        from datetime import datetime
        now = datetime.now().isoformat()
        self.conn.execute("""
            UPDATE tax_records
            SET filed = 1, filed_date = ?
            WHERE agent_id = ? AND tax_year = ?
        """, (now, agent_id, tax_year))
        self.conn.commit()

    def get_tax_years(self) -> list[int]:
        """Get all distinct tax years that have records."""
        rows = self.conn.execute(
            "SELECT DISTINCT tax_year FROM tax_records ORDER BY tax_year DESC"
        ).fetchall()
        return [row[0] for row in rows]

    def _row_to_tax_record(self, row):
        from core.models import TaxRecord
        return TaxRecord(
            id=row['id'],
            agent_id=row['agent_id'],
            tax_year=row['tax_year'],
            total_compensation=row['total_compensation'],
            manual_adjustment=row['manual_adjustment'],
            adjustment_note=row['adjustment_note'] or "",
            filed=bool(row['filed']),
            filed_date=row['filed_date'],
            agent_name=row['agent_name'] if 'agent_name' in row.keys() else None,
        )

    # --- Helpers ---

    def _row_to_agent(self, row) -> Agent:
        return Agent(
            id=row['id'],
            name=row['name'],
            license_number=row['license_number'],
            license_expiration=row['license_expiration'],
            split_type=row['split_type'],
            agent_split_pct=row['agent_split_pct'],
            office_split_pct=row['office_split_pct'],
            tier_rules=row['tier_rules'],
            transaction_fee=row['transaction_fee'],
            cap_amount=row['cap_amount'],
            contract_date=row['contract_date'],
            is_active=row['is_active'],
            is_test=row['is_test'] if 'is_test' in row.keys() else 0,
            notes=row['notes'],
            tin=row['tin'] or "",
            street_address=row['street_address'] or "",
            city=row['city'] or "",
            state=row['state'] or "MI",
            zip_code=row['zip_code'] or "",
        )

    def _row_to_transaction(self, row) -> Transaction:
        return Transaction(
            id=row['id'],
            agent_id=row['agent_id'],
            invoice_number=row['invoice_number'],
            property_address=row['property_address'],
            gross_commission=row['gross_commission'],
            closing_date=row['closing_date'],
            is_company_lead=row['is_company_lead'],
            compliance_fee_amount=row['compliance_fee_amount'],
            compliance_fee_payer=row['compliance_fee_payer'],
            office_share=row['office_share'],
            agent_share=row['agent_share'],
            amount_toward_cap=row['amount_toward_cap'],
            cap_before_txn=row['cap_before_txn'],
            cap_after_txn=row['cap_after_txn'],
            agent_pct_used=row['agent_pct_used'],
            office_pct_used=row['office_pct_used'],
            payment_method=row['payment_method'],
            total_payout=row['total_payout'],
            cap_year_start=row['cap_year_start'],
            cap_year_end=row['cap_year_end'],
            notes=row['notes'],
            created_at=row['created_at'],
            agent_name=row['agent_name'] if 'agent_name' in row.keys() else None,
        )

    def close(self):
        self.conn.close()
