import os

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.business_errors import BUSINESS_ERROR_CASES, ENDPOINT_BUSINESS_CASES
from app.api.docs import ENDPOINT_DOCS, ENDPOINT_ROUTE_MAP


def test_business_error_catalog_prefix_matches_http_status() -> None:
    for case_id, case in BUSINESS_ERROR_CASES.items():
        if case["http_status"] == 400:
            assert case_id.startswith("B400-"), case_id
        elif case["http_status"] == 404:
            assert case_id.startswith("B404-"), case_id
        elif case["http_status"] == 409:
            assert case_id.startswith("B409-"), case_id
        else:
            raise AssertionError(f"HTTP status no soportado: {case['http_status']}")


def test_endpoint_business_matrix_references_existing_cases() -> None:
    for route, matrix in ENDPOINT_BUSINESS_CASES.items():
        for status_code, case_ids in (
            (400, matrix["cases_400"]),
            (404, matrix["cases_404"]),
            (409, matrix["cases_409"]),
        ):
            for case_id in case_ids:
                assert case_id in BUSINESS_ERROR_CASES, (route, case_id)
                assert BUSINESS_ERROR_CASES[case_id]["http_status"] == status_code


def test_documented_business_responses_have_matrix_cases() -> None:
    for doc_key, doc in ENDPOINT_DOCS.items():
        route = ENDPOINT_ROUTE_MAP.get(doc_key)
        assert route is not None, doc_key
        matrix = ENDPOINT_BUSINESS_CASES.get(route)
        assert matrix is not None, route

        if 400 in doc["responses"]:
            assert matrix["cases_400"], route
        if 404 in doc["responses"]:
            assert matrix["cases_404"], route
        if 409 in doc["responses"]:
            assert matrix["cases_409"], route


def test_endpoint_error_codes_include_all_business_case_codes() -> None:
    for doc_key, doc in ENDPOINT_DOCS.items():
        route = ENDPOINT_ROUTE_MAP[doc_key]
        matrix = ENDPOINT_BUSINESS_CASES[route]
        for case_id in matrix["cases_400"] + matrix["cases_404"] + matrix["cases_409"]:
            expected_code = BUSINESS_ERROR_CASES[case_id]["code"]
            assert expected_code in doc["error_codes"], (doc_key, case_id, expected_code)
