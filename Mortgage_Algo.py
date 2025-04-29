import math
from typing import List, Dict, Tuple, Optional


class Mortgage:
    def __init__(
        self,
        principal: float,
        annual_rate: float,
        years: float,
        compounds_per_year: int = 12,
    ):
        """
        Mortgage loan initializer.

        :param principal: Initial loan amount
        :param annual_rate: Annual interest rate (percentage, e.g., 4.5 for 4.5%)
        :param years: Term of the loan in years
        :param compounds_per_year: How many times interest is compounded per year (default 12)
        """
        self.principal = principal
        self.annual_rate = annual_rate / 100.0
        self.years = years
        self.compounds_per_year = compounds_per_year
        self.monthly_rate = self.annual_rate / compounds_per_year
        self.total_periods = int(years * compounds_per_year)
        # standard payment formula
        self.monthly_payment = self._calc_periodic_payment()

    def _calc_periodic_payment(self) -> float:
        """Compute the fixed periodic payment (annuity formula)."""
        r = self.monthly_rate
        n = self.total_periods
        P = self.principal
        return P * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def amortization_schedule(
        self,
        recurring_extra: float = 0.0,
        lumpsum_extras: Optional[Dict[int, float]] = None,
    ) -> List[Dict[str, float]]:
        """
        Generate the amortization schedule.

        :param recurring_extra: flat extra payment added every period
        :param lumpsum_extras: dict mapping period index (1-based) -> extra payment
        :return: List of dicts with keys:
                 period, payment, interest, principal, extra, balance
        """
        if lumpsum_extras is None:
            lumpsum_extras = {}

        schedule = []
        balance = self.principal

        for period in range(1, self.total_periods + 1):
            interest = balance * self.monthly_rate
            principal_paid = self.monthly_payment - interest
            extra = recurring_extra + lumpsum_extras.get(period, 0.0)

            # If final payment would overpay
            if principal_paid + extra > balance:
                principal_paid = balance
                payment = balance + interest
                extra = 0.0
            else:
                payment = self.monthly_payment + extra

            balance -= principal_paid + extra
            schedule.append({
                "period": period,
                "payment": payment,
                "interest": interest,
                "principal": principal_paid,
                "extra": extra,
                "balance": max(balance, 0.0),
            })

            if balance <= 0:
                break

        return schedule

    def summarize_schedule(
        self,
        schedule: List[Dict[str, float]],
    ) -> Dict[str, float]:
        """
        Summarize a given amortization schedule.

        :param schedule: output from amortization_schedule()
        :return: Dict with total_paid, total_interest, periods_used
        """
        total_paid = sum(x["payment"] for x in schedule)
        total_interest = sum(x["interest"] for x in schedule)
        return {
            "total_paid": total_paid,
            "total_interest": total_interest,
            "periods_used": schedule[-1]["period"],
        }

    def optimize_extra(
        self,
        total_extra_budget: float,
        start_period: int = 1,
    ) -> Tuple[str, Dict[str, float]]:
        """
        Compare several extra-payment strategies and pick the one
        that minimizes total interest paid.

        Strategies evaluated:
          1) Single lump-sum at start_period
          2) Uniform recurring monthly extra
          3) Annual lump-sums at the first period of each year

        :param total_extra_budget: total budget available for extra payments
        :param start_period: earliest period for applying extra payments
        :return: (best_strategy_name, summary_of_best)
        """
        results = {}

        # Strategy 1: Single lump-sum at start_period
        lumpsum = {start_period: total_extra_budget}
        sched = self.amortization_schedule(lumpsum_extras=lumpsum)
        results["single_lumpsum"] = self.summarize_schedule(sched)

        # Strategy 2: Uniform monthly extra
        remaining_periods = self.total_periods - start_period + 1
        if remaining_periods > 0:
            monthly_extra = total_extra_budget / remaining_periods
            sched = self.amortization_schedule(
                recurring_extra=monthly_extra,
                lumpsum_extras=None
            )
            results["uniform_monthly"] = self.summarize_schedule(sched)

        # Strategy 3: Annual lump-sums at year-start
        years = math.ceil((self.total_periods - start_period + 1) / self.compounds_per_year)
        annual_extra = total_extra_budget / years
        lumpsum_annual = {
            start_period + (i * self.compounds_per_year): annual_extra
            for i in range(years)
            if start_period + (i * self.compounds_per_year) <= self.total_periods
        }
        sched = self.amortization_schedule(lumpsum_extras=lumpsum_annual)
        results["annual_lumpsum"] = self.summarize_schedule(sched)

        # Select best strategy (lowest total_interest)
        best = min(results.items(), key=lambda kv: kv[1]["total_interest"])
        best_name, best_summary = best
        return best_name, best_summary


if __name__ == "__main__":
    # Example usage
    principal = float(input("Principal amount: "))
    annual_rate = float(input("Annual interest rate (%, e.g. 3.75): "))
    years = float(input("Term (years): "))
    extra_budget = float(input("Total extra payment budget: "))
    start_period = int(input(
        "Start applying extras at period (1-based month number, default 1): ") or "1"
    )

    loan = Mortgage(principal, annual_rate, years)

    # Baseline without extra
    base_sched = loan.amortization_schedule()
    base_summary = loan.summarize_schedule(base_sched)
    print("\n=== Baseline (no extra payments) ===")
    print(f"  Periods: {base_summary['periods_used']} months")
    print(f"  Total paid: {base_summary['total_paid']:.2f}")
    print(f"  Total interest: {base_summary['total_interest']:.2f}")

    # Find the best extra-payment strategy
    best_strategy, best_summary = loan.optimize_extra(extra_budget, start_period)
    print(f"\n=== Optimal extra-payment strategy: {best_strategy} ===")
    print(f"  Periods: {best_summary['periods_used']} months")
    print(f"  Total paid: {best_summary['total_paid']:.2f}")
    print(f"  Total interest: {best_summary['total_interest']:.2f}")
