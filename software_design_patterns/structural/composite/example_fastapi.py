from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request

from structural.composite.example_finance import Bond
from structural.composite.example_finance import Cash
from structural.composite.example_finance import Instrument
from structural.composite.example_finance import Portfolio
from structural.composite.example_finance import Stock

app = FastAPI()


def build_household_portfolio():
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

    return household


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: build the portfolio tree once
    portfolio = build_household_portfolio()
    app.state.portfolio = portfolio
    print(f"[Lifespan] Loaded portfolio: ${portfolio.get_value():,.2f}")
    yield
    # SHUTDOWN: cleanup
    print("[Lifespan] Shutting down")


app = FastAPI(lifespan=lifespan)


@app.get("/portfolio/value")
async def get_value(request: Request):
    portfolio: Portfolio = request.app.state.portfolio
    return {
        "name": portfolio.name,
        "total_value": portfolio.get_value(),
        "blended_risk": round(portfolio.get_risk(), 3),
    }


@app.get("/portfolio/report")
async def get_report(request: Request):
    portfolio: Portfolio = request.app.state.portfolio
    return _to_nested_dict(portfolio)


def _to_nested_dict(item: Instrument) -> dict:
    """Recursively serialize the tree — again, uniform for leaves and composites."""
    return {
        "name": item.name,
        "value": item.get_value(),
        "risk": round(item.get_risk(), 3),
        "children": [_to_nested_dict(c) for c in item.get_children()],
    }


@app.post("/portfolio/{name}/add-stock")
async def add_stock(request: Request, name: str, ticker: str, shares: float, price: float):
    portfolio: Portfolio = request.app.state.portfolio
    target = _find(portfolio, name)
    if not isinstance(target, Portfolio):
        raise HTTPException(400, f"'{name}' is not a portfolio — can't add children to a leaf")
    target.add(Stock(ticker, shares, price))
    return {"total_value": portfolio.get_value()}


def _find(item: Instrument, name: str) -> Instrument | None:
    if item.name == name:
        return item
    for child in item.get_children():
        found = _find(child, name)
        if found:
            return found
    return None


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
