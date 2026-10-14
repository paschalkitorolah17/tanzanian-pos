from .branch_utils import get_current_branch, get_user_branches


def branch_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'current_branch': get_current_branch(request),
        'user_branches': get_user_branches(request.user),
    }
