from core.mvc.view.pagination import Pagination
from tests.fake_request import FakeRequest


def test_pagination_expose_limit_offset_et_contexte_standard():
    request = FakeRequest("GET", "/contacts", params={"page": "3"})
    pagination = Pagination(request, total=95, par_page=10)

    assert pagination.page == 3
    assert pagination.limit == 10
    assert pagination.offset == 20
    assert pagination.pages == 10
    assert pagination.has_previous is True
    assert pagination.previous_page == 2
    assert pagination.has_next is True
    assert pagination.next_page == 4
    assert pagination.to_dict()["nb_pages"] == 10
    assert pagination.context["pagination"]["offset"] == 20


def test_pagination_borne_la_page_demandee():
    request = FakeRequest("GET", "/contacts", params={"page": "999"})
    pagination = Pagination(request, total=12, par_page=5)

    assert pagination.page == 3
    assert pagination.offset == 10
