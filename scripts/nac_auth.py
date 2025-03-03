# Copyright (c) 2025 Nokia All rights reserved.
# Licensed under the BSD 3-Clause License
# SPDX-License-Identifier: BSD-3-Clause

import logging
import os
import urllib.parse
from typing import Tuple

import httpx
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("nac_auth")
app = FastAPI()

# NaC RapidAPI URLs and Hosts
# Client crendentials for RapidAPI Org/App
nac_auth_clientcredentials_url = os.getenv("NAC_AUTH_CLIENTCREDENTIALS_URL", "https://nac-authorization-server.p-eu.rapidapi.com")
nac_auth_clientcredentials_host = os.getenv("NAC_AUTH_CLIENTCREDENTIALS_HOST", "nac-authorization-server.nokia.rapidapi.com")
nac_auth_clientcredentials_path = "/auth/clientcredentials"
# NaC well-known metadata to retrieve authorize and token endpoints
nac_wellknown_metadata_url = os.getenv("NAC_WELLKNOWN_METADATA_URL", "https://well-known-metadata.p-eu.rapidapi.com")
nac_wellknown_metadata_host = os.getenv("NAC_WELLKNOWN_METADATA_HOST", "well-known-metadata.nokia.rapidapi.com")
nac_wellknown_metadata_path = "/oauth-authorization-server"


class WellknownMetadata(BaseModel):
    authorization_endpoint: str
    token_endpoint: str


class Clientcredentials(BaseModel):
    client_id: str
    client_secret: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = Field(default=None)
    scope: str | None = Field(default=None)


httpClientProxy = os.getenv("HTTP_CLIENT_PROXY") or None


class NacAuth():
    def __init__(self, rapid_api_key: str):
        self._rapid_api_key = rapid_api_key
        self._clientcredentials_client = httpx.AsyncClient(base_url=nac_auth_clientcredentials_url, http2=True, timeout=10, proxy=httpClientProxy)
        self._wellknown_metadata_client = httpx.AsyncClient(base_url=nac_wellknown_metadata_url, http2=True, timeout=10, proxy=httpClientProxy)
        self._token_client = None
        self._nac_authorize_url = None
        self._parsed_nac_token_url = None
        self._client_id: str | None = None
        self._client_secret: str | None = None

    async def get_wellknown_metadata(self):
        """Gets wellknown metadata and sets _nac_authorize_url and _parsed_nac_token_url if successful."""

        if self._nac_authorize_url is None or self._parsed_nac_token_url is None:
            headers = {
                "X-RapidAPI-Host": nac_wellknown_metadata_host,
                "X-RapidAPI-Key": self._rapid_api_key
            }
            try:
                logger.debug(f"{headers}")
                resp = await self._wellknown_metadata_client.get(url=nac_wellknown_metadata_path, headers=headers)
                resp.raise_for_status()
                wellknown_metadata = WellknownMetadata(**resp.json())
            except Exception as e:
                logger.error(f"error while retrieving wellknown metadata: {e}")
                raise e
            self._nac_authorize_url = wellknown_metadata.authorization_endpoint
            self._parsed_nac_token_url = urllib.parse.urlparse(wellknown_metadata.token_endpoint)
            self._token_client = httpx.AsyncClient(base_url=f"{self._parsed_nac_token_url.scheme}://{self._parsed_nac_token_url.netloc}", http2=True, timeout=10, proxy=httpClientProxy)

    async def get_clientcredentials(self) -> Tuple[str, str]:
        """Returns NaC client_id and client_secret for Org/App identified by RapidAPI key.

        Returns:
            Tuple[str, str]: client_id and client_secret corresponding to RapidAPI key
        """

        headers = {
            "X-RapidAPI-Host": nac_auth_clientcredentials_host,
            "X-RapidAPI-Key": self._rapid_api_key
        }
        try:
            resp = await self._clientcredentials_client.get(url=nac_auth_clientcredentials_path, headers=headers)
            resp.raise_for_status()
            client_credentials = Clientcredentials(**resp.json())
        except Exception as e:
            logger.error(f"error while retrieving clientcredentials: {e}")
            raise e

        return client_credentials.client_id, client_credentials.client_secret

    async def redirect_authorize(self, app_redirect_uri: str, login_hint: str) -> RedirectResponse:
        """Redirects to NaC authorize with predefined url params. It also retrieves NaC authorize url if unknown.

        Args:
            redirect_uri (str): app redirect uri where authorization code is sent after successful authorization
            login_hint (str): a phone number to verify
            client_id (str): client_id corresponding to RapidAPI key

        Returns:
            RedirectResponse: an HTTP response redirecting to NaC authorize url with params
        """

        if not self._nac_authorize_url:
            try:
                await self.get_wellknown_metadata()
            except Exception:
                raise

        if not self._client_id:
            try:
                self._client_id, self._client_secret = await self.get_clientcredentials()
            except Exception:
                raise

        params = {
            "scope": "number-verification:verify",
            "state": "app-state",
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": app_redirect_uri,
            "login_hint": login_hint
        }
        location = self._nac_authorize_url+"?"+urllib.parse.urlencode(query=params, quote_via=urllib.parse.quote)
        logger.debug(f"location: {location}")

        return RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)

    async def retrieve_token(self, code: str) -> str:
        """Retrieves token for received parameters. It also retrieves NaC token url if unknown.

        Args:
            code (str): NaC authorization code received after authorization
            client_id (str): client_id corresponding to RapidAPI key
            client_secret (str): client_secret corresponding to RapidAPI key

        Returns:
            str: token in form of: "{token_type} {acces_token}"
        """

        if not self._parsed_nac_token_url:
            logger.debug("retrieve_token try to get token url")
            try:
                await self.get_wellknown_metadata()
            except Exception:
                raise

        if not self._client_id or not self._client_secret:
            try:
                self._client_id, self._client_secret = await self.get_clientcredentials()
            except Exception:
                raise

        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        body = {
            "grant_type": "authorization_code",
            "code": code
        }
        try:
            resp = await self._token_client.post(url=self._parsed_nac_token_url.path, data=body, headers=headers, auth=HTTPBasicAuth(self._client_id, self._client_secret))
            resp.raise_for_status()
            token_resp = AccessTokenResponse(**resp.json())
        except Exception as e:
            logger.error(f"error while retrieving token: {e}")
            raise e

        return token_resp.token_type + " " + token_resp.access_token
