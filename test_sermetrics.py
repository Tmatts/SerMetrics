import unittest
from unittest.mock import Mock, patch
from salesforce_auth import SalesforceJWTAuth, SalesforceSession
from salesforce_requests import SalesforceRequests
from bulk_qry_rqst import BulkQueryRequest


class TestSerMetrics(unittest.TestCase):
    @patch("app.SalesforceJWTAuth.create_session")
    def test_salesforce_connection(self, mock_connect):
        mock_connect.return_value = Mock()
        auth = SalesforceJWTAuth()
        sf = auth.authenticate()
        self.assertIsNotNone(sf)

    @patch("salesforce_requests.SalesforceRequests.get_report_data")
    def test_get_report_data(self, mock_get_report):
        mock_get_report.return_value = {"reportMetadata": {}, "factMap": {}}
        auth = Mock()
        sf = Mock()
        sf_requests = SalesforceRequests(sf)
        report_data = sf_requests.get_report_data(
            "test_report_id", include_details=False
        )
        self.assertIsInstance(report_data, dict)

    def test_bulk_query_request(self):
        query = "SELECT Id FROM Contact"
        body = BulkQueryRequest(query=query)
        self.assertEqual(body.query, query)
        self.assertTrue(body.validate())

    # @patch("pandas.DataFrame")
    # def test_salesforce_report_parser(self, mock_df):
    #     mock_df.return_value = Mock()
    #     report_data = {"reportMetadata": {}, "factMap": {}}
    #     df = SalesforceRequests.parse_report_to_dataframe(report_data)
    #     self.assertIsNotNone(df)


if __name__ == "__main__":
    unittest.main()
