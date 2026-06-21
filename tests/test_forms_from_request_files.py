
from core.forms import Form, ImageField, FileField, StringField
from forge_mvc_testing import FakeRequest


class DummyUpload:
    def __init__(self, filename="photo.jpg", size=100, content_type="image/jpeg"):
        self.filename = filename
        self.size = size
        self.content_type = content_type


class PhotoForm(Form):
    photo = ImageField(required=True)


class DocForm(Form):
    doc = FileField(required=False)


class MixedForm(Form):
    nom = FileField(required=False)


# 1. Comportement classique body uniquement

def test_from_request_lit_le_body():
    req = FakeRequest("POST", "/", body={"nom": "Alice"})

    class SimpleForm(Form):
        nom = StringField()

    form = SimpleForm.from_request(req)
    assert form.raw_data["nom"] == ["Alice"]


# 2. Requête sans attribut files (compatibilité)

def test_from_request_sans_attribut_files():
    req = FakeRequest("POST", "/", body={"x": "1"})
    del req.files  # simule une requête qui n'a pas files

    class SimpleForm(Form):
        x = StringField()

    form = SimpleForm.from_request(req)
    assert form.raw_data.get("x") == ["1"]


# 3. Fichiers injectés depuis request.files

def test_from_request_injecte_fichier():
    upload = DummyUpload()
    req = FakeRequest("POST", "/", files={"photo": upload})
    form = PhotoForm.from_request(req)
    assert form.raw_data.get("photo") is upload


# 4. request.body non modifié en place

def test_from_request_ne_modifie_pas_body():
    upload = DummyUpload()
    req = FakeRequest("POST", "/", body={"nom": "Alice"}, files={"photo": upload})
    original_keys = set(req.body.keys())
    PhotoForm.from_request(req)
    assert set(req.body.keys()) == original_keys
    assert "photo" not in req.body


# 5. files gagne sur body pour la même clé

def test_from_request_files_ecrase_body():
    upload = DummyUpload()
    req = FakeRequest("POST", "/", body={"nom": [""]}, files={"nom": upload})
    form = MixedForm.from_request(req)
    assert form.raw_data["nom"] is upload


# 6. ImageField required=True reçoit le fichier et est valide

def test_image_field_required_recoit_upload_depuis_files():
    upload = DummyUpload(filename="photo.jpg", content_type="image/jpeg")
    req = FakeRequest("POST", "/", files={"photo": upload})
    form = PhotoForm.from_request(req)
    assert form.is_valid(), form.errors


# 7. FileField required=False absent reste valide et vaut None

def test_file_field_optionnel_absent_reste_valide():
    req = FakeRequest("POST", "/")
    form = DocForm.from_request(req)
    assert form.is_valid(), form.errors
    assert form.cleaned_data.get("doc") is None
