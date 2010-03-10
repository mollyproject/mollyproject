def require_auth(view, redirect=None):
    view.require_auth = redirect
    return view

def require_unauth(view, redirect=None):
    view.require_unauth = redirect
    return view
