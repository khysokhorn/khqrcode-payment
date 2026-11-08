import io
import json
import unittest
import urllib.error
import urllib.parse
from unittest.mock import patch

import httpx
from fastapi import FastAPI

from app.api.public_bakong import router
from app.services.public_bakong_open_api import PublicBakongOpenAPI, resolve_nuxt_data


# Hand-written Nuxt fixture: dictionary values point to entries in this array.
SUCCESS_DATA = [
    ["ShallowReactive", 1],
    {"data": 2},
    ["ShallowReactive", 3],
    {"tx-lookup": 4},
    {"txResult": 5, "txError": 6},
    {"hash": 7, "amount": 8, "currency": 9, "createdDateMs": 10,
     "acknowledgedDateMs": 11, "description": 12},
    None,
    "a" * 64,
    2000,
    "KHR",
    0,
    1000,
    "Test payment",
]


def html_response(data):
    return io.BytesIO(
        ("<html><script type='application/json' id='__NUXT_DATA__'>"
         + json.dumps(data) + "</script></html>").encode()
    )


class PublicBakongClientTests(unittest.TestCase):
    def setUp(self):
        self.client = PublicBakongOpenAPI()

    def test_resolves_transaction_without_treating_primitive_numbers_as_references(self):
        result = resolve_nuxt_data(SUCCESS_DATA)
        self.assertEqual(result["txResult"]["amount"], 2000)
        self.assertEqual(result["txResult"]["createdDateMs"], 0)
        self.assertIsNone(result["txError"])

    def test_resolves_undefined_and_shared_refs(self):
        data = [{"tx-lookup": 1}, {"txResult": 2, "txError": -1},
                {"first": 3, "second": 3}, ["Ref", 4], False]
        self.assertEqual(resolve_nuxt_data(data), {
            "txResult": {"first": False, "second": False}, "txError": None,
        })

    def test_cyclic_reference_does_not_recurse_forever(self):
        self.assertEqual(resolve_nuxt_data([
            {"tx-lookup": 1}, {"txResult": 1, "txError": 2}, None,
        ]), {"txResult": None, "txError": None})

    def test_lookup_encodes_cookie_and_enriches_zero_timestamp(self):
        with patch("urllib.request.urlopen", return_value=html_response(SUCCESS_DATA)) as request:
            result = self.client.check_transaction(value=" BDF5AC24 ", amount="2000")
        payload = json.loads(urllib.parse.unquote(
            request.call_args.args[0].get_header("Cookie").split(";", 1)[0].split("=", 1)[1]
        ))
        self.assertEqual(payload, {"type": "SHORT_HASH", "value": "BDF5AC24",
                                   "amount": "2000", "ccy": "KHR"})
        self.assertEqual(result["txResult"]["createdDateIso"], "1970-01-01T00:00:00+00:00")
        self.assertEqual(result["txResult"]["acknowledgedDateIso"], "1970-01-01T00:00:01+00:00")

    def test_md5_and_hash_lookups_do_not_require_amount(self):
        for search_type, length in (("MD5", 32), ("HASH", 64)):
            with self.subTest(search_type=search_type), patch(
                "urllib.request.urlopen", return_value=html_response(SUCCESS_DATA)
            ):
                result = self.client.check_transaction(search_type=search_type, value="a" * length)
                self.assertEqual(result["txResult"]["hash"], "a" * 64)

    def test_invalid_inputs_are_rejected_before_network_request(self):
        cases = [
            {"value": "bdf5ac24"},
            {"value": "bdf5ac24", "amount": "0"},
            {"value": "bdf5ac24", "amount": "-1"},
            {"value": "bdf5ac24", "amount": "NaN"},
            {"value": "bdf5ac24", "amount": "Infinity"},
            {"value": "bdf5ac24", "amount": "bad"},
            {"value": "bdf5ac24", "amount": "2000", "ccy": "EUR"},
            {"value": "not-hex!", "amount": "2000"},
            {"search_type": "MD5", "value": "abc"},
            {"search_type": "INVALID", "value": "bdf5ac24"},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), patch("urllib.request.urlopen") as request:
                with self.assertRaises(ValueError):
                    self.client.check_transaction(**kwargs)
                request.assert_not_called()

    def test_upstream_errors_are_preserved(self):
        data = [{"tx-lookup": 1}, {"txResult": 2, "txError": 3}, None,
                {"errorCode": 4, "message": 5}, 1, "Transaction not found"]
        with patch("urllib.request.urlopen", return_value=html_response(data)):
            result = self.client.check_transaction("MD5", "a" * 32)
        self.assertEqual(result, {"txResult": None, "txError": {
            "errorCode": 1, "message": "Transaction not found",
        }})

    def test_network_failure_is_not_reported_as_a_payment(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unavailable")):
            result = self.client.check_transaction("MD5", "a" * 32)
        self.assertIsNone(result["txResult"])
        self.assertEqual(result["txError"]["errorCode"], -1)
        self.assertTrue(result["txError"]["isNetworkError"])

    def test_missing_script_and_malformed_data_have_structured_errors(self):
        cases = [
            (b"<html>Unavailable</html>", -2),
            (b'<script id="__NUXT_DATA__">invalid</script>', -3),
            (html_response({"wrong": "shape"}).getvalue(), -3),
            (html_response([{"tx-lookup": 99}]).getvalue(), -3),
            (html_response([{"tx-lookup": 1}, []]).getvalue(), -3),
            (html_response([{}]).getvalue(), 1),
        ]
        for body, expected_code in cases:
            with self.subTest(body=body), patch("urllib.request.urlopen", return_value=io.BytesIO(body)):
                result = self.client.check_transaction("MD5", "a" * 32)
                self.assertIsNone(result["txResult"])
                self.assertEqual(result["txError"]["errorCode"], expected_code)


class PublicBakongRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_valid_query_returns_transaction(self):
        with patch("urllib.request.urlopen", return_value=html_response(SUCCESS_DATA)):
            response = await self.client.get("/api/v1/public-bakong/check", params={
                "value": "bdf5ac24", "amount": "2000", "ccy": "KHR",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["txResult"]["amount"], 2000)

    async def test_hash_alias_and_normalization(self):
        with patch("urllib.request.urlopen", return_value=html_response(SUCCESS_DATA)):
            response = await self.client.get("/api/v1/public-bakong/check", params={
                "type": " md5 ", "hash": "a" * 32,
            })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["txError"])

    async def test_missing_identifier_or_amount_returns_bad_request(self):
        for params in ({}, {"value": "bdf5ac24"}):
            with self.subTest(params=params):
                response = await self.client.get("/api/v1/public-bakong/check", params=params)
                self.assertEqual(response.status_code, 400)

    async def test_health_does_not_contact_upstream(self):
        with patch("urllib.request.urlopen") as request:
            response = await self.client.get("/api/v1/public-bakong/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
