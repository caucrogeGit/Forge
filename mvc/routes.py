from core.mvc.controller.base_controller import BaseController
from core.http.router import Router
from mvc.controllers.auth_controller import AuthController, mfa_available

router = Router()

with router.group("", public=True) as pub:
    pub.add("GET", "/", lambda req: BaseController.redirect("/welcome"), name="home")

with router.group("", public=True) as pub:
    pub.add("GET",  "/login",  AuthController.login_form, name="login_form")
    pub.add("POST", "/login",  AuthController.login,      name="login")
    pub.add("POST", "/logout", AuthController.logout,     name="logout")

if mfa_available():
    from mvc.controllers.mfa_challenge_controller import MfaChallengeController
    with router.group("", public=True) as pub:
        pub.add("GET",  "/login/mfa", MfaChallengeController.form,   name="mfa_challenge_form")
        pub.add("POST", "/login/mfa", MfaChallengeController.verify, name="mfa_challenge_verify")

# forge-starter:welcome:start
from mvc.controllers.welcome_controller import WelcomeController

with router.group("", public=True) as pub:
    pub.add("GET", "/welcome", WelcomeController.index, name="welcome_index")
# forge-starter:welcome:end
