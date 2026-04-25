from core.forge import get as _cfg


class Pagination:
    """
    Encapsule la logique de pagination pour les vues liste.

    Usage :
        pagination = Pagination(request, count_clients(), PAR_PAGE)
        items      = get_clients_page(pagination.page, PAR_PAGE)
        context    = {"lignes": ..., **pagination.context}
    """

    def __init__(self, request, total, par_page):
        self.total    = max(int(total or 0), 0)
        self.par_page = max(int(par_page or 1), 1)
        self.nb_pages = -(-self.total // self.par_page) if self.total else 1
        self.page     = self._extraire_page(request, self.nb_pages)
        self.limit    = self.par_page
        self.offset   = (self.page - 1) * self.par_page
        self.pages    = self.nb_pages

    @staticmethod
    def _extraire_page(request, nb_pages):
        try:
            page = int(request.params.get("page", [1])[0])
        except (ValueError, TypeError):
            page = 1
        return min(max(page, 1), nb_pages)

    @property
    def context(self):
        """Retourne le dict prêt à injecter dans le template."""
        payload = self.to_dict()
        return {
            "page"     : self.page,
            "nb_pages" : self.nb_pages,
            "prev_page": self.page - 1 if self.page > 1 else "",
            "next_page": self.page + 1 if self.page < self.nb_pages else "",
            "has_prev" : _cfg("css_visible") if self.page > 1 else _cfg("css_hidden"),
            "has_next" : _cfg("css_visible") if self.page < self.nb_pages else _cfg("css_hidden"),
            "total"    : self.total,
            "par_page" : self.par_page,
            "limit"    : self.limit,
            "offset"   : self.offset,
            "pagination": payload,
        }

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.nb_pages

    @property
    def previous_page(self) -> int | None:
        return self.page - 1 if self.has_previous else None

    @property
    def next_page(self) -> int | None:
        return self.page + 1 if self.has_next else None

    def to_dict(self):
        return {
            "page"     : self.page,
            "nb_pages" : self.nb_pages,
            "pages"    : self.pages,
            "prev_page": self.previous_page,
            "previous_page": self.previous_page,
            "next_page": self.next_page,
            "has_prev" : self.has_previous,
            "has_previous": self.has_previous,
            "has_next" : self.has_next,
            "total"    : self.total,
            "par_page" : self.par_page,
            "limit"    : self.limit,
            "offset"   : self.offset,
        }
