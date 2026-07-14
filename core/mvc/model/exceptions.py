# pyright: strict
class DoublonError(Exception):
    """
    Levée par un model quand une contrainte d'unicité est violée.

    Usage dans un model :
        except mariadb.IntegrityError:
            raise DoublonError(client["ClientId"])

    Usage dans un controller :
        except DoublonError as e:
            form.add_error("client_id", f"L'ID « {e} » existe déjà.")
    """
