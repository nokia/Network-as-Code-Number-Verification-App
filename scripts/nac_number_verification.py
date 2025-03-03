# Copyright (c) 2025 Nokia All rights reserved.
# Licensed under the BSD 3-Clause License
# SPDX-License-Identifier: BSD-3-Clause


import logging
import os

import httpx
from pydantic import BaseModel

logger = logging.getLogger("nac_number_verification")

nac_number_verification_url = os.getenv("NAC_NUMBER_VERIFICATION_URL", "https://number-verification.p-eu.rapidapi.com")
nac_number_verification_host = os.getenv("NAC_NUMBER_VERIFICATION_HOST", "number-verification.nokia.rapidapi.com")
nac_number_verification_verify_path = "/verify"
nac_number_verification_device_path = "/device-phone-number"


class NumberVerificationVerifyResult(BaseModel):
    devicePhoneNumberVerified: bool


class NumberVerificationDeviceResult(BaseModel):
    devicePhoneNumber: str


class NacNumberVerification():
    def __init__(self, rapid_api_key: str):
        self._rapid_api_key = rapid_api_key
        self._num_verification_client = httpx.AsyncClient(base_url=nac_number_verification_url, http2=True, timeout=10)

    async def verify_number(self, phone_number: str, token: str) -> bool:
        """Verifies the phone number via NaC.

        Args:
            phone_number (str): the phone number to verify
            token (str): NaC access token

        Returns:
            bool: True if phone number is verified else False
        """
        headers = {
            "X-RapidAPI-Host": nac_number_verification_host,
            "X-RapidAPI-Key": self._rapid_api_key,
            "Authorization": token
        }
        body = {
            "phoneNumber": phone_number
        }
        try:
            resp = await self._num_verification_client.post(url=nac_number_verification_verify_path, json=body, headers=headers)
            resp.raise_for_status()
            num_verif_result = NumberVerificationVerifyResult(**resp.json())
        except Exception as e:
            logger.error(f"error while retrieving clientcredentials: {e}")
            raise e

        return num_verif_result.devicePhoneNumberVerified
