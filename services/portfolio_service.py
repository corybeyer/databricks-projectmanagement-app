"""Portfolio Service — KPI calculations and portfolio data."""

from repositories import portfolio_repo


def get_dashboard_data(user_token: str = None) -> dict:
    """Get all data needed for the dashboard page."""
    portfolios = portfolio_repo.get_portfolios(user_token=user_token)

    if portfolios.empty:
        return {
            "portfolios": portfolios,
            "total_projects": 0, "avg_completion": 0,
            "total_budget": 0, "total_spent": 0,
            "green_count": 0, "yellow_count": 0, "red_count": 0,
        }

    return {
        "portfolios": portfolios,
        "total_projects": int(portfolios["project_count"].sum()),
        "avg_completion": float(portfolios["avg_completion"].mean()),
        "total_budget": float(portfolios["total_budget"].sum()),
        "total_spent": float(portfolios["total_spent"].sum()),
        "green_count": len(portfolios[portfolios["health"] == "green"]),
        "yellow_count": len(portfolios[portfolios["health"] == "yellow"]),
        "red_count": len(portfolios[portfolios["health"] == "red"]),
    }


def get_portfolio_projects(portfolio_id: str, user_token: str = None):
    return portfolio_repo.get_portfolio_projects(portfolio_id, user_token=user_token)
