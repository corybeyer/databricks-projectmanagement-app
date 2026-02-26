"""Auto Refresh — interval timer for data sections."""

from dash import dcc


def auto_refresh(interval_id="refresh-interval", interval_ms=30_000):
    return dcc.Interval(id=interval_id, interval=interval_ms, n_intervals=0)
