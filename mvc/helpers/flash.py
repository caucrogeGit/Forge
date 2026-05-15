from core.templating.manager import template_manager
from core.security.session import get_session_id, get_flash


def render_flash_html(request) -> str:
    flash = get_flash(get_session_id(request))
    if not flash:
        return ""
    return template_manager.render(
        "components/alert.html",
        {"message": flash["message"], "type": flash["level"]},
    )
