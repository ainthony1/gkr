import json
from datetime import date, timedelta
from core.models import Agent, CommissionResult


def get_cap_year(contract_date_str: str | None, reference_date: date) -> tuple[str, str]:
    if not contract_date_str:
        # Default to calendar year if no contract date
        year_start = date(reference_date.year, 1, 1)
        year_end = date(reference_date.year, 12, 31)
        return year_start.isoformat(), year_end.isoformat()

    contract = date.fromisoformat(contract_date_str)

    def _safe_replace_year(d: date, y: int) -> date:
        """Replace year safely, handling Feb 29 in non-leap years."""
        try:
            return d.replace(year=y)
        except ValueError:
            # Feb 29 → Feb 28 in non-leap years
            return d.replace(year=y, day=28)

    anniversary_this_year = _safe_replace_year(contract, reference_date.year)

    if reference_date >= anniversary_this_year:
        year_start = anniversary_this_year
        year_end = _safe_replace_year(contract, anniversary_this_year.year + 1) - timedelta(days=1)
    else:
        year_start = _safe_replace_year(contract, reference_date.year - 1)
        year_end = anniversary_this_year - timedelta(days=1)

    return year_start.isoformat(), year_end.isoformat()


def _get_split_for_tiered(agent: Agent, txn_count_before: int) -> tuple[float, float]:
    """Get agent_pct, office_pct for a tiered agent based on prior transaction count."""
    if not agent.tier_rules:
        return agent.agent_split_pct or 70.0, agent.office_split_pct or 30.0

    rules = json.loads(agent.tier_rules)
    tiers = rules.get('tiers', [])

    for tier in tiers:
        max_count = tier.get('max_txn_count')
        if max_count is None or txn_count_before < max_count:
            return float(tier['agent_pct']), float(tier['office_pct'])

    # Fallback to last tier
    if tiers:
        last = tiers[-1]
        return float(last['agent_pct']), float(last['office_pct'])
    return 70.0, 30.0


