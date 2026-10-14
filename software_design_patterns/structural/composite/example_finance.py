from abc import ABC
from abc import abstractmethod


class Instrument(ABC):
    """
    The Component. EVERYTHING in the portfolio is an Instrument —
    individual assets AND portfolios of assets.
    Clients only ever talk to this interface.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_value(self) -> float:
        """Total value in USD."""

    @abstractmethod
    def get_risk(self) -> float:
        """Risk score from 0.0 (cash) to 1.0 (speculative)."""

    def get_children(self) -> list["Instrument"]:
        """
        Leaves return an empty list.
        Composites override this to return their holdings.
        This keeps traversal code 100% uniform.
        """
        return []


# ----- The Leaves (Individual Assets)

class Stock(Instrument):
    def __init__(self, ticker: str, shares: float, price: float, risk: float = 0.8):
        super().__init__(ticker)
        self.ticker = ticker
        self.shares = shares
        self.price = price
        self.risk = risk

    def get_value(self) -> float:
        return self.shares * self.price

    def get_risk(self) -> float:
        return self.risk


class Bond(Instrument):
    def __init__(self, name: str, principal: float, price_ratio: float = 1.0, risk: float = 0.2):
        super().__init__(name)
        self.principal = principal
        self.price_ratio = price_ratio
        self.risk = risk

    def get_value(self) -> float:
        return self.principal * self.price_ratio

    def get_risk(self) -> float:
        return self.risk


class Cash(Instrument):
    def __init__(self, amount: float, currency: str = "USD"):
        super().__init__(f"Cash ({currency})")
        self.amount = amount
        self.risk = 0.0

    def get_value(self) -> float:
        return self.amount

    def get_risk(self) -> float:
        return self.risk


# ----- The Composite (The Portfolio)

class Portfolio(Instrument):
    """
    The Composite. Holds children — which may be leaves OR other portfolios.
    This is what makes the pattern recursive and powerful.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._children: list[Instrument] = []

    # --- Child management (only exists on the Composite) ---
    def add(self, item: Instrument) -> "Portfolio":
        if item is self:
            raise ValueError("A portfolio cannot contain itself")
        # deeper check: walk item's subtree to ensure `self` isn't in it
        self._children.append(item)
        return self

    def remove(self, item: Instrument):
        self._children.remove(item)

    def get_children(self) -> list[Instrument]:
        return self._children

    # --- The magic: recursion through the Component interface ---
    def get_value(self) -> float:
        # Doesn't care if children are stocks, bonds, or whole portfolios!
        return sum(child.get_value() for child in self._children)

    def get_risk(self) -> float:
        total = self.get_value()
        if total == 0:
            return 0.0
        # Value-weighted average risk
        weighted = sum(c.get_value() * c.get_risk() for c in self._children)
        return weighted / total


def print_report(item: Instrument, indent: int = 0) -> None:
    """
    Works on a leaf OR a composite. No type checking needed,
    because get_children() returns [] for leaves.
    """
    pad = "  " * indent
    print(f"{pad}{item.name}: ${item.get_value():>12,.2f}  | risk {item.get_risk():.2f}")
    for child in item.get_children():
        print_report(child, indent + 1)


if __name__ == "__main__":
    # --- LEAVES ---
    aapl = Stock("AAPL", shares=50, price=190.00, risk=0.8)
    msft = Stock("MSFT", shares=30, price=380.00, risk=0.7)
    us_bond = Bond("US-10Y", principal=10_000, price_ratio=0.97)
    reserve = Cash(10_000)

    # --- COMPOSE THEM ---
    tech_bucket = Portfolio("Tech Stocks")
    tech_bucket.add(aapl).add(msft)

    fixed_income = Portfolio("Fixed Income")
    fixed_income.add(us_bond).add(reserve)

    retirement = Portfolio("Retirement 401k")
    retirement.add(tech_bucket).add(fixed_income)

    taxable = Portfolio("Taxable Brokerage")
    taxable.add(Stock("VTI", shares=100, price=250.00, risk=0.75))

    household = Portfolio("Household Portfolio")
    household.add(retirement).add(taxable)

    # --- CLIENT CODE: completely uniform ---
    print(f"Total value: ${household.get_value():,.2f}")
    print(f"Blended risk: {household.get_risk():.2f}")

    print(f"\nA single leaf responds to the same call:")
    print(f"  AAPL value: ${aapl.get_value():,.2f}")

    print(f"\nA sub-portfolio too:")
    print(f"  Tech bucket: ${tech_bucket.get_value():,.2f} \n\n")

    print_report(household)
