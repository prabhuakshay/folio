import pytest
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.db import models
from django.urls import reverse
from django.utils.module_loading import import_string


def test_robots_txt_disallows_everything(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert response.content.decode() == "User-agent: *\nDisallow: /\n"


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/robots.txt", "/healthz", "/", "/nowhere"])
def test_every_response_asks_not_to_be_indexed(client, path):
    assert client.get(path)["X-Robots-Tag"] == "noindex"


@pytest.mark.django_db
def test_pages_refuse_framing_and_keep_referrers_on_site(client):
    response = client.get(reverse("login"))

    assert response["X-Frame-Options"] == "DENY"
    assert response["Referrer-Policy"] == "same-origin"


@pytest.mark.django_db
def test_https_responses_carry_an_hour_of_hsts_without_preload(client):
    response = client.get(reverse("login"), secure=True)

    assert response["Strict-Transport-Security"] == "max-age=3600"


def test_no_model_stores_files_on_disk():
    file_fields = [
        f"{model.__name__}.{field.name}"
        for model in apps.get_models()
        for field in model._meta.get_fields()
        if isinstance(field, models.FileField)
    ]

    assert file_fields == []


def test_uploads_never_spill_to_temp_files(settings):
    handlers = [import_string(path) for path in settings.FILE_UPLOAD_HANDLERS]

    assert not any(issubclass(h, TemporaryFileUploadHandler) for h in handlers)


def test_saved_files_stay_off_disk(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path

    default_storage.save("statement.pdf", ContentFile(b"%PDF"))

    assert list(tmp_path.iterdir()) == []
