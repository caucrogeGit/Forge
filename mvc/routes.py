from core.http.router import Router
from mvc.controllers.auth_controller import AuthController
from mvc.controllers.home_controller import HomeController

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", HomeController.index, name="home")

with router.group("", public=True) as pub:
    pub.add("GET",  "/login",  AuthController.login_form, name="login_form")
    pub.add("POST", "/login",  AuthController.login,      name="login")
    pub.add("POST", "/logout", AuthController.logout,     name="logout")
