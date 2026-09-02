"""`STATS-IP-ANONYMISATION-001`, `STATS-EVENT-KIND-001`, `DOC-STATS-AGGREGATES-001`.

`forge-mvc-stats` ne stockait **aucune** adresse : sa table n'a pas de colonne
pour cela, et ce n'est pas un oubli mais son périmètre. Il compte des
événements, il n'enquête pas.

`metadata` est pourtant libre, et rien n'empêchait d'y écrire
`{"ip": request.remote_addr}`. C'est le geste naturel de qui veut compter des
visiteurs uniques, et il transforme une table de statistiques en fichier de
données personnelles sans que personne ne l'ait décidé.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

pytest.importorskip("forge_mvc_stats")

from forge_mvc_stats.aggregate import (  # noqa: E402
    StatsAggregateError,
    get_stats_counts_sql,
    prepare_stats_counts_params,
)
from forge_mvc_stats.events import (  # noqa: E402
    EVENT_KINDS,
    KIND_ACTION,
    KIND_PAGE_VIEW,
    StatsEvent,
    StatsEventError,
)
from forge_mvc_stats.privacy import (  # noqa: E402
    ADDRESS_KEYS,
    IPV4_KEEP_BITS,
    IPV6_KEEP_BITS,
    StatsPrivacyError,
    anonymize_ip,
    assert_no_raw_address,
    looks_like_address_key,
    visitor_hash,
)
from forge_mvc_stats.tracking import (  # noqa: E402
    get_track_event_sql,
    prepare_track_event_values,
)


# ------------------------------------------------- STATS-IP-ANONYMISATION


class TestTroncature:

    def test_ipv4_perd_son_dernier_octet(self) -> None:
        assert anonymize_ip("203.0.113.42") == "203.0.113.0"

    def test_ipv6_perd_tout_ce_qui_suit_son_48(self) -> None:
        assert anonymize_ip("2001:db8:85a3:1234:5678:8a2e:370:7334") == "2001:db8:85a3::"

    def test_les_bits_conserves_sont_ceux_admis(self) -> None:
        assert (IPV4_KEEP_BITS, IPV6_KEEP_BITS) == (24, 48)

    def test_une_adresse_deja_tronquee_ne_change_pas(self) -> None:
        assert anonymize_ip("203.0.113.0") == "203.0.113.0"

    @pytest.mark.parametrize("mauvais", ["", "  ", "pas une ip", "999.1.1.1", "1.2.3"])
    def test_une_valeur_qui_n_est_pas_une_adresse_leve(self, mauvais: str) -> None:
        with pytest.raises(StatsPrivacyError, match="invalide"):
            anonymize_ip(mauvais)


class TestEmpreinteTournante:

    def test_deux_visites_du_meme_jour_donnent_la_meme_empreinte(self) -> None:
        jour = date(2026, 9, 2)

        assert visitor_hash("203.0.113.42", "s", day=jour) == visitor_hash(
            "203.0.113.42", "s", day=jour
        )

    def test_le_lendemain_donne_une_autre_empreinte(self) -> None:
        """C'est ce qui empêche de suivre un visiteur dans la durée."""
        assert visitor_hash("203.0.113.42", "s", day=date(2026, 9, 2)) != visitor_hash(
            "203.0.113.42", "s", day=date(2026, 9, 3)
        )

    def test_deux_adresses_donnent_deux_empreintes(self) -> None:
        jour = date(2026, 9, 2)

        assert visitor_hash("203.0.113.1", "s", day=jour) != visitor_hash(
            "203.0.113.2", "s", day=jour
        )

    def test_le_secret_change_l_empreinte(self) -> None:
        jour = date(2026, 9, 2)

        assert visitor_hash("203.0.113.1", "a", day=jour) != visitor_hash(
            "203.0.113.1", "b", day=jour
        )

    def test_l_empreinte_ne_contient_pas_l_adresse(self) -> None:
        empreinte = visitor_hash("203.0.113.42", "s", day=date(2026, 9, 2))

        assert "203" not in empreinte
        assert "113" not in empreinte

    def test_un_secret_vide_leve(self) -> None:
        """Sans lui, l'espace des adresses IPv4 se parcourt en quelques secondes."""
        with pytest.raises(StatsPrivacyError, match="secret"):
            visitor_hash("203.0.113.1", "")

    def test_un_datetime_est_ramene_a_sa_journee(self) -> None:
        jour = date(2026, 9, 2)
        instant = datetime(2026, 9, 2, 23, 59)

        assert visitor_hash("1.1.1.1", "s", day=instant) == visitor_hash(
            "1.1.1.1", "s", day=jour
        )

    def test_une_adresse_invalide_leve(self) -> None:
        with pytest.raises(StatsPrivacyError):
            visitor_hash("pas une ip", "s")


