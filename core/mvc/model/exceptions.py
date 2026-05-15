class DoublonError(Exception):
    """
    Levée par un model quand une contrainte d'unicité est violée.

    Usage dans un model :
        except mariadb.IntegrityError:
            raise DoublonError(client["ClientId"])

    Usage dans un controller :
        except DoublonError as e:
            validator.add_error(f"L'ID « {e} » existe déjà.")
    """
