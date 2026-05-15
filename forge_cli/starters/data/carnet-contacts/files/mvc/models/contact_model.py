from core.database.db import execute, fetch_all, fetch_one, insert


SELECT_CONTACTS = """
SELECT
    contact.ContactId,
    contact.Nom,
    contact.Prenom,
    contact.Email,
    contact.Telephone,
    contact.VilleId,
    ville.Nom AS VilleNom,
    ville.CodePostal AS VilleCodePostal
FROM contact
LEFT JOIN ville ON ville.VilleId = contact.VilleId
ORDER BY contact.Nom, contact.Prenom
"""

SELECT_CONTACT_BY_ID = """
SELECT
    contact.ContactId,
    contact.Nom,
    contact.Prenom,
    contact.Email,
    contact.Telephone,
    contact.VilleId,
    ville.Nom AS VilleNom,
    ville.CodePostal AS VilleCodePostal
FROM contact
LEFT JOIN ville ON ville.VilleId = contact.VilleId
WHERE contact.ContactId = ?
LIMIT 1
"""

INSERT_CONTACT = """
INSERT INTO contact (Nom, Prenom, Email, Telephone, VilleId)
VALUES (?, ?, ?, ?, ?)
"""

UPDATE_CONTACT = """
UPDATE contact
SET Nom = ?, Prenom = ?, Email = ?, Telephone = ?, VilleId = ?
WHERE ContactId = ?
"""

DELETE_CONTACT = "DELETE FROM contact WHERE ContactId = ?"


def _clean_payload(data: dict) -> tuple:
    return (
        data["nom"],
        data["prenom"],
        data["email"],
        data.get("telephone") or None,
        data.get("ville_id") or None,
    )


def get_contacts():
    return fetch_all(SELECT_CONTACTS)


def get_contact_by_id(contact_id: int):
    return fetch_one(SELECT_CONTACT_BY_ID, (contact_id,))


def add_contact(data: dict) -> int:
    return insert(INSERT_CONTACT, _clean_payload(data))


def update_contact(contact_id: int, data: dict) -> None:
    execute(UPDATE_CONTACT, (*_clean_payload(data), contact_id))


def delete_contact(contact_id: int) -> None:
    execute(DELETE_CONTACT, (contact_id,))
