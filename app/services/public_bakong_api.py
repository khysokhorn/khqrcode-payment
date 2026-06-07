import os

import requests
import asyncio
import httpx

import asyncio
import os
from typing import Any

import httpx

from app.models.public_bankong_api_response import BakongTransactionResponse


class PublicBakongAPI:
    def __init__(self, max_retries: int = 3, delay_in_seconds: int = 3):
        base_url = os.getenv("PUBLIC_BAKONG_API")
        if not base_url:
            raise ValueError("PUBLIC_BAKONG_API environment variable is not set.")

        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.delay_in_seconds = delay_in_seconds
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,km-KH;q=0.8,km;q=0.7",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://api-bakong.nbc.gov.kh",
            "Priority": "u=1, i",
            "Referer": "https://api-bakong.nbc.gov.kh/",
            "Sec-CH-UA": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
        }

    async def check_transaction_by_md5(
        self,
        md5: str,
        attempt: int = 1,
    ) -> BakongTransactionResponse:
        url = "/local/v1/check_transaction_by_md5"
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30,
                headers=self.headers,
            ) as client:
                response = await client.post(
                    url,
                    json={"md5": md5},
                )
                response.raise_for_status()
                result = BakongTransactionResponse.model_validate(response.json())
                if result.responseCode == 0 and result.data is not None:
                    return result

                if attempt >= self.max_retries:
                    return BakongTransactionResponse(
                        responseCode=-1,
                        responseMessage=result.responseMessage,
                        errorCode="PENDING",
                        data=None,
                    )

        except Exception as e:
            if attempt >= self.max_retries:
                return BakongTransactionResponse(
                    responseCode=-1,
                    responseMessage=str(e),
                    errorCode="ERROR",
                    data=None,
                )

        await asyncio.sleep(self.delay_in_seconds)

        return await self.check_transaction_by_md5(
            md5=md5,
            attempt=attempt + 1,
        )


publicBakongApi = PublicBakongAPI()
