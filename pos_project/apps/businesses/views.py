from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .branch_utils import set_current_branch, get_user_branches


@login_required
def switch_branch(request):
    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        branch = set_current_branch(request, branch_id)
        if branch:
            messages.success(request, f'Switched to branch: {branch.name}')
        else:
            messages.error(request, 'Invalid branch')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
