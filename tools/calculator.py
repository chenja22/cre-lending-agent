def calculate_dscr(noi: float, annual_debt_service: float) -> float:
    """Net Operating Income / Annual Debt Service"""
    if annual_debt_service == 0:
        return 0
    return round(noi / annual_debt_service, 2)

def calculate_ltv(loan_amount: float, appraised_value: float) -> float:
    """Loan Amount / Appraised Value"""
    if appraised_value == 0:
        return 0
    return round(loan_amount / appraised_value, 4)

def calculate_debt_yield(noi: float, loan_amount: float) -> float:
    """NOI / Loan Amount — leverage neutral stress test"""
    if loan_amount == 0:
        return 0
    return round(noi / loan_amount, 4)

def calculate_annual_debt_service(
    loan_amount: float,
    interest_rate: float,
    amortization_years: int
) -> float:
    """Monthly mortgage payment * 12 using standard amortization formula"""
    if amortization_years == 0 or interest_rate == 0:
        return loan_amount  # interest only fallback
    monthly_rate = (interest_rate / 100) / 12
    n = amortization_years * 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)
    return round(monthly_payment * 12, 2)

def calculate_stress_dscr(noi: float, annual_debt_service: float, stress_rate: float = 0.08) -> float:
    """DSCR if interest rate rises to stress_rate (default 8%)"""
    # Approximate: scale debt service by rate increase
    stressed_ds = annual_debt_service * (stress_rate / 0.0675)
    return calculate_dscr(noi, stressed_ds)

def flag_deal(dscr: float, ltv: float, debt_yield: float) -> str:
    """Simple pass/watch/fail logic based on standard CRE thresholds"""
    if dscr >= 1.25 and ltv <= 0.75 and debt_yield >= 0.08:
        return "PASS"
    elif dscr >= 1.10 and ltv <= 0.80:
        return "WATCH"
    else:
        return "FAIL"