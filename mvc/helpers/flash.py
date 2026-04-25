from core.templating.manager import template_manager
from core.security.session import get_session_id, get_flash

_CLASSES = {
    "success": "bg-green-100 border-green-400 text-green-800",
    "error"  : "bg-red-100 border-red-400 text-red-800",
    "warning": "bg-gray-100 border-gray-300 text-gray-800",
    "info"   : "bg-gray-100 border-gray-300 text-gray-800",
}


def render_flash_html(request) -> str:
    flash = get_flash(get_session_id(request))
    if not flash:
        return ""
    classes = _CLASSES.get(flash["level"], _CLASSES["success"])
    return template_manager.render("partials/flash.html", {"message": flash["message"], "classes": classes})