class TestRefusDAdresseBrute:
    """Le refus a lieu à l'écriture : la ligne ne doit pas exister."""

    @pytest.mark.parametrize("cle", sorted(ADDRESS_KEYS))
    def test_toutes_les_cles_d_adresse_sont_couvertes(self, cle: str) -> None:
        with pytest.raises(StatsPrivacyError):
            assert_no_raw_address({cle: "203.0.113.42"})

    def test_la_casse_et_le_tiret_sont_absorbes(self) -> None:
        with pytest.raises(StatsPrivacyError):
            assert_no_raw_address({"Client-IP": "203.0.113.42"})

    def test_une_adresse_deja_tronquee_passe(self) -> None:
        """Accepter serait incohérent avec le fait de proposer la troncature."""
        assert_no_raw_address({"ip": "203.0.113.0"})

    def test_une_empreinte_passe(self) -> None:
        assert_no_raw_address({"ip": visitor_hash("203.0.113.42", "s")})

    def test_un_numero_de_version_n_est_pas_une_adresse(self) -> None:
        """« 1.2.3.4 » est une adresse IPv4 valide ET un numéro de version.

        Le contrôle porte sur la CLÉ, sans quoi il casserait des métadonnées
        parfaitement légitimes.
        """
        assert_no_raw_address({"version": "1.2.3.4"})
        assert_no_raw_address({"build": "10.0.19041.1"})

    def test_une_valeur_qui_n_est_pas_une_adresse_passe(self) -> None:
        assert_no_raw_address({"ip": "inconnue"})

    def test_une_valeur_non_textuelle_passe(self) -> None:
        assert_no_raw_address({"ip": 42})

    def test_ipv6_est_refusee_aussi(self) -> None:
        with pytest.raises(StatsPrivacyError):
            assert_no_raw_address({"ip": "2001:db8:85a3:1234:5678:8a2e:370:7334"})

    def test_le_message_nomme_les_deux_solutions(self) -> None:
        with pytest.raises(StatsPrivacyError) as leve:
            assert_no_raw_address({"ip": "203.0.113.42"})

        message = str(leve.value)
        assert "visitor_hash" in message and "anonymize_ip" in message

    def test_le_message_oriente_vers_audit_pour_la_securite(self) -> None:
        """Conserver une adresse à des fins de sécurité n'est pas une
        statistique : c'est le périmètre de forge-mvc-audit."""
        with pytest.raises(StatsPrivacyError, match="forge-mvc-audit"):
            assert_no_raw_address({"remote_addr": "203.0.113.42"})

    def test_une_cle_ordinaire_n_est_pas_une_cle_d_adresse(self) -> None:
        assert not looks_like_address_key("page")
        assert looks_like_address_key("REMOTE_ADDR")


class TestGardeALEcriture:

    def test_un_evenement_portant_une_adresse_est_refuse(self) -> None:
        with pytest.raises(StatsPrivacyError):
            StatsEvent(name="page_vue", metadata={"ip": "203.0.113.42"})

    def test_un_evenement_ordinaire_passe(self) -> None:
        evenement = StatsEvent(name="page_vue", metadata={"page": "/accueil"})

        assert evenement.metadata == {"page": "/accueil"}

    def test_une_empreinte_dans_les_metadonnees_passe(self) -> None:
        evenement = StatsEvent(
            name="page_vue",
            metadata={"visiteur": visitor_hash("203.0.113.42", "secret")},
        )

        assert evenement.metadata["visiteur"]


# ------------------------------------------------------ STATS-EVENT-KIND


class TestTypeDEvenement:

    def test_le_vocabulaire_est_ferme(self) -> None:
        """Un troisième type inventé par une application le rendrait
        incomparable d'un projet à l'autre, ce qui est ce que le champ doit
        permettre."""
        assert EVENT_KINDS == {KIND_PAGE_VIEW, KIND_ACTION}

    def test_le_defaut_est_l_action(self) -> None:
        """Les événements déjà en base viennent d'appels délibérés de
        l'application, jamais d'un suivi de page."""
        assert StatsEvent(name="commande_passee").kind == KIND_ACTION

    def test_une_vue_de_page_se_declare(self) -> None:
        assert StatsEvent(name="page_vue", kind=KIND_PAGE_VIEW).kind == KIND_PAGE_VIEW

    def test_la_casse_et_les_espaces_sont_absorbees(self) -> None:
        assert StatsEvent(name="p", kind="  PAGE_VIEW ").kind == KIND_PAGE_VIEW

    @pytest.mark.parametrize("mauvais", ["clic", "", "vue", "page-view", None])
    def test_un_type_inconnu_leve(self, mauvais: Any) -> None:
        with pytest.raises(StatsEventError, match="kind invalide"):
            StatsEvent(name="p", kind=mauvais)

    def test_il_est_orthogonal_a_la_categorie(self) -> None:
        """`category` est la taxonomie libre de l'application ; le type dit si
        l'événement est passif ou délibéré."""
        evenement = StatsEvent(name="p", category="boutique", kind=KIND_PAGE_VIEW)

        assert (evenement.category, evenement.kind) == ("boutique", KIND_PAGE_VIEW)

    def test_l_insertion_porte_le_type(self) -> None:
        assert "kind" in get_track_event_sql()
        assert prepare_track_event_values(StatsEvent(name="p"))[-1] == KIND_ACTION

    def test_le_nombre_de_marqueurs_suit_le_nombre_de_valeurs(self) -> None:
        """Un marqueur de trop ou de moins fait échouer l'insertion sur les
        quatre backends, avec un message qui ne dit pas lequel manque."""
        sql = get_track_event_sql()
        valeurs = prepare_track_event_values(StatsEvent(name="p"))

        assert sql.count("?") == len(valeurs)


