from core.mvc.controller.base_controller import BaseController


class HomeController(BaseController):

    @staticmethod
    def index(request):
        return BaseController.render("landing/index.html", request=request)
