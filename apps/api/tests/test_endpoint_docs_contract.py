import os

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.business_errors import BUSINESS_ERROR_CASES, ENDPOINT_BUSINESS_CASES
from app.api.docs import ENDPOINT_DOCS, ENDPOINT_ROUTE_MAP
from app.main import app

client = TestClient(app)

OPERATION_DOC_MAP = {
    "registerPublicUser": "auth_register",
    "loginUser": "auth_login",
    "refreshToken": "auth_refresh",
    "logoutUser": "auth_logout",
    "changePassword": "auth_change_password",
    "getCurrentUser": "auth_me",
    "createUser": "users_create",
    "listUsers": "users_list",
    "getUserById": "users_get",
    "updateUserById": "users_update",
    "softDeleteUserById": "users_delete",
    "createExperience": "experiences_create",
    "listExperiences": "experiences_list",
    "getExperienceById": "experiences_get",
    "updateExperienceById": "experiences_update",
    "deactivateExperienceById": "experiences_delete",
    "createSchedule": "schedules_create",
    "listSchedules": "schedules_list",
    "getScheduleById": "schedules_get",
    "updateScheduleById": "schedules_update",
    "deactivateScheduleById": "schedules_delete",
    "createReservation": "reservations_create",
    "listReservations": "reservations_list",
    "getReservationById": "reservations_get",
    "updateReservationById": "reservations_update",
    "confirmReservationById": "reservations_confirm",
    "transitionReservationStatusById": "reservations_transition",
    "cancelReservationById": "reservations_cancel",
    "createPaymentProofForReservation": "reservation_payment_proofs_create",
    "createParticipantForReservation": "participants_create",
    "getPaymentProofById": "payment_proofs_get",
    "updatePaymentProofById": "payment_proofs_update",
    "getParticipantById": "participants_get",
    "updateParticipantById": "participants_update",
    "createEquine": "equines_create",
    "listEquines": "equines_list",
    "getEquineById": "equines_get",
    "updateEquineById": "equines_update",
    "deactivateEquineById": "equines_delete",
    "createSaddle": "saddles_create",
    "listSaddles": "saddles_list",
    "getSaddleById": "saddles_get",
    "updateSaddleById": "saddles_update",
    "createAssignment": "assignments_create",
    "getAssignmentById": "assignments_get",
    "updateAssignmentById": "assignments_update",
    "createLog": "logs_create",
    "getLogById": "logs_get",
    "updateLogById": "logs_update",
    "createProvider": "providers_create",
    "getProviderById": "providers_get",
    "updateProviderById": "providers_update",
    "deactivateProviderById": "providers_delete",
    "createPolicy": "policies_create",
    "getPolicyById": "policies_get",
    "updatePolicyById": "policies_update",
    "getEmergencyContacts": "config_emergency_contacts",
    "getReservationRules": "config_get",
    "updateReservationRules": "config_update",
}


def test_endpoint_docs_contract_shape() -> None:
    for key, doc in ENDPOINT_DOCS.items():
        assert isinstance(doc["summary"], str) and doc["summary"].strip(), key
        assert isinstance(doc["description"], str) and doc["description"].strip(), key
        assert isinstance(doc["permissions"], list), key
        assert isinstance(doc["responses"], dict) and doc["responses"], key
        assert isinstance(doc["error_codes"], list), key
        assert isinstance(doc["service_docstring"], str) and doc["service_docstring"].strip(), key


def test_openapi_operations_use_documented_contract() -> None:
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]
    operation_ids: dict[str, dict] = {}
    for methods in paths.values():
        for operation in methods.values():
            operation_id = operation.get("operationId")
            if operation_id:
                operation_ids[operation_id] = operation

    for operation_id, doc_key in OPERATION_DOC_MAP.items():
        assert operation_id in operation_ids, operation_id
        operation = operation_ids[operation_id]
        doc = ENDPOINT_DOCS[doc_key]
        assert operation.get("summary") == doc["summary"]
        description = operation.get("description", "")
        assert doc["description"] in description
        for status_code in doc["responses"]:
            assert str(status_code) in operation.get("responses", {})


def test_openapi_business_examples_follow_master_catalog() -> None:
    openapi = client.get("/openapi.json").json()
    operation_ids: dict[str, dict] = {}
    for methods in openapi["paths"].values():
        for operation in methods.values():
            operation_id = operation.get("operationId")
            if operation_id:
                operation_ids[operation_id] = operation

    for operation_id, doc_key in OPERATION_DOC_MAP.items():
        route = ENDPOINT_ROUTE_MAP[doc_key]
        matrix = ENDPOINT_BUSINESS_CASES[route]
        operation = operation_ids[operation_id]
        responses = operation.get("responses", {})

        for status_code, case_ids in (
            ("400", matrix["cases_400"]),
            ("404", matrix["cases_404"]),
            ("409", matrix["cases_409"]),
        ):
            if not case_ids:
                continue
            response = responses[status_code]
            examples = response.get("content", {}).get("application/json", {}).get("examples", {})
            assert examples, (operation_id, status_code)
            for case_id in case_ids:
                assert case_id in examples, (operation_id, status_code, case_id)
                assert examples[case_id]["value"]["code"] == BUSINESS_ERROR_CASES[case_id]["code"]
