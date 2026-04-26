from core.database.connection import close_connection, get_connection


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
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_CONTACTS)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_contact_by_id(contact_id: int):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_CONTACT_BY_ID, (contact_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def add_contact(data: dict) -> int:
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(INSERT_CONTACT, _clean_payload(data))
        connection.commit()
        return cursor.lastrowid
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def update_contact(contact_id: int, data: dict) -> None:
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(UPDATE_CONTACT, (*_clean_payload(data), contact_id))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def delete_contact(contact_id: int) -> None:
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(DELETE_CONTACT, (contact_id,))
        connection.commit()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
