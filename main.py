import logging
from typing import Dict, Any
from salesforce_auth import SalesforceJWTAuth
from salesforce_requests import SalesforceRequests, SalesforceSession
from bulk_qry_rqst import BulkQueryRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORT_ID = "00OHq000007fZJfMAM"
TIMEHEETS_QUERY = ""


def main() -> None:
    """Main function to run the SerMetrics application."""
    logger.info("Starting SerMetrics application")

    try:
        auth = SalesforceJWTAuth()
        sf_session = auth.create_session()
        sf_requests = SalesforceRequests(sf_session)

        report_data = sf_requests.get_report_data(REPORT_ID, include_details=True)
        report_df = sf_requests.parse_report_to_dataframe(report_data)
        report_df.to_csv("report_data.csv", index=False)
        # logger.info("Invoice report data:\n%s", report_df.head())

        body = BulkQueryRequest(query=TIMESHEETS_QUERY)
        body.validate()
        response = sf.post_bulk_job(body.to_dict())
        logger.info("Bulk query job response: %s", response)

    except Exception as e:
        logger.error("An error occurred: %s", str(e))


if __name__ == "__main__":
    main()
