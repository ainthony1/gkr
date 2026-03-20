# Test Profile Exclusion Design

## Goal

Allow the existing "Test Agent" profile to function fully for testing (invoices, 1099s, etc.) while excluding its data from company-wide aggregate numbers (dashboard stats, tax summaries).

## Approach

Add an `is_test` flag to the agents table. The flag marks an agent as a test profile. All aggregate/summary queries filter out test agents and their transactions. Individual agent operations remain unaffected.

## Schema Change

Add column to `agents` table via existing `_migrate_schema()`:

```
is_test INTEGER DEFAULT 0
```

Add `is_test` field to the `Agent` dataclass in `models.py` (default `0`).

On migration, auto-detect the existing Test Agent by name match (`name LIKE '%test%'` case-insensitive) and set `is_test = 1`.

Update `_row_to_agent()` in `database.py` to read the new column.

## Database Methods

**New methods:**

- `get_real_agents()` - Returns active agents where `is_test = 0`. Used only for aggregate calculations.
- `get_real_transactions()` - Returns all transactions joined with agents, excluding those belonging to `is_test = 1` agents. Used for dashboard YTD stats.

**Unchanged methods (include test agent):**

- `get_active_agents()` - Still returns all active agents. Used for agent selection lists, manage agents, taxes table rows.
- `get_all_agents()` - Still returns everything. Used for agent management.
- `get_all_transactions()` - Still returns everything. Used for history view.
- `get_transactions_for_agent()` - Still works per-agent. Used for individual agent history.

## Filtered Locations (Exclude Test)

### Dashboard (`dashboard_frame.py`)

- **Active Agents count**: Use `get_real_agents()` instead of `get_active_agents()`
- **YTD gross commissions**: Use `get_real_transactions()` instead of `get_all_transactions()`
- **YTD agent payouts**: Same, derived from real transactions
- **Pending 1099s count**: Filter tax records to exclude test agent

### Taxes Frame (`taxes_frame.py`)

- **Summary bar totals**: When summing total compensation, agents above threshold, and agents missing info, skip agents where `is_test = 1`
- Individual rows still show the test agent (it appears in the table, just excluded from the summary numbers)

## Unfiltered Locations (Include Test)

- Agent select dropdown (invoices) - test agent can be selected to create test invoices
- Manage Agents list - test agent is visible and editable
- Taxes table rows - test agent has its own row with generate/adjust buttons
- History view - test agent transactions are visible
- All individual agent operations (generate invoice, generate 1099)

## UI Indicator

Add a small "[TEST]" text label next to the test agent's name in list views (agent select, manage agents, taxes table) so it's visually distinct from real agents. This is a display-only change using the existing `is_test` flag.

## Files Modified

1. `src/core/models.py` - Add `is_test: int = 0` field to Agent dataclass
2. `src/core/database.py` - Add migration column, add `get_real_agents()` and `get_real_transactions()`, update `_row_to_agent()`
3. `src/ui/dashboard_frame.py` - Use real (non-test) methods for stats
4. `src/ui/taxes_frame.py` - Exclude test agent from summary bar totals
5. `src/ui/agent_select_frame.py` - Add "[TEST]" indicator next to test agent name
6. `src/ui/agent_manage_frame.py` - Add "[TEST]" indicator next to test agent name

## Edge Cases

- If someone renames the Test Agent, `is_test` flag persists (it's on the row, not name-based at runtime)
- New agents default to `is_test = 0` (real agents)
- If the test agent is deactivated, it disappears from active lists as usual but `is_test` is preserved if reactivated