def calculate_commission(
    agent: Agent,
    gross_commission: float,
    is_company_lead: bool,
    compliance_fee_amount: float,
    compliance_fee_payer: str,
    cap_paid_to_date: float,
    txn_count_in_period: int,
) -> CommissionResult:
    # --- Transaction Fee Agents ---
    if agent.split_type == 'transaction_fee':
        fee = agent.transaction_fee or 0
        agent_share = gross_commission - fee
        office_share = fee

        # Handle compliance
        compliance_to_office, compliance_to_agent = _calc_compliance(
            compliance_fee_amount, compliance_fee_payer
        )
        total_payout = agent_share + compliance_to_agent

        return CommissionResult(
            gross_commission=gross_commission,
            agent_split_pct_used=0,
            office_split_pct_used=0,
            office_share=office_share,
            agent_share=agent_share,
            amount_toward_cap=0,
            cap_before=0,
            cap_after=0,
            compliance_fee_amount=compliance_fee_amount,
            compliance_fee_payer=compliance_fee_payer,
            compliance_to_office=compliance_to_office,
            compliance_to_agent=compliance_to_agent,
            total_payout=total_payout,
            is_capped=False,
            is_post_cap=False,
        )

    # --- Determine split percentages ---
    if agent.split_type == 'tiered':
        agent_pct, office_pct = _get_split_for_tiered(agent, txn_count_in_period)
    else:
        agent_pct = agent.agent_split_pct or 0
        office_pct = agent.office_split_pct or 0

    cap_amount = agent.cap_amount if agent.cap_amount is not None else 0

    # --- $0 Cap (perpetually capped, e.g. Hasan Abbas) ---
    if cap_amount == 0:
        if is_company_lead:
            office_share = round(gross_commission * 0.50, 2)
            agent_share = round(gross_commission - office_share, 2)
        else:
            office_share = 0
            agent_share = gross_commission

        compliance_to_office, compliance_to_agent = _calc_compliance(
            compliance_fee_amount, compliance_fee_payer
        )
        total_payout = agent_share + compliance_to_agent

        return CommissionResult(
            gross_commission=gross_commission,
            agent_split_pct_used=100 if not is_company_lead else 50,
            office_split_pct_used=0 if not is_company_lead else 50,
            office_share=office_share,
            agent_share=agent_share,
            amount_toward_cap=0,
            cap_before=0,
            cap_after=0,
            compliance_fee_amount=compliance_fee_amount,
            compliance_fee_payer=compliance_fee_payer,
            compliance_to_office=compliance_to_office,
            compliance_to_agent=compliance_to_agent,
            total_payout=total_payout,
            is_capped=True,
            is_post_cap=True,
        )

    # --- Already fully capped ---
    if cap_paid_to_date >= cap_amount:
        if is_company_lead:
            office_share = round(gross_commission * 0.50, 2)
            agent_share = round(gross_commission - office_share, 2)
        else:
            office_share = 0
            agent_share = gross_commission

        compliance_to_office, compliance_to_agent = _calc_compliance(
            compliance_fee_amount, compliance_fee_payer
        )
        total_payout = agent_share + compliance_to_agent

        return CommissionResult(
            gross_commission=gross_commission,
            agent_split_pct_used=100 if not is_company_lead else 50,
            office_split_pct_used=0 if not is_company_lead else 50,
            office_share=office_share,
            agent_share=agent_share,
            amount_toward_cap=0,
            cap_before=cap_paid_to_date,
            cap_after=cap_paid_to_date,
            compliance_fee_amount=compliance_fee_amount,
            compliance_fee_payer=compliance_fee_payer,
            compliance_to_office=compliance_to_office,
            compliance_to_agent=compliance_to_agent,
            total_payout=total_payout,
            is_capped=True,
            is_post_cap=True,
        )

    # --- Not yet capped: apply percentage split ---
    office_share_raw = round(gross_commission * (office_pct / 100), 2)
    agent_share_raw = round(gross_commission - office_share_raw, 2)
    cap_remaining = cap_amount - cap_paid_to_date

    if office_share_raw <= cap_remaining:
        # Normal split, does not exceed cap
        office_share = office_share_raw
        agent_share = agent_share_raw
        amount_toward_cap = office_share_raw
        is_capped_now = (cap_paid_to_date + amount_toward_cap) >= cap_amount
    else:
        # This transaction partially fills the cap
        amount_toward_cap = cap_remaining
        is_capped_now = True

        if is_company_lead:
            # Fill cap first, then 50/50 on the rest
            office_from_cap = cap_remaining
            leftover = gross_commission - cap_remaining
            office_from_post_cap = round(leftover * 0.50, 2)
            office_share = round(office_from_cap + office_from_post_cap, 2)
            agent_share = round(gross_commission - office_share, 2)
        else:
            # Fill cap, agent gets everything else
            office_share = cap_remaining
            agent_share = round(gross_commission - cap_remaining, 2)

    cap_after = cap_paid_to_date + amount_toward_cap

    compliance_to_office, compliance_to_agent = _calc_compliance(
        compliance_fee_amount, compliance_fee_payer
    )
    total_payout = agent_share + compliance_to_agent

    return CommissionResult(
        gross_commission=gross_commission,
        agent_split_pct_used=agent_pct,
        office_split_pct_used=office_pct,
        office_share=office_share,
        agent_share=agent_share,
        amount_toward_cap=amount_toward_cap,
        cap_before=cap_paid_to_date,
        cap_after=cap_after,
        compliance_fee_amount=compliance_fee_amount,
        compliance_fee_payer=compliance_fee_payer,
        compliance_to_office=compliance_to_office,
        compliance_to_agent=compliance_to_agent,
        total_payout=total_payout,
        is_capped=is_capped_now,
        is_post_cap=False,
    )


def _calc_compliance(fee_amount: float, payer: str) -> tuple[float, float]:
    """Returns (compliance_to_office, compliance_to_agent).
    compliance_to_agent is negative when agent waived (deducted from payout).
    """
    if fee_amount <= 0:
        return 0.0, 0.0
    if payer == 'agent_waived':
        return fee_amount, -fee_amount  # office gets it, agent pays it
    else:
        return fee_amount, 0.0  # buyer/seller pays, agent unaffected
