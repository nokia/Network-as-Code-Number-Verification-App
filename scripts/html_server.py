# Copyright (c) 2025 Nokia All rights reserved.
# Licensed under the BSD 3-Clause License
# SPDX-License-Identifier: BSD-3-Clause


import logging
import os
import re

from fastapi import FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from nac_auth import NacAuth
from nac_number_verification import NacNumberVerification

logger = logging.getLogger("html_server")
app = FastAPI()
templates = Jinja2Templates(directory="html_templates")

app_redirect_uri = os.getenv("INGRESS_URL")+"/redirect"
rapid_api_key = os.getenv("API_KEY", "")
nac_auth = NacAuth(rapid_api_key=rapid_api_key)
nac_num_verif = NacNumberVerification(rapid_api_key=rapid_api_key)


def get_allowed_phone_numbers():
    allowed_phone_numbers = os.getenv("ALLOWED_PHONE_NUMBERS", "").removeprefix("[").removesuffix("]")
    return allowed_phone_numbers.split()


allowed_phone_numbers = get_allowed_phone_numbers()


def check_phone_number(phone_number: str):
    """Checks if phone number is allowed"""
    if len(allowed_phone_numbers) == 0:
        return
    if not phone_number in allowed_phone_numbers:
        raise HTTPException(status.HTTP_403_FORBIDDEN)


def redirect_error() -> RedirectResponse:
    url = "/?error=true"
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/", response_class=HTMLResponse)
async def serve_form(request: Request,
                     verif_result: str | None = Query(default=None),
                     error: str | None = Query(default=None)
                     ):
    context: dict = {"request": request}
    if error:
        context["error"] = True
    elif verif_result:
        context["show_result"] = verif_result == "True"

    logger.debug(f"context: {context}")
    return templates.TemplateResponse("index.html", context)


@app.post("/submit",
          status_code=status.HTTP_303_SEE_OTHER)
async def handle_form_submission(phone_number: str = Form()):
    try:
        phone_number = "+" + re.sub(r"\D", "", phone_number)
        check_phone_number(phone_number)
        return await nac_auth.redirect_authorize(app_redirect_uri=app_redirect_uri+"/"+phone_number, login_hint=phone_number)
    except Exception:
        return redirect_error()


@app.get("/redirect/{phone_number}",
         summary="Receive NaC auth code",
         description="Endpoint for receiving NaC auth code upon authorization code flow.",
         status_code=status.HTTP_303_SEE_OTHER)
async def receive_nac_code(phone_number: str, code: str = Query()):
    # Front-end app calls this at end of redirect flow
    try:
        token = await nac_auth.retrieve_token(code)
    except Exception:
        return redirect_error()

    try:
        num_verif_result = await nac_num_verif.verify_number(phone_number, token)
    except Exception:
        return redirect_error()

    return RedirectResponse(url=f"/?verif_result={num_verif_result}", status_code=status.HTTP_303_SEE_OTHER)
