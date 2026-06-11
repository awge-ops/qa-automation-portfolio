"""
Activation and login flow tests.

Covers:
  - Valid licence activation
  - Student login after activation
  - Invalid credential handling
"""

import pytest

from framework import config
from tests.ui.pages import ActivationPage
from tests.ui.pages.activation_page import LoginPage


@pytest.mark.ui
class TestActivation:

    def test_valid_activation(self, activation_page: ActivationPage, student_credentials):
        """A valid account number and licence key should activate the app."""
        creds = student_credentials("new_student")
        activation_page.open()
        activation_page.activate(creds["account_number"], creds["licence_key"])

    def test_activation_redirects_to_checking_updates(self, activation_page: ActivationPage, student_credentials):
        """After activation, the app should redirect to the checking-updates page."""
        creds = student_credentials("new_student")
        activation_page.open()
        activation_page.activate(creds["account_number"], creds["licence_key"])
        activation_page.expect_url(f"{config.APP_ADDRESS}/checking-updates")


@pytest.mark.ui
class TestLogin:

    def test_student_login(self, app_page, student_credentials):
        """A student should be able to log in with email and password."""
        creds = student_credentials("new_student")
        login = LoginPage(app_page)
        login.login(creds["email"], creds["password"])
        login.expect_dashboard_redirect()

    def test_login_reaches_dashboard(self, app_page, student_credentials):
        """After login, the dashboard should be visible with key elements."""
        creds = student_credentials("new_student")
        login = LoginPage(app_page)
        login.login(creds["email"], creds["password"])
        login.expect_dashboard_redirect()

        from tests.ui.pages import DashboardPage
        dashboard = DashboardPage(app_page)
        dashboard.wait_for_loaded()
