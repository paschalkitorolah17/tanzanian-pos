"""
Helpers for current branch selection.
"""

def get_user_branches(user):
    """Return active branches the user can access."""
    if not user.business:
        return []
    return list(
        user.business.branches.filter(is_active=True).order_by('name')
    )


def get_current_branch(request):
    """
    Return the currently selected branch for this session.
    Falls back to the first available branch.
    """
    from apps.businesses.models import Branch

    branches = get_user_branches(request.user)
    if not branches:
        return None

    branch_id = request.session.get('current_branch_id')
    if branch_id:
        for b in branches:
            if b.id == branch_id:
                return b

    # Default to first branch
    request.session['current_branch_id'] = branches[0].id
    return branches[0]


def set_current_branch(request, branch_id):
    """Set the active branch in the session."""
    branches = get_user_branches(request.user)
    for b in branches:
        if b.id == int(branch_id):
            request.session['current_branch_id'] = b.id
            return b
    return None