class TestColonneKind:

    def test_elle_est_declaree_dans_la_table(self) -> None:
        from forge_mvc_stats.tables import STATS_EVENTS, STATS_EVENTS_COLUMNS

        assert "kind" in STATS_EVENTS_COLUMNS
        assert any(c.name == "kind" for c in STATS_EVENTS.columns)

    def test_une_migration_additive_est_livree(self) -> None:
        """Une table déjà créée ne se recrée pas : l'ALTER est la seule façon
        de la faire évoluer sans perdre les événements enregistrés."""
        from forge_mvc_stats.tables import ADDED_COLUMNS

        assert any(ajout.column_name == "kind" for _, ajout in ADDED_COLUMNS)

    def test_l_alter_se_rend_sur_le_backend_actif(self) -> None:
        from core.database.backend import get_backend
        from core.database.table_ddl import render_add_column

        from forge_mvc_stats.tables import ADDED_COLUMNS

        for _, ajout in ADDED_COLUMNS:
            instructions = render_add_column(
                ajout.table, ajout.column_name, get_backend().dialect, ajout.index_names
            )
            assert instructions
            assert any("kind" in i for i in instructions)


# --------------------------------------------------- DOC-STATS-AGGREGATES


class TestAgregationParJour:

    def test_elle_existe(self) -> None:
        """Grouper par journée demandait de rapatrier tous les horodatages pour
        les tronquer en Python."""
        sql = get_stats_counts_sql("day")

        assert "GROUP BY" in sql and "created_at" in sql

    def test_l_expression_vient_du_dialecte(self) -> None:
        """Aucun des quatre backends n'écrit la troncature de la même façon."""
        from core.database.backend import get_backend

        attendue = get_backend().dialect.date_expression("created_at")

        assert attendue in get_stats_counts_sql("day")

    def test_une_serie_temporelle_est_triee_par_le_temps(self) -> None:
        """Trier une courbe par total décroissant la rendrait illisible."""
        sql = get_stats_counts_sql("day")

        assert "ORDER BY" in sql
        assert "total DESC" not in sql

    def test_les_autres_dimensions_gardent_leur_tri_par_frequence(self) -> None:
        assert "total DESC" in get_stats_counts_sql("name")


class TestDimensionsAutorisees:

    @pytest.mark.parametrize("dimension", ["name", "category", "kind", "day"])
    def test_les_quatre_dimensions_repondent(self, dimension: str) -> None:
        assert get_stats_counts_sql(dimension)

    @pytest.mark.parametrize("mauvais", ["jour", "ip", "created_at", "1=1"])
    def test_une_dimension_inconnue_leve(self, mauvais: str) -> None:
        """`group_by` finit dans un `GROUP BY` : la liste blanche est ce qui
        empêche une injection."""
        with pytest.raises(StatsAggregateError, match="invalide"):
            get_stats_counts_sql(mauvais)

    def test_le_message_liste_les_dimensions(self) -> None:
        with pytest.raises(StatsAggregateError, match="day"):
            get_stats_counts_sql("jour")

    def test_les_params_refusent_aussi_la_dimension_inconnue(self) -> None:
        with pytest.raises(StatsAggregateError):
            prepare_stats_counts_params("jour")


class TestFiltreParType:

    def test_le_filtre_ajoute_un_marqueur(self) -> None:
        sql = get_stats_counts_sql("name", kind=KIND_PAGE_VIEW)
        params = prepare_stats_counts_params("name", kind=KIND_PAGE_VIEW)

        assert "kind = ?" in sql
        assert sql.count("?") == len(params)

    def test_un_type_inconnu_leve_au_lieu_de_rendre_zero(self) -> None:
        """Un filtre qui rend zéro sans motif fait chercher un défaut ailleurs,
        dans les données ou dans l'écriture des événements."""
        with pytest.raises(StatsAggregateError, match="kind invalide"):
            prepare_stats_counts_params("name", kind="clic")

    def test_l_ordre_des_marqueurs_suit_celui_des_params(self) -> None:
        """Un décalage donnerait un filtre appliqué à la mauvaise colonne."""
        sql = get_stats_counts_sql(
            "name", name="page_vue", category="blog", since="2026-01-01",
            kind=KIND_PAGE_VIEW,
        )
        params = prepare_stats_counts_params(
            "name", name="page_vue", category="blog", since="2026-01-01",
            kind=KIND_PAGE_VIEW,
        )

        assert sql.count("?") == len(params) == 4
        assert params[-1] == KIND_PAGE_VIEW
        assert sql.index("name = ?") < sql.index("category = ?")
        assert sql.index("category = ?") < sql.index("created_at >= ?")
        assert sql.index("created_at >= ?") < sql.index("kind = ?")
