"""Loading Wrapper — dcc.Loading wrapper for data sections."""

from dash import dcc


def loading_wrapper(children, loading_id=None):
    return dcc.Loading(children, type="circle", color="#6366f1", id=loading_id)
