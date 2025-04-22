from dataclasses import dataclass
from base_sf_rqst import BaseSalesforceRequest

@dataclass
class BulkQueryRequest(BaseSalesforceRequest):
    query: str
    operation: str = "query"
    contentType: str = "JSON"
    lineEnding: str = "LF"

