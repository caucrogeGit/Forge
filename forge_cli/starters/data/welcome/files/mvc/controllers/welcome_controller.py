from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):
    """Cycle HTTP illustré — starter d'entrée Forge sans base de données."""

    @staticmethod
    def index(request):
        return BaseController.render("welcome/index.html", request=request)

    @staticmethod
    def cycle(request):
        return BaseController.render("welcome/cycle.html", request=request)

    @staticmethod
    def request_example(request):
        ctx = {
            "method": request.method,
            "path": request.path,
            "params": {k: v[0] if len(v) == 1 else v for k, v in request.params.items()},
        }
        return BaseController.render("welcome/request_example.html", context=ctx, request=request)

    @staticmethod
    def response_example(request):
        return BaseController.render("welcome/response_example.html", request=request)

    @staticmethod
    def routing_example(request):
        return BaseController.render("welcome/routing_example.html", request=request)

    @staticmethod
    def not_found_demo(request):
        return BaseController.render("welcome/not_found_demo.html", request=request)
